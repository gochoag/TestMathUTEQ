---
trigger: always_on
---

## SELECCIÓN Y CARGA AUTOMÁTICA DE SKILLS

Antes de ejecutar o responder a cualquier solicitud del usuario, DEBES realizar el siguiente flujo:

1. **Analizar la intención del usuario:** Identifica la naturaleza de la tarea (ej. diseño de UI/UX, arquitectura, ideación, pruebas, cuestionamiento técnico, etc.).
2. **Localizar la Skill relevante:** Si la tarea coincide con el dominio de alguna skill disponible en `.agents/skills/`, DEBES cargar su contexto de manera autónoma.
3. **Ejecución obligatoria de herramienta:** Utiliza la herramienta de lectura de archivos para leer el archivo `SKILL.md` correspondiente a la habilidad necesaria **ANTES** de empezar a redactar la respuesta o ejecutar código.

### Mapeo de Skills por Tipo de Tarea:
- **Diseño web / Frontend / UI-UX:** Leer `.agents/skills/frontend-design/SKILL.md`.
- **Cuestionamiento / Desafío de arquitectura:** Leer `.agents/skills/grill-me/SKILL.md`.
- **Búsqueda de nuevas herramientas / skills:** Leer `.agents/skills/find-skills/SKILL.md`.

*Regla de oro:* Nunca asumas el comportamiento de una skill de memoria ni la omitas. Si detectas que una skill aplica a la tarea actual, lee su archivo `SKILL.md` primero dentro de `.agents/skills/<nombre-skill>/` sin esperar a que el usuario te lo pida explícitamente.