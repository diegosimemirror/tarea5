# ============================================================
# PROCESO 5: Mostrar la cartera de inversiones en lenguaje simple (aplicación web)
# Insumo:    data/procesado/cinco_preguntas.parquet (resultado del Proceso 4)
# Resultado: una página web con tres pasos:
#              1) elegir un ministerio, 2) ver su árbol y sus proyectos, 3) abrir la ficha de cinco preguntas
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
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "procesado" / "cinco_preguntas.parquet"
FECHA_DATOS = "08/11/2026"

st.set_page_config(page_title="Inversiones en simple", page_icon="🏛️", layout="wide")

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
    return tabla

inversiones = cargar()

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
</style>""", unsafe_allow_html=True)

def chip(estado, n=None):
    color, simbolo, _ = ESTADOS[estado]
    cuenta = f" · {n:,}" if n is not None else ""
    return f'<span class="chip" style="color:{color}"><b>{simbolo}</b>{html.escape(estado)}{cuenta}</span>'

def millones(x):
    if pd.isna(x):
        return "sin dato"
    return f"S/ {x / 1e9:,.1f} mil millones" if x >= 1e9 else (f"S/ {x / 1e6:,.1f} millones" if x >= 1e6 else f"S/ {x / 1e3:,.0f} mil")

# ============================================================
# PASO 5.2: Paso 1 de la página — elegir un ministerio
# ============================================================
st.title("Cartera de inversiones del Estado, en simple")
st.caption(f"Ministerios y entidades del gobierno nacional · datos del MEF al {FECHA_DATOS} · versión sin IA (las respuestas salen de reglas)")

conteo = inversiones.groupby("sector").size().sort_values(ascending=False)
opciones = list(conteo.index)
por_defecto = opciones.index("DESARROLLO E INCLUSION SOCIAL") if "DESARROLLO E INCLUSION SOCIAL" in opciones else 0
sector = st.selectbox("Elige un ministerio o entidad", opciones, index=por_defecto,
                      format_func=lambda s: f"{NOMBRES.get(s, s.title())} — {conteo[s]:,} proyectos")
cartera = inversiones[inversiones["sector"] == sector]
nombre_sector = NOMBRES.get(sector, sector.title())

c1, c2, c3 = st.columns(3)
c1.metric("Proyectos", f"{len(cartera):,}")
c2.metric("Cuestan en total", millones(cartera["costo"].sum()))
c3.metric("Atrasados", f"{(cartera['estado'] == 'Atrasado').sum():,}")
st.markdown("".join(chip(e, int((cartera["estado"] == e).sum())) for e in sorted(ESTADOS, key=lambda e: ESTADOS[e][2])),
            unsafe_allow_html=True)

# ============================================================
# PASO 5.3: Paso 2 — el árbol: ministerio → unidades ejecutoras (se muestran las 8 con más proyectos)
# ============================================================
unidades = (cartera.groupby("unidad")
            .agg(n=("id", "size"), atrasados=("estado", lambda s: int((s == "Atrasado").sum())), costo=("costo", "sum"))
            .sort_values("n", ascending=False))

def etiqueta(texto, ancho=26):
    return "\\n".join(textwrap.wrap(texto.replace('"', "'"), ancho))

nodos = [f'raiz [label="{etiqueta(nombre_sector, 34)}\\n{len(cartera):,} proyectos", shape=box, style="rounded,filled", fillcolor="#e9eef8", color="#103f91", fontname="Helvetica"];']
for i, (unidad, fila) in enumerate(unidades.head(8).iterrows()):
    borde = "#d03b3b" if fila["atrasados"] else "#9aa0a6"
    nodos.append(f'u{i} [label="{etiqueta(unidad.title())}\\n{fila["n"]:,} proyectos · {fila["atrasados"]:,} atrasados", '
                 f'shape=box, style="rounded", color="{borde}", fontname="Helvetica", fontsize=11];')
    nodos.append(f"raiz -> u{i};")
if len(unidades) > 8:
    nodos.append(f'otras [label="Otras {len(unidades) - 8} unidades", shape=box, style="rounded,dashed", color="#9aa0a6", fontname="Helvetica", fontsize=11];')
    nodos.append("raiz -> otras;")
with st.expander("Árbol de la cartera", expanded=True):
    st.graphviz_chart("digraph { rankdir=TB; node [margin=\"0.15,0.08\"]; edge [color=\"#9aa0a6\", arrowhead=none]; " + " ".join(nodos) + " }",
                      width="stretch")
    st.caption("En rojo, las unidades con al menos un proyecto atrasado.")

# ============================================================
# PASO 5.4: Elegir unidad, estado y búsqueda; mostrar los proyectos como tarjetas
# ============================================================
f1, f2, f3 = st.columns([2, 2, 1.4])
lista_unidades = ["Todas las unidades"] + list(unidades.index)
unidad = f1.selectbox("Unidad ejecutora", lista_unidades,
                      format_func=lambda u: u if u == "Todas las unidades" else f"{u.title()} — {unidades.loc[u, 'n']:,}")
estados_elegidos = f2.multiselect("Estado", sorted(ESTADOS, key=lambda e: ESTADOS[e][2]), placeholder="Todos los estados")
busqueda = f3.text_input("Buscar", placeholder="Nombre, lugar o CUI")

vista = cartera if unidad == "Todas las unidades" else cartera[cartera["unidad"] == unidad]
if estados_elegidos:
    vista = vista[vista["estado"].isin(estados_elegidos)]
if busqueda:
    q = busqueda.strip().lower()
    vista = vista[vista["que_es"].str.lower().str.contains(q, regex=False) | vista["lugar"].str.lower().str.contains(q, regex=False)
                  | vista["id"].str.contains(q, regex=False)]
vista = vista.assign(_orden=vista["estado"].map(lambda e: ESTADOS[e][2])).sort_values(["_orden", "costo"], ascending=[True, False])

# ============================================================
# PASO 5.5: Paso 3 — la ficha de cinco preguntas (ventana emergente)
# ============================================================
@st.dialog("Ficha del proyecto", width="large")
def ficha(fila):
    st.markdown(chip(fila["estado"]) + f' <span style="color:#5b6068">{html.escape(fila["estado_motivo"])}</span>', unsafe_allow_html=True)
    preguntas = [("¿Qué es?", f'{fila["que_es"]}. {fila["tipo_simple"]} en {fila["lugar"]}.'),
                 ("¿Qué problema resuelve?", fila["problema"]),
                 ("¿Cuánto cuesta y cuánto se ha gastado?", fila["cuanto"]),
                 ("¿Cuándo termina?", fila["cuando"]),
                 ("¿Cómo va?", f'{fila["estado"]}. {fila["estado_motivo"]}')]
    if fila["lo_que_frena"]:
        preguntas.append(("¿Qué lo frena?", fila["lo_que_frena"]))
    for pregunta, respuesta in preguntas:
        st.markdown(f'<p class="pregunta">{pregunta}</p><p class="respuesta">{html.escape(respuesta)}</p>', unsafe_allow_html=True)
    st.caption("Textos redactados por IA a partir de los datos del MEF; revisa el detalle técnico antes de citarlos."
               if fila["redactado_por_ia"] else "Textos generados con reglas a partir de los datos del MEF (versión sin IA).")
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

st.subheader(f"{len(vista):,} proyectos" + ("" if unidad == "Todas las unidades" else f" de {unidad.title()}"))
if "mostrar" not in st.session_state:
    st.session_state.mostrar = 24
columnas = st.columns(3)
for i, (_, fila) in enumerate(vista.head(st.session_state.mostrar).iterrows()):
    with columnas[i % 3].container(border=True):
        st.markdown(chip(fila["estado"]), unsafe_allow_html=True)
        titulo = fila["que_es"] if len(fila["que_es"]) <= 110 else fila["que_es"][:107].rsplit(" ", 1)[0] + "…"
        st.markdown(f"**{titulo}**")
        st.caption(f'{fila["lugar"]} · {millones(fila["costo"])} · {fila["avance"]:.0f} % de avance')
        if st.button("Ver ficha", key=f"ver-{fila['id']}"):
            ficha(fila)
if len(vista) > st.session_state.mostrar:
    if st.button(f"Mostrar más ({len(vista) - st.session_state.mostrar:,} restantes)"):
        st.session_state.mostrar += 24
        st.rerun()

# ============================================================
# PASO 5.6: Cómo se calcula (transparencia) y fuente
# ============================================================
with st.expander("¿Cómo se calcula el estado?"):
    st.markdown(
        "- **Atrasado:** la fecha de término registrada ya pasó y el avance es menor a 95 %.\n"
        "- **En riesgo este año:** tiene presupuesto 2026 y lleva gastado menos de la mitad.\n"
        "- **Sin reportes recientes:** ya empezó, pero su último reporte de avance (formato 12-B) tiene más de 180 días.\n"
        "- **Por cerrar:** está prácticamente terminado (95 % o más) y falta el cierre formal.\n"
        "- **Sin presupuesto este año:** está aprobado, no ha empezado y no tiene presupuesto en 2026.\n"
        "- **En marcha:** ninguna de las anteriores.\n\n"
        "El avance es el mayor entre el avance físico y el porcentaje gastado del costo. Reglas de ejemplo, por validar.")
st.caption(f"Fuente: MEF, Datos Abiertos (Detalle de inversiones, Inversiones y brechas, Formato 12-B), al {FECHA_DATOS}.")
