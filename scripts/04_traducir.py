# ============================================================
# PROCESO 4: Traducir cada inversión a cinco preguntas en lenguaje simple
# Insumo:    data/procesado/inversiones.parquet
# Resultado: data/procesado/cinco_preguntas.parquet, con las columnas:
#            que_es, problema, cuanto, cuando, estado, estado_motivo (y los datos para mostrarlas)
#            Versión con REGLAS. Cuando haya API de IA, la IA reescribirá "que_es" y "problema".
# Uso:       uv run --with pandas --with pyarrow python scripts/04_traducir.py
# ============================================================

# --- Paquetes ---
# pathlib, re: rutas y búsqueda de patrones en el texto (vienen con Python)
# pandas: tablas
from pathlib import Path
import re
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "procesado"
HOY = pd.Timestamp("2026-11-10")
CIERRE_ANIO = pd.Timestamp("2026-12-31")
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

base = pd.read_parquet(PROCESADO / "inversiones.parquet")
# El único CUI repetido (2022788) tiene dos filas distintas: se les da un identificador propio a cada una
base["id"] = base["id"] + base.groupby("id").cumcount().map(lambda n: "" if n == 0 else f"-{n + 1}")

# ============================================================
# PASO 4.1: Ayudas de redacción
# ============================================================
SIGLAS = ["CIAI", "ULE", "MIDIS", "SINAFO", "PNCM", "FONCODES", "PAIS", "PGH", "I.E.", "IE", "EsSalud", "MINSA", "MTC", "SUNAT",
          "INPE", "PNP", "UGEL", "SEDAPAL", "TI", "UPS", "RCC", "APP", "SS.HH."]
MENORES = {"de", "del", "la", "las", "los", "y", "el", "en", "a", "e"}

def titulo(s):
    """'VILLA EL SALVADOR' -> 'Villa el Salvador' (para lugares)."""
    palabras = str(s or "").lower().split()
    return " ".join(p if (i > 0 and p in MENORES) else p[:1].upper() + p[1:] for i, p in enumerate(palabras))

def oracion(s):
    """'MEJORAMIENTO DEL CIAI' -> 'Mejoramiento del CIAI' (primera letra en mayúscula y siglas conocidas)."""
    t = str(s or "").lower()
    t = t[:1].upper() + t[1:]
    for g in SIGLAS:
        t = re.sub(r"\b" + re.escape(g.lower()) + r"(?=\b|\s|$)", g, t)
    t = re.sub(r"cion\b", "ción", t)                       # el MEF publica "CREACION": toda palabra en -cion lleva tilde
    t = re.sub(r"\btambo\b", "Tambo", t)
    t = re.sub(r"\bdel estado\b", "del Estado", t)
    return t

def millones(x):
    """1 853 953 -> 'S/ 1.9 millones'; 850 000 -> 'S/ 850 mil'."""
    if pd.isna(x):
        return "sin dato"
    if x >= 1e9:
        return f"S/ {x / 1e9:,.1f} mil millones"
    if x >= 1e6:
        return f"S/ {x / 1e6:,.1f} millones"
    return f"S/ {x / 1e3:,.0f} mil"

def mes_anio(f):
    return f"{MESES[f.month - 1]} de {f.year}"

def meses_entre(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)

# ============================================================
# PASO 4.2: ¿Qué es?  (nombre corto + lugar)
#   Antes: "CREACION DEL SERVICIO ... EN EL CENTRO POBLADO X, DISTRITO DE Y, PROVINCIA ..., DEPARTAMENTO ..."
#   Después: "Creación del servicio ..." + "Y, Departamento"
# ============================================================
CORTE = re.compile(r"\s*,?\s+(?:DE CENTRO POBLADO|EN EL CENTRO POBLADO|EN LA LOCALIDAD|DE LA LOCALIDAD|DISTRITO DE|"
                   r"EN EL DISTRITO|DEL DISTRITO|PROVINCIA DE|EN EL\(LA\)|- DISTRITO|, DISTRITO)\b.*$", re.I)
TIPOS = [(r"IOARR", "Inversión menor: reposición, ampliación o equipamiento"),
         (r"IRI", "Reconstrucción después de un desastre"),
         (r"PROGRAMA", "Programa de inversión (agrupa varios proyectos)"),
         (r"EMBLEMATICO", "Proyecto emblemático"),
         (r".", "Proyecto")]

def que_es(f):
    corto = CORTE.sub("", f["nombre"]).strip(" ,-")
    corto = oracion(corto if len(corto) >= 25 else f["nombre"])
    if len(corto) > 140:
        corto = corto[:137].rsplit(" ", 1)[0] + "…"
    return corto

def lugar(f):
    d = f["departamento"]
    if not d or re.search(r"MUL|TODOS|NACIONAL", d, re.I):
        return "Varios departamentos"
    dist = f["distrito"] if f["distrito"] and not re.search(r"TODOS|MUL", f["distrito"], re.I) else ""
    return (titulo(dist) + ", " if dist else "") + titulo(d)

