# Conversación N.º 4 — Revisión de cómo se ordena la cartera (11/11/2026)

> Revisión de la versión publicada el 11/11/2026. Lo que sigue es un resumen del founder.

- **Fecha:** 11 de noviembre de 2026
- **Rol de la persona** (sin nombre): revisora externa de la app
- **Medio:** revisión de la app pública

## 1 y 2. Cómo lo hace hoy y qué le costó
- No se abordó: la revisión fue sobre la app.

## 3. Reacción a la versión 1
Para ordenar y analizar mejor, la app debería bajar nivel por nivel hasta la unidad ejecutora y, recién después, mostrar la inversión. Ejemplo:
1. **Nivel de gobierno:** Nacional
2. **Sector:** Salud
3. **Pliego:** Ministerio de Salud
4. **Unidad ejecutora:** el MINSA y las unidades ejecutoras que dependen de él

El MINSA es pliego, también es unidad ejecutora y, además, tiene unidades ejecutoras que dependen de él.

## Lo que verificamos después
- **Hoy la app pasa del sector a la unidad ejecutora y se salta el pliego.**
  - En Salud hay 3 pliegos que la app no distingue: Ministerio de Salud (1 207 inversiones), Instituto Nacional de Salud (15) e INEN (11).
  - En el gobierno nacional, 19 de los 33 sectores tienen más de un pliego.
- **Entre las unidades ejecutoras de inversiones del MINSA aparecen unidades de gobiernos regionales.** Por ejemplo, la sede central de la Región Apurímac figura con 89 inversiones.

## Lo que aprendí
- Quien trabaja en el Estado ubica una inversión por la **estructura presupuestal**: nivel de gobierno, sector, pliego y unidad ejecutora. El árbol de la app debe seguir ese orden, aunque el texto sea simple.

## Qué cambia en el producto
- **Por hacer:** agregar el pliego al árbol y a los filtros, con el orden sector → pliego → unidad ejecutora → inversión.
- **Siguiente versión:** el nivel de gobierno, cuando entren los gobiernos regionales y locales.
