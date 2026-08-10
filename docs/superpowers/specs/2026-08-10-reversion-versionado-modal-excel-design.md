# Reversión del versionado manual del modal de Excel

## Objetivo

Eliminar el parámetro manual de versión de `excel_modal.js` y conservar la URL
estática estándar del modal.

## Cambio

La inclusión del script volverá a usar exclusivamente la URL generada por
`{% static 'js/excel_modal.js' %}`. No se modificarán el JavaScript, las
dependencias ni el procesamiento de archivos Excel.

## Operación

Si un navegador conserva una copia antigua del recurso tras un cambio futuro,
se podrá actualizar con una recarga forzada (`Ctrl + F5`) o limpiando la caché.
