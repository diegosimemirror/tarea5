# ============================================================
# MÓDULO: piezas visuales de la app (las usa app/app.py)
#   1) PALETA: un color fijo por tipo de objeto, inspirado en la lógica de MIT Technology Review (texto casi negro,
#      fondos claros y un color de resalte distinto para cada clase de objeto). El color nunca va solo: siempre lo
#      acompaña una palabra o un símbolo.
#   2) esquema(): la cartera como un esquema con sangrías que se abre y se cierra (reemplaza al árbol de cajas)
#   3) flujo(): las fases de la inversión como un flujo vertical con un desvío por tipo (proyecto o IOARR), con cuántas
#      inversiones hay en cada fase y su lugar en el orden de prioridad del MEF
#   4) marcas_componentes(): los componentes de una inversión con un check de color
# Insumo:    tablas de proyectos (pandas) con las columnas que preparan los Procesos 4 y 10
# Resultado: texto HTML para st.markdown(..., unsafe_allow_html=True)
# ============================================================

# html: proteger los textos al ponerlos en HTML (viene con Python)
import html

# --- 1) Paleta: un color por clase de objeto ---
TINTA = "#08090c"                      # texto principal (casi negro)
NIVELES_COLOR = {0: "#08090c", 1: "#a2cafa", 2: "#89f0e1", 3: "#c8a0f5", 4: "#f2dc6f"}   # total, nivel, sector, pliego, unidad
COMPONENTES = {   # clave interna: (nombre para mostrar, color de resalte, color oscuro para el texto o el borde)
    "infra": ("Infraestructura", "#f5ad6e", "#7a3d06"),
    "equipo": ("Equipamiento", "#a2cafa", "#14263e"),
    "gestion": ("Gestión e intangibles", "#c8a0f5", "#29143e"),
}
# Fases: de la idea al cierre, en una escala de un solo color (de claro a oscuro = de menos a más avanzado)
FASES = [   # (clave, nombre para proyectos, nombre para IOARR, color de fondo, color del texto)
    ("idea", "Idea o en estudio", "Idea o en estudio", "#eefcf9", TINTA),
    ("aprobada", "Viable, sin expediente técnico", "Aprobada, sin documento técnico", "#cdf7f0", TINTA),
    ("expediente", "Expediente técnico en elaboración", "Documento técnico en elaboración", "#a9f2e6", TINTA),
    ("contratar", "Lista para contratar", "Lista para comprar o contratar", "#7fe3d4", TINTA),
    ("ejecucion", "En ejecución (obra o compra)", "En ejecución (compra u obra)", "#2fb5a2", TINTA),
    ("terminada", "Terminada: recepción o liquidación", "Terminada: recepción o conformidad", "#0f7466", "#ffffff"),
    ("ejecutada", "Ya ejecutada: falta el cierre", "Ya ejecutada: falta el cierre", "#004142", "#ffffff"),
]
FASE_CLAVES = [f[0] for f in FASES]
DETENIDA = ("detenida", "Detenida o por desactivar", "#5b6068", "#ffffff")

