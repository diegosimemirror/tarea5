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
    return f"S/ {x / 1e9:,.1f} mil millones" if abs(x) >= 1e9 else f"S/ {x / 1e6:,.1f} millones"

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
lista = (brechas.assign(texto=brechas["indicador"] + " (aporta " + brechas["aporte"].map(lambda a: f"{a:,.0f}" if pd.notna(a) else "?")
                        + " " + brechas["unidad_medida"].str.lower() + ")")
         .groupby("cui").agg(n_brechas_total=("indicador", "size"), brechas_lista=("texto", " | ".join)).reset_index())
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
        r"|conclu\w* al 100|culmin\w* al 100"
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
ind["temas"] = ind.apply(lambda f: ", ".join(t for t, c in columnas_tema if f[c]), axis=1)
ind.loc[reporta & (ind["temas"] == ""), "temas"] = "Otros problemas"
print("7.5 P4 clases:", ind["clase_problema"].value_counts().to_dict())
print("    temas:", {t: int(ind[c].sum()) for t, c in columnas_tema}, "| otros:", int((ind["temas"] == "Otros problemas").sum()))

# ============================================================
# P5 — PASO 7.6: ¿Tiene financiamiento?
#   Con presupuesto 2026 (PIM > 0) > Solo programado para años siguientes (PMI_ANIO_1 a 4 > 0) > Sin financiamiento
#   Dentro de "sin financiamiento" se separan los prácticamente terminados (avance >= 95 %), que ya no necesitan fondos.
# ============================================================
pmi_futuro = inv[["pmi_1", "pmi_2", "pmi_3", "pmi_4"]].fillna(0).sum(axis=1)
ind["programado_anios_siguientes"] = pmi_futuro

def financiamiento(f, futuro):
    if f["pim_2026"] > 0:
        return "Con presupuesto 2026"
    if futuro > 0:
        return "Solo programado para años siguientes"
    return "Sin financiamiento – prácticamente terminado" if f["avance"] >= 95 else "Sin financiamiento – le falta ejecutar"
ind["financiamiento"] = [financiamiento(f, fut) for (_, f), fut in zip(ind.iterrows(), pmi_futuro)]
ind["con_financiamiento"] = ind["financiamiento"].isin(["Con presupuesto 2026", "Solo programado para años siguientes"])
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
    }
    fila["pct_cumple_programacion"] = proporcion(fila["devengado_ene_oct"], fila["programado_ene_oct"])
    # P5: tres grupos con su número, costo y saldo
    for grupo, clave in [("Con presupuesto 2026", "con_pim"), ("Solo programado para años siguientes", "solo_programado"),
                         ("Sin financiamiento – le falta ejecutar", "sin_fin_falta"),
                         ("Sin financiamiento – prácticamente terminado", "sin_fin_terminado")]:
        m = g["financiamiento"] == grupo
        fila[f"n_{clave}"], fila[f"costo_{clave}"], fila[f"saldo_{clave}"] = int(m.sum()), g.loc[m, "costo"].sum(), g.loc[m, "saldo_total"].sum()
    fila["pct_n_con_financiamiento"] = g["con_financiamiento"].mean()
    fila["pct_costo_con_financiamiento"] = proporcion(g.loc[g["con_financiamiento"], "costo"].sum(), g["costo"].sum())
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
    *[f"| {g} | {n(t['n_' + k])} | {millones(t['costo_' + k])} | {millones(t['saldo_' + k])} |" for g, k in [
        ("Con presupuesto 2026", "con_pim"), ("Solo programado para años siguientes", "solo_programado"),
        ("Sin financiamiento – le falta ejecutar", "sin_fin_falta"), ("Sin financiamiento – prácticamente terminado", "sin_fin_terminado")]],
    "", f"Con financiamiento (las dos primeras filas): **{pct(t['pct_n_con_financiamiento'])} de las inversiones y {pct(t['pct_costo_con_financiamiento'])} del costo**.", "",
    "### P7. Atraso",
    f"- Atrasadas: **{n(t['n_atrasados'])}**; mediana de **{t['mediana_meses_atraso']:.0f} meses**; más de 1 año: {n(t['n_atraso_mas_12'])}; "
    f"más de 3 años: **{n(t['n_atraso_mas_36'])}**.",
    "- Se mide contra la última fecha de fin registrada; el atraso frente al plan original puede ser mayor.",
    f"- Programación 2026 (12-B): de enero a octubre se programó {millones(t['programado_ene_oct'])} y se gastó "
    f"{millones(t['devengado_ene_oct'])} (**{pct(t['pct_cumple_programacion'])}**). {n(t['n_bajo_70_programacion'])} inversiones gastaron menos del 70 % de lo programado.", "",
    "## Por ministerio o entidad (de mayor a menor costo)", "",
    "| Ministerio o entidad | Inversiones | Costo | Con brecha | Falta gastar 2026 | Desviación del costo | Reportan problemas | Con financiamiento | Atrasadas (mediana) |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for _, f in cartera[cartera["sector"] != TODO].sort_values("costo", ascending=False).iterrows():
    mediana = f"{f['mediana_meses_atraso']:.0f} m" if pd.notna(f["mediana_meses_atraso"]) else "—"
    nombre = " ".join(p if i == 0 or p not in ("Y", "De", "Del", "La", "E") else p.lower()
                      for i, p in enumerate(f["sector"].title().split()))   # "Desarrollo E Inclusion" -> "Desarrollo e Inclusion"
    lineas.append(f"| {nombre} | {n(f['n'])} | {millones(f['costo'])} | {pct(f['pct_con_brecha'])} | {pct(f['pct_pendiente_2026'])} "
                  f"| {pct(f['pct_desv_total'])} | {n(f['n_reporta_problemas'])} | {pct(f['pct_n_con_financiamiento'])} | {n(f['n_atrasados'])} ({mediana}) |")
lineas += ["", "## Definiciones y advertencias", "",
           "- **Fuentes:** Detalle de inversiones, Inversiones y brechas y Formato 12-B (MEF, Datos Abiertos). El diccionario del MEF da error 404: "
           "el significado de algunas columnas (programación mensual del 12-B, `PMI_ANIO_1` a `4`) se dedujo de su nombre.",
           "- **P2:** pendiente 2026 = PIM − devengado 2026 (solo inversiones con PIM > 0). Saldo total = `SALDO_EJECUTAR` del MEF.",
           "- **P3:** solo inversiones con monto viable y costo actualizado mayores que 0. Desviación = costo actualizado − monto viable.",
           "- **P4:** reglas de palabras sobre el último texto de problemas del 12-B; son aproximadas y es lo que la entidad reporta. "
           "Son problemas actuales, no riesgos con probabilidad e impacto.",
           "- **P5:** \"programado para años siguientes\" = suma de `PMI_ANIO_1` a `PMI_ANIO_4` mayor que 0. La fuente del dinero no está en estos archivos.",
           "- **P7:** atraso = meses desde la fecha de fin registrada, si ya pasó y el avance es menor a 95 %. "
           "Programación mensual: devengado de enero a octubre ÷ lo programado para esos meses."]
(DOCS / "indicadores_resultados.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
print("7.10 Informe escrito en docs/indicadores_resultados.md")
