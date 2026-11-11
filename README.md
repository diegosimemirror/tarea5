# Portafolio de proyectos del Estado · La cartera de inversiones, en simple

Simplificamos la lectura de cómo van los proyectos de inversión del Estado peruano: cuántos hay, cuánto cuestan, cuánto se ha ejecutado, dónde están y qué problemas reportan, en preguntas simples y con datos abiertos del MEF.

> **Demo en vivo:** https://proyectos-inversiones-peru.streamlit.app/ · Versión del 10/11/2026. Las partes marcadas **POR COMPLETAR** las escribe el founder.

## 1. One-liner

**Simplificamos la lectura de cómo van los proyectos de inversión del Estado, para quienes deciden o supervisan sin ser especialistas en Invierte.pe, traduciendo los datos abiertos del MEF a preguntas simples, indicadores de cartera y un mapa.**

## 2. Founder

**POR COMPLETAR (Diego).** Quién soy y por qué soy la persona indicada. Ideas para confirmar: gestor público, PMP, experiencia en inversión pública y en cooperación (MIDIS, EsSalud), y haber visto de cerca que un ministerio no siempre tiene a mano el Excel completo de sus proyectos.

## 3. Problema

- **Quién lo sufre:** la alta dirección, los organismos cooperantes, los asesores, los periodistas y la ciudadanía. Son personas que necesitan una vista de alto nivel, pero no trabajan en inversiones.
- **Qué les pasa:**
  - La información existe, pero está escrita para especialistas: siglas (PIM, devengado, UEI, OPMI, IOARR), formatos (8, 9, 12-B) y fichas de un proyecto a la vez.
  - Los informes de seguimiento son textos largos que no dejan ver el conjunto.
- **Cuánto pesa:** el gobierno nacional tiene **12 731 inversiones activas por S/ 621 mil millones**. Con nuestras reglas, **3 380 están atrasadas** según sus propias fechas registradas.
- **Cómo lo resuelven hoy:** abren el SSI ficha por ficha, piden un Excel a la OPMI o leen informes.
- **Evidencia:** notas de 3 conversaciones en [`docs/research/`](docs/research/). Las dos primeras son anteriores a la app y están reconstruidas de memoria:
  - **Noviembre–diciembre de 2019, asesores de la OPMI de un ministerio del sector salud** ([nota 1](docs/research/01_conversacion.md)): para seguir las obras del Bicentenario era difícil tener al día una matriz con ejecución, ubicación, problemas y riesgos.
  - **Julio de 2023, la banca multilateral con la alta dirección de un ministerio del sector salud** ([nota 2](docs/research/02_conversacion.md)): lo primero que pidió fue una cartera de proyectos visible y ordenable por temas. No se pudo mostrar en la reunión: se armó después, en Excel que se actualizaban uno sobre otro.
  - **Conversación 3, con la app:** **POR COMPLETAR.**

## 4. Solución e insight

**Solución.** Primero ves la **cartera completa**: cada ministerio o entidad con su número de proyectos y su costo. Luego eliges un ministerio y ves:
1. El **árbol de su cartera**: el ministerio, sus unidades ejecutoras y sus proyectos.
2. Cada proyecto respondido en **cinco preguntas**: ¿qué es?, ¿qué problema resuelve?, ¿cuánto cuesta y cuánto se ha gastado?, ¿cuándo termina? y ¿cómo va?
3. El detalle técnico, a un clic, en el MEF.

**Insight.** El problema no es la falta de datos, porque el MEF publica todo y a diario. El problema es que **están escritos para quien los registra, no para quien decide**. El valor está en traducir, no en sumar indicadores.

## 5. Why now

- El MEF publica en su portal de Datos Abiertos, **en bloque y con actualización frecuente** (la última, el 08/11/2026), el detalle de todas las inversiones, sus brechas y su último seguimiento (12-B). El conjunto "Detalle de inversiones" existe desde marzo de 2023.
- **Los modelos de lenguaje ya pueden traducir** un texto técnico a lenguaje simple a bajo costo y con salidas estructuradas verificables.

## 6. Demo

- **URL pública:** https://proyectos-inversiones-peru.streamlit.app/ (Streamlit Community Cloud, gratis). Para abrir directamente la ficha de un proyecto: `https://proyectos-inversiones-peru.streamlit.app/?ficha=CUI` (por ejemplo, `?ficha=2613205`).
- **Correr en local:**
  ```bash
  pip install -r requirements.txt
  python scripts/01_descargar.py      # baja los datos del MEF (≈ 537 MB)
  python scripts/03_preparar.py       # arma la base del gobierno nacional
  python scripts/04_traducir.py       # cinco preguntas en lenguaje simple
  streamlit run app/app.py
  ```
  Los archivos procesados ya vienen en `data/procesado/`, así que basta con el último comando.
- **Capturas:** **POR COMPLETAR** (3).
- **Arquitectura:**
  ```mermaid
  flowchart LR
    A[MEF · Datos Abiertos] -->|descarga diaria| B[Preparar en Python]
    B --> C[Traducir: reglas + IA]
    C --> D[App web en Streamlit]
    D --> E[Persona en el navegador]
  ```