CSS = f"""
<style>
/* Esquema con sangrías: cada nivel se abre o se cierra con su flecha; la línea vertical marca qué está dentro de qué */
.esquema {{font-size:0.95rem; line-height:1.35;}}
.esquema details > summary {{list-style:none; cursor:pointer; display:flex; flex-wrap:wrap; align-items:baseline; gap:0 .5rem;
                            padding:3px 4px; border-radius:6px;}}
.esquema details > summary::-webkit-details-marker {{display:none;}}
.esquema details > summary:hover {{background:rgba(128,128,128,.10);}}
.esquema summary::before {{content:"›"; display:inline-block; width:.8em; font-weight:700; transition:transform .15s;
                          transform:rotate(0deg); color:rgba(128,128,128,.9);}}
.esquema details[open] > summary::before {{transform:rotate(90deg);}}
.esquema .hijos {{margin-left:.45rem; padding-left:1.05rem; border-left:1.5px solid rgba(128,128,128,.35);}}
.esquema .hoja {{display:flex; flex-wrap:wrap; align-items:baseline; gap:0 .5rem; padding:3px 4px 3px 1.3em;}}
.esquema .punto {{display:inline-block; width:.62em; height:.62em; border-radius:50%; border:1px solid rgba(8,9,12,.55);
                  transform:translateY(-.05em);}}
.esquema .dato {{opacity:.72; font-size:.9rem;}}
.esquema .alerta {{color:#d03b3b; font-size:.85rem; white-space:nowrap;}}
.esquema .mas {{opacity:.6; font-size:.88rem; padding:2px 4px 2px 1.3em;}}
/* Flujo de fases: tarjetas apiladas con flechas, un desvío por tipo y la prioridad del MEF en un círculo */
.flujo {{font-size:.9rem;}}
.flujo .inicio, .flujo .desvio {{margin:0 auto; text-align:center; max-width:360px; padding:7px 12px; border-radius:10px;
                                border:1.5px solid {TINTA}; background:#ffffff; color:{TINTA};}}
.flujo .desvio {{transform:none; border-style:dashed; font-weight:700;}}
.flujo .flecha {{text-align:center; opacity:.55; line-height:1.1; margin:2px 0;}}
.flujo .carriles {{display:grid; grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); gap:10px;}}
.flujo .carril-titulo {{font-size:.78rem; letter-spacing:.06em; text-transform:uppercase; font-weight:700; margin:0 0 4px 2px;}}
.flujo .nodo {{display:grid; grid-template-columns:auto 1fr; gap:0 .5rem; align-items:start; padding:6px 9px; border-radius:10px;
              border:1px solid rgba(8,9,12,.25);}}
.flujo .nodo b {{display:block; font-weight:650;}}
.flujo .nodo span.cifras {{display:block; font-size:.84rem; opacity:.9;}}
.flujo .prio {{display:inline-flex; align-items:center; justify-content:center; min-width:1.45em; height:1.45em; padding:0 .3em;
              box-sizing:border-box; border-radius:999px; background:{TINTA}; color:#ffffff; font-size:.75rem; font-weight:700;
              margin-top:.1em; white-space:nowrap;}}
.flujo .prio.sin {{background:transparent; color:inherit; border:1px dashed currentColor;}}
.flujo .vacio {{opacity:.45;}}
.flujo .aparte {{margin-top:8px;}}
/* Componentes: un check de color con su nombre */
.comp {{display:inline-flex; align-items:center; gap:5px; padding:1px 9px 1px 4px; border-radius:999px; margin:0 6px 4px 0;
        font-size:.9rem; color:{TINTA};}}
.comp i {{font-style:normal; display:inline-grid; place-items:center; width:1.15em; height:1.15em; border-radius:50%;
          color:#ffffff; font-size:.75rem; font-weight:700;}}
.comp.no {{background:transparent !important; opacity:.55; border:1px dashed rgba(128,128,128,.7); color:inherit;}}
.comp.no i {{background:transparent !important; color:inherit; border:1px solid rgba(128,128,128,.7);}}
/* Etiqueta de sección al estilo de una revista: mayúsculas pequeñas con una raya de color */
.seccion {{font-size:.78rem; letter-spacing:.08em; text-transform:uppercase; font-weight:700; margin:.4rem 0 .2rem 0;
           padding-left:.5rem; border-left:4px solid #89f0e1;}}
</style>"""


def _e(texto):
    return html.escape(str(texto))


# --- 2) Esquema de la cartera ---
def esquema(tabla, niveles, nombres, millones, plural, raiz, max_hijos=40, abiertos=1):
    """Esquema con sangrías de una tabla de proyectos.
    niveles: lista de (columna, color) de lo general a lo particular, p. ej. [("nivel", ..), ("cartera", ..), ("entidad", ..)]
    nombres: función (columna, valor) -> nombre para mostrar
    raiz: nombre del primer renglón (lo elegido), que aparece abierto
    Antes: filas de proyectos | Después: HTML con un renglón por grupo (proyectos, costo y atrasados), que se abre y se cierra.
    En cada nivel se muestran hasta max_hijos grupos (de mayor a menor costo); el resto se resume en un renglón «y N más».
    abiertos: cuántos niveles, debajo de la raíz, aparecen abiertos al cargar."""
    def renglon(nombre, g, color):
        atrasados = int((g["estado"] == "Atrasado").sum())
        alerta = (f'<span class="alerta">! {atrasados:,} {"atrasado" if atrasados == 1 else "atrasados"}</span>'
                  if atrasados else "")
        return (f'<span class="punto" style="background:{color}"></span><b>{_e(nombre)}</b>'
                f'<span class="dato">{plural(len(g), "proyecto")} · {millones(g["costo"].sum())}</span>{alerta}')

    def rama(g, profundidad):
        if profundidad >= len(niveles):
            return ""
        columna, color = niveles[profundidad]
        grupos = g.groupby(columna, sort=False)["costo"].sum().sort_values(ascending=False)
        partes = []
        for valor in grupos.index[:max_hijos]:
            sub = g[g[columna] == valor]
            hijos = rama(sub, profundidad + 1)
            texto = renglon(nombres(columna, valor), sub, color)
            if hijos:
                abierto = " open" if profundidad < abiertos else ""
                partes.append(f'<details{abierto}><summary>{texto}</summary><div class="hijos">{hijos}</div></details>')
            else:
                partes.append(f'<div class="hoja">{texto}</div>')
        if len(grupos) > max_hijos:
            resto = g[g[columna].isin(grupos.index[max_hijos:])]
            partes.append(f'<div class="mas">y {len(grupos) - max_hijos:,} más · {plural(len(resto), "proyecto")} · '
                          f'{millones(resto["costo"].sum())}</div>')
        return "".join(partes)

    hijos = rama(tabla, 0)
    cabeza = renglon(raiz, tabla, NIVELES_COLOR[0])
    cuerpo = (f'<details open><summary>{cabeza}</summary><div class="hijos">{hijos}</div></details>' if hijos
              else f'<div class="hoja">{cabeza}</div>')
    return f'<div class="esquema">{cuerpo}</div>'


