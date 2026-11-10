# Instrucciones para Claude Code en este proyecto

## Qué es

Proyecto final del curso Data Science con Python (Diplomatura Q-Lab PUCP), issue #204 de `d2cml-ai/Data-Science-Python`:
una startup con software funcionando. La app web traduce los datos abiertos de inversión pública del MEF a **cinco
preguntas en lenguaje simple** (¿qué es?, ¿qué problema resuelve?, ¿cuánto cuesta y cuánto se ha gastado?, ¿cuándo
termina?, ¿cómo va?) para quienes deciden o supervisan sin ser especialistas en Invierte.pe.

- **Usuario objetivo:** alta dirección, cooperantes, asesores, periodistas y ciudadanía. **No** es el especialista de la OPMI.
- **Alcance actual:** las 12 731 inversiones activas del gobierno nacional, con datos al 08/11/2026.

## Cómo correrlo

Desde la carpeta del proyecto:

```bash
uv run --with-requirements requirements.txt streamlit run app/app.py     # abre la app en http://localhost:8501
uv run --with-requirements requirements.txt python scripts/probar_app.py # prueba automática (debe dar 0 errores)
```

Sin `uv`, se puede usar `pip install -r requirements.txt` y después `streamlit run app/app.py`.

- Los archivos procesados vienen en `data/procesado/`, así que la app corre sin descargar nada.
- Para rehacer la base: `scripts/01_descargar.py` (baja ≈ 512 MB a `data/crudo/`, que no se sube), luego `03_preparar.py` y `04_traducir.py`.

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
