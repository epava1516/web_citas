# Supresión y limitación: comprobación aplicable al producto actual

Run `20261015-234759-542fcdbb`, SHA `790f26c` completo en [recibo terminal y aserciones](cr09-current-erasure-processing-terminal-20261015.json), producto integrado3ba2ec4. **11 PASS132,71s;0FAIL/ERROR/SKIP**. PostgreSQL17.11 y Redis propios, Python3.12.15, kernel canónico native-sealed comprobado antes de lanzamiento, dependencias congeladas, límites habituales sin modificación. No producción, datos reales ni perfiladores.

Motivo de reapertura concreta: `apps/safety/erasure_execution.py` y recorrido de publicaciones cambiaron desde la regresión común8fb4cf1. Las pruebas antiguas se conservan; esta selección comprueba comportamientos afectados sobre fuentes actuales, sin repetir restauración/urgencia cerradas por rutina.

| Archivo | Alcance inspeccionado | Casos PASS |
| --- | --- | ---: |
| test_account_erasure_execution.py | Cuenta propia: preservación de evidencias/canal; rechazo de ámbito editorial, revisión ausente, versión caducada y producción | 3 |
| test_media_erasure.py | Retirada durable de archivos/huellas, sujeto ajeno, fallo parcial/reintento, procesamiento concurrente y ruta compartida | 5 |
| test_processing_execution.py | Limitación de uso conservando preferencias/derechos; rechazo de finalidad no soportada y borrado de preferencias restringidas | 3 |

Los tres casos de cuenta incluyen parametrización; las funciones/aserciones y los casos JUnit exactos están en recibo. Un assert listado es evidencia de la comprobación ejecutada, no prueba de completitud del derecho ni de todos los helpers/transitivas. No nueva funcionalidad ni conclusión sobre conformidad jurídica integral.

Runner también pasó dependencias/Ruff/docs/Django/migraciones/herramientas nativas. Verificación independiente:source-hashes inicial igual a fuentes terminales;controlador/hijo ausentes;temporal retirado;ambos contenedorespropios ausentes;unidad exit0/MainPID0/ControlGroupvacío. Recibo conserva hashes deJUnit/result/source.

Pendientes mantenidos: matriz de finalidad/excepción/política porrecurso y scheduling de todaslaspurgas; cobertura derechos/comunicaciones/históricos necesaria; rendimiento directorio; N3 versión común. La aceptación provisional deexportaciones no se altera. No afirmar CR09cerrado ni rendimiento mejorado.
