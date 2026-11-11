# ============================================================
# PROCESO 7: Calcular los indicadores de cartera (enfoque de portafolio / PMO)
# Insumo:    data/procesado/cinco_preguntas.parquet (Proceso 4) y data/procesado/brechas_gobierno_nacional.parquet (Proceso 3)
# Resultado: data/procesado/indicadores_proyecto.parquet  (una fila por inversión)
#            data/procesado/indicadores_cartera.parquet   (una fila por ministerio o entidad + la cartera completa)
#            docs/indicadores_resultados.md               (definiciones y cifras, para revisar)
# Preguntas: P1 brecha · P2 presupuesto pendiente · P3 desviación del costo · P4 problemas reportados
#            P5 financiamiento · P7 atraso.  (La P6, alineamiento estratégico, queda fuera por decisión del founder.)
# Uso:       uv run --with pandas --with pyarrow python scripts/07_indicadores.py
# ============================================================

# --- Paquetes ---
# pathlib: rutas de archivos (viene con Python)
# pandas: tablas; pyarrow: leer y guardar parquet (se instalan una vez)
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO, DOCS = RAIZ / "data" / "procesado", RAIZ / "docs"
HOY = pd.Timestamp("2026-11-10")      # misma fecha de referencia que el Proceso 4
TODO = "CARTERA COMPLETA"

def millones(x):
    """Monto legible. Antes: 16302345678.9 | Después: 'S/ 16.3 mil millones'."""
    if pd.isna(x):
        return "sin dato"
    if abs(x) >= 1e9:
        return f"S/ {x / 1e9:,.1f} mil millones"
    return f"S/ {x / 1e6:,.1f} millones" if abs(x) >= 1e6 else f"S/ {x / 1e3:,.0f} mil"

def porc(x):
    """Porcentaje al estilo de la app. Antes: 0.1 | Después: "10 %"."""
    return f"{100 * x:.0f} %"

def proporcion(a, b):
    """a / b, o faltante si b es 0 o falta (evita divisiones entre cero)."""
    return a / b if pd.notna(b) and b != 0 else float("nan")

# ============================================================
# PASO 7.1: Cargar
# ============================================================
inv = pd.read_parquet(PROCESADO / "cinco_preguntas.parquet")
brechas = pd.read_parquet(PROCESADO / "brechas_gobierno_nacional.parquet")
print("7.1 Inversiones:", inv.shape, "| filas de brechas:", brechas.shape)
ind = inv[["id", "cui", "sector", "unidad", "tipo", "marco", "estado", "avance", "costo", "viable"]].copy()

# ============================================================
# P1 — PASO 7.2: ¿Qué brecha cubre cada inversión?
#   Antes: una fila por inversión y brecha (17 119) | Después: por inversión, cuántas brechas y la lista de indicadores
#   Si no tiene brecha, se explica el motivo más probable según su tipo y su marco normativo.
# ============================================================
# Texto para mostrar: "PORCENTAJE DE ..." -> "Porcentaje de ..."; el aporte solo si es mayor que 0
#   Una misma brecha puede venir repetida (otro año u otro ámbito): se cuenta y se muestra una sola vez
aporte = [f" (aporta {a:,.0f} {u.lower()})" if pd.notna(a) and a > 0 else "" for a, u in zip(brechas["aporte"], brechas["unidad_medida"])]
lista = (brechas.assign(texto=brechas["indicador"].str.capitalize() + aporte)
         .groupby("cui").agg(n_brechas_total=("indicador", "nunique"),
                             brechas_lista=("texto", lambda s: " | ".join(dict.fromkeys(s)))).reset_index())
ind = ind.merge(lista, on="cui", how="left")
ind["n_brechas_total"] = ind["n_brechas_total"].fillna(0).astype(int)
ind["tiene_brecha"] = ind["n_brechas_total"] > 0

def motivo_sin_brecha(f):
    if f["tiene_brecha"]:
        return ""
    if "IRI" in f["tipo"]:
        return "Reconstrucción (IRI)"
    if f["marco"] == "SNIP":
        return "Proyecto del antiguo SNIP (anterior a las brechas)"
    if "IOARR" in f["tipo"]:
        return "Inversión menor (IOARR)"
    return "Sin brecha registrada"
ind["motivo_sin_brecha"] = ind.apply(motivo_sin_brecha, axis=1)
print("7.2 P1 con brecha:", int(ind["tiene_brecha"].sum()), "| motivos sin brecha:",
      ind.loc[~ind["tiene_brecha"], "motivo_sin_brecha"].value_counts().to_dict())

# ============================================================
# P2 — PASO 7.3: ¿Qué porcentaje del presupuesto falta ejecutar?
#   Dos niveles: (a) este año: presupuesto 2026 (PIM) menos lo gastado (devengado) 2026
#                (b) toda la vida del proyecto: saldo por ejecutar del MEF frente al costo actualizado
# ============================================================
ind["pim_2026"] = inv["pim_2026"].fillna(0)
ind["dev_2026"] = inv["dev_2026"].fillna(0)
ind["certificado_2026"] = inv["certificado_2026"].fillna(0)
ind["pendiente_2026"] = (ind["pim_2026"] - ind["dev_2026"]).clip(lower=0).where(ind["pim_2026"] > 0)
ind["pct_pendiente_2026"] = (ind["pendiente_2026"] / ind["pim_2026"]).where(ind["pim_2026"] > 0)
ind["saldo_total"] = inv["saldo"]
ind["pct_saldo_total"] = (inv["saldo"] / inv["costo"]).where(inv["costo"] > 0)
print("7.3 P2 con PIM 2026:", int((ind["pim_2026"] > 0).sum()), "| pendiente 2026:", millones(ind["pendiente_2026"].sum()),
      "| saldo total:", millones(ind["saldo_total"].sum()))

