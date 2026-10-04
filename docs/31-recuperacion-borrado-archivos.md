# Recuperación operativa de borrado de archivos

Fecha: 2026-10-04. REQ-CR09-MEDIA-RECOVERY-01. Amplía [supresión media](30-supresion-imagenes-almacenamiento.md). Recuperación verificada localmente; CR-09 sigue abierto.

## Permisos y pantallas

`/es|en/moderation/rights/<case>/media-jobs/` muestra trabajos de esa solicitud,50 por página, sin rutas, imágenes ni motivos. Enlace desde inspección visible con permiso específico. Detalle `/media-jobs/<job>/` muestra estado/contador y formulario solo si failed/attempts>=5. En la cola los agotados tienen indicación persistente; no es un aviso entregado a un operador ni sustituye alertas duraderas pendientes.

Exige review_rights_request, manage_media_erasure y MFA vigente de sesión para HTTP; COI actual/histórico del caso se comprueba antes de mostrar o recuperar. El permiso nuevo no se otorga automáticamente a todos los moderadores. Un coordinador autorizado puede recuperar trabajos anteriores sin una nueva prueba de identidad: continúa exclusivamente el borrado ya autorizado, no crea un nuevo ámbito.

POST key/version/reason20–2000, CSRF y cabeceras privadas/noindex. Requeue solo failed con cinco intentos, Blob erasing y rutas cifradas disponibles. Una ejecución simulada no autoriza recuperación nueva en producción. No autoriza mostrar o cambiar rutas ni ejecutar almacenamiento durante HTTP. Respuesta302 a cola;400 formulario,409 ciclo/estado incompatible,403 permiso/COI/CSRF,404 caso o trabajo ajeno.

## Auditoría y concurrencia

Locks Agency→Person→RightsRequest→Blob→MediaErasure, compatibles con executor y worker. recovery_version independiente de versión de caso; incremento por ciclo y auditoría MediaErasureRecovery protegida con previous_version/previous_attempts y RightsAction de UUID global, actor, caso, firma y motivo cifrado.

Requeue restablece queued/attempts0/next_attempt_at=ahora/error vacío; worker/Beat procesa después. No modifica contenido cifrado, prueba/plan, cuenta, datos conservados, solicitud o vencimientos. Replay exacto devuelve auditoría previa incluso tras completar el job; no reinicia intentos ni cambia estado. Conflicto de UUID revierte toda transacción.

La recuperación conserva número previo de intentos por ciclo en auditoría. La tabla del job muestra contador actual; no confundirlo con acumulado de todos los ciclos. Cada nuevo ciclo exige nueva clave/versión y un nuevo motivo operativo. La aplicación no comprueba automáticamente que el operador haya resuelto la incidencia de almacenamiento.

## Verificación y pendientes

Migración mediafiles0009. Pruebas PostgreSQL/Chromium registradas a continuación con agotamiento como fixture sintético de estado (cinco fallos no provocados en estas pruebas), borrado físico local posterior, permisos/CSRF/producción, replay tras completar, carrera de dos conexiones y móvil. No comunicación/proveedor/identidad reales acreditados. Alertas entregadas/recibidas, recuperación transversal y aceptación común CR09 siguen pendientes.


CR-09 recuperación de trabajos de archivos agotados: REQ-CR09-MEDIA-RECOVERY-01, docs/31-recuperacion-borrado-archivos.md. MediaErasure.recovery_version y MediaErasureRecovery protegida/acción RightsAction UUID global/actor/motivo cifrado/previous_version/attempts. Permiso separado manage_media_erasure + review/MFA/COI actual-histórico, no otorgado por defecto a todos los moderadores. Cola y detalle por caso50/página sin rutas/contenido/motivos; enlace condicionado desde consulta de derechos. Failed/attempts>=5/Blob erasing/contenido cifrado vigente; requeue actualiza queued/attempts0/next_at/versión sin borrar en HTTP, ejecutar nuevo ámbito, revalidar identidad simulada en producción ni cerrar expediente. Exact replay no reinicia ciclos nuevos/completados. Inventario incluye recovery_version y auditorías seleccionadas.
Inicial9 passed67.29s (media_operations/media_erasure), ampliación10 passed75.12s (media_operations/erasure_inventory), PostgreSQL/Chromium sin skips. UI móvil login/MFA→cola→detalle→motivo→requeue→recarga persistente; recuperación/borrado físico local/replay tras completar/CSRF/permiso retirado/producción/versión obsoleta, carrera real de2 conexiones misma clave/un ciclo, gestor con permisos operativos igualmente excluido, replay antiguo no cambia3 intentos de ciclo posterior. Agotamiento fue fixture de estado failed/5, no5 fallos provocados ni incidente real. No sumar baterías como común ni afirmar aviso recibido. Ruff/format/check/makemigrations/diff limpios; worker erase_one/tarea/schedule sin cambios, ensayo operativo físico anterior conserva alcance docs/30, no repetido sin cambio funcional en tarea.
Pendientes: alertas internas duraderas/operador, recursos compartidos, conservación/evidencias/plazos, cuenta/contacto/representación, tombstones externos/restauración/destinatarios/respuestas y demás CR09; CR10→GS01→BF/BB→C pendientes. Claude3/3 sin nuevas invocaciones.

Docker recuperación: mediafiles0009 aplicada, app/worker/Beat reconstruidos/recreados. App confirma UID10001/nueva ruta media_erasure_jobs/adaptadores derechos y avisos disabled; salud Caddy200. SHA256 media_operations.py host/contenedor coincide581691a0e2c4ce7bdb3a17655bfb809ce339792559e32e48abf53182896afe3b. No nuevo ensayo operativo de tarea (worker/schedule funcionalmente sin cambios), producción no habilitada.
