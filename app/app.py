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
IA = RAIZ / "data" / "procesado" / "ia_respuestas.parquet"

@st.cache_data
def cargar():
    """Lee las cinco preguntas. Si existen respuestas de la IA (Proceso 6), las usa en lugar de las reglas."""
    tabla = pd.read_parquet(DATOS)
    tabla["redactado_por_ia"] = False
    tabla["lo_que_frena"] = ""
    if IA.exists():
        ia = pd.read_parquet(IA)[["id", "que_es", "problema", "lo_que_frena"]].rename(
            columns={"que_es": "que_es_ia", "problema": "problema_ia", "lo_que_frena": "frena_ia"})
        tabla = tabla.merge(ia, on="id", how="left")
        con_ia = tabla["que_es_ia"].fillna("") != ""
        tabla.loc[con_ia, "que_es"] = tabla.loc[con_ia, "que_es_ia"]
        tabla.loc[con_ia, "problema"] = tabla.loc[con_ia, "problema_ia"]
        tabla.loc[con_ia, "lo_que_frena"] = tabla.loc[con_ia, "frena_ia"]
        tabla.loc[con_ia, "redactado_por_ia"] = True
    # Indicadores de cartera del Proceso 7: las frases para la ficha y la clasificación de problemas de cada proyecto
    #   Antes: 1 fila por proyecto con las cinco preguntas | Después: la misma fila, con 8 columnas más
    frases = pd.read_parquet(PROCESADO / "indicadores_proyecto.parquet")[
        ["id", "brechas_lista", "frase_brecha", "frase_costo", "frase_dinero", "frase_problemas", "frase_programacion",
         "clase_problema", "temas", "pct_gastado_vida", "pct_gastado_2026", "frase_indice", "frase_alerta", "alerta_gasto_avance",
         "meses_atraso"]]
    return tabla.merge(frases, on="id", how="left")

@st.cache_data
def cargar_indicadores():
    """Una fila por ministerio o entidad, más la fila 'CARTERA COMPLETA' (Proceso 7)."""
    return pd.read_parquet(PROCESADO / "indicadores_cartera.parquet").set_index("sector")

inversiones = cargar()
indicadores = cargar_indicadores()
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
.cifra {font-size:1.9rem; font-weight:600; line-height:1.2; margin:0.15rem 0 0.2rem 0;}
.explica {font-size:0.95rem; margin:0;}
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

def tarjeta(columna, pregunta, cifra, explicacion):
    """Una tarjeta: la pregunta, una cifra grande y una frase que la explica."""
    with columna.container(border=True):
        st.markdown(f'<p class="pregunta">{pregunta}</p><p class="cifra">{cifra}</p><p class="explica">{explicacion}</p>',
                    unsafe_allow_html=True)