# ============================================================
# P3 — PASO 7.4: ¿Cuánto se desvió el costo?
#   Total: costo actualizado frente al monto con que se declaró viable
#   En dos tramos, si hay expediente técnico: diseño (viable -> expediente) y ejecución (expediente -> costo actual)
#   Las adendas de contratos no están en los datos del MEF (son del SEACE).
# ============================================================
comparable = (inv["viable"] > 0) & (inv["costo"] > 0)
ind["desv_total"] = (inv["costo"] - inv["viable"]).where(comparable)
ind["pct_desv_total"] = (ind["desv_total"] / inv["viable"]).where(comparable)
con_et = comparable & (inv["monto_et"] > 0)
ind["monto_et"] = inv["monto_et"]
ind["desv_diseno"] = (inv["monto_et"] - inv["viable"]).where(con_et)
ind["desv_ejecucion"] = (inv["costo"] - inv["monto_et"]).where(con_et)
ind["laudo"] = inv["laudo"].fillna(0)

def rango_desviacion(p):
    if pd.isna(p):
        return "Sin dato"
    if p < -0.001:
        return "Bajó"
    if p <= 0.001:
        return "Sin cambio"
    if p <= 0.2:
        return "Subió hasta 20 %"
    if p <= 1:
        return "Subió entre 20 % y 100 %"
    return "Más que se duplicó"
ind["rango_desviacion"] = ind["pct_desv_total"].map(rango_desviacion)
print("7.4 P3 rangos:", ind["rango_desviacion"].value_counts().to_dict(), "| desviación neta:", millones(ind["desv_total"].sum()))

# ============================================================
# P4 — PASO 7.5: ¿Qué problemas reportan los seguimientos (12-B)?
#   Clasificación con reglas de palabras (aproximada; la versión con IA queda para el Proceso 6).
#   Antes: un texto libre | Después: una clase y los temas que menciona (puede tener varios)
# ============================================================
texto = inv["problema_12b"].fillna("").str.lower()
# "Dice que no hay problemas": la frase aparece al inicio del texto (primeros 100 caracteres)
NADA = (r"^\W*(?:ningun[oa]?(?:\b|_)|ningún|nada\b|sin (?:problemas?|inconvenientes?|observaciones|restr?[ia]cci\w*|dificultades|novedad)|no aplica|n/?a\b)"
        r"|\bno (?:se )?(?:presenta\w*|present[oó]|han? presentado|registra\w*|identific\w*|evidencia\w*|tiene\w*|hay|existen?|reporta\w*|cuenta\w* con)"
        r"(?:\W*$|\W+(?:\w+\W+){0,3}?(?:problema|inconveniente|dificultad|restricci|observaci|riesgo|contratiempo))"
        r"|conclu\w* al 100|culmin\w* al 100|^\W*se (?:culmin|conclu|termin)\w*"
        r"|^\W*(?:la |el )?(?:obra|inversi\w*|proyecto)?\s*(?:se encuentra |est[aá] |fue )?(?:culminad|concluid|terminad)\w*\W*$")
inicio = texto.str[:100]
dice_nada = inicio.str.contains(NADA, regex=True)
ind["clase_problema"] = "Reporta problemas"
ind.loc[dice_nada, "clase_problema"] = "Dice que no hay problemas"
# Vacíos o solo signos ("--", ".", "-"): no dicen nada
ind.loc[~texto.str.contains(r"[a-zñáéíóú]", regex=True), "clase_problema"] = "Sin texto de problemas"
ind.loc[inv["fecha_12b"].isna(), "clase_problema"] = "Sin reporte de seguimiento"

