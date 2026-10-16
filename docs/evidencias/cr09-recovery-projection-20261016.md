# Corrección de recuperación: retirar proyección de publicación restaurada

**Defecto reproducido y corregido.** La proyección PublicationState contiene texto de búsqueda y fechas de publicación. La supresión ordinaria ya la retiraba, pero recovery_apply.apply_database conservaba la copia restaurada hasta un refresco posterior. El bloqueo HTTP de RECOVERY_MODE seguía activo: no se ha demostrado exposición pública. El defecto era la conservación de una copia que debía retirarse al reaplicar la finalidad publication.

Reproducción `20261016-000756-47bfe58b`:1FAIL/1PASS en56,47s. Falló la variante publication seleccionada; la variante excluida preservaba correctamente la copia. Fuentes congeladas y retirada independiente verificadas antes de corregir. Se conserva el fallo.

Corrección integrada `9f92f94`: elimina PublicationState del sujeto dentro de la misma transacción y rama publication de recuperación, antes de cualquier refresco. No elimina proyecciones de otros sujetos ni de finalidades excluidas. Sin migración, cache o nueva autorización. Los triggers/dirty markers y la reconciliación existente continúan su función.

[Verificación terminal](cr09-recovery-projection-terminal-20261016.json):run `20261016-000952-d23d1fae`,**9PASS120,27s;0FAIL/ERROR/SKIP**. Cubre dos variantes nuevas, controles de recovery_apply y pg_dump/pg_restore reales con medios sintéticos. El test de restauración exige ausencia de la proyección antes del refresco y reconstrucción ineligible sin texto ni fechas después. Incluye autoridad independiente/rollback rechazado, credenciales antiguas, preservación de terceros y replay. Las pruebas no aceptan custodia productiva, disponibilidad externa ni todo CR09/N3.

SHA al ejecutar8b6eb11, con cambio/test todavía sin commit incluidos en source-hashes originales; SHA exactos por archivo y casos en recibo. Commit posterior9f92f94 conserva esas fuentes. Python3.12.15, PostgreSQL17.11/Redis propios, límites existentes, sin datos reales ni servicios normales. Dependencias/Ruff/docs/Django/migraciones/nativos pasaron. Fuente congelada verificada independientemente, controlador/hijo ausentes, temporal del runner retirado y contenedores propios ausentes. La restauración también verifica y declara retirada de su base adicional antes de eliminar el contenedor; unidad exit0/MainPID0/ControlGroup vacío.

Este cambio afecta recuperación, no el recorrido normal de requests: no hay nuevo p95 ni mejora de rendimiento atribuida. Versión común/N3 y resto de criterios pendientes.
