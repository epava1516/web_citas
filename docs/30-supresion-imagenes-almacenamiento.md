# Supresión de imágenes, huellas y almacenamiento

Fecha: 2026-10-04. REQ-CR09-ERASURE-MEDIA-01. Extensión de docs/28–29. Ejecución local de archivos no compartidos verificada; CR-09 y derecho integral siguen abiertos.

## Ejecución por ámbito

media exige decisión erase vigente y permisos/prueba/lecturas/confirmación del ejecutor. Bloquea Blob ordenados y fotos propias antes de revalidar inventario. Si cualquier foto de otro perfil referencia uno de esos Blob, rechaza íntegramente: no elimina contenido compartido ni resuelve propiedad por primera carga. Sigue pendiente redacción/desvinculación revisada para recursos compartidos.

Marca fotos propias removed_at, approved=false/comparison_complete=true; conserva filas y referencias de evidencia. Cada Blob no compartido entra erasing, sustituye sha256 por valor aleatorio sin relación con imagen y vacía pHash, firmas/regionales y dimensiones. El hash aleatorio solo mantiene unicidad de la fila, no identifica bytes ni bloquea una nueva carga independiente. Los archivos físicos permanecen hasta completar tarea; no afirmar borrado físico al guardar el plan.

MediaErasure referencia Blob/ErasureExecution protegidos; cifra nombres de original/derivado. Transacción registra trabajo y revoca pruebas mediante rights_version. Resultado media_jobs_queued indica trabajos pendientes. No cierre automático de solicitud ni borrado de cuenta/expedientes.

## Worker y fallos

Tarea apps.mediafiles.tasks.erase_media_files, Beat60s, hasta100 trabajos por tanda. Cada trabajo bloquea Blob→MediaErasure. Borra original y derivado mediante backend de FileField y confirma inexistencia. Si falla almacenamiento, registra código genérico, intentos y backoff60/120/240/480/960s; máximo5 intentos automáticos. Se conserva información de reintento tras borrado parcial: borrar un archivo ya ausente es seguro. Alertas/recuperación de agotados aún pendientes.

Solo tras confirmar ambos archivos: Blob erased/nombres vacíos, tarea completed/fecha y nombres cifrados vacíos. Un rollback después de borrar archivo conserva trabajo pendiente y permite repetir. No transacción distribuida de filesystem/BD ni borrado acreditado de versiones históricas S3/réplicas/CDN/WAL/backups.

process comprueba erasing/erased al comenzar y al guardar el derivado; sus errores no sobrescriben esos estados. Ingest rechaza Blob en esos estados. El registro de coincidencias bloquea ambos Blob por UUID ordenado y vuelve a comprobar estados/fotos eliminadas; una comparación iniciada antes del borrado no crea evidencias nuevas de esa imagen después. Recuperación de trabajos media no selecciona esos estados.

## Evidencias y límites

Pruebas PostgreSQL con archivos sintéticos reales locales, fallo de almacenamiento inyectado explícito y carrera de dos conexiones en ejecución. Proveedor S3/canal/identidad reales no usados. Migración mediafiles0008. Ensayo operativo de la nueva tarea con Redis/worker/Beat reales registrado a continuación; una llamada directa a la tarea no sustituye ese ensayo.


