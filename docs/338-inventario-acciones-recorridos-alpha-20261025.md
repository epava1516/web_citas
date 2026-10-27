# Inventario actualizado de acciones y recorridos — alfa, 27 de octubre de 2026

Actualización diferencial de N15, posterior al [grafo completo 503](503-n15-grafo-total-reconstruido-y-verificado-20261027.md).
El [censo actual](evidencias/inventario-acciones-actual-20261027.json) y su
[verificación](evidencias/inventario-acciones-verificacion-20261027.json) conservan
los 443 IDs originales y añaden un receptor de login nativo de Admin: **444 unidades**.
No son 444 funcionalidades enteras PASS. La [base 111](111-inventario-rendimiento-recorridos-beta-20261020.md)
y el [censo original del 25](evidencias/inventario-acciones-final-20261025.json)
permanecen intactos. Este documento y 339 anteriores pueden recuperarse con
`git show 9a32f5e:docs/338-inventario-acciones-recorridos-alpha-20261025.md`
y su equivalente 339. [Diferencial actual 339](339-diferencial-inventario-recorridos-20261025.md).

N11 tiene aceptación local por [498](498-n11-aceptacion-local-integracion-20261027.md):
11/13 bloques obligatorios. N15 sigue abierto; conserva [deuda viva](deuda-pendiente-viva.md),
N02/MOD09 diferido, N12/B14, N13/B15 y N14/B17 condicionados y QA general hasta
estable. Alpha/noindex. Este inventario no abre beta ni producción.

## Método y unidades

Censo AST nuevo,170 handlers localizados, dependencias propias acotadas a profundidad 2,
métodos/ramas observados en código, formularios, tareas, Beat, despachos, señales,
comandos,129 plantillas y tres JavaScript.641 fuentes de app/config/templates/static
y manifiestos congeladas;422 huellas de fuentes relacionadas en el censo.
No se confunden cantidades de archivos, rutas, formularios, valores y acciones.

Resolver nuevo de Django 5.2.17 con settings sintéticos y conexiones de socket/base
bloqueadas:372 filas al recorrer ES/EN,366 patrones distintos. Los 186 patrones ES
y 46 comandos coinciden exactamente con DjangoAI, cuyo backend es dummy y no
acredita esquema, migraciones ni permisos. No se hicieron peticiones, comandos
administrativos, emisiones de señales ni tareas desde este inventario.

Los doce archivos declarantes de URL/tareas conservan su contraste histórico con 111;
las declaraciones estables no garantizan igualdad transitiva. Cada una de las 443
unidades originales conserva su ID aunque cambien líneas. Sus fuentes directas
coinciden con las ya conciliadas por N11; las implementaciones respecto al 25 se
comparan por huella sin atribuir cambio funcional a todas las funciones de un archivo.

| Unidad | Cantidad actual | Límite |
| --- | --- | --- |
| Familias I01–I28 | 28 | Identidades conservadas |
| Rutas propias con nombre | 170 | 334 patrones ES/EN y comunes |
| Admin canónico | 16 | 32 patrones ES/EN; sólo auth.group |
| shared_task | 27 | No equivalen a 25 declaraciones Beat |
| Beat | 25 | 24 por defecto /25 test /0 recuperación; fuente de modo preservada |
| Comandos propios / framework | 15 /31 | Registro no ejecución; testigos N10 separados |
| Runbooks de producto/operación | 11 | No inventar ejecución por registrarlos |
| Lugares async/commit | 14 | IDs originales y expresiones conservados |
| Inscripciones propias de señales | 2 | Un bucle con 3 señales de modelo y un receptor user_logged_in |
| Plantillas / interactivas / navegación | 129 /106 /124 | Markup no acredita autorización o navegador |
| JavaScript propio | 3 | Vendor se registra por versión, no como tres scripts propios |
| Valores literales de controles | 154 | Con repeticiones y condiciones; no 154 acciones ni combinaciones válidas |

## Familias estables y disposición actual

