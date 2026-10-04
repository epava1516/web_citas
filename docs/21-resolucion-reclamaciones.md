# Resolución independiente de reclamaciones — CR-09

Estado: implementación local parcial del flujo global; no cierre de CR-09 ni acreditación jurídica. Datos sintéticos y PostgreSQL. Vinculado a contratos/10 y acta/04.

## Operaciones y autorizaciones

| Ruta (prefijo ES/EN) | Método | Acceso y efecto |
| --- | --- | --- |
| /moderation/complaints/<uuid>/ | GET/POST | GET oculta contenido; POST con purpose registra ComplaintAccess/intake de versión de caso y origen. Evidencia de revisión solo con review_listing; denuncia exige además consulta original auditada con review_report. COI y MFA aplicados bajo locks. |
| /moderation/complaints/<uuid>/photo/<uuid>/ | GET | Derivado WebP de fotografía vigente de la revisión enlazada; exige review_complaint/review_listing/MFA/COI y consulta actual. Registra ComplaintAccess/image. Otra revisión o foto retirada404; consulta ausente o procesamiento409; permiso/COI403. Nunca originales. |
| /moderation/complaints/<uuid>/resolve/ | GET/POST | Permisos review_complaint + resolve_complaint, MFA vigente, permiso del origen e independencia. Formulario; POST resuelve atómicamente o devuelve400/403/409. Éxito/replay exacto302 a consulta. |
| /safety/complaints/<uuid>/<secret>/ | GET | Acuse propio válido/no caducado muestra fecha, resultado y respuesta cifrada de resolución; no notas internas, identidad del revisor ni expediente ajeno. |

Todos los recursos son privados/no-store/noindex/referrer same-origin, incluidos errores. CSRF sigue obligatorio en POST. Resolver no demuestra identidad del solicitante ni verdad de su relación declarada. El secreto permite consultar solo su propia solicitud.

## Formulario y evidencia

Campos: key UUID único, version positivo del caso, source_version positivo del origen (ocultos); outcome upheld/reconsidered; reason interno20–2000; response al solicitante50–2000; redaction_confirmed obligatorio. El permiso resolve_complaint es independiente de asignación y lectura. El responsable debe ser el actor del caso reviewing, con ComplaintAccess/intake actual y source_version coincidente con origen y snapshot del enlace. Registros antiguos null no conceden lectura del origen.

Para revisión de anuncio se entregan motivo original, descripción/alternativa, tipo/idioma, geografía, contactos, categorías/servicios, disponibilidad y tarifas por pantalla privada, más derivados por la ruta auditada del caso. Todas las imágenes vigentes deben tener auditoría image de actor/caso/versión/origen antes de resolver. Acceso de imagen no sustituye lectura de texto. Auditorías registran autorización/entrega, no comprensión humana. Procesamiento no terminado bloquea consulta de imagen y resolución hasta recuperar/verificar; procedimiento alternativo para material irrecuperable sigue pendiente.

Para denuncia, el actor requiere ReportAccess de versión actual/página reciente y consulta del expediente original con su permiso separado. La reclamación no concede automáticamente acceso al denunciante. Se contrasta la última decisión sustantiva del origen. Versiones/gestión/fuente cambiadas provocan409; reidentificación/actualización segura del enlace y triage de casos sin fuente fiable aún pendientes.

Respuesta y notas se cifran por separado. La respuesta exige declaración de revisión humana; controles adicionales rechazan enlaces, contactos, números largos y nombre/correo del notificante original. No constituyen un detector completo de datos personales ni prueban que la motivación sea correcta. Moderación formada y procedimiento de redacción/revisión jurídica siguen siendo gates externos. Plantillas escapan texto/HTML; CSP no se relaja.

## Resultados y transacción

| Origen | Mantener | Reconsiderar |
| --- | --- | --- |
| Denuncia restringida/confirmada | Central decisions.act/uphold, con review_restriction, independencia y evidencia actuales | decisions.act/lift; levanta solo esa restricción, sin republicar ni liberar otras |
| Denuncia desestimada/levantada | Resolución de reclamación conserva estado | Reabre received, elimina asignación, incrementa Report.version y crea ReportAction/reopen con aviso transaccional; requiere nuevo claim/consulta/decisión |
| Revisión de anuncio aprobado/rechazado | Mantiene decisión vigente, sin publicación adicional | Revisión pending, edit_version+1 e imágenes no aprobadas; validación actual de autorización/legal/contacto/calidad. Reabrir anuncio aprobado retira cabeza cuestionada hacia su base y deja listing pending/paused; requiere nueva decisión para publicar. Reabrir actualización rechazada conserva cabeza pública anterior, fechas y estado. |

Listing conserva ID. Cambios de exposición incrementan lifecycle_version y limpian disponible ahora; una actualización rechazada sin cambio de cabeza no modifica el ciclo de la versión pública válida. Reapertura también incrementa edit_version en recursos autenticados existentes para rechazar formularios antiguos. Una nueva moderación debe cargar la versión actual y pasar las guardas comunes.

ComplaintAction/resolve y ComplaintResolution uno por caso se registran con clave/firma/motivo cifrado. Case.status=resolved y version+1; fechas originales/caducidad/payload recibidos intactos. Reintento exacto no vuelve a alterar origen ni crea respuesta/aviso duplicados; conflicto de clave o competencia causa rollback completo. Locks de origen preceden al caso; denuncia bloquea Listing antes de Report para evitar inversión al reutilizar decisions.act.

Restriction sigue siendo proyección de estado actual por Report. Reabrir una denuncia levantada y restringirla de nuevo actualiza esa proyección (acción actual, activa, sin revisión anterior, fecha nueva), preservando ReportAction históricos y avisos. No sustituirlo por borrado de historia ni interpretar la fecha actual como la fecha del primer evento. Restricción ya activa exige revisión independiente, no sobrescritura por restrict.

## Avisos y alcance pendiente

ComplaintNotice uno por resolución con contacto declarado: destinatario cifrado y texto fijo mínimo «respuesta disponible; consulta tu enlace guardado», sin respuesta, motivo, ID ni secreto. Se crea en la misma transacción; sin contacto no hay aviso. Estado queued significa únicamente preparación, no envío/entrega. Worker, reintentos/fallos, simulador declarado para esta nueva outbox y confirmación de canal quedan pendientes. No hay correo real ni proveedor contratado. ReportNotice ya admite mensaje mínimo reopen, también en cola.

Siguen pendientes cierre completo de recursos desconocidos/obsoletos, procedimientos de información adicional y material no recuperable, comunicación operativa por worker, avisos a afectados, derechos/copia integral/supresión/retención, común y Docker final CR09. Continúa CR10→GS01→BF/BB→C. No se congela GS01 ni se proclama cumplimiento completo de RGPD/LOPDGDD/DSA.
