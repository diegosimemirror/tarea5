# Conversación N.º 3 — Un especialista en inversión pública revisa la app (11/11/2026)

> Revisión de la versión publicada el 11/11/2026. No hay frases textuales; lo que sigue es un resumen del founder.

- **Fecha:** 11 de noviembre de 2026
- **Rol de la persona** (sin nombre): especialista en inversión pública
- **Medio:** conversación con el founder, después de usar la app pública

## 1 y 2. Cómo lo hace hoy y qué le costó
- No se abordó: la conversación fue sobre la app.

## 3. Reacción a la versión 1

**Palabras que pide cambiar o aclarar**
- **"Cuestan en total"** (sobre la lista de proyectos): el término correcto es **costo total**.
- **"Con programación desde 2027"** (tarjeta "¿Tienen financiamiento?"): no queda claro qué significa.
- **"Con costo duplicado o más"** (tarjeta "¿Cuánto cambiaron los costos?"): no queda claro si se refiere a un alza de más de 100 %.
- **"Expediente técnico"** (tarjeta "¿Qué problemas reportan?"): no se sabe si el problema es un expediente técnico vencido o su calidad.

**Uso**
- La herramienta debería ser más amigable e intuitiva.
- **La búsqueda falla en casos concretos.** Buscó el hospital de Chupaca y el hospital Antonio Lorena y no los encontró; incluso apareció un proyecto de otra región.

## Lo que verificamos después
- **Los dos hospitales no son del gobierno nacional**, y esta versión solo tiene el gobierno nacional:
  - el de Chupaca (establecimiento de salud Pedro Sánchez Meza, CUI 2337618, S/ 166 millones) lo ejecuta el Gobierno Regional de Junín;
  - el Antonio Lorena (CUI 2094808, S/ 1 433 millones), el Gobierno Regional del Cusco.

  Cuando la búsqueda no encuentra nada, la app no explica que puede ser una obra regional o local.
- **La "otra región":** al buscar "Chupaca" aparece un proyecto del MINSA en el puesto de salud Chupaca, en Paucartambo (Pasco) (CUI 2477003).
- **La búsqueda solo lee el título y el lugar, no el nombre oficial, y distingue tildes.** De los 21 proyectos nacionales con "Chupaca" en su nombre oficial encuentra 10; "Pedro Sanchez" no encuentra "Sánchez"; y "hospital de Chupaca" solo funciona si esas palabras aparecen juntas.
- **"Costo duplicado o más"** cuenta los proyectos cuyo costo subió más de 100 % desde que se aprobaron.
- **"Programación desde 2027"** agrupa los proyectos sin presupuesto 2026 ni programación para 2026, que tienen montos programados para 2027 en adelante en la programación multianual de inversiones (PMI).
- **"Expediente técnico"** se marca cuando el último reporte de seguimiento (Formato 12-B) menciona el expediente técnico o los estudios. Es una búsqueda por palabras clave: no distingue si el expediente está vencido, en elaboración o tiene deficiencias.

## Lo que aprendí
- El lenguaje simple no debe cambiar los términos que el especialista ya conoce, como **costo total**. Lo que hace falta es explicar las etiquetas cortas.
- Las personas buscan una obra **por el nombre con que la conocen** ("hospital de Chupaca"), no por el nombre oficial, y no saben qué nivel de gobierno la ejecuta. Esto confirma que el siguiente paso son los gobiernos regionales y locales.

## Qué cambia en el producto
- **Hecho el mismo 11/11/2026:**
  - "Cuestan en total" pasó a **"Costo total"**.
  - Las etiquetas dicen lo que miden:
    - "con alza de más de 100 % (más del doble)";
    - "sin presupuesto 2026, programados para 2027 o después";
    - "expediente técnico o estudios", con una nota que aclara que no distingue si el expediente está vencido, en elaboración o tiene deficiencias.

    Las mismas definiciones están en "¿Cómo se calculan el estado y los indicadores?".
  - **La búsqueda** ahora:
    - lee también el nombre oficial y la unidad ejecutora;
    - no distingue tildes ni mayúsculas;
    - busca palabra por palabra.

    Si no encuentra nada, dice dónde sí está (otra unidad, otro estado u otro ministerio) o avisa que esta versión solo tiene el gobierno nacional. "Bernales" pasa de 4 a 9 proyectos en Salud; "hospital de Chupaca" muestra el aviso.
- **Por hacer:** hacer la herramienta más amigable e intuitiva, con más pruebas de uso.
- **Siguiente versión:** gobiernos regionales y locales (ya figura en "Qué sigue" del README).
