# Nueva medida durante una supresión pendiente

Fecha: 2026-10-05. Estado: verificación local parcial. Complementa docs62–64; CR-09 y contrato completo abiertos. Fuente funcional/runtime0072 sin cambios en esta entrega.

## Escenario verificado

La prueba prepara una restricción de preferencias y una excepción de supresión posteriormente aprobada de forma independiente. Una conexión PostgreSQL mantiene el bloqueo del expediente de supresión; otra intenta consumir la excepción y se observa su espera con pg_blocking_pids.

Mientras permanece bloqueada, la conexión que mantiene el bloqueo completa un segundo procedimiento del mismo sujeto: entrada pública de solicitud, asignación, enlace de cuenta, consulta auditada, comprobación proporcional explícitamente simulada, preparación por finalidad, consulta/revisión independiente y ejecución real local de una nueva restricción de preferencias. No inserta directamente una fila de medida ni marca como aprobado un plan por actualización manual.

La transacción confirma la nueva medida al liberar el bloqueo. La supresión que esperaba revalida su ámbito/fuente y se deniega. Las dos medidas permanecen activas, los favoritos se conservan, la aprobación sigue sin consumir y no hay acción durable ni ejecución de supresión.

Este escenario prueba la invalidación por el nuevo procedimiento y sus efectos pertinentes en la fuente. No aísla únicamente la comparación de IDs de medidas: los registros del segundo expediente también alteran la fuente seleccionada y pueden provocar la denegación antes de llegar al consumidor. No afirmar que se hayan verificado todas las intercalaciones posibles o una incorporación de medida que evada los bloqueos de sujeto.

64770 terminal0:1 correcta32,84s PostgreSQL, sin fallos/errores/skips. Evidencia `evidencias/excepciones-nueva-medida.json`. La identidad sigue simulada; bloqueo/transacciones/servicios de decisión y creación de medidas son locales reales. No es comprobación de proveedor externo ni operación humana de producción.

## Continuación

Completar regresión conjunta y variantes de interfaz cuando cambien el contrato. Continuar finalidades pendientes y ámbito integral de derechos, conservación histórica/backup/restauración, exportaciones y comunicaciones/cierre. El inventario de cuenta44 modelos sigue seleccionado; no declarar CR09, GS01 o producción aceptados por esta prueba.
