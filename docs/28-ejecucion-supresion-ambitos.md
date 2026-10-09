# Ejecución parcial de supresión por ámbitos

Fecha: 2026-10-04. Requisito: REQ-CR09-ERASURE-EXECUTE-01. CR-09 sigue en curso. Complementa [inventario](26-inventario-supresion-retencion.md) y [decisiones](27-planes-supresion-conservacion.md); no sustituye los requisitos del derecho completo ni acredita cumplimiento jurídico.

## Operaciones de la primera entrega 9acfc48

La ampliación vigente de alias y contenido editorial se especifica en [docs/29](29-supresion-contenido-publicacion.md). La tabla siguiente conserva el alcance verificado de la primera entrega.

POST `/en/moderation/rights/<case>/erasure-execute/<plan>/` (también ES) ejecuta exclusivamente finalidades seleccionadas cuya decisión del plan es `erase`:

| Finalidad | Efecto local | Recursos conservados |
| --- | --- | --- |
| authentication | Borra AccountToken y RecoveryCode de Person.subject; incrementa versiones de sesión y MFA | Cuenta, contraseña, secreto TOTP, roles y aceptaciones |
| account_preferences | Borra favoritos de Person.subject; revoca sesiones y MFA | Favoritos de otros usuarios, anuncios y relaciones de agencia |
| transient_copy | Vacía JSON y adjuntos cifrados de RightsExport de esa persona; marca purged_at | Filas de auditoría, fotos fuente, originales y expedientes |

Cada ejecución incrementa Person.rights_version, invalida pruebas anteriores de esa persona incluso en otras solicitudes y actualiza versión/scope de la solicitud ejecutada. Generación de copias y descargas comprueban la versión de privacidad. La solicitud permanece `reviewing`, conserva vencimientos y no emite una resolución final automática. Las otras solicitudes conservan el estado histórico de la comprobación; ese estado por sí solo ya no autoriza operaciones.

## Autorización, concurrencia y auditoría

Exige permisos review/execute, MFA, ausencia de conflicto, responsable asignado, lectura completa vigente, prueba de identidad/ámbito erase vigente, inventario del mismo actor/persona/solicitud y digest de fuente sin cambios. El simulador no autoriza producción. Plan vencido, finalidades no implementadas o decididas review/retain/redact se rechazan. Confirmación explícita y motivo minimizado20–2000 caracteres.

Locks Agency→Person→Listing→RightsRequest, después cuenta propia y copias/adjuntos ordenados. User usa FOR NO KEY UPDATE: bloquea escritores de cuenta y la comprobación explícita de favoritos, pero permite referencias FK de auditoría sin bloquear innecesariamente otro ejecutor. Añadir favorito bloquea persona/anuncio destino y luego User; vuelve a comprobar account_version dentro de la transacción. Una petición que atravesó el middleware antes de la revocación no puede recrear favoritos después del borrado.

AccountGateMiddleware consume account_version registrado al acceder. Sesiones locales antiguas sin versión solo se vinculan automáticamente cuando session_version=0; una versión revocada nunca se vuelve a vincular. La siguiente petición privada con sesión antigua pierde autenticación. No se afirma que se borren físicamente todas las filas de sesión ni que se interrumpa toda petición ya iniciada.

ErasureExecution protege plan/action/proof/person y cifra resultados y contadores. UUID global/firma canónica: replay exacto devuelve el resultado anterior sin repetir borrados; conflicto409. Cada plan admite una ejecución; continuar otras finalidades requiere nueva comprobación/inventario/plan. Transacción completa revierte ante conflicto. GET no muestra resultados ni motivos históricos; POST muestra contadores minimizados. CSRF, no-store y noindex de rutas privadas.

## Límites y pendientes vinculantes

Quedan pendientes la supresión/redacción de perfil y publicación, originales/derivados/huellas, contactos compartidos, cuenta y otras responsabilidades, inventario físico integral, bloqueo reservado y conservación por fundamento/plazo, tareas/cargas, cachés, destinatarios, tombstones/restore, WAL/backups, notificaciones y respuesta/cierre completos. Este ejecutor parcial no satisface por sí solo la supresión solicitada. Política jurídica/revisión independiente y proveedores reales siguen pendientes conforme a docs/06 y docs/27.

## Evidencia

Primera batería: `tests/test_erasure_execution.py tests/test_erasure_plans.py tests/test_favorites.py tests/test_accounts.py`:25 passed111.84s, PostgreSQL y Chromium, sin skips. Incluye borrado/replay/aislamiento de favorito ajeno/fuente conservada, sesión revocada, rechazo de cambios de fuente/producción/CSRF y concurrencia real de misma clave, interfaz móvil. La copia almacenada de la fixture de ejecución es un snapshot sintético con adjunto de bytes inventados, no una copia de acceso liberada ni un WebP procesado. La segunda batería amplía los escenarios con copia de acceso real de desarrollo, invalidación entre solicitudes y petición de favorito intercalada; resultado:7 passed54.69s, PostgreSQL/Chromium sin skips; la copia usa el generador y canal de descarga reales locales con identidad simulada, sin canal externo. No sumar baterías como regresión común CR-09.

Docker de ejecución parcial: app/worker/Beat reconstruidos y recreados; app confirma core0012/safety0036/0037, UID10001, ruta erasure_execute y derechos/avisos disabled. SHA256 host/contenedor erasure_execution.py coincide58d909a5c17ce21ee198b1cca7a76a4b6815a7ad8b9c3035b105d6adb5ae4388; salud Caddy200. Primera consulta operativa usó nombre inexistente NOTICE_DELIVERY_BACKEND y falló; corregida a SAFETY_NOTICE_BACKEND, segunda consulta exit0 confirma disabled. No ensayo de nueva tarea ni producción por esta operación.