def tipo_simple(t):
    return next(etq for patron, etq in TIPOS if re.search(patron, t or "", re.I))

# ============================================================
# PASO 4.3: ¿Qué problema resuelve?  (desde la brecha)
#   Antes: "PORCENTAJE DE LOCALES EDUCATIVOS ... CON CAPACIDAD INSTALADA INADECUADA (LEEPCII)."
#   Después: "Mejora locales educativos ... que hoy están en malas condiciones."
# ============================================================
PLANTILLAS = [
    (r"^PORCENTAJE DE (.+?) (?:QUE (?:CONTIENE|CUENTAN? CON) )?(?:CON )?(?:CAPACIDAD INSTALADA INADECUADA|EN CONDICIONES INADECUADAS|"
     r"QUE OPERAN EN CONDICIONES INADECUADAS|CON INADECUAD[OA]S? .+|INADECUAD[OA]S?|QUE NO FUNCIONAN ADECUADAMENTE|CON CAPACIDAD OPERATIVA INADECUADA)\.?$",
     "Mejora {x} que hoy están en malas condiciones."),
    (r"^PORCENTAJE DE (.+?) (?:SIN|QUE NO CUENTA[N]? CON|NO ATENDID[OA]S? (?:CON|POR)) (.+?)\.?$", "Lleva {y} a {x} que hoy no lo tienen."),
    (r"^PORCENTAJE DE (.+?) POR IMPLEMENTAR\.?$", "Crea {x} que todavía faltan."),
    (r"^PORCENTAJE DE (.+?) (?:POR|QUE REQUIEREN|QUE NECESITAN) (.+?)\.?$", "Atiende {x} que requieren {y}."),
]

def problema(f):
    b = f["brecha"]
    if not isinstance(b, str) or not b:
        return "No tiene una brecha registrada."
    limpio = re.sub(r"\s*\([A-ZÑ]{3,}\)\s*", " ", b).strip()           # quita siglas como (LEEPCII)
    frase = None
    for patron, molde in PLANTILLAS:
        m = re.match(patron, limpio, re.I)
        if m:
            x = m.group(1).lower()
            y = m.group(2).lower() if m.lastindex and m.lastindex >= 2 else ""
            frase = molde.format(x=x, y=y)
            break
    if frase is None:
        frase = "Contribuye a reducir: " + limpio.lower().rstrip(".") + "."
    frase = oracion(frase)                                    # mayúscula inicial, siglas y tildes, antes de agregar el aporte
    aporte, unidad = f["brecha_aporte"], f["brecha_unidad"]
    if pd.notna(aporte) and aporte > 0 and isinstance(unidad, str) and unidad and "DEFINIR" not in unidad:
        if re.match(r"PERSONA|POBLACI", unidad, re.I):
            frase += f" Beneficia a {aporte:,.0f} personas."
        else:
            frase += f" Aporta {aporte:,.0f} {unidad.lower()}."
    return frase

# ============================================================
# PASO 4.4: ¿Cuánto cuesta y cuánto se ha gastado?
# ============================================================
def cuanto(f):
    costo, gastado = f["costo"], f["dev_acumulado"]
    pct = (100 * gastado / costo) if costo and costo > 0 else None
    if pct is None:
        gasto = ""
    elif not gastado:
        gasto = "Aún no se ha gastado nada."
    else:
        gasto = f"Se ha gastado {millones(gastado)} ({pct:.0f} %)."
    t = f"Cuesta {millones(costo)}. " + gasto
    # El cambio de costo desde que se aprobó (subió o bajó) lo calcula el Proceso 7 (frase_costo) y la app lo agrega aquí
    return t.strip()

# Avance de la inversión, en %. Antes se tomaba el MAYOR entre el avance físico y el % gastado: eso mezclaba avance y
# dinero, y escondía los proyectos que gastaron mucho y avanzaron poco (p. ej., 97 % gastado y 45 % declarado).
# Ahora:
#   1) el avance de ejecución que la entidad declaró en el último año (todos los componentes), si es mayor que 0;
#   2) si no hay una declaración reciente, el % gastado del costo (devengado / costo), como aproximación.
DECLARACION_RECIENTE = HOY - pd.DateOffset(years=1)

def avance_declarado(f):
    """True si la entidad declaró su avance en el último año y el valor es mayor que 0."""
    return (pd.notna(f["avance_ejecucion"]) and f["avance_ejecucion"] > 0
            and pd.notna(f["fecha_declaracion"]) and f["fecha_declaracion"] >= DECLARACION_RECIENTE)

def avance(f):
    if avance_declarado(f):
        return f["avance_ejecucion"]
    gastado = 100 * f["dev_acumulado"] / f["costo"] if f["costo"] and f["costo"] > 0 else 0
    return min(gastado, 100)

def avance_fuente(f):
    return "declarado por la entidad" if avance_declarado(f) else "según lo gastado"

