# N09D — prerregistro de reclamaciones y levantamiento de medidas

Antes del diagnóstico, sin cambiar aplicación. Basef65a530, correcciones locales [428](428-n09-c-operaciones-autoridad-verificada-20261026.md), [425](425-n09-b-inspeccion-autoridad-verificada-20261026.md) y [422](422-n09-a-correccion-verificada-recuperaciones-20261026.md) conservadas sin repetir58/19/29por notas. N09 abierto139IDs/8de13bloques. Corte previo:2.053fuentes exactas,SHA256 `a9de48747efe95d93104bdc851f7742448f86cd42f2dd8ba48b7e11d7f37745f`.

## Condiciones de fuente, sin fallo runtime nuevo

Reclamaciones: inspect vuelve a consultar allowed tras locked sobre el mismo request.user; photo comprueba review_listing antes de esperar y abre la imagen después sin Usernuevo; complaint_actions.act y complaint_resolutions.resolve reciben actor/permisos cacheables alrededor de locks. La resolución de listing se añade a los cinco grupos del triage porque comparte la frontera y puede modificar decisión/publicación y emitir respuesta. No se considera probada por analizar claim.

Levantamiento: privacy_release.actor_check usa el actor existente; propose llama tarde a issue, que refresca review/respond/MFA/epochs pero no review_privacy_hold/execute, y el replay retorna antes de issue. Execute usa actor_check después de los locks y puede esperar primero en un JOIN de propuesta antes del Hold explícito. Proof/ámbito/auditoría vigentes no sustituyen autoridad actual. Estas condiciones requieren reproducción propia; no son seis FAILanticipados.

## Seis diagnósticos previstos:cincoPOST y unGET

| Caso | Preparación nativa sintética | Lock observado y permiso retirado | Oráculo |
| --- | --- | --- | --- |
| Inspección de reclamación |test_complaint_assignment.prepared, caso anónimo sin fuente|Complaint;review_complaint|403;sin nuevo acceso/cambio|
| Fotografía privada |test_complaint_resolutions.listing_case(rejected=True), inspection(images=False),derivada ready local|Complaint;listings.review_listing|403 no streaming;sin auditoría de imagen/cambio|
| Asignar reclamación |prepared y action(operation=claim),received/sin asignación|Complaint;review_complaint|403;sin acción/asignación/versión|
| Resolver listing |listing_case(rejected=True),inspection(images=True),resolution válida|Complaint;resolve_complaint|403;sin resolución/notice/acción ni cambios de caso/revisión/publicación|
| Proponer levantamiento |test_privacy_release.prepared,actual kind restriction, reviewer independiente y prueba vigente|PrivacyPublicationHold;review_privacy_hold|403;sin propuesta/respuesta/notice/acción/cambio|
| Ejecutar levantamiento |prepared,plan,confirmación explícita del canal y fresh posterior nativos|PrivacyHoldReleaseProposal;review_privacy_hold|403;medida activa y propuesta sin ejecutar,dominio intacto|

Todas las sesiones, lecturas y efectos legítimos anteriores quedan preparados antes de bloquear y conservados como referencia. Refrescar caso/proof/hold/propuesta después de servicios nativos. La fixture prepared(kind) de privacy_release fija restriction: estos dos diagnósticos afirman sólo ese tipo real, no tres tipos por su parámetro. Los proof son del simulador no producción, sin identidad real ni proveedor. Resolución de listing no acredita resolución de report ni los permisos extra de unassign/reassess; sus condiciones permanecen separadas para regresión/evaluación pertinente.

Reutilizar el observador pasivo de419para POST: PID efectivo, pg_stat_activity/Lock y PID propio bloqueante antes de quitar el permiso, Usernuevo confirma revocación y transacción confirma al liberar. No parchear guards, ORM de negocio, cifrado o respuesta. Guard propio explícito/serial/noPROD/PGpropio por archivo, sin reutilizar __file__ ajeno. Snapshots escalares incluyen caso/acciones/accesos/notice/resolución y recursos vinculados o dominio de derechos/hold/propuesta/respuesta/acuse/proof, excluyendo la mutación deliberada del operador. Denegación requiere snapshots/estado mínimo idénticos y limpieza de hilo/conexión/lock.

Para fotografía, un adaptador local satisface la interfaz callback del observador pero llama **Client.get real**, nunca post ni respuesta fabricada. Registrar método real de response.wsgi_request, status y streaming. Si la respuesta errónea entrega imagen, consumir streaming local con cota1MiB de fixture, registrar sólo longitud/digest y cerrar en finally; no registrar bytes/ruta física. El403corregido debe ser no streaming/con0bytes de imagen y respuesta cerrada. La espera/GET/lectura de FileResponse es local del handler, no proxy/proveedor/browser. Sus tiempos incluyen el bloqueo y el consumo/cierre, distintos de unPOSTsin cuerpo streaming.

## Ejecución y clasificación

Propuestas aisladas con propiedad explícita, revisión Django Expert/Reviewer/fixtures/rutas/instrumento, lint antes de AST/semántica/corte/congelación. Runner oficial con PostgreSQL/Redis propios desechables, serial, parser nativo, broker aislado/observación HTTP y timeout900s. Seis casos, sin QA global/exportación larga. Avisos Telegram de inicio/terminal, recibos y limpieza comprobados.

Conservar FAIL/ERROR/SKIP.200/302y efectos tras espera/revocación confirmadas demuestran defecto de esa operación; foto200con auditoría y stream consumido demuestra entrega local indebida, sin publicar su contenido. Un fallo antes de observar espera/revocación es potencialmente instrumental; no convertirlo en fallo de producto. Si deniega correctamente, conservar evidencia sin corregir por semejanza. Prerregistrar corrección/regresión después de diagnosticar, sin anticipar candidatos. Tiempos inducidos no son latencia normal ni aceleración causal. N09/139IDs, restantes condiciones de fuente y referencias finitas purgas/outbox/jobs siguen pendientes; N02al final/N10compartido/N12–N14condicionados/alfa/sinproveedor/sinapertura.
