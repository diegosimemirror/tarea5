# ============================================================
# PROCESO 10: ¿Ya se ejecutó?, ¿qué incluye? y ¿en qué fase está? (lectura del 12-B, componentes, fase y prioridad del MEF)
# Insumo:    data/procesado/inversiones.parquet (Proceso 3: textos del último 12-B, avance declarado, formatos 8 y 9,
#            nombre, descripción técnica y tipología de cada inversión)
# Resultado: data/procesado/fases_componentes.parquet, una fila por inversión con:
#            lectura_12b y lectura_porque: qué dice el texto del 12-B sobre la ejecución y la frase que lo sustenta
#            ya_ejecutada: True si el texto, el número o el formato de cierre dicen que ya se ejecutó (sale de los portafolios)
#            comp_infra, comp_equipo, comp_gestion, componentes y comp_fuente: componentes deducidos del nombre y de la
#              descripción técnica (el MEF no publica los componentes en sus datos abiertos)
#            fase y prelacion: fase de la inversión y su grupo (1 a 9) en el orden de prelación del MEF para el PMI
#              (Directiva N.° 001-2019-EF/63.01, art. 15.2)
# Uso:       uv run --with "pandas<3" --with pyarrow python scripts/10_fases_componentes.py
# Por qué:   en EsSalud, 308 inversiones tienen 0 % de avance en el 12-B, pero su texto dice «inversiones ejecutadas en el
#            marco de la pandemia». Leer solo el número las hacía ver como pendientes de financiar.
# ============================================================

# --- Paquetes ---
# pathlib, re, json: rutas, búsqueda de patrones en el texto y leer la fecha de los datos (vienen con Python)
# pandas: tablas; pyarrow: leer y guardar parquet (se instalan una vez)
from pathlib import Path
import re
import json
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADO = RAIZ / "data" / "procesado"
HOY = pd.Timestamp(json.loads((PROCESADO / "fechas.json").read_text(encoding="utf-8"))["mef"])

inv = pd.read_parquet(PROCESADO / "inversiones.parquet")
print("10.0 Inversiones:", len(inv))

# --- Ayudas de texto ---
TABLA = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")

def norm(t):
    """Minúsculas y sin tildes, con el mismo largo (así la frase encontrada se ubica en el texto original).
    Antes: 'Inversión EJECUTADA' | Después: 'inversion ejecutada'."""
    return str(t or "").translate(TABLA).lower()

def partes(texto):
    """Separa la categoría del 12-B de su detalle. El Proceso 3 ya quitó la fecha inicial.
    Antes: '- En proceso de recepción / conformidad técnica <br>EJECUTADO, SEGÚN CEABE'
    Después: ('En proceso de recepción / conformidad técnica', 'EJECUTADO, SEGÚN CEABE')"""
    t = re.sub(r"^\s*-\s*", "", str(texto or ""))
    if re.search(r"<br\s*/?>", t, re.I):
        cat, det = re.split(r"<br\s*/?>", t, maxsplit=1, flags=re.I)
    else:
        cat, det = "", t
    limpiar = lambda s: re.sub(r"\s+", " ", re.sub(r"<br\s*/?>", " ", s, flags=re.I)).strip().strip('"').strip()
    return limpiar(cat), limpiar(det)

def fragmento(original, ini, fin, ancho=60):
    """La frase encontrada con hasta `ancho` caracteres de contexto a cada lado, cortada en palabras completas.
    Antes: '…egistro correcto, teniendo…' | Después: '…registro correcto, teniendo…'"""
    a, b = max(0, ini - ancho), min(len(original), fin + ancho)
    if a > 0 and " " in original[a:ini]:
        a = original.index(" ", a) + 1                 # empieza en la palabra siguiente, no a la mitad de una
    if b < len(original) and " " in original[fin:b]:
        b = original.rindex(" ", fin, b)               # termina en la palabra anterior
    return ("…" if a > 0 else "") + original[a:b].strip() + ("…" if b < len(original) else "")

