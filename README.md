# [Nombre por definir] · Cartera de inversiones del Estado, en simple

> Borrador del 10/11/2026. Las partes marcadas **POR COMPLETAR** las escribe el founder.

## 1. One-liner

**Hacemos que cualquier persona entienda en un minuto cómo van los proyectos de inversión de un ministerio, para quienes deciden o supervisan sin ser especialistas en Invierte.pe, traduciendo los datos abiertos del MEF a cinco preguntas simples.**

## 2. Founder

**POR COMPLETAR (Diego).** Quién soy y por qué soy la persona indicada. Ideas para confirmar: gestor público, PMP, experiencia en inversión pública y en cooperación (MIDIS, EsSalud), y haber visto de cerca que un ministerio no siempre tiene a mano el Excel completo de sus proyectos.

## 3. Problema

- **Quién lo sufre:** la alta dirección, los organismos cooperantes, los asesores, los periodistas y la ciudadanía. Son personas que necesitan una vista de alto nivel, pero no trabajan en inversiones.
- **Qué les pasa:**
  - La información existe, pero está escrita para especialistas: siglas (PIM, devengado, UEI, OPMI, IOARR), formatos (8, 9, 12-B) y fichas de un proyecto a la vez.
  - Los informes de seguimiento son textos largos que no dejan ver el conjunto.
- **Cuánto pesa:** el gobierno nacional tiene **12 731 inversiones activas por S/ 621 mil millones**. Con nuestras reglas, **3 380 están atrasadas** según sus propias fechas registradas.
- **Cómo lo resuelven hoy:** abren el SSI ficha por ficha, piden un Excel a la OPMI o leen informes.
- **Evidencia:** notas de 3 conversaciones en [`docs/research/`](docs/research/). **POR COMPLETAR.**

## 4. Solución e insight

**Solución.** Eliges un ministerio y ves:
1. El **árbol de su cartera**: el ministerio, sus unidades ejecutoras y sus proyectos.
2. Cada proyecto respondido en **cinco preguntas**: ¿qué es?, ¿qué problema resuelve?, ¿cuánto cuesta y cuánto se ha gastado?, ¿cuándo termina? y ¿cómo va?
3. El detalle técnico, a un clic, en el MEF.

**Insight.** El problema no es la falta de datos, porque el MEF publica todo y a diario. El problema es que **están escritos para quien los registra, no para quien decide**. El valor está en traducir, no en sumar indicadores.

## 5. Why now

- El MEF publica en su portal de Datos Abiertos, **en bloque y con actualización frecuente** (la última, el 08/11/2026), el detalle de todas las inversiones, sus brechas y su último seguimiento (12-B). El conjunto "Detalle de inversiones" existe desde marzo de 2023.
- **Los modelos de lenguaje ya pueden traducir** un texto técnico a lenguaje simple a bajo costo y con salidas estructuradas verificables.

## 6. Demo

- **URL pública:** **POR COMPLETAR** (Streamlit Community Cloud).
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

**POR COMPLETAR**, con lo que salga de las conversaciones. Opciones para validar:
- **Quién paga:** organismos cooperantes y consultoras que supervisan carteras; OPMI y alta dirección de entidades; medios y ONG de transparencia (versión ciudadana gratuita).
- **Precio concreto:** por definir. Por ejemplo, una suscripción mensual por entidad seguida.
- **Costo por usuario:**
  - El servidor es gratuito (Streamlit Community Cloud) y los datos son públicos.
  - La IA se paga una sola vez por cada actualización de los textos: tokens por proyecto × proyectos × precio del proveedor. Se calcula al elegir la API.

## 8. Herramientas del curso

| Herramienta | Sesión | Dónde está |
|---|---|---|
| Datos e ingesta: APIs y datos abiertos | 03 | `scripts/01_descargar.py` |
| Dashboards | 05 | `app/app.py` |
| LLMs con salidas estructuradas | 08 | `scripts/06_ia.py` (listo; falta elegir proveedor y poner la clave) |

## 9. Qué hizo el agente

Claude Code escribió los scripts de descarga, exploración, preparación y traducción, la app en Streamlit y su prueba automática, a partir del problema, el diseño y las decisiones del founder. **POR COMPLETAR:** qué revisó y cambió el founder.

## Datos y limitaciones

- **Fuente:** MEF, Datos Abiertos (Detalle de inversiones, Inversiones y brechas, Formato 12-B), al 08/11/2026.
- **Exploración y decisiones de limpieza:** [`docs/informe_exploracion.md`](docs/informe_exploracion.md).
- **Mapa de procesos:** [`docs/mapa_de_procesos.md`](docs/mapa_de_procesos.md).
- **El estado de cada proyecto se calcula con reglas de ejemplo** a partir de las fechas y montos que registran las entidades. No es una evaluación oficial.
- **Datos personales:** no se usan.