# ============================================================
# PASO 4.5: ¿Cuándo termina?  (periodo de ejecución + cómo está respecto de su fecha de fin)
#   Antes: inicio = 2016-02-01, fin = 2018-02-01
#   Después: "febrero 2016 – febrero 2018 (24 meses). Debía terminar en febrero de 2018: lleva ..."
# ============================================================
def periodo(f):
    """Periodo de ejecución registrado y su duración en meses (días / 30,44, redondeado)."""
    ini, fin = f["inicio"], f["fin"]
    if pd.isna(ini) or pd.isna(fin):
        return "No se consigna información sobre su duración."
    if fin < ini:   # 12 casos: el fin registrado es anterior al inicio (p. ej., inicio digitado como 2069)
        return "Las fechas de inicio y fin registradas no son coherentes."
    meses = round((fin - ini).days / 30.44)
    duracion = "menos de 1 mes" if meses == 0 else ("1 mes" if meses == 1 else f"{meses} meses")
    return f"{MESES[ini.month - 1]} {ini.year} – {MESES[fin.month - 1]} {fin.year} ({duracion})."

def cuando(f):
    return f"{periodo(f)} {situacion_plazo(f)}".strip()

def situacion_plazo(f):
    fin = f["fin"]
    if pd.isna(fin):
        return ""
    if fin >= HOY:
        m = meses_entre(HOY, fin)
        resto = "este mes" if m == 0 else (f"faltan {m} meses" if m < 24 else f"faltan {m // 12} años")
        return f"Debe terminar en {mes_anio(fin)} ({resto})."
    if avance(f) >= 95:
        return f"Debía terminar en {mes_anio(fin)} y está prácticamente terminado, pero no se ha cerrado."
    m = meses_entre(fin, HOY)
    atraso = f"{m} meses" if m < 24 else f"{m // 12} años"
    return f"Debía terminar en {mes_anio(fin)}: lleva {atraso} de retraso según las fechas registradas."

# ============================================================
# PASO 4.6: ¿Cómo va?  (un estado en palabras simples y su motivo)
#   Orden de prioridad: Atrasado > En riesgo este año > Sin reportes recientes > Por cerrar > Sin presupuesto este año > En marcha
#   Reglas de ejemplo, por validar con el usuario.
# ============================================================
DIAS_AL_CIERRE = (CIERRE_ANIO - HOY).days

def estado(f):
    av, fin, pim, dev26 = avance(f), f["fin"], f["pim_2026"] or 0, f["dev_2026"] or 0
    empezado = (f["dev_acumulado"] or 0) > 0
    if pd.notna(fin) and fin < HOY and av < 95:
        return "Atrasado", f"Su plazo venció en {mes_anio(fin)} y tiene {av:.0f} % de avance."
    if pim > 0 and dev26 / pim < 0.5:
        return "En riesgo este año", f"Le faltan {millones(pim - dev26)} por gastar de su presupuesto 2026 en {DIAS_AL_CIERRE} días."
    if empezado and av < 95 and (pd.isna(f["fecha_12b"]) or (HOY - f["fecha_12b"]).days > 180):
        cuando_ = f"desde {mes_anio(f['fecha_12b'])}" if pd.notna(f["fecha_12b"]) else "nunca"
        return "Sin reportes recientes", f"Está en marcha, pero la entidad no informa su avance {cuando_}."
    if av >= 95:
        return "Por cerrar", "Está prácticamente terminado; falta el cierre formal."
    if not empezado and pim == 0:
        return "Sin presupuesto este año", "Está aprobado, pero no ha empezado y no tiene presupuesto en 2026."
    return "En marcha", "Avanza sin alertas con las reglas actuales."

# ============================================================
# PASO 4.7: Aplicar a todas las inversiones y guardar
# ============================================================
salida = base.copy()
salida["que_es"] = salida.apply(que_es, axis=1)
salida["lugar"] = salida.apply(lugar, axis=1)
salida["tipo_simple"] = salida["tipo"].map(tipo_simple)
salida["problema"] = salida.apply(problema, axis=1)
salida["cuanto"] = salida.apply(cuanto, axis=1)
salida["avance"] = salida.apply(avance, axis=1)
salida["avance_fuente"] = salida.apply(avance_fuente, axis=1)
salida["cuando"] = salida.apply(cuando, axis=1)
salida[["estado", "estado_motivo"]] = salida.apply(lambda f: pd.Series(estado(f)), axis=1)
salida.to_parquet(PROCESADO / "cinco_preguntas.parquet", index=False)

# Verificación: cómo quedan repartidos los estados y tres ejemplos
print("Estados:\n", salida["estado"].value_counts().to_string())
print("Problemas que usaron una plantilla:", int((~salida["problema"].str.startswith(("Contribuye", "No tiene"))).sum()), "de", len(salida))
for cui in ["2613205", "2534846", "2702890"]:
    f = salida[salida["cui"] == cui].iloc[0]
    print(f"\n[{cui}] ¿Qué es? {f.que_es} · {f.lugar}\n  ¿Qué problema? {f.problema}\n  ¿Cuánto? {f.cuanto}\n  ¿Cuándo? {f.cuando}\n  ¿Cómo va? {f.estado}: {f.estado_motivo}")