# ============================================================
# PASO 10.1: ¿Qué dice el 12-B sobre la ejecución? (lectura del texto)
#   Se leen la situación actual (categoría y detalle) y los próximos pasos. Reglas en orden; gana la primera que aplica.
#   Revisadas a mano sobre todos los textos distintos de las 798 inversiones de EsSalud (19/11/2026).
#   Antes: '[Otras situaciones] … se trata de inversiones ejecutadas en el marco de la pandemia por COVID-19.' con 0 %
#   Después: lectura_12b = 'Ya ejecutada', lectura_porque = 'Situación actual: «…inversiones ejecutadas en el marco…»'
# ============================================================
HECHO = (r"se ejecutaron|se ejecuto|items? (?:se encuentra[n]? )?ejecutad|ejecutados|se han ejecutado|se ha ejecutado"
         r"|ya fue ejecutad|se encuentra ejecutado el|adquiridos?|se han adquirido|en etapa de recepcion|en proceso de recepcion el"
         r"|ejecucion parcial|pendientes de ejecucion \d+ unidades")
PENDIENTE = (r"actos preparatorios|interaccion (?:de|con el) mercado|convocatoria|pendiente|por ejecutar|por adquirir|por aquirir"
             r"|estudio de mercado|desierto|ejecucion contractual|ejecucion parcial|en proceso de compra|de los cuales")
# Cierre que NO es por haber terminado: por pérdida de vigencia, sin ejecución, o «priorización o cierre» (aún se evalúa)
NO_TERMINADA = r"perdida de vigencia|perdio vigencia|sin ejecucion|no se ejecut|desactiv|priorizacion o cierre|o cierre de la"
REGLAS = [   # (lectura, dónde se busca, expresión regular)
    # Solo con una intención clara («se solicitará», «procederá a gestionar», «en proceso de»): «el riesgo de desactivación»
    # o «analizará la posible desactivación» no bastan
    ("No se ejecutará", "det", r"se solicitara la desactivacion|solucion menos eficiente"
                               r"|(?:gestionar|se procedera con|en proceso de|solicitar) (?:la )?desactivacion"),
    ("No se ejecutará", "prox", r"cierre por perdida de vigencia|cierre por no ejecuci|cierre sin ejecuci"
                                r"|(?:gestionar|se procedera con|en proceso de|solicitar) (?:la )?desactivacion"),
    ("Obra concluida, con pagos pendientes (APP)", "det", r"retribucion por inversiones|obras culminadas en \w+ \d{4}"),
    ("Ejecución parcial", "parcial", None),
    # Terminada pero con un pago pendiente (todavía necesita dinero): «culminada, pendiente pago de liquidación»
    ("Terminada, en recepción o liquidación", "det", r"pendiente (?:de )?pago|pago de (?:la )?liquidacion|pagos? pendientes?|por pagar"),
    ("Terminada, en recepción o liquidación", "prox", r"pendiente (?:de )?pago|pago de (?:la )?liquidacion"),
    # Obra o inversión terminada, dicho de muchas formas (regla amplia, con excepciones: ver TERMINO más abajo)
    ("Ya ejecutada", "termino", None),
    ("Ya ejecutada", "det", r"inversiones ejecutadas en el marco de la pandemia|ejecutado,? segun lo informado por ceabe"
                            r"|inversion(?: de \w+)? ejecutada|ioarr(?: de \w+)? ejecutad[oa]|se ha culminado la adquisicion de equipos"
                            r"|adquirido al 100|^ejecutad[oa]\b|^(?:obra|inversion|ioarr|proyecto) (?:culminad|concluid|ejecutad)"
                            # «proyecto ejecutado bajo la modalidad de contrata» habla de la modalidad, no de que terminó
                            r"(?![a-z]*\s+(?:bajo|mediante|por|en la modalidad|a traves))"),
    ("Terminada, en recepción o liquidación", "det", r"\ben recepcion|etapa de recepcion|recepcion de obra|en proceso de recepcion"
                                                    r"|obra recepcionada|proceso de liquidacion"),
    ("Ya ejecutada", "cat", r"inversion culminada / 100% ejecutada"),
    ("Terminada, en recepción o liquidación", "cat", r"en proceso de recepcion|en proceso de liquidacion"),
    ("Ya ejecutada", "prox", r"registrar (?:el )?cierre|registro de cierre|proceso de cierre|evaluar (?:el )?cierre|evaluara el cierre"
                             r"|coordinaciones para el cierre|formato de cierre|cierre de la inversion|se encuentra ejecutada"),
    ("Perdió vigencia o en evaluación", "det", r"perdio vigencia|para continuidad|persistencia de necesidad"),
    ("Sin información en el texto", "det", r"recabando informacion|coordinando con ceabe|^$"),
]
CAMPO = {"det": "Situación actual", "cat": "Categoría del 12-B", "prox": "Próximos pasos", "parcial": "Situación actual"}
# Regla amplia de término: «la obra fue concluida», «el proyecto ha culminado su ejecución física», «fue recepcionada»,
# «en operación y mantenimiento». No cuentan «expediente técnico culminado» ni «diseño culminado» (no es la obra).
TERMINO = (r"(?:obra|proyecto|inversion|ioarr|infraestructura)(?: de inversion(?: publica)?)?\s+"
           r"(?:se encuentra |esta |fue |ha sido |ha |han )?(?:culminad[oa]|culminado|concluid[oa]|terminad[oa])\b"
           r"|culminad[oa] la ejecucion (?:fisica|de la obra)|(?:ha|han) culminado (?:su|la) ejecucion fisica"
           r"|ejecucion fisica (?:culminad[oa]|concluid[oa]|terminad[oa])"
           r"|fue recepcionad[oa]|obra recepcionada|en operacion y mantenimiento|se encuentra en funcionamiento")
