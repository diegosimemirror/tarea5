# ============================================================
# PRUEBA AUTOMÁTICA DE LA APP (sin abrir el navegador)
# Insumo:    app/app.py
# Resultado: en pantalla, si la página carga sin errores y si las listas, la ficha, la búsqueda y el mapa funcionan
# Uso:       uv run --with streamlit --with pandas --with pyarrow python scripts/probar_app.py
# ============================================================

# streamlit.testing: ejecuta la app como si fuera un navegador y permite "hacer clic" desde el código
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "app.py")
TODO = "__todo__"     # la opción «Todos» o «Todas» de cada lista
# Listas desplegables, de arriba abajo: nivel, sector o gobierno regional, pliego, unidad ejecutora, tipo, estado y orden
NIVEL, CARTERA, PLIEGO, UNIDAD, TIPO, ESTADO, ORDEN = range(7)

app = AppTest.from_file(APP, default_timeout=180)
app.run()
cifras = lambda: sum(m.value.count('class="cifra"') for m in app.markdown)      # tarjetas de indicadores
cajas = lambda: sum(m.value.count('class="edt-caja"') for m in app.markdown)    # cajas del árbol de la cartera
metricas = lambda: [m.value for m in app.metric]
lista = lambda: app.dataframe[-1].value                                         # la lista de proyectos (la última tabla)
print("1. Carga inicial (portafolio total) — errores:", len(app.exception), "| métricas:", metricas(),
      "| indicadores:", cifras(), "| cajas del árbol:", cajas(), "| filas de la lista:", len(lista()))

app.selectbox[NIVEL].select("Gobierno nacional").run()
print("1b. Gobierno nacional — errores:", len(app.exception), "| métricas:", metricas(), "| cajas:", cajas())

# Un sector del nacional (MIDIS): la lista, ordenarla y sus columnas
app.selectbox[CARTERA].select("DESARROLLO E INCLUSION SOCIAL").run()
print("2. MIDIS — errores:", len(app.exception), "| métricas:", metricas(), "| filas:", len(lista()), "| columnas:", list(lista().columns))
app.selectbox[ORDEN].select("Costo: de mayor a menor").run()
costos = lista()["Costo (S/)"]
print("   Ordenada de mayor a menor costo:", bool(costos.is_monotonic_decreasing), "| primera fila:", lista().iloc[0]["Proyecto"][:60])

# Abrir una ficha con el enlace directo (?ficha=CUI) y comprobar que no hay errores ni preguntas faltantes
app.query_params["ficha"] = "2613205"
app.run()
preguntas = [p for p in ["¿Tiene financiamiento?", "¿Qué problemas reporta?", "¿Cuánto se ha ejecutado?"] if any(p in m.value for m in app.markdown)]
print("3. Ficha por enlace (2613205) — errores:", len(app.exception), "| preguntas presentes:", preguntas)
del app.query_params["ficha"]

# "Ubicar": un proyecto marcado debe aparecer resaltado en el mapa (se simula la marca guardada en la sesión)
app.session_state["ubicar_ids"] = ["2613205"]
app.run()
resaltado = [m.value for m in app.markdown if "Resaltado en el mapa" in m.value]
print("3b. Ubicar en el mapa (2613205) — errores:", len(app.exception), "| resaltado:", bool(resaltado),
      "| casilla marcada en la lista:", int(lista()["Mapa"].sum()))
app.session_state["ubicar_ids"] = []

# Salud tiene 3 pliegos: el árbol muestra los pliegos; al elegir el Ministerio de Salud, sus unidades ejecutoras
app.selectbox[CARTERA].select("SALUD").run()
print("4. Salud — errores:", len(app.exception), "| métricas:", metricas(), "| pliegos:", app.selectbox[PLIEGO].options[1:])
app.selectbox[PLIEGO].select("MINISTERIO DE SALUD").run()
print("4b. Pliego Ministerio de Salud — errores:", len(app.exception), "| métricas:", metricas(),
      "| unidades ejecutoras:", len(app.selectbox[UNIDAD].options) - 1)

