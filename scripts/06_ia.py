# ============================================================
# PROCESO 6: Títulos de alcance con IA (LLM con salida estructurada, sesión 08)
# Insumo:    data/procesado/cinco_preguntas.parquet: nombre oficial y "alternativa" (la descripción técnica de lo que
#            hace cada proyecto, registrada en el MEF; está llena en cerca del 48 % de los proyectos)
# Resultado: data/procesado/ia_titulos.parquet: una fila por proyecto con un título de una línea que dice QUÉ hace,
#            CUÁNTO y DÓNDE. La app lo usa en lugar del nombre oficial (que sigue visible en "Para especialistas")
# Uso:       1) poner la clave en .env (GEMINI_API_KEY=… y MODELO=…); el archivo .env nunca se sube a GitHub
#            2) ensayo, sin llamar a la IA:  python scripts/06_ia.py --sector "REGISTRO NACIONAL DE IDENTIFICACION Y ESTADO CIVIL" --ensayo
#            3) prueba:                      python scripts/06_ia.py --sector "DESARROLLO E INCLUSION SOCIAL" "REGISTRO NACIONAL DE IDENTIFICACION Y ESTADO CIVIL"
#            4) todo el gobierno nacional:   python scripts/06_ia.py --limite 7000
#            Si se acaba el cupo diario del proveedor, se guarda lo avanzado: al volver a correrlo, sigue donde se quedó.
# ============================================================

# --- Paquetes (vienen con Python, salvo pandas y pyarrow) ---
# argparse: leer opciones como --sector · json: armar y leer JSON · os: leer la clave del archivo .env
# re: buscar cifras en los textos · time: pausas entre pedidos · urllib: llamar a la API · datetime: fecha del resultado
import argparse, json, os, re, time, urllib.error, urllib.request
from datetime import date
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "procesado"
SALIDA = PROCESADO / "ia_titulos.parquet"

# Proveedores con la misma forma de llamada (formato compatible con OpenAI). El modelo va en MODELO, dentro de .env.
PROVEEDORES = {
    "GEMINI_API_KEY": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "OPENAI_API_KEY": "https://api.openai.com/v1/chat/completions",
    "DEEPSEEK_API_KEY": "https://api.deepseek.com/chat/completions",
}
POR_PEDIDO = 20          # proyectos por pedido: menos pedidos, para no agotar el cupo gratuito

