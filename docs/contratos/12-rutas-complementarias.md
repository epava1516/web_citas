# Contrato complementario de rutas — inventario GS01

Fecha: 2026-10-10. Fuente: extracción del código en `4fa657e` (resolución de URLs, decoradores de las vistas, formularios instanciados, códigos HTTP explícitos y permisos comprobados en el cuerpo). Completa las rutas que no aparecían en los contratos `00`–`11`; no cambia comportamiento ni sustituye las pruebas. Las rutas de administración de Django quedan fuera por ser interfaz del framework con su propio control de permisos. La semántica funcional de cada flujo se describe en los documentos de derechos/comunicaciones enlazados desde [contratos10](10-denuncias-derechos.md) y [seguimiento17](../17-seguimiento-desarrollo.md).

Convenciones: los prefijos `es/`/`en/` son equivalentes; «sesión» significa `login_required` y la vista comprueba además autorización de objeto; las cabeceras de caché de cada vista se verifican en sus pruebas de flujo. Los códigos listados son los explícitos en la vista; los errores de validación de formulario devuelven la misma página con errores de campo. Ninguna vista del proyecto usa `csrf_exempt`: el middleware CSRF de Django se aplica a todo POST.

| Nombre | Ruta | Métodos | Acceso | Vista | Formularios | Códigos explícitos | Permiso explícito |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `rights_recipient_notices` | `es/account/rights-notices/` | GET/POST | sesión | `apps.safety.communication_notice_views.inbox` | NoticeForm | 403 | — |
| `rights_communications` | `es/moderation/rights/<uuid:case_id>/communications/` | GET/POST | sesión | `apps.safety.rights_communication_views.communications` | CommunicationForm | 403 | — |
| `rights_access_close` | `es/rights/<uuid:case_id>/access/close/<int:review_id>/` | GET/POST | sesión | `apps.safety.rights_access_close_views.close_response` | CloseForm | 403 | safety.respond_rights_request |
| `rights_access_supplement` | `es/rights/<uuid:case_id>/access/scope/<int:inventory_id>/supplement/` | GET/POST | sesión | `apps.safety.rights_access_supplement_views.preview` | SupplementForm | 403,409 | — |
| `rights_access_field_prepare` | `es/rights/<uuid:case_id>/access/scope/<int:inventory_id>/decision/` | GET | sesión | `apps.safety.rights_access_field_decision_views.prepare` | ProposalForm | 403 | — |
| `rights_access_field_review` | `es/rights/<uuid:case_id>/access/decision/<int:decision_id>/` | GET/POST | sesión | `apps.safety.rights_access_field_decision_views.independent` | DecisionForm,ReviewForm | 403,409 | — |
| `rights_access_scope` | `es/rights/<uuid:case_id>/access/scope/` | GET/POST | sesión | `apps.safety.rights_access_scope_views.inventory` | ProposalForm,ScopeForm | 403,409 | — |
| `rights_access_coverage_review` | `es/moderation/rights/<uuid:case_id>/access/coverage/<int:coverage_id>/review/` | GET/POST | sesión | `apps.safety.rights_access_coverage_review_views.review` | DecisionForm,ReviewForm | 403,409 | — |
| `rectification_recipients` | `es/moderation/rights/<uuid:case_id>/rectification-execution/<int:execution_id>/recipients/` | GET/POST | sesión | `apps.safety.rectification_recipients.prepare_view` | InventoryForm | 403 | — |
| `rectification_notices` | `es/account/correction-notices/` | GET | sesión | `apps.safety.rectification_notices.inbox` | — | 403 | — |
| `rectification_notice_acknowledge` | `es/account/correction-notices/<int:notice_id>/acknowledge/` | POST | sesión | `apps.safety.rectification_notices.acknowledge` | — | 403 | — |
| `rectification_review` | `es/moderation/rights/<uuid:case_id>/rectification/<int:proposal_id>/review/` | GET/POST | sesión | `apps.safety.rectification_review.prepare` | ReviewForm | 403 | — |
| `media_erasure_recover` | `es/moderation/rights/<uuid:case_id>/media-jobs/<int:job_id>/` | GET/POST | sesión | `apps.safety.media_operations.recover` | RecoveryForm | — | — |
| `complaint_photo` | `es/moderation/complaints/<uuid:complaint_id>/photo/<uuid:photo_id>/` | GET | sesión | `apps.safety.complaints.photo` | — | 403,409 | listings.review_listing |
| `complaint_resolve` | `es/moderation/complaints/<uuid:complaint_id>/resolve/` | GET/POST | sesión | `apps.safety.complaints.resolve` | ResolutionForm | 403 | safety.resolve_complaint |
| `complaint_message` | `es/safety/complaints/<uuid:complaint_id>/<str:secret>/message/` | POST | recibo/token secreto sin sesión | `apps.safety.complaint_messages.submit` | MessageForm | 400,409,429 | — |
| `rights_response_acknowledge` | `es/safety/rights/<uuid:case_id>/<str:secret>/response/<int:response_id>/acknowledge/` | POST | recibo/token secreto sin sesión | `apps.safety.rights_responses.acknowledge` | — | 400 | — |
| `rights_portability_coverage_review` | `es/moderation/rights/<uuid:case_id>/portability/coverage/<int:coverage_id>/review/` | GET/POST | sesión | `apps.safety.rights_portability_coverage_review_views.review` | DecisionForm,PageForm | 403 | — |
| `rights_access_response_prepare` | `es/moderation/rights/<uuid:case_id>/access/response/` | GET/POST | sesión | `apps.safety.rights_access_response_views.prepare_response` | DraftForm | 403,409 | — |
| `rights_access_response_review` | `es/moderation/rights/<uuid:case_id>/access/response/<int:draft_id>/review/` | GET/POST | sesión | `apps.safety.rights_access_response_views.review_response` | DecisionForm,ReviewForm | 403 | — |
| `photo_reuse_queue` | `es/moderation/photo-reuse/` | GET | sesión | `apps.safety.photo_reintroduction_views.queue` | — | — | — |
| `photo_reuse_review` | `es/moderation/photo-reuse/<int:candidate_id>/` | GET/POST | sesión | `apps.safety.photo_reintroduction_views.review` | AuditForm,DecisionForm | 400,409 | — |
| `photo_reuse_image` | `es/moderation/photo-reuse/<int:candidate_id>/reads/<int:read_id>/<str:side>/` | GET | sesión | `apps.safety.photo_reintroduction_views.image` | — | — | — |
| `privacy_hold_release` | `es/moderation/rights/<uuid:case_id>/publication-hold/release/` | GET/POST | sesión | `apps.safety.privacy_release.review` | ReleaseForm | 403,409 | safety.execute_rights_request + safety.review_privacy_hold + safety.respond_rights_request (en vista) |
| `account_email_confirmation` | `es/safety/account-email-confirm/<uuid:confirmation_id>/` | GET/POST | recibo/token secreto sin sesión | `apps.safety.account_email_views.confirm` | ConfirmationForm | 400,429 | — |
| `account_email_confirmation_exchange` | `es/safety/account-email/<uuid:confirmation_id>/<str:raw>/` | GET | recibo/token secreto sin sesión | `apps.safety.account_email_views.exchange` | — | 400 | — |
| `match_image` | `es/moderation/matches/<int:match_id>/<str:side>/image/` | GET | sesión | `apps.listings.match_views.image` | — | 403,404 | listings.review_listing + MFA de sesión vigente; sin conflicto de interés |
| `recipient_assessment` | `es/moderation/rights/<uuid:case_id>/recipient-inventory/<int:inventory_id>/assessment/` | GET/POST | sesión | `apps.safety.recipient_assessment_views.prepare` | AccessForm | 400,403 | ver [contratos10](10-denuncias-derechos.md) |
| `rights_portability_image_coverage` | `es/moderation/rights/<uuid:case_id>/portability/coverage/images/` | GET/POST | sesión | `apps.safety.rights_portability_coverage_views.prepare_image_omissions` | (misma vista que `rights_portability_coverage`) | 403,409 | ver [contratos10](10-denuncias-derechos.md) |
| `dashboard` | `es/account/` | GET | sesión | `apps.core.accounts.dashboard` | — | — | — |
| `legal_index` | `es/legal/` | GET | público | `apps.core.legal.index` | — | — | — |
| `robots` | `robots.txt` | GET | público | `apps.core.sitemaps.robots` | — | — | — |
| `sitemap_index` | `sitemap.xml` | GET | público | `apps.core.sitemaps.index` | — | 503 | — |
| `sitemap_directory` | `sitemaps/directory.xml` | GET | público | `apps.core.sitemaps.directory` | — | — | — |
| `sitemap_listings` | `sitemaps/listings/<int:page>.xml` | GET | público | `apps.core.sitemaps.listings` | — | — | — |

## Límites

- Inventario estructural verificable por código; las garantías de autorización, frescura, idempotencia y privacidad de cada operación están en sus contratos funcionales y pruebas, no en esta tabla.
- `robots`/`sitemap*`: `require_safe`; `sitemap_index` puede responder 503 cuando no hay datos de sitemap disponibles. Reglas de indexación: [SEO/sitemaps](../evidencias/sitemaps-preparacion0110.json).
- Cualquier ruta nueva debe añadirse aquí o en su contrato de flujo antes de GS01. `tests/test_route_inventory.py` lo exige: cada patrón de `urls.py` (salvo `admin/`) debe aparecer en `docs/contratos/` o en un documento de flujo de `docs/`; la comprobación se repite al emitir el acta.
