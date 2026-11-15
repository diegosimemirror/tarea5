# Informe de exploración de los datos

Fecha: 10/11/2026 · Datos del MEF actualizados al 08/11/2026 · Salida completa del script en `exploracion_resultados.md`.

## 1. Fuentes

| Archivo (Datos Abiertos del MEF) | Qué es cada fila | Filas | Peso |
|---|---|---:|---:|
| `DETALLE_INVERSIONES.csv` | Una inversión activa del Banco de Inversiones | 150 641 | 248 MB |
| `INVERSIONES_BRECHAS.csv` | Una brecha que cierra una inversión (una inversión puede tener varias) | 505 452 | 100 MB |
| `FORMATO_12B.csv` | El último seguimiento de una inversión (incluye cerradas y desactivadas) | 227 566 | 189 MB |

- **Quién produce los datos:** el MEF, a partir de lo que registran las propias entidades en el Banco de Inversiones (Invierte.pe) y en el SIAF.
- **Cobertura:** todo el país y los tres niveles de gobierno. La primera versión usó solo el **gobierno nacional**: 12 731 inversiones, 33 sectores y 184 entidades. Desde el 14/11/2026 la app suma los **gobiernos regionales** (13 681 inversiones, misma estructura): 26 412 en total. Las cifras de las secciones 2 a 5 son del gobierno nacional.
- **Diccionario de variables:** el MEF lo publica en su portal, pero **los enlaces dan error 404**. El significado de cada columna se dedujo de su nombre y de los valores. Las dudas quedan marcadas abajo.
- **Suficiencia:** alcanza para responder qué es, qué brecha cierra, cuánto cuesta, cuándo termina y cómo va cada inversión. No alcanza para saber por qué se atrasa; para eso están los textos del 12-B, que la IA leerá.

## 2. Revisión de la base de gobierno nacional (12 731 inversiones)

| # | Qué se revisó | Qué se encontró | Qué propongo |
|---|---|---|---|
| 1 | Tamaño | 12 731 filas y 68 columnas | — |
| 3 | Tipos | **Todo viene como texto**, incluidos montos y fechas | Convertir a número y fecha (hecho en el Proceso 3) |
| 4 | Duplicados | 1 CUI repetido (2022788) en 2 filas que no son idénticas. Hay 11 inversiones antiguas (SNIP) sin CUI | Conservar ambas filas con identificadores distintos. Las 11 se identifican con su código SNIP |
| 5 | Faltantes | Vacías: avance físico en 7 681, beneficiarios en 6 435, descripción técnica en 6 430, fechas de ejecución en 1 296 | Dejar como están; la app muestra "sin dato" |
| 5b | Faltantes disfrazados | **Coordenadas en 0** (3 297) y otras fuera del Perú: 3 469 en total | Marcar como faltantes, sin borrar el valor original |
| 6 | Montos | Costo en 0 en 21 inversiones; **saldo negativo en 349** (se gastó más que el costo registrado) | Dejar y mostrar; el saldo negativo puede ser una pregunta de calidad del dato |
| 7 | Categorías | 12 tipos de inversión: IOARR (4 826), proyecto (3 233), PIP mayor SNIP (2 628), reconstrucción IRI (1 442), etc. | Traducir a 4 tipos simples |
| 8 | Escritura | Dos sectores con espacios dobles; "Pública Privada" escrito con y sin tilde | Corregir solo en la copia para mostrar |
| 8b | Codificación | **251 nombres con "¿" en lugar de un guion largo** (p. ej., "Marcona ¿ Andahuaylas") | Reemplazar por "–" solo en la copia para mostrar |
| 9 | Fechas | Fin de ejecución entre 2005 y 2047; 5 fechas después de 2040; **5 122 con el fin vencido** y sin informe de cierre | Ver la nota sobre "atrasado" más abajo |
| 10 | Atípicos | **17 avances físicos mayores a 100 %** (hasta 67 418 %) y **11 cifras de beneficiarios mayores a la población del Perú** (hasta 341 millones) | Marcar como faltantes, sin borrar el original |
| 10b | Montos muy grandes | Los mayores son reales: Ferrocarril Marcona–Andahuaylas (S/ 30,5 mil millones), Nueva Carretera Central (S/ 25,4 mil millones), Ferrocarril Lima–Ica (S/ 24,5 mil millones), Línea 3 del Metro (S/ 23,6 mil millones) | Dejar. Explican por qué Transportes suma S/ 286 mil millones |

**Nota sobre "atrasado".** Que la fecha de fin haya pasado no siempre significa atraso: muchas obras terminaron y solo falta cerrarlas. Por eso la app separa las dos cosas:
- **Atrasado:** la fecha pasó y el avance es menor a 95 %. Son 3 380.
- **Por cerrar:** el avance es de 95 % o más. Son 2 978.

## 3. Base de brechas

- **Cobertura:** 10 046 de las 12 731 inversiones del gobierno nacional tienen al menos una brecha.
- **Varias brechas por inversión:** la mayoría tiene una o dos, pero una llega a 269. La app usa la primera e informa cuántas tiene.
- **El tamaño de la brecha en el territorio (`VALOR`) casi nunca está registrado:** solo 1 645 de 505 452 filas, y 412 de ellas superan 100, así que no son porcentajes. **No se usa** hasta aclarar su significado.
- **El aporte del proyecto (`CONTRIBUCION`) sí está casi siempre.** Su unidad varía: personas, km, locales, etc. Se muestra con su unidad.