# Excepciones: si el texto habla de etapas, tramos o componentes, solo terminó una parte; sin acta de recepción, falta recibirla
PARTE = r"\betapa\s*0?\d|\btramo\b|componente de|primigenia|primera etapa|segunda etapa|parcial"
SIN_RECEPCION = r"no cuenta con acta de recepcion|sin acta de recepcion|pendiente (?:de )?(?:la )?recepcion"

def leer(cat, det, prox):
    """(categoría, detalle, próximos pasos) -> (lectura, frase que la sustenta)."""
    campos = {"det": det, "cat": cat, "prox": prox}
    for lectura, campo, patron in REGLAS:
        if campo == "parcial":
            h, p = re.search(HECHO, norm(det)), re.search(PENDIENTE, norm(det))
            if h and p:
                a, b = sorted([h, p], key=lambda m: m.start())
                if b.end() - a.start() <= 200:
                    return lectura, f"Situación actual: «{fragmento(det, a.start(), b.end(), 40)}»"
                return lectura, (f"Situación actual: «{fragmento(det, a.start(), a.end(), 50)}» … "
                                 f"«{fragmento(det, b.start(), b.end(), 50)}»")
            continue
        if campo == "termino":
            m = re.search(TERMINO, norm(det))
            if m:
                frase = f"Situación actual: «{fragmento(det, m.start(), m.end())}»"
                if re.search(PARTE, norm(det)):
                    return "Ejecución parcial", frase
                if re.search(SIN_RECEPCION, norm(det)):
                    return "Terminada, en recepción o liquidación", frase
                return lectura, frase
            continue
        m = re.search(patron, norm(campos[campo]))
        # «Registrar el cierre» no prueba que terminó si es un cierre por pérdida de vigencia o una evaluación abierta
        if m and lectura == "Ya ejecutada" and campo == "prox" and re.search(NO_TERMINADA, norm(prox)):
            continue
        if m:
            if campo == "det" and not det:
                return lectura, "La situación actual del 12-B no tiene texto."
            return lectura, f"{CAMPO[campo]}: «{fragmento(campos[campo], m.start(), m.end())}»"
    return "En proceso", ""

# Tiene 12-B si tiene fecha de su último 12-B o algún texto (un 12-B con el texto vacío es «sin información», no «sin 12-B»)
tiene_texto = inv["fecha_12b"].notna() | (inv["situacion_12b"].fillna("") != "")
sit = inv["situacion_12b"].fillna("").map(partes)
prox = inv["acciones_12b"].fillna("").map(lambda t: " ".join(partes(t)).strip())
inv["sit_categoria"] = [c for c, _ in sit]
lecturas = [leer(c, d, p) if t else ("Sin 12-B", "La entidad no tiene un formato 12-B registrado en el MEF.")
            for (c, d), p, t in zip(sit, prox, tiene_texto)]
inv["lectura_12b"] = [l for l, _ in lecturas]
inv["lectura_porque"] = [p for _, p in lecturas]

