# ============================================================
# PROCESO 3: Preparar la base de inversiones del gobierno nacional y de los gobiernos regionales
# Insumo:    data/crudo/DETALLE_INVERSIONES.csv, INVERSIONES_BRECHAS.csv y FORMATO_12B.csv
# Resultado: data/procesado/inversiones.parquet (una fila por inversión, con su brecha y su último 12-B)
#            data/procesado/brechas.parquet (todas las brechas: una fila por inversión y brecha)
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
# PASO 3.1: Cargar el detalle y quedarse con el gobierno nacional y los gobiernos regionales
#   Antes: 150 641 inversiones de todo el país | Después: solo NIVEL = "GN" (nacional) y "GR" (regional)
#   Los gobiernos locales (NIVEL = "GL", 124 229 inversiones) quedan para una versión posterior.
# ============================================================
detalle = pd.read_csv(CRUDO / "DETALLE_INVERSIONES.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False)
inv = detalle[detalle["NIVEL"].isin(["GN", "GR"])].copy()
print("3.1 Nacional y regional:", len(inv), "de", len(detalle), "|", inv["NIVEL"].value_counts().to_dict())

# ============================================================
# PASO 3.2: Duplicados e identificador
#   drop_duplicates(): elimina solo filas idénticas en todas las columnas (no se pierde información)
#   Las inversiones antiguas sin CUI se identifican con su código SNIP
# ============================================================
antes = len(inv)
inv = inv.drop_duplicates()
print("3.2 Filas idénticas eliminadas:", antes - len(inv))
inv["id"] = inv["CODIGO_UNICO"].where(inv["CODIGO_UNICO"] != "", "SNIP-" + inv["CODIGO_SNIP"])
print("    Identificadores repetidos que quedan:", inv["id"].duplicated().sum(), "| sin CUI (usan SNIP):", (inv["CODIGO_UNICO"] == "").sum())

# ============================================================
# PASO 3.3: Convertir números y fechas
#   Antes: texto ("466749379.0", "2026-03-01 00:00:00", "") | Después: números y fechas; "" queda como faltante
# ============================================================
numeros = {"MONTO_VIABLE": "viable", "COSTO_ACTUALIZADO": "costo", "CTRL_CONCURR": "ctrl", "DEVEN_ACUMUL_ANIO_ANT": "dev_hasta_2025",
           "DEV_ANIO_ACTUAL": "dev_2026", "PIM_ANIO_ACTUAL": "pim_2026", "SALDO_EJECUTAR": "saldo", "AVANCE_FISICO": "avance_fisico_original",
           "NUM_HABITANTES_BENEF": "beneficiarios_original", "LATITUD": "lat_original", "LONGITUD": "lon_original",
           # Para los indicadores de cartera (Proceso 7): expediente técnico, laudos, cartas fianza, certificado 2026 y
           # montos de la programación multianual (PMI_ANIO_1 a 4: los años siguientes, según el nombre de la columna)
           "MONTO_ET_F8": "monto_et", "MONTO_LAUDO": "laudo", "MONTO_FIANZA": "fianza", "CERTIF_ANIO_ACTUAL": "certificado_2026",
           "PMI_ANIO_1": "pmi_1", "PMI_ANIO_2": "pmi_2", "PMI_ANIO_3": "pmi_3", "PMI_ANIO_4": "pmi_4",
           # Avance de ejecución que declara la entidad en el 12-B: avance de TODOS los componentes (productos, gestión del
           # proyecto, expediente técnico, supervisión y liquidación), valorizado a su costo. Verificado con el detalle por
           # componente del SSI (verDetEstimacion) en 3 proyectos. AVANCE_FISICO es lo mismo, pero solo con los productos.
           "AVANCE_EJECUCION": "avance_ejecucion_original"}
for col, nuevo in numeros.items():
    inv[nuevo] = pd.to_numeric(inv[col], errors="coerce")
for col, nuevo in {"FECHA_VIABILIDAD": "fecha_viable", "FEC_INI_EJECUCION": "inicio", "FEC_FIN_EJECUCION": "fin",
                   "FEC_INI_EJEC_FISICA": "inicio_fisico", "FEC_FIN_EJEC_FISICA": "fin_fisico",
                   "ULT_FEC_DECLA_ESTIM": "fecha_declaracion"}.items():   # fecha en que la entidad declaró su avance
    inv[nuevo] = pd.to_datetime(inv[col], errors="coerce")
inv["dev_acumulado"] = inv["dev_hasta_2025"].fillna(0) + inv["dev_2026"].fillna(0)

# ============================================================
# PASO 3.4: Marcar valores imposibles como faltantes (sin borrar la columna original)
#   Avance físico > 100 %; beneficiarios > 35 millones (más que la población del Perú);
#   coordenadas fuera del Perú (incluye las que vienen en 0)
# ============================================================
inv["avance_fisico"] = inv["avance_fisico_original"].where(inv["avance_fisico_original"] <= 100)
inv["avance_ejecucion"] = inv["avance_ejecucion_original"].where(inv["avance_ejecucion_original"] <= 100)
inv["beneficiarios"] = inv["beneficiarios_original"].where(inv["beneficiarios_original"] <= 35_000_000)
en_peru = inv["lat_original"].between(-18.5, 0.1) & inv["lon_original"].between(-81.5, -68.5)
inv["lat"], inv["lon"] = inv["lat_original"].where(en_peru), inv["lon_original"].where(en_peru)
print("3.4 Marcados como faltantes -> avance físico:", int((inv["avance_fisico_original"] > 100).sum()),
      "| avance de ejecución:", int((inv["avance_ejecucion_original"] > 100).sum()),
      "| beneficiarios:", int((inv["beneficiarios_original"] > 35_000_000).sum()),
      "| coordenadas:", int((~en_peru).sum()))

# ============================================================
# PASO 3.5: Limpiar textos para mostrar
#   " ¿ " es un guion largo mal codificado en el origen: se reemplaza por " – " solo en la copia para mostrar
# ============================================================
for col in ["SECTOR", "ENTIDAD", "NOMBRE_UEP", "NOMBRE_UF", "NOMBRE_UEI", "NOMBRE_OPMI", "DES_MODALIDAD", "TIPO_INVERSION",
            "SITUACION", "DEPARTAMENTO", "PROVINCIA", "DISTRITO", "FUNCION", "ALTERNATIVA"]:
    inv[col] = texto(inv[col])
inv["nombre"] = texto(inv["NOMBRE_INVERSION"]).str.replace(" ¿ ", " – ", regex=False)
inv["DES_MODALIDAD"] = inv["DES_MODALIDAD"].str.replace("PUBLICA PRIVADA", "PÚBLICA PRIVADA", regex=False)
inv["NOMBRE_UEP"] = inv["NOMBRE_UEP"].replace("", "Sin unidad ejecutora registrada")

# ============================================================
# PASO 3.5b: Niveles de la cartera y tipo de inversión
#   nivel:   "Gobierno nacional" o "Gobierno regional" (antes: "GN" o "GR")
#   cartera: el segundo nivel del árbol. En el nacional es el sector (p. ej., SALUD); en el regional, el gobierno regional
#            (p. ej., GOBIERNO REGIONAL JUNIN), porque en el MEF todos los regionales tienen el mismo sector: GOBIERNOS REGIONALES.
#   pliego:  la entidad (ENTIDAD), que es el pliego presupuestal. En el regional coincide con el gobierno regional.
#   tipo_grupo: el tipo de inversión en 4 grupos. Antes: 12 tipos del MEF | Después: 4 grupos
# ============================================================
inv["nivel"] = inv["NIVEL"].map({"GN": "Gobierno nacional", "GR": "Gobierno regional"})
inv["cartera"] = inv["SECTOR"].where(inv["NIVEL"] == "GN", inv["ENTIDAD"])
TIPO_GRUPO = {"PROYECTO DE INVERSION": "Proyecto de inversión", "PIP MAYOR (SNIP)": "Proyecto de inversión",
              "PIP MENOR (SNIP)": "Proyecto de inversión", "INVERSIONES IOARR": "IOARR",
              "INTERVENCIONES IRI": "IRI (Reconstrucción con Cambios)"}
inv["tipo_grupo"] = inv["TIPO_INVERSION"].map(TIPO_GRUPO).fillna("Programas y otros")
print("3.5b Tipo de inversión por nivel:", inv.groupby(["nivel", "tipo_grupo"]).size().to_dict())

# ============================================================
# PASO 3.6: Unir la brecha (archivo nacional de brechas)
#   Una inversión puede tener varias brechas: se guarda la primera y cuántas tiene en total
# ============================================================
brechas = pd.read_csv(CRUDO / "INVERSIONES_BRECHAS.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False)
brechas = brechas[brechas["CODIGO_UNICO"].isin(inv["CODIGO_UNICO"])]
primera = brechas.groupby("CODIGO_UNICO").agg(
    brecha=("DES_BRECHA", "first"), brecha_servicio=("DES_SERVICIO", "first"), brecha_unidad=("DES_UM", "first"),
    brecha_aporte=("CONTRIBUCION", "first"), n_brechas=("DES_BRECHA", "size")).reset_index()
primera["brecha_aporte"] = pd.to_numeric(primera["brecha_aporte"], errors="coerce")
for c in ["brecha", "brecha_servicio", "brecha_unidad"]:
    primera[c] = texto(primera[c])
inv = inv.merge(primera, on="CODIGO_UNICO", how="left")
print("3.6 Con brecha:", int(inv["brecha"].notna().sum()), "de", len(inv))

# PASO 3.6b: Guardar TODAS las brechas (no solo la primera), una fila por inversión y brecha, para el Proceso 7
#   Antes: 505 452 filas de todo el país | Después: solo las del gobierno nacional y los regionales, con nombres claros
todas = pd.DataFrame({"cui": brechas["CODIGO_UNICO"], "servicio": texto(brechas["DES_SERVICIO"]),
                      "indicador": texto(brechas["DES_BRECHA"]), "unidad_medida": texto(brechas["DES_UM"]),
                      "espacio": texto(brechas["ESPACIO_GEOGRAFICO"]), "anio": brechas["ANIO"],
                      "aporte": pd.to_numeric(brechas["CONTRIBUCION"], errors="coerce")})
todas.to_parquet(PROCESADO / "brechas.parquet", index=False)
print("3.6b Todas las brechas:", todas.shape, "| inversiones:", todas["cui"].nunique())

# ============================================================
# PASO 3.7: Unir el último seguimiento (formato 12-B nacional)
#   Los textos vienen con la fecha al inicio: "[21/01/2026] En proceso de liquidación" -> se separa la fecha
# ============================================================
# Programación mensual del año (para el Proceso 7). Significado deducido del nombre, porque el diccionario del MEF da error 404:
#   MONTO_PROGRAMADO_m: lo que se programó gastar en el mes m | MONTO_ACTUALIZADO_m: la programación ya ajustada
#   DEV_ENE_AÑO_VIG...: lo que se gastó (devengó) cada mes. Se suman de enero a octubre (los meses cerrados al 08/11/2026).
#   El devengado de cada mes de 2026 (enero a noviembre) se guarda también por separado: con él se calcula lo gastado
#   hasta el mes en que la entidad declaró su avance, para comparar avance y gasto en la misma fecha (Proceso 7).
MESES_DEV = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SET", "OCT", "NOV"]
cols_dev = [f"DEV_{m}_AÑO_VIG" for m in MESES_DEV]
cols_mes = [f"MONTO_PROGRAMADO_{i}" for i in range(1, 11)] + [f"MONTO_ACTUALIZADO_{i}" for i in range(1, 11)] + cols_dev
cols12 = ["CODIGO_UNICO", "FECHA_ULT_ACT_F12B", "ULT_ESTADO_SITUACIONAL", "ULT_PROBLEMA", "ACC_PROBLEMA"]
f12b = pd.read_csv(CRUDO / "FORMATO_12B.csv", dtype=str, encoding="utf-8-sig", keep_default_na=False, usecols=cols12 + cols_mes)
f12b = f12b[f12b["CODIGO_UNICO"].isin(inv["CODIGO_UNICO"])]
# sum(axis=1): suma los 10 meses de cada fila. Antes: 10 columnas por concepto | Después: 1 total de enero a octubre
mensual = {nombre: f12b[[c for c in cols_mes if c.startswith(prefijo)]].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
           for nombre, prefijo in [("programado_ene_oct", "MONTO_PROGRAMADO_"), ("reprogramado_ene_oct", "MONTO_ACTUALIZADO_")]}
dev_mes = f12b[cols_dev].apply(pd.to_numeric, errors="coerce")
mensual["devengado_ene_oct"] = dev_mes.iloc[:, :10].sum(axis=1, min_count=1)
for i, c in enumerate(cols_dev, 1):
    mensual[f"dev_2026_{i:02d}"] = dev_mes[c]          # dev_2026_01 = enero ... dev_2026_11 = noviembre
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
                     "acciones_12b": sin_fecha(f12b["ACC_PROBLEMA"]), **mensual})
