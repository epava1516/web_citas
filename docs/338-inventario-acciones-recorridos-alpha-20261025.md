# Inventario actualizado de acciones y recorridos — alfa, 25 de octubre de 2026

Versión actualizada separada de la [base111](111-inventario-rendimiento-recorridos-beta-20261020.md), que permanece intacta. Conserva I01–I28 y se acompaña del [diferencial339](339-diferencial-inventario-recorridos-20261025.md) y de la [matriz legible por máquina](evidencias/inventario-acciones-final-20261025.json). Se realiza después de la [reconstrucción completa del grafo](evidencias/grafo-final-reconstruccion-20261025.json), conforme a la adenda del contrato16.

El proyecto permanece en alfa. B16 tiene aceptación local por acta22; B14/B15/B17 se difieren según336, sin convertirse en PASS. Este inventario está completado en el alcance declarado; sus estados parciales se refieren a cobertura funcional o medición de cada escenario, no a una reapertura automática de las aceptaciones locales.

## Método y unidades

Censo AST de declaraciones de URL, funciones, decoradores de método, controles de formularios, llamadas propias hasta profundidad dos, tareas, despachos y comandos. Registro de URL de Django5.2.17 inspeccionado con conexiones de socket y de base de datos bloqueadas, configuración sintética explícita, sin ejecutar peticiones ni comandos administrativos. La expansión del registro no es prueba funcional de Admin.

Son 170 declaraciones con nombre de la aplicación y 27 tareas `shared_task`, igual que en la base. Los doce archivos que definen ambas superficies coinciden por bytes con el testigo de fuentes20261020-111928-b91538fc citado por111. Esto acredita identidad de esas declaraciones, no de todos sus servicios transitivos ni de la hora exacta de revisión manual de111.

Las 170 declaraciones producen334 patrones de aplicación al considerar ES/EN y no duplicar las seis rutas sin idioma. Admin añade16 patrones canónicos,32 con idiomas:366 patrones distintos en total. Son patrones con parámetros, no un número finito de URLs concretas o de funcionalidades. El barrido de dos idiomas devuelve372 filas antes de deduplicar esas seis rutas comunes.

Además:15 comandos propios,25 declaraciones de Beat,14 lugares de despacho/callback de commit, tres tipos de señales de modelo,106 plantillas con formularios/controles/HTMX y tres JavaScript propios. Hay154 valores de controles de formulario asociados a rutas, con repeticiones: no son154 acciones de negocio independientes ni un producto cartesiano válido. Estos recuentos representan unidades diferentes y no se suman.

## Matriz estable I01–I28

Cada familia enlaza contrato14/16 y los puntos indicados del roadmap103. La matriz JSON vincula cada ruta, tarea o comando con fuentes, líneas, huellas, dependencias relevantes y evidencia familiar. La cobertura de una familia no adjudica PASS a todos sus métodos, estados o valores de control. «Parcial» conserva ese límite.

| ID | Familia | Roadmap | Evidencia y límite de medición |
| --- | --- | --- | --- |
| I01 | Listado orgánico | B07/B08/B16 | [318](318-matriz-rutas-vigente-b16-20261024.md), [330](330-conciliacion-exclusiones-b16-20261024.md), [332](332-auditoria-http-corto-b16-20261025.md), [334](334-auditoria-http-contractual-b16-20261025.md). Mezcla vigente y oráculos; no p95 exclusivo de listado ni todas las poblaciones. |
| I02 | Listado promocionado | B07/B08/B16 | [318](318-matriz-rutas-vigente-b16-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md), [330](330-conciliacion-exclusiones-b16-20261024.md), [332](332-auditoria-http-corto-b16-20261025.md), [334](334-auditoria-http-contractual-b16-20261025.md). Promociones sintéticas; prioridad/páginas/autoridad, no compra ni autosubida bajo toda carga. |
| I03 | Búsquedas y filtros | B07/B08/B16 | [318](318-matriz-rutas-vigente-b16-20261024.md), [330](330-conciliacion-exclusiones-b16-20261024.md), [332](332-auditoria-http-corto-b16-20261025.md), [334](334-auditoria-http-contractual-b16-20261025.md). Combinaciones ciudad/perfil/idioma/texto con oráculo; no producto cartesiano de todos los filtros. |
| I04 | Paginación | B07/B08/B16 | [318](318-matriz-rutas-vigente-b16-20261024.md), [330](330-conciliacion-exclusiones-b16-20261024.md), [334](334-auditoria-http-contractual-b16-20261025.md). Páginas inicial/intermedia/última y vacíos; no todas las páginas grandes ni p95 por página. |
| I05 | Ficha pública | B02/B03/B07/B16 | [105](105-adaptacion-perfil-beta-b02b03-20261020.md), [329](329-revision-semantica-testigos-b16-20261024.md), [330](330-conciliacion-exclusiones-b16-20261024.md), [334](334-auditoria-http-contractual-b16-20261025.md). Ficha participa en tercios de mezcla; agregado no equivale a p95 individual. |
| I06 | Entrega de imágenes | B03/B09/B16 | [305](305-seleccion-sql-cola-denuncias-b09-20261024.md), [306](306-diagnostico-entrega-galeria-b09-20261024.md), [307](307-conciliacion-lectura-entrega-b09-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md). Entrega/privacidad y carga inicial de galería; sin presupuesto universal de transferencia o red. |
| I07 | Favoritos | B03/B16 | [329](329-revision-semantica-testigos-b16-20261024.md). Exposición y retirada en favoritos con tercero intacto; sin presupuesto individual de latencia. |
| I08 | SEO y documentos públicos | B02/B03/B16 | [105](105-adaptacion-perfil-beta-b02b03-20261020.md), [329](329-revision-semantica-testigos-b16-20261024.md). Textos versionados, superficies y SEO locales; textos sintéticos no revisión jurídica ni medición de cada sitemap. |
| I09 | Cuenta y sesión | B00/B02/B03/B16 | [105](105-adaptacion-perfil-beta-b02b03-20261020.md), [299](299-autoridad-cobertura-conciliacion-b00-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md). Autoridad de cuenta/sesión y aceptación vigentes en escenarios; sin entrega de identidad externa real. |
| I10 | Seguridad y verificación | B00/B14/B16 | [299](299-autoridad-cobertura-conciliacion-b00-20261024.md), [312](312-guardia-inicio-contacto-b14-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md). Guardias locales/MFA y rechazo de simuladores; proveedores reales no elegidos ni integrados. |
| I11 | Panel del anunciante | B02/B03/B16 | [105](105-adaptacion-perfil-beta-b02b03-20261020.md), [329](329-revision-semantica-testigos-b16-20261024.md). Panel/perfil simple, navegación y actores probados; no presupuesto de cada cardinalidad de panel. |
| I12 | Edición del perfil | B02/B03/B11/B16 | [105](105-adaptacion-perfil-beta-b02b03-20261020.md), [311](311-interfaz-formularios-copia-b11-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md). Perfil romántico, rechazo de campos profesionales e historia privada preservada; UI/autoridad no p95 de guardado. |
| I13 | Subida de fotografías | B03/B07/B10/B16 | [327](327-escenarios-crecimiento-densidad-similitud-b10-20261024.md), [328](328-conciliacion-exportacion-similitud-b10-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md), [334](334-auditoria-http-contractual-b16-20261025.md). 15subidas302conPhoto/UploadAttempt en borradores distintos; no procesamiento asíncrono entero desde302. |
| I14 | Procesamiento fotográfico | B10/B16 | [327](327-escenarios-crecimiento-densidad-similitud-b10-20261024.md), [328](328-conciliacion-exportacion-similitud-b10-20261024.md). Detector1000Blob/5positivos3,20s y100densos14,39s; no80koriginales, ingestión/cola completa o índice adoptado. |
| I15 | Gestión de fotografías | B03/B06/B16 | [329](329-revision-semantica-testigos-b16-20261024.md). Fotos WEBP/sinEXIF, lectura privada/retirada/revisión por escenarios; no medición completa de transferencia/ordenación. |
| I16 | Revisión y publicación | B02/B03/B06/B16 | [105](105-adaptacion-perfil-beta-b02b03-20261020.md), [317](317-registros-historicos-senal-publicacion-b16-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md). Revisión/publicación ESEN, rechazo/corrección, actores y worker/Beat reales; tiempos humanos excluidos. |
| I17 | Ciclo de vida | B04/B05/B06/B16 | [329](329-revision-semantica-testigos-b16-20261024.md). Ventana4h, renovación idempotente, carreras, caducidad y retirada sin esperarBeat; sin p95 por operación. |
| I18 | Agencias y representación | B00/B02/B03/B16 | [299](299-autoridad-cobertura-conciliacion-b00-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md). Representados con teléfono compartido y autoridad separada; no identidad/representación externa real. |
| I19 | Gestión comercial sintética | B07/B08/B14/B16 | [329](329-revision-semantica-testigos-b16-20261024.md), [330](330-conciliacion-exclusiones-b16-20261024.md), [334](334-auditoria-http-contractual-b16-20261025.md). Derechos/rotación/rollback y fixtures comerciales; no ventas, pasarela ni compra concurrente reales. |
| I20 | Denuncias y reclamaciones | B06/B09/B12/B13/B16 | [305](305-seleccion-sql-cola-denuncias-b09-20261024.md), [307](307-conciliacion-lectura-entrega-b09-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md), [335](335-conciliacion-final-candidata-b16-20261025.md). ColaSQL30/210→10/10y revocación/retirada/urgencia; no latencia de cada decisión ni cobertura humana real. |
| I21 | Derechos y rectificación | B00/B11/B13/B16 | [299](299-autoridad-cobertura-conciliacion-b00-20261024.md), [311](311-interfaz-formularios-copia-b11-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md), [335](335-conciliacion-final-candidata-b16-20261025.md). Autoridad fresca antes de descifrado, derechos y recuperación por escenario; no aceptación jurídica global. |
| I22 | Exportación y portabilidad | B10/MOD09/B11/B13/B16 | [326](326-auditoria-medicion-actual-mod09-b10-20261024.md), [328](328-conciliacion-exportacion-similitud-b10-20261024.md), [334](334-auditoria-http-contractual-b16-20261025.md), [335](335-conciliacion-final-candidata-b16-20261025.md). Dos sujetos1500revisiones/16MiBJSON/64MiBoriginales:FAILtemporal actual conservado, integridad verificada; selección31páginas p95<2s. |
| I23 | Avisos y comunicaciones | B12/B13/B14/B16 | [140](140-conciliacion-purgas-beta-b12-20261021.md), [160](160-conciliacion-final-beta-b13-20261021.md), [329](329-revision-semantica-testigos-b16-20261024.md), [335](335-conciliacion-final-candidata-b16-20261025.md). Outbox/reintento y dos caídas locales; primer intento no recepción email/SMS externa. |
| I24 | Publicación en segundo plano | B07/B08/B12/B13/B16 | [317](317-registros-historicos-senal-publicacion-b16-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md), [330](330-conciliacion-exclusiones-b16-20261024.md), [334](334-auditoria-http-contractual-b16-20261025.md), [335](335-conciliacion-final-candidata-b16-20261025.md). Guardia de modelos históricos y reparación actual14→0marcas; autoridad inmediata separada de convergencia; backlog no universal. |
| I25 | Limpieza y recuperación | B12/B13/B16 | [140](140-conciliacion-purgas-beta-b12-20261021.md), [160](160-conciliacion-final-beta-b13-20261021.md), [329](329-revision-semantica-testigos-b16-20261024.md), [335](335-conciliacion-final-candidata-b16-20261025.md). 16purgas/limpiezas conciliadas y5restauraciones actuales; noPITR/custodia externa/recifrado exhaustivo o todas las cardinalidades. |
| I26 | Navegador y entrega web | B02/B03/B09/B11/B16 | [305](305-seleccion-sql-cola-denuncias-b09-20261024.md), [306](306-diagnostico-entrega-galeria-b09-20261024.md), [307](307-conciliacion-lectura-entrega-b09-20261024.md), [311](311-interfaz-formularios-copia-b11-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md). Geografía local sinXHR, teclado/ESEN y galería8→1imagen inicial; noSLO browser completo con red/dispositivo reales. |
| I27 | Infraestructura transversal | B00/B07/B10/B12/B13/B16 | [326](326-auditoria-medicion-actual-mod09-b10-20261024.md), [328](328-conciliacion-exportacion-similitud-b10-20261024.md), [329](329-revision-semantica-testigos-b16-20261024.md), [334](334-auditoria-http-contractual-b16-20261025.md), [335](335-conciliacion-final-candidata-b16-20261025.md). Cuotas8CPU/8GiB/swap0y recursos propios; no aislamiento del host ni capacidad universal o cada endpoint a20RPS. |
| I28 | Operación administrativa | B12/B13/B17/B16 | [137](137-evaluacion-runbook-beta-b12-20261021.md), [140](140-conciliacion-purgas-beta-b12-20261021.md), [143](143-inventario-claves-hmac-beta-b13-20261021.md), [160](160-conciliacion-final-beta-b13-20261021.md), [335](335-conciliacion-final-candidata-b16-20261025.md), [336](336-deuda-siguiente-contrato-y-cierre-alpha-20261025.md). 15comandos y registroAdmin offline; no ejecutar comandos destructivos niCRUDAdmin; responsables/custodia/apertura pendientes. |