# (columna, tema en palabras simples, palabras que lo delatan)
TEMAS = [
    ("tema_presupuesto", "Presupuesto o financiamiento", r"presupuest|financiamiento|\bpia\b|\bpim\b|pendiente de transferencia|falta de recursos|sin recursos|no (?:se )?cuenta\w* con (?:los )?recursos|recursos (?:financieros|econ)|demanda adicional|transferencia de recursos"),
    ("tema_programacion", "Aún no programada o en espera de inicio", r"previst\w* (?:iniciar|para)|programad\w* para|no se ha programado|incorporad\w* (?:al|en el) pmi|cartera del pmi|pmi 20\d\d|cartera de inversiones|a[uú]n no inicia"),
    ("tema_documentos", "Documentos o información pendiente", r"documentaci[oó]n|presentaci[oó]n de (?:los )?informes|informaci[oó]n (?:pendiente|incompleta)|antig[uü]edad de (?:los )?documentos|acervo documentario|expedientes? de (?:pago|liquidaci)"),
    ("tema_terreno", "Terreno o saneamiento legal", r"saneamiento f[ií]sico|terreno|predio|libre disponibilidad|titularidad|expropiaci"),
    ("tema_expediente", "Expediente técnico o estudios", r"expediente t[eé]cnico|estudio definitivo|estudios? de pre ?inversi|deficiencias? (?:en|del) (?:el )?(?:expediente|estudio)"),
    ("tema_contratista", "Contratista o contrato", r"contratista|consultor|resoluci[oó]n (?:del|de) contrato|penalidad|[ia][nm]cumplimiento|consorcio"),
    ("tema_arbitraje", "Arbitraje o controversias", r"arbitra|arbritra|controversia|conciliaci|laudo|junta de resoluci[oó]n de disputas"),
    ("tema_adicionales", "Adicionales o ampliación de plazo", r"adicional(?:es)? de obra|prestaci[oó]n(?:es)? adicional|deductivo|ampliaci[oó]n(?:es)? de plazo|mayores metrados|presupuesto adicional"),
    ("tema_paralizada", "Obra paralizada o suspendida", r"paraliza|suspensi[oó]n|suspendid"),
    ("tema_permisos", "Permisos, trámites o pronunciamientos de otras entidades", r"licencia|permiso|\bcira\b|autorizaci[oó]n|interferencia|opini[oó]n (?:favorable|t[eé]cnica)|pronunciamiento|tr[aá]mite|factibilidad|media tensi[oó]n|suministro el[eé]ctrico"),
    ("tema_contratacion", "Proceso de contratación", r"proceso de selecci[oó]n|desiert|convocatoria|licitaci|concurso p[uú]blico|buena pro|[oó]rgano encargado de las contrataciones|\boec\b|estudio de mercado|requerimiento"),
    ("tema_control", "Observaciones de control (Contraloría)", r"contralor|\bcgr\b|control concurrente|informe de control|\boci\b"),
    ("tema_clima", "Clima o desastres", r"lluvia|clim[aá]tic|friaje|helada|huaico|inundaci|sismo|fen[oó]meno"),
    ("tema_conflictos", "Conflictos sociales", r"conflictos? social|oposici[oó]n|protesta|paro\b|comuner"),
    ("tema_cierre", "Liquidación o cierre pendiente", r"liquidaci[oó]n|liquidar|cierre (?:del|de la|de) (?:proyecto|inversi|obra)|proceso de cierre|recepci[oó]n de (?:la )?obra"),
]
reporta = ind["clase_problema"] == "Reporta problemas"
columnas_tema = []
for col, tema, patron in TEMAS:
    # str.contains(): True si el texto menciona alguna de las palabras del tema. Antes: texto | Después: sí/no por tema
    ind[col] = reporta & texto.str.contains(patron, regex=True)
    columnas_tema.append((tema, col))
ind["temas"] = ind.apply(lambda f: "; ".join(t for t, c in columnas_tema if f[c]), axis=1)
ind.loc[reporta & (ind["temas"] == ""), "temas"] = "Otros problemas"
print("7.5 P4 clases:", ind["clase_problema"].value_counts().to_dict())
print("    temas:", {t: int(ind[c].sum()) for t, c in columnas_tema}, "| otros:", int((ind["temas"] == "Otros problemas").sum()))

# ============================================================
# P5 — PASO 7.6: ¿Tiene financiamiento?
#   La programación multianual (PMI_ANIO_1 a 4) empieza, según la evidencia, en 2026: en el INSN San Borja (CUI 2547701)
#   el año 1 es idéntico a su presupuesto 2026, y en toda la base el año 1 suma S/ 19,5 mil millones frente a
#   S/ 16,3 mil millones de presupuesto 2026. Por eso: año 1 = 2026; años 2 a 4 = 2027 en adelante (sin confirmación oficial).
#   Cinco grupos, en este orden de prioridad:
#     1. Con presupuesto 2026 (PIM > 0)
#     2. Programado para 2026, sin presupuesto (año 1 > 0 y PIM = 0): se planificó y no se financió
#     3. Programado para 2027 en adelante (años 2 a 4 > 0)
#     4 y 5. Sin financiamiento ni programación: se separan los prácticamente terminados (avance >= 95 %), que ya no lo necesitan
# ============================================================
GRUPOS_FIN = [("Con presupuesto 2026", "con_pim"), ("Programado para 2026, sin presupuesto", "prog_2026_sin_pim"),
              ("Programado para 2027 en adelante", "prog_2027"), ("Sin financiamiento – le falta ejecutar", "sin_fin_falta"),
              ("Sin financiamiento – prácticamente terminado", "sin_fin_terminado")]
NIVEL_FIN = {GRUPOS_FIN[0][0]: "Con presupuesto 2026", GRUPOS_FIN[1][0]: "Programado, sin presupuesto",
             GRUPOS_FIN[2][0]: "Programado, sin presupuesto", GRUPOS_FIN[3][0]: "Sin financiamiento ni programación",
             GRUPOS_FIN[4][0]: "Sin financiamiento ni programación"}
ind["programado_pmi_2026"] = inv["pmi_1"].fillna(0)
ind["programado_pmi_desde_2027"] = inv[["pmi_2", "pmi_3", "pmi_4"]].fillna(0).sum(axis=1)

def financiamiento(pim, pmi_2026, pmi_2027, avance):
    if pim > 0:
        return GRUPOS_FIN[0][0]
    if pmi_2026 > 0:
        return GRUPOS_FIN[1][0]
    if pmi_2027 > 0:
        return GRUPOS_FIN[2][0]
    return GRUPOS_FIN[4][0] if avance >= 95 else GRUPOS_FIN[3][0]
ind["financiamiento"] = [financiamiento(*v) for v in
                         zip(ind["pim_2026"], ind["programado_pmi_2026"], ind["programado_pmi_desde_2027"], ind["avance"])]
ind["nivel_financiamiento"] = ind["financiamiento"].map(NIVEL_FIN)
print("7.6 P5:", ind["financiamiento"].value_counts().to_dict())