- **Modelos y APIs:** API pública de Datos Abiertos del MEF. El LLM para redactar está **POR COMPLETAR**, según la API que se elija; ver la sección 8.

## 7. Modelo de negocio

### Quién usa y quién paga
- **Usa:** la alta dirección de una entidad pública y sus asesores (ministros, viceministros, gobernadores, alcaldes). Necesitan ver su cartera sin ser especialistas en Invierte.pe.
- **Paga:** la propia **entidad pública**. Contrata la oficina que hoy arma los reportes (planeamiento u OPMI).
- **Evidencia:** en julio de 2023, la alta dirección de un ministerio no pudo mostrar su cartera en una reunión con la banca multilateral; hubo que armarla después ([nota 2](docs/research/02_conversacion.md)).
- **Segundo grupo:** la banca multilateral, los cooperantes y las consultoras, que revisan carteras de varios sectores antes de financiar.
- **Gratis:** la versión que ya funciona (gobierno nacional), para la ciudadanía, los periodistas y los estudiantes.

### Precio
**US$ 100 al mes por entidad** (≈ S/ 370), o **US$ 1 200 al año**, hasta 5 usuarios. Incluye:
- su cartera con los indicadores y las fichas;
- alertas por correo cuando un proyecto cambia de estado;
- un reporte descargable para reuniones;
- el **historial**: una copia diaria de los datos del MEF para medir el atraso frente a la fecha original, que el MEF no guarda.

**Por qué ese precio:**
- **Hoy la cartera la arma un especialista a mano.** Supuesto: gana S/ 7 000 al mes y dedica una semana al mes a armarla, unos S/ 1 750 mensuales. El precio es casi cinco veces menor.
- **El monto anual es pequeño para una entidad.** Hay que verificar en la Ley 32069 el umbral para contrataciones menores.
- **Supuestos por validar** en la conversación 3.

**Mercado:** **2 020 entidades** tienen hoy inversiones activas: 184 del gobierno nacional, 30 regionales y 1 806 locales (MEF, 08/11/2026). Si todas pagaran, serían US$ 2,4 millones al año.

### Costo por usuario (servidor y tokens)

| Concepto | Hoy | Versión de pago |
|---|---|---|
| Servidor | US$ 0 (Streamlit Community Cloud) | ≈ US$ 25 al mes, compartido por todos los clientes |
| Datos | US$ 0 (MEF, datos abiertos) | US$ 0 |
| Tokens de IA | US$ 0 (los textos salen de reglas) | ≈ US$ 4 por actualizar los 12 731 proyectos nacionales; ≈ US$ 45 por los 150 641 de todo el país |

- **Supuesto de tokens:** 1 000 de entrada y 250 de salida por proyecto, con un modelo pequeño a US$ 0,15 y US$ 0,60 por millón de tokens. El precio exacto se confirma al elegir el proveedor (sección 8).
- **Con 20 entidades,** servidor más IA suman ≈ US$ 70 al mes: **≈ US$ 3,5 por entidad**, frente a un precio de US$ 100.
- **La IA se paga por proyecto actualizado, no por usuario,** así que el costo por cliente baja con cada cliente nuevo.

### Qué sigue
1. Gobiernos regionales y locales (13 681 y 124 229 inversiones).
2. Pasar de "problemas reportados" a "riesgos" con IA.
3. Historial diario y alertas.
4. Los primeros 3 clientes, entre las entidades donde el founder ha trabajado.

## 8. Herramientas del curso

| Herramienta | Sesión | Dónde está | Por qué esta |
|---|---|---|---|
| Scraping y APIs (datos abiertos) | 03 | `scripts/01_descargar.py` | Los datos de inversión pública ya existen y son públicos: el valor está en traerlos solos y al día, no en digitarlos. |
| Dashboards | 05 | `app/app.py` | La usuaria es la alta dirección: necesita ver su cartera en una pantalla, en el navegador, sin instalar nada. |
| LLMs con salidas estructuradas | 08 | `scripts/06_ia.py` (código listo, **todavía sin activar**: falta elegir proveedor y poner la clave) | Para redactar en simple los textos técnicos y clasificar los problemas, con salida en JSON para revisar cada campo. Mientras no esté activa, no se cuenta entre las dos herramientas del producto. |

## 9. Qué hizo el agente

Claude Code escribió los scripts de descarga, exploración, preparación y traducción, la app en Streamlit y su prueba automática, a partir del problema, el diseño y las decisiones del founder. **POR COMPLETAR:** qué revisó y cambió el founder.

## Datos y limitaciones

- **Fuente:** MEF, Datos Abiertos (Detalle de inversiones, Inversiones y brechas, Formato 12-B), al 08/11/2026.
- **Exploración y decisiones de limpieza:** [`docs/informe_exploracion.md`](docs/informe_exploracion.md).
- **Mapa de procesos:** [`docs/mapa_de_procesos.md`](docs/mapa_de_procesos.md).
- **El estado de cada proyecto se calcula con reglas de ejemplo** a partir de las fechas y montos que registran las entidades. No es una evaluación oficial.
- **Datos personales:** no se usan.