## Estado de mediciones y presupuestos

La carga pública vigente334 termina con18000 respuestas correctas y15 subidas, p95 observable410,559ms, bajo cuotas8CPU/8GiB y swap0. Es una mezcla en tercios de listado/búsqueda/ficha ES/EN y filtros combinados, con68 oráculos antes/después; no certifica p95 de cada endpoint, cada idioma por separado, todos los filtros ni toda cardinalidad. La subida302 con persistencia no mide procesamiento y cola completos.

I14 conserva el diagnóstico de detector:1000Blob distintos/cinco positivos,3,20s;100Blob densos/cien coincidencias,14,39s. No es latencia de subida, cola completa,80mil originales o retención ilimitada. No se adoptó índice nuevo.

I22 conserva el FAIL temporal actual362: cobertura alrededor3,37s y paquetes JSON/binario alrededor6,5–6,8s frente a objetivos2/5s, con integridad y separación verificadas. MOD09 mantiene su aceptación provisional y deuda; no se reescribe como PASS. Las31 lecturas de selección por sujeto sí tienen p95 recalculados1,472582/1,474600s y solapamiento real. Tampoco ese dato acepta todo el flujo.

Los límites contractuales de mezcla pública permanecen estrictamente<800ms/<1%, con contabilidad y generador originales. Los p99, umbrales individuales, tiempos de navegador y plazos asíncronos adicionales de111 siguen siendo propuestas pendientes de validación, no gates adoptados retrospectivamente. Un timeout no es un tiempo de respuesta aceptable. La frecuencia real de usuarios y los costes productivos aún no están acreditados.

## Matriz de endpoints y controles

En la tabla, los patrones son locales a su archivo de declaración; las formas completas y ambos idiomas están en JSON. Métodos se toman de decoradores explícitos. Veinticinco funciones no tienen un decorador de método: sus ramas observadas no constituyen una lista de métodos admitidos, y middleware/delegaciones pueden intervenir. No se inventa GET exclusivo. Las ramas de presentación como `event.operation == expire` se conservan como diagnóstico de código y no como una nueva acción ofrecida.

Toda ruta conserva RecoveryGate, sesiones/CSRF y AccountGate cuando aplican, además de sus permisos y autoridad de sujeto, versión, consentimiento, representación, MFA y revocación en servicios. La lista de llamadas no prueba esos permisos: las evidencias y límites familiares remiten a pruebas concretas de B16. Las dependencias de profundidad dos son navegación estática, no un grafo transitivo ni un trace runtime exhaustivos.

