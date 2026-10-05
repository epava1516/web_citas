# Inventario seleccionado de evidencias por finalidad

Fecha: 2026-10-05. Estado: ampliación verificada parcialmente; CR-09 abierto. Complementa docs56 y docs58–62. No es acceso integral, calendario jurídico definitivo ni autorización para eliminar evidencias.

## Cobertura ampliada

La fuente de cuenta `account_erasure_inventory.source` pasa de31 a44 modelos seleccionados. Incorpora13: ProcessingPurposePlan, ProcessingPlanRead, ProcessingPlanReview, ProcessingExecution, PurposeRestriction, PurposeRestrictionRead, PurposeReleaseProposal, PurposeCalendarEvent, PurposeExceptionProposal, PurposeExceptionRead, PurposeExceptionReview, RetentionReview y RetentionReviewEvent.

Estos registros se clasifican como dependent_evidence. El inventario devuelve por modelo finalidad, recuento, HMAC del estado y disposición pendiente de revisión; no entrega filas, fundamentos, motivos ni contenido cifrado. La huella de algunos registros incorpora ciphertext opaco para detectar cambios de integridad sin descifrar. Reencriptar un registro puede cambiar la huella aunque su contenido sea equivalente; se exige revisión fresca de forma conservadora.

El ámbito se determina por la cuenta del sujeto o por perfil cuyo subject sea esa cuenta; las medidas se filtran directamente por su sujeto y sus dependencias por la medida. No concede autoridad sobre perfiles de agencia cuyo sujeto sea otra persona. Planes de cuenta y planes de perfil se mantienen separados en sus consumidores.

## Fuente estable y cambios pertinentes

Los planes/lecturas/revisiones/ejecuciones de preparación por finalidad se excluyen solo cuando pertenecen al expediente consultado. Igual para las propuestas/lecturas/revisiones de excepción y el seguimiento de conservación del plan de supresión propio. Las medidas durables y el historial de sus restricciones/levantamiento/calendario siguen incluidos, también si afectan al expediente consultado: son efectos de tratamiento que deben detectarse.

Los procedimientos ajenos del mismo sujeto mantienen sus registros y estados en la fuente. Una excepción registrada en otro expediente aparece con recuento y huella; cambios de resultado, consumo, expiración o ciphertext alteran la huella pertinente. Las lecturas RightsAccess del expediente actual de supresión se excluyen para evitar que la consulta de un revisor invalide su propio plan; las de otros expedientes permanecen incluidas.

Se conserva esquema account-erasure-inventory-v2, cuya cobertura es seleccionada y evolutiva. El digest de un inventario anterior no coincide automáticamente con la fuente ampliada: sus planes requieren nueva preparación/revisión; los snapshots cifrados históricos no se reescriben. No existe excepción de compatibilidad que omita comprobación fresca.

## Verificación y límites

8290 terminal1: reproducción1 fallida28,82s de expectativa antigua que exigía RightsAccess propios en un expediente de supresión. Expectativa ajustada al protocolo de lectura estable introducido en docs62; la fuente mantiene las lecturas de otros procedimientos.85405 terminal0:6 conjuntas correctas68,81s PostgreSQL, dependencias/legado y consumo de excepción, sin fallos/errores/skips.

24857 terminal0:17 conjuntas correctas154,07s PostgreSQL/Chromium, sin fallos/errores/skips. Proyección explícita de44 modelos, exclusión de excepciones propias/visibilidad de las ajenas e integridad de ciphertext opaco, inventario de cuenta, preparación/revisión de restricciones, carreras de consumo y móvil ESEN. Evidencia `evidencias/inventario-finalidades-regresion.json`; no sumar a las6 anteriores como suite única23. Build91185 y recreate79245 terminal0 app/worker/Beat; esquema0072 sin migración nueva. Auditoría1603 terminal0:10 fuentes iguales host/app/worker/Beat, UID10001/check/migrate--check/health200, proveedores disabled. Evidencia `evidencias/inventario-finalidades-runtime.json`.

Pendiente: inventario integral de perfil y datos históricos, clasificación jurídica/retención final de estas evidencias, exportación y redacción pertinente, dependencias físicas/backups/restauración/tombstones, grandes volúmenes y ejecución por otras finalidades. La fuente actual recorre metadatos seleccionados; no acredita rendimiento a gran escala ni que todas las dependencias existentes estén censadas. Identidad externa continúa simulada en pruebas y los proveedores de runtime permanecen desactivados. No aceptar CR09 completo ni producción por esta ampliación.
