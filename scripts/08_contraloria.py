# ============================================================
# PROCESO 8: Obras paralizadas según la Contraloría
# Insumo:    Anexo N.° 01 del "Informe de obras paralizadas en el territorio nacional a junio de 2026"
#            (Contraloría General de la República, publicado en gob.pe; una fila por obra, 2 262 obras)
#            y data/procesado/inversiones.parquet (Proceso 3), para unir cada obra con su proyecto por el CUI
# Resultado: data/procesado/contraloria_paralizadas.parquet: una fila por obra paralizada que pertenece a un proyecto
#            de nuestra base, con su causa, su avance físico, su año de inicio y su código INFOBRAS
# Uso:       uv run --no-project --with pandas --with openpyxl --with pyarrow python scripts/08_contraloria.py
# Idea tomada de "Obras que esperan" (https://github.com/bocchienjoyer/obras-que-esperan), que usa el mismo anexo.
# ============================================================

# --- Paquetes ---
# pathlib, urllib, re: rutas, descarga del archivo y limpieza de textos (vienen con Python)
# pandas: tablas; openpyxl: lo usa pandas para leer archivos de Excel (.xlsx) (se instalan una vez)
from pathlib import Path
import re
import urllib.request
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / "data" / "contraloria"
ANEXO = CARPETA / "anexo_01_obras_paralizadas_junio_2026.xlsx"
URL_ANEXO = ("https://cdn.www.gob.pe/uploads/document/file/10466637/8489152-anexo-n-01-base-de-datos-con-la-lista-de-"
             "obras-publicas-paralizadas-en-el-territorio-nacional.XLSX?v=1787003153")
SALIDA = RAIZ / "data" / "procesado" / "contraloria_paralizadas.parquet"

# ============================================================
# PASO 8.1: Descargar el anexo (solo si no está en la carpeta)
#   Antes: nada en data/contraloria | Después: el archivo de Excel de la Contraloría (≈ 0,7 MB)
# ============================================================
if not ANEXO.exists():
    CARPETA.mkdir(parents=True, exist_ok=True)
    print("Descargando el anexo de la Contraloría…")
    urllib.request.urlretrieve(URL_ANEXO, ANEXO)
print("Anexo:", ANEXO.name, f"({ANEXO.stat().st_size / 1e6:.1f} MB)")

# ============================================================
# PASO 8.2: Leer el anexo
#   pd.read_excel(dtype=str): lee la hoja "Data" como texto, para que el CUI no pierda ceros ni se vuelva decimal
#   Antes: archivo de Excel | Después: tabla de 2 262 obras × 38 columnas
#   Los nombres de columna traen una nota en una segunda línea ("COSTO DE OBRA…\n(Según…)"): se deja solo la primera
# ============================================================
obras = pd.read_excel(ANEXO, sheet_name="Data", dtype=str)
obras.columns = [c.split("\n")[0].strip() for c in obras.columns]
print("Obras en el anexo:", obras.shape)

# ============================================================
# PASO 8.3: Limpiar solo lo que se va a mostrar (el anexo no se modifica)
# ============================================================
# CUI: sin espacios. 134 obras tienen CUI "0" (sin código): no se pueden unir con un proyecto y quedan fuera del cruce
obras["CUI"] = obras["CUI"].str.strip()
print("  Obras sin CUI (valor 0):", (obras["CUI"] == "0").sum())

def causa_legible(texto):
    """Causa de paralización en minúsculas normales y sin su número de código.
    Antes: '5 DEFICIENCIA EN EL EXPEDIENTE TÉCNICO' o '9 EVENTOS CLIMÁTICOS ' (con espacio al final)
    Después: 'Deficiencia en el expediente técnico', 'Eventos climáticos' (las dos variantes quedan iguales)."""
    if pd.isna(texto):
        return "Sin causa registrada"
    return re.sub(r"^\d+\s+", "", " ".join(str(texto).split())).capitalize()

obras["causa"] = obras["CAUSAL PARALIZACION"].map(causa_legible)
# Avance físico de la obra y año de inicio: de texto a número (54 obras no tienen avance: quedan vacías)
obras["avance_fisico_obra"] = pd.to_numeric(obras["AVANCE FÍSICO"], errors="coerce")
obras["anio_inicio_obra"] = pd.to_numeric(obras["AÑO INICIO OBRA"], errors="coerce").astype("Int64")
print("  Causas distintas después de limpiar:", obras["causa"].nunique())

# ============================================================
# PASO 8.4: Unir cada obra con su proyecto por el CUI
#   merge(how="inner"): conserva solo las obras cuyo CUI está en nuestra base (gobierno nacional y gobiernos regionales).
#   Un proyecto puede tener varias obras paralizadas (por ejemplo, un programa con obras en varios distritos).
#   Antes: 2 262 obras del país | Después: las obras de nuestros proyectos, con el 'id' que usa la app
# ============================================================
inversiones = pd.read_parquet(RAIZ / "data" / "procesado" / "inversiones.parquet", columns=["id", "cui", "nivel"])
inversiones = inversiones[inversiones["cui"].fillna("") != ""].drop_duplicates("cui")
cruce = obras.merge(inversiones, left_on="CUI", right_on="cui", how="inner")

paralizadas = pd.DataFrame({
    "id": cruce["id"],
    "infobras": cruce["CODIGO INFOBRAS"].str.strip(),
    "obra": cruce["DESCRIPCION OBRA"].str.strip(),
    "causa": cruce["causa"],
    "avance_fisico_obra": cruce["avance_fisico_obra"],
    "anio_inicio_obra": cruce["anio_inicio_obra"],
    "nivel_contraloria": cruce["NIVEL DE GOBIERNO"],
}).sort_values(["id", "infobras"])

# ============================================================
# PASO 8.5: Verificar y guardar
# ============================================================
print("\nObras que pertenecen a proyectos de nuestra base:", len(paralizadas),
      "| proyectos distintos:", paralizadas["id"].nunique())
print(cruce.groupby("nivel").size().rename("obras").to_string())
print("\nCausas (obras de nuestra base):")
print(paralizadas["causa"].value_counts().to_string())
sin_cruce = obras[(obras["NIVEL DE GOBIERNO"] != "G. LOCAL") & (obras["CUI"] != "0") & ~obras["CUI"].isin(inversiones["cui"])]
print("\nObras nacionales o regionales cuyo CUI no está entre las inversiones activas (cerradas o desactivadas):", len(sin_cruce))
paralizadas.to_parquet(SALIDA, index=False)
print("Guardado:", SALIDA.relative_to(RAIZ), paralizadas.shape)
