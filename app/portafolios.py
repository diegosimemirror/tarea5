# ============================================================
# MÓDULO: guardar y abrir los portafolios A y B (sin cuentas de usuario)
# Lo usa la app (app/app.py). Un portafolio es una lista de proyectos que la persona marca a mano.
# Se guarda de dos formas, y ninguna queda en el servidor:
#   1) en el enlace de la página (?a=CUI,CUI&b=CUI&na=nombre&nb=nombre), para portafolios pequeños
#   2) en un archivo CSV que la persona descarga y vuelve a subir (se abre también en Excel)
# Insumo:    los códigos (CUI) de cada portafolio y la tabla de proyectos de la app
# Resultado: texto para el enlace, el archivo CSV, o las listas de códigos leídas de vuelta
# ============================================================

# io, re: leer un archivo subido como texto y validar códigos (vienen con Python); pandas: tablas
import io
import re
import pandas as pd

LETRAS = ("A", "B")
MAX_ENLACE = 400        # hasta 400 proyectos por portafolio en el enlace (≈ 3 200 caracteres); más, solo con el archivo
CODIGO = re.compile(r"^(\d{1,8}|SNIP-\d{1,8})$")   # CUI (solo números) o el código SNIP de los proyectos antiguos sin CUI


def codigos_del_enlace(texto):
    """Antes: '2613205, 2324655,,x' (lo que viene en el enlace) | Después: ['2613205', '2324655'] (solo códigos válidos)."""
    return [c for c in (p.strip() for p in str(texto or "").split(",")) if CODIGO.match(c)]


def a_enlace(portafolios, nombres):
    """Parámetros del enlace para los portafolios que caben (hasta MAX_ENLACE proyectos).
    Antes: {'A': ['2613205', …], 'B': [...]} | Después: {'a': '2613205,…', 'na': 'Mi portafolio A', …}."""
    parametros = {}
    for letra in LETRAS:
        ids = portafolios[letra]
        if ids and len(ids) <= MAX_ENLACE:
            parametros[letra.lower()] = ",".join(ids)
            if nombres[letra] != f"Portafolio {letra}":      # el nombre solo va si la persona lo cambió
                parametros["n" + letra.lower()] = nombres[letra]
    return parametros


def a_csv(portafolios, nombres, proyectos):
    """Archivo CSV con una fila por proyecto y portafolio (un proyecto puede estar en A y en B).
    Antes: listas de códigos | Después: texto CSV con columnas portafolio, nombre_portafolio, cui, proyecto, estado, costo,
    fase, prioridad del MEF, componentes, avance del 12-B y presupuesto (las columnas que faltan en la tabla quedan vacías).
    Se guarda en UTF-8 con marca (utf-8-sig) para que Excel muestre bien las tildes."""
    datos = proyectos.set_index("id")
    extra = {"fase": "fase_nombre", "prioridad_mef": "prelacion", "componentes": "componentes", "avance_12b": "avance_12b",
             "presupuesto_2026_soles": "pim_2026", "pmi_2027_2029_soles": "pmi_siguientes"}
    filas = []
    for letra in LETRAS:
        for cui in portafolios[letra]:
            if cui in datos.index:
                p = datos.loc[cui]
                fila = {"portafolio": letra, "nombre_portafolio": nombres[letra], "cui": cui,
                        "proyecto": p["que_es"], "estado": p["estado"], "costo_soles": round(float(p["costo"] or 0))}
                for nombre, columna in extra.items():
                    valor = p[columna] if columna in p.index else None      # la columna puede no estar en la tabla
                    vacio = valor is None or (not isinstance(valor, str) and pd.isna(valor)) or valor == ""
                    fila[nombre] = "" if vacio else (round(float(valor)) if nombre.endswith("_soles") else valor)
                filas.append(fila)
    columnas = ["portafolio", "nombre_portafolio", "cui", "proyecto", "estado", "costo_soles", *extra]
    return pd.DataFrame(filas, columns=columnas).to_csv(index=False).encode("utf-8-sig")


def leer_csv(contenido):
    """Lee un archivo descargado antes (o editado en Excel, que a veces separa con punto y coma).
    Antes: bytes del archivo | Después: ({'A': [códigos], 'B': [códigos]}, {'A': nombre, 'B': nombre}).
    Solo usa las columnas 'portafolio' y 'cui'; las demás son para leerlo en Excel. Lanza ValueError si no las tiene."""
    texto = contenido.decode("utf-8-sig", errors="replace")
    tabla = pd.read_csv(io.StringIO(texto), sep=None, engine="python", dtype=str).fillna("")
    tabla.columns = [c.strip().lower() for c in tabla.columns]
    if not {"portafolio", "cui"} <= set(tabla.columns):
        raise ValueError("El archivo debe tener las columnas «portafolio» y «cui».")
    portafolios, nombres = {}, {}
    for letra in LETRAS:
        parte = tabla[tabla["portafolio"].str.strip().str.upper() == letra]
        portafolios[letra] = list(dict.fromkeys(c for c in parte["cui"].str.strip() if CODIGO.match(c)))
        nombre = parte["nombre_portafolio"].str.strip() if "nombre_portafolio" in parte else pd.Series(dtype=str)
        nombres[letra] = nombre[nombre != ""].iloc[0] if (nombre != "").any() else f"Portafolio {letra}"
    return portafolios, nombres