| Ruta estable | Familia | Métodos explícitos | Patrón local | Implementación | Valores de control |
| --- | --- | --- | --- | --- | --- |
| `R_promotion_orders` | I19 | GET/POST | `` | [apps.catalog.promotion_order_views.orders](../apps/catalog/promotion_order_views.py) L104 | — |
| `R_promotion_order_detail` | I19 | GET/POST | `<uuid:order_id>/` | [apps.catalog.promotion_order_views.detail](../apps/catalog/promotion_order_views.py) L150 | `outcome=pending,failed,succeeded` |
| `R_promotion_products` | I19 | GET/POST | `` | [apps.catalog.promotion_views.products](../apps/catalog/promotion_views.py) L34 | — |
| `R_promotion_product_versions` | I19 | GET/POST | `<uuid:product_id>/` | [apps.catalog.promotion_views.versions](../apps/catalog/promotion_views.py) L68 | — |
| `R_promotion_version_edit` | I19 | GET/POST | `<uuid:product_id>/versions/<int:number>/` | [apps.catalog.promotion_views.edit](../apps/catalog/promotion_views.py) L84 | — |
| `R_promotion_version_preview` | I19 | GET/POST | `<uuid:product_id>/versions/<int:number>/preview/` | [apps.catalog.promotion_views.preview](../apps/catalog/promotion_views.py) L119 | — |
| `R_listing_lifecycle` | I17 | GET/POST | `listing/<uuid:listing_id>/manage/` | [apps.listings.lifecycle.panel](../apps/listings/lifecycle.py) L162 | `operation=pause,resume,renew,withdraw,available,unavailable` |
| `R_favorites` | I07 | GET | `favorites/` | [apps.listings.favorites.index](../apps/listings/favorites.py) L18 | — |
| `R_favorite_add` | I07 | POST | `listing/<uuid:listing_id>/favorite/` | [apps.listings.favorites.add](../apps/listings/favorites.py) L40 | — |
| `R_favorite_remove` | I07 | POST | `favorites/<int:favorite_id>/remove/` | [apps.listings.favorites.remove](../apps/listings/favorites.py) L60 | — |
| `R_photo_appeal_queue` | I15/I20 | sin decorador de método | `moderation/photo-appeals/` | [apps.listings.photo_appeals.queue](../apps/listings/photo_appeals.py) L18 | — |
| `R_photo_appeal_review` | I15/I20 | GET/POST | `moderation/photo-appeals/<int:appeal_id>/` | [apps.listings.photo_appeals.review](../apps/listings/photo_appeals.py) L37 | — |
| `R_photo_restriction` | I15/I20 | GET/POST | `person/photo-restrictions/<int:restriction_id>/` | [apps.listings.photo_restrictions.detail](../apps/listings/photo_restrictions.py) L19 | — |
| `R_agency_appeal_submit` | I18 | GET/POST | `agency/decisions/<int:decision_id>/appeal/` | [apps.core.agency_appeals.submit](../apps/core/agency_appeals.py) L26 | — |
| `R_agency_appeal_queue` | I18 | sin decorador de método | `moderation/agency-appeals/` | [apps.core.agency_appeals.queue](../apps/core/agency_appeals.py) L68 | — |
| `R_agency_appeal_review` | I18 | GET/POST | `moderation/agency-appeals/<int:appeal_id>/` | [apps.core.agency_appeals.review](../apps/core/agency_appeals.py) L84 | — |
| `R_manager_appeal_submit` | I18 | GET/POST | `person/manager-decisions/<int:decision_id>/appeal/` | [apps.core.manager_appeals.submit](../apps/core/manager_appeals.py) L35 | — |
| `R_manager_appeal_queue` | I18 | sin decorador de método | `moderation/manager-appeals/` | [apps.core.manager_appeals.queue](../apps/core/manager_appeals.py) L73 | — |
| `R_manager_appeal_review` | I18 | GET/POST | `moderation/manager-appeals/<int:appeal_id>/` | [apps.core.manager_appeals.review](../apps/core/manager_appeals.py) L89 | — |
| `R_appeal_submit` | I15/I20 | GET/POST | `draft/decisions/<int:decision_id>/appeal/` | [apps.listings.appeals.submit](../apps/listings/appeals.py) L53 | — |
| `R_appeal_queue` | I15/I20 | sin decorador de método | `moderation/appeals/` | [apps.listings.appeals.queue](../apps/listings/appeals.py) L90 | — |
| `R_appeal_review` | I15/I20 | GET/POST | `moderation/appeals/<int:appeal_id>/` | [apps.listings.appeals.review](../apps/listings/appeals.py) L106 | — |
| `R_manager_queue` | I18 | sin decorador de método | `moderation/managers/` | [apps.core.manager_review.queue](../apps/core/manager_review.py) L77 | — |
| `R_manager_review` | I18 | GET/POST | `moderation/managers/<uuid:person_id>/` | [apps.core.manager_review.review](../apps/core/manager_review.py) L93 | `outcome=,approved,failed` |
| `R_match_queue` | I16 | sin decorador de método | `moderation/matches/` | [apps.listings.match_views.queue](../apps/listings/match_views.py) L89 | — |
| `R_match_review` | I16 | GET/POST | `moderation/matches/<int:match_id>/` | [apps.listings.match_views.review](../apps/listings/match_views.py) L104 | `outcome=,false_positive,distinct_people,conflict` |
| `R_match_image` | I06/I16 | sin decorador de método | `moderation/matches/<int:match_id>/<str:side>/image/` | [apps.listings.match_views.image](../apps/listings/match_views.py) L138 | — |
| `R_moderation_queue` | I16 | sin decorador de método | `moderation/listings/` | [apps.listings.moderation_views.queue](../apps/listings/moderation_views.py) L60 | — |
| `R_moderation_review` | I16 | GET/POST | `moderation/listings/<uuid:revision_id>/` | [apps.listings.moderation_views.review](../apps/listings/moderation_views.py) L77 | `outcome=,approved,rejected` |
| `R_moderation_photo` | I06/I16 | sin decorador de método | `moderation/photos/<uuid:photo_id>/` | [apps.listings.moderation_views.review_photo](../apps/listings/moderation_views.py) L121 | — |
| `R_listing_detail` | I05 | sin decorador de método | `listing/<uuid:listing_id>/` | [apps.listings.moderation_views.public_detail](../apps/listings/moderation_views.py) L162 | — |
| `R_public_photo` | I06 | sin decorador de método | `listing/<uuid:listing_id>/photo/<uuid:photo_id>/` | [apps.listings.moderation_views.public_photo](../apps/listings/moderation_views.py) L220 | — |
| `R_organization_queue` | I18 | sin decorador de método | `moderation/organizations/` | [apps.core.organization_review.queue](../apps/core/organization_review.py) L59 | — |
| `R_organization_review` | I18 | GET/POST | `moderation/organizations/<uuid:agency_id>/` | [apps.core.organization_review.review](../apps/core/organization_review.py) L75 | `outcome=,passed,failed` |
| `R_submit_revision` | I12 | POST | `draft/<uuid:revision_id>/submit/` | [apps.listings.views.send_for_review](../apps/listings/views.py) L31 | — |
| `R_revision_status` | I12 | sin decorador de método | `draft/<uuid:revision_id>/status/` | [apps.listings.views.revision_status](../apps/listings/views.py) L56 | — |
| `R_photo_reorder` | I15 | POST | `photos/<uuid:photo_id>/reorder/` | [apps.mediafiles.views.reorder](../apps/mediafiles/views.py) L123 | — |
| `R_photo_upload` | I13 | POST | `draft/<uuid:revision_id>/photos/upload/` | [apps.mediafiles.views.upload](../apps/mediafiles/views.py) L28 | — |
| `R_private_photo` | I06/I15 | sin decorador de método | `photos/<uuid:photo_id>/private/` | [apps.mediafiles.views.private_photo](../apps/mediafiles/views.py) L52 | — |
| `R_photo_remove` | I15 | POST | `photos/<uuid:photo_id>/remove/` | [apps.mediafiles.views.remove](../apps/mediafiles/views.py) L91 | — |
| `R_listing_start` | I12 | POST | `person/<uuid:person_id>/listing/start/` | [apps.listings.views.start](../apps/listings/views.py) L80 | — |
| `R_draft_edit` | I12 | GET/POST | `draft/<uuid:revision_id>/<int:step>/` | [apps.listings.views.edit](../apps/listings/views.py) L112 | — |
| `R_individual_create` | I10 | GET/POST | `person/create/` | [apps.core.verification.individual](../apps/core/verification.py) L158 | — |
| `R_person_verification` | I10 | sin decorador de método | `person/<uuid:person_id>/verification/` | [apps.core.verification.status](../apps/core/verification.py) L182 | — |
| `R_age_check` | I10 | GET/POST | `person/<uuid:person_id>/age/` | [apps.core.verification.age](../apps/core/verification.py) L369 | `outcome=pending,failed,passed` |
| `R_phone_start` | I10 | GET/POST | `person/<uuid:person_id>/phone/` | [apps.core.verification.phone_start](../apps/core/verification.py) L387 | — |
| `R_phone_confirm` | I10 | GET/POST | `phone/<uuid:challenge_id>/confirm/` | [apps.core.verification.phone_confirm](../apps/core/verification.py) L425 | — |
| `R_consent_invite` | I10 | GET/POST | `person/<uuid:person_id>/consent/invite/` | [apps.core.verification.invite_consent](../apps/core/verification.py) L209 | — |
| `R_self_consent` | I10 | GET/POST | `person/<uuid:person_id>/consent/` | [apps.core.verification.self_consent](../apps/core/verification.py) L313 | — |
| `R_consent_accept` | I10 | GET/POST | `representation/<uuid:invitation_id>/<str:raw>/` | [apps.core.verification.accept_consent](../apps/core/verification.py) L248 | — |
| `R_representation_revoke` | I10 | POST | `person/<uuid:person_id>/revoke/` | [apps.core.verification.revoke](../apps/core/verification.py) L490 | — |
| `R_representation_transfer` | I10 | GET/POST | `person/<uuid:person_id>/transfer/` | [apps.core.verification.transfer](../apps/core/verification.py) L517 | — |
| `R_mfa_enroll` | I10 | GET/POST | `account/mfa/enroll/` | [apps.core.mfa.enroll](../apps/core/mfa.py) L109 | — |
| `R_mfa_challenge` | I10 | GET/POST | `account/mfa/` | [apps.core.mfa.challenge](../apps/core/mfa.py) L174 | — |
| `R_agency_create` | I18 | GET/POST | `agency/create/` | [apps.core.agencies.create](../apps/core/agencies.py) L94 | — |
| `R_agency_panel` | I18 | sin decorador de método | `agency/<uuid:agency_id>/` | [apps.core.agencies.panel](../apps/core/agencies.py) L122 | — |
| `R_agency_invite` | I18 | GET/POST | `agency/<uuid:agency_id>/invite/` | [apps.core.agencies.invite](../apps/core/agencies.py) L145 | — |
| `R_agency_add_person` | I18 | GET/POST | `agency/<uuid:agency_id>/people/add/` | [apps.core.agencies.add_person](../apps/core/agencies.py) L240 | — |
| `R_agency_assign` | I18 | GET/POST | `agency/<uuid:agency_id>/people/<uuid:person_id>/assign/` | [apps.core.agencies.assign](../apps/core/agencies.py) L258 | — |
| `R_agency_revoke` | I18 | POST | `agency/<uuid:agency_id>/members/<int:member_id>/revoke/` | [apps.core.agencies.revoke_member](../apps/core/agencies.py) L217 | — |
| `R_agency_accept_invitation` | I18 | GET/POST | `agency/invitation/<uuid:invitation_id>/<str:raw>/` | [apps.core.agencies.accept_invitation](../apps/core/agencies.py) L177 | — |
| `R_resend` | I09 | GET/POST | `account/resend/` | [apps.core.accounts.resend](../apps/core/accounts.py) L393 | — |
| `R_accept_current` | I09 | GET/POST | `account/accept/` | [apps.core.accounts.accept_current](../apps/core/accounts.py) L453 | — |
| `R_signup` | I09 | GET/POST | `account/signup/` | [apps.core.accounts.signup](../apps/core/accounts.py) L196 | — |
| `R_login` | I09 | GET/POST | `account/login/` | [apps.core.accounts.signin](../apps/core/accounts.py) L249 | — |
| `R_logout` | I09 | POST | `account/logout/` | [apps.core.accounts.signout](../apps/core/accounts.py) L284 | — |
| `R_recover` | I09 | GET/POST | `account/recover/` | [apps.core.accounts.recover](../apps/core/accounts.py) L290 | — |
| `R_account_token` | I09 | GET/POST | `account/token/<uuid:token_id>/<str:raw>/` | [apps.core.accounts.token_view](../apps/core/accounts.py) L316 | — |
| `R_account_email_confirmation` | I23 | GET/POST | `safety/account-email-confirm/<uuid:confirmation_id>/` | [apps.safety.account_email_views.confirm](../apps/safety/account_email_views.py) L57 | — |
| `R_account_email_confirmation_exchange` | I23 | GET | `safety/account-email/<uuid:confirmation_id>/<str:raw>/` | [apps.safety.account_email_views.exchange](../apps/safety/account_email_views.py) L31 | — |
| `R_dashboard` | I11 | sin decorador de método | `account/` | [apps.core.accounts.dashboard](../apps/core/accounts.py) L367 | — |
| `R_legal_index` | I08 | sin decorador de método | `legal/` | [apps.core.legal.index](../apps/core/legal.py) L6 | — |
| `R_legal_document` | I08 | sin decorador de método | `legal/<slug:slug>/` | [apps.core.legal.document](../apps/core/legal.py) L13 | — |
| `R_rights_object_authorize` | I22 | GET | `internal/rights-objects/authorize/` | [apps.safety.rights_object_views.authorize](../apps/safety/rights_object_views.py) L17 | — |
| `R_rights_recipient_notices` | I23 | GET/POST | `account/rights-notices/` | [apps.safety.communication_notice_views.inbox](../apps/safety/communication_notice_views.py) L89 | `operation=inspect,ack` |
| `R_rights_communications` | I23 | GET/POST | `moderation/rights/<uuid:case_id>/communications/` | [apps.safety.rights_communication_views.communications](../apps/safety/rights_communication_views.py) L97 | `operation=source,propose,inspect,review,deliver; outcome=approved,rejected` |
| `R_rights_access_close` | I21 | GET/POST | `rights/<uuid:case_id>/access/close/<int:review_id>/` | [apps.safety.rights_access_close_views.close_response](../apps/safety/rights_access_close_views.py) L29 | — |
| `R_rights_access_supplement` | I21 | GET/POST | `rights/<uuid:case_id>/access/scope/<int:inventory_id>/supplement/` | [apps.safety.rights_access_supplement_views.preview](../apps/safety/rights_access_supplement_views.py) L60 | — |
| `R_rights_access_field_prepare` | I21 | POST | `rights/<uuid:case_id>/access/scope/<int:inventory_id>/decision/` | [apps.safety.rights_access_field_decision_views.prepare](../apps/safety/rights_access_field_decision_views.py) L78 | `outcome=included,redacted,omitted` |
| `R_rights_access_field_review` | I21 | GET/POST | `rights/<uuid:case_id>/access/decision/<int:decision_id>/` | [apps.safety.rights_access_field_decision_views.independent](../apps/safety/rights_access_field_decision_views.py) L140 | `outcome=approved,rejected` |
| `R_rights_access_scope` | I21 | GET/POST | `rights/<uuid:case_id>/access/scope/` | [apps.safety.rights_access_scope_views.inventory](../apps/safety/rights_access_scope_views.py) L39 | `outcome=included,redacted,omitted` |
| `R_rights_access_coverage_review` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/access/coverage/<int:coverage_id>/review/` | [apps.safety.rights_access_coverage_review_views.review](../apps/safety/rights_access_coverage_review_views.py) L25 | `outcome=approved,rejected` |
| `R_publication_calendar_queue` | I21 | GET | `moderation/publication-calendar/` | [apps.safety.publication_calendar_queue.queue](../apps/safety/publication_calendar_queue.py) L30 | — |
| `R_publication_purpose_release` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/publication-purpose/<int:hold_id>/release/` | [apps.safety.publication_purpose_views.release](../apps/safety/publication_purpose_views.py) L81 | `operation=inspect,propose,execute,follow_up,history` |
| `R_purpose_exception_review` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/exceptions/<int:proposal_id>/review/` | [apps.safety.purpose_exception_views.review](../apps/safety/purpose_exception_views.py) L189 | `operation=inspect,review; outcome=,approved,rejected` |
| `R_purpose_exception_prepare` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/exceptions/<uuid:plan_id>/prepare/` | [apps.safety.purpose_exception_views.prepare](../apps/safety/purpose_exception_views.py) L73 | — |
| `R_purpose_calendar_queue` | I21 | GET | `moderation/rights/restrictions/calendar/` | [apps.safety.purpose_calendar_views.queue](../apps/safety/purpose_calendar_views.py) L190 | — |
| `R_purpose_calendar_detail` | I21 | GET/POST | `moderation/rights/restrictions/<int:restriction_id>/follow-up/` | [apps.safety.purpose_calendar_views.detail](../apps/safety/purpose_calendar_views.py) L69 | `operation=inspect,follow_up` |
| `R_purpose_restriction_queue` | I21 | GET | `moderation/rights/<uuid:case_id>/restrictions/` | [apps.safety.purpose_release_views.queue](../apps/safety/purpose_release_views.py) L249 | — |
| `R_processing_prepare` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/processing/` | [apps.safety.processing_views.preparation](../apps/safety/processing_views.py) L79 | `operation=preview,prepare` |
| `R_processing_review` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/processing/<uuid:plan_id>/` | [apps.safety.processing_views.review](../apps/safety/processing_views.py) L202 | `operation=inspect,review; outcome=,approved,rejected` |
| `R_processing_execute` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/processing/<uuid:plan_id>/execute/` | [apps.safety.processing_views.execution](../apps/safety/processing_views.py) L303 | — |
| `R_purpose_restriction_release` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/restrictions/<int:restriction_id>/release/` | [apps.safety.purpose_release_views.release](../apps/safety/purpose_release_views.py) L105 | `operation=inspect,propose,execute` |
| `R_processing_final` | I21 | sin decorador de método | `moderation/rights/<uuid:case_id>/processing/final/` | [apps.safety.processing_final_views.final](../apps/safety/processing_final_views.py) L15 | — |
| `R_erasure_final` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/erasure/final/` | [apps.safety.erasure_final_views.final](../apps/safety/erasure_final_views.py) L101 | — |
| `R_rectification_final` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/rectification/final/` | [apps.safety.rectification_final_views.final](../apps/safety/rectification_final_views.py) L103 | `operation=prepare,inspect,review,close; outcome=approved,rejected` |
| `R_retention_queue` | I21 | GET | `moderation/rights/retention/` | [apps.safety.retention_views.queue](../apps/safety/retention_views.py) L29 | — |
| `R_retention_review` | I21 | GET/POST | `moderation/rights/retention/<uuid:review_id>/` | [apps.safety.retention_views.inspect](../apps/safety/retention_views.py) L120 | `operation=inspect,follow_up` |
| `R_recipient_assessment_review` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/recipient-assessment/<int:assessment_id>/review/` | [apps.safety.recipient_review_views.prepare](../apps/safety/recipient_review_views.py) L66 | `operation=inspect,review; outcome=accepted,rejected` |
| `R_recipient_assessment` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/recipient-inventory/<int:inventory_id>/assessment/` | [apps.safety.recipient_assessment_views.prepare](../apps/safety/recipient_assessment_views.py) L152 | `operation=inspect,propose` |
| `R_rectification_recipients` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/rectification-execution/<int:execution_id>/recipients/` | [apps.safety.rectification_recipients.prepare_view](../apps/safety/rectification_recipients.py) L226 | — |
| `R_rectification_notices` | I21 | GET | `account/correction-notices/` | [apps.safety.rectification_notices.inbox](../apps/safety/rectification_notices.py) L60 | — |
| `R_rectification_notice_acknowledge` | I21 | POST | `account/correction-notices/<int:notice_id>/acknowledge/` | [apps.safety.rectification_notices.acknowledge](../apps/safety/rectification_notices.py) L79 | — |
| `R_rectification_review` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/rectification/<int:proposal_id>/review/` | [apps.safety.rectification_review.prepare](../apps/safety/rectification_review.py) L244 | `operation=inspect,review,confirm_email,notify,execute; outcome=approved,rejected` |
| `R_rights_rectification` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/rectification/` | [apps.safety.rights_rectification.prepare](../apps/safety/rights_rectification.py) L532 | `operation=preview,propose` |
| `R_rights_rectification_photo` | I21 | GET | `moderation/rights/<uuid:case_id>/rectification/photos/<uuid:photo_id>/` | [apps.safety.rights_rectification.source_photo](../apps/safety/rights_rectification.py) L660 | — |
| `R_rectification_uploads` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/rectification/uploads/` | [apps.safety.rectification_uploads.prepare](../apps/safety/rectification_uploads.py) L264 | `operation=upload,discard` |
| `R_erasure_execute` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/erasure-execute/<uuid:plan_id>/` | [apps.safety.erasure_execution.apply](../apps/safety/erasure_execution.py) L591 | — |
| `R_erasure_plan` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/erasure-plan/<uuid:inventory_id>/` | [apps.safety.erasure_plans.prepare](../apps/safety/erasure_plans.py) L264 | — |
| `R_erasure_inventory` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/erasure-inventory/` | [apps.safety.erasure_inventory.inspect](../apps/safety/erasure_inventory.py) L1308 | — |
| `R_privacy_publication_hold` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/publication-hold/` | [apps.safety.privacy_holds.apply](../apps/safety/privacy_holds.py) L129 | — |
| `R_rights_response` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/response/` | [apps.safety.rights_responses.respond](../apps/safety/rights_responses.py) L257 | — |
| `R_media_erasure_jobs` | I25 | GET | `moderation/rights/<uuid:case_id>/media-jobs/` | [apps.safety.media_operations.queue](../apps/safety/media_operations.py) L132 | — |
| `R_media_erasure_recover` | I25 | GET/POST | `moderation/rights/<uuid:case_id>/media-jobs/<int:job_id>/` | [apps.safety.media_operations.recover](../apps/safety/media_operations.py) L145 | — |
| `R_notice_queue` | I23/I25 | GET | `moderation/notices/` | [apps.safety.notice_operations.queue](../apps/safety/notice_operations.py) L155 | — |
| `R_notice_recover` | I23/I25 | GET/POST | `moderation/notices/<str:kind>/<int:notice_id>/` | [apps.safety.notice_operations.recover](../apps/safety/notice_operations.py) L191 | — |
| `R_complaint_photo` | I20 | GET | `moderation/complaints/<uuid:complaint_id>/photo/<uuid:photo_id>/` | [apps.safety.complaints.photo](../apps/safety/complaints.py) L455 | — |
| `R_complaint_resolve` | I20 | GET/POST | `moderation/complaints/<uuid:complaint_id>/resolve/` | [apps.safety.complaints.resolve](../apps/safety/complaints.py) L558 | `outcome=upheld,reconsidered,unidentified` |
| `R_complaint_create` | I20 | GET/POST | `safety/complaints/` | [apps.safety.complaints.submit](../apps/safety/complaints.py) L78 | — |
| `R_complaint_message` | I20 | POST | `safety/complaints/<uuid:complaint_id>/<str:secret>/message/` | [apps.safety.complaint_messages.submit](../apps/safety/complaint_messages.py) L125 | — |
| `R_complaint_receipt` | I20 | GET | `safety/complaints/<uuid:complaint_id>/<str:secret>/` | [apps.safety.complaints.receipt](../apps/safety/complaints.py) L140 | — |
| `R_complaint_queue` | I20 | GET | `moderation/complaints/` | [apps.safety.complaints.queue](../apps/safety/complaints.py) L202 | — |
| `R_complaint_action` | I20 | GET/POST | `moderation/complaints/<uuid:complaint_id>/action/` | [apps.safety.complaints.action](../apps/safety/complaints.py) L416 | `operation=claim,unassign,link,link_listing,clarify,reassess` |
| `R_complaint_inspect` | I20 | GET/POST | `moderation/complaints/<uuid:complaint_id>/` | [apps.safety.complaints.inspect](../apps/safety/complaints.py) L233 | — |
| `R_rights_create` | I21 | GET/POST | `safety/rights/` | [apps.safety.rights.submit](../apps/safety/rights.py) L130 | — |
| `R_rights_receipt` | I21 | GET/POST | `safety/rights/<uuid:case_id>/<str:secret>/` | [apps.safety.rights.receipt](../apps/safety/rights.py) L205 | — |
| `R_rights_response_acknowledge` | I21 | POST | `safety/rights/<uuid:case_id>/<str:secret>/response/<int:response_id>/acknowledge/` | [apps.safety.rights_responses.acknowledge](../apps/safety/rights_responses.py) L324 | — |
| `R_rights_verification` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/verification/` | [apps.safety.rights_verification.verification](../apps/safety/rights_verification.py) L311 | `operation=start,result; outcome=,pending,failed,passed` |
| `R_rights_image_inspect` | I22 | POST | `moderation/rights/<uuid:case_id>/image/<uuid:photo_id>/` | [apps.safety.rights_exports.inspect_image](../apps/safety/rights_exports.py) L957 | — |
| `R_rights_image_download` | I22 | POST | `safety/rights/<uuid:case_id>/<str:secret>/export/<uuid:export_id>/image/<uuid:image_id>/` | [apps.safety.rights_exports.download](../apps/safety/rights_exports.py) L711 | — |
| `R_rights_part_download` | I22 | POST | `safety/rights/<uuid:case_id>/<str:secret>/export/<uuid:export_id>/part/<uuid:part_id>/` | [apps.safety.rights_exports.download](../apps/safety/rights_exports.py) L711 | — |
| `R_rights_information_review` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/information/<int:information_id>/review/` | [apps.safety.rights_information_review_views.review](../apps/safety/rights_information_review_views.py) L49 | `operation=inspect,review; outcome=,approved,rejected` |
| `R_rights_portability_coverage_review` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/coverage/<int:coverage_id>/review/` | [apps.safety.rights_portability_coverage_review_views.review](../apps/safety/rights_portability_coverage_review_views.py) L105 | `outcome=approved,rejected` |
| `R_rights_portability_image_coverage` | I22 | sin decorador de método | `moderation/rights/<uuid:case_id>/portability/coverage/images/` | [apps.safety.rights_portability_coverage_views.prepare_image_omissions](../apps/safety/rights_portability_coverage_views.py) L338 | — |
| `R_rights_portability_coverage` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/coverage/` | [apps.safety.rights_portability_coverage_views.prepare](../apps/safety/rights_portability_coverage_views.py) L127 | — |
| `R_rights_portability_images` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/images/` | [apps.safety.rights_portability_image_views.prepare_images](../apps/safety/rights_portability_image_views.py) L50 | — |
| `R_rights_portability_export` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/export/` | [apps.safety.rights_portability_export_views.prepare](../apps/safety/rights_portability_export_views.py) L88 | — |
| `R_rights_portability_export_job` | I22 | GET | `moderation/rights/<uuid:case_id>/portability/export/jobs/<uuid:job_id>/` | [apps.safety.rights_portability_export_views.job_status](../apps/safety/rights_portability_export_views.py) L168 | — |
| `R_rights_access_response_prepare` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/access/response/` | [apps.safety.rights_access_response_views.prepare_response](../apps/safety/rights_access_response_views.py) L111 | — |
| `R_rights_access_response_review` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/access/response/<int:draft_id>/review/` | [apps.safety.rights_access_response_views.review_response](../apps/safety/rights_access_response_views.py) L286 | `outcome=approved,rejected` |
| `R_rights_portability_response_prepare` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/response/` | [apps.safety.rights_portability_response_views.prepare_response](../apps/safety/rights_portability_response_views.py) L56 | — |
| `R_rights_portability_response_review` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/response/<int:draft_id>/review/` | [apps.safety.rights_portability_response_views.review_response](../apps/safety/rights_portability_response_views.py) L188 | `outcome=approved,rejected` |
| `R_rights_portability_response_close` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/response/<int:review_id>/close/` | [apps.safety.rights_portability_response_views.close_response](../apps/safety/rights_portability_response_views.py) L314 | — |
| `R_rights_portability_select` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/select/` | [apps.safety.rights_portability_prepare_selection_views.prepare](../apps/safety/rights_portability_prepare_selection_views.py) L187 | — |
| `R_rights_portability_image_inspect` | I22 | POST | `moderation/rights/<uuid:case_id>/portability/selection/<int:selection_id>/image/<uuid:photo_id>/` | [apps.safety.rights_portability_selection_views.inspect_image](../apps/safety/rights_portability_selection_views.py) L227 | — |
| `R_rights_portability_selection_review` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/selection/<int:selection_id>/review/` | [apps.safety.rights_portability_selection_views.review](../apps/safety/rights_portability_selection_views.py) L69 | `operation=inspect,review; outcome=,approved,rejected` |
| `R_rights_portability_review` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/<int:assessment_id>/review/` | [apps.safety.rights_portability_review_views.review](../apps/safety/rights_portability_review_views.py) L49 | `operation=inspect,review; outcome=,approved,rejected` |
| `R_rights_portability_prepare` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/portability/` | [apps.safety.rights_portability_views.prepare](../apps/safety/rights_portability_views.py) L141 | `operation=inspect` |
| `R_rights_copy_information_prepare` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/information/` | [apps.safety.rights_copy_information_views.prepare](../apps/safety/rights_copy_information_views.py) L143 | — |
| `R_rights_export_prepare` | I22 | GET/POST | `moderation/rights/<uuid:case_id>/export/` | [apps.safety.rights_exports.prepare](../apps/safety/rights_exports.py) L526 | `operation=preview,inspect_page,inspect_saved_page,compile_pages,generate_pages,generate_pages_with_information,generate` |
| `R_rights_export_download` | I22 | POST | `safety/rights/<uuid:case_id>/<str:secret>/export/<uuid:export_id>/` | [apps.safety.rights_exports.download](../apps/safety/rights_exports.py) L711 | — |
| `R_photo_reuse_queue` | I21 | sin decorador de método | `moderation/photo-reuse/` | [apps.safety.photo_reintroduction_views.queue](../apps/safety/photo_reintroduction_views.py) L145 | — |
| `R_photo_reuse_review` | I21 | GET/POST | `moderation/photo-reuse/<int:candidate_id>/` | [apps.safety.photo_reintroduction_views.review](../apps/safety/photo_reintroduction_views.py) L63 | `outcome=,maintain,false_positive,authorize` |
| `R_photo_reuse_image` | I06/I25 | sin decorador de método | `moderation/photo-reuse/<int:candidate_id>/reads/<int:read_id>/<str:side>/` | [apps.safety.photo_reintroduction_views.image](../apps/safety/photo_reintroduction_views.py) L115 | — |
| `R_rights_queue` | I21 | GET | `moderation/rights/` | [apps.safety.rights.queue](../apps/safety/rights.py) L347 | — |
| `R_rights_action` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/action/` | [apps.safety.rights.action](../apps/safety/rights.py) L773 | `operation=claim,link,clarify,withdraw,extend,unassign` |
| `R_rights_inspect` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/` | [apps.safety.rights.inspect](../apps/safety/rights.py) L405 | — |
| `R_report_decision` | I21 | GET/POST | `moderation/reports/<uuid:report_id>/decision/` | [apps.safety.views.decision](../apps/safety/views.py) L498 | `operation=claim,unassign,uphold,lift,link,restrict,dismiss` |
| `R_report_inspect` | I21 | GET/POST | `moderation/reports/<uuid:report_id>/` | [apps.safety.views.inspect](../apps/safety/views.py) L299 | — |
| `R_report_create` | I21 | GET/POST | `safety/report/` | [apps.safety.views.submit](../apps/safety/views.py) L133 | — |
| `R_report_receipt` | I21 | GET | `safety/receipt/<uuid:report_id>/<str:secret>/` | [apps.safety.views.receipt](../apps/safety/views.py) L228 | — |
| `R_report_queue` | I21 | GET | `moderation/reports/` | [apps.safety.views.queue](../apps/safety/views.py) L250 | — |
| `R_privacy_hold_release` | I21 | GET/POST | `moderation/rights/<uuid:case_id>/publication-hold/release/` | [apps.safety.privacy_release.review](../apps/safety/privacy_release.py) L284 | `operation=propose,execute` |
| `R_urgent_report_alerts` | I21 | GET/POST | `moderation/reports/urgent-alerts/` | [apps.safety.urgent_alerts.queue](../apps/safety/urgent_alerts.py) L30 | — |
| `R_health` | I27/I28 | sin decorador de método | `health/` | [apps.core.views.health](../apps/core/views.py) L7 | — |
| `R_robots` | I08 | GET/HEAD | `robots.txt` | [apps.core.sitemaps.robots](../apps/core/sitemaps.py) L99 | — |
| `R_sitemap_index` | I08 | GET/HEAD | `sitemap.xml` | [apps.core.sitemaps.index](../apps/core/sitemaps.py) L53 | — |
| `R_sitemap_directory` | I08 | GET/HEAD | `sitemaps/directory.xml` | [apps.core.sitemaps.directory](../apps/core/sitemaps.py) L72 | — |
| `R_sitemap_listings` | I08 | GET/HEAD | `sitemaps/listings/<int:page>.xml` | [apps.core.sitemaps.listings](../apps/core/sitemaps.py) L81 | — |
| `R_home` | I01/I02/I03/I04 | sin decorador de método | `` | [apps.core.views.home](../apps/core/views.py) L16 | — |

## Tareas, disparadores y recuperación

Las25 declaraciones de Beat no son25 tareas ejecutadas. Sin promoción sintética hay24 entradas; con ese modo hay25; en recuperación, cero y `RecoveryAwareTask.before_start` ignora además mensajes de negocio consumidos. Cola por defecto `clasificados`, prefijo por generación y JSON; estados `succeeded` o resultados ignorados no acreditan recepción externa.

Cadencias declaradas: una de10s, una de30s,21 de60s y dos de3600s, contando la promoción condicional. `process_blob` y `generate_portability_export` se despachan a demanda; recuperar medios vuelve a encolar trabajo elegible. Límites generales90s suave/120s duro; exportación240/300s por intento. El procesamiento fotográfico reintenta OSError con backoff y máximo tres reintentos; la recuperación revisa cola, antigüedad mayor de tres minutos, intentos y comparación incompleta, por lotes de cien. No son SLA de extremo a extremo.

Publicación conecta `post_save`, `post_delete` y `m2m_changed` al callback deduplicado después del commit. Se excluyen registros históricos de migración. Las tablas elegibles y las plantillas de triggers SQL están enumeradas en JSON; no se simula un censo de triggers de una base viva. Escrituras bulk/rawSQL, invalidación de base, lectura nativa y reparación por Beat se distinguen de las señales Python. Retirada o revocación no esperan a la próxima cadencia para impedir exposición.

| Tarea | Familia | Cadencia declarada | Fuente |
| --- | --- | --- | --- |
| `apps.catalog.tasks.bump_promotions` | I19 | 60s; sólo modo sintético | [tasks.py](../apps/catalog/tasks.py) L10 |
| `apps.listings.tasks.expire_listings` | I17/I24 | 60s | [tasks.py](../apps/listings/tasks.py) L41 |
| `apps.listings.tasks.refresh_publication_state` | I24 | 30s | [tasks.py](../apps/listings/tasks.py) L51 |
| `apps.listings.tasks.sweep_publication_state` | I24 | 3600s | [tasks.py](../apps/listings/tasks.py) L66 |
| `apps.mediafiles.tasks.process_blob` | I13/I14 | a demanda | [tasks.py](../apps/mediafiles/tasks.py) L9 |
| `apps.mediafiles.tasks.recover_media_jobs` | I15/I25 | 60s | [tasks.py](../apps/mediafiles/tasks.py) L14 |
| `apps.mediafiles.tasks.erase_media_files` | I15/I25 | 60s | [tasks.py](../apps/mediafiles/tasks.py) L34 |
| `apps.mediafiles.tasks.cleanup_prepared_media` | I15/I25 | 60s | [tasks.py](../apps/mediafiles/tasks.py) L41 |
| `apps.safety.rights_object_content.purge_orphan_export_objects` | I22/I25 | 3600s | [rights_object_content.py](../apps/safety/rights_object_content.py) L185 |
| `apps.safety.rights_object_delivery.purge_object_deliveries` | I22/I25 | 10s | [rights_object_delivery.py](../apps/safety/rights_object_delivery.py) L313 |
| `apps.safety.tasks.deliver_safety_notices` | I23 | 60s | [tasks.py](../apps/safety/tasks.py) L9 |
| `apps.safety.tasks.reconcile_urgent_report_alerts` | I20/I23 | 60s | [tasks.py](../apps/safety/tasks.py) L16 |
| `apps.safety.tasks.purge_expired_exports` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L31 |
| `apps.safety.tasks.purge_expired_account_confirmation_delivery` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L50 |
| `apps.safety.tasks.reconcile_retention_reviews` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L57 |
| `apps.safety.tasks.purge_expired_copy_page_reviews` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L64 |
| `apps.safety.tasks.purge_expired_copy_information` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L82 |
| `apps.safety.tasks.purge_expired_portability_assessments` | I22/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L100 |
| `apps.safety.tasks.purge_expired_portability_selections` | I22/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L118 |
| `apps.safety.tasks.purge_expired_portability_coverage` | I22/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L136 |
| `apps.safety.tasks.purge_expired_portability_response_drafts` | I22/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L154 |
| `apps.safety.tasks.purge_expired_access_response_drafts` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L172 |
| `apps.safety.tasks.purge_expired_access_coverage` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L194 |
| `apps.safety.tasks.purge_expired_access_scope_inventory` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L212 |
| `apps.safety.tasks.purge_expired_access_field_decision` | I21/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L230 |
| `apps.safety.tasks.generate_portability_export` | I22 | a demanda | [tasks.py](../apps/safety/tasks.py) L254 |
| `apps.safety.tasks.reconcile_portability_export_jobs` | I22/I25 | 60s | [tasks.py](../apps/safety/tasks.py) L261 |

## Operación administrativa

Admin registra únicamente `auth.group` en este censo. Sus rutas genéricas pueden denegar o devolver404 para objetivos sin soporte. Las guardias de Django de usuario activo/staff y permisos del modelo se suman a AccountGate, MFA y RecoveryGate del proyecto. El registro global ofrece `delete_selected`, condicionado a permisos y confirmación; no se ejecutó ni se acredita por enumerarlo. Los paneles propios de moderación/derechos están en sus familias correspondientes, no se confunden con Django Admin.

| Nombre Admin | Callback | Patrones ES/EN |
| --- | --- | --- |
| `admin:index` | `django.contrib.admin.sites.AdminSite.index` | `es/admin/`; `en/admin/` |
| `admin:login` | `django.contrib.admin.sites.AdminSite.login` | `es/admin/login/`; `en/admin/login/` |
| `admin:logout` | `django.contrib.admin.sites.AdminSite.logout` | `es/admin/logout/`; `en/admin/logout/` |
| `admin:password_change` | `django.contrib.admin.sites.AdminSite.password_change` | `es/admin/password_change/`; `en/admin/password_change/` |
| `admin:password_change_done` | `django.contrib.admin.sites.AdminSite.password_change_done` | `es/admin/password_change/done/`; `en/admin/password_change/done/` |
| `admin:autocomplete` | `django.contrib.admin.sites.AdminSite.autocomplete_view` | `es/admin/autocomplete/`; `en/admin/autocomplete/` |
| `admin:jsi18n` | `django.contrib.admin.sites.AdminSite.i18n_javascript` | `es/admin/jsi18n/`; `en/admin/jsi18n/` |
| `admin:view_on_site` | `django.contrib.contenttypes.views.shortcut` | `es/admin/r/<path:content_type_id>/<path:object_id>/`; `en/admin/r/<path:content_type_id>/<path:object_id>/` |
| `admin:auth_group_changelist` | `django.contrib.admin.options.ModelAdmin.changelist_view` | `es/admin/auth/group/`; `en/admin/auth/group/` |
| `admin:auth_group_add` | `django.contrib.admin.options.ModelAdmin.add_view` | `es/admin/auth/group/add/`; `en/admin/auth/group/add/` |
| `admin:auth_group_history` | `django.contrib.admin.options.ModelAdmin.history_view` | `es/admin/auth/group/<path:object_id>/history/`; `en/admin/auth/group/<path:object_id>/history/` |
| `admin:auth_group_delete` | `django.contrib.admin.options.ModelAdmin.delete_view` | `es/admin/auth/group/<path:object_id>/delete/`; `en/admin/auth/group/<path:object_id>/delete/` |
| `admin:auth_group_change` | `django.contrib.admin.options.ModelAdmin.change_view` | `es/admin/auth/group/<path:object_id>/change/`; `en/admin/auth/group/<path:object_id>/change/` |
| `A_unnamed_34b71d47a538` | `django.views.generic.base.View.as_view.<locals>.view` | `es/admin/auth/group/<path:object_id>/`; `en/admin/auth/group/<path:object_id>/` |
| `admin:app_list` | `django.contrib.admin.sites.AdminSite.app_index` | `es/admin/^(?P<app_label>auth)/$`; `en/admin/^(?P<app_label>auth)/$` |
| `A_unnamed_4dc81e24708e` | `django.contrib.admin.sites.AdminSite.catch_all_view` | `es/admin/(?P<url>.*)$`; `en/admin/(?P<url>.*)$` |

| Comando propio | Diferencia de fuente | Fuente y alcance |
| --- | --- | --- |
| `import_geography` | conserved | [import_geography.py](../apps/catalog/management/commands/import_geography.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `seed_catalog` | conserved | [seed_catalog.py](../apps/catalog/management/commands/seed_catalog.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `bootstrap` | conserved | [bootstrap.py](../apps/core/management/commands/bootstrap.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `encryption_key_inventory` | added | [encryption_key_inventory.py](../apps/core/management/commands/encryption_key_inventory.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `operational_assessment` | added | [operational_assessment.py](../apps/core/management/commands/operational_assessment.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `operational_events_report` | added | [operational_events_report.py](../apps/core/management/commands/operational_events_report.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `operational_snapshot` | added | [operational_snapshot.py](../apps/core/management/commands/operational_snapshot.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `seed_demo` | conserved | [seed_demo.py](../apps/core/management/commands/seed_demo.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `refresh_publication_state` | conserved | [refresh_publication_state.py](../apps/listings/management/commands/refresh_publication_state.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `apply_recovery_ledger` | modified | [apply_recovery_ledger.py](../apps/safety/management/commands/apply_recovery_ledger.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `check_recovery_ledger` | conserved | [check_recovery_ledger.py](../apps/safety/management/commands/check_recovery_ledger.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `clear_recovery_sessions` | conserved | [clear_recovery_sessions.py](../apps/safety/management/commands/clear_recovery_sessions.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `configure_rights_evidence_role` | conserved | [configure_rights_evidence_role.py](../apps/safety/management/commands/configure_rights_evidence_role.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `initialize_rights_runtime` | conserved | [initialize_rights_runtime.py](../apps/safety/management/commands/initialize_rights_runtime.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |
| `restore_publication_calendar` | conserved | [restore_publication_calendar.py](../apps/safety/management/commands/restore_publication_calendar.py); argumentos/confirmaciones en JSON; no se ejecutó `handle()` |

### Herramientas de Django y recorridos operativos

El registro añade31 comandos del framework a los15 propios. Se enumeran con su fuente y huella en JSON; no se han ejecutado. Las herramientas de QA y generación de proyectos quedan fuera de la optimización de recorridos de aplicación.

| Comando Django | Alcance |
| --- | --- |
| `changepassword` | operator_tool; registrado, no ejecutado |
| `check` | operator_tool; registrado, no ejecutado |
| `clearsessions` | operator_tool; registrado, no ejecutado |
| `collectstatic` | operator_tool; registrado, no ejecutado |
| `compilemessages` | operator_tool; registrado, no ejecutado |
| `createcachetable` | operator_tool; registrado, no ejecutado |
| `createsuperuser` | operator_tool; registrado, no ejecutado |
| `dbshell` | operator_tool; registrado, no ejecutado |
| `diffsettings` | operator_tool; registrado, no ejecutado |
| `dumpdata` | operator_tool; registrado, no ejecutado |
| `findstatic` | operator_tool; registrado, no ejecutado |
| `flush` | operator_tool; registrado, no ejecutado |
| `inspectdb` | operator_tool; registrado, no ejecutado |
| `loaddata` | operator_tool; registrado, no ejecutado |
| `makemessages` | operator_tool; registrado, no ejecutado |
| `makemigrations` | operator_tool; registrado, no ejecutado |
| `migrate` | operator_tool; registrado, no ejecutado |
| `optimizemigration` | operator_tool; registrado, no ejecutado |
| `remove_stale_contenttypes` | operator_tool; registrado, no ejecutado |
| `runserver` | operator_tool; registrado, no ejecutado |
| `sendtestemail` | operator_tool; registrado, no ejecutado |
| `shell` | operator_tool; registrado, no ejecutado |
| `showmigrations` | operator_tool; registrado, no ejecutado |
| `sqlflush` | operator_tool; registrado, no ejecutado |
| `sqlmigrate` | operator_tool; registrado, no ejecutado |
| `sqlsequencereset` | operator_tool; registrado, no ejecutado |
| `squashmigrations` | operator_tool; registrado, no ejecutado |
| `startapp` | code_generation_not_product_journey; registrado, no ejecutado |
| `startproject` | code_generation_not_product_journey; registrado, no ejecutado |
| `test` | QA_deferred; registrado, no ejecutado |
| `testserver` | QA_deferred; registrado, no ejecutado |

Los once recorridos operativos enlazan manuales, autoridad, evidencia fechada y límites. Su enumeración no acredita una operación nueva ni disponibilidad productiva. B17 conserva las responsabilidades externas pendientes.

| Recorrido | Familia | Fuentes | Evidencia y límite |
| --- | --- | --- | --- |
| Inicio/parada y comprobación de servicios locales | I27/I28 | [02-arquitectura.md](../docs/02-arquitectura.md), [12-operacion-seguridad.md](../docs/12-operacion-seguridad.md), [compose.yaml](../compose.yaml) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Configuración/locales ensayados; no despliegue o disponibilidad del destino. |
| Recuperación de worker/broker y outbox | I23/I25/I28 | [141-continuidad-moderacion-beta-b13-20261021.md](../docs/141-continuidad-moderacion-beta-b13-20261021.md), [160-conciliacion-final-beta-b13-20261021.md](../docs/160-conciliacion-final-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Dos caídas propias y replay; no reinicio de host o fallo a mitad de toda tarea. |
| Transición de cifrado y lectores retenidos | I21/I25/I28 | [142-rotacion-secretos-beta-b13-20261021.md](../docs/142-rotacion-secretos-beta-b13-20261021.md), [143-inventario-claves-hmac-beta-b13-20261021.md](../docs/143-inventario-claves-hmac-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Lectura antigua/escritura nueva e inventario acotado; no recifrado exhaustivo, retirada universal o recuperación de claves perdidas. |
| Rotación de firma Django y consumidores | I09/I21/I28 | [147-consumidores-hmac-beta-b13-20261021.md](../docs/147-consumidores-hmac-beta-b13-20261021.md), [151-clave-hmac-dominio-beta-b13-20261021.md](../docs/151-clave-hmac-dominio-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Sesiones y HMAC derivados tienen ámbitos diferentes; no revalidación automática de todas las decisiones/bindings. |
| Rotación y reconexión de credencial PostgreSQL | I27/I28 | [148-rotacion-credencial-postgresql-beta-b13-20261021.md](../docs/148-rotacion-credencial-postgresql-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Reconexiones propias y reinicio coordinado; no hot reload universal o credencial productiva. |
| Rotación Redis/Kombu y continuidad de cola | I23/I27/I28 | [149-rotacion-broker-redis-beta-b13-20261021.md](../docs/149-rotacion-broker-redis-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Mensajes/namespace propios conservados en escenario; no garantía exactly-once o recepción externa. |
| Recarga del secreto del proxy Caddy | I22/I27/I28 | [154-recarga-secreto-caddy-beta-b13-20261021.md](../docs/154-recarga-secreto-caddy-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Transporte local, secreto viejo rechazado y grant pendiente; no operación de proveedor/destino. |
| Copia/pg_dump/pg_restore/medios y reconciliación | I21/I25/I28 | [152-restauracion-clave-hmac-beta-b13-20261021.md](../docs/152-restauracion-clave-hmac-beta-b13-20261021.md), [155-matriz-vigente-b13-beta-20261021.md](../docs/155-matriz-vigente-b13-beta-20261021.md), [160-conciliacion-final-beta-b13-20261021.md](../docs/160-conciliacion-final-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Cinco restauraciones actuales en353y autoridad/replay/medio verificados; noPITR/offsite/custodia humana real. |
| Retorno y vuelta entre versiones de runtime | I25/I27/I28 | [145-estrategia-rollback-beta-b13-20261021.md](../docs/145-estrategia-rollback-beta-b13-20261021.md), [146-rollback-escrituras-workers-beta-b13-20261021.md](../docs/146-rollback-escrituras-workers-beta-b13-20261021.md), [158-retorno-hmac-correo-beta-b13-20261021.md](../docs/158-retorno-hmac-correo-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Ciclo histórico local versionado, sin downgrade de esquema; no afirmar repetición sobre toda imagen/candidata actual. |
| Incidente y revocación de clave HMAC de dominio | I09/I21/I28 | [159-incidente-clave-dominio-beta-b13-20261021.md](../docs/159-incidente-clave-dominio-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Cierra autoridad antigua y permite entrada nueva; no migración automática de bindings ni reutilizar clave comprometida para reabrirlos. |
| Retirada urgente, escalado y sustitución local | I16/I20/I28 | [144-restauracion-retirada-beta-b13-20261021.md](../docs/144-restauracion-retirada-beta-b13-20261021.md), [160-conciliacion-final-beta-b13-20261021.md](../docs/160-conciliacion-final-beta-b13-20261021.md) | [15-beta-b13-aceptacion-local-20261021.md](../docs/actas/15-beta-b13-aceptacion-local-20261021.md), [b16-operational-gates-reconciliation-20261025.json](../docs/evidencias/b16-operational-gates-reconciliation-20261025.json). Drills y retirada ES/EN con evidencia/tercero preservados; no cobertura humana o tiempo de resolución real. |

## Navegador y entrega

Se revisan las129 plantillas propias, incluidos enlaces, botones e imágenes/recursos;106 contienen formularios, controles de operación o HTMX. Las referencias literales de nombres URL resuelven contra las170 declaraciones. Los atributos dinámicos conservan su expresión, sin inventar destino. Los tres JavaScript propios cubren selectores geográficos y asociación de errores; las opciones geográficas se manipulan localmente, sin una nueva API de geografía. HTMX y recursos del navegador se distinguen del JavaScript propio; la dependencia vendorizada no se cuenta como código propio.

La consulta periódica de exportación pendiente y la entrega diferida de fotografías requieren fijar sesiones simultáneas, duración, bytes, red y dispositivo al medir. Un navegador probado funcionalmente no demuestra un p99 de interacción; el HTML no acredita el backend. La mejora de galería de B09 conserva su evidencia de carga inicial dentro de su escenario, sin generalizar a toda red.

## Primera cola del siguiente contrato

1. Acordar escenarios, clase de tamaño, uso esperado y presupuestos aplicables sobre esta matriz. Priorizar evidencia de coste y riesgo; no inferir frecuencia desde centralidad del grafo o duración de QA.
2. Retomar deuda medida de I22/MOD09 e I14: cobertura/paquetes, cardinalidad de Blob, densidad, confirmación/registro, retención, concurrencia y cola. Conservar la excepción y los negativos hasta una comparación nueva válida.
3. Segmentar I01–I05 por selectividad, página, idioma, estado y frío/caliente; completar I11–I17 desde recepción hasta estado utilizable, manteniendo autoridad y formatos. No repetir la batería contractual por rutina.
4. Medir decisiones/colas I20–I25 y navegador/imágenes I06/I26 según volumen y responsabilidad local. Tratar transferencia, espera humana y proveedor por separado.
5. Revisar los nuevos comandos y la administración I28 en escenarios propios, con roles y confirmaciones. B14/B15/B17 siguen diferidos según336; no se eligen proveedores, no se implementa personalización ni se abre beta por esta matriz.

La medición/corrección/optimización específica de QA permanece aplazada hasta la primera versión estable/productiva. Este inventario es de acciones de aplicación y operación, no ese contrato de QA. Las próximas pruebas de producto sólo se justificarán por un cambio, incertidumbre o escenario concreto; no por el número de filas.

## Límites de exhaustividad

Cobertura estructural contrastada con todas las declaraciones propias de rutas y tareas, registro de URL del modo explícito, comandos, plantillas y señales indicados. No enumera todas las combinaciones de datos/estados, métodos de librería, URL concreta con cada UUID, destinatario/proveedor, proceso humano o rama dinámica. La recuperación y los modos cambian exposición y planificación. Las fuentes externas y los permisos efectivos requieren el entorno autorizado correspondiente. Esas exclusiones son explícitas, no PASS ni defectos supuestos.

No se detectó una referencia literal de plantilla a nombre URL inexistente en este censo. No se ha ejecutado una batería nueva ni cambiado código de aplicación. El cierre documental exige aún integrar este inventario al grafo y comprobar los entregables finales del contrato.