| ID | Familia | Unidades asociadas | Asignación primaria | Disposición/límite |
| --- | --- | --- | --- | --- |
| I01 | Listado orgánico | 1 | N04 | Disposiciones acotadas por 498; sin PASS universal |
| I02 | Listado promocionado | 1 | N04 | Disposiciones acotadas por 498; sin PASS universal |
| I03 | Búsquedas y filtros | 1 | N04 | Disposiciones acotadas por 498; sin PASS universal |
| I04 | Paginación | 1 | N04 | Disposiciones acotadas por 498; sin PASS universal |
| I05 | Ficha pública | 1 | N04 | Disposiciones acotadas por 498; sin PASS universal |
| I06 | Entrega de imágenes | 5 | N05 | Disposiciones acotadas por 498; sin PASS universal |
| I07 | Favoritos | 3 | N08 | Disposiciones acotadas por 498; sin PASS universal |
| I08 | SEO y documentos públicos | 6 | N08 | Disposiciones acotadas por 498; sin PASS universal |
| I09 | Cuenta y sesión | 11 | N06, N10 | N06 + receptor Admin de N10; no concede MFA |
| I10 | Seguridad y verificación | 13 | N06 | Disposiciones acotadas por 498; sin PASS universal |
| I11 | Panel del anunciante | 2 | N06 | Disposiciones acotadas por 498; sin PASS universal |
| I12 | Edición del perfil | 6 | N06 | Disposiciones acotadas por 498; sin PASS universal |
| I13 | Subida de fotografías | 6 | N03, N07 | Disposiciones acotadas por 498; sin PASS universal |
| I14 | Procesamiento fotográfico | 4 | N03 | Disposiciones acotadas por 498; sin PASS universal |
| I15 | Gestión de fotografías | 16 | N07 | Disposiciones acotadas por 498; sin PASS universal |
| I16 | Revisión y publicación | 7 | N07 | Disposiciones acotadas por 498; sin PASS universal |
| I17 | Ciclo de vida | 3 | N07 | Disposiciones acotadas por 498; sin PASS universal |
| I18 | Agencias y representación | 18 | N06 | Disposiciones acotadas por 498; sin PASS universal |
| I19 | Gestión comercial sintética | 8 | N08 | Disposiciones acotadas por 498; sin PASS universal |
| I20 | Denuncias y reclamaciones | 18 | N09 | Disposiciones acotadas por 498; sin PASS universal |
| I21 | Derechos y rectificación | 83 | N09 | Disposiciones acotadas por 498; sin PASS universal |
| I22 | Exportación y portabilidad | 39 | N02 | N09 acotado; N02 residual/FAIL 2 s / 5 s aplazado por 367 |
| I23 | Avisos y comunicaciones | 13 | N09 | Disposiciones acotadas por 498; sin PASS universal |
| I24 | Publicación en segundo plano | 10 | N07 | Disposiciones acotadas por 498; sin PASS universal |
| I25 | Limpieza y recuperación | 52 | N09 | Disposiciones acotadas por 498; sin PASS universal |
| I26 | Navegador y entrega web | 132 | N05 | Disposiciones acotadas por 498; sin PASS universal |
| I27 | Infraestructura transversal | 11 | N10 | Disposiciones acotadas por 498; sin PASS universal |
| I28 | Operación administrativa | 76 | N10 | Disposiciones acotadas por 498; sin PASS universal |

Una unidad puede pertenecer a varias familias; la columna no se suma como censo
único. El JSON separa asignación primaria y bloques con disposiciones por unidad;
current_blocks es su unión. N02 puede figurar por una disposición diferida, sin
aceptación íntegra de la familia por cada bloque. Los presupuestos y resultados se leen en los testigos de cada bloque;
la matrizN11 no presta PASS ni latencia a métodos/roles/estados no medidos.
Se conserva el límite contractual de mezcla pública<800 ms/<1% con sus oráculos;
los objetivos 2 s/5 s de MOD09 siguen FAIL/diferidos según 367. Este censo no mide
nuevas latencias ni rebaja presupuestos.

## Rutas propias y métodos

Método vacío significa que esta función no declara allowlist mediante los
decoradores reconocidos; sus ramas y helpers están en JSON. No se presume
GET-only ni una lista universal de métodos permitidos. Las muestras N11D son
por ruta/caso: estado coincidente no demuestra haber ejecutado una rama concreta.

