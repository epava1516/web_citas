# CR09: conciliación de mecanismos sobre la regresión integrada

Se verificaron los journals terminales v3 de `8fb4cf1` y la huella exacta de cada archivo de test con las fuentes actuales. No se lanzaron pruebas nuevas. El cambio posterior `3708aa8` afecta únicamente al test de navegación documentado por separado.

| Alcance seleccionado | Archivos | Llamadas PASS | Fallos/omisiones de la selección |
|---|---:|---:|---:|
| Conservación | 7 | 20 | 0 |
| Comunicaciones | 6 | 27 | 0 |
| Restauración real PG/medios | 1 | 1 | 0 |
| Urgencias y revocación | 1 | 14 | 0 |

[Reports y aserciones por archivo](cr09-mecanismos-conciliacion-integrada-20261015.json). Estos resultados sustituyen la espera de ejecución integrada de esas selecciones en las auditorías anteriores; no sustituyen la revisión de completitud del criterio ni convierten las baterías originales negativas en PASS.

Pendientes concretos: correspondencia de excepciones/finalidades/backups y tareas de purga; matriz de destinatarios/canales por derecho; fuentes históricas necesarias con asociación no demostrada; criterio de carga del directorio y N3 completo. El enlace refresh Beat→worker ya verificado no acredita el scheduling de todas las tareas de purga. No repetir simulacro de urgencias/restauración por rutina.

La recepción externa, identidad real, custodia y operación humanas no se deducen del escenario sintético. Los pesos y la aceptación provisional MOD09 permanecen intactos; CR09 sigue abierto.
