# ============================================================
# PRUEBA AUTOMÁTICA DE LA APP (sin abrir el navegador)
# Insumo:    app/app.py
# Resultado: en pantalla, si la página carga sin errores y si las listas, la ficha, la búsqueda y el mapa funcionan
# Uso:       uv run --with streamlit --with pandas --with pyarrow python scripts/probar_app.py
# ============================================================

# streamlit.testing: ejecuta la app como si fuera un navegador y permite "hacer clic" desde el código
from pathlib import Path
import io
import re   # re: leer las cifras de ejecución en el HTML de la ficha
import sys
import pandas as pd   # pandas: leer las obras paralizadas y los proyectos para elegir casos de prueba
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parents[1]
APP = str(RAIZ / "app" / "app.py")
TODO = "__todo__"     # la opción «Todos» o «Todas» de cada lista
# Listas desplegables, en el orden en que aparecen en la página (fila por fila, de izquierda a derecha): nivel, sector o
# gobierno regional, pliego | unidad ejecutora, tipo, estado | componentes, fase, presupuesto | orden de la lista
NIVEL, CARTERA, PLIEGO, UNIDAD, TIPO, ESTADO, COMPONENTES, FASE, PRESUPUESTO, ORDEN = range(10)

app = AppTest.from_file(APP, default_timeout=180)
app.run()
cifras = lambda: sum(m.value.count('class="cifra"') for m in app.markdown)      # tarjetas de indicadores
cajas = lambda: sum(m.value.count('class="punto"') for m in app.markdown)       # renglones del esquema de la cartera
metricas = lambda: [m.value for m in app.metric]
lista_de = lambda prueba: next(d.value for d in prueba.dataframe if "Ficha" in d.value.columns)   # la lista de proyectos
lista = lambda: lista_de(app)
print("1. Carga inicial (portafolio total) — errores:", len(app.exception), "| métricas:", metricas(),
      "| indicadores:", cifras(), "| renglones del esquema:", cajas(), "| filas de la lista:", len(lista()),
      "| flujo de fases:", any('class="flujo"' in m.value for m in app.markdown),
      "| ya ejecutadas en la lista (deben ser 0):", int(lista()["Estado"].str.contains("Ya ejecutada").sum()))

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
print("10. Buscar 'bernales' en Salud — errores:", len(busca.exception), "| filas:", len(lista_de(busca)),
      "| incluye el hospital:", lista_de(busca)["Proyecto"].str.contains("Demuele").any())
busca.text_input[0].input("hospital de Chupaca").run()
print("    Buscar 'hospital de Chupaca' en Salud — errores:", len(busca.exception), "| aviso:", [i.value[:90] for i in busca.info])
busca.selectbox[CARTERA].select(TODO).run()
busca.text_input[0].input("Antonio Lorena").run()
resultado = lista_de(busca)
print("    Buscar 'Antonio Lorena' en todo el portafolio — errores:", len(busca.exception), "| filas:", len(resultado),
      "| dónde:", resultado["Sector o gobierno regional"].unique()[:3].tolist() if "Sector o gobierno regional" in resultado else "-")

# Obras paralizadas según la Contraloría: el recuadro aparece en la ficha de un proyecto con una obra, en la de uno con
# varias, y NO aparece en un proyecto sin obras paralizadas (2613205, del MIDIS)
pruebas = [app, enlace, busca]
paralizadas = pd.read_parquet(RAIZ / "data" / "procesado" / "contraloria_paralizadas.parquet")
obras = paralizadas["id"].value_counts()
for cui in (obras[obras == 1].index[0], obras.index[0], "2613205"):
    f = AppTest.from_file(APP, default_timeout=180)
    f.query_params["ficha"] = cui
    f.run()
    print(f"11. Ficha {cui} ({int(obras.get(cui, 0))} obras paralizadas) — errores:", len(f.exception),
          "| recuadro:", any('<p class="pregunta">Obra paralizada según la Contraloría</p>' in m.value for m in f.markdown),
          "| fuente y fecha:", any("Fecha de corte: 30/06/2026" in c.value for c in f.caption))
    pruebas.append(f)

