# Plan: Segmentacion de Preguntas por Dificultad

**Objetivo:** Que cada estudiante reciba una distribucion equilibrada de preguntas (X faciles, Y medianas, Z dificiles) seleccionadas aleatoriamente dentro de cada bucket, garantizando equidad en la dificultad del examen.

---

## Arquitectura Actual

```
Evaluacion
├── preguntas_a_mostrar = 10   ← total de preguntas que ve el estudiante
├── preguntas (FK inversa)     ← pool completo de preguntas
│   └── cada Pregunta tiene: categoria (FK), puntos, texto, 4 opciones
└── get_preguntas_para_estudiante(participante_id, intento)
    → selecciona N preguntas random del pool total (seed determinístico MD5)
```

**Problema:** Un estudiante puede recibir pura pregunta difícil y otro pura fácil, aun con seed determinístico.

---

## Arquitectura Propuesta

```
Evaluacion
├── preguntas_a_mostrar = 10        ← TOTAL (calculado = suma de los 3)
├── preguntas_faciles = 4           ← cuántas fáciles mostrar
├── preguntas_medianas = 3          ← cuántas medianas mostrar
├── preguntas_dificiles = 3         ← cuántas difíciles mostrar
├── preguntas (FK inversa)
│   └── cada Pregunta ahora tiene:
│       categoria (FK), dificultad (1/2/3), puntos, texto, 4 opciones
└── get_preguntas_para_estudiante(participante_id, intento)
    → 4 del bucket FACIL + 3 del bucket MEDIA + 3 del bucket DIFICIL
    → seed determinístico por bucket, mezcla final aleatoria
```

---

## Fases de Implementacion

### Fase 1: Modelo `Pregunta` — nuevo campo `dificultad`

**Archivo:** `matholymp/quizzes/models.py:818`

```python
class DificultadChoices(models.IntegerChoices):
    FACIL = 1, 'Facil'
    MEDIA = 2, 'Media'
    DIFICIL = 3, 'Dificil'

# Dentro de class Pregunta:
dificultad = models.PositiveSmallIntegerField(
    choices=DificultadChoices.choices,
    default=DificultadChoices.FACIL,
    help_text='Nivel de dificultad de la pregunta'
)
```

---

### Fase 2: Modelo `Evaluacion` — 3 nuevos campos

**Archivo:** `matholymp/quizzes/models.py:416`

```python
preguntas_faciles = models.PositiveIntegerField(
    default=4, help_text='Cantidad de preguntas faciles a mostrar'
)
preguntas_medianas = models.PositiveIntegerField(
    default=3, help_text='Cantidad de preguntas medias a mostrar'
)
preguntas_dificiles = models.PositiveIntegerField(
    default=3, help_text='Cantidad de preguntas dificiles a mostrar'
)
```

**Validacion en `clean()`:** Auto-ajustar `preguntas_a_mostrar = preguntas_faciles + preguntas_medianas + preguntas_dificiles` si no coinciden.

---

### Fase 3: Modificar `get_preguntas_para_estudiante()` — METODO CRITICO

**Archivo:** `matholymp/quizzes/models.py:757-782`

```python
def get_preguntas_para_estudiante(self, participante_id, numero_intento=1):
    import hashlib, random

    hash_base = f"{self.id}_{participante_id}_{numero_intento}"
    hash_participante = hashlib.md5(hash_base.encode()).hexdigest()
    seed = int(hash_participante[:8], 16)
    random.seed(seed)

    buckets = [
        (DificultadChoices.FACIL, self.preguntas_faciles),
        (DificultadChoices.MEDIA, self.preguntas_medianas),
        (DificultadChoices.DIFICIL, self.preguntas_dificiles),
    ]

    seleccionadas = []
    for dificultad, cantidad in buckets:
        pool = list(
            self.preguntas.filter(dificultad=dificultad)
            .prefetch_related('opciones')
            .order_by('id')
        )
        n = min(cantidad, len(pool))
        if n > 0:
            seleccionadas.extend(random.sample(pool, n))

    random.shuffle(seleccionadas)
    return seleccionadas
```

**Tambien actualizar `get_preguntas_aleatorias()`** (linea 744) con la misma logica.

---