def tablero(clave, cartera):
    """PASO 5.2a: los indicadores de cartera del Proceso 7 en seis tarjetas, con el mismo estilo de pregunta y respuesta.
    Insumo: la fila de indicadores_cartera del ministerio elegido (o de la cartera completa) | Resultado: tarjetas y detalles."""
    r = indicadores.loc[clave]
    st.subheader("¿Cómo está la cartera?")
    fila1, fila2 = st.columns(4), st.columns(3)

    # Avance frente a gasto (aproximación al valor ganado): solo proyectos con avance declarado en 2026
    if r["n_comparables_avance"] > 0:
        indice = f"{r['indice_avance_gasto']:.2f}".replace(".", ",")
        tarjeta(fila1[3], "¿Avanzan al ritmo de lo que gastan?", f"{r['n_alerta_gasto_avance']:,.0f}",
                f"proyectos gastaron 30 puntos o más por encima del avance que declaran. En los {r['n_comparables_avance']:,.0f} "
                f"que declararon su avance en 2026: avance {porc(r['pct_avance_declarado'])}, gastado {porc(r['pct_gastado_comparable'])}; "
                f"por cada sol gastado, un avance de S/ {indice}.")
    else:
        tarjeta(fila1[3], "¿Avanzan al ritmo de lo que gastan?", "—", "Ningún proyecto declaró su avance en 2026.")

    # P1: brechas
    tarjeta(fila1[0], "¿A qué brechas apuntan?", porc(r["pct_con_brecha"]),
            f"de los proyectos están vinculados a una brecha de servicio. Con dos o más brechas: {r['n_varias_brechas']:,.0f}.")

    # P2: presupuesto 2026 que falta gastar
    if r["pim_2026"] > 0:
        tarjeta(fila1[1], "¿Cuánto falta gastar este año?", porc(r["pct_pendiente_2026"]),
                f"del presupuesto 2026: {millones(r['pendiente_2026'])} de {millones(r['pim_2026'])}, y quedan {DIAS_AL_CIERRE} días. "
                f"Con más de la mitad sin gastar: {plural(r['n_mas_mitad_pendiente'], 'proyecto')}.")
    else:
        tarjeta(fila1[1], "¿Cuánto falta gastar este año?", "—", "No tiene presupuesto 2026 registrado en estos datos.")

    # P3: cambio de costo desde la aprobación
    p = r["pct_desv_total"]
    if pd.notna(p):
        tarjeta(fila1[2], "¿Cuánto cambiaron los costos?", f"{'+' if p >= 0 else '−'}{abs(100 * p):.0f} %",
                f"desde que se aprobaron: hoy cuestan {millones(abs(r['desv_total']))} {'más' if p >= 0 else 'menos'}. "
                f"Subieron más de 20 %: {r['n_subio_mas_20']:,.0f}; más que duplicaron su costo: {r['n_mas_que_duplico']:,.0f}.")
    else:
        tarjeta(fila1[2], "¿Cuánto cambiaron los costos?", "—", "No hay montos para comparar.")

    # P4: problemas del último reporte de seguimiento
    con_problemas = cartera[cartera["clase_problema"] == "Reporta problemas"]
    temas = con_problemas["temas"].str.split("; ").explode().value_counts()
    comunes = temas.drop("Otros problemas", errors="ignore").head(3)
    lista = ", ".join(f"{t.lower()} ({n:,})" for t, n in comunes.items())
    tarjeta(fila2[0], "¿Qué problemas reportan?", f"{len(con_problemas):,}",
            (f"proyectos reportan problemas en su último seguimiento. Los más comunes: {lista}." if lista
             else "proyectos reportan problemas en su último seguimiento."))

    # P5: financiamiento
    tarjeta(fila2[1], "¿Tienen financiamiento?", porc(r["pct_n_presupuesto"]),
            f"de los proyectos tienen presupuesto 2026. Programados para 2026 pero sin presupuesto: {r['n_prog_2026_sin_pim']:,.0f}; "
            f"programados desde 2027: {r['n_prog_2027']:,.0f}. Sin presupuesto ni programación y con obra por hacer: "
            f"{r['n_sin_fin_falta']:,.0f} ({millones(r['saldo_sin_fin_falta'])} por ejecutar).")

    # P7: atraso y cumplimiento del plan de gasto
    plan = (f" Entre enero y octubre gastaron el {porc(r['pct_cumple_programacion'])} de lo que planearon gastar."
            if pd.notna(r["pct_cumple_programacion"]) else "")
    if r["n_atrasados"] > 0:
        tarjeta(fila2[2], "¿Cuánto atraso hay?", meses(r["mediana_meses_atraso"]),
                f"es el atraso típico: la mitad de los {r['n_atrasados']:,.0f} atrasados lleva más que eso. "
                f"Más de 3 años: {r['n_atraso_mas_36']:,.0f}.{plan}")
    else:
        tarjeta(fila2[2], "¿Cuánto atraso hay?", "0", f"proyectos atrasados.{plan}")

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

# ============================================================
# PASO 5.2: Paso 1 de la página — elegir la cartera completa o un ministerio
# ============================================================
st.title("Cartera de inversiones del Estado")
st.caption(f"Ministerios y entidades del gobierno nacional · datos del Ministerio de Economía y Finanzas (MEF) al {FECHA_DATOS}")