## 4. Formato 12-B (seguimiento)

- **Cobertura:** 9 373 inversiones del gobierno nacional tienen fila en el 12-B, y 9 112 tienen la fecha de su última actualización. Ningún CUI está repetido.
- **Textos:** hay situación en 8 912, problemas en 8 249 y acciones en 8 250. Cada uno empieza con su fecha entre corchetes, que se separa del texto.
- **Muchos textos dicen "no hay problemas" o son muy breves.** Es una limitación para la IA, no un error.

## 5. Decisiones de preprocesamiento (aplicadas)

Ninguna fila se eliminó: el gobierno nacional entra completo, con sus 12 731 inversiones.

| Decisión | Registros afectados | Reversible |
|---|---:|---|
| Filtrar el gobierno nacional (los niveles regional y local quedan para después) | 137 910 fuera de esta versión | Sí: cambiar el filtro |
| Avance físico mayor a 100 % → faltante | 17 | Sí: se conserva `avance_fisico_original` |
| Beneficiarios mayores a 35 millones → faltante | 11 | Sí: `beneficiarios_original` |
| Coordenadas fuera del Perú o en 0 → faltante | 3 469 | Sí: `lat_original` y `lon_original` |
| "¿" → "–" en nombres; espacios dobles; "Pública" con tilde | 251 nombres, 2 sectores y la modalidad APP | Sí: solo afecta la copia para mostrar |
| Usar solo la primera brecha de cada inversión | 10 046 inversiones (se guarda `n_brechas`) | Sí |
| Datos personales en los textos del 12-B: nombres con título (Ing., Lic., …) → "[nombre omitido]"; correos electrónicos → "[correo omitido]" | 14 textos con nombres y 2 con correos | Sí: el texto original sigue en `data/crudo/` |

## 6. Pendientes

- Confirmar con el MEF o con la normativa el significado de `VALOR`, `CONTRIBUCION` y `AVANCE_EJECUCION`.
- **Validar las reglas del estado** (umbrales de 95 %, 50 % y 180 días). Son reglas de ejemplo.
- ~~Extender el análisis a los gobiernos regionales~~: hecho el 14/11/2026 (13 681 inversiones).

## 7. Obras paralizadas de la Contraloría (Proceso 8, 14/11/2026)

**Fuente:** Contraloría General de la República, "Informe de obras paralizadas en el territorio nacional a junio de 2026", Anexo N.° 01 (Excel publicado en gob.pe, 0,7 MB). Corte al 30/06/2026. Cada fila es una **obra**, no una inversión: una inversión puede tener varias obras.

| # | Qué se revisó | Qué se encontró | Qué se hizo |
|---|---|---|---|
| 1 | Tamaño | 2 262 obras y 38 columnas, en una sola hoja ("Data") | — |
| 3 | Tipos | Todo se lee como texto; los nombres de columna traen una nota en una segunda línea | Avance físico y año de inicio a número; nombres de columna solo con su primera línea |
| 4 | Duplicados | Ninguna fila repetida ni código INFOBRAS repetido. 177 CUI aparecen más de una vez: son varias obras de una misma inversión (y los CUI en 0) | Se conservan todas; la ficha lista cada obra |
| 5 | Faltantes | Avance físico vacío en 54; plazo en 57; las 9 columnas del inventario del MEF (informe situacional, lista priorizada…) vacías en 1 529 | Se dejan vacíos; esas 9 columnas no se usan |
| 5b | Faltantes disfrazados | **CUI = "0" en 134 obras** (sin código de inversión); "URL" con solo un espacio | Las 134 no se pueden unir con un proyecto y quedan fuera del cruce |
| 7 | Categorías | Nivel: 1 543 locales, 396 nacionales y 323 regionales. 16 causas; las más comunes: falta de recursos (625), incumplimiento de contrato (592), arbitraje (185), deficiencia en el expediente técnico (164) | — |
| 8 | Escritura | "9 EVENTOS CLIMÁTICOS" aparece también con un espacio al final (7 obras); las causas llevan su número de código | Se quitan espacios y número: quedan 15 causas, escritas en minúsculas normales |
| 10 | Atípicos | Avance físico entre 0 y 100 %, ninguno fuera de rango; año de inicio entre 2007 y 2026 | — |

**Cruce con nuestra base (por el CUI):** 551 obras pertenecen a **519 proyectos** (340 obras del gobierno nacional y 211 de los gobiernos regionales). Otras 179 obras nacionales o regionales tienen un CUI que no está entre las inversiones activas (probablemente cerradas o desactivadas) y no se muestran.

**El nivel de gobierno no siempre coincide:** 32 obras que la Contraloría registra como locales son de proyectos que el MEF registra como nacionales (25) o regionales (7), y 29 cambian entre nacional y regional. Se respeta el nivel del MEF, porque el cruce es por el código del proyecto.

**El estado de la app y la Contraloría miden cosas distintas:** de los 519 proyectos con obras paralizadas, 175 figuran "En marcha" con las reglas de la app, que solo usan fechas y montos del MEF. Por eso la ficha muestra la información de la Contraloría en un recuadro aparte, con su fuente y su fecha, sin cambiar el estado.

**Ningún dato se modificó ni se eliminó:** el anexo se guarda tal cual en `data/contraloria/`.
