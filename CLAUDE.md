# Instrucciones para Claude Code en este proyecto

## Qué es

Proyecto final del curso Data Science con Python (Diplomatura Q-Lab PUCP), issue #204 de `d2cml-ai/Data-Science-Python`:
una startup con software funcionando. La app web traduce los datos abiertos de inversión pública del MEF a **cinco
preguntas en lenguaje simple** (¿qué es?, ¿qué problema resuelve?, ¿cuánto cuesta y cuánto se ha gastado?, ¿cuándo
termina?, ¿cómo va?) para quienes deciden o supervisan sin ser especialistas en Invierte.pe.

- **Usuario objetivo:** alta dirección, cooperantes, asesores, periodistas y ciudadanía. **No** es el especialista de la OPMI.
- **Alcance actual:** las 26 250 inversiones activas del gobierno nacional (12 695) y de los gobiernos regionales (13 555), con datos al 20/11/2026 (las fechas están en `data/procesado/fechas.json`), más las obras paralizadas de la Contraloría (corte al 30/06/2026; `scripts/08_contraloria.py`).

## Cómo correrlo

Desde la carpeta del proyecto:

```bash
uv run --with-requirements requirements.txt streamlit run app/app.py     # abre la app en http://localhost:8501
uv run --with-requirements requirements.txt python scripts/probar_app.py # prueba automática (debe dar 0 errores)
```

Sin `uv`, se puede usar `pip install -r requirements.txt` y después `streamlit run app/app.py`.

- Los archivos procesados vienen en `data/procesado/`, así que la app corre sin descargar nada.
- Para rehacer la base, en este orden: 1 → 11 → 3 → 9 → 10 → 4 → 7 → 8.
  - `01_descargar.py` baja ≈ 537 MB a `data/crudo/` (no se sube) y anota la fecha en `fechas.json`.
  - `11_12b_en_vivo.py` consulta el 12-B de EsSalud en vivo (≈ 16 min).
  - `03_preparar.py` arma la base. Si el MEF publica el 12-B vacío, usa `respaldo_12b.parquet`.
  - `09_gasto_empresas.py` trae el gasto de EsSalud y FONAFE, que no usan el SIAF (≈ 20 min).
  - `10_fases_componentes.py` decide si ya se ejecutó, los componentes, la fase y la prioridad del MEF.
  - Después: `04_traducir.py`, `07_indicadores.py` y `08_contraloria.py`.
- **pandas:** los procesados se generan con pandas 2.x (`uv run --with "pandas<3" --with pyarrow python scripts/…`). Con pandas 3, las expresiones regulares del Proceso 7 usan otro motor y 53 textos del 12-B cambian de clase de problema.
- **Empresas públicas:** EsSalud y FONAFE no registran su gasto en el SIAF. Su gasto viene de su reporte a FONAFE (Proceso 9); si no hay reporte, la ejecución es «sin dato», nunca 0 %.
- **Ya ejecutadas:** no basta el porcentaje del 12-B. El Proceso 10 lee su texto; por ejemplo, 308 inversiones de EsSalud de la pandemia tienen 0 % y su texto dice «ejecutadas». Las ya ejecutadas se ocultan en la app (interruptor) porque no necesitan financiamiento. Toda regla nueva se revisa leyendo los textos distintos que clasifica.
- **Memoria de la app:** la tabla principal se comparte entre todos los visitantes (`st.cache_resource`), así que la app nunca debe modificarla: solo filtrarla o armar tablas nuevas. Las columnas que la página no usa van en `NO_SE_USAN` (`app/app.py`) y no se cargan. Si la app empieza a usar una, hay que sacarla de esa lista. Antes (`st.cache_data`) se copiaban ≈ 107 MB en cada clic y la página se caía en el plan gratuito de Streamlit.
- **Prioridad del MEF:** el orden de prelación de la Directiva 001-2019-EF/63.01, art. 15.2 (9 grupos). «Ejecutabilidad» no es un término de esa norma.

## Dónde está cada cosa

- `docs/mapa_de_procesos.md`: el mapa insumo → método → resultado. Los scripts llevan su misma numeración. **Si el código cambia, actualiza el mapa.**
- `docs/informe_exploracion.md`: los hallazgos y las decisiones de limpieza, con cuántos registros afectó cada una.
- `scripts/06_ia.py`: la redacción con un LLM con salida JSON (OpenAI, DeepSeek o Gemini). La clave va en `.env`, que nunca se sube.
- `README.md`: las 9 partes que pide el curso. Las marcadas **POR COMPLETAR** las escribe el founder.

## Reglas

1. **Lenguaje simple en la vista principal.** Siglas y términos del MEF (PIM, devengado, UEI, OPMI, 12-B…) solo en el desplegable "Para especialistas". El founder rechazó un diseño anterior por tener demasiada información y seguir la jerga de Invierte.pe.
2. **Sin datos personales.**
   - Los nombres de personas en los textos del 12-B se reemplazan por "[nombre omitido]" (Proceso 3).
   - Un contratista que sea persona natural se muestra como "Persona natural (nombre omitido)".
   - Verifica que siga así después de cada cambio.
3. **Sin claves ni datos crudos en el repositorio.** `.env` y `data/crudo/` están en `.gitignore`.
4. **No copiar textos de libros con licencia** (por ejemplo, guías del PMI) al repositorio ni a la app.
5. **Commit y push solo cuando el founder lo pida.**
6. **Estilo de código:**
   - un título `# PROCESO N:` con su insumo y su resultado;
   - un comentario de para qué sirve cada paquete;
   - una explicación de qué cambio produce cada función (antes → después);
   - nombres en español y una verificación después de cada proceso.
7. **No eliminar ni modificar datos** sin decir antes cuántos registros se afectan y por qué.
8. **Responder en español** y explicar cada término técnico la primera vez.
