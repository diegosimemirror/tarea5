# ============================================================
# PROCESO 5: Mostrar la cartera de inversiones en lenguaje simple (aplicación web)
# Insumo:    data/procesado/cinco_preguntas.parquet (resultado del Proceso 4)
# Resultado: una página web con tres pasos:
#              1) elegir la cartera completa o un ministerio, 2) ver su árbol y sus proyectos, 3) abrir la ficha de cinco preguntas
#            (en la cartera completa solo se ve la estructura de desglose por ministerio o entidad)
# Uso:       uv run --with streamlit --with pandas --with pyarrow streamlit run app/app.py
# ============================================================

# --- Paquetes ---
# pathlib, textwrap, html: rutas, cortar textos largos en líneas y proteger textos al ponerlos en HTML (vienen con Python)
# pandas: tablas
# streamlit: convierte este programa de Python en una página web, sin escribir HTML (se instala una vez)
from pathlib import Path
import textwrap
import html
import pandas as pd
import pydeck as pdk   # pydeck: mapas interactivos; viene instalado con Streamlit
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "procesado"
DATOS = PROCESADO / "cinco_preguntas.parquet"
FECHA_DATOS = "08/11/2026"

st.set_page_config(page_title="Cartera de inversiones del Estado", page_icon="🏛️", layout="wide")

# ============================================================
# PASO 5.1: Cargar los datos una sola vez (st.cache_data guarda la tabla en memoria entre clics)
# ============================================================
IA = RAIZ / "data" / "procesado" / "ia_titulos.parquet"

@st.cache_data
def cargar():
    """Lee las cinco preguntas. Si existen títulos de alcance hechos con IA (Proceso 6), los usa en lugar del nombre
    acortado; el nombre oficial sigue en la columna 'nombre' (se muestra en "Para especialistas")."""
    tabla = pd.read_parquet(DATOS)
    tabla["redactado_por_ia"] = False
    tabla["lo_que_frena"] = ""
    if IA.exists():
        # Antes: que_es = nombre oficial acortado | Después: que_es = título de alcance (si la IA lo produjo y pasó el control)
        ia = pd.read_parquet(IA)[["id", "titulo_ia"]]
        tabla = tabla.merge(ia, on="id", how="left")
        con_ia = tabla["titulo_ia"].fillna("") != ""
        tabla.loc[con_ia, "que_es"] = tabla.loc[con_ia, "titulo_ia"]
        tabla.loc[con_ia, "redactado_por_ia"] = True
    # Indicadores de cartera del Proceso 7: las frases para la ficha y la clasificación de problemas de cada proyecto
    #   Antes: 1 fila por proyecto con las cinco preguntas | Después: la misma fila, con 8 columnas más
    frases = pd.read_parquet(PROCESADO / "indicadores_proyecto.parquet")[
        ["id", "brechas_lista", "frase_brecha", "frase_costo", "frase_dinero", "frase_problemas", "frase_programacion",
         "clase_problema", "temas", "pct_gastado_vida", "pct_gastado_2026", "frase_indice", "frase_alerta", "alerta_gasto_avance",
         "meses_atraso"]]
    tabla = tabla.merge(frases, on="id", how="left")
    # Ejecución presupuestal en % (las mismas dos medidas de la ficha), para la lista y el mapa
    #   Antes: proporciones (0.153) | Después: porcentajes (15.3); sin presupuesto 2026 queda vacío
    tabla["ejec_2026"] = 100 * tabla["pct_gastado_2026"]
    tabla["ejec_acum"] = 100 * tabla["pct_gastado_vida"]
    return tabla

@st.cache_data
def cargar_indicadores():
    """Una fila por ministerio o entidad, más la fila 'CARTERA COMPLETA' (Proceso 7)."""
    return pd.read_parquet(PROCESADO / "indicadores_cartera.parquet").set_index("sector")

@st.cache_data
def cargar_brechas():
    """Todas las brechas de cada proyecto (Proceso 3): una fila por proyecto y brecha, con su aporte y su unidad.
    Antes: 'PORCENTAJE DE …' en mayúsculas | Después: 'Porcentaje de …' (solo la primera letra en mayúscula)."""
    b = pd.read_parquet(PROCESADO / "brechas_gobierno_nacional.parquet")
    b["indicador"] = b["indicador"].str.capitalize()
    b["unidad_medida"] = b["unidad_medida"].str.lower()
    return b

inversiones = cargar()
indicadores = cargar_indicadores()
brechas_todas = cargar_brechas()
DIAS_AL_CIERRE = (pd.Timestamp("2026-12-31") - pd.Timestamp("2026-11-10")).days   # misma fecha de referencia que los Procesos 4 y 7

# Nombres que entiende cualquiera, en lugar de los nombres de sector del MEF
NOMBRES = {
    "TRANSPORTES Y COMUNICACIONES": "Ministerio de Transportes y Comunicaciones",
    "VIVIENDA, CONSTRUCCION Y SANEAMIENTO": "Ministerio de Vivienda, Construcción y Saneamiento",
    "EDUCACION": "Ministerio de Educación", "SALUD": "Ministerio de Salud",
    "ECONOMIA Y FINANZAS": "Ministerio de Economía y Finanzas", "FONAFE": "FONAFE (empresas del Estado)",
    "AGRICULTURA Y RIEGO": "Ministerio de Desarrollo Agrario y Riego",
    "PRESIDENCIA DEL CONSEJO DE MINISTROS": "Presidencia del Consejo de Ministros",
    "INTERIOR": "Ministerio del Interior", "ENERGIA Y MINAS": "Ministerio de Energía y Minas", "ESSALUD": "EsSalud",
    "JUSTICIA": "Ministerio de Justicia y Derechos Humanos", "PRODUCCION": "Ministerio de la Producción",
    "CULTURA": "Ministerio de Cultura", "PODER JUDICIAL": "Poder Judicial",
    "COMERCIO EXTERIOR Y TURISMO": "Ministerio de Comercio Exterior y Turismo", "AMBIENTAL": "Ministerio del Ambiente",
    "DEFENSA": "Ministerio de Defensa", "MINISTERIO PUBLICO": "Ministerio Público",
    "RELACIONES EXTERIORES": "Ministerio de Relaciones Exteriores", "CONTRALORIA GENERAL": "Contraloría General de la República",
    "UNIVERSIDADES": "Universidades públicas", "REGISTRO NACIONAL DE IDENTIFICACION Y ESTADO CIVIL": "RENIEC",
    "DESARROLLO E INCLUSION SOCIAL": "Ministerio de Desarrollo e Inclusión Social",
    "OFICINA NACIONAL DE PROCESOS ELECTORALES-ONPE": "ONPE", "TRABAJO Y PROMOCION DEL EMPLEO": "Ministerio de Trabajo y Promoción del Empleo",
    "MUJER Y POBLACIONES VULNERABLES": "Ministerio de la Mujer y Poblaciones Vulnerables",
    "CONSEJO NACIONAL DE LA MAGISTRATURA": "Junta Nacional de Justicia", "DEFENSORIA DEL PUEBLO": "Defensoría del Pueblo",
    "TRIBUNAL CONSTITUCIONAL": "Tribunal Constitucional", "CONGRESO DE LA REPUBLICA": "Congreso de la República",
    "FUERO MILITAR POLICIAL": "Fuero Militar Policial", "JURADO NACIONAL DE ELECCIONES-JNE": "Jurado Nacional de Elecciones",
}

