# Supresión de contenido editorial y alias

Fecha: 2026-10-04. REQ-CR09-ERASURE-PUBLICATION-01. Amplía [ejecución por ámbitos](28-ejecucion-supresion-ambitos.md). Ejecución editorial verificada localmente; no aceptación del derecho completo.

## Alcance del ejecutor

La finalidad publication decidida erase vacía todas las revisiones de la persona: título, descripciones ES/alternativa, tipo de perfil, ciudad/CP/zona, idiomas, días/franja, desplazamiento/recepción, teléfono/WhatsApp/Telegram y aceptación de exposición. Elimina tarifas y relaciones categorías/servicios/municipios de desplazamiento. Incrementa edit_version, marca revisiones withdrawn, retira anuncio, desvincula approved_revision, vacía fechas de publicación/caducidad/disponibilidad e incrementa lifecycle_version.

Las filas de revisión se conservan como referencias de auditoría: Submission, ModerationDecision, denuncias y otros registros las protegen. Se conservan IDs, gestor/manager_version, autoría contractual, fechas técnicas e historial relacional. Esto no implica que todas las evidencias sean anónimas o tengan ya una política definitiva de conservación.

La finalidad profile decidida erase elimina alias y editor asignado. Debe ejecutarse junto a publication para evitar que un perfil aún expuesto permanezca sin alias. Las relaciones subject/individual/agency y comprobaciones se conservan para tratar los demás ámbitos; cuenta/representación/contacto compartido tienen decisiones y ejecución independientes. No se llama a esta operación borrado integral de Person.

## Prevención de reaparición

Person.publication_erased_at es una marca persistente con fecha. person_queryset excluye ese perfil de gestión; locked_manager_person vuelve a comprobarla bajo bloqueo. create_draft, publication_ready y validate_submission la comprueban explícitamente. Una transferencia o una tarea antigua no elimina la marca; no existe acción de levantarla.

El ejecutor mantiene locks Agency→Person→Listing→RightsRequest y bloquea revisiones ordenadas antes de revalidar el inventario. Formularios que esperan esos bloqueos deben volver a comprobar autorización/versión. Una aprobación o actualización anterior que cambie la fuente invalida el plan; si el borrado ocurre primero, las operaciones posteriores encuentran la marca y revisiones withdrawn. No se promete interrumpir una respuesta que ya estaba leyendo contenido antes de la transacción.

Esta marca protege la DB activa; todavía no es un tombstone persistido fuera de la base para reconciliar restauraciones de backups. Ese procedimiento, originales/derivados/huellas, caches, información retenida en evidencias, cuenta, destinatarios y cierre siguen pendientes. Los archivos se conservan físicamente hasta la ejecución específica de media; la marca impide exposición y acceso de gestores al perfil.

## Interfaz y contrato

Misma ruta/permiso/CSRF/replay de docs/28, nuevas opciones profile/publication. Solo operaciones erase revisadas y vigentes; profile sola o publication sin decisión erase producen409. Resultados incluyen revisions_cleared, rates_deleted y profile_alias_cleared, cifrados en ErasureExecution. Identidad simulada solo desarrollo, producción rechazada. Solicitud sigue reviewing sin variar vencimientos.

Migración core0013. Resultados de pruebas PostgreSQL/Chromium registrados a continuación; no usar este documento como prueba de cumplimiento jurídico.


CR-09 supresión de contenido editorial y alias: REQ-CR09-ERASURE-PUBLICATION-01, docs/29-supresion-contenido-publicacion.md. Ejecuta publication erase vaciando textos/contactos/ubicación/atributos/rates/M2M de todas las revisiones propias, withdrawn/edit_version+1 y retirada Listing/desvinculación head/fechas vacías/lifecycle_version+1. Profile erase solo junto a publication: alias/editor vacíos. Referencias de revisión/contrato/gestor y evidencias protegidas conservadas; no borrado integral de Person/cuenta/archivo. Marca persistente publication_erased_at, person_queryset/locked_manager_person/create_draft/publication_ready/validate_submission impiden gestión/exposición incluso status forzado o manager posterior. Bloqueo de revisiones y fuente revalidada; UUID/replay/motivos cifrados/permisos/MFA/COI/prueba siguen vigentes, request reviewing/fechas intactas.
Inicial1 failed/16 passed87.02s (erasure_execution/favorites/drafts): nueva prueba construía URL de foto sin listing_id, NoReverseMatch; se corrige argumento según contrato, código funcional sin cambio. Ampliación final11 passed80.11s (erasure_execution), PostgreSQL/Chromium sin skips: móvil tokens/favoritos/copia y alias/publicación, aislamiento de otro modelo/datos Blob conservados, rechazo de profile sola y decisión review, exposición forzada rechazada404; petición real de gestor iniciada antes del borrado espera bloqueo, después403/sin borrador nuevo. Carrera usa dos conexiones y eventos, no simulador de BD. No sumar ejecuciones como suite común. Ruff/format/check/makemigrations/diff limpios. core0013 aplicada en PostgreSQL principal.
Quedan identidad de cuenta/relaciones/representación/contacto, media física/huellas/evidencias/retención/bloqueo reservado, tombstones externos para restore/backups/caches/destinatarios/respuesta final y demás CR09. Esta marca es de DB activa, no reconciliación de backups. CR10→GS01→BF/BB→C siguen pendientes; Claude3/3 sin nuevas llamadas.

Docker de supresión editorial: app/worker/Beat reconstruidos/recreados, aplicación confirma core0013/publication_erased_at/UID10001 y rights/notice backends disabled. SHA256 erasure_execution.py host/contenedor coincide c523d5906d2d4a2dbb067ecbacfc7c863912e71b362f166b534b260b2aa63fc1; salud Caddy200. No nueva tarea ensayada ni producción habilitada.