# ============================================================
# P7 — PASO 7.7: ¿Cuánto tiempo lleva de atraso?
#   Atraso = meses entre la fecha de fin registrada y hoy, solo si ya venció y el avance es menor a 95 % (regla del estado
#   "Atrasado"). Se mide contra la ÚLTIMA fecha registrada: el atraso frente al plan original puede ser mayor.
#   Complemento: cumplimiento de la programación mensual 2026 (devengado ene-oct / programado ene-oct, del 12-B).
# ============================================================
vencido = inv["fin"].notna() & (inv["fin"] < HOY)
ind["fin"] = inv["fin"]
ind["meses_desde_fin"] = ((HOY - inv["fin"]).dt.days / 30.44).round().where(vencido)
atrasado = vencido & (ind["avance"] < 95)
# "atrasado" es la misma regla del estado "Atrasado" del Proceso 4 (3 380): se cuenta con esta marca y no con los meses,
# porque los que vencieron hace menos de medio mes quedan en 0 meses al redondear
ind["atrasado"] = atrasado
ind["meses_atraso"] = ind["meses_desde_fin"].where(atrasado, 0).where(inv["fin"].notna())

def rango_atraso(f):
    if pd.isna(f["fin"]):
        return "Sin fecha de fin"
    if not f["atrasado"]:
        return "Sin atraso"
    m = f["meses_atraso"]
    return "Hasta 12 meses" if m <= 12 else ("De 1 a 3 años" if m <= 36 else "Más de 3 años")
ind["rango_atraso"] = ind.apply(rango_atraso, axis=1)

ind["programado_ene_oct"] = inv["programado_ene_oct"]
ind["reprogramado_ene_oct"] = inv["reprogramado_ene_oct"]
# Sin devengado registrado en esos meses = no gastó nada (0), no "sin dato"
ind["devengado_ene_oct"] = inv["devengado_ene_oct"].fillna(0)
ind["pct_cumple_programacion"] = (ind["devengado_ene_oct"] / inv["programado_ene_oct"]).where(inv["programado_ene_oct"] > 0)
ind["rango_programacion"] = pd.cut(ind["pct_cumple_programacion"], [-0.01, 0.7, 0.9, float("inf")],
                                   labels=["Gastó menos del 70 % de lo programado", "Gastó entre 70 % y 90 %",
                                           "Gastó 90 % o más"]).astype(str).replace("nan", "Sin programación mensual")
print("7.7 P7 rangos de atraso:", ind["rango_atraso"].value_counts().to_dict())

# ============================================================
# PASO 7.7a: ¿Cuánto avanzó y cuánto gastó?  (aproximación al valor ganado con datos públicos)
#   Cuatro porcentajes de naturaleza distinta:
#     - avance de ejecución (declarado por la entidad): todos los componentes, valorizados a su costo  -> se parece al valor ganado (EV)
#     - avance físico (declarado): solo los productos (obra y equipos)
#     - gastado en toda su vida: devengado acumulado / costo (SIAF)                                     -> se parece al costo real (AC)
#     - gastado este año: devengado 2026 / presupuesto 2026 (PIM)
#   Para comparar avance y gasto en la MISMA fecha se usa lo gastado hasta el mes de la declaración: devengado hasta 2025 +
#   devengado de 2026 hasta ese mes. Solo es posible si la declaración es de 2026 (hay gasto mes a mes de ese año).
#   Índice tipo valor ganado (como el CPI del PMBOK) = avance declarado / gastado a esa fecha. 0,85 = por cada sol gastado
#   se avanzó el equivalente a 85 céntimos. Advertencias: el avance lo declara la entidad; el gasto es contable (incluye adelantos).
# ============================================================
ind["avance_ejecucion"] = inv["avance_ejecucion"]
ind["avance_fisico"] = inv["avance_fisico"]
ind["fecha_declaracion"] = inv["fecha_declaracion"]
ind["avance_fuente"] = inv["avance_fuente"]
ind["pct_gastado_vida"] = (inv["dev_acumulado"] / inv["costo"]).where(inv["costo"] > 0)
ind["pct_gastado_2026"] = (inv["dev_2026"].fillna(0) / inv["pim_2026"]).where(inv["pim_2026"] > 0)

meses_2026 = inv[[f"dev_2026_{i:02d}" for i in range(1, 12)]].fillna(0).to_numpy()
mes_decl = inv["fecha_declaracion"].dt.month.fillna(0).astype(int).clip(0, 11).to_numpy()
# Suma del gasto de enero hasta el mes de la declaración. Antes: 11 columnas mensuales | Después: 1 monto por proyecto
gastado_hasta_mes = [fila[:m].sum() for fila, m in zip(meses_2026, mes_decl)]
comparable = (inv["fecha_declaracion"].dt.year == 2026) & (inv["avance_ejecucion"] > 0) & (inv["costo"] > 0)
ind["gastado_a_la_declaracion"] = (inv["dev_hasta_2025"].fillna(0) + pd.Series(gastado_hasta_mes, index=inv.index)).where(comparable)
ind["pct_gastado_a_la_declaracion"] = ind["gastado_a_la_declaracion"] / inv["costo"]
ind["valor_avanzado"] = (inv["avance_ejecucion"] / 100 * inv["costo"]).where(comparable)       # EV
ind["indice_avance_gasto"] = (ind["valor_avanzado"] / ind["gastado_a_la_declaracion"]).where(ind["gastado_a_la_declaracion"] > 0)
ind["diferencia_gasto_avance"] = 100 * ind["pct_gastado_a_la_declaracion"] - inv["avance_ejecucion"].where(comparable)   # en puntos
ind["alerta_gasto_avance"] = ind["diferencia_gasto_avance"] >= 30
print("7.7a Avance frente a gasto: comparables", int(comparable.sum()), "| con alerta (gasto 30 puntos o más por encima del avance):",
      int(ind["alerta_gasto_avance"].sum()), "| fuente del avance:", ind["avance_fuente"].value_counts().to_dict())