# Formato de cierre (formato 9) registrado y pendiente de liquidación: la ejecución física terminó (lo declara la entidad)
cierre_f9 = (inv["tiene_f9"] == "SI") & inv["etapa_f9"].str.contains("liquidaci", case=False, na=False)
neutra = inv["lectura_12b"].isin(["En proceso", "Sin información en el texto", "Sin 12-B"])
inv.loc[cierre_f9 & neutra, "lectura_12b"] = "Ya ejecutada"
inv.loc[cierre_f9 & neutra, "lectura_porque"] = "Registró su formato de cierre (formato 9): " + inv["etapa_f9"].str.lower() + "."
# Avance declarado de 100 % o más con un texto que no dice otra cosa: también se considera ejecutada
cien = (inv["avance_ejecucion_original"].fillna(0) >= 100) & inv["lectura_12b"].isin(["En proceso", "Sin información en el texto", "Sin 12-B"])
inv.loc[cien, "lectura_porque"] = ("La entidad declaró un avance de ejecución de " + inv["avance_ejecucion_original"].round(1).astype(str)
                                   + " % en el 12-B.")
inv.loc[cien, "lectura_12b"] = "Ya ejecutada"
inv["ya_ejecutada"] = inv["lectura_12b"] == "Ya ejecutada"
print("10.1 Lectura del 12-B:\n", inv["lectura_12b"].value_counts().to_string())
print("     Ya ejecutadas:", int(inv["ya_ejecutada"].sum()), "| por formato de cierre:", int((cierre_f9 & neutra).sum()),
      "| por avance de 100 % o más:", int(cien.sum()))

# ============================================================
# PASO 10.2: ¿Qué incluye? Componentes deducidos del nombre y de la descripción técnica
#   Tres clases, según los factores productivos de Invierte.pe:
#     Infraestructura (obras: construir, ampliar, remodelar, renovar ambientes, redes, vías…),
#     Equipamiento (equipos, mobiliario y vehículos) y Gestión e intangibles (software, sistemas de información,
#     capacitación, asistencia técnica, estudios, modelos de gestión).
#   IOARR: su nombre sigue el formato del MEF «ACCIÓN DE ACTIVOS; EN EL(LA) …»: se lee cada acción con su activo.
#   Proyectos y otros: la descripción técnica (ALTERNATIVA) suele listar sus componentes; si no dice nada útil, el nombre.
#   Antes: 'ADQUISICION DE CAMIONETA EN EL(LA) DESPACHOS FISCALES…' | Después: comp_equipo = True (fuente: nombre)
# ============================================================
ACCIONES_OBRA = (r"construccion|remodelacion|ampliacion|rehabilitacion|reparacion|reconstruccion|mejoramiento|instalacion|creacion"
                 r"|habilitacion|acondicionamiento|demolicion|sustitucion|adecuacion|recuperacion|renovacion|reforzamiento"
                 r"|optimizacion|reubicacion|implementacion")
ACCION = re.compile(r"\b(adquisicion|" + ACCIONES_OBRA + r")\s+(?:de|del|de la|de los|de las)\b", re.I)
EQUIPO = (r"\b(equipo|equipos|equipamiento|mobiliario|mobiliarios|vehiculo|vehiculos|vehicular|ambulancia|ambulancias|camioneta"
          r"|camionetas|camion|camiones|motocicleta|motocicletas|bus|buses|omnibus|grupo electrogeno|computadora|computadoras"
          r"|computo|impresora|impresoras|scanner|escaner|refrigeradora|tomografo|ventilador|ventiladores|monitor|monitores|ecografo"
          r"|resonador|rayos x|mamografo|autoclave|esterilizador|analizador|ascensor|ascensores|montacargas|maquinaria|maquina|maquinas"
          r"|embarcacion|embarcaciones|aeronave|dron|drones|camara|camaras|luminaria|luminarias|bomba|bombas|electrobomba|transformador"
          r"|instrumental|aire acondicionado|chiller|caldero|calderos|incubadora|incubadoras|cama|camas|mesa|mesas|silla|sillas"
          r"|carpeta|carpetas|estante|estantes|armario|servidor|servidores|laptop|proyector|multimedia|tablet|tabletas|radio|radios"
          r"|telescopio|microscopio|centrifuga|horno|congeladora|cocina|lavadora|secadora|mochila|kit|kits|uniforme"
          r"|implementacion|implementado|implementada|equipado|equipada|equipados|equipadas"
          r"|desfibrilador|electrocardiografo|endoscopio|videoendoscopio|laparoscopio|angiografo|acelerador lineal|gammagrafo"
          r"|tractor|tractores|retroexcavadora|cargador frontal|volquete|motoniveladora|rodillo|grua|cisterna movil|lancha|bote)\b")
