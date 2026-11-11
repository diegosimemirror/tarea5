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
preguntas = [p for p in ["¿Tiene financiamiento?", "¿Qué problemas reporta?"] if any(p in m.value for m in app.markdown)]
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
    if app.exception or cifras() != 6:
        fallas.append(s)
print("6. Los 33 ministerios o entidades — con error o sin sus 6 indicadores:", fallas or "ninguno")
for e in app.exception:
    print("ERROR:", e.value)