INSTRUCCIONES = (
    "Eres un editor que convierte descripciones técnicas de proyectos de inversión pública del Perú en títulos claros "
    "para personas que no trabajan en inversión pública. Para cada proyecto recibes su id, su nombre oficial y su "
    "descripción técnica. Escribe UN título de una sola línea, de máximo 15 palabras, que diga qué hace el proyecto y, "
    "si la descripción lo dice, cuánto (cantidades) y dónde (lugares). Empieza con un verbo en presente: Construye, "
    "Mejora, Amplía, Equipa, Instala, Abre, Renueva, Repone, Adquiere. "
    "El título debe combinar dos cosas: (1) las ACCIONES CONCRETAS que detalla la descripción (qué se construye, equipa, "
    "instala o implementa, con sus cantidades si las hay: cuántos locales, aulas, ventanillas, kilómetros, equipos) y "
    "(2) el servicio o la instalación en palabras comunes (centro infantil, posta de salud, hospital, colegio, sistema de "
    "agua potable, carretera, oficinas de atención). No repitas ni parafrasees el nombre oficial: di lo que la "
    "descripción detalla. Escribe las siglas con su significado (CIAI = centro infantil; EESS = establecimiento de salud; "
    "IE = colegio). Ejemplos inventados: descripción 'Construcción de 12 aulas, 1 laboratorio y servicios higiénicos; "
    "adquisición de mobiliario' con nombre 'Mejoramiento del servicio educativo de la IE 123 de Ayaviri' -> 'Construye "
    "12 aulas y un laboratorio y equipa el colegio 123 de Ayaviri'; descripción 'Implementación de 5 módulos de atención "
    "y equipamiento informático en las sedes de Puno y Juliaca' -> 'Implementa 5 módulos de atención y equipa con "
    "computadoras las sedes de Puno y Juliaca'. "
    "Reglas: usa SOLO la información dada; no inventes cifras, lugares ni beneficiarios; copia las cifras tal como "
    "aparecen, sin sumarlas; no uses términos técnicos (PIP, IOARR, UEI, expediente, componente). Si la descripción no "
    "permite saber qué hace el proyecto, devuelve el título vacío. "
    'Responde solo con JSON: {"titulos": [{"id": "...", "titulo": "..."}]}, con un elemento por proyecto recibido.'
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

def paquete(filas):
    """Arma el pedido de un grupo de proyectos. Antes: filas de la tabla | Después: un texto JSON con id, nombre y descripción."""
    return json.dumps([{"id": f["id"], "nombre_oficial": f["nombre"], "descripcion_tecnica": f["alternativa"][:1200]}
                       for _, f in filas.iterrows()], ensure_ascii=False)

def cifras(texto):
    """Números que aparecen en un texto, sin separadores ni ceros a la izquierda.
    'Abre 1,200 puntos y 02 ventanillas' -> {'1200', '2'} (así '02' en el MEF y '2' en el título son la misma cifra)."""
    return {re.sub(r"[.,]", "", n).lstrip("0") or "0" for n in re.findall(r"\d[\d.,]*\d|\d", texto)}

def valido(titulo, fuente):
    """Control automático: el título no está vacío, es corto y todas sus cifras están en el texto del MEF."""
    return bool(titulo) and len(titulo) <= 130 and cifras(titulo) <= cifras(fuente)

def llamar(url, clave, modelo, contenido):
    cuerpo = json.dumps({"model": modelo, "temperature": 0.2, "response_format": {"type": "json_object"},
                         "messages": [{"role": "system", "content": INSTRUCCIONES}, {"role": "user", "content": contenido}]}).encode()
    pedido = urllib.request.Request(url, data=cuerpo, headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=120) as r:
        respuesta = json.loads(r.read().decode())
    datos = json.loads(respuesta["choices"][0]["message"]["content"])   # salida estructurada: si no es JSON, falla aquí
    return {str(x.get("id")): str(x.get("titulo", "")).strip() for x in datos.get("titulos", [])}, respuesta.get("usage", {})

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sector", nargs="*", help='Uno o más sectores tal como los escribe el MEF; sin esta opción, todos')
    p.add_argument("--limite", type=int, default=200, help="Máximo de proyectos a procesar en esta corrida (tope de gasto)")
    p.add_argument("--ensayo", action="store_true", help="Muestra lo que se enviaría, sin llamar a la IA")
    p.add_argument("--rehacer", action="store_true", help="Vuelve a procesar los proyectos elegidos aunque ya tengan título")
    a = p.parse_args()

    # Proyectos con una descripción útil (más de 30 caracteres), de mayor a menor costo
    base = pd.read_parquet(PROCESADO / "cinco_preguntas.parquet")
    base = base[base["alternativa"].fillna("").str.strip().str.len() > 30]
    if a.sector:
        base = base[base["sector"].isin(a.sector)]
    previas = pd.read_parquet(SALIDA) if SALIDA.exists() else pd.DataFrame(columns=["id", "titulo_ia", "modelo", "fecha"])
    if a.rehacer:   # se olvidan los títulos anteriores de los proyectos elegidos, para escribirlos de nuevo
        previas = previas[~previas["id"].isin(base["id"])]
    pendientes = base[~base["id"].isin(previas["id"])].sort_values("costo", ascending=False).head(a.limite)
    print(f"Con descripción: {len(base):,} · ya procesados: {base['id'].isin(previas['id']).sum():,} · en esta corrida: {len(pendientes):,}")

    if a.ensayo:
        print("--- Instrucciones ---\n" + INSTRUCCIONES)
        print("--- Ejemplo de pedido (primeros 2 proyectos) ---\n" + (paquete(pendientes.head(2)) if len(pendientes) else "(nada pendiente)"))
        return

    leer_env()
    clave_env = next((k for k in PROVEEDORES if os.environ.get(k)), None)
    modelo = os.environ.get("MODELO")
    if not clave_env or not modelo:
        raise SystemExit("Falta la clave o el modelo en .env (ver .env.example).")

    nuevas, rechazados, tokens_in, tokens_out = [], 0, 0, 0
    for inicio in range(0, len(pendientes), POR_PEDIDO):
        grupo = pendientes.iloc[inicio:inicio + POR_PEDIDO]
        try:
            titulos, uso = llamar(PROVEEDORES[clave_env], os.environ[clave_env], modelo, paquete(grupo))
        except urllib.error.HTTPError as e:
            if e.code == 429:                                   # se acabó el cupo: guardar lo avanzado y salir
                print("Se alcanzó el límite del proveedor (429). Se guarda lo avanzado; vuelve a correrlo más tarde.")
                break
            print(f"  error HTTP {e.code} en el grupo que empieza en {inicio}")
            continue
        except Exception as e:                                  # una falla no detiene el resto
            print(f"  error en el grupo que empieza en {inicio}: {type(e).__name__}")
            continue
        tokens_in += uso.get("prompt_tokens", 0)
        tokens_out += uso.get("completion_tokens", 0)
        for _, f in grupo.iterrows():
            t = titulos.get(str(f["id"]), "")
            if valido(t, f"{f['alternativa']} {f['nombre']}"):
                nuevas.append({"id": f["id"], "titulo_ia": t.rstrip("."), "modelo": modelo, "fecha": str(date.today())})
            else:
                rechazados += 1
                sobran = cifras(t) - cifras(f"{f['alternativa']} {f['nombre']}")
                print(f"    descartado {f['id']}: «{t}»" + (f" (cifras que no están en el MEF: {', '.join(sorted(sobran))})" if sobran else ""))
        print(f"  {inicio + len(grupo):,} de {len(pendientes):,} enviados")
        time.sleep(2)

    todas = pd.concat([previas, pd.DataFrame(nuevas)], ignore_index=True).drop_duplicates("id", keep="last")
    todas.to_parquet(SALIDA, index=False)
    print(f"Listo: {len(nuevas):,} títulos nuevos · rechazados por el control: {rechazados:,} · total guardado: {len(todas):,}")
    print(f"Tokens: {tokens_in:,} de entrada y {tokens_out:,} de salida (multiplica por el precio de tu modelo para el costo)")

if __name__ == "__main__":
    main()