GESTION = (r"\b(software|licencia|licencias|sistema de informacion|sistemas de informacion|sistema informatico|aplicativo|aplicativos"
           r"|plataforma (?:digital|informatica|tecnologica|web|virtual)|capacitacion|capacitaciones|desarrollo de capacidades"
           r"|fortalecimiento de capacidades|asistencia tecnica|sensibilizacion|educacion sanitaria|modelo de gestion|gestion del conocimiento"
           r"|consultoria|consultorias|transferencia tecnologica|base de datos|interoperabilidad|telesalud"
           r"|telemedicina|historia clinica electronica|digitalizacion|organizacion comunal|fortalecimiento institucional"
           r"|desarrollo de competencias|plan de negocios)\b")
INFRA = (r"\b(infraestructura|edificacion|edificaciones|ambiente|ambientes|aula|aulas|cerco|cerco perimetrico|techo|techos|cobertura"
         r"|coberturas|pabellon|pabellones|local|locales|sala|salas|topico|consultorio|consultorios|servicios higienicos|pista|pistas"
         r"|calzada|vereda|veredas|via|vias|carretera|carreteras|camino|caminos|puente|puentes|pontones?|canal|canales|reservorio|reservorios"
         r"|captacion|captaciones|redes?|linea de conduccion|lineas de conduccion|tuberia|tuberias|pavimento|pavimentacion|losa|losas|muro"
         r"|muros|almacen|almacenes|modulo|modulos|cisterna|tanque elevado|alcantarillado|desague|drenaje|obras? de arte|obra|obras"
         r"|m2|bloque|bloques|piso|pisos|escalera|escaleras|rampa|rampas|fachada|cerramiento|cubierta|cubiertas|defensa ribereña"
         r"|defensas ribereñas|dique|bocatoma|planta de tratamiento|subestacion|linea de transmision|linea primaria|red primaria"
         r"|red secundaria|plataforma|afirmado|asfalto|asfaltado|carpeta asfaltica|embalse|presa|muelle|terminal|losa deportiva"
         r"|estadio|coliseo|complejo|centro de salud|puesto de salud|hospital|establecimiento|establecimientos|sede|comisaria|cancha"
         r"|piscina|campo deportivo|trocha|camino vecinal|zanja|aliviadero|enrocado|gavion|gaviones|sistema de riego|riego)\b")

def componentes_ioarr(nombre):
    """IOARR: cada acción con su lista de activos. Antes: el nombre | Después: {'infra', 'equipo', 'gestion'} presentes."""
    n = norm(nombre)
    n = re.split(r"\ben el\(la\)|\ben (?:el|la|los|las) (?=\w)", n, maxsplit=1)[0]   # quita la ubicación «EN EL(LA) …»
    encontrados = set()
    marcas = list(ACCION.finditer(n))
    for i, m in enumerate(marcas):
        accion = m.group(1)
        activos = n[m.end(): marcas[i + 1].start() if i + 1 < len(marcas) else len(n)]
        if re.search(GESTION, activos):
            encontrados.add("gestion")
        if re.search(EQUIPO, activos):
            encontrados.add("equipo")
        if re.search(INFRA, activos):
            encontrados.add("infra")
        if not re.search(GESTION + "|" + EQUIPO + "|" + INFRA, activos):   # activo sin palabra conocida: decide la acción
            encontrados.add("equipo" if accion == "adquisicion" else "infra")
    return encontrados

def componentes_texto(texto):
    """Proyectos: palabras de cada clase en la descripción técnica o el nombre."""
    t = norm(texto)
    hallados = set()
    if re.search(r"\b(" + ACCIONES_OBRA + r")\b", t) and re.search(INFRA, t) or re.search(r"\binfraestructura\b|\bobras?\b|\bm2\b", t):
        hallados.add("infra")
    if re.search(EQUIPO, t):
        hallados.add("equipo")
    if re.search(GESTION, t):
        hallados.add("gestion")
    return hallados