# Portafolios A y B: abrirlos desde el enlace (un código que no existe se ignora), agregar toda una lista y vaciar uno
port = AppTest.from_file(APP, default_timeout=180)
port.query_params["a"], port.query_params["na"] = "2613205,2324655,9999999", "Prioridades"
port.query_params["b"] = ",".join(paralizadas["id"].unique()[:3])
port.run()
comparacion = lambda: next(d.value for d in port.dataframe if "Indicador" in d.value.columns)
print("12. Portafolios desde el enlace — errores:", len(port.exception), "| columnas:", list(comparacion().columns)[1:],
      "| proyectos:", comparacion().iloc[0, 1:].tolist(),
      "| con obras paralizadas:", comparacion().set_index("Indicador").loc["Con obras paralizadas según la Contraloría"].tolist())
port.selectbox[NIVEL].select("Gobierno nacional").run()
port.selectbox[CARTERA].select("DESARROLLO E INCLUSION SOCIAL").run()
port.button(key="agregar_B").click().run()
port.button(key="vaciar_A").click().run()
print("    Agregar la lista del MIDIS a B y vaciar A — errores:", len(port.exception),
      "| proyectos A y B:", comparacion().iloc[0, 1:].tolist(), "| casillas B marcadas en la lista:", int(lista_de(port)["B"].sum()))
pruebas.append(port)

# Archivo CSV: lo que se descarga, al volver a subirlo, da los mismos portafolios (también si Excel lo guardó con «;»)
sys.path.insert(0, str(RAIZ / "app"))
from portafolios import a_csv, leer_csv
proyectos = pd.read_parquet(RAIZ / "data" / "procesado" / "cinco_preguntas.parquet", columns=["id", "que_es", "estado", "costo"])
ida = ({"A": ["2613205", "2324655"], "B": [obras.index[0]]}, {"A": "Prioridades, 2027", "B": "Resto"})
archivo = a_csv(*ida, proyectos)
con_punto_y_coma = pd.read_csv(io.BytesIO(archivo), dtype=str).to_csv(index=False, sep=";").encode("utf-8")
print("13. Archivo CSV — ida y vuelta igual:", leer_csv(archivo) == ida, "| con «;» (Excel):", leer_csv(con_punto_y_coma) == ida,
      "| tamaño:", len(archivo), "bytes")

# Empresas públicas (Proceso 9): el Hospital del Altiplano de EsSalud (2300016) muestra su gasto reportado a FONAFE, no 0 %;
# una inversión de EsSalud sin reporte a FONAFE (2547586) muestra "sin dato" y el estado "Sin datos de avance"
for cui, esperado in (("2300016", "reportó a FONAFE"), ("2547586", "no publica su reporte a FONAFE")):
    f = AppTest.from_file(APP, default_timeout=180)
    f.query_params["ficha"] = cui
    f.run()
    ejecucion = next((m.value for m in f.markdown if "¿Cuánto se ha ejecutado?" in m.value), "")
    cifras = re.findall(r"(\d+(?:,\d)?) % · ", ejecucion)
    print(f"14. Ficha {cui} (empresa pública) — errores:", len(f.exception), "| nota de la fuente:", esperado in ejecucion,
          "| cifras de ejecución:", cifras or "sin dato",
          "| estado:", next((m.value.split("</p>")[1][:60] for m in f.markdown if "¿Cómo va?" in m.value), "-"))
    pruebas.append(f)

# Ya ejecutadas (Proceso 10): ocultas por defecto; el interruptor las muestra
ej = AppTest.from_file(APP, default_timeout=180)
ej.run()
n_antes = ej.metric[0].value                                   # «Proyectos» de la selección
ej.toggle[0].set_value(True).run()
n_despues = ej.metric[0].value
# Con el interruptor, el estado «Ya ejecutada» aparece en la lista de estados; al elegirlo, solo quedan ya ejecutadas
ej.selectbox[ESTADO].select("Ya ejecutada").run()
estados = lista_de(ej)["Estado"]
print("15. Interruptor «Mostrar las ya ejecutadas» — errores:", len(ej.exception), "| proyectos antes:", n_antes,
      "| después:", n_despues, "| estado «Ya ejecutada»:", ej.metric[0].value, "proyectos",
      "| todas ya ejecutadas:", bool(estados.str.contains("Ya ejecutada").all()))