inv = inv.merge(f12b, on="CODIGO_UNICO", how="left")
print("3.7 Con último 12-B:", int(inv["fecha_12b"].notna().sum()), "de", len(inv))

# ============================================================
# PASO 3.8: Guardar solo las columnas que usa la app
# ============================================================
columnas = {
    "id": "id", "CODIGO_UNICO": "cui", "CODIGO_SNIP": "snip", "nivel": "nivel", "cartera": "cartera", "SECTOR": "sector",
    "ENTIDAD": "entidad", "NOMBRE_UEP": "unidad", "tipo_grupo": "tipo_grupo",
    "nombre": "nombre", "TIPO_INVERSION": "tipo", "SITUACION": "situacion", "MARCO": "marco", "DES_MODALIDAD": "modalidad",
    "FUNCION": "funcion", "DEPARTAMENTO": "departamento", "PROVINCIA": "provincia", "DISTRITO": "distrito",
    "NOMBRE_UF": "uf", "NOMBRE_UEI": "uei", "NOMBRE_OPMI": "opmi", "ALTERNATIVA": "alternativa",
    "EXPEDIENTE_TECNICO": "expediente_tecnico", "INFORME_CIERRE": "informe_cierre", "REGISTRADO_PMI": "en_pmi", "TIENE_F12B": "tiene_12b",
}
salida = inv.rename(columns=columnas)[list(columnas.values()) + [
    "viable", "costo", "ctrl", "dev_hasta_2025", "dev_2026", "dev_acumulado", "pim_2026", "saldo",
    "avance_fisico", "avance_fisico_original", "beneficiarios", "beneficiarios_original", "lat", "lon",
    "fecha_viable", "inicio", "fin", "brecha", "brecha_servicio", "brecha_unidad", "brecha_aporte", "n_brechas",
    "fecha_12b", "situacion_12b", "problema_12b", "acciones_12b",
    # columnas para los indicadores de cartera (Proceso 7)
    "monto_et", "laudo", "fianza", "certificado_2026", "pmi_1", "pmi_2", "pmi_3", "pmi_4", "inicio_fisico", "fin_fisico",
    "programado_ene_oct", "reprogramado_ene_oct", "devengado_ene_oct",
    # avance declarado por la entidad y gasto mensual de 2026 (avance frente a gasto, Proceso 7)
    "avance_ejecucion", "avance_ejecucion_original", "fecha_declaracion", *[f"dev_2026_{i:02d}" for i in range(1, 12)]]]
salida.to_parquet(PROCESADO / "inversiones.parquet", index=False)
print("3.8 Guardado:", salida.shape, "->", PROCESADO / "inversiones.parquet")