# Cada estado: color, símbolo y orden. El símbolo y la palabra acompañan siempre al color.
ESTADOS = {
    "Atrasado": ("#d03b3b", "!", 1), "En riesgo este año": ("#c98a00", "▲", 2), "Sin reportes recientes": ("#ec835a", "?", 3),
    "Por cerrar": ("#5b6068", "✓", 4), "Sin presupuesto este año": ("#8a9097", "–", 5), "En marcha": ("#0c8a0c", "●", 6),
}

st.markdown("""
<style>
.chip {display:inline-flex; align-items:center; gap:6px; padding:2px 10px; border-radius:999px; border:1px solid currentColor;
       font-size:0.9rem; white-space:nowrap; margin:0 6px 6px 0;}
.chip b {display:inline-grid; place-items:center; width:1.1em;}
.respuesta {font-size:1.05rem; margin:0 0 0.9rem 0;}
.pregunta {font-weight:700; margin:0;}
/* Estructura de desglose de la cartera completa: una caja arriba y los sectores debajo */
.edt-raiz {max-width:380px; margin:0.5rem auto 0 auto; text-align:center; padding:10px 14px; border:1.5px solid #103f91;
           border-radius:8px; background:rgba(16,63,145,0.08);}
.edt-linea {width:0; height:18px; margin:0 auto; border-left:1.5px solid rgba(128,128,128,0.6);}
.edt-hijos {display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:10px; padding-top:14px;
            border-top:1.5px solid rgba(128,128,128,0.6); margin-bottom:0.5rem;}
.edt-caja {padding:8px 10px; border:1px solid rgba(128,128,128,0.55); border-radius:8px; font-size:0.92rem;}
.edt-raiz b, .edt-caja b {display:block;}
.edt-raiz span, .edt-caja span {opacity:0.75;}
/* Tarjetas de indicadores: una pregunta, una cifra y una frase */
div[data-testid="stMarkdownContainer"] p.cifra {font-size:2rem; font-weight:700; line-height:1.15; margin:0.15rem 0 0.1rem 0;}
.explica {font-size:0.95rem; margin:0;}
div[data-testid="stMarkdownContainer"] p.rotulo {font-size:0.9rem; opacity:0.8; margin:0 0 0.35rem 0;}
ul.lineas {font-size:0.9rem; margin:0; padding-left:1.1rem;}
ul.lineas li {margin:0 0 0.15rem 0;}
/* Detalles dentro de la ficha: brechas y el texto original del reporte */
.detalle {font-size:0.92rem; opacity:0.85; margin:-0.6rem 0 0.9rem 0;}
ul.detalle {padding-left:1.2rem;}
.cita {font-size:0.92rem; font-style:italic; opacity:0.85; border-left:3px solid rgba(128,128,128,0.5);
       padding-left:0.6rem; margin:-0.6rem 0 0.9rem 0;}
/* Barras horizontales de los problemas reportados (un solo color; el número va al lado de la barra) */
.barras {display:grid; grid-template-columns:minmax(140px, 22rem) 1fr; gap:6px 12px; align-items:center; font-size:0.92rem;}
.barra {display:flex; align-items:center; gap:8px;}
.barra i {display:block; height:10px; border-radius:0 4px 4px 0; background:#2a78d6;}
@media (prefers-color-scheme: dark) {.barra i {background:#3987e5;}}
/* Avance y gasto en la ficha: barras de 0 a 100 sobre una pista gris, con el valor al lado */
.avance {display:grid; grid-template-columns:minmax(120px, 11rem) minmax(100px, 1fr) minmax(150px, auto); gap:5px 10px;
         align-items:center; font-size:0.92rem; margin:0 0 0.4rem 0;}
.avance .grupo {grid-column:1 / -1; opacity:0.8; margin-top:0.35rem;}
.pista {height:10px; background:rgba(128,128,128,0.18); border-radius:0 4px 4px 0;}
.pista i {display:block; height:100%; background:#2a78d6; border-radius:0 4px 4px 0;}
@media (prefers-color-scheme: dark) {.pista i {background:#3987e5;}}
.nota {font-size:0.92rem; opacity:0.85; margin:0.2rem 0 0.9rem 0;}
</style>""", unsafe_allow_html=True)

def chip(estado, n=None):
    color, simbolo, _ = ESTADOS[estado]
    cuenta = f" · {n:,}" if n is not None else ""
    return f'<span class="chip" style="color:{color}"><b>{simbolo}</b>{html.escape(estado)}{cuenta}</span>'

def millones(x):
    if pd.isna(x):
        return "sin dato"
    return f"S/ {x / 1e9:,.1f} mil millones" if x >= 1e9 else (f"S/ {x / 1e6:,.1f} millones" if x >= 1e6 else f"S/ {x / 1e3:,.0f} mil")

def plural(n, palabra):
    """Cuenta en palabras sin decimales: 1 -> '1 proyecto'; 715 -> '715 proyectos'."""
    n = int(n)
    return f"{n:,} {palabra}" if n == 1 else f"{n:,} {palabra}s"

def porc(x):
    """Porcentaje para mostrar. Antes: 0.293 | Después: '29 %'."""
    return "sin dato" if pd.isna(x) else f"{100 * x:.0f} %"

def meses(m):
    return "1 mes" if int(m) == 1 else f"{int(m)} meses"

def pie_de_pagina():
    """PASO 5.6: Cómo se calculan el estado y los indicadores (transparencia) y fuente de los datos."""
    with st.expander("¿Cómo se calculan el estado y los indicadores?"):
        st.markdown(
            "**Estado de cada proyecto**\n"
            "- **Atrasado:** la fecha de término registrada ya pasó y el avance es menor a 95 %.\n"
            "- **En riesgo este año:** tiene presupuesto 2026 y lleva gastado menos de la mitad.\n"
            "- **Sin reportes recientes:** ya empezó, pero su último reporte de avance (formato 12-B) tiene más de 180 días.\n"
            "- **Por cerrar:** está prácticamente terminado (95 % o más) y falta el cierre formal.\n"
            "- **Sin presupuesto este año:** está aprobado, no ha empezado y no tiene presupuesto en 2026.\n"
            "- **En marcha:** ninguna de las anteriores.\n\n"
            "El avance es el que declaró la entidad en el último año (todos los componentes). Si no lo declaró, se usa el "
            "porcentaje gastado del costo. Reglas de ejemplo, por validar.\n\n"
            "**Indicadores de la cartera**\n"
            "- **Brechas:** el vínculo que la entidad registró entre el proyecto y una brecha de servicio.\n"
            "- **Falta gastar este año:** presupuesto 2026 menos lo ya gastado (devengado).\n"
            "- **Cambio de costo:** costo actual frente al monto con que se aprobó el proyecto.\n"
            "- **Problemas:** el último reporte de seguimiento (formato 12-B), clasificado por temas con palabras clave. "
            "Son problemas que ya ocurren, no riesgos.\n"
            "- **Financiamiento:** presupuesto 2026 o montos en la programación multianual (se toma su primer año como 2026).\n"
            "- **Avance y gasto:** el avance lo declara la entidad (\"toda la inversión\" incluye gestión, expediente técnico, "
            "supervisión y liquidación; \"solo obra y equipos\", no). El gasto es lo devengado. Para compararlos se usa lo gastado "
            "hasta el mes de la declaración. Se parece al valor ganado, pero el avance es autodeclarado y el gasto incluye adelantos.\n"
            "- **Atraso:** meses desde la última fecha de fin registrada; frente al plan original puede ser mayor. "
            "**Plan de gasto:** lo gastado de enero a octubre de 2026 frente a lo que la entidad planeó gastar en esos meses.")
    st.caption(f"Fuente: MEF, Datos Abiertos (Detalle de inversiones, Inversiones y brechas, Formato 12-B), al {FECHA_DATOS}.")

def tarjeta(columna, pregunta, cifra, rotulo, lineas=()):
    """Una tarjeta de lectura rápida: la pregunta, una cifra grande con una etiqueta corta, y hasta 3 líneas que
    empiezan con su número. Cada línea es (número, texto). Antes: un párrafo | Después: cifras primero, texto después."""
    filas = "".join(f"<li><b>{html.escape(str(n))}</b> {html.escape(t)}</li>" for n, t in lineas)
    with columna.container(border=True):
        st.markdown(f'<p class="pregunta">{pregunta}</p><p class="cifra">{cifra}</p><p class="rotulo">{rotulo}</p>'
                    + (f'<ul class="lineas">{filas}</ul>' if filas else ""), unsafe_allow_html=True)

# Nombres cortos de los temas de problemas, para las tarjetas
TEMA_CORTO = {"Presupuesto o financiamiento": "presupuesto", "Liquidación o cierre pendiente": "liquidación o cierre",
              "Permisos, trámites o pronunciamientos de otras entidades": "permisos y trámites",
              "Expediente técnico o estudios": "expediente técnico", "Documentos o información pendiente": "documentos pendientes",
              "Contratista o contrato": "contratista", "Arbitraje o controversias": "arbitraje", "Proceso de contratación": "contratación",
              "Aún no programada o en espera de inicio": "en espera de inicio", "Terreno o saneamiento legal": "terreno",
              "Obra paralizada o suspendida": "obra paralizada", "Adicionales o ampliación de plazo": "adicionales o ampliación",
              "Clima o desastres": "clima o desastres", "Conflictos sociales": "conflictos sociales",
              "Observaciones de control (Contraloría)": "Contraloría"}
n_ = lambda x: f"{int(x):,}"   # número entero con separador de miles

