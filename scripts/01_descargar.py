# ============================================================
# PROCESO 1: Descargar los datos abiertos del MEF
# Insumo:    tres archivos públicos del Portal de Datos Abiertos del MEF (se actualizan a diario)
# Resultado: data/crudo/DETALLE_INVERSIONES.csv (≈248 MB), INVERSIONES_BRECHAS.csv (≈100 MB) y FORMATO_12B.csv (≈189 MB)
# Uso:       python scripts/01_descargar.py
# ============================================================

# --- Paquetes (todos vienen con Python) ---
# pathlib: rutas de archivos · urllib: descargar desde internet · shutil: copiar la descarga al disco por partes
from pathlib import Path
import shutil
import urllib.request

CRUDO = Path(__file__).resolve().parents[1] / "data" / "crudo"
CRUDO.mkdir(parents=True, exist_ok=True)
BASE = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/"

# Qué contiene cada archivo (los diccionarios de variables del MEF no están disponibles: el enlace da error 404)
ARCHIVOS = {
    "DETALLE_INVERSIONES.csv": "una fila por inversión activa: costo, presupuesto, gasto, fechas, ubicación, responsables",
    "INVERSIONES_BRECHAS.csv": "una o más filas por inversión: la brecha que cierra y cuánto aporta",
    "FORMATO_12B.csv": "una fila por inversión: último seguimiento (situación, problemas, acciones) y gasto mensual",
}

for nombre, descripcion in ARCHIVOS.items():
    destino = CRUDO / nombre
    print(f"Descargando {nombre}: {descripcion}")
    # urlopen(): abre la conexión · copyfileobj(): guarda el archivo por partes, sin cargarlo entero en memoria
    #   Antes: archivo en el servidor del MEF | Después: archivo en data/crudo/
    with urllib.request.urlopen(BASE + nombre, timeout=600) as respuesta, open(destino, "wb") as salida:
        shutil.copyfileobj(respuesta, salida)
    print(f"  listo: {destino.stat().st_size / 1e6:.0f} MB")
