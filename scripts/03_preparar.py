# ============================================================
# PROCESO 3: Preparar la base de inversiones del gobierno nacional
# Insumo:    data/crudo/DETALLE_INVERSIONES.csv, INVERSIONES_BRECHAS.csv y FORMATO_12B.csv
# Resultado: data/procesado/gobierno_nacional.parquet (una fila por inversión, con su brecha y su último 12-B)
#            Se conservan las columnas originales de los valores que se marcan como no válidos.
# Uso:       uv run --with pandas --with pyarrow python scripts/03_preparar.py
# ============================================================

# --- Paquetes ---
# pathlib, re: rutas de archivos y limpieza de texto (vienen con Python)
# pandas: tablas; pyarrow: guardar en formato parquet, más liviano y rápido que CSV (se instalan una vez)
from pathlib import Path
import re
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDO, PROCESADO = RAIZ / "data" / "crudo", RAIZ / "data" / "procesado"
PROCESADO.mkdir(parents=True, exist_ok=True)

def texto(serie):
    """Quita espacios repetidos. Antes: 'DEFENSORIA  DEL PUEBLO' | Después: 'DEFENSORIA DEL PUEBLO'."""
    return serie.fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

# ============================================================
# PASO 3.1: Cargar el detalle y quedarse con el gobierno nacional
#   Antes: 150 641 inversiones de todo el país | Después: solo NIVEL = "GN"
# ============================================================
detalle = pd.read_csv(CRUDO / "DETALLE_INVERSIONES.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False)
gn = detalle[detalle["NIVEL"] == "GN"].copy()
print("3.1 Gobierno nacional:", len(gn), "de", len(detalle))

# ============================================================
# PASO 3.2: Duplicados e identificador
#   drop_duplicates(): elimina solo filas idénticas en todas las columnas (no se pierde información)
#   Las inversiones antiguas sin CUI se identifican con su código SNIP
# ============================================================
antes = len(gn)
gn = gn.drop_duplicates()
print("3.2 Filas idénticas eliminadas:", antes - len(gn))
gn["id"] = gn["CODIGO_UNICO"].where(gn["CODIGO_UNICO"] != "", "SNIP-" + gn["CODIGO_SNIP"])
print("    Identificadores repetidos que quedan:", gn["id"].duplicated().sum(), "| sin CUI (usan SNIP):", (gn["CODIGO_UNICO"] == "").sum())

# ============================================================
# PASO 3.3: Convertir números y fechas
#   Antes: texto ("466749379.0", "2026-03-01 00:00:00", "") | Después: números y fechas; "" queda como faltante
# ============================================================
numeros = {"MONTO_VIABLE": "viable", "COSTO_ACTUALIZADO": "costo", "CTRL_CONCURR": "ctrl", "DEVEN_ACUMUL_ANIO_ANT": "dev_hasta_2025",
           "DEV_ANIO_ACTUAL": "dev_2026", "PIM_ANIO_ACTUAL": "pim_2026", "SALDO_EJECUTAR": "saldo", "AVANCE_FISICO": "avance_fisico_original",
           "NUM_HABITANTES_BENEF": "beneficiarios_original", "LATITUD": "lat_original", "LONGITUD": "lon_original"}
for col, nuevo in numeros.items():
    gn[nuevo] = pd.to_numeric(gn[col], errors="coerce")
for col, nuevo in {"FECHA_VIABILIDAD": "fecha_viable", "FEC_INI_EJECUCION": "inicio", "FEC_FIN_EJECUCION": "fin"}.items():
    gn[nuevo] = pd.to_datetime(gn[col], errors="coerce")
gn["dev_acumulado"] = gn["dev_hasta_2025"].fillna(0) + gn["dev_2026"].fillna(0)

# ============================================================
# PASO 3.4: Marcar valores imposibles como faltantes (sin borrar la columna original)
#   Avance físico > 100 %; beneficiarios > 35 millones (más que la población del Perú);
#   coordenadas fuera del Perú (incluye las que vienen en 0)
# ============================================================
gn["avance_fisico"] = gn["avance_fisico_original"].where(gn["avance_fisico_original"] <= 100)
gn["beneficiarios"] = gn["beneficiarios_original"].where(gn["beneficiarios_original"] <= 35_000_000)
en_peru = gn["lat_original"].between(-18.5, 0.1) & gn["lon_original"].between(-81.5, -68.5)
gn["lat"], gn["lon"] = gn["lat_original"].where(en_peru), gn["lon_original"].where(en_peru)
print("3.4 Marcados como faltantes -> avance físico:", int((gn["avance_fisico_original"] > 100).sum()),
      "| beneficiarios:", int((gn["beneficiarios_original"] > 35_000_000).sum()),
      "| coordenadas:", int((~en_peru).sum()))

# ============================================================
# PASO 3.5: Limpiar textos para mostrar
#   " ¿ " es un guion largo mal codificado en el origen: se reemplaza por " – " solo en la copia para mostrar
# ============================================================
for col in ["SECTOR", "ENTIDAD", "NOMBRE_UEP", "NOMBRE_UF", "NOMBRE_UEI", "NOMBRE_OPMI", "DES_MODALIDAD", "TIPO_INVERSION",
            "SITUACION", "DEPARTAMENTO", "PROVINCIA", "DISTRITO", "FUNCION", "ALTERNATIVA"]:
    gn[col] = texto(gn[col])
gn["nombre"] = texto(gn["NOMBRE_INVERSION"]).str.replace(" ¿ ", " – ", regex=False)
gn["DES_MODALIDAD"] = gn["DES_MODALIDAD"].str.replace("PUBLICA PRIVADA", "PÚBLICA PRIVADA", regex=False)
gn["NOMBRE_UEP"] = gn["NOMBRE_UEP"].replace("", "Sin unidad ejecutora registrada")

# ============================================================
# PASO 3.6: Unir la brecha (archivo nacional de brechas)
#   Una inversión puede tener varias brechas: se guarda la primera y cuántas tiene en total
# ============================================================
brechas = pd.read_csv(CRUDO / "INVERSIONES_BRECHAS.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False)
brechas = brechas[brechas["CODIGO_UNICO"].isin(gn["CODIGO_UNICO"])]
primera = brechas.groupby("CODIGO_UNICO").agg(
    brecha=("DES_BRECHA", "first"), brecha_servicio=("DES_SERVICIO", "first"), brecha_unidad=("DES_UM", "first"),
    brecha_aporte=("CONTRIBUCION", "first"), n_brechas=("DES_BRECHA", "size")).reset_index()
primera["brecha_aporte"] = pd.to_numeric(primera["brecha_aporte"], errors="coerce")
for c in ["brecha", "brecha_servicio", "brecha_unidad"]:
    primera[c] = texto(primera[c])
gn = gn.merge(primera, on="CODIGO_UNICO", how="left")
print("3.6 Con brecha:", int(gn["brecha"].notna().sum()), "de", len(gn))

# ============================================================
# PASO 3.7: Unir el último seguimiento (formato 12-B nacional)
#   Los textos vienen con la fecha al inicio: "[21/01/2026] En proceso de liquidación" -> se separa la fecha
# ============================================================
cols12 = ["CODIGO_UNICO", "FECHA_ULT_ACT_F12B", "ULT_ESTADO_SITUACIONAL", "ULT_PROBLEMA", "ACC_PROBLEMA"]
f12b = pd.read_csv(CRUDO / "FORMATO_12B.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False, usecols=cols12)
f12b = f12b[f12b["CODIGO_UNICO"].isin(gn["CODIGO_UNICO"])]
# Nombres de personas en los textos (p. ej., "Ing. Juan Pérez"): se reemplazan por "[nombre omitido]" en la copia para mostrar.
# La regla es prudente: puede ocultar alguna palabra de más, pero no deja nombres a la vista.
PERSONA = (r"\b(Ing|ING|Sr|SR|Sra|SRA|Srta|Lic|LIC|Arq|ARQ|Dr|DR|Dra|DRA|Econ|ECON|Abog|ABOG|CPC|Mg|MG)\.\s*"
           r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){0,3}")

# Correos electrónicos (p. ej., "nombre@entidad.gob.pe"): también identifican a personas; se reemplazan por "[correo omitido]".
CORREO = r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"

def sin_fecha(s):
    """Quita la fecha inicial '[21/01/2026] ' y oculta nombres de personas y correos.
    Antes: '[21/01/2026] El Ing. Juan Pérez (jperez@x.pe) informa...'
    Después: 'El Ing. [nombre omitido] ([correo omitido]) informa...'"""
    limpio = texto(s).str.replace(r"^\[\d{2}/\d{2}/\d{4}\]\s*", "", regex=True)
    limpio = limpio.str.replace(CORREO, "[correo omitido]", regex=True)
    return limpio.str.replace(PERSONA, lambda m: m.group(1) + ". [nombre omitido]", regex=True)
f12b = pd.DataFrame({"CODIGO_UNICO": f12b["CODIGO_UNICO"],
                     "fecha_12b": pd.to_datetime(f12b["FECHA_ULT_ACT_F12B"], errors="coerce"),
                     "situacion_12b": sin_fecha(f12b["ULT_ESTADO_SITUACIONAL"]),
                     "problema_12b": sin_fecha(f12b["ULT_PROBLEMA"]),
                     "acciones_12b": sin_fecha(f12b["ACC_PROBLEMA"])})
gn = gn.merge(f12b, on="CODIGO_UNICO", how="left")
print("3.7 Con último 12-B:", int(gn["fecha_12b"].notna().sum()), "de", len(gn))

# ============================================================
# PASO 3.8: Guardar solo las columnas que usa la app
# ============================================================
columnas = {
    "id": "id", "CODIGO_UNICO": "cui", "CODIGO_SNIP": "snip", "SECTOR": "sector", "ENTIDAD": "entidad", "NOMBRE_UEP": "unidad",
    "nombre": "nombre", "TIPO_INVERSION": "tipo", "SITUACION": "situacion", "MARCO": "marco", "DES_MODALIDAD": "modalidad",
    "FUNCION": "funcion", "DEPARTAMENTO": "departamento", "PROVINCIA": "provincia", "DISTRITO": "distrito",
    "NOMBRE_UF": "uf", "NOMBRE_UEI": "uei", "NOMBRE_OPMI": "opmi", "ALTERNATIVA": "alternativa",
    "EXPEDIENTE_TECNICO": "expediente_tecnico", "INFORME_CIERRE": "informe_cierre", "REGISTRADO_PMI": "en_pmi", "TIENE_F12B": "tiene_12b",
}
salida = gn.rename(columns=columnas)[list(columnas.values()) + [
    "viable", "costo", "ctrl", "dev_hasta_2025", "dev_2026", "dev_acumulado", "pim_2026", "saldo",
    "avance_fisico", "avance_fisico_original", "beneficiarios", "beneficiarios_original", "lat", "lon",
    "fecha_viable", "inicio", "fin", "brecha", "brecha_servicio", "brecha_unidad", "brecha_aporte", "n_brechas",
    "fecha_12b", "situacion_12b", "problema_12b", "acciones_12b"]]
salida.to_parquet(PROCESADO / "gobierno_nacional.parquet", index=False)
print("3.8 Guardado:", salida.shape, "->", PROCESADO / "gobierno_nacional.parquet")
