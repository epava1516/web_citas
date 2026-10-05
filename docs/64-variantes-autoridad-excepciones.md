# Variantes y autoridad de excepciones durante la espera

Fecha: 2026-10-05. Estado: verificación local parcial; CR-09 abierto. Complementa docs62–63. Código funcional y runtime0072 sin cambios en esta entrega; no integración externa nueva.

## Autoridad posterior a bloqueos

La prueba `test_purpose_exception_late_authority` retiene la fila PurposeExceptionReview con una conexión PostgreSQL y observa mediante pg_blocking_pids que otra conexión que ejecuta supresión está esperando ese bloqueo. La espera se produce después de las comprobaciones preliminares del inventario y la autorización, dentro del consumidor de excepción.

Mientras espera, se prueban cuatro cambios por separado:

- Retirada del permiso específico del aprobador mediante su relación de permisos.
- Cambio almacenado de versión MFA del ejecutor; estado sintético de revocación, no recorrido de recuperación MFA.
- Invalidación almacenada de la prueba proporcional; no callback de proveedor real ni prueba de entrega externa.
- Avance controlado únicamente del reloj de excepción más allá de su caducidad; los relojes de comprobación de identidad y plan mantienen su tiempo. No presentar como espera real de24 horas.

En los cuatro casos, al liberar el bloqueo la supresión se deniega. La aprobación permanece sin consumir; favoritos, versión de expediente y restricción activa se conservan. No queda acción durable de ejecución ni registro de supresión.4626 terminal0:4 correctas56,54s PostgreSQL, cero fallos/errores/skips. Evidencia `evidencias/excepciones-autoridad-tardia.json`.

## Oposición y ámbito de perfil

`test_purpose_exception_opposition` crea un expediente local de oposición, su comprobación explícitamente simulada, preparación/revisión de finalidad y ejecución real local de una medida cease. Posteriormente crea y revisa una excepción vinculada a una nueva solicitud de supresión. Consumirla elimina solo favoritos seleccionados, conserva activa la medida cease y no desactiva la cuenta.64744 terminal0:1 correcta31,95s PostgreSQL. Evidencia `evidencias/excepciones-oposicion.json`.

`test_purpose_exception_profile` usa un expediente enlazado a anuncio/perfil, preparación/revisión y restricción efectiva reales locales, seguido de nuevo expediente de supresión enlazado al mismo anuncio, prueba simulada y propuesta/revisión de excepción. El inventario/plan permanece en ámbito Person con account_subject nulo. El consumo elimina favoritos, conserva la restricción y preserva estado/revisión aprobada/versión de ciclo de vida del anuncio, versión de gestor y registros de agencias.90435 terminal0:1 correcta33,27s PostgreSQL. Evidencia `evidencias/excepciones-ambito-perfil.json`.

Son tres ejecuciones separadas, no una suite conjunta6. Estas pruebas amplían evidencia de los servicios existentes; no prueban interfaz móvil de oposición/perfil ni revisión jurídica de fundamentos. La comprobación de identidad sigue simulada en todos los escenarios.

## Continuación obligatoria

Crear y observar una nueva medida real del mismo sujeto mientras una supresión espera, incluyendo las medidas concurrentes que aún no estaban en la propuesta. Verificar la fuente y el conjunto completo tras esperar; no sustituir ese caso por insertar una fila sin procedimiento. Completar pruebas de variantes de interfaz cuando afecten el contrato, regresión conjunta de finalidades y evidencia de mismo commit. Mantener pendientes inventario integral, otras finalidades de tratamiento, conservación histórica/restore/backups, exportación integral y comunicaciones/cierre. No aceptar CR09, GS01 o producción por estas pruebas parciales.
