# Correctivas de regresión pendientes de verificación

Base: b0d2af0aed0bb0a353b943b8e081d25aba472271. Worktree aislado: web_modelos_cr09_regression_correctives.

Se prepara la resolución de MAX_FILES al invocar _check o construir ArchiveSink. Se mantienen la validación 1..256, el máximo predeterminado 100, los límites explícitos y la reserva de report.json. Motivación: tres fallos reales del bloque 1 por captura del valor al importar.

El control AST de capacity_paths compara primero la función cargada completa con HEAD. Después reconstruye independientemente desde HEAD el único cambio del baseline y compara su objeto de código completo con original_compiler. Normaliza las líneas para equiparar inspect.getsource con el archivo completo. Motivación: el control anterior comparaba el baseline deliberadamente reconstruido con el HEAD optimizado.

Estado: borrador, sin ejecución de pruebas ni integración. git diff --check pasa; no demuestra comportamiento correcto. La regresión del worktree de integración continúa sin cambios. Pendiente reproducir el fallo reading_common production y ejecutar las correctivas con PostgreSQL real cuando termine la carga de regresión.

Diagnóstico adicional: rules_version estaba memorizada sin argumentos aunque incluía PRODUCTION, VERIFICATION_PROVIDER y SECRET_KEY. Se prepara un wrapper cuya caché usa estos valores como clave, conservando cache_clear para invalidar fuentes. Tres pruebas nuevas cubren cambio/restauración de configuración sin vaciado manual. Esto es hipótesis estática del fallo production, aún sin reproducción PostgreSQL. Los cuatro archivos editados pasan análisis sintáctico y diff --check; pruebas funcionales pendientes.

Revisión del borrador: la normalización de líneas AST precede al reemplazo para conservar las ubicaciones del baseline generado. Añadidos controles de límites explícitos frente a cambios del predeterminado y rechazo de valores 0, 257, booleano y cadena. Cinco archivos pasan análisis sintáctico y diff --check; ninguna prueba funcional ejecutada todavía.

Bloque 2 terminal: un fallo AST adicional en test_capacity_revision_equivalence. El baseline limita defer a search_document mientras HEAD ya difiere campos adicionales. Se prepara comparación completa del código cargado con HEAD, seguida de reconstrucción independiente del único defer de referencia. Se conserva la prueba real de igualdad de salida, SQL y filas. Pendiente verificación; no integrado.