TODO = "CARTERA COMPLETA"   # opción especial: todos los ministerios y entidades juntos
conteo = inversiones.groupby("sector").size().sort_values(ascending=False)
opciones = [TODO] + list(conteo.index)
por_defecto = opciones.index("DESARROLLO E INCLUSION SOCIAL") if "DESARROLLO E INCLUSION SOCIAL" in opciones else 0
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
#           Debajo, el árbol (ministerio -> sus 8 unidades con más proyectos) y el mapa, ambos con el estado elegido.
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

# El árbol y el mapa se ven uno debajo del otro (sin pestañas, para que el mapa no quede escondido)
with st.expander("Árbol de la cartera", expanded=True):
    # Árbol con el estado elegido. Antes: filas de proyectos | Después: una caja por unidad con su número de proyectos y su costo
    unidades_estado = (cartera_estado.groupby("unidad")
                       .agg(n=("id", "size"), atrasados=("estado", lambda s: int((s == "Atrasado").sum())), costo=("costo", "sum"))
                       .sort_values("n", ascending=False))
    nodos = [f'raiz [label="{etiqueta(nombre_sector, 34)}\\n{plural(len(cartera_estado), "proyecto")} · {millones(cartera_estado["costo"].sum())}", '
             f'shape=box, style="rounded,filled", fillcolor="#e9eef8", color="#103f91", fontname="Helvetica"];']
    # itertuples() conserva los números enteros; iterrows() los convertía en decimales (715 -> "715.0")
    for i, u in enumerate(unidades_estado.head(8).itertuples()):
        borde = "#d03b3b" if u.atrasados else "#9aa0a6"
        nodos.append(f'u{i} [label="{etiqueta(u.Index.title())}\\n{plural(u.n, "proyecto")} · {millones(u.costo)}", '
                     f'shape=box, style="rounded", color="{borde}", fontname="Helvetica", fontsize=11];')
        nodos.append(f"raiz -> u{i};")
    if len(unidades_estado) > 8:
        nodos.append(f'otras [label="Otras {len(unidades_estado) - 8} unidades", shape=box, style="rounded,dashed", '
                     f'color="#9aa0a6", fontname="Helvetica", fontsize=11];')
        nodos.append("raiz -> otras;")
    st.graphviz_chart("digraph { rankdir=TB; node [margin=\"0.15,0.08\"]; edge [color=\"#9aa0a6\", arrowhead=none]; "
                      + " ".join(nodos) + " }", width="stretch")
    st.caption("En rojo, las unidades con al menos un proyecto atrasado.")

