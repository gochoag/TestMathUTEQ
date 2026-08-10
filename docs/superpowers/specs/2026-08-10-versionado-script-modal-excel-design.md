# Versionado del script del modal de Excel

## Objetivo

Evitar que el navegador ejecute una versión antigua de `excel_modal.js` que
referencia `XLSX`, aunque el código actual procesa el archivo en el servidor
con `openpyxl` y no usa esa librería.

## Cambio

El template del modal añadirá un parámetro de versión explícito a la URL de
`excel_modal.js`. El navegador tratará la URL como un recurso nuevo y cargará
el script vigente. No se añadirá SheetJS ni se modificarán los endpoints de
importación.

## Mantenimiento y validación

La versión se incrementará en futuras modificaciones del script. Se verificará
que el template conserve una única inclusión del script y que el archivo no
contenga referencias a `XLSX`.