| ID estable | Handler actual | Guarda declarada | Familias | Muestra acotada |
| --- | --- | --- | --- | --- |
| `route:R_promotion_orders` | `apps.catalog.promotion_order_views.orders` | GET, POST | I19 | Sin muestra N11D aquí |
| `route:R_promotion_order_detail` | `apps.catalog.promotion_order_views.detail` | GET, POST | I19 | Sin muestra N11D aquí |
| `route:R_promotion_products` | `apps.catalog.promotion_views.products` | GET, POST | I19 | Sin muestra N11D aquí |
| `route:R_promotion_product_versions` | `apps.catalog.promotion_views.versions` | GET, POST | I19 | Sin muestra N11D aquí |
| `route:R_promotion_version_edit` | `apps.catalog.promotion_views.edit` | GET, POST | I19 | Sin muestra N11D aquí |
| `route:R_promotion_version_preview` | `apps.catalog.promotion_views.preview` | GET, POST | I19 | Sin muestra N11D aquí |
| `route:R_listing_lifecycle` | `apps.listings.lifecycle.panel` | GET, POST | I17 | GET 200, GET 302, GET 404, POST 302, POST 409 |
| `route:R_favorites` | `apps.listings.favorites.index` | GET | I07 | GET 200 |
| `route:R_favorite_add` | `apps.listings.favorites.add` | POST | I07 | GET 405, POST 302, POST 404 |
| `route:R_favorite_remove` | `apps.listings.favorites.remove` | POST | I07 | POST 302, POST 404 |
| `route:R_photo_appeal_queue` | `apps.listings.photo_appeals.queue` | Sin guarda explícita aquí | I15,I20 | Sin muestra N11D aquí |
| `route:R_photo_appeal_review` | `apps.listings.photo_appeals.review` | GET, POST | I15,I20 | Sin muestra N11D aquí |
| `route:R_photo_restriction` | `apps.listings.photo_restrictions.detail` | GET, POST | I15,I20 | Sin muestra N11D aquí |
| `route:R_agency_appeal_submit` | `apps.core.agency_appeals.submit` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_agency_appeal_queue` | `apps.core.agency_appeals.queue` | Sin guarda explícita aquí | I18 | Sin muestra N11D aquí |
| `route:R_agency_appeal_review` | `apps.core.agency_appeals.review` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_manager_appeal_submit` | `apps.core.manager_appeals.submit` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_manager_appeal_queue` | `apps.core.manager_appeals.queue` | Sin guarda explícita aquí | I18 | Sin muestra N11D aquí |
| `route:R_manager_appeal_review` | `apps.core.manager_appeals.review` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_appeal_submit` | `apps.listings.appeals.submit` | GET, POST | I15,I20 | Sin muestra N11D aquí |
| `route:R_appeal_queue` | `apps.listings.appeals.queue` | Sin guarda explícita aquí | I15,I20 | Sin muestra N11D aquí |
| `route:R_appeal_review` | `apps.listings.appeals.review` | GET, POST | I15,I20 | Sin muestra N11D aquí |
| `route:R_manager_queue` | `apps.core.manager_review.queue` | Sin guarda explícita aquí | I18 | Sin muestra N11D aquí |
| `route:R_manager_review` | `apps.core.manager_review.review` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_match_queue` | `apps.listings.match_views.queue` | Sin guarda explícita aquí | I16 | Sin muestra N11D aquí |
| `route:R_match_review` | `apps.listings.match_views.review` | GET, POST | I16 | Sin muestra N11D aquí |
| `route:R_match_image` | `apps.listings.match_views.image` | Sin guarda explícita aquí | I06,I16 | Sin muestra N11D aquí |
| `route:R_moderation_queue` | `apps.listings.moderation_views.queue` | Sin guarda explícita aquí | I16 | Sin muestra N11D aquí |
| `route:R_moderation_review` | `apps.listings.moderation_views.review` | GET, POST | I16 | POST 400 |
| `route:R_moderation_photo` | `apps.listings.moderation_views.review_photo` | Sin guarda explícita aquí | I06,I16 | Sin muestra N11D aquí |
| `route:R_listing_detail` | `apps.listings.moderation_views.public_detail` | Sin guarda explícita aquí | I05 | GET 200, GET 404 |
| `route:R_public_photo` | `apps.listings.moderation_views.public_photo` | Sin guarda explícita aquí | I06 | Sin muestra N11D aquí |
| `route:R_organization_queue` | `apps.core.organization_review.queue` | Sin guarda explícita aquí | I18 | Sin muestra N11D aquí |
| `route:R_organization_review` | `apps.core.organization_review.review` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_submit_revision` | `apps.listings.views.send_for_review` | POST | I12 | Sin muestra N11D aquí |
| `route:R_revision_status` | `apps.listings.views.revision_status` | Sin guarda explícita aquí | I12 | Sin muestra N11D aquí |
| `route:R_photo_reorder` | `apps.mediafiles.views.reorder` | POST | I15 | Sin muestra N11D aquí |
| `route:R_photo_upload` | `apps.mediafiles.views.upload` | POST | I13 | POST 302 |
| `route:R_private_photo` | `apps.mediafiles.views.private_photo` | Sin guarda explícita aquí | I06,I15 | GET 200, GET 302, GET 404 |
| `route:R_photo_remove` | `apps.mediafiles.views.remove` | POST | I15 | POST 302 |
| `route:R_listing_start` | `apps.listings.views.start` | POST | I12 | POST 302 |
| `route:R_draft_edit` | `apps.listings.views.edit` | GET, POST | I12 | GET 200, POST 302 |
| `route:R_individual_create` | `apps.core.verification.individual` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_person_verification` | `apps.core.verification.status` | Sin guarda explícita aquí | I10 | Sin muestra N11D aquí |
| `route:R_age_check` | `apps.core.verification.age` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_phone_start` | `apps.core.verification.phone_start` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_phone_confirm` | `apps.core.verification.phone_confirm` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_consent_invite` | `apps.core.verification.invite_consent` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_self_consent` | `apps.core.verification.self_consent` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_consent_accept` | `apps.core.verification.accept_consent` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_representation_revoke` | `apps.core.verification.revoke` | POST | I10 | Sin muestra N11D aquí |
| `route:R_representation_transfer` | `apps.core.verification.transfer` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_mfa_enroll` | `apps.core.mfa.enroll` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_mfa_challenge` | `apps.core.mfa.challenge` | GET, POST | I10 | Sin muestra N11D aquí |
| `route:R_agency_create` | `apps.core.agencies.create` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_agency_panel` | `apps.core.agencies.panel` | Sin guarda explícita aquí | I18 | Sin muestra N11D aquí |
| `route:R_agency_invite` | `apps.core.agencies.invite` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_agency_add_person` | `apps.core.agencies.add_person` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_agency_assign` | `apps.core.agencies.assign` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_agency_revoke` | `apps.core.agencies.revoke_member` | POST | I18 | Sin muestra N11D aquí |
| `route:R_agency_accept_invitation` | `apps.core.agencies.accept_invitation` | GET, POST | I18 | Sin muestra N11D aquí |
| `route:R_resend` | `apps.core.accounts.resend` | GET, POST | I09 | Sin muestra N11D aquí |
| `route:R_accept_current` | `apps.core.accounts.accept_current` | GET, POST | I09 | Sin muestra N11D aquí |
| `route:R_signup` | `apps.core.accounts.signup` | GET, POST | I09 | POST 200 |
| `route:R_login` | `apps.core.accounts.signin` | GET, POST | I09 | POST 302, POST 400 |
| `route:R_logout` | `apps.core.accounts.signout` | POST | I09 | GET 405, POST 302 |
| `route:R_recover` | `apps.core.accounts.recover` | GET, POST | I09 | Sin muestra N11D aquí |
| `route:R_account_token` | `apps.core.accounts.token_view` | GET, POST | I09 | GET 200, GET 400, POST 302, POST 400 |
| `route:R_account_email_confirmation` | `apps.safety.account_email_views.confirm` | GET, POST | I23 | Sin muestra N11D aquí |
| `route:R_account_email_confirmation_exchange` | `apps.safety.account_email_views.exchange` | GET | I23 | Sin muestra N11D aquí |
| `route:R_dashboard` | `apps.core.accounts.dashboard` | Sin guarda explícita aquí | I11 | GET 200, GET 302 |
| `route:R_legal_index` | `apps.core.legal.index` | Sin guarda explícita aquí | I08 | Sin muestra N11D aquí |
| `route:R_legal_document` | `apps.core.legal.document` | Sin guarda explícita aquí | I08 | Sin muestra N11D aquí |
| `route:R_rights_object_authorize` | `apps.safety.rights_object_views.authorize` | GET | I22 | Sin muestra N11D aquí |
| `route:R_rights_recipient_notices` | `apps.safety.communication_notice_views.inbox` | GET, POST | I23 | Sin muestra N11D aquí |
| `route:R_rights_communications` | `apps.safety.rights_communication_views.communications` | GET, POST | I23 | Sin muestra N11D aquí |
| `route:R_rights_access_close` | `apps.safety.rights_access_close_views.close_response` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_access_supplement` | `apps.safety.rights_access_supplement_views.preview` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_access_field_prepare` | `apps.safety.rights_access_field_decision_views.prepare` | POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_access_field_review` | `apps.safety.rights_access_field_decision_views.independent` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_access_scope` | `apps.safety.rights_access_scope_views.inventory` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_access_coverage_review` | `apps.safety.rights_access_coverage_review_views.review` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_publication_calendar_queue` | `apps.safety.publication_calendar_queue.queue` | GET | I21 | Sin muestra N11D aquí |
| `route:R_publication_purpose_release` | `apps.safety.publication_purpose_views.release` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_purpose_exception_review` | `apps.safety.purpose_exception_views.review` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_purpose_exception_prepare` | `apps.safety.purpose_exception_views.prepare` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_purpose_calendar_queue` | `apps.safety.purpose_calendar_views.queue` | GET | I21 | Sin muestra N11D aquí |
| `route:R_purpose_calendar_detail` | `apps.safety.purpose_calendar_views.detail` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_purpose_restriction_queue` | `apps.safety.purpose_release_views.queue` | GET | I21 | Sin muestra N11D aquí |
| `route:R_processing_prepare` | `apps.safety.processing_views.preparation` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_processing_review` | `apps.safety.processing_views.review` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_processing_execute` | `apps.safety.processing_views.execution` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_purpose_restriction_release` | `apps.safety.purpose_release_views.release` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_processing_final` | `apps.safety.processing_final_views.final` | Sin guarda explícita aquí | I21 | Sin muestra N11D aquí |
| `route:R_erasure_final` | `apps.safety.erasure_final_views.final` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rectification_final` | `apps.safety.rectification_final_views.final` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_retention_queue` | `apps.safety.retention_views.queue` | GET | I21 | Sin muestra N11D aquí |
| `route:R_retention_review` | `apps.safety.retention_views.inspect` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_recipient_assessment_review` | `apps.safety.recipient_review_views.prepare` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_recipient_assessment` | `apps.safety.recipient_assessment_views.prepare` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rectification_recipients` | `apps.safety.rectification_recipients.prepare_view` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rectification_notices` | `apps.safety.rectification_notices.inbox` | GET | I21 | Sin muestra N11D aquí |
| `route:R_rectification_notice_acknowledge` | `apps.safety.rectification_notices.acknowledge` | POST | I21 | Sin muestra N11D aquí |
| `route:R_rectification_review` | `apps.safety.rectification_review.prepare` | GET, POST | I21 | GET 200, GET 403, POST 200, POST 302, POST 403, POST 409 |
| `route:R_rights_rectification` | `apps.safety.rights_rectification.prepare` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_rectification_photo` | `apps.safety.rights_rectification.source_photo` | GET | I21 | Sin muestra N11D aquí |
| `route:R_rectification_uploads` | `apps.safety.rectification_uploads.prepare` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_erasure_execute` | `apps.safety.erasure_execution.apply` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_erasure_plan` | `apps.safety.erasure_plans.prepare` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_erasure_inventory` | `apps.safety.erasure_inventory.inspect` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_privacy_publication_hold` | `apps.safety.privacy_holds.apply` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_response` | `apps.safety.rights_responses.respond` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_media_erasure_jobs` | `apps.safety.media_operations.queue` | GET | I25 | Sin muestra N11D aquí |
| `route:R_media_erasure_recover` | `apps.safety.media_operations.recover` | GET, POST | I25 | Sin muestra N11D aquí |
| `route:R_notice_queue` | `apps.safety.notice_operations.queue` | GET | I23,I25 | Sin muestra N11D aquí |
| `route:R_notice_recover` | `apps.safety.notice_operations.recover` | GET, POST | I23,I25 | GET 200, POST 302, POST 409 |
| `route:R_complaint_photo` | `apps.safety.complaints.photo` | GET | I20 | GET 200 |
| `route:R_complaint_resolve` | `apps.safety.complaints.resolve` | GET, POST | I20 | GET 200, POST 302 |
| `route:R_complaint_create` | `apps.safety.complaints.submit` | GET, POST | I20 | GET 200, POST 302 |
| `route:R_complaint_message` | `apps.safety.complaint_messages.submit` | POST | I20 | Sin muestra N11D aquí |
| `route:R_complaint_receipt` | `apps.safety.complaints.receipt` | GET | I20 | GET 200 |
| `route:R_complaint_queue` | `apps.safety.complaints.queue` | GET | I20 | Sin muestra N11D aquí |
| `route:R_complaint_action` | `apps.safety.complaints.action` | GET, POST | I20 | GET 200, POST 302 |
| `route:R_complaint_inspect` | `apps.safety.complaints.inspect` | GET, POST | I20 | POST 200 |
| `route:R_rights_create` | `apps.safety.rights.submit` | GET, POST | I21 | GET 200, POST 302 |
| `route:R_rights_receipt` | `apps.safety.rights.receipt` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_response_acknowledge` | `apps.safety.rights_responses.acknowledge` | POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_verification` | `apps.safety.rights_verification.verification` | GET, POST | I21 | GET 200, POST 302, POST 403, POST 409 |
| `route:R_rights_image_inspect` | `apps.safety.rights_exports.inspect_image` | POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_image_download` | `apps.safety.rights_exports.download` | POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_part_download` | `apps.safety.rights_exports.download` | POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_information_review` | `apps.safety.rights_information_review_views.review` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_portability_coverage_review` | `apps.safety.rights_portability_coverage_review_views.review` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_image_coverage` | `apps.safety.rights_portability_coverage_views.prepare_image_omissions` | Sin guarda explícita aquí | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_coverage` | `apps.safety.rights_portability_coverage_views.prepare` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_images` | `apps.safety.rights_portability_image_views.prepare_images` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_export` | `apps.safety.rights_portability_export_views.prepare` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_export_job` | `apps.safety.rights_portability_export_views.job_status` | GET | I22 | Sin muestra N11D aquí |
| `route:R_rights_access_response_prepare` | `apps.safety.rights_access_response_views.prepare_response` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_access_response_review` | `apps.safety.rights_access_response_views.review_response` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_portability_response_prepare` | `apps.safety.rights_portability_response_views.prepare_response` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_response_review` | `apps.safety.rights_portability_response_views.review_response` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_response_close` | `apps.safety.rights_portability_response_views.close_response` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_select` | `apps.safety.rights_portability_prepare_selection_views.prepare` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_image_inspect` | `apps.safety.rights_portability_selection_views.inspect_image` | POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_selection_review` | `apps.safety.rights_portability_selection_views.review` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_review` | `apps.safety.rights_portability_review_views.review` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_portability_prepare` | `apps.safety.rights_portability_views.prepare` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_copy_information_prepare` | `apps.safety.rights_copy_information_views.prepare` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_rights_export_prepare` | `apps.safety.rights_exports.prepare` | GET, POST | I22 | Sin muestra N11D aquí |
| `route:R_rights_export_download` | `apps.safety.rights_exports.download` | POST | I22 | Sin muestra N11D aquí |
| `route:R_photo_reuse_queue` | `apps.safety.photo_reintroduction_views.queue` | Sin guarda explícita aquí | I21 | Sin muestra N11D aquí |
| `route:R_photo_reuse_review` | `apps.safety.photo_reintroduction_views.review` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_photo_reuse_image` | `apps.safety.photo_reintroduction_views.image` | Sin guarda explícita aquí | I06,I25 | Sin muestra N11D aquí |
| `route:R_rights_queue` | `apps.safety.rights.queue` | GET | I21 | Sin muestra N11D aquí |
| `route:R_rights_action` | `apps.safety.rights.action` | GET, POST | I21 | GET 200, POST 302 |
| `route:R_rights_inspect` | `apps.safety.rights.inspect` | GET, POST | I21 | POST 200 |
| `route:R_report_decision` | `apps.safety.views.decision` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_report_inspect` | `apps.safety.views.inspect` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_report_create` | `apps.safety.views.submit` | GET, POST | I21 | GET 200, POST 302, POST 400, POST 409 |
| `route:R_report_receipt` | `apps.safety.views.receipt` | GET | I21 | GET 200, GET 404 |
| `route:R_report_queue` | `apps.safety.views.queue` | GET | I21 | Sin muestra N11D aquí |
| `route:R_privacy_hold_release` | `apps.safety.privacy_release.review` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_urgent_report_alerts` | `apps.safety.urgent_alerts.queue` | GET, POST | I21 | Sin muestra N11D aquí |
| `route:R_health` | `apps.core.views.health` | Sin guarda explícita aquí | I27,I28 | Sin muestra N11D aquí |
| `route:R_robots` | `apps.core.sitemaps.robots` | GET, HEAD | I08 | Sin muestra N11D aquí |
| `route:R_sitemap_index` | `apps.core.sitemaps.index` | GET, HEAD | I08 | Sin muestra N11D aquí |
| `route:R_sitemap_directory` | `apps.core.sitemaps.directory` | GET, HEAD | I08 | Sin muestra N11D aquí |
| `route:R_sitemap_listings` | `apps.core.sitemaps.listings` | GET, HEAD | I08 | Sin muestra N11D aquí |
| `route:R_home` | `apps.core.views.home` | Sin guarda explícita aquí | I01,I02,I03,I04 | GET 200, GET 400, GET 404 |