with st.expander("Mapa: ¿dónde están los proyectos?", expanded=True):
    # Mapa (versión rápida, con pydeck, que viene con Streamlit): un punto por proyecto con coordenadas, del color de su estado.
    #   Antes: lat y lon de cada proyecto | Después: puntos en el mapa del Perú; al pasar el cursor, nombre, estado, costo y avance
    puntos = cartera_estado.dropna(subset=["lat", "lon"])
    if len(puntos):
        datos_mapa = pd.DataFrame({
            "lat": puntos["lat"], "lon": puntos["lon"], "color": puntos["estado"].map(lambda e: rgb(ESTADOS[e][0])),
            "titulo": puntos["que_es"].str.slice(0, 90), "estado": puntos["estado"],
            "costo": puntos["costo"].map(millones), "avance": puntos["avance"].map(lambda a: f"{a:.0f} % de avance")})
        capa = pdk.Layer("ScatterplotLayer", data=datos_mapa, get_position=["lon", "lat"], get_fill_color="color",
                         get_radius=3000, radius_min_pixels=4, radius_max_pixels=12, pickable=True,
                         stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1)
        st.pydeck_chart(pdk.Deck(layers=[capa], map_provider="carto", map_style="light",
                                 initial_view_state=pdk.ViewState(latitude=-9.6, longitude=-75.0, zoom=4.2),
                                 tooltip={"html": "<b>{titulo}</b><br/>{estado} · {costo} · {avance}"}), height=480)
        # Leyenda: el color siempre va con el nombre del estado y su símbolo
        st.markdown("".join(chip(e, int((puntos["estado"] == e).sum())) for e in ORDEN_ESTADOS if (puntos["estado"] == e).any()),
                    unsafe_allow_html=True)
    st.caption(f"{len(puntos):,} de {len(cartera_estado):,} proyectos tienen coordenadas. La ubicación la registra la entidad; "
               "a veces es la de su oficina y no la de la obra.")

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
           "Avance: de menor a mayor": (["avance"], [True]), "Avance: de mayor a menor": (["avance"], [False]),
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
    # "¿Cuánto avanzó y cuánto gastó?": dos avances que declara la entidad y dos medidas de gasto, en barras de 0 a 100
    def barra(etiqueta, valor, unidad):
        if pd.isna(valor):
            return f"<span>{etiqueta}</span><span></span><span>sin dato</span>"
        cifra = f"{valor:.1f}".replace(".", ",") if abs(valor) < 10 else f"{valor:.0f}"   # 3,5 % y 2,5 % no se confunden
        return (f'<span>{etiqueta}</span><span class="pista" title="{etiqueta}: {cifra} {unidad}">'
                f'<i style="width:{min(max(valor, 0), 100):.0f}%"></i></span><span>{cifra} {unidad}</span>')
    partes = []
    if pd.notna(fila.get("avance_ejecucion")) and pd.notna(fila.get("fecha_declaracion")):
        partes.append(f'<span class="grupo">Avance que declara la entidad ({fila["fecha_declaracion"]:%d/%m/%Y})</span>')
        partes.append(barra("Toda la inversión", fila["avance_ejecucion"], "%"))
        if pd.notna(fila.get("avance_fisico")):
            partes.append(barra("Solo obra y equipos", fila["avance_fisico"], "%"))
    else:
        partes.append('<span class="grupo">La entidad no ha declarado su avance.</span>')
    partes.append('<span class="grupo">Dinero gastado</span>')
    gastado_vida, gastado_anio = fila.get("pct_gastado_vida"), fila.get("pct_gastado_2026")
    partes.append(barra("En toda su vida", 100 * gastado_vida if pd.notna(gastado_vida) else float("nan"), "% de su costo"))
    partes.append(barra("Este año", 100 * gastado_anio, "% de su presupuesto 2026") if pd.notna(gastado_anio)
                  else "<span>Este año</span><span></span><span>no tiene presupuesto 2026</span>")
    detalle_avance = f'<div class="avance">{"".join(partes)}</div>'
    if texto("frase_indice"):
        detalle_avance += f'<p class="nota">{html.escape(texto("frase_indice"))}</p>'
    if texto("frase_alerta"):   # la señal lleva su símbolo; el texto va en el color normal
        detalle_avance += f'<p class="nota"><b style="color:#c98a00">!</b> {html.escape(texto("frase_alerta"))}</p>'
    fuente_avance = ("Para su estado se usa el avance que declaró la entidad." if fila.get("avance_fuente") == "declarado por la entidad"
                     else "Para su estado se usa lo gastado, porque la entidad no declaró su avance en el último año.")

    preguntas = [("¿Qué es?", f'{fila["que_es"]}. {fila["tipo_simple"]} en {fila["lugar"]}.', ""),
                 ("¿Qué problema resuelve?", fila["problema"], detalle_brecha),
                 ("¿Cuánto cuesta y cuánto se ha gastado?", f'{fila["cuanto"]} {texto("frase_costo")}'.strip(), ""),
                 ("¿Cuánto avanzó y cuánto gastó?", "", detalle_avance + f'<p class="nota">{fuente_avance}</p>'),
                 ("¿Tiene financiamiento?", texto("frase_dinero"), ""),
                 ("¿Cuándo termina?", fila["cuando"], ""),
                 ("¿Cómo va?", f'{fila["estado"]}. {fila["estado_motivo"]} {texto("frase_programacion")}'.strip(), ""),
                 ("¿Qué problemas reporta?", texto("frase_problemas"), detalle_problema)]
    if fila["lo_que_frena"]:
        preguntas.append(("¿Qué lo frena?", fila["lo_que_frena"], ""))
    for pregunta, respuesta, detalle in preguntas:
        cuerpo = f'<p class="respuesta">{html.escape(respuesta)}</p>' if respuesta else ""
        st.markdown(f'<p class="pregunta">{pregunta}</p>{cuerpo}{detalle}', unsafe_allow_html=True)
    st.caption("Resumen redactado con inteligencia artificial a partir de los datos del MEF; confírmalo en el detalle técnico antes de citarlo."
               if fila["redactado_por_ia"] else "Resumen elaborado automáticamente a partir de los datos del MEF.")
    if fila["cui"]:
        st.link_button("Ver el detalle técnico en el MEF ↗", f'https://ofi5.mef.gob.pe/ssi/Ssi/Index?codigo={fila["cui"]}&tipo=2')
    with st.expander("Para especialistas (términos de Invierte.pe)"):
        st.markdown(
            f"- **CUI:** {fila['id']} · **Unidad ejecutora:** {fila['unidad']}\n"
            f"- **UEI:** {fila['uei'] or 'sin dato'} · **OPMI:** {fila['opmi'] or 'sin dato'}\n"
            f"- **PIM 2026:** {millones(fila['pim_2026'])} · **Devengado 2026:** {millones(fila['dev_2026'])}\n"
            f"- **Modalidad:** {fila['modalidad'] or 'sin dato'} · **Registrada en el PMI:** {fila['en_pmi']}\n"
            f"- **Brecha (texto del MEF):** {fila['brecha'] or 'sin dato'}")
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
    "Avance": vista["avance"].clip(0, 100).round(0),
    "Atraso (meses)": vista["meses_atraso"].fillna(0).astype(int),   # 0 si no está atrasado (la tabla mostraría "None")
    "Lugar": vista["lugar"],
})
if unidad == "Todas las unidades":
    tabla["Unidad ejecutora"] = vista["unidad"].str.title()
