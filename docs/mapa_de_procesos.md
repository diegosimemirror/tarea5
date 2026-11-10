# Mapa de procesos

El código sigue esta numeración: cada script empieza con el número de su proceso.

| N.º | Proceso | Insumo | Método | Resultado | Archivo |
|---|---|---|---|---|---|
| 1 | Descargar | Portal de Datos Abiertos del MEF | Descarga de 3 archivos públicos | `data/crudo/*.csv` (≈ 537 MB, no se suben a GitHub) | `scripts/01_descargar.py` |
| 2 | Explorar | Los 3 archivos crudos | La lista de revisión: tamaño, tipos, duplicados, faltantes, atípicos | `docs/exploracion_resultados.md` e `informe_exploracion.md` | `scripts/02_explorar.py` |
| 3 | Preparar | Archivos crudos | Filtrar el gobierno nacional, convertir tipos, marcar valores imposibles, unir brecha y 12-B | `data/procesado/gobierno_nacional.parquet` (12 731 × 49) | `scripts/03_preparar.py` |
| 4 | Traducir | Base preparada | Reglas en lenguaje simple: ¿qué es?, ¿qué problema resuelve?, ¿cuánto?, ¿cuándo?, ¿cómo va? | `data/procesado/cinco_preguntas.parquet` | `scripts/04_traducir.py` |
| 5 | Mostrar | Las cinco preguntas | App web en Streamlit: ministerio → árbol → proyectos → ficha | Página web | `app/app.py` |
| 6 | Redactar con IA *(código listo; falta la clave en `.env`)* | Nombre, descripción técnica, brecha y textos del 12-B | LLM con salida estructurada en JSON: ¿qué es?, ¿qué problema resuelve? y ¿qué lo frena?, solo con los datos dados | `data/procesado/ia_respuestas.parquet`, que la app usa si existe | `scripts/06_ia.py` |
| — | Probar | `app/app.py` | Prueba automática: carga, clic en "Ver ficha" y cambio de ministerio | Errores encontrados (hoy: 0) | `scripts/probar_app.py` |

```mermaid
flowchart LR
  A[MEF · Datos Abiertos] -->|1 Descargar| B[(data/crudo)]
  B -->|2 Explorar| C[Informe de exploración]
  B -->|3 Preparar| D[(gobierno_nacional.parquet)]
  D -->|4 Traducir con reglas| E[(cinco_preguntas.parquet)]
  E -.->|6 IA, pendiente| E
  E -->|5 Mostrar| F[App web en Streamlit]
```
