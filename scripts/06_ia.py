# ============================================================
# PROCESO 6: Redactar con IA "¿Qué es?", "¿Qué problema resuelve?" y "¿Qué lo frena?" en lenguaje simple
# Insumo:    data/procesado/cinco_preguntas.parquet (nombre, descripción técnica, brecha y textos del 12-B)
# Resultado: data/procesado/ia_respuestas.parquet (una fila por inversión procesada), que la app usa si existe
# Uso:       1) copiar .env.example como .env y poner la clave
#            2) ensayo sin gastar:  python scripts/06_ia.py --sector "DESARROLLO E INCLUSION SOCIAL" --ensayo
#            3) en serio:           python scripts/06_ia.py --sector "DESARROLLO E INCLUSION SOCIAL"
# ============================================================

# --- Paquetes (todos vienen con Python, salvo pandas y pyarrow) ---
# argparse: leer opciones como --sector · json: armar y leer el formato JSON · os: leer la clave del archivo .env
# urllib: llamar a la API por internet · time: pausas entre llamadas · pathlib: rutas
import argparse, json, os, time, urllib.request
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "procesado"

# Tres proveedores con la misma forma de llamada (formato compatible con OpenAI).
# Verifica en la página del proveedor el nombre del modelo vigente y pon el tuyo en MODELO dentro de .env.
PROVEEDORES = {
    "OPENAI_API_KEY": "https://api.openai.com/v1/chat/completions",
    "DEEPSEEK_API_KEY": "https://api.deepseek.com/chat/completions",
    "GEMINI_API_KEY": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
}

INSTRUCCIONES = (
    "Eres un traductor de información pública para personas que no trabajan en inversión pública. "
    "Escribe en español del Perú, frases cortas, sin siglas ni términos técnicos (no uses PIM, devengado, UEI, OPMI, IOARR, 12-B). "
    "Usa SOLO los datos que te doy; si un dato no está, dilo en vez de inventarlo. "
    'Responde solo con un JSON con tres claves: "que_es" (máximo 20 palabras: qué se construye o mejora y para quién), '
    '"problema" (máximo 25 palabras: qué problema de la gente resuelve), '
    '"lo_que_frena" (máximo 25 palabras: qué dice el último reporte que lo retrasa, o "No reporta problemas").'
)

def leer_env():
    """Lee el archivo .env (líneas CLAVE=valor) sin mostrar su contenido."""
    env = RAIZ / ".env"
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            if "=" in linea and not linea.strip().startswith("#"):
                clave, valor = linea.split("=", 1)
                if valor.strip():
                    os.environ.setdefault(clave.strip(), valor.strip())

def mensaje(f):
    """Arma los datos de una inversión para la IA. Antes: una fila de la tabla | Después: un texto ordenado."""
    return json.dumps({
        "nombre_oficial": f["nombre"], "lugar": f["lugar"], "descripcion_tecnica": (f["alternativa"] or "")[:1200],
        "brecha_oficial": f["brecha"] or "", "aporte": f"{f['brecha_aporte']} {f['brecha_unidad']}" if pd.notna(f["brecha_aporte"]) else "",
        "ultimo_reporte_situacion": (f["situacion_12b"] or "")[:800], "ultimo_reporte_problemas": (f["problema_12b"] or "")[:600],
    }, ensure_ascii=False)

def llamar(url, clave, modelo, contenido):
    cuerpo = json.dumps({"model": modelo, "temperature": 0.2, "response_format": {"type": "json_object"},
                         "messages": [{"role": "system", "content": INSTRUCCIONES}, {"role": "user", "content": contenido}]}).encode()
    pedido = urllib.request.Request(url, data=cuerpo, headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=90) as r:
        respuesta = json.loads(r.read().decode())
    texto = respuesta["choices"][0]["message"]["content"]
    datos = json.loads(texto)                                   # salida estructurada: si no es JSON válido, falla aquí
    uso = respuesta.get("usage", {})
    return {k: str(datos.get(k, "")).strip() for k in ["que_es", "problema", "lo_que_frena"]}, uso

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sector", required=True, help='Sector tal como lo escribe el MEF, p. ej. "DESARROLLO E INCLUSION SOCIAL"')
    p.add_argument("--limite", type=int, default=100, help="Máximo de inversiones a procesar (tope de gasto)")
    p.add_argument("--ensayo", action="store_true", help="Muestra lo que se enviaría, sin llamar a la API")
    a = p.parse_args()

    base = pd.read_parquet(PROCESADO / "cinco_preguntas.parquet")
    cartera = base[base["sector"] == a.sector].sort_values("costo", ascending=False).head(a.limite)
    salida_archivo = PROCESADO / "ia_respuestas.parquet"
    previas = pd.read_parquet(salida_archivo) if salida_archivo.exists() else pd.DataFrame(columns=["id"])
    pendientes = cartera[~cartera["id"].isin(previas["id"])]
    print(f"{a.sector}: {len(cartera)} inversiones, {len(pendientes)} pendientes")

    if a.ensayo:
        print("--- Ejemplo de lo que se enviaría ---\n", INSTRUCCIONES, "\n", mensaje(pendientes.iloc[0]) if len(pendientes) else "(nada pendiente)")
        return

    leer_env()
    clave_env = next((k for k in PROVEEDORES if os.environ.get(k)), None)
    modelo = os.environ.get("MODELO")
    if not clave_env or not modelo:
        raise SystemExit("Falta la clave o el modelo en .env (ver .env.example).")
    nuevas, tokens = [], 0
    for _, f in pendientes.iterrows():
        try:
            r, uso = llamar(PROVEEDORES[clave_env], os.environ[clave_env], modelo, mensaje(f))
            nuevas.append({"id": f["id"], **r, "modelo": modelo})
            tokens += uso.get("total_tokens", 0)
        except Exception as e:                                  # una falla no detiene el resto
            print("  error en", f["id"], ":", type(e).__name__)
        time.sleep(0.5)
    todas = pd.concat([previas, pd.DataFrame(nuevas)], ignore_index=True)
    todas.to_parquet(salida_archivo, index=False)
    print(f"Listo: {len(nuevas)} nuevas · tokens usados: {tokens:,} · total guardado: {len(todas)}")

if __name__ == "__main__":
    main()