def tablero(clave, cartera):
    """PASO 5.2a: los indicadores de cartera del Proceso 7 en seis tarjetas, con el mismo estilo de pregunta y respuesta.
    Insumo: la fila de indicadores_cartera del ministerio elegido (o de la cartera completa) | Resultado: tarjetas y detalles."""
    r = indicadores.loc[clave]
    st.subheader("¿Cómo está la cartera?")
    # Seis tarjetas en dos filas de tres (las brechas van solo en su desplegable, "Ver todas las brechas que abordan")
    fila1, fila2 = st.columns(3), st.columns(3)

    # P1: brechas de esta cartera, para el desplegable: cuántos proyectos apuntan a cada una, cuánto cuestan esos proyectos
    #   y cuánto aportan (en la unidad de cada brecha).
    #   Antes: una fila por proyecto y brecha | Después: una fila por brecha, de la que tiene más proyectos a la que tiene menos
    b = brechas_todas[brechas_todas["cui"].isin(cartera["cui"])]
    costos = cartera.drop_duplicates("cui").set_index("cui")["costo"]
    por_brecha = (b.drop_duplicates(["indicador", "cui"]).assign(costo=lambda d: d["cui"].map(costos))
                  .groupby("indicador").agg(proyectos=("cui", "nunique"), costo=("costo", "sum"))
                  .sort_values("proyectos", ascending=False))

    # P2: presupuesto 2026 que falta gastar
    if r["pim_2026"] > 0:
        tarjeta(fila1[0], "¿Cuánto falta gastar este año?", porc(r["pct_pendiente_2026"]), "del presupuesto 2026 sin gastar",
                [(millones(r["pendiente_2026"]), f"de {millones(r['pim_2026'])}"),
                 (n_(DIAS_AL_CIERRE), "días para cerrar el año"),
                 (n_(r["n_mas_mitad_pendiente"]), "con más de la mitad sin gastar")])
    else:
        tarjeta(fila1[0], "¿Cuánto falta gastar este año?", "—", "sin presupuesto 2026 en estos datos")

    # P3: cambio de costo desde la aprobación
    p = r["pct_desv_total"]
    if pd.notna(p):
        tarjeta(fila1[1], "¿Cuánto cambiaron los costos?", f"{'+' if p >= 0 else '−'}{abs(100 * p):.0f} %", "desde que se aprobaron",
                [(millones(abs(r["desv_total"])), "más" if p >= 0 else "menos"),
                 (n_(r["n_subio_mas_20"]), "con alza de más de 20 %"),
                 (n_(r["n_mas_que_duplico"]), "con costo duplicado o más")])
    else:
        tarjeta(fila1[1], "¿Cuánto cambiaron los costos?", "—", "sin montos para comparar")

    # Avance frente a gasto (aproximación al valor ganado): solo proyectos con avance declarado en 2026
    #   Cifra principal: cuánto avance declaran por cada sol gastado. S/ 1 = avanzan al mismo ritmo que gastan;
    #   menos de S/ 1 = gastan más rápido de lo que avanzan
    if r["n_comparables_avance"] > 0:
        indice = f"{r['indice_avance_gasto']:.2f}".replace(".", ",")
        tarjeta(fila1[2], "¿Avanzan al ritmo de lo que gastan?", f"S/ {indice}",
                "de avance declarado por cada sol gastado (S/ 1 = al mismo ritmo)",
                [(n_(r["n_comparables_avance"]), "con avance declarado en 2026 (base del cálculo)"),
                 (n_(r["n_alerta_gasto_avance"]), "con gasto 30 puntos o más por encima de su avance")])
    else:
        tarjeta(fila1[2], "¿Avanzan al ritmo de lo que gastan?", "—", "ningún proyecto declaró su avance en 2026")

    # P4: problemas del último reporte de seguimiento (los 3 temas más comunes, con nombre corto)
    con_problemas = cartera[cartera["clase_problema"] == "Reporta problemas"]
    temas = con_problemas["temas"].str.split("; ").explode().value_counts()
    comunes = temas.drop("Otros problemas", errors="ignore").head(3)
    tarjeta(fila2[0], "¿Qué problemas reportan?", n_(len(con_problemas)), "con problemas reportados",
            [(n_(k), TEMA_CORTO.get(t, t.lower())) for t, k in comunes.items()])

    # P5: financiamiento
    tarjeta(fila2[1], "¿Tienen financiamiento?", porc(r["pct_n_presupuesto"]), "con presupuesto 2026",
            [(n_(r["n_prog_2026_sin_pim"]), "con programación 2026, pero sin presupuesto"),
             (n_(r["n_prog_2027"]), "con programación desde 2027"),
             (n_(r["n_sin_fin_falta"]), f"sin presupuesto ni programación · {millones(r['saldo_sin_fin_falta'])} por ejecutar")])

    # P7: atraso y cumplimiento del plan de gasto
    plan = ([(porc(r["pct_cumple_programacion"]), "de lo planeado gastado (ene–oct)")]
            if pd.notna(r["pct_cumple_programacion"]) else [])
    if r["n_atrasados"] > 0:
        tarjeta(fila2[2], "¿Cuánto atraso hay?", meses(r["mediana_meses_atraso"]), f"atraso típico de los {n_(r['n_atrasados'])} atrasados",
                [(n_(r["n_atraso_mas_36"]), "con más de 3 años")] + plan)
    else:
        tarjeta(fila2[2], "¿Cuánto atraso hay?", "0", "proyectos atrasados", plan)

    # Detalles a un clic: todos los temas de problemas y los cinco grupos de financiamiento
    d1, d2 = st.columns(2)
    with d1.expander("Ver todos los problemas reportados"):
        if len(temas):
            maximo = temas.max()
            filas = "".join(f'<span>{html.escape(t)}</span><span class="barra" title="{html.escape(t)}: {n:,} proyectos">'
                            f'<i style="width:{max(2, 85 * n / maximo):.0f}%"></i>{n:,}</span>' for t, n in temas.items())
            st.markdown(f'<div class="barras">{filas}</div>', unsafe_allow_html=True)
            st.caption("Un proyecto puede tener varios temas. Clasificación con palabras clave del último reporte de seguimiento.")
        else:
            st.write("Ningún proyecto reporta problemas.")
    with d2.expander("Ver el detalle del financiamiento"):
        grupos = [("Con presupuesto 2026", "con_pim"), ("Programado para 2026, sin presupuesto", "prog_2026_sin_pim"),
                  ("Programado para 2027 en adelante", "prog_2027"), ("Sin financiamiento – le falta ejecutar", "sin_fin_falta"),
                  ("Sin financiamiento – prácticamente terminado", "sin_fin_terminado")]
        st.dataframe(pd.DataFrame([{"Grupo": g, "Proyectos": int(r[f"n_{k}"]), "Costo": millones(r[f"costo_{k}"]),
                                    "Falta ejecutar": millones(r[f"saldo_{k}"])} for g, k in grupos]),
                     hide_index=True, width="stretch")

    # Todas las brechas: cuántos proyectos apuntan a cada una y cuánto aportan entre todos, en la unidad de la brecha
    #   (personas, establecimientos, locales…). Es el "tamaño" del impacto que registran las entidades.
    with st.expander("Ver todas las brechas que abordan"):
        if len(b):
            aporte = (b.dropna(subset=["aporte"]).groupby(["indicador", "unidad_medida"])["aporte"].sum().reset_index())
            aporte["texto"] = aporte.apply(lambda f: f"{f['aporte']:,.0f} {f['unidad_medida']}", axis=1)
            aporte_txt = aporte.groupby("indicador")["texto"].agg("; ".join)
            tabla_brechas = pd.DataFrame({"Brecha": por_brecha.index, "Proyectos": por_brecha["proyectos"].to_numpy(),
                                          # costo de los proyectos que apuntan a la brecha, en millones (número, para poder ordenar)
                                          "Valorización (S/ millones)": (por_brecha["costo"] / 1e6).round(1).to_numpy(),
                                          "Aporte total registrado": [aporte_txt.get(t, "sin dato") for t in por_brecha.index]})
            st.dataframe(tabla_brechas, hide_index=True, width="stretch",
                         column_config={"Brecha": st.column_config.TextColumn("Brecha", width="large"),
                                        "Valorización (S/ millones)": st.column_config.NumberColumn(
                                            "Valorización (S/ millones)", format="localized",
                                            help="Costo actual de los proyectos que apuntan a esta brecha")})
            st.caption("Valorización: costo actual de los proyectos que apuntan a cada brecha. Un proyecto con varias brechas "
                       "suma su costo en cada una, así que la suma de la columna puede superar el costo de la cartera. "
                       "Aporte: lo que las entidades registran que cada proyecto aportará para cerrar la brecha "
                       "(por ejemplo, personas atendidas o establecimientos mejorados), sumado entre proyectos. "
                       "Puede haber superposición entre proyectos de una misma zona, y algunas sumas no son creíbles por errores de registro "
                       "(por ejemplo, más establecimientos de salud de los que existen en el país): tómalas como referencia.")
        else:
            st.write("Ningún proyecto de esta cartera tiene brechas registradas.")

# ============================================================
# PASO 5.2: Paso 1 de la página — elegir la cartera completa o un ministerio
# ============================================================
st.title("Cartera de inversiones del Estado")
st.caption(f"Ministerios y entidades del gobierno nacional · datos del Ministerio de Economía y Finanzas (MEF) al {FECHA_DATOS}")

TODO = "CARTERA COMPLETA"   # opción especial: todos los ministerios y entidades juntos
conteo = inversiones.groupby("sector").size().sort_values(ascending=False)
opciones = [TODO] + list(conteo.index)
por_defecto = 0   # la página abre en la cartera completa
def reiniciar_filtros():
    """Al cambiar de ministerio, los estados elegidos vuelven a 'Todos los estados' (no se arrastran del ministerio anterior)."""
    for clave in ("estado_ministerio", "estado_unidad"):
        st.session_state.pop(clave, None)

sector = st.selectbox("¿Qué cartera quieres ver?", opciones, index=por_defecto, on_change=reiniciar_filtros,
                      format_func=lambda s: f"Cartera completa — {len(inversiones):,} proyectos" if s == TODO
                      else f"{NOMBRES.get(s, s.title())} — {conteo[s]:,} proyectos")