def componentes(f):
    """Antes: una fila del MEF | Después: (conjunto de componentes, fuente de la deducción)."""
    if f["tipo_grupo"] == "IOARR":
        return componentes_ioarr(f["nombre"]), "nombre"
    alt = str(f["alternativa"] or "")
    # La descripción sirve si dice algo distinto del nombre (a veces lo repite) y tiene un largo mínimo
    if len(alt) >= 60 and norm(alt)[:60] != norm(f["nombre"])[:60]:
        hallados = componentes_texto(alt)
        if hallados:
            return hallados, "descripción técnica"
    hallados = componentes_texto(f["nombre"])
    if hallados:
        return hallados, "nombre"
    # Último recurso: la tipología del MEF (vías, agua, riego, energía… son obras)
    if re.search(r"carreter|vias|vial|riego|saneamiento|agua|energ|electri|puerto|aeropuerto|defensa|camino|puente|infraestructura",
                 norm(f["tipologia"])):
        return {"infra"}, "tipología (aproximado)"
    return set(), "sin información suficiente"

dedu = inv.apply(componentes, axis=1)
for clave in ("infra", "equipo", "gestion"):
    inv[f"comp_{clave}"] = [clave in c for c, _ in dedu]
inv["comp_fuente"] = [f for _, f in dedu]
NOMBRES_COMP = {"infra": "Infraestructura", "equipo": "Equipamiento", "gestion": "Gestión e intangibles"}

def combinacion(f):
    """Antes: comp_infra=True, comp_equipo=True, comp_gestion=False | Después: 'Infraestructura + Equipamiento'."""
    presentes = [NOMBRES_COMP[k] for k in NOMBRES_COMP if f[f"comp_{k}"]]
    if not presentes:
        return "Sin información"
    return ("Solo " + presentes[0].lower()) if len(presentes) == 1 else " + ".join(presentes)

inv["componentes"] = inv.apply(combinacion, axis=1)
print("10.2 Componentes:\n", inv["componentes"].value_counts().to_string())
print("     Fuente:", inv["comp_fuente"].value_counts().to_dict())

# ============================================================
# PASO 10.3: ¿En qué fase está?
#   Tres fuentes, y gana la más avanzada (una inversión no retrocede de fase):
#     1) la categoría de la situación del último 12-B; 2) la etapa del formato 8 (A = antes del expediente técnico,
#     B = expediente técnico registrado, C = ejecución física); 3) el avance físico declarado.
#   La lectura del 12-B manda para «ya ejecutada», «terminada» y «detenida».
#   Fases (de menos a más avanzada): idea → aprobada → expediente → contratar → ejecucion → terminada → ejecutada.
#   Antes: etapa_f8 = 'Ejecución física (C)', categoría = 'En actos previos para la contratación…' | Después: fase = 'ejecucion'
# ============================================================
ORDEN_FASE = ["idea", "aprobada", "expediente", "contratar", "ejecucion", "terminada", "ejecutada"]
CATEGORIA_FASE = [   # (patrón de la categoría del 12-B, fase)
    (r"elaboracion de expediente|actos previos para la contratacion de et|seleccion / contratacion para la elaboracion"
     r"|actualizacion / reformulacion", "expediente"),
    (r"actos previos para la contratacion de adquisicion|seleccion / contratacion de adquisicion|contrato suscrito"
     r"|documento equivalente aprobado, sin inicio", "contratar"),
    (r"en ejecucion de obra", "ejecucion"),
    (r"recepcion / conformidad|proceso de liquidacion|inversion culminada", "terminada"),
]