# ============================================================
# PASO 7.7b: Frases en lenguaje simple para la ficha de cada proyecto (las muestra la app, Proceso 5)
#   Antes: números (pim_2026 = 681092, pct_pendiente_2026 = 0.0) | Después: "Sí. Tiene S/ 681 mil de presupuesto 2026 y ya lo gastó todo."
# ============================================================
def frase_brecha(f):
    if f["tiene_brecha"]:
        return "Apunta a 1 brecha registrada:" if f["n_brechas_total"] == 1 else f"Apunta a {f['n_brechas_total']} brechas registradas:"
    motivos = {"Reconstrucción (IRI)": "es una reconstrucción, que no se vincula a brechas",
               "Proyecto del antiguo SNIP (anterior a las brechas)": "es un proyecto anterior al sistema de brechas",
               "Inversión menor (IOARR)": "es una inversión menor de reposición o equipamiento"}
    return f"No tiene brecha registrada: {motivos.get(f['motivo_sin_brecha'], 'la entidad no la registró')}."

def frase_costo(f):
    """P3: cuánto cambió el costo desde que se aprobó, y laudos si los hay."""
    partes = []
    p = f["pct_desv_total"]
    if pd.notna(p) and p > 0.001:
        partes.append(f"Cuando se aprobó costaba {millones(f['viable'])}: subió {porc(p)}.")
    elif pd.notna(p) and p < -0.001:
        partes.append(f"Cuando se aprobó costaba {millones(f['viable'])}: bajó {porc(-p)}.")
    if f["laudo"] > 0:
        partes.append(f"Tiene laudos arbitrales por {millones(f['laudo'])}.")
    return " ".join(partes)

def frase_dinero(f):
    """P2 + P5: si tiene dinero este año, cuánto le falta gastar y cuánto le falta en total."""
    g = f["financiamiento"]
    if g == GRUPOS_FIN[0][0]:
        pend = f["pct_pendiente_2026"]
        resto = "ya lo gastó todo" if pend < 0.005 else f"le falta gastar el {porc(pend)} ({millones(f['pendiente_2026'])})"
        t = f"Sí. Tiene {millones(f['pim_2026'])} de presupuesto 2026 y {resto}."
    elif g == GRUPOS_FIN[1][0]:
        t = f"No. Estaba programado para 2026 ({millones(f['programado_pmi_2026'])}), pero no recibió presupuesto."
    elif g == GRUPOS_FIN[2][0]:
        t = f"Todavía no. Está programado desde 2027 ({millones(f['programado_pmi_desde_2027'])})."
    elif g == GRUPOS_FIN[3][0]:
        return f"No. No tiene presupuesto 2026 ni está programado, y le falta ejecutar {millones(f['saldo_total'])}."
    else:
        return "No lo necesita: está prácticamente terminado."
    if pd.notna(f["pct_saldo_total"]) and f["pct_saldo_total"] > 0.005:
        t += f" En total, le falta ejecutar el {porc(f['pct_saldo_total'])} de su costo."
    return t

def frase_problemas(f, fecha):
    """P4: qué dice su último reporte de seguimiento (12-B)."""
    c = f["clase_problema"]
    if c == "Sin reporte de seguimiento":
        return "La entidad no ha registrado reportes de seguimiento."
    cuando_ = f"Según su último reporte ({fecha:%d/%m/%Y})"
    if c == "Dice que no hay problemas":
        return f"{cuando_}, no tiene problemas."
    if c == "Sin texto de problemas":
        return f"{cuando_}, no describe problemas."
    if f["temas"] == "Otros problemas":
        return f"{cuando_}, tiene este problema:"
    return f"{cuando_}, sus problemas son de: {f['temas'].lower()}."

def frase_programacion(f):
    """P7, complemento: cumplimiento de su propio plan de gasto mensual de 2026."""
    p = f["pct_cumple_programacion"]
    return "" if pd.isna(p) else f"De enero a octubre de 2026 gastó el {porc(p)} de lo que planeó gastar."

ind["frase_brecha"] = ind.apply(frase_brecha, axis=1)
ind["frase_costo"] = ind.apply(frase_costo, axis=1)
ind["frase_dinero"] = ind.apply(frase_dinero, axis=1)
ind["frase_problemas"] = [frase_problemas(f, fecha) for (_, f), fecha in zip(ind.iterrows(), inv["fecha_12b"])]
ind["frase_programacion"] = ind.apply(frase_programacion, axis=1)

def frase_indice(f):
    """Índice tipo valor ganado en palabras: 0,85 -> 'Por cada sol gastado ... el equivalente a S/ 0,85'."""
    i = f["indice_avance_gasto"]
    if pd.isna(i) or i >= 10:          # 10 o más: gasto casi nulo frente al avance; el índice no dice nada útil
        return ""
    monto = f"{i:.2f}".replace(".", ",")
    return f"Por cada sol gastado hasta esa fecha, la entidad declara un avance equivalente a S/ {monto}."