# Todos los sectores y gobiernos regionales: ninguno debe dar error y todos deben tener sus 5 indicadores
app.selectbox[NIVEL].select(TODO).run()
carteras = app.selectbox[CARTERA].options[1:]
fallas = []
for c in carteras:
    app.selectbox[CARTERA].select(c).run()
    if app.exception or cifras() != 5:
        fallas.append(c)
print("5. Las", len(carteras), "carteras (sectores y gobiernos regionales) — con error o sin sus 5 indicadores:", fallas or "ninguna")

# Gobiernos regionales: el árbol con sus gobiernos regionales; Junín y solo sus IOARR
app.selectbox[CARTERA].select(TODO).run()
app.selectbox[NIVEL].select("Gobierno regional").run()
print("6. Gobiernos regionales — errores:", len(app.exception), "| métricas:", metricas(), "| cajas:", cajas())
app.selectbox[CARTERA].select("GOBIERNO REGIONAL JUNIN").run()
app.selectbox[TIPO].select("IOARR").run()
print("6b. Junín, solo IOARR — errores:", len(app.exception), "| métricas:", metricas(), "| filas:", len(lista()))

# Estado y unidad ejecutora en el MIDIS
app.selectbox[TIPO].select(TODO).run()
app.selectbox[NIVEL].select("Gobierno nacional").run()
app.selectbox[CARTERA].select("DESARROLLO E INCLUSION SOCIAL").run()
app.selectbox[ESTADO].select("Atrasado").run()
print("7. MIDIS con estado 'Atrasado' — errores:", len(app.exception), "| métricas:", metricas())
app.selectbox[ESTADO].select(TODO).run()
app.selectbox[UNIDAD].select(app.selectbox[UNIDAD].options[1]).run()
app.selectbox[ESTADO].select(app.selectbox[ESTADO].options[-1]).run()
print("8. Primera unidad del MIDIS y su último estado (", app.selectbox[ESTADO].value, ") — errores:", len(app.exception),
      "| métricas:", metricas())

# Abrir la app directamente desde un enlace a una ficha (RENIEC), sin elegir nada antes: debe ir a su sector y abrir la ficha
enlace = AppTest.from_file(APP, default_timeout=180)
enlace.query_params["ficha"] = "2324655"
enlace.run()
print("9. Enlace directo ?ficha=2324655 — errores:", len(enlace.exception), "| sector:", enlace.selectbox[CARTERA].value,
      "| ficha abierta:", any("¿Cuánto se ha ejecutado?" in m.value for m in enlace.markdown))

# Búsqueda: sin tildes, palabra por palabra y con aviso cuando no hay resultados
busca = AppTest.from_file(APP, default_timeout=180)
busca.run()
busca.selectbox[CARTERA].select("SALUD").run()
busca.text_input[0].input("bernales").run()
print("10. Buscar 'bernales' en Salud — errores:", len(busca.exception), "| filas:", len(busca.dataframe[-1].value),
      "| incluye el hospital:", busca.dataframe[-1].value["Proyecto"].str.contains("Demuele").any())
busca.text_input[0].input("hospital de Chupaca").run()
print("    Buscar 'hospital de Chupaca' en Salud — errores:", len(busca.exception), "| aviso:", [i.value[:90] for i in busca.info])
busca.selectbox[CARTERA].select(TODO).run()
busca.text_input[0].input("Antonio Lorena").run()
resultado = busca.dataframe[-1].value
print("    Buscar 'Antonio Lorena' en todo el portafolio — errores:", len(busca.exception), "| filas:", len(resultado),
      "| dónde:", resultado["Sector o gobierno regional"].unique()[:3].tolist() if "Sector o gobierno regional" in resultado else "-")

for prueba in (app, enlace, busca):
    for e in prueba.exception:
        print("ERROR:", e.value)