## Tareas y cadencias

| ID estable | Fuente actual | Línea | Familias |
| --- | --- | --- | --- |
| `task:T_apps.catalog.tasks.bump_promotions` | `apps/catalog/tasks.py` | 10 | I19 |
| `task:T_apps.listings.tasks.expire_listings` | `apps/listings/tasks.py` | 41 | I17,I24 |
| `task:T_apps.listings.tasks.refresh_publication_state` | `apps/listings/tasks.py` | 51 | I24 |
| `task:T_apps.listings.tasks.sweep_publication_state` | `apps/listings/tasks.py` | 66 | I24 |
| `task:T_apps.mediafiles.tasks.process_blob` | `apps/mediafiles/tasks.py` | 9 | I13,I14 |
| `task:T_apps.mediafiles.tasks.recover_media_jobs` | `apps/mediafiles/tasks.py` | 14 | I15,I25 |
| `task:T_apps.mediafiles.tasks.erase_media_files` | `apps/mediafiles/tasks.py` | 40 | I15,I25 |
| `task:T_apps.mediafiles.tasks.cleanup_prepared_media` | `apps/mediafiles/tasks.py` | 47 | I15,I25 |
| `task:T_apps.safety.rights_object_content.purge_orphan_export_objects` | `apps/safety/rights_object_content.py` | 185 | I22,I25 |
| `task:T_apps.safety.rights_object_delivery.purge_object_deliveries` | `apps/safety/rights_object_delivery.py` | 313 | I22,I25 |
| `task:T_apps.safety.tasks.deliver_safety_notices` | `apps/safety/tasks.py` | 9 | I23 |
| `task:T_apps.safety.tasks.reconcile_urgent_report_alerts` | `apps/safety/tasks.py` | 16 | I20,I23 |
| `task:T_apps.safety.tasks.purge_expired_exports` | `apps/safety/tasks.py` | 31 | I21,I25 |
| `task:T_apps.safety.tasks.purge_expired_account_confirmation_delivery` | `apps/safety/tasks.py` | 50 | I21,I25 |
| `task:T_apps.safety.tasks.reconcile_retention_reviews` | `apps/safety/tasks.py` | 57 | I21,I25 |
| `task:T_apps.safety.tasks.purge_expired_copy_page_reviews` | `apps/safety/tasks.py` | 64 | I21,I25 |
| `task:T_apps.safety.tasks.purge_expired_copy_information` | `apps/safety/tasks.py` | 82 | I21,I25 |
| `task:T_apps.safety.tasks.purge_expired_portability_assessments` | `apps/safety/tasks.py` | 100 | I22,I25 |
| `task:T_apps.safety.tasks.purge_expired_portability_selections` | `apps/safety/tasks.py` | 118 | I22,I25 |
| `task:T_apps.safety.tasks.purge_expired_portability_coverage` | `apps/safety/tasks.py` | 136 | I22,I25 |
| `task:T_apps.safety.tasks.purge_expired_portability_response_drafts` | `apps/safety/tasks.py` | 154 | I22,I25 |
| `task:T_apps.safety.tasks.purge_expired_access_response_drafts` | `apps/safety/tasks.py` | 172 | I21,I25 |
| `task:T_apps.safety.tasks.purge_expired_access_coverage` | `apps/safety/tasks.py` | 194 | I21,I25 |
| `task:T_apps.safety.tasks.purge_expired_access_scope_inventory` | `apps/safety/tasks.py` | 212 | I21,I25 |
| `task:T_apps.safety.tasks.purge_expired_access_field_decision` | `apps/safety/tasks.py` | 230 | I21,I25 |
| `task:T_apps.safety.tasks.generate_portability_export` | `apps/safety/tasks.py` | 254 | I22 |
| `task:T_apps.safety.tasks.reconcile_portability_export_jobs` | `apps/safety/tasks.py` | 261 | I22,I25 |

El JSON registra decoradores, políticas, llamadas y 25 cadencias. Cola, eager,
Task.run, worker real y Beat conservan sus diferencias de evidencia. Callback
on_commit no prueba que el consumidor o proveedor haya terminado.

## Despachos e inscripciones de señales

| ID estable | Ubicación actual | Declaración |
| --- | --- | --- |
| `dispatch:0:apps/core/accounts.py:235` | `apps/core/accounts.py`:235 | `transaction.on_commit(lambda: send_token(user, 'verify', request.LANGUAGE_CODE))` |
| `dispatch:1:apps/listings/publication_signals.py:17` | `apps/listings/publication_signals.py`:17 | `refresh_publication_state.delay()` |
| `dispatch:2:apps/listings/publication_signals.py:33` | `apps/listings/publication_signals.py`:33 | `transaction.on_commit(_enqueue_refresh, robust=True)` |
| `dispatch:3:apps/listings/revisions.py:54` | `apps/listings/revisions.py`:54 | `transaction.on_commit(lambda blob_id=blob_id: process_blob.delay(blob_id), robust=True)` |
| `dispatch:4:apps/listings/revisions.py:54` | `apps/listings/revisions.py`:54 | `process_blob.delay(blob_id)` |
| `dispatch:5:apps/mediafiles/services.py:121` | `apps/mediafiles/services.py`:127 | `transaction.on_commit(lambda: process_blob.delay(str(blob.pk)), robust=True)` |
| `dispatch:6:apps/mediafiles/services.py:121` | `apps/mediafiles/services.py`:127 | `process_blob.delay(str(blob.pk))` |
| `dispatch:7:apps/mediafiles/tasks.py:30` | `apps/mediafiles/tasks.py`:36 | `process_blob.delay(str(blob_id))` |
| `dispatch:8:apps/safety/rectification_execution.py:326` | `apps/safety/rectification_execution.py`:337 | `transaction.on_commit(lambda blob_id=blob_id: process_blob.delay(blob_id), robust=True)` |
| `dispatch:9:apps/safety/rectification_execution.py:327` | `apps/safety/rectification_execution.py`:338 | `process_blob.delay(blob_id)` |
| `dispatch:10:apps/safety/rectification_uploads.py:179` | `apps/safety/rectification_uploads.py`:196 | `transaction.on_commit(lambda: process_blob.delay(str(blob.pk)), robust=True)` |
| `dispatch:11:apps/safety/rectification_uploads.py:179` | `apps/safety/rectification_uploads.py`:196 | `process_blob.delay(str(blob.pk))` |
| `dispatch:12:apps/safety/rights_portability_jobs.py:151` | `apps/safety/rights_portability_jobs.py`:151 | `transaction.on_commit(lambda: dispatch(job.pk), robust=True)` |
| `dispatch:13:apps/safety/rights_portability_jobs.py:160` | `apps/safety/rights_portability_jobs.py`:160 | `generate_portability_export.apply_async(args=[str(job_id)], ignore_result=True)` |
| `signal_connection:0` | `apps/listings/apps.py`:14 | `signal.connect(schedule_refresh, dispatch_uid=f'publication_state_{signal!r}')` |
| `signal_connection:user_logged_in:apps.core.admin.bind_admin_login_epoch` | `apps/core/admin.py`:15 | `receiver(user_logged_in, sender=User, dispatch_uid='core.admin.bind_account_epoch')` |

`signal_connection:0` sigue identificando el bucle de publicación, aunque aparece
en la posición 1 del escáner actual. Tres eventos no son tres inscripciones de
fuente. El nuevo receptor tiene ID
`signal_connection:user_logged_in:apps.core.admin.bind_admin_login_epoch`.
Se limita a POST del login nativo de Admin y copia session_version a account_version;
no concede MFA ni permisos. Fuente actual ligada a los testigos N10 ya aceptados,
sin emitir la señal de nuevo aquí. Las plantillas SQL de triggers son fuente,
no un censo de triggers aplicados a una base viva.

## Admin nativo y acciones

Sólo auth.group, con implementación actual `apps.core.admin.CurrentGroupAdmin`.
El módulo propio no existía en el corte N00. Se conservan 16 IDs/patrones canónicos;
la implementación y sus guardas han cambiado, no el número de URL. N10 verificó
casos propios de Group y autoridad fresca; registro no significa que todas las
ramas de las 16 superficies sean PASS. Este inventario no ejecuta CRUD o acciones.

| ID estable | Callback registrado | Patrones ES/EN |
| --- | --- | --- |
| `admin_pattern:A_admin:index` | `django.contrib.admin.sites.AdminSite.index` | `en/admin/`; `es/admin/` |
| `admin_pattern:A_admin:login` | `django.contrib.admin.sites.AdminSite.login` | `en/admin/login/`; `es/admin/login/` |
| `admin_pattern:A_admin:logout` | `django.contrib.admin.sites.AdminSite.logout` | `en/admin/logout/`; `es/admin/logout/` |
| `admin_pattern:A_admin:password_change` | `django.contrib.admin.sites.AdminSite.password_change` | `en/admin/password_change/`; `es/admin/password_change/` |
| `admin_pattern:A_admin:password_change_done` | `django.contrib.admin.sites.AdminSite.password_change_done` | `en/admin/password_change/done/`; `es/admin/password_change/done/` |
| `admin_pattern:A_admin:autocomplete` | `django.contrib.admin.sites.AdminSite.autocomplete_view` | `en/admin/autocomplete/`; `es/admin/autocomplete/` |
| `admin_pattern:A_admin:jsi18n` | `django.contrib.admin.sites.AdminSite.i18n_javascript` | `en/admin/jsi18n/`; `es/admin/jsi18n/` |
| `admin_pattern:A_admin:view_on_site` | `django.contrib.contenttypes.views.shortcut` | `en/admin/r/<path:content_type_id>/<path:object_id>/`; `es/admin/r/<path:content_type_id>/<path:object_id>/` |
| `admin_pattern:A_admin:auth_group_changelist` | `django.contrib.admin.options.ModelAdmin.changelist_view` | `en/admin/auth/group/`; `es/admin/auth/group/` |
| `admin_pattern:A_admin:auth_group_add` | `django.contrib.admin.options.ModelAdmin.add_view` | `en/admin/auth/group/add/`; `es/admin/auth/group/add/` |
| `admin_pattern:A_admin:auth_group_history` | `django.contrib.admin.options.ModelAdmin.history_view` | `en/admin/auth/group/<path:object_id>/history/`; `es/admin/auth/group/<path:object_id>/history/` |
| `admin_pattern:A_admin:auth_group_delete` | `django.contrib.admin.options.ModelAdmin.delete_view` | `en/admin/auth/group/<path:object_id>/delete/`; `es/admin/auth/group/<path:object_id>/delete/` |
| `admin_pattern:A_admin:auth_group_change` | `django.contrib.admin.options.ModelAdmin.change_view` | `en/admin/auth/group/<path:object_id>/change/`; `es/admin/auth/group/<path:object_id>/change/` |
| `admin_pattern:A_unnamed_34b71d47a538` | `django.views.generic.base.View.as_view.<locals>.view` | `en/admin/auth/group/<path:object_id>/`; `es/admin/auth/group/<path:object_id>/` |
| `admin_pattern:A_admin:app_list` | `django.contrib.admin.sites.AdminSite.app_index` | `en/admin/^(?P<app_label>auth)/$`; `es/admin/^(?P<app_label>auth)/$` |
| `admin_pattern:A_unnamed_4dc81e24708e` | `django.contrib.admin.sites.AdminSite.catch_all_view` | `en/admin/(?P<url>.*)$`; `es/admin/(?P<url>.*)$` |

El registro global mantiene delete_selected; el modelo Group declara su override
en CurrentGroupAdmin. La disponibilidad efectiva depende de la petición y los
permisos actuales. El registro no equivale a ejecutar esa acción ni sus confirmaciones.

## Comandos y operaciones

| ID estable | Fuente |
| --- | --- |
| `own_command:import_geography` | `apps/catalog/management/commands/import_geography.py` |
| `own_command:seed_catalog` | `apps/catalog/management/commands/seed_catalog.py` |
| `own_command:bootstrap` | `apps/core/management/commands/bootstrap.py` |
| `own_command:encryption_key_inventory` | `apps/core/management/commands/encryption_key_inventory.py` |
| `own_command:operational_assessment` | `apps/core/management/commands/operational_assessment.py` |
| `own_command:operational_events_report` | `apps/core/management/commands/operational_events_report.py` |
| `own_command:operational_snapshot` | `apps/core/management/commands/operational_snapshot.py` |
| `own_command:seed_demo` | `apps/core/management/commands/seed_demo.py` |
| `own_command:refresh_publication_state` | `apps/listings/management/commands/refresh_publication_state.py` |
| `own_command:apply_recovery_ledger` | `apps/safety/management/commands/apply_recovery_ledger.py` |
| `own_command:check_recovery_ledger` | `apps/safety/management/commands/check_recovery_ledger.py` |
| `own_command:clear_recovery_sessions` | `apps/safety/management/commands/clear_recovery_sessions.py` |
| `own_command:configure_rights_evidence_role` | `apps/safety/management/commands/configure_rights_evidence_role.py` |
| `own_command:initialize_rights_runtime` | `apps/safety/management/commands/initialize_rights_runtime.py` |
| `own_command:restore_publication_calendar` | `apps/safety/management/commands/restore_publication_calendar.py` |

Los 31 comandos framework, sus fuentes y disposiciones están en JSON. Ningún
handle se ejecuta desde este censo; las selecciones N10 anteriores son acotadas.

| ID estable | Operación |
| --- | --- |
| `runbook:O_STARTUP` | Inicio/parada y comprobación de servicios locales |
| `runbook:O_WORKER_BROKER` | Recuperación de worker/broker y outbox |
| `runbook:O_ENCRYPTION` | Transición de cifrado y lectores retenidos |
| `runbook:O_DJANGO_SIGNING` | Rotación de firma Django y consumidores |
| `runbook:O_PG_CREDENTIAL` | Rotación y reconexión de credencial PostgreSQL |
| `runbook:O_REDIS_CREDENTIAL` | Rotación Redis/Kombu y continuidad de cola |
| `runbook:O_PROXY_SECRET` | Recarga del secreto del proxy Caddy |
| `runbook:O_RESTORE` | Copia/pg_dump/pg_restore/medios y reconciliación |
| `runbook:O_RUNTIME_RETURN` | Retorno y vuelta entre versiones de runtime |
| `runbook:O_DOMAIN_INCIDENT` | Incidente y revocación de clave HMAC de dominio |
| `runbook:O_URGENT_WITHDRAWAL` | Retirada urgente, escalado y sustitución local |

Las cinco obligaciones de cierre N15 constan en contract_closeout_controls,
separadas de las 444 unidades de producto/operación: grafo, diferencial, relevo
frontend, resumen externo y purga final. Esta última permanece pendiente en el
corte técnico y su ejecución se acreditará por la constancia terminal del resumen;
no se da por realizada antes de borrar.

## Base de frontend y límites

Las 129 plantillas y tres scripts propios quedan indexados por fuente, hash,
formularios/controles, referencias URL, navegación/recursos y atributos HTMX.
La versión vendorizada observada es htmx 2.0.11. La dirección Django Templates/htmx 4
pertenece al siguiente contrato; no se implementa ni migra aquí.

El relevo final añadirá contratos por entrada/estado/respuesta/efecto y referencias
al insumo estático verificado, sin convertirlo en QA de navegador, accesibilidad
o todas las ramas. Fuente esperada, observación con versión y no ejecutado son
campos distintos. Las condiciones dinámicas no se sustituyen por combinaciones
cartesianas de valores. Autenticación no elimina revisión de autorización,
IDOR, revocación o permiso actual antes del efecto.

Última acción del contrato: purga completa de artifacts después del acta/Git y
resumen externo. No borra docs/evidencias, fuentes, Git, datos, volúmenes o servicios.
Las referencias a brutos eliminados serán históricas. Alpha/noindex y deuda viva
permanecen; el inventario actualizado no declara N15 ni el objetivo completos.