# --- 3) Flujo de fases ---
def inversiones_txt(n):
    """1 -> '1 inversión'; 715 -> '715 inversiones'."""
    return f"{int(n):,} inversión" if int(n) == 1 else f"{int(n):,} inversiones"


def _nodo(nombre, g, fondo, letra, prioridad, millones):
    vacio = " vacio" if g.empty else ""
    circulo = (f'<span class="prio" title="Lugar en el orden de prioridad del MEF">{prioridad}</span>' if prioridad
               else '<span class="prio sin" title="Fuera del orden de prioridad">–</span>')
    return (f'<div class="nodo{vacio}" style="background:{fondo}; color:{letra}">{circulo}<span><b>{_e(nombre)}</b>'
            f'<span class="cifras">{inversiones_txt(len(g))} · {millones(g["costo"].sum())}</span></span></div>')


def flujo(tabla, prioridad_por_fase, millones, mostrar_ejecutadas=True):
    """Flujo vertical de fases con un desvío por tipo de inversión.
    tabla: proyectos con las columnas 'fase' (clave de FASES o 'detenida') y 'tipo_grupo'
    prioridad_por_fase: {clave de fase: número en el orden de prioridad del MEF o None}
    Antes: proyectos | Después: HTML con dos carriles (proyectos e IOARR), una tarjeta por fase con cuántas hay y su costo."""
    carriles = [("Proyectos de inversión, IRI y programas", tabla[tabla["tipo_grupo"] != "IOARR"], 1),
                ("IOARR (inversiones menores)", tabla[tabla["tipo_grupo"] == "IOARR"], 2)]
    columnas = []
    for titulo, g, indice in carriles:
        tarjetas = []
        for clave, nombre_pi, nombre_ioarr, fondo, letra in FASES:
            if clave == "ejecutada" and not mostrar_ejecutadas:
                continue
            nombre = nombre_pi if indice == 1 else nombre_ioarr
            tarjetas.append(_nodo(nombre, g[g["fase"] == clave], fondo, letra, prioridad_por_fase.get(clave), millones))
        cuerpo = '<div class="flecha">↓</div>'.join(tarjetas)
        det = g[g["fase"] == DETENIDA[0]]
        aparte = (f'<div class="aparte">{_nodo(DETENIDA[1], det, DETENIDA[2], DETENIDA[3], None, millones)}</div>'
                  if len(det) else "")
        columnas.append(f'<div><div class="carril-titulo">{_e(titulo)} · {len(g):,}</div>{cuerpo}{aparte}</div>')
    return (f'<div class="flujo"><div class="inicio"><b>{inversiones_txt(len(tabla))}</b> '
            f'· {millones(tabla["costo"].sum())}</div><div class="flecha">↓</div>'
            f'<div class="desvio">◆ ¿Es un proyecto de inversión o una IOARR?</div><div class="flecha">↙ ↘</div>'
            f'<div class="carriles">{"".join(columnas)}</div></div>')


# --- 4) Componentes ---
def marcas_componentes(fila, solo_presentes=False):
    """Antes: comp_infra=True, comp_equipo=False, comp_gestion=True | Después: tres píldoras; las que tiene llevan ✓ de color."""
    partes = []
    for clave, (nombre, claro, oscuro) in COMPONENTES.items():
        tiene = bool(fila.get(f"comp_{clave}"))
        if tiene:
            partes.append(f'<span class="comp" style="background:{claro}"><i style="background:{oscuro}">✓</i>{_e(nombre)}</span>')
        elif not solo_presentes:
            partes.append(f'<span class="comp no"><i>·</i>{_e(nombre)}</span>')
    return "".join(partes)