# Primera columna: una casilla "Ver ficha" en cada fila; al marcarla se abre la ficha de ese proyecto
tabla.insert(0, "Ficha", False)
# La clave cambia con los filtros y después de abrir cada ficha: así la lista vuelve a mostrarse sin casillas marcadas
version = st.session_state.get("version_lista", 0)
clave_lista = f"lista_{version}_" + str(abs(hash((sector, unidad, len(vista), orden, busqueda, solo_alerta, tuple(vista["id"].head(3))))))
editada = st.data_editor(
    tabla, hide_index=True, width="stretch", height=min(38 + 35 * len(tabla), 460), key=clave_lista,
    disabled=[c for c in tabla.columns if c != "Ficha"],          # solo se puede marcar "Ver ficha"; los datos no se editan
    column_config={
        "Ficha": st.column_config.CheckboxColumn("Ver ficha", help="Marca la casilla para abrir la ficha del proyecto", width=90),
        "Proyecto": st.column_config.TextColumn("Proyecto", width="large"),
        "Costo (S/)": st.column_config.NumberColumn("Costo (S/)", format="localized"),
        "Avance": st.column_config.ProgressColumn("Avance", min_value=0, max_value=100, format="%.0f%%"),
        "Atraso (meses)": st.column_config.NumberColumn("Atraso (meses)", format="%d"),
    })
st.caption(plural(len(vista), "proyecto") + ("" if unidad == "Todas las unidades" else f" de {unidad.title()}")
           + ". Marca «Ver ficha» en una fila para abrir la ficha del proyecto.")

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
# PASO 5.6: Cómo se calcula (transparencia) y fuente — definido arriba en pie_de_pagina()
# ============================================================
pie_de_pagina()