pruebas.append(ej)

# Componentes: «Solo equipamiento» deja solo filas con el check de equipamiento y sin los otros dos
comp = AppTest.from_file(APP, default_timeout=180)
comp.run()
comp.selectbox[COMPONENTES].select("Solo equipamiento").run()
t = lista_de(comp)
print("16. Componentes «Solo equipamiento» — errores:", len(comp.exception), "| filas:", len(t),
      "| todas con solo equipamiento:", bool(t["Equipo"].eq("🟢").all() and t["Infra"].eq("").all() and t["Gestión"].eq("").all()),
      "| opciones:", comp.selectbox[COMPONENTES].options[1:4])
# Fase y orden según la prioridad del MEF: la columna «Prioridad MEF» queda de menor a mayor
comp.selectbox[COMPONENTES].select(TODO).run()
comp.selectbox[ORDEN].select("Prioridad según el MEF: primero lo más avanzado").run()
prio = lista_de(comp)["Prioridad MEF"].dropna()
print("17. Orden por prioridad del MEF — errores:", len(comp.exception), "| de menor a mayor:", bool(prio.is_monotonic_increasing),
      "| fases:", comp.selectbox[FASE].options[1:])
comp.selectbox[FASE].select("ejecucion").run()
print("    Fase «En ejecución» — errores:", len(comp.exception), "| filas:", len(lista_de(comp)),
      "| todas en ejecución:", bool(lista_de(comp)["Fase"].str.startswith("En ejecución").all()))
pruebas.append(comp)

# Ficha de una inversión de la pandemia de EsSalud (0 % en el 12-B, pero su texto dice que se ejecutó): se abre por enlace
# aunque esté oculta, y dice «Según el texto: ya ejecutada», qué incluye y en qué fase está
f = AppTest.from_file(APP, default_timeout=180)
f.query_params["ficha"] = "2538136"
f.run()
texto_ficha = " ".join(m.value for m in f.markdown)
print("18. Ficha 2538136 (EsSalud, pandemia) — errores:", len(f.exception), "| según el texto:", "Según el texto: ya ejecutada" in texto_ficha,
      "| ¿Qué incluye?:", "¿Qué incluye?" in texto_ficha, "| ¿En qué fase está?:", "¿En qué fase está?" in texto_ficha)
pruebas.append(f)

# Marcador de departamentos: Lima y Callao dejan en la lista solo sus proyectos (sin las ya ejecutadas, ocultas por defecto);
# al cambiar una lista de arriba, lo marcado se mantiene
dep = AppTest.from_file(APP, default_timeout=180)
dep.run()
base = pd.read_parquet(RAIZ / "data" / "procesado" / "cinco_preguntas.parquet", columns=["departamento", "ya_ejecutada"])
esperado = int((base["departamento"].isin(["LIMA", "CALLAO"]) & ~base["ya_ejecutada"]).sum())
dep.multiselect[0].select("Lima").select("Callao").run()
proyectos_lista = lambda: [m.value for m in dep.metric if m.label == "Proyectos"][-1]   # la cifra junto al buscador
t = lista_de(dep)
print("19. Departamentos Lima y Callao — errores:", len(dep.exception), "| proyectos en la lista:", proyectos_lista(),
      "| esperados:", f"{esperado:,}", "| todas las filas en Lima o Callao:", bool(t["Lugar"].str.contains(r"(?:^|, )(?:Lima|Callao)$").all()),
      "| opciones:", dep.multiselect[0].options[:3])
dep.selectbox[NIVEL].select("Gobierno regional").run()
print("    Con «Gobiernos regionales» — errores:", len(dep.exception), "| marcados:", dep.multiselect[0].value,
      "| proyectos en la lista:", proyectos_lista())
pruebas.append(dep)

for prueba in pruebas:
    for e in prueba.exception:
        print("ERROR:", e.value)
