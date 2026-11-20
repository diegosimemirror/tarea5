# ============================================================
# PROCESO 9: Gasto de las empresas públicas (EsSalud, FONAFE y otras que no usan el SIAF)
# Insumo:    data/procesado/inversiones.parquet (Proceso 3), para saber qué inversiones consultar, y el servicio público
#            del MEF que alimenta la sección «I. Información financiera – Empresas públicas» de la consulta SSI
#            (https://ofi5.mef.gob.pe/invierteWS/Ssi/traeFonafeSSI, una consulta por inversión)
# Resultado: data/procesado/gasto_empresas.parquet: una fila por inversión consultada, con su gasto acumulado, su gasto
#            y presupuesto 2026, su gasto mes a mes de 2026 y el mes hasta el que llega el dato.
#            Las respuestas del MEF se guardan en data/crudo/empresas/ (no se suben); si ya están, no se vuelven a pedir.
# Uso:       uv run --with pandas --with pyarrow python scripts/09_gasto_empresas.py
#            (≈ 2 000 consultas, una tras otra, con una pausa entre cada una: ≈ 20 minutos la primera vez)
#            Prueba con pocas inversiones: ... python scripts/09_gasto_empresas.py --prueba 20 (no guarda el parquet)
# Por qué:   EsSalud y las empresas de FONAFE no registran su gasto en el SIAF, así que en DETALLE_INVERSIONES su
#            devengado y su PIM vienen en 0. La app mostraba 0 % de ejecución en proyectos casi terminados (p. ej., el
#            Hospital del Altiplano de Puno, CUI 2300016: 95 % gastado según FONAFE). Este proceso trae ese gasto.
# ============================================================

# --- Paquetes ---
# pathlib, json, sys, time, urllib: rutas, leer las respuestas, leer la opción --prueba, pausar entre consultas y
#   consultar al MEF (vienen con Python)
# pandas: tablas; pyarrow: guardar en parquet (se instalan una vez)
from pathlib import Path
import json
import sys
import time
import urllib.parse
import urllib.request
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "procesado"
RESPUESTAS = RAIZ / "data" / "crudo" / "empresas"
RESPUESTAS.mkdir(parents=True, exist_ok=True)
URL = "https://ofi5.mef.gob.pe/invierteWS/Ssi/traeFonafeSSI"
ANIO = 2026
PAUSA = 0.3          # segundos entre consultas, para no recargar el servidor del MEF
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# ============================================================
# PASO 9.1: Elegir las inversiones que se consultan
#   Las de EsSalud y FONAFE (por sector) y las de empresas públicas que figuran en otros sectores (SEDAPAL, CORPAC,
#   EGASA, Electro Sur Este). Se excluyen las que ya tienen gasto o presupuesto en el SIAF: su dato ya está completo.
#   Antes: 26 412 inversiones | Después: ≈ 1 950 inversiones por consultar
# ============================================================
inv = pd.read_parquet(PROCESADO / "inversiones.parquet")
empresa = inv["sector"].isin(["ESSALUD", "FONAFE"]) | inv["entidad"].str.contains(r"S\.A|EMPRESA|SEDAPAL|S\.R\.L", regex=True)
con_siaf = (inv["dev_acumulado"].fillna(0) > 0) | (inv["pim_2026"].fillna(0) > 0)
cuis = sorted(set(inv.loc[empresa & ~con_siaf & (inv["cui"] != ""), "cui"]))
PRUEBA = int(sys.argv[sys.argv.index("--prueba") + 1]) if "--prueba" in sys.argv else None
if PRUEBA:                                                  # prueba: el Hospital del Altiplano y las N - 1 primeras
    cuis = ["2300016"] + [c for c in cuis if c != "2300016"][:PRUEBA - 1]
print("9.1 Inversiones de empresas públicas:", int(empresa.sum()), "| con gasto en el SIAF (no se consultan):",
      int((empresa & con_siaf).sum()), "| por consultar:", len(cuis))

# ============================================================
# PASO 9.2: Consultar al MEF, una inversión a la vez (y guardar cada respuesta)
#   consultar(): Antes: el CUI '2300016' | Después: la lista de filas que devuelve el MEF (una por empresa y año reportado)
#   tipo=FINAN es la consulta que usa la página del SSI: trae el último reporte, con el gasto de cada mes de ese año,
#   el acumulado de toda la vida, el presupuesto inicial (PIA) y el modificado (PIM)
# ============================================================
def consultar(cui, intentos=3):
    archivo = RESPUESTAS / f"{cui}.json"
    if archivo.exists():                                   # ya se consultó antes: no se vuelve a pedir
        return json.loads(archivo.read_text(encoding="utf-8"))
    datos = urllib.parse.urlencode({"id": cui, "tipo": "FINAN"}).encode()
    for intento in range(1, intentos + 1):
        try:
            pedido = urllib.request.Request(URL, data=datos, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(pedido, timeout=60) as respuesta:
                filas = json.loads(respuesta.read().decode("utf-8"))
            archivo.write_text(json.dumps(filas, ensure_ascii=False), encoding="utf-8")
            time.sleep(PAUSA)
            return filas
        except Exception as error:                        # corte de red o servidor ocupado: se espera y se reintenta
            print(f"    {cui}: intento {intento} falló ({error})")
            time.sleep(5 * intento)
    return None                                           # no respondió: queda como "no consultado"

respuestas = {}
inicio = time.time()
for i, cui in enumerate(cuis, 1):
    respuestas[cui] = consultar(cui)
    if i % 100 == 0 or i == len(cuis):
        print(f"9.2 Consultadas {i} de {len(cuis)} ({(time.time() - inicio) / 60:.1f} min)", flush=True)

# ============================================================
# PASO 9.3: Resumir cada respuesta en una fila
#   Se suman las filas de una misma inversión, como hace la página del SSI (una inversión puede tener más de una fila).
#   Solo cuentan los meses hasta el mes reportado (mesEje): los meses siguientes del año traen montos que aún no son gasto.
#   Presupuesto 2026: el modificado (PIM) si la empresa lo reportó; si no, el inicial (PIA).
#   Antes: [{"anioEje": "2026", "mesEje": "9", "enero": 0, "febrero": 10400, ..., "sumaTotalEjecAlMes": 366646018}]
#   Después: gasto_acumulado = 366 646 018 · gasto_2026 = 22 504 219 · corte = septiembre de 2026
# ============================================================
def resumir(cui, filas):
    fila = {"cui": cui, "consultado": filas is not None, "con_dato": bool(filas)}
    if not filas:
        return fila
    anio_corte, mes_corte = max((int(f["anioEje"]), int(f["mesEje"])) for f in filas)
    del_anio = [f for f in filas if int(f["anioEje"]) == ANIO]
    pim = sum(f["pimHistoricoPorAnio"] or 0 for f in del_anio)
    pia = sum(f["piaHistoricoPorAnio"] or 0 for f in del_anio)
    fila.update({
        "empresa": ", ".join(sorted({f["siglas"] for f in filas})),
        "anio_corte": anio_corte, "mes_corte": mes_corte,
        "gasto_acumulado": float(sum(f["sumaTotalEjecAlMes"] or 0 for f in filas)),
        "gasto_2026": float(sum(f["totalEjecutadoAlMes"] or 0 for f in del_anio)),
        "presupuesto_2026": float(pim if pim > 0 else pia),
        "presupuesto_2026_tipo": "modificado (PIM)" if pim > 0 else ("inicial (PIA)" if pia > 0 else ""),
    })
    for m, nombre in enumerate(MESES, 1):              # gasto de cada mes de 2026, solo hasta el mes reportado
        fila[f"gasto_2026_{m:02d}"] = float(sum((f[nombre] or 0) for f in del_anio if m <= int(f["mesEje"])))
    return fila

gasto = pd.DataFrame([resumir(cui, filas) for cui, filas in respuestas.items()])

# ============================================================
# PASO 9.3b: Corregir acumulados imposibles
#   Lo gastado en toda la vida no puede ser menor que lo gastado en 2026. En 4 inversiones de empresas eléctricas
#   (consulta del 19/11/2026: 2513625, 2522048, 2652824 y 2674874) el MEF reporta un acumulado menor: se usa lo gastado
#   en 2026 como acumulado (el mínimo posible) y se conserva el valor original en gasto_acumulado_original.
#   Antes (2652824): acumulado S/ 17 689, 2026 S/ 35 378 | Después: acumulado S/ 35 378
# ============================================================
gasto["gasto_acumulado_original"] = gasto.get("gasto_acumulado")
imposible = gasto["con_dato"] & (gasto["gasto_acumulado"] + 1 < gasto["gasto_2026"])
gasto.loc[imposible, "gasto_acumulado"] = gasto.loc[imposible, "gasto_2026"]
print("9.3b Acumulado menor que el gasto 2026 (corregidos):", int(imposible.sum()), gasto.loc[imposible, "cui"].tolist())

# ============================================================
# PASO 9.4: Verificar y guardar
#   El gasto de 2026 debe ser igual a la suma de sus meses; el acumulado no puede ser menor que lo gastado en 2026
# ============================================================
con = gasto[gasto["con_dato"]]
meses_cols = [f"gasto_2026_{m:02d}" for m in range(1, 13)]
assert (con[meses_cols].sum(axis=1) - con["gasto_2026"]).abs().max() < 1, "el gasto 2026 no cuadra con sus meses"
assert (con["gasto_acumulado"] + 1 >= con["gasto_2026"]).all(), "hay un acumulado menor que el gasto 2026"
print("9.4 Con dato de FONAFE:", len(con), "de", len(gasto), "| sin respuesta del MEF:", int((~gasto["consultado"]).sum()),
      "| gasto acumulado:", f"S/ {con['gasto_acumulado'].sum() / 1e9:,.2f} mil millones",
      "| mes de corte más frecuente:", con[["anio_corte", "mes_corte"]].value_counts().head(3).to_dict())
ejemplo = gasto[gasto["cui"] == "2300016"]
if len(ejemplo):
    e = ejemplo.iloc[0]
    print(f"    Ejemplo 2300016 (Hospital del Altiplano, Puno): acumulado S/ {e.gasto_acumulado:,.0f}, 2026 S/ {e.gasto_2026:,.0f}, "
          f"presupuesto 2026 S/ {e.presupuesto_2026:,.0f} ({e.presupuesto_2026_tipo}), corte {MESES[int(e.mes_corte) - 1]} {int(e.anio_corte)}")
if PRUEBA:
    print("    Prueba: no se guarda el parquet.")
else:
    gasto.to_parquet(PROCESADO / "gasto_empresas.parquet", index=False)
    print("    Guardado:", gasto.shape, "->", PROCESADO / "gasto_empresas.parquet")