### Fase 4: Vistas de creacion/edicion de evaluacion

**Archivos:** `matholymp/quizzes/views.py`

| Vista | Linea | Cambio |
|-------|-------|--------|
| `create_evaluacion` | 2080 | Recibir `preguntas_faciles`, `preguntas_medianas`, `preguntas_dificiles` del JSON. Calcular `preguntas_a_mostrar = suma`. Validar >= 0. |
| `editar_evaluacion` | 2560 | Mismo cambio. Si no se envian (backward compat), usar defaults (4, 3, 3). |

---

### Fase 5: Actualizar `save_question` y `update_question`

**Archivo:** `matholymp/quizzes/views.py`

| Vista | Linea | Cambio |
|-------|-------|--------|
| `save_question` | 2211 | Recibir `dificultad` del JSON, validar en [1,2,3], pasar a `Pregunta.objects.create()` |
| `update_question` | 2419 | Recibir `dificultad` y actualizar el campo |

---

### Fase 6: Templates Admin

| Template | Cambio |
|----------|--------|
| `templates/quizzes/manage_questions.html` | Modal crear/editar pregunta: agregar `<select>` de dificultad |
| `templates/quizzes/edit_evaluacion.html` | Agregar 3 campos numericos: faciles, medias, dificiles |
| `templates/quizzes/view_evaluacion.html` | Mostrar distribucion: "10 preguntas: 4F / 3M / 3D" |
| `templates/quizzes/manage_quizs.html` | Mostrar distribucion en la tabla de evaluaciones |
| `templates/quizzes/evaluacion_results.html` | (Opcional) Agrupar resultados por dificultad en analiticas |

---

### Fase 7: Migraciones

1. **0031** — `AddField dificultad` a `Pregunta` (default=FACIL)
2. **0032** — `AddField preguntas_faciles/medianas/dificiles` a `Evaluacion` + data migration para setear defaults en evaluaciones existentes

---

### Fase 8: Seed Scripts

Actualizar management commands:

| Archivo | Linea | Cambio |
|---------|-------|--------|
| `2_crear_evaluacion_etapa1.py` | 51 | Agregar `preguntas_faciles=4, preguntas_medianas=3, preguntas_dificiles=3` |
| `crear_evaluacion_etapa1.py` | 213, 328, 442 | Mismo cambio en las 3 evaluaciones |
| `validar_cambio_cantidad_etapas.py` | 73 | Mismo cambio |
| Preguntas creadas en seeds | — | Distribuir `dificultad` aleatoriamente o en lotes |

---

## Resumen Visual: Experiencia del Estudiante

```
ANTES (injusto):
"10 preguntas aleatorias" — pool unico sin segmentar

Estudiante A: podria recibir 8 dificiles + 2 faciles  → desventaja
Estudiante B: podria recibir 8 faciles + 2 dificiles  → ventaja


AHORA (equitativo):
"10 preguntas: 4 faciles + 3 medias + 3 dificiles" — mezcladas aleatoriamente

Estudiante A: [Q2(F), Q5(M), Q8(D), Q1(F), Q3(M), Q9(D), Q4(F), Q7(M), Q10(D), Q6(F)]
Estudiante B: [Q7(F), Q1(M), Q3(D), Q6(F), Q9(M), Q2(D), Q5(F), Q8(M), Q4(D), Q10(F)]
                  ↑ misma distribucion 4F/3M/3D, diferentes preguntas concretas
```

---

## Orden de Ejecucion Recomendado

| # | Tarea | Impacto |
|---|-------|---------|
| 1 | Agregar `DificultadChoices` + campo `dificultad` en `Pregunta` + migracion | Modelo |
| 2 | Agregar 3 campos en `Evaluacion` + migracion + data migration | Modelo |
| 3 | Modificar `get_preguntas_para_estudiante()` y `get_preguntas_aleatorias()` | Logica core |
| 4 | Actualizar `save_question` / `update_question` | Backend |
| 5 | Actualizar `create_evaluacion` / `editar_evaluacion` | Backend |
| 6 | Actualizar templates admin | Frontend |
| 7 | Actualizar seed scripts | Datos de prueba |
| 8 | Probar con `python manage.py test` | QA |
