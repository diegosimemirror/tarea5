# ============================================================
# PROCESO 11: Último 12-B en vivo de las inversiones de EsSalud (consulta del MEF, una por inversión)
# Insumo:    data/crudo/DETALLE_INVERSIONES.csv (Proceso 1), para saber qué inversiones consultar, y el servicio público del
#            MEF que alimenta la página del formato 12-B (https://ofi5.mef.gob.pe/invierteWS/Ssi/traeInfSeguimF12B)
# Resultado: data/procesado/f12b_en_vivo.parquet: una fila por inversión con su situación actual (con su CATEGORÍA, p. ej.
#            «Inversión culminada / 100% ejecutada físicamente»), sus problemas, sus PRÓXIMOS PASOS (p. ej., «Registrar
#            cierre de inversión») y la fecha de su último 12-B. Nombres y correos ya ocultos (módulo privacidad.py).
#            Las respuestas del MEF se guardan en data/crudo/f12b_vivo/<fecha>/ (no se suben).
# Uso:       uv run --with "pandas<3" --with pyarrow python scripts/11_12b_en_vivo.py      (≈ 800 consultas, ≈ 16 min)
# Por qué:   1) el archivo de datos abiertos del 12-B no trae la categoría ni los próximos pasos, que son las señales más
#               claras de que una inversión ya se ejecutó (se usan en el Proceso 10);
#            2) desde el 18/11/2026 el MEF publica ese archivo vacío (solo la fila de títulos).
#            Se consulta EsSalud porque es la cartera que se revisó a mano; el resto usa el archivo de datos abiertos.
# ============================================================

# --- Paquetes ---
# pathlib, json, re, sys, time, datetime, urllib: rutas, leer respuestas, limpiar texto, pausas, la fecha y consultar
#   al MEF (vienen con Python) · pandas: tablas · privacidad: ocultar nombres y correos (scripts/privacidad.py)
from pathlib import Path
import json
import re
import sys
import time
import datetime
import urllib.parse
import urllib.request
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from privacidad import ocultar

RAIZ = Path(__file__).resolve().parents[1]
CRUDO, PROCESADO = RAIZ / "data" / "crudo", RAIZ / "data" / "procesado"
HOY = datetime.date.today().isoformat()
RESPUESTAS = CRUDO / "f12b_vivo" / HOY
RESPUESTAS.mkdir(parents=True, exist_ok=True)
URL = "https://ofi5.mef.gob.pe/invierteWS/Ssi/traeInfSeguimF12B"
PAUSA = 0.3   # segundos entre consultas, para no recargar el servidor del MEF

# ============================================================
# PASO 11.1: Elegir las inversiones: las de EsSalud del gobierno nacional (sector ESSALUD o unidad de inversiones de EsSalud)
#   Antes: ≈ 150 000 inversiones del país | Después: ≈ 800 de EsSalud
# ============================================================
detalle = pd.read_csv(CRUDO / "DETALLE_INVERSIONES.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False,
                      usecols=["NIVEL", "SECTOR", "NOMBRE_UEI", "CODIGO_UNICO"])
essalud = detalle[detalle["NIVEL"].isin(["GN", "GR"]) & ((detalle["SECTOR"] == "ESSALUD") | detalle["NOMBRE_UEI"].str.contains("ESSALUD"))]
cuis = sorted(set(essalud["CODIGO_UNICO"]) - {""})
print("11.1 Inversiones de EsSalud por consultar:", len(cuis))

# ============================================================
# PASO 11.2: Consultar una a la vez (y guardar cada respuesta; si ya está guardada hoy, no se vuelve a pedir)
#   La respuesta viene en UTF-8; si no, en Windows-1252 (así las tildes no se dañan)
# ============================================================
def consultar(cui, intentos=3):
    archivo = RESPUESTAS / f"{cui}.json"
    if archivo.exists():
        return json.loads(archivo.read_text(encoding="utf-8"))
    for intento in range(1, intentos + 1):
        try:
            pedido = urllib.request.Request(URL, data=urllib.parse.urlencode({"id": cui}).encode(),
                                            headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(pedido, timeout=60) as respuesta:
                crudo = respuesta.read()
            try:
                texto = crudo.decode("utf-8")
            except UnicodeDecodeError:
                texto = crudo.decode("cp1252")
            archivo.write_text(texto, encoding="utf-8")
            time.sleep(PAUSA)
            return json.loads(texto)
        except Exception as error:
            print(f"    {cui}: intento {intento} falló ({error})", flush=True)
            time.sleep(5 * intento)
    return None

inicio = time.time()
respuestas = {}
for i, cui in enumerate(cuis, 1):
    respuestas[cui] = consultar(cui)
    if i % 100 == 0 or i == len(cuis):
        print(f"11.2 Consultadas {i} de {len(cuis)} ({(time.time() - inicio) / 60:.1f} min)", flush=True)

# ============================================================
# PASO 11.3: Una fila por inversión, con los textos sin la fecha inicial y sin datos personales
#   Antes: '[09/11/2026]  - En proceso de recepción / conformidad técnica <br>EJECUTADO, SEGÚN LO INFORMADO POR CEABE'
#   Después: 'En proceso de recepción / conformidad técnica <br>EJECUTADO, SEGÚN LO INFORMADO POR CEABE'
#   (se conserva «<br>», que separa la categoría del detalle: el Proceso 10 los lee por separado)
# ============================================================
def limpiar(t):
    t = re.sub(r"^\s*\[[^\]]*\]\s*-?\s*", "", str(t or ""))
    return ocultar(re.sub(r"[ \t\r\n]+", " ", t).strip())

def fecha_net(x):
    """'/Date(1794200400000)/' -> 2026-11-09 (hora de Lima)."""
    m = re.search(r"\d+", str(x or ""))
    return pd.Timestamp(int(m.group()), unit="ms").tz_localize("UTC").tz_convert("America/Lima").tz_localize(None) if m else pd.NaT

filas = []
for cui, r in respuestas.items():
    if not r:                      # sin 12-B en el MEF, o no respondió
        continue
    d = r[0]
    filas.append({"cui": cui, "fecha_12b": fecha_net(d.get("FECHA_ULT_ACT_F12B")),
                  "situacion_12b": limpiar(d.get("ULT_ESTADO_SITUACIONAL")), "problema_12b": limpiar(d.get("ULT_PROBLEMA")),
                  "acciones_12b": limpiar(d.get("PROB_ET_1")), "consultado": HOY})
vivo = pd.DataFrame(filas)

# Verificación: sin caracteres dañados, una fila por inversión, y cuántas no respondieron
assert vivo["cui"].is_unique, "CUI repetido"
danados = vivo[["situacion_12b", "problema_12b", "acciones_12b"]].apply(lambda s: s.str.contains("�")).any(axis=1).sum()
print("11.3 Con 12-B:", len(vivo), "| sin 12-B:", sum(1 for r in respuestas.values() if r == []),
      "| sin respuesta:", sum(1 for r in respuestas.values() if r is None), "| textos con caracteres dañados:", int(danados))
vivo.to_parquet(PROCESADO / "f12b_en_vivo.parquet", index=False)
print("    Guardado:", vivo.shape, "->", PROCESADO / "f12b_en_vivo.parquet")
