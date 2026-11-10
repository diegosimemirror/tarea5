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
print("1. Carga inicial — errores:", len(app.exception), "| métricas:", [m.value for m in app.metric])

# Hacer clic en el primer botón "Ver ficha" y comprobar que no hay errores
botones = [b for b in app.button if b.label == "Ver ficha"]
print("2. Tarjetas con botón 'Ver ficha':", len(botones))
botones[0].click().run()
print("3. Después de abrir la ficha — errores:", len(app.exception))

# Cambiar de ministerio (Transportes) y volver a revisar
app.selectbox[0].select("TRANSPORTES Y COMUNICACIONES").run()
print("4. Transportes — errores:", len(app.exception), "| métricas:", [m.value for m in app.metric])
for e in app.exception:
    print("ERROR:", e.value)