def fase(f):
    """Antes: una fila del MEF | Después: la clave de su fase ('detenida' si está detenida o se desactivará)."""
    if f["ya_ejecutada"]:
        return "ejecutada"
    if f["lectura_12b"] == "Terminada, en recepción o liquidación":
        return "terminada"
    candidatas = []
    cat = norm(f["sit_categoria"])
    for patron, clave in CATEGORIA_FASE:
        if re.search(patron, cat):
            candidatas.append(clave)
    etapa = str(f["etapa_f8"] or "")
    empezo = (f["avance_fisico"] or 0) > 0 or (f["avance_ejecucion"] or 0) > 0
    if "(C)" in etapa:
        candidatas.append("ejecucion" if empezo else "contratar")
    elif "(B)" in etapa or f["expediente_tecnico"] == "SI":
        candidatas.append("contratar")
    elif "(A)" in etapa:
        candidatas.append("expediente")
    if empezo:
        candidatas.append("ejecucion")
    if not candidatas:
        candidatas.append("idea" if "FORMULACION" in str(f["situacion"]) else "aprobada")
    mejor = max(candidatas, key=ORDEN_FASE.index)
    # Detenida: la entidad dice que no se ejecutará, perdió vigencia o está en controversia (si no llegó a terminar)
    detenida = (f["lectura_12b"] in ("No se ejecutará", "Perdió vigencia o en evaluación")
                or re.search(r"controversia|paralizad", cat) is not None)
    if detenida and ORDEN_FASE.index(mejor) < ORDEN_FASE.index("terminada"):
        return "detenida"
    return mejor

inv["fase"] = inv.apply(fase, axis=1)

# ============================================================
# PASO 10.4: Prioridad según el MEF (orden de prelación para el Programa Multianual de Inversiones, PMI)
#   Directiva N.° 001-2019-EF/63.01, artículo 15, párrafo 15.2 (vigente; EsSalud también lo aplica, art. 17.1):
#     1 ejecución física concluida, en liquidación o por iniciarla · 2 en ejecución física que termina en el año 1 del PMI ·
#     3 en ejecución física que termina en los años 2 o 3 · 4 en ejecución física que termina después del PMI ·
#     5 sin ejecución física, con expediente técnico o documento equivalente completo y vigente ·
#     6 sin ejecución física, con expediente o documento en elaboración · 7 con viabilidad o aprobación vigente ·
#     8 en formulación y evaluación · 9 ideas (no están en estos datos: solo hay inversiones activas)
#   PMI de referencia: el siguiente (año 1 = el próximo año). Detenidas: fuera del orden (vacío).
#   Antes: fase = 'ejecucion', fin = 2027-06-30 | Después: prelacion = 2
# ============================================================
ANIO_1 = HOY.year + 1
FIN_ANIO_1 = pd.Timestamp(year=ANIO_1, month=12, day=31)
FIN_ANIO_3 = pd.Timestamp(year=ANIO_1 + 2, month=12, day=31)
PRELACION = {"ejecutada": 1, "terminada": 1, "contratar": 5, "expediente": 6, "aprobada": 7, "idea": 8}

def prelacion(f):
    if f["fase"] == "ejecucion":
        if pd.notna(f["fin"]) and f["fin"] <= FIN_ANIO_1:
            return 2
        return 3 if pd.notna(f["fin"]) and f["fin"] <= FIN_ANIO_3 else 4
    return PRELACION.get(f["fase"])

inv["prelacion"] = inv.apply(prelacion, axis=1).astype("Int64")
print("10.3 Fase:\n", inv["fase"].value_counts().reindex(ORDEN_FASE + ["detenida"]).to_string())
print("10.4 Prioridad del MEF:\n", inv["prelacion"].value_counts(dropna=False).sort_index().to_string())

# ============================================================
# PASO 10.5: Verificar y guardar
# ============================================================
salida = inv[["id", "lectura_12b", "lectura_porque", "ya_ejecutada", "comp_infra", "comp_equipo", "comp_gestion", "componentes",
              "comp_fuente", "fase", "prelacion", "sit_categoria"]]
assert salida["id"].is_unique and len(salida) == len(inv), "se perdió o duplicó una inversión"
assert salida.loc[salida["ya_ejecutada"], "fase"].eq("ejecutada").all(), "una ya ejecutada quedó en otra fase"
assert salida["prelacion"].isna().eq(salida["fase"] == "detenida").all(), "prioridad sin fase"
for cui in ["2300016", "2569571", "2538136"]:
    e = inv[inv["cui"] == cui]
    if len(e):
        e = e.iloc[0]
        print(f"     {cui}: {e.lectura_12b} · fase {e.fase} · prioridad {e.prelacion} · {e.componentes} ({e.comp_fuente})")
salida.to_parquet(PROCESADO / "fases_componentes.parquet", index=False)
print("10.5 Guardado:", salida.shape, "->", PROCESADO / "fases_componentes.parquet")
