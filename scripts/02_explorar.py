# ============================================================
# PROCESO 2: Explorar las tres bases del MEF antes de procesarlas
# Insumo:    data/crudo/DETALLE_INVERSIONES.csv, INVERSIONES_BRECHAS.csv y FORMATO_12B.csv
# Resultado: docs/exploracion_resultados.md (salida en bruto de la lista de revisión)
#            No modifica ningún dato: solo lee y cuenta.
# Uso:       uv run --with pandas python scripts/02_explorar.py
# ============================================================

# --- Paquetes ---
# pathlib: armar rutas de archivos que funcionan en Windows y en Linux (viene con Python)
# pandas: leer los CSV como tablas y calcular conteos y estadísticos (se instala una vez: pip install pandas)
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "data" / "crudo"
SALIDA = RAIZ / "docs" / "exploracion_resultados.md"
HOY = pd.Timestamp("2026-11-10")
lineas = []                                    # aquí se acumula el informe en bruto

def anotar(titulo, contenido=""):
    """Agrega una sección al informe. No cambia los datos."""
    lineas.append(f"\n## {titulo}\n")
    if contenido is not None and str(contenido) != "":
        lineas.append("```\n" + str(contenido) + "\n```")

# ============================================================
# PASO 2.1: Cargar el detalle de inversiones
# pd.read_csv(dtype=str): lee todo como texto, para ver cómo viene registrado antes de convertir
#   Antes: archivo de 248 MB en el disco | Después: tabla en memoria llamada detalle
# ============================================================
detalle = pd.read_csv(CRUDO / "DETALLE_INVERSIONES.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False)
anotar("1. Tamaño del detalle (filas, columnas)", detalle.shape)
anotar("2. Columnas", ", ".join(detalle.columns))
anotar("3. Tres filas al azar (columnas clave)",
       detalle.sample(3, random_state=1)[["NIVEL", "SECTOR", "ENTIDAD", "CODIGO_UNICO", "NOMBRE_INVERSION",
                                          "COSTO_ACTUALIZADO", "FEC_FIN_EJECUCION"]].to_string())

# ---- Duplicados: ¿una fila por inversión? ----
anotar("4. CUI duplicados en el detalle", detalle["CODIGO_UNICO"].duplicated().sum())

# ---- Faltantes: celdas vacías ("") por columna, solo en gobierno nacional ----
gn = detalle[detalle["NIVEL"] == "GN"].copy()
vacios = (gn == "").sum()
anotar("5. Celdas vacías por columna en gobierno nacional (de " + str(len(gn)) + ")",
       vacios[vacios > 0].sort_values(ascending=False).to_string())

# ---- Números guardados como texto: convertir una copia y contar lo que no se pudo convertir ----
montos = ["MONTO_VIABLE", "COSTO_ACTUALIZADO", "DEVEN_ACUMUL_ANIO_ANT", "DEV_ANIO_ACTUAL", "PIM_ANIO_ACTUAL",
          "SALDO_EJECUTAR", "AVANCE_FISICO", "AVANCE_EJECUCION", "NUM_HABITANTES_BENEF", "LATITUD", "LONGITUD"]
convertido = gn[montos].apply(lambda c: pd.to_numeric(c, errors="coerce"))
no_convertible = ((gn[montos] != "") & convertido.isna()).sum()
anotar("6a. Valores que no son número (sin contar vacíos)", no_convertible.to_string())
anotar("6b. Estadísticos de montos en gobierno nacional (soles)", convertido.describe().round(1).T.to_string())
anotar("6c. Montos en cero o negativos",
       pd.DataFrame({"cero": (convertido == 0).sum(), "negativo": (convertido < 0).sum()}).to_string())

# ---- Frecuencias y valores únicos ----
for col in ["NIVEL", "ESTADO", "SITUACION", "MARCO", "TIPO_INVERSION", "DES_MODALIDAD", "TIENE_F12B",
            "EXPEDIENTE_TECNICO", "INFORME_CIERRE", "REGISTRADO_PMI", "ANIO_PROCESO"]:
    anotar(f"7. Frecuencias de {col} (gobierno nacional)", gn[col].value_counts().head(12).to_string())
sectores = sorted(gn["SECTOR"].unique())
anotar("8a. Sectores únicos con espacios dobles o al final", [s for s in sectores if "  " in s or s != s.strip()])
anotar("8b. Número de entidades por sector", gn.groupby("SECTOR")["ENTIDAD"].nunique().sort_values(ascending=False).to_string())

# ---- Fechas ----
for col in ["FECHA_VIABILIDAD", "FEC_INI_EJECUCION", "FEC_FIN_EJECUCION"]:
    f = pd.to_datetime(gn[col], errors="coerce")
    anotar(f"9. Rango de {col}", f"mín {f.min()} | máx {f.max()} | vacías o inválidas {f.isna().sum()} | "
                                   f"después de 2040: {(f > '2040-12-31').sum()}")
fin = pd.to_datetime(gn["FEC_FIN_EJECUCION"], errors="coerce")
anotar("9b. Fin de ejecución ya vencido y sin informe de cierre",
       int(((fin < HOY) & (gn["INFORME_CIERRE"] == "NO")).sum()))

# ---- Atípicos: las inversiones más caras y los avances imposibles ----
gn["_costo"] = convertido["COSTO_ACTUALIZADO"]
anotar("10a. Las 15 inversiones más caras del gobierno nacional",
       gn.nlargest(15, "_costo")[["SECTOR", "CODIGO_UNICO", "_costo", "TIPO_INVERSION", "NOMBRE_INVERSION"]]
       .assign(NOMBRE_INVERSION=lambda d: d["NOMBRE_INVERSION"].str[:80]).to_string())
anotar("10b. Avance físico o de ejecución mayor a 100 %",
       f"físico: {(convertido['AVANCE_FISICO'] > 100).sum()} | ejecución: {(convertido['AVANCE_EJECUCION'] > 100).sum()}")
anotar("10c. Coordenadas faltantes o en cero (no se pueden mapear)",
       int((convertido["LATITUD"].isna() | (convertido["LATITUD"] == 0)).sum()))
anotar("10d. Caracteres mal codificados (Ã, �) en nombres", int(gn["NOMBRE_INVERSION"].str.contains("Ã|�", regex=True).sum()))

# ============================================================
# PASO 2.2: Explorar la base de brechas
# ============================================================
brechas = pd.read_csv(CRUDO / "INVERSIONES_BRECHAS.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False)
anotar("11. Brechas: tamaño, columnas y ejemplo", f"{brechas.shape}\n{list(brechas.columns)}\n{brechas.head(3).to_string()}")
por_cui = brechas.groupby("CODIGO_UNICO").size()
anotar("11b. Brechas por inversión (cuántas filas tiene cada CUI)", por_cui.describe().round(2).to_string())
anotar("11c. Inversiones de gobierno nacional con al menos una brecha",
       f"{gn['CODIGO_UNICO'].isin(brechas['CODIGO_UNICO']).sum()} de {len(gn)}")
for col in ["ESPACIO_GEOGRAFICO", "ANIO", "DES_UM"]:
    anotar(f"11d. Frecuencias de {col}", brechas[col].value_counts().head(10).to_string())
valor = pd.to_numeric(brechas["VALOR"], errors="coerce")
anotar("11e. Estadísticos de VALOR (tamaño de la brecha) y CONTRIBUCION",
       pd.DataFrame({"VALOR": valor.describe(), "CONTRIBUCION": pd.to_numeric(brechas["CONTRIBUCION"], errors="coerce").describe()}).round(2).to_string())
anotar("11f. VALOR mayor a 100 (no puede ser porcentaje)", int((valor > 100).sum()))
anotar("11g. Filas duplicadas exactas en brechas", int(brechas.duplicated().sum()))

# ============================================================
# PASO 2.3: Explorar el formato 12-B (solo las columnas de texto y fechas)
# ============================================================
cols12 = ["CODIGO_UNICO", "ESTADO", "FECHA_ULT_ACT_F12B", "ULT_PERIODO_REG_F12B", "ULT_ESTADO_SITUACIONAL",
          "ULT_PROBLEMA", "ACC_PROBLEMA", "AVANCE_FISICO"]
f12b = pd.read_csv(CRUDO / "FORMATO_12B.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False, usecols=cols12)
anotar("12. Formato 12-B: tamaño y duplicados", f"{f12b.shape} | CUI duplicados: {f12b['CODIGO_UNICO'].duplicated().sum()}")
anotar("12b. Estados en el 12-B", f12b["ESTADO"].value_counts().to_string())
fecha12 = pd.to_datetime(f12b["FECHA_ULT_ACT_F12B"], errors="coerce")
anotar("12c. Fecha de la última actualización del 12-B", f"mín {fecha12.min()} | máx {fecha12.max()} | vacías {fecha12.isna().sum()}")
gn12 = f12b[f12b["CODIGO_UNICO"].isin(gn["CODIGO_UNICO"])]
anotar("12d. Inversiones de gobierno nacional con fila en el 12-B", f"{len(gn12)} de {len(gn)}")
anotar("12e. Textos no vacíos (gobierno nacional)",
       {c: int((gn12[c] != "").sum()) for c in ["ULT_ESTADO_SITUACIONAL", "ULT_PROBLEMA", "ACC_PROBLEMA"]})
anotar("12f. Ejemplos de ULT_PROBLEMA", gn12.loc[gn12["ULT_PROBLEMA"] != "", "ULT_PROBLEMA"].str[:160].head(8).to_string())

SALIDA.write_text("# Resultados de la exploración (salida en bruto)\n" + "\n".join(lineas), encoding="utf-8")
print("Listo:", SALIDA, "| secciones:", sum(1 for l in lineas if l.startswith("\n## ")))
