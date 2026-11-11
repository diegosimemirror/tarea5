# ============================================================
# PRUEBA AUTOMÁTICA DE LA APP (sin abrir el navegador)
# Insumo:    app/app.py
# Resultado: en pantalla, si la página carga sin errores y si la ficha se abre al hacer clic
# Uso:       uv run --with streamlit --with pandas --with pyarrow python scripts/probar_app.py
# ============================================================

# streamlit.testing: ejecuta la app como si fuera un navegador y permite "hacer clic" desde el código
from pathlib import Path
from streamlit.testing.v1 import AppTest

app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app" / "app.py"), default_timeout=120)
app.run()
cifras = lambda: sum(m.value.count('class="cifra"') for m in app.markdown)   # tarjetas de indicadores de cartera
print("1. Carga inicial — errores:", len(app.exception), "| métricas:", [m.value for m in app.metric], "| indicadores:", cifras())

# Hacer clic en el primer botón "Ver ficha" y comprobar que no hay errores ni preguntas faltantes
botones = [b for b in app.button if b.label == "Ver ficha"]
print("2. Tarjetas con botón 'Ver ficha':", len(botones))
botones[0].click().run()
preguntas = [p for p in ["¿Tiene financiamiento?", "¿Qué problemas reporta?", "¿Cuánto avanzó y cuánto gastó?"] if any(p in m.value for m in app.markdown)]
print("3. Después de abrir la ficha — errores:", len(app.exception), "| preguntas nuevas presentes:", preguntas)

# Cambiar de ministerio (Transportes) y volver a revisar
app.selectbox[0].select("TRANSPORTES Y COMUNICACIONES").run()
print("4. Transportes — errores:", len(app.exception), "| métricas:", [m.value for m in app.metric])

# Elegir la cartera completa: debe mostrar el desglose por ministerio y ninguna tarjeta de proyecto
app.selectbox[0].select("CARTERA COMPLETA").run()
fichas = [b for b in app.button if b.label == "Ver ficha"]
print("5. Cartera completa — errores:", len(app.exception), "| métricas:", [m.value for m in app.metric],
      "| tarjetas:", len(fichas), "| cajas del desglose:", sum(m.value.count('class="edt-caja"') for m in app.markdown),
      "| indicadores:", cifras())

# Recorrer todos los ministerios: ninguno debe dar error (por ejemplo, los que no tienen presupuesto 2026)
fallas = []
for s in app.selectbox[0].options[1:]:
    app.selectbox[0].select(s).run()
    if app.exception or cifras() != 7:
        fallas.append(s)
print("6. Los 33 ministerios o entidades — con error o sin sus 7 indicadores:", fallas or "ninguno")

# Nivel 2 (ministerio): elegir el estado "Atrasado" en el MIDIS; las cifras deben ser solo las de los atrasados
#   Selectores: [0] cartera, [1] estado del ministerio, [2] unidad ejecutora, [3] estado de la unidad
app.selectbox[0].select("DESARROLLO E INCLUSION SOCIAL").run()
app.selectbox[1].select("Atrasado").run()
print("7. Nivel 2, MIDIS con estado 'Atrasado' — errores:", len(app.exception), "| métricas:", [m.value for m in app.metric])

# Nivel 3 (unidad ejecutora): elegir una unidad y un estado
app.selectbox[1].select("Todos los estados").run()
app.selectbox[2].select(app.selectbox[2].options[1]).run()
app.selectbox[3].select("Sin presupuesto este año").run()
print("8. Nivel 3, primera unidad y 'Sin presupuesto este año' — errores:", len(app.exception), "| métricas:", [m.value for m in app.metric])

# Filtro "solo los que gastaron 30 puntos o más por encima de su avance" en Educación
app.selectbox[0].select("EDUCACION").run()
app.toggle[0].set_value(True).run()
print("9. Filtro de alerta (Educación) — errores:", len(app.exception), "| proyectos del nivel 3:", [m.value for m in app.metric][2])
for e in app.exception:
    print("ERROR:", e.value)
