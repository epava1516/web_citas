# Redacción de referencias a imágenes compartidas

Fecha: 2026-10-04. REQ-CR09-SHARED-MEDIA-REDACTION-01. Extensión de docs/28–31. Verificado localmente; no entrega integral de supresión ni decisión sobre derechos de otros modelos.

## Alcance revisado

Una decisión media redact puede ejecutarse seleccionando media en el formulario existente. Exige la misma identidad/ámbito, lecturas actuales, responsabilidad, permisos/MFA/COI, fuente íntegra y confirmación que erase. Erase de un Blob compartido sigue prohibido; redact sin ninguna referencia compartida se rechaza para requerir una decisión adecuada a archivos exclusivos.

Bajo bloqueo de Blob y fotos propias, determina referencias compartidas por Photo de otra persona, incluso fotos ya retiradas que conservan referencias. Retira todas las fotos propias de exposición. Las fotos propias que referencian un Blob compartido pasan a una fila Blob vacía, estado erased y SHA aleatorio sin relación con bytes. Ese marcador no contiene original, derivado, huellas ni dimensiones; conserva IDs Photo/revisión y referencias de auditoría.

El Blob original conserva archivos/huellas y las fotos de otro perfil conservan su asociación/estado. No se crea trabajo físico sobre ese Blob ni se procesa eliminación durante HTTP. No se reasigna propiedad de la imagen ni se asume consentimiento de otro modelo. Los datos conservados en planes/expedientes/coincidencias siguen sujetos a revisión/retención independiente; el marcador no los anonimiza por sí solo.

## Ámbitos mixtos y continuación

Fotos exclusivas quedan retiradas pero conservan su referencia original. No se borran archivos por inferir un significado de los motivos de texto. Resultado cifra media_refs_detached y exclusive_media_pending; si hay exclusivos, media sigue en pending_purposes. UI informa de la diferencia entre redacción compartida y borrado posterior.

Tras nueva comprobación del ámbito, inventario y plan media erase, los marcadores erased se omiten y los archivos exclusivos siguen el worker durable de docs/30. Así puede continuar un ámbito mixto sin crear originales huérfanos de forma intencionada. Una ruta física compartida entre Blob distintos continúa exigiendo revisión especial y no se interpreta como autorización de borrar.

Cada plan admite una ejecución y todo replay exacto conserva resultado anterior sin nuevos marcadores. rights_version/case.version aumentan; solicitud reviewing/fechas intactas. Estas operaciones no acreditan comunicación a destinatarios, bloqueo reservado, conservación jurídica ni cumplimiento de una solicitud sobre apariciones de la misma imagen en anuncios de otras personas.

## Evidencias

Pruebas PostgreSQL/Chromium registradas a continuación: shared refs→marcador, filas Photo preservadas, archivos reales sintéticos de otro perfil intactos, ámbito mixto→nueva comprobación independiente simulada→inventario/plan→borrado físico exclusivo, móvil. No cambio de migración ni tarea de borrado. No nuevos proveedores/canales reales ni publicaciones.


CR-09 redacción de referencias a imágenes compartidas: REQ-CR09-SHARED-MEDIA-REDACTION-01, docs/32-redaccion-imagenes-compartidas.md. Ejecuta media redact revisado; bloquea Blob/Photo, retira fotos propias y reasigna solo referencias compartidas a Blob marcador erased vacío/SHA aleatorio sin bytes/huellas. Conserva Photo IDs/revisiones/auditoría y archivos/huellas/fotos del otro perfil. Sin job físico para shared; exclusivos retirados conservan referencia, contador exclusive_media_pending y media pendiente permiten nueva comprobación/inventario/plan erase que omite marcador y borra exclusivos. Redact sin shared rechazado. UUID/replay/epoch/COI/MFA/fuente de executor siguen vigentes; solicitud abierta.
Inicial1 failed/14 passed109.69s (shared_media_redaction/media_erasure/erasure_plans): test móvil esperaba resultado privado oculto al reload de POST, que reenvió correctamente POST y devolvió replay. Se corrige expectativa y añade navegación GET sin resultado. Ampliación2 failed/15 passed121.67s (shared_media_redaction/erasure_execution): consulta ORM introducida dentro de contexto Playwright generó SynchronousOnlyOperation; movida fuera. Fallo real adicional: descifrar decisiones antes de comprobar proveedor/producción produjo500 al faltar clave en fixture PRODUCTION=true. Se adelanta enabled() antes de descifrar; sin ejecución ni datos mutados.
Final17 passed126.13s PostgreSQL/Chromium sin skips (shared_media_redaction/erasure_execution), sobre corrección funcional. Incluye shared/mixto/archivo de peer intacto/fotos propias con IDs preservados, nueva comprobación independiente simulada y source/plan erase seguido de borrado físico exclusivo, móvil POST/recarga replay/GET privado oculto, carrera real2 conexiones/un marcador, redact sin shared rechazado, scopes iniciales/producción rechazada409/CSRF/permiso/sesión revocada/favorito intercalado/epoch y copia. No sumar ejecuciones como comúnCR09. Ruff/format/check/makemigrations/diff limpios; sin nuevas migraciones ni cambios de task/schedule. Claude3/3 sin nuevas invocaciones.
Quedan asociaciones/datos en evidencias/planes históricos, conservación/bloqueo/plazos, contacto/cuenta/representación, otras apariciones de la imagen/destinatarios/alertas, tombstones externos/restore/backups y respuesta/cierre integral, demás CR09; CR10→GS01→BF/BB→C pendientes. No acreditar propiedad/consentimiento de otro perfil ni anonimización de evidencias por marcador.

Docker redacción shared: app/worker/Beat reconstruidos/recreados, esquema mediafiles0009 existente confirmado/UID10001/backends disabled/salud Caddy200. SHA256 erasure_execution.py host/contenedor coincidea236ad75f8e52fe6334e94f86a745564011b13409ca750379c7306166d185f71. Sin nueva tarea/ensayo operativo, tarea de archivos/schedule sin cambios; producción no habilitada.