CR-09 supresión de media implementada localmente: REQ-CR09-ERASURE-MEDIA-01, docs/30-supresion-imagenes-almacenamiento.md. Erase revisado por finalidad y fuente bajo locks Blob/Photo, rechazo de Blob referenciado por otro perfil y rutas físicas compartidas. Fotos removed/approved=false, Blob erasing, SHA sustituido por valor aleatorio no relacionado/pHash-firmas-regionales/dimensiones vacías. MediaErasure protegido liga ejecución/Blob, nombres cifrados y estado/attempts/backoff. No borrado físico en transacción web ni cierre de solicitud. Tarea erase_media_files/Beat60s confirma inexistencia de original/derivado, marca erased/completed y vacía nombres solo al completar; fallo parcial OSError conserva reintento, máximo5 intentos.
process comprueba estado al comenzar y al guardar derivado, errores no sobrescriben erasing/erased; ingest rechaza esos estados. record_match bloquea Blob por UUID ordenados y revalida fotos retiradas, evita nuevas coincidencias obsoletas. Inventario incluye estado de MediaErasure; UI ES/EN distingue retirada/huellas del borrado físico pendiente y muestra número de trabajos. Archivos compartidos/redacción y alertas/recuperación de agotados pendientes.
Pruebas iniciales21 passed122.28s (media_erasure/erasure_execution/photos), PostgreSQL/Chromium sin skips. Ampliación final27 passed181.19s (media_erasure/erasure_execution/erasure_inventory/erasure_plans), tras añadir inventario de jobs/guarda de rutas y browser media; no sumar baterías como común. Borrado físico de archivos sintéticos locales/metadata vacía/Photo preservada/replay; fallo de almacenamiento explícitamente inyectado elimina primero original y reintenta derivado sin restaurar archivo; Blob compartido rechazado/preservado; dos conexiones reales y eventos: worker calculando firma, nueva fuente preparada con estado processing, ejecución/borrado ocurren antes de finalizar cálculo y worker no escribe nuevo derivado. Browser móvil tres ámbitos, solicitud abierta. Proveedores/identidad reales no verificados. Ruff/format/check/makemigrations/diff limpios, mediafiles0008 aplicada en PG principal. Claude3/3 sin nuevas invocaciones.
Pendientes: media compartida/desvinculación, política jurídica/evidencias/retención, cuenta/contacto/representación, tombstones externos para restore/backups/versiones S3/CDN/réplicas, destinatarios/cierre integral, alertas/agotados y demás CR09; CR10→GS01→BF/BB→C pendientes.

Ensayo operativo media terminado: `uv run python -m scripts.probe_media_erasure_worker launch`, PostgreSQL/Redis/worker/Beat reales aislados, originales PNG/derivados WebP sintéticos y archivos de control vigentes. Fixture de tarea con Proof pending/plan-ejecución sintéticos y fuente draft, no decisión de derechos/identidad acreditada. Worker procesó eafc19fd-aea5-4c44-857d-93d842e2a74f:1 completed/2 archivos objetivo ausentes/2 controles intactos por SHA256/2 Photo y1 ejecución conservadas. Segunda tanda sin despacho manual: Beat con schedule original60s únicamente de erase-private-media en cola aislada,2 completed/4 objetivos ausentes/4 controles intactos/4 Photo y2 ejecuciones conservadas,65.078s; logs de scheduler/tarea comprobados. Resultado terminal exit0. Base media_probe_9cc6525248e9/contenedores/archivos sintéticos eliminados y cola vaciada; comprobación posterior0 bases/ningún contenedor/0 archivos del namespace. No S3/versiones/CDN/backups/identidad/canal real ni aceptación comúnCR09.
Docker principal app/worker/Beat reconstruidos/recreados, app confirma mediafiles0008/UID10001/adaptadores disabled/schedule erase-private-media60s y salud Caddy200. SHA256 host/contenedor erasure_execution=f536eb92817ce709e3bed1d99fd650088cb9bc4db3008d0d068317bee0ac3368 y mediafiles/services=2ac5b1550320923ca1d919d9c67fb43c72a0a809c17cc6061c35c5392cef4eb9 coinciden.

Regresión final de alias físico:1 passed17.98s PostgreSQL, distinto Blob apunta al derivado del objetivo como original; ejecución rechazada y archivo preservado/sin job. Fuente funcional idéntica a27 pruebas/probe; solo prueba añadida. No sumar como suite común.

Recuperación revisada de agotados implementada posteriormente en [docs/31](31-recuperacion-borrado-archivos.md); avisos entregados al operador siguen pendientes.

Redacción revisada de asociación propia con archivos compartidos implementada posteriormente en [docs/32](32-redaccion-imagenes-compartidas.md). Conserva archivos del otro perfil; no determina su propiedad ni elimina datos en evidencia histórica.