cartera = inversiones if sector == TODO else inversiones[inversiones["sector"] == sector]
nombre_sector = NOMBRES.get(sector, sector.title())

TODOS = "Todos los estados"
ORDEN_ESTADOS = sorted(ESTADOS, key=lambda e: ESTADOS[e][2])

def elegir_estado(columna, tabla, clave):
    """Lista de estados con su número de proyectos entre paréntesis; la primera opción es 'Todos los estados'.
    Antes: la tabla completa | Después: solo las filas del estado elegido (o todas)."""
    cuenta = tabla["estado"].value_counts()
    elegido = columna.selectbox("Estado", [TODOS] + ORDEN_ESTADOS, key=clave,
                                format_func=lambda e: f"{e} ({len(tabla) if e == TODOS else int(cuenta.get(e, 0)):,})")
    return tabla if elegido == TODOS else tabla[tabla["estado"] == elegido]

# ============================================================
# PASO 5.2b: NIVEL 1 — Cartera completa (sin cambios): proyectos, costo y atrasados; los indicadores; y la estructura de
#            desglose: "Cartera total" arriba y cada ministerio o entidad debajo, con su número de proyectos y su costo.
#   Antes: 12 731 filas (una por proyecto) | Después: 33 cajas (una por ministerio o entidad), de mayor a menor costo
# ============================================================
if sector == TODO:
    c1, c2, c3 = st.columns(3)
    c1.metric("Proyectos", f"{len(cartera):,}")
    c2.metric("Cuestan en total", millones(cartera["costo"].sum()))
    c3.metric("Atrasados", f"{(cartera['estado'] == 'Atrasado').sum():,}")
    st.markdown("".join(chip(e, int((cartera["estado"] == e).sum())) for e in ORDEN_ESTADOS), unsafe_allow_html=True)
    tablero(sector, cartera)
    sectores = (inversiones.groupby("sector").agg(n=("id", "size"), costo=("costo", "sum"))
                .sort_values("costo", ascending=False))
    st.subheader("La cartera por ministerio o entidad")
    cajas = "".join(f'<div class="edt-caja"><b>{html.escape(NOMBRES.get(s.Index, s.Index.title()))}</b>'
                    f'<span>{plural(s.n, "proyecto")} · {millones(s.costo)}</span></div>' for s in sectores.itertuples())
    st.markdown(f'<div class="edt-raiz"><b>Cartera total</b><span>{plural(len(inversiones), "proyecto")} · '
                f'{millones(inversiones["costo"].sum())}</span></div><div class="edt-linea"></div>'
                f'<div class="edt-hijos">{cajas}</div>', unsafe_allow_html=True)
    st.caption("Ordenados de mayor a menor costo. Para ver los proyectos, elige un ministerio o entidad arriba.")
    pie_de_pagina()
    st.stop()   # en la cartera completa la página termina aquí

# ============================================================
# PASO 5.3: NIVEL 2 — Ministerio o entidad: elegir un estado (o todos) y ver cuántos proyectos son y cuánto cuestan.
#           Debajo, el árbol (ministerio -> sus 6 unidades con más proyectos) con el estado elegido. El mapa va al final (PASO 5.4c).
# ============================================================
st.subheader(nombre_sector)
m1, m2, m3 = st.columns([1.6, 1, 1.2])
cartera_estado = elegir_estado(m1, cartera, "estado_ministerio")
m2.metric("Proyectos", f"{len(cartera_estado):,}")
m3.metric("Cuestan en total", millones(cartera_estado["costo"].sum()))

def etiqueta(texto, ancho=26):
    return "\\n".join(textwrap.wrap(texto.replace('"', "'"), ancho))

def rgb(hexa, alfa=210):
    """'#d03b3b' -> [208, 59, 59, 210]: el formato de color que usa el mapa."""
    return [int(hexa[i:i + 2], 16) for i in (1, 3, 5)] + [alfa]

