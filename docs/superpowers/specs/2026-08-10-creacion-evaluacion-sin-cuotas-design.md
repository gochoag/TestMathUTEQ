# Creación de evaluaciones sin cuotas iniciales

## Objetivo

Corregir el error de JavaScript que bloquea la creación de evaluaciones al
referenciar `cuotas_unidades`, una variable que ya no forma parte del modal de
creación.

## Comportamiento

Una evaluación nueva se creará sin cuotas por unidad y conservará
`preguntas_a_mostrar = NULL`. La interfaz mostrará el estado "Sin configurar".
Las cuotas y el total de preguntas se configurarán posteriormente desde
Gestionar preguntas, que es el único flujo responsable de enviarlas y
guardarlas.

## Cambio acotado

En `matholymp/static/js/manage_quizs.js`, `createQuiz()` dejará de incluir
`cuotas_unidades` en el cuerpo JSON enviado al endpoint de creación. El
endpoint dejará de crear cuotas predeterminadas cuando esa clave no llegue en
la solicitud. No se modificarán modelos, migraciones ni el formulario de
cuotas.

## Validación

Se comprobará que el archivo no contenga referencias ejecutables a
`cuotas_unidades` en `createQuiz()`, que el JavaScript sea sintácticamente
válido y que el endpoint no cree `EvaluacionCuotaUnidad` cuando se genere una
evaluación nueva sin cuotas.
