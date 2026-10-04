# Supresión de desafíos, invitaciones y asociación de teléfono

Fecha: 2026-10-04. REQ-CR09-CONTACT-ERASURE-01. Extensión de docs/28–32; verificado localmente. No cierre integral de derechos.

## Finalidades conectadas

| Finalidad/decisión | Efecto propio | Recursos conservados |
| --- | --- | --- |
| contact erase | Borra PhoneChallenge del perfil, incluidos usados/caducados | PhoneClaim, otros perfiles y datos de evidencia |
| representation erase | Borra RepresentationInvitation del perfil | RepresentationAction/consentimiento ya otorgado, sujeto/gestor |
| shared_contact_review redact | Desvincula Person.phone_claim y vacía phone/whatsapp en revisiones propias; incrementa edit/lifecycle y limpia disponibilidad; pausa solo published | Registro PhoneClaim de gestor/agencia y revisiones de otros perfiles |

El ejecutor no interpreta erase del teléfono del gestor como autorización de borrar su registro global. Esa operación no está conectada; la decisión disponible para asociación es redact. Otros contactos como Telegram, cuenta y consentimiento existente tienen finalidades/evidencias pendientes. Si publication se selecciona también, aplica después su retirada y vaciado completo.

Mismos permisos/MFA/COI/lectura integral/proof/fuente/confirmación y UUID/replay que docs/28. Resultado cifrado añade phone_challenges_deleted/representation_invitations_deleted/phone_association_detached. rights_version/case.version incrementan; solicitud reviewing y vencimientos intactos.

## Callbacks y concurrencia

PhoneChallenge y RepresentationInvitation incorporan person_rights_version (core0014), estampado al crear. Confirmar/aceptar exige versión actual; invitación tampoco puede otorgar consentimiento a publicación suprimida. Si un callback cargó la fila antes del borrado y espera Person, vuelve a buscar el código bajo bloqueo: fila ausente produce409, sin500 ni recreación. Consultas nuevas a un código ya eliminado siguen404.

Creación de invitaciones pasa a transacción/locked_manager_person, igual que teléfono. Ambas operaciones capturan la versión de privacidad al inicio y la revalidan al adquirir bloqueo: petición iniciada antes de la supresión que espera Person retorna409, sin código nuevo. El inventario incluye versión/phone/attempts de desafíos y versión/email de invitaciones como HMAC; no muestra sus valores.

Una nueva petición explícita posterior puede crear un código con la versión actual mientras el perfil siga siendo gestionable. No se usa la supresión de tokens transitorios como prohibición permanente de consentimiento futuro. Las marcas de publicación suprimida y restricciones vigentes conservan sus guardas.

## Límites y evidencia

Pruebas PostgreSQL/Chromium registradas a continuación: borrado propio/aislamiento de teléfono de agencia y otro perfil/grants conservados; carreras de confirmación, nuevo desafío, nueva invitación y aceptación; pantalla móvil. Datos sintéticos y códigos preparados como fixture, correo/SMS solo adaptadores locales de pruebas. No canal/identidad reales ni política jurídica de retención definitiva.

Pendiente consentimiento/representación existente, información de cuenta, contacto global cuando proceda, evidencias/bloqueo/conservación/plazos, tombstones/restore/backups, destinatarios/alertas y cierre integral CR09; CR10→GS01→BF/BB→C posteriores.


CR-09 supresión de desafíos/invitaciones y redacción de asociación al teléfono: REQ-CR09-CONTACT-ERASURE-01, docs/33-supresion-contactos-invitaciones.md. contact erase borra PhoneChallenge, representation erase borra RepresentationInvitation, shared_contact_review redact desvincula Person.phone_claim/vacía teléfono-WhatsApp de revisiones propias/incrementa edit-lifecycle/limpia disponibilidad/pausa solo published. PhoneClaim global de agencia/otros perfiles y RepresentationAction/consentimiento existente conservados. Resto de contactos/free text/cuenta/evidencia pendientes; no borrado de teléfono global ni cierre integral. Same UUID/permiso/MFA/COI/proof/lecturas/fuente/epoch de executor, contadores cifrados y Case reviewing/fechas intactas.
Core0014 estampa person_rights_version en PhoneChallenge/RepresentationInvitation. Creación de invitaciones pasa a transacción y bloqueo del gestor/persona; teléfono e invitación comparan epoch inicial bajo bloqueo. Callbacks comparan epoch y vuelven a buscar fila: código eliminado mientras esperaban retorna409, no500/no recreación. Invitación no reautoriza publicación suprimida. Inventario HMAC incluye epoch/phone/attempts y email propios, sin revelar valores. Petición explícita nueva posterior puede emitir códigos actuales mientras perfil gestionable; no prohibición permanente de consentimiento futuro.
Inicial12 passed65.15s (contact_erasure/verification), ampliación23 passed158.67s (contact_erasure/erasure_execution/erasure_inventory), PostgreSQL/Chromium sin skips. Cuatro carreras reales de2 conexiones con eventos, callback confirmar/aceptar y creación teléfono/invitación empezaron antes de erasure y tras espera409/sin códigos recreados. Borrado propio/aislamiento peer/registro Claim global/grants conservados, móvil login/MFA→tres ámbitos→ejecución→GET sin resultados. Ampliación verifica códigos retenidos pero epoch obsoleto400/409; nuevo PhoneChallenge epoch2 emitido y confirmado302 por adaptador simulado local, teléfono no reaparece en revisiones. Códigos/invitaciones iniciales fueron fixtures sintéticos, ninguna verificación real de SMS/email/identidad. No sumar baterías como comúnCR09. Ruff/format/check/makemigrations/diff limpios. Claude3/3 sin nuevas llamadas.
Pendientes: consentimiento/representación actual, cuenta/contacto global cuando proceda, campos libres/evidencias/conservación-bloqueo-plazos, tombstones/restore/backups/destinatarios/alertas/respuesta final y demás CR09; CR10→GS01→BF/BB→C pendientes.

Docker contactos/invitaciones: core0014 aplicada en PG principal; app/worker/Beat reconstruidos/recreados. App confirma schema/UID10001/derechos y avisos disabled/salud Caddy200. SHA256 host/contenedor erasure_execution=08d89a6537a6f8a8f3c4d229032a3516b8568526274a50f912830c75cf658d99 y core/verification=a1de460a33c97892ded41ba5388fca5fbeca0343959fa2335aaf43adf1c11f56 coinciden. No nueva tarea ni comunicación externa verificada; producción no habilitada.