# Árbol del ministerio con el estado elegido
with st.expander("Árbol de la cartera", expanded=True):
    # Árbol con el estado elegido. Antes: filas de proyectos | Después: una caja por unidad con su número de proyectos y su costo
    unidades_estado = (cartera_estado.groupby("unidad")
                       .agg(n=("id", "size"), atrasados=("estado", lambda s: int((s == "Atrasado").sum())), costo=("costo", "sum"))
                       .sort_values("n", ascending=False))
    # Tamaño homogéneo: todas las cajas miden lo mismo (fixedsize) y el árbol tiene SIEMPRE 7 espacios (6 unidades + "Otras").
    # Si hay menos unidades, los espacios que sobran se dibujan invisibles a ambos lados. Así, al estirarse al ancho de la
    # página, la escala es la misma con 7 unidades que con 2, y las cajas no se agrandan.
    ESPACIOS, UNIDADES_VISIBLES = 7, 6
    # Letra grande (16) porque el árbol se reduce al estirarse a 7 espacios; nombre en hasta 3 líneas, y número y costo aparte
    CAJA = 'shape=box, fixedsize=true, width=1.75, height=1.4, fontname="Helvetica", fontsize=16'
    etiqueta_caja = lambda t: "\\n".join(textwrap.wrap(t.replace('"', "'"), 15, max_lines=3, placeholder="…"))
    nodos = [f'raiz [label="{etiqueta(nombre_sector, 30)}\\n{plural(len(cartera_estado), "proyecto")}\\n{millones(cartera_estado["costo"].sum())}", '
             f'shape=box, fixedsize=true, width=3.4, height=1.25, style="rounded,filled", fillcolor="#e9eef8", color="#103f91", '
             f'fontname="Helvetica", fontsize=15];']
    hijos = []
    # itertuples() conserva los números enteros; iterrows() los convertía en decimales (715 -> "715.0")
    for i, u in enumerate(unidades_estado.head(UNIDADES_VISIBLES).itertuples()):
        borde = "#d03b3b" if u.atrasados else "#9aa0a6"
        hijos.append((f"u{i}", f'label="{etiqueta_caja(u.Index.title())}\\n{plural(u.n, "proyecto")}\\n{millones(u.costo)}", '
                               f'{CAJA}, style="rounded", color="{borde}"'))
    if len(unidades_estado) > UNIDADES_VISIBLES:
        resto = unidades_estado.iloc[UNIDADES_VISIBLES:]
        hijos.append(("otras", f'label="Otras {len(resto)}\\nunidades\\n{plural(resto["n"].sum(), "proyecto")}\\n{millones(resto["costo"].sum())}", '
                               f'{CAJA}, style="rounded,dashed", color="#9aa0a6"'))
    sobran = ESPACIOS - len(hijos)
    vacios = [(f"vacio{i}", f'label="", {CAJA}, style=invis') for i in range(sobran)]
    # Orden de izquierda a derecha: la mitad de los vacíos, las unidades reales y la otra mitad (así quedan centradas)
    for nombre, atributos in vacios[:sobran // 2] + hijos + vacios[sobran // 2:]:
        nodos.append(f"{nombre} [{atributos}];")
        nodos.append(f"raiz -> {nombre}" + (" [style=invis];" if nombre.startswith("vacio") else ";"))
    st.graphviz_chart("digraph { rankdir=TB; ordering=out; nodesep=0.15; edge [color=\"#9aa0a6\", arrowhead=none]; "
                      + " ".join(nodos) + " }", width="stretch")
    st.caption("En rojo, las unidades con al menos un proyecto atrasado. Se muestran las 6 unidades con más proyectos; el resto va en «Otras unidades».")

tablero(sector, cartera)

# ============================================================
# PASO 5.4: NIVEL 3 — Unidad ejecutora: elegir una unidad (o todas) y un estado (o todos); ver cuántos proyectos son y cuánto
#           cuestan; buscar, filtrar y ordenar; y mostrar los proyectos en una lista (el nivel 4 es la ficha de cada uno)
# ============================================================
st.subheader("Unidades ejecutoras y sus proyectos")
unidades = cartera.groupby("unidad").size().sort_values(ascending=False)
f1, f2, f3, f4 = st.columns([2, 1.5, 0.8, 1.6])
lista_unidades = ["Todas las unidades"] + list(unidades.index)
unidad = f1.selectbox("Unidad ejecutora", lista_unidades,
                      format_func=lambda u: u if u == "Todas las unidades" else f"{u.title()} — {unidades[u]:,}")
vista = cartera if unidad == "Todas las unidades" else cartera[cartera["unidad"] == unidad]
vista = elegir_estado(f2, vista, "estado_unidad")
# Órdenes posibles de la lista: (columnas, ¿de menor a mayor?) para sort_values()
ORDENES = {"Estado: primero los que requieren atención": (["_orden", "costo"], [True, False]),
           "Costo: de mayor a menor": (["costo"], [False]), "Costo: de menor a mayor": (["costo"], [True]),
           "Ejecución acumulada: de menor a mayor": (["ejec_acum"], [True]),
           "Ejecución acumulada: de mayor a menor": (["ejec_acum"], [False]),
           "Ejecución 2026: de menor a mayor": (["ejec_2026"], [True]),
           "Atraso: de mayor a menor": (["meses_atraso"], [False]), "Nombre: de la A a la Z": (["que_es"], [True])}
b1, b2, b3 = st.columns([1, 1.2, 1.8])
busqueda = b1.text_input("Buscar", placeholder="Nombre, lugar o CUI")
orden = b2.selectbox("Ordenar por", list(ORDENES))
b3.write("")
solo_alerta = b3.toggle("Solo los que gastaron 30 puntos o más por encima de lo que declaran haber avanzado")
if solo_alerta:
    vista = vista[vista["alerta_gasto_avance"].fillna(False).astype(bool)]
if busqueda:
    q = busqueda.strip().lower()
    vista = vista[vista["que_es"].str.lower().str.contains(q, regex=False) | vista["lugar"].str.lower().str.contains(q, regex=False)
                  | vista["id"].str.contains(q, regex=False)]
# sort_values(): reordena las filas según el orden elegido; los que no tienen dato (p. ej., sin atraso) van al final
columnas_orden, ascendente = ORDENES[orden]
vista = (vista.assign(_orden=vista["estado"].map(lambda e: ESTADOS[e][2]))
         .sort_values(columnas_orden, ascending=ascendente, na_position="last"))
# Las cifras del nivel 3 van junto a los selectores, ya con todos los filtros aplicados
f3.metric("Proyectos", f"{len(vista):,}")
f4.metric("Cuestan en total", millones(vista["costo"].sum()))

# ============================================================
# PASO 5.5: Paso 3 — la ficha de cinco preguntas (ventana emergente)
# ============================================================
@st.dialog("Ficha del proyecto", width="large")
def ficha(fila):
    st.markdown(chip(fila["estado"]) + f' <span style="color:#5b6068">{html.escape(fila["estado_motivo"])}</span>', unsafe_allow_html=True)
    texto = lambda col: fila[col] if isinstance(fila.get(col), str) else ""   # columnas del Proceso 7 (vacío si falta)

    # Detalle bajo "¿Qué problema resuelve?" (P1): la frase y la lista de brechas a las que apunta
    brechas = [b for b in texto("brechas_lista").split(" | ") if b]
    detalle_brecha = f'<p class="detalle">{html.escape(texto("frase_brecha"))}</p>'
    if brechas:
        detalle_brecha = (f'<p class="detalle">{html.escape(texto("frase_brecha"))}</p><ul class="detalle">'
                          + "".join(f"<li>{html.escape(b)}</li>" for b in brechas) + "</ul>")
    # Detalle bajo "¿Qué problemas reporta?" (P4): el texto original del reporte, recortado
    detalle_problema = ""
    if texto("clase_problema") == "Reporta problemas" and texto("problema_12b"):
        original = fila["problema_12b"] if len(fila["problema_12b"]) <= 300 else fila["problema_12b"][:297].rsplit(" ", 1)[0] + "…"
        detalle_problema = f'<p class="cita">«{html.escape(original)}»</p>'

    # (pregunta, respuesta, detalle opcional en HTML)
    # "¿Cuánto se ha ejecutado?": solo dos medidas, en barras de 0 a 100 (lo demás va en "Para especialistas")
    #   1) Ejecución presupuestal 2026: devengado 2026 / presupuesto 2026 (PIM)
    #   2) Ejecución acumulada: devengado de toda su vida / costo actualizado
    def barra(etiqueta, valor, detalle_monto):
        if pd.isna(valor):
            return f"<span>{etiqueta}</span><span></span><span>{detalle_monto}</span>"
        cifra = f"{valor:.1f}".replace(".", ",") if abs(valor) < 10 else f"{valor:.0f}"   # 3,5 % y 2,5 % no se confunden
        return (f'<span>{etiqueta}</span><span class="pista" title="{etiqueta}: {cifra} %">'
                f'<i style="width:{min(max(valor, 0), 100):.0f}%"></i></span><span>{cifra} % · {detalle_monto}</span>')
    pim, dev_anio, dev_vida, costo = fila["pim_2026"], fila["dev_2026"], fila["dev_acumulado"], fila["costo"]
    partes = [
        barra("Ejecución presupuestal 2026", 100 * dev_anio / pim, f"{millones(dev_anio)} de {millones(pim)}")
        if pd.notna(pim) and pim > 0 else barra("Ejecución presupuestal 2026", float("nan"), "no tiene presupuesto 2026"),
        barra("Ejecución acumulada (toda su vida)", 100 * dev_vida / costo if costo else float("nan"),
              f"{millones(dev_vida)} de {millones(costo)}"),
    ]
    detalle_ejecucion = f'<div class="avance">{"".join(partes)}</div>'

    preguntas = [("¿Qué es?", f'{fila["que_es"]}. {fila["tipo_simple"]} en {fila["lugar"]}.', ""),
                 ("¿Qué problema resuelve?", fila["problema"], detalle_brecha),
                 ("¿Cuánto cuesta?", f'Cuesta {millones(costo)}. {texto("frase_costo")}'.strip(), ""),
                 ("¿Cuánto se ha ejecutado?", "", detalle_ejecucion),
                 ("¿Tiene financiamiento?", texto("frase_dinero"), ""),
                 ("¿Cuándo termina?", fila["cuando"], ""),
                 ("¿Cómo va?", f'{fila["estado"]}. {fila["estado_motivo"]} {texto("frase_programacion")}'.strip(), ""),
                 ("¿Qué problemas reporta?", texto("frase_problemas"), detalle_problema)]
    if fila["lo_que_frena"]:
        preguntas.append(("¿Qué lo frena?", fila["lo_que_frena"], ""))
    for pregunta, respuesta, detalle in preguntas:
        cuerpo = f'<p class="respuesta">{html.escape(respuesta)}</p>' if respuesta else ""
        st.markdown(f'<p class="pregunta">{pregunta}</p>{cuerpo}{detalle}', unsafe_allow_html=True)
    st.caption("El título lo redactó una IA a partir de la descripción técnica del MEF; el nombre oficial está en "
               "«Para especialistas». El resto del resumen se elaboró automáticamente con los datos del MEF."
               if fila["redactado_por_ia"] else "Resumen elaborado automáticamente a partir de los datos del MEF.")
    if fila["cui"]:
        st.link_button("Ver el detalle técnico en el MEF ↗", f'https://ofi5.mef.gob.pe/ssi/Ssi/Index?codigo={fila["cui"]}&tipo=2')
    with st.expander("Para especialistas (términos de Invierte.pe)"):
        st.markdown(
            f"- **Nombre oficial:** {fila['nombre']}\n"
            f"- **CUI:** {fila['id']} · **Unidad ejecutora:** {fila['unidad']}\n"
            f"- **UEI:** {fila['uei'] or 'sin dato'} · **OPMI:** {fila['opmi'] or 'sin dato'}\n"
            f"- **PIM 2026:** {millones(fila['pim_2026'])} · **Devengado 2026:** {millones(fila['dev_2026'])}\n"
            f"- **Modalidad:** {fila['modalidad'] or 'sin dato'} · **Registrada en el PMI:** {fila['en_pmi']}\n"
            f"- **Brecha (texto del MEF):** {fila['brecha'] or 'sin dato'}")
        # Avance que declara la entidad (12-B) frente a lo gastado: aproximación al valor ganado
        if pd.notna(fila.get("avance_ejecucion")) and pd.notna(fila.get("fecha_declaracion")):
            fisico = f"; solo obra y equipos: {fila['avance_fisico']:.0f} %" if pd.notna(fila.get("avance_fisico")) else ""
            st.markdown(f"**Avance que declara la entidad ({fila['fecha_declaracion']:%d/%m/%Y}):** toda la inversión "
                        f"{fila['avance_ejecucion']:.0f} %{fisico}.")
        else:
            st.markdown("**Avance que declara la entidad:** no lo ha declarado.")
        for frase in [texto("frase_indice"), texto("frase_alerta")]:
            if frase:
                st.markdown(frase)
        st.markdown("Para su estado se usa el avance que declaró la entidad." if fila.get("avance_fuente") == "declarado por la entidad"
                    else "Para su estado se usa lo gastado, porque la entidad no declaró su avance en el último año.")
        if pd.notna(fila["fecha_12b"]):
            st.markdown(f"**Último 12-B ({fila['fecha_12b']:%d/%m/%Y})**")
            for etq, col in [("Situación", "situacion_12b"), ("Problemas", "problema_12b"), ("Acciones", "acciones_12b")]:
                if fila[col]:
                    st.markdown(f"*{etq}:* {fila[col][:600]}")

# ============================================================
# PASO 5.4b: La lista de proyectos (una fila por proyecto). Al hacer clic en una fila se abre su ficha (nivel 4).
#   Antes: tarjetas de 3 en 3, 24 a la vez | Después: una tabla con todos, que se puede ordenar con el selector
#   o haciendo clic en el nombre de cada columna
# ============================================================
# Las cifras van junto al nombre, para que se vean sin desplazarse; el lugar y la unidad, al final
tabla = pd.DataFrame({
    "Estado": vista["estado"].map(lambda e: f"{ESTADOS[e][1]} {e}"),     # el símbolo acompaña al nombre del estado
    "Proyecto": vista["que_es"],
    "Costo (S/)": vista["costo"].round(0),
    # Las mismas dos medidas de "¿Cuánto se ha ejecutado?" en la ficha (el avance declarado queda para especialistas)
    "Ejecución 2026": vista["ejec_2026"].clip(0, 100).round(0),            # vacío si no tiene presupuesto 2026
    "Ejecución acumulada": vista["ejec_acum"].clip(0, 100).round(0),
    "Atraso (meses)": vista["meses_atraso"].fillna(0).astype(int),   # 0 si no está atrasado (la tabla mostraría "None")
    "Lugar": vista["lugar"],
})
if unidad == "Todas las unidades":
    tabla["Unidad ejecutora"] = vista["unidad"].str.title()
# Dos casillas al inicio de cada fila:
#   "Ver ficha": al marcarla se abre la ficha de ese proyecto
#   "Ubicar":    al marcarla, el proyecto se resalta en el mapa (al final de la página). Las marcas se guardan por proyecto,
#                así que se mantienen aunque se abra una ficha o cambie el orden
ubicar = set(st.session_state.get("ubicar_ids", []))
tabla.insert(0, "Ficha", False)
tabla.insert(1, "Mapa", vista["id"].isin(ubicar))
# La clave cambia con los filtros y después de abrir cada ficha: así la lista vuelve a mostrarse sin "Ver ficha" marcado
version = st.session_state.get("version_lista", 0)
clave_lista = f"lista_{version}_" + str(abs(hash((sector, unidad, len(vista), orden, busqueda, solo_alerta, tuple(vista["id"].head(3))))))
editada = st.data_editor(
    tabla, hide_index=True, width="stretch", height=min(38 + 35 * len(tabla), 460), key=clave_lista,
    disabled=[c for c in tabla.columns if c not in ("Ficha", "Mapa")],   # solo se marcan las casillas; los datos no se editan
    column_config={
        "Ficha": st.column_config.CheckboxColumn("Ver ficha", help="Marca la casilla para abrir la ficha del proyecto", width=90),
        "Mapa": st.column_config.CheckboxColumn("Ubicar", help="Marca la casilla para resaltar el proyecto en el mapa", width=75),
        # Anchos en píxeles para que las cifras clave se vean sin desplazarse; el lugar y la unidad quedan a la derecha
        "Estado": st.column_config.TextColumn("Estado", width=150),
        "Proyecto": st.column_config.TextColumn("Proyecto", width=290),
        "Costo (S/)": st.column_config.NumberColumn("Costo (S/)", format="localized", width=95),
        "Ejecución 2026": st.column_config.ProgressColumn("Ejecución 2026", min_value=0, max_value=100, format="%.0f%%",
                                                          help="Lo gastado en 2026 frente a su presupuesto 2026", width=115),
        "Ejecución acumulada": st.column_config.ProgressColumn("Ejecución acumulada", min_value=0, max_value=100, format="%.0f%%",
                                                               help="Lo gastado en toda su vida frente a su costo", width=125),
        "Atraso (meses)": st.column_config.NumberColumn("Atraso (meses)", format="%d", width=95),
    })
st.caption(plural(len(vista), "proyecto") + ("" if unidad == "Todas las unidades" else f" de {unidad.title()}")
           + ". Marca «Ver ficha» para abrir la ficha de un proyecto, o «Ubicar» para resaltarlo en el mapa (al final de la página).")

# Actualizar las marcas de "Ubicar" de los proyectos que están en la lista (los demás conservan su marca)
#   Antes: casillas en la tabla | Después: el conjunto de proyectos marcados, guardado entre clics
visibles = set(vista["id"])
marcados_mapa = set(vista.loc[editada.index[editada["Mapa"]], "id"])
st.session_state["ubicar_ids"] = sorted((ubicar - visibles) | marcados_mapa)

# Abrir la ficha de la fila marcada. La tabla conserva el índice de 'vista', así que se busca la fila por ese índice.
marcadas = editada.index[editada["Ficha"]].tolist()
abierta = False                      # solo se puede abrir una ficha (ventana) a la vez
if marcadas:
    st.session_state["version_lista"] = version + 1     # la próxima vez la lista aparece sin la casilla marcada
    ficha(vista.loc[marcadas[0]])
    abierta = True

# Enlace directo a una ficha: http://localhost:8501/?ficha=CUI (sirve para compartir un proyecto y para la prueba automática)
pedido = st.query_params.get("ficha")
if pedido and not abierta and st.session_state.get("ficha_enlace") != pedido:
    encontrados = inversiones[inversiones["id"] == pedido]
    if len(encontrados):
        st.session_state["ficha_enlace"] = pedido
        ficha(encontrados.iloc[0])

# ============================================================
# PASO 5.4c: Mapa (versión rápida, con pydeck, que viene con Streamlit), al final de la página.
#   Muestra los mismos proyectos de la lista (con su unidad, estado, búsqueda y filtro): un punto por proyecto con
#   coordenadas, del color de su estado. Antes: lat y lon de cada proyecto | Después: puntos en el mapa del Perú;
#   al pasar el cursor, nombre, estado, costo y avance
# ============================================================
with st.expander("Mapa: ¿dónde están los proyectos de la lista?", expanded=True):
    puntos = vista.dropna(subset=["lat", "lon"])
    if len(puntos):
        datos_mapa = pd.DataFrame({
            "lat": puntos["lat"], "lon": puntos["lon"], "color": puntos["estado"].map(lambda e: rgb(ESTADOS[e][0])),
            "titulo": puntos["que_es"].str.slice(0, 90), "estado": puntos["estado"],
            "costo": puntos["costo"].map(millones),
            "avance": puntos["ejec_acum"].map(lambda a: f"{a:.0f} % de ejecución acumulada" if pd.notna(a) else "")})
        capa = pdk.Layer("ScatterplotLayer", data=datos_mapa, get_position=["lon", "lat"], get_fill_color="color",
                         get_radius=3000, radius_min_pixels=4, radius_max_pixels=12, pickable=True,
                         stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1)
        capas = [capa]
        # Proyectos marcados con "Ubicar": un anillo azul grande encima de su punto, y el mapa se centra en el primero
        resaltados = datos_mapa[puntos["id"].isin(st.session_state.get("ubicar_ids", [])).to_numpy()]
        vista_inicial = pdk.ViewState(latitude=-9.6, longitude=-75.0, zoom=4.2)
        if len(resaltados):
            capas.append(pdk.Layer("ScatterplotLayer", data=resaltados, get_position=["lon", "lat"], filled=False, stroked=True,
                                   get_radius=9000, radius_min_pixels=14, radius_max_pixels=30,
                                   get_line_color=[16, 63, 145, 255], line_width_min_pixels=4, pickable=False))
            vista_inicial = pdk.ViewState(latitude=float(resaltados["lat"].iloc[0]), longitude=float(resaltados["lon"].iloc[0]),
                                          zoom=6.5 if len(resaltados) == 1 else 5)
        st.pydeck_chart(pdk.Deck(layers=capas, map_provider="carto", map_style="light", initial_view_state=vista_inicial,
                                 tooltip={"html": "<b>{titulo}</b><br/>{estado} · {costo} · {avance}"}), height=480)
        # Leyenda: el color siempre va con el nombre del estado y su símbolo
        st.markdown("".join(chip(e, int((puntos["estado"] == e).sum())) for e in ORDEN_ESTADOS if (puntos["estado"] == e).any()),
                    unsafe_allow_html=True)
        # Qué proyectos están resaltados (y cuáles no se pueden ubicar por no tener coordenadas)
        marcados = vista[vista["id"].isin(st.session_state.get("ubicar_ids", []))]
        if len(marcados):
            con_punto = marcados.dropna(subset=["lat", "lon"])
            sin_punto = marcados[marcados["lat"].isna() | marcados["lon"].isna()]
            texto_marcados = "; ".join(f"{q[:70]} ({l})" for q, l in zip(con_punto["que_es"], con_punto["lugar"]))
            if len(con_punto):
                st.markdown(f'<p class="nota"><b style="color:#103f91">◯</b> Resaltado en el mapa: {html.escape(texto_marcados)}</p>',
                            unsafe_allow_html=True)
            if len(sin_punto):
                st.markdown(f'<p class="nota">Sin coordenadas registradas, no se puede ubicar: '
                            f'{html.escape("; ".join(q[:70] for q in sin_punto["que_es"]))}</p>', unsafe_allow_html=True)
    st.caption(f"{len(puntos):,} de {len(vista):,} proyectos de la lista tienen coordenadas. La ubicación la registra la entidad; "
               "a veces es la de su oficina y no la de la obra.")

# ============================================================
# PASO 5.6: Cómo se calcula (transparencia) y fuente — definido arriba en pie_de_pagina()
# ============================================================
pie_de_pagina()