def frase_alerta(f):
    """Solo si lo gastado supera al avance declarado por 30 puntos o más, comparados en la misma fecha. Redacción neutral."""
    if not f["alerta_gasto_avance"]:
        return ""
    return (f"Lo gastado hasta la fecha de esa declaración ({porc(f['pct_gastado_a_la_declaracion'])}) supera en "
            f"{f['diferencia_gasto_avance']:.0f} puntos al avance que declaró la entidad ({f['avance_ejecucion']:.0f} %).")

ind["frase_indice"] = ind.apply(frase_indice, axis=1)
ind["frase_alerta"] = ind.apply(frase_alerta, axis=1)
print("7.7b Ejemplo (INSN San Borja, 2547701):", ind.loc[ind["cui"] == "2547701", ["frase_dinero", "frase_costo", "frase_problemas"]].iloc[0].tolist())

# ============================================================
# PASO 7.8: Resumir por ministerio o entidad y para la cartera completa
#   Antes: 12 731 filas (una por inversión) | Después: 34 filas (33 sectores + la cartera completa)
# ============================================================
def resumen(g):
    pim = g["pim_2026"].sum(); dev = g["dev_2026"].sum()
    comp = g["desv_total"].notna()
    con_pim = g["pim_2026"] > 0
    fila = {
        "n": len(g), "costo": g["costo"].sum(),
        # P1
        "n_con_brecha": int(g["tiene_brecha"].sum()), "pct_con_brecha": g["tiene_brecha"].mean(),
        "n_varias_brechas": int((g["n_brechas_total"] >= 2).sum()),
        # P2
        "pim_2026": pim, "dev_2026": dev, "certificado_2026": g["certificado_2026"].sum(),
        "pendiente_2026": g["pendiente_2026"].sum(), "pct_pendiente_2026": proporcion(g["pendiente_2026"].sum(), pim),
        "n_con_pim": int(con_pim.sum()), "n_mas_mitad_pendiente": int((g["pct_pendiente_2026"] > 0.5).sum()),
        "n_sin_gasto_2026": int((con_pim & (g["dev_2026"] == 0)).sum()),
        "saldo_total": g["saldo_total"].sum(), "pct_saldo_total": proporcion(g["saldo_total"].sum(), g["costo"].sum()),
        # P3
        "viable_comparable": g.loc[comp, "viable"].sum(), "costo_comparable": g.loc[comp, "costo"].sum(),
        "desv_total": g["desv_total"].sum(), "pct_desv_total": proporcion(g["desv_total"].sum(), g.loc[comp, "viable"].sum()),
        "n_subio": int((g["pct_desv_total"] > 0.001).sum()), "n_bajo": int((g["pct_desv_total"] < -0.001).sum()),
        "n_subio_mas_20": int((g["pct_desv_total"] > 0.2).sum()), "n_mas_que_duplico": int((g["pct_desv_total"] > 1).sum()),
        "n_con_laudo": int((g["laudo"] > 0).sum()), "laudo_total": g["laudo"].sum(),
        # P4
        "n_reporta_problemas": int((g["clase_problema"] == "Reporta problemas").sum()),
        "n_dice_sin_problemas": int((g["clase_problema"] == "Dice que no hay problemas").sum()),
        "n_sin_seguimiento": int(g["clase_problema"].isin(["Sin reporte de seguimiento", "Sin texto de problemas"]).sum()),
        **{"n_" + c: int(g[c].sum()) for _, c in columnas_tema},
        # P7
        "n_atrasados": int(g["atrasado"].sum()),
        "mediana_meses_atraso": g.loc[g["atrasado"], "meses_atraso"].median(),
        "n_atraso_mas_12": int((g["meses_atraso"] > 12).sum()), "n_atraso_mas_36": int((g["meses_atraso"] > 36).sum()),
        "programado_ene_oct": g["programado_ene_oct"].sum(), "devengado_ene_oct": g.loc[g["programado_ene_oct"] > 0, "devengado_ene_oct"].sum(),
        "n_bajo_70_programacion": int((g["pct_cumple_programacion"] < 0.7).sum()),
        # Avance frente a gasto (solo proyectos con avance declarado en 2026, comparados en la misma fecha)
        "n_avance_declarado": int((g["avance_fuente"] == "declarado por la entidad").sum()),
        "n_comparables_avance": int(g["valor_avanzado"].notna().sum()),
        "n_alerta_gasto_avance": int(g["alerta_gasto_avance"].sum()),
        "valor_avanzado": g["valor_avanzado"].sum(), "gastado_a_la_declaracion": g["gastado_a_la_declaracion"].sum(),
        "costo_comparable_avance": g.loc[g["valor_avanzado"].notna(), "costo"].sum(),
    }
    fila["pct_cumple_programacion"] = proporcion(fila["devengado_ene_oct"], fila["programado_ene_oct"])
    fila["pct_avance_declarado"] = proporcion(fila["valor_avanzado"], fila["costo_comparable_avance"])
    fila["pct_gastado_comparable"] = proporcion(fila["gastado_a_la_declaracion"], fila["costo_comparable_avance"])
    fila["indice_avance_gasto"] = proporcion(fila["valor_avanzado"], fila["gastado_a_la_declaracion"])
    # P5: los cinco grupos con su número, costo y saldo; y los tres niveles en porcentaje de proyectos y de costo
    for grupo, clave in GRUPOS_FIN:
        m = g["financiamiento"] == grupo
        fila[f"n_{clave}"], fila[f"costo_{clave}"], fila[f"saldo_{clave}"] = int(m.sum()), g.loc[m, "costo"].sum(), g.loc[m, "saldo_total"].sum()
    for nivel, clave in [("Con presupuesto 2026", "presupuesto"), ("Programado, sin presupuesto", "programado"),
                         ("Sin financiamiento ni programación", "sin_nada")]:
        m = g["nivel_financiamiento"] == nivel
        fila[f"pct_n_{clave}"] = m.mean()
        fila[f"pct_costo_{clave}"] = proporcion(g.loc[m, "costo"].sum(), g["costo"].sum())
    return pd.Series(fila)

por_sector = ind.groupby("sector").apply(resumen, include_groups=False)
total = resumen(ind).to_frame(TODO).T
cartera = pd.concat([total, por_sector]).rename_axis("sector").reset_index()
print("7.8 Resumen:", cartera.shape)

# ============================================================
# PASO 7.9: Verificar que los totales cuadran y guardar
# ============================================================
assert len(ind) == len(inv), "se perdieron o duplicaron inversiones"
assert abs(cartera.loc[cartera["sector"] != TODO, "costo"].sum() - cartera.loc[cartera["sector"] == TODO, "costo"].iloc[0]) < 1, "la suma por sector no cuadra"
assert cartera.loc[cartera["sector"] != TODO, "n"].sum() == len(ind)
ind.to_parquet(PROCESADO / "indicadores_proyecto.parquet", index=False)
cartera.to_parquet(PROCESADO / "indicadores_cartera.parquet", index=False)
print("7.9 Guardados:", ind.shape, cartera.shape)

# ============================================================
# PASO 7.10: Escribir el informe de resultados (docs/indicadores_resultados.md)
# ============================================================
t = cartera.set_index("sector").loc[TODO]
pct = lambda x: f"{x:.0%}" if pd.notna(x) else "sin dato"
n = lambda x: f"{int(x):,}".replace(",", " ")
lineas = [
    "# Indicadores de cartera (enfoque de portafolio)", "",
    f"> Generado por `scripts/07_indicadores.py`. Gobierno nacional, datos del MEF al 08/11/2026, fecha de referencia {HOY:%d/%m/%Y}.",
    "> Las preguntas siguen la numeración del founder; la P6 (alineamiento estratégico) queda fuera.", "",
    "## Cartera completa", "",
    f"**{n(t['n'])} inversiones**, con un costo actualizado de **{millones(t['costo'])}**.", "",
    "### P1. Brecha que cubre cada inversión",
    f"- Con al menos una brecha: **{n(t['n_con_brecha'])} ({pct(t['pct_con_brecha'])})**; con dos o más: {n(t['n_varias_brechas'])}.",
    "- Sin brecha, por motivo: " + "; ".join(f"{k}: {n(v)}" for k, v in ind.loc[~ind['tiene_brecha'], 'motivo_sin_brecha'].value_counts().items()) + ".",
    "- No se puede decir qué parte de la brecha cierra cada inversión: el tamaño de la brecha casi nunca está registrado.", "",
    "### P2. Presupuesto pendiente de ejecutar",
    f"- **Este año:** {n(t['n_con_pim'])} inversiones tienen presupuesto 2026 (PIM) por {millones(t['pim_2026'])}; "
    f"se ha gastado {millones(t['dev_2026'])} y falta **{millones(t['pendiente_2026'])} ({pct(t['pct_pendiente_2026'])})**. "
    f"Certificado: {millones(t['certificado_2026'])}.",
    f"- {n(t['n_mas_mitad_pendiente'])} inversiones tienen sin gastar más de la mitad de su presupuesto; {n(t['n_sin_gasto_2026'])} no han gastado nada.",
    f"- **Toda la vida del proyecto:** saldo por ejecutar de **{millones(t['saldo_total'])} ({pct(t['pct_saldo_total'])} del costo)**.", "",
    "### P3. Desviación del costo (costo actualizado frente al monto viable)",
    f"- Subieron: **{n(t['n_subio'])}**; bajaron: {n(t['n_bajo'])}; subieron más de 20 %: **{n(t['n_subio_mas_20'])}**; "
    f"más que duplicaron su costo: **{n(t['n_mas_que_duplico'])}**.",
    f"- Desviación neta: **{millones(t['desv_total'])} ({pct(t['pct_desv_total'])})**. "
    f"En diseño (viable → expediente): {millones(ind['desv_diseno'].sum())}; en ejecución (expediente → costo actual): {millones(ind['desv_ejecucion'].sum())}.",
    f"- Con laudo arbitral: {n(t['n_con_laudo'])}, por {millones(t['laudo_total'])}. Las adendas de contratos no están en los datos del MEF.", "",
    "### P4. Problemas reportados en el seguimiento (12-B), clasificados con reglas de palabras",
    f"- Reportan problemas: **{n(t['n_reporta_problemas'])}**; dicen que no hay problemas: {n(t['n_dice_sin_problemas'])}; "
    f"sin seguimiento o sin texto: {n(t['n_sin_seguimiento'])}.",
    "- Temas (una inversión puede tener varios):", "",
    "| Tema | Inversiones |", "|---|---:|",
    *[f"| {tema} | {n(t['n_' + c])} |" for tema, c in sorted(columnas_tema, key=lambda x: -t["n_" + x[1]])],
    f"| Otros problemas (ningún tema reconocido) | {n((ind['temas'] == 'Otros problemas').sum())} |", "",
    "### P5. Financiamiento", "",
    "| Grupo | Inversiones | Costo | Saldo por ejecutar |", "|---|---:|---:|---:|",
    *[f"| {g} | {n(t['n_' + k])} | {millones(t['costo_' + k])} | {millones(t['saldo_' + k])} |" for g, k in GRUPOS_FIN],
    "", f"- **Con presupuesto 2026:** {pct(t['pct_n_presupuesto'])} de las inversiones y {pct(t['pct_costo_presupuesto'])} del costo.",
    f"- **Programadas, pero sin presupuesto:** {pct(t['pct_n_programado'])} de las inversiones y {pct(t['pct_costo_programado'])} del costo.",
    f"- **Sin financiamiento ni programación:** {pct(t['pct_n_sin_nada'])} de las inversiones y {pct(t['pct_costo_sin_nada'])} del costo.", "",
    "### Avance frente a gasto (aproximación al valor ganado)",
    f"- El avance que usa la app sale de la **declaración de la entidad** en {n(t['n_avance_declarado'])} proyectos; en el resto, de lo gastado.",
    f"- Comparables en la misma fecha (avance declarado en 2026): **{n(t['n_comparables_avance'])}**. En ellos, el avance declarado es "
    f"**{pct(t['pct_avance_declarado'])}** y lo gastado a esa fecha **{pct(t['pct_gastado_comparable'])}** del costo: "
    f"por cada sol gastado se declara un avance de **S/ {t['indice_avance_gasto']:.2f}**.",
    f"- Con lo gastado 30 puntos o más por encima del avance declarado: **{n(t['n_alerta_gasto_avance'])}** proyectos.", "",
    "### P7. Atraso",
    f"- Atrasadas: **{n(t['n_atrasados'])}**; mediana de **{t['mediana_meses_atraso']:.0f} meses**; más de 1 año: {n(t['n_atraso_mas_12'])}; "
    f"más de 3 años: **{n(t['n_atraso_mas_36'])}**.",
    "- Se mide contra la última fecha de fin registrada; el atraso frente al plan original puede ser mayor.",
    f"- Programación 2026 (12-B): de enero a octubre se programó {millones(t['programado_ene_oct'])} y se gastó "
    f"{millones(t['devengado_ene_oct'])} (**{pct(t['pct_cumple_programacion'])}**). {n(t['n_bajo_70_programacion'])} inversiones gastaron menos del 70 % de lo programado.", "",
    "## Por ministerio o entidad (de mayor a menor costo)", "",
    "| Ministerio o entidad | Inversiones | Costo | Con brecha | Falta gastar 2026 | Desviación del costo | Reportan problemas | Con presupuesto 2026 | Atrasadas (mediana) |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for _, f in cartera[cartera["sector"] != TODO].sort_values("costo", ascending=False).iterrows():
    mediana = f"{f['mediana_meses_atraso']:.0f} m" if pd.notna(f["mediana_meses_atraso"]) else "—"
    nombre = " ".join(p if i == 0 or p not in ("Y", "De", "Del", "La", "E") else p.lower()
                      for i, p in enumerate(f["sector"].title().split()))   # "Desarrollo E Inclusion" -> "Desarrollo e Inclusion"
    lineas.append(f"| {nombre} | {n(f['n'])} | {millones(f['costo'])} | {pct(f['pct_con_brecha'])} | {pct(f['pct_pendiente_2026'])} "
                  f"| {pct(f['pct_desv_total'])} | {n(f['n_reporta_problemas'])} | {pct(f['pct_n_presupuesto'])} | {n(f['n_atrasados'])} ({mediana}) |")
lineas += ["", "## Definiciones y advertencias", "",
           "- **Fuentes:** Detalle de inversiones, Inversiones y brechas y Formato 12-B (MEF, Datos Abiertos). El diccionario del MEF da error 404: "
           "el significado de algunas columnas (programación mensual del 12-B, `PMI_ANIO_1` a `4`) se dedujo de su nombre.",
           "- **P2:** pendiente 2026 = PIM − devengado 2026 (solo inversiones con PIM > 0). Saldo total = `SALDO_EJECUTAR` del MEF.",
           "- **P3:** solo inversiones con monto viable y costo actualizado mayores que 0. Desviación = costo actualizado − monto viable.",
           "- **P4:** reglas de palabras sobre el último texto de problemas del 12-B; son aproximadas y es lo que la entidad reporta. "
           "Son problemas actuales, no riesgos con probabilidad e impacto.",
           "- **P5:** `PMI_ANIO_1` se toma como 2026 y `PMI_ANIO_2` a `4` como 2027 en adelante (evidencia: en el INSN San Borja, CUI 2547701, "
           "el año 1 es igual a su presupuesto 2026; sin confirmación oficial). La fuente del dinero no está en estos archivos.",
           "- **Avance frente a gasto:** el avance de ejecución lo declara la entidad en el 12-B (todos los componentes, valorizados a "
           "su costo; el avance físico solo considera los productos). Lo gastado es el devengado del SIAF hasta el mes de la declaración. "
           "Índice = avance declarado ÷ gastado (se parece al CPI del valor ganado; falta el valor planificado para el índice de cronograma). "
           "Advertencias: el avance es autodeclarado y el gasto incluye adelantos a contratistas.",
           "- **P7:** atraso = meses desde la fecha de fin registrada, si ya pasó y el avance es menor a 95 %. "
           "Programación mensual: devengado de enero a octubre ÷ lo programado para esos meses."]
(DOCS / "indicadores_resultados.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
print("7.10 Informe escrito en docs/indicadores_resultados.md")
