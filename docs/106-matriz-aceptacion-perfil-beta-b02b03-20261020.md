# Matriz de aceptación local B02–B03

Fecha: 2026-10-20. Estado: doce criterios conciliados y B02/B03 aceptados técnicamente en local por [acta12](actas/12-beta-b02b03-aceptacion-local-20261020.md); no aceptación beta global. Requisitos del [roadmap103](103-roadmap-beta-clasificados-20261020.md), [matriz104](104-consolidacion-contrato-beta-b00b01-20261020.md) y [contrato14](14-contrato-funcional-v1.md); implementación y negativos en [incremento105](105-adaptacion-perfil-beta-b02b03-20261020.md).

## Criterios y pruebas afectadas

| ID | Requisito y evidencia requerida | Selección identificada |
| --- | --- | --- |
| P01 | Catálogo romántico nuevo, IDs y datos heredados conservados; migración de ida/vuelta sin republicación automática | test_beta_profile_contract: migración0022→0025→0022 y reversión bloqueada ante etiqueta seleccionada y legacy privado |
| P02 | Perfil sin categorías/servicios/tarifas profesionales; rechazar entrada manipulada y valores incompatibles almacenados | test_beta_profile_contract, test_drafts, test_submissions y test_listing_moderation |
| P03 | Tipo voluntario sin asignación automática; conservar valores existentes; desconocido no es una declaración concreta | test_optional_profile_type y test_beta_profile_contract: migración; publicación sin tipo, filtros y paridad |
| P03b | Etiqueta trans voluntaria independiente del tipo, sin inferencia, con copia/rectificación/supresión/recuperación y conservación de formato histórico | test_declared_profile_label, test_rights_exports y rectificación completa con etiqueta previa seleccionada, formato antiguo y cambios explícitos; verificados en candidata común034242 |
| P04 | Listado/ficha ES–EN y filtros coherentes, parámetros profesionales antiguos explícitamente rechazados, paginación exacta | test_discovery y test_beta_profile_contract |
| P05 | Misma autoridad en envío, aprobación y lectura; reglas versionadas, estado derivado conservador, retirada sin esperar refresco | test_public_validation_context, test_publication_state y guardas de test_beta_profile_contract |
| P06 | Documentos aceptados inmutables y lectura privada del historial compatible | test_beta_profile_contract: documentos; test_rights_exports: descarga con contratos actual y heredado |
| P07 | Entrada Mi perfil sobre la persona existente; borrador y cambios pendientes separados de versión aprobada, estados y motivos ES–EN | test_profile_status y acceso a perfil de test_beta_profile_contract |
| P08 | Guardar, retomar, corregir, revisar y publicar sin perder borrador ni modificar aprobados; reintentos y versiones conservados | test_drafts, test_submissions, test_listing_moderation y test_browser_beta_profile_journey |
| P09 | Publicar, rechazo/corrección, pausar/reanudar, renovar y retirar desde móvil/escritorio ES–EN | test_browser_beta_profile_journey: cuatro combinaciones de idioma/ancho; test_lifecycle: transiciones, confirmación y carreras |
| P10 | Teclado, errores y recarga comprobados en navegador, fotos privadas procesadas y derivadas autorizadas | test_browser_drafts, test_browser_submissions, test_browser_listing_moderation y test_photos |
| P11 | Ninguna operación sobre personas ajenas; particular/agencia/editor, MFA y consentimiento por persona conservados | test_drafts, test_submissions, test_listing_moderation, test_lifecycle, test_agency_publication y test_verification |

Las referencias de la tabla identifican pruebas. El resultado procede de la [auditoría terminal común](evidencias/b02b03-common-terminal-audit-20261020.json), que enlaza los doce criterios con nodeids concretos y aserciones revisadas:192PASS/0FAIL/0ERROR/0SKIP. Una coincidencia nominal no sustituye esa revisión.

## Selección común y aceptación

Resultado común034242:24selectores/192casos, sin exclusiones ni omisiones, fuentes congeladas y comparadas de nuevo, limpieza de contenedores/temporal/procesos y Telegram comprobados independientemente. Las ocho variantes de rectificación pasan.

Prerregistro local: `artifacts/beta-profile-20261020/common-selection.json`, selección ampliable a los módulos de derechos afectados por la etiqueta voluntaria, PostgreSQL/Redis reales propios, dos workers funcionales, snapshots de fixtures aislados y broker aislado por caso. Se conserva la selección literal en el resultado del runner. No es una medición de capacidad ni sustituye B07/B16.

Exigir cero fallos y cero omisiones en todos los casos seleccionados, fuentes congeladas, limpieza de procesos/servicios y recibo Telegram terminal confirmado. Auditar JUnit/journal y las huellas del runner sobre una sola candidata. Los resultados anteriores de selecciones diferentes y el negativo del montaje de navegador permanecen separados; no sumarlos como batería común.

El recorrido de navegador usa cuenta, consentimientos y foto inicial sintéticos preparados. La ventana de renovación se abre ajustando sólo la caducidad sintética con una conexión real independiente; las acciones, decisiones y visibilidad se ejercitan por HTTP/navegador. No desactivar la protección asíncrona de Django ni sustituir autorización o PostgreSQL por simuladores.

## Límites de cierre

B02/B03 quedan aceptados localmente al verificarse esta matriz y sus evidencias, según acta12. Los atributos físicos adicionales y preferencias/recomendaciones B15 continúan diferidos conforme al contrato previo por atributo; no se infieren de imágenes ni se añaden datos sin revisión de finalidad/exposición. La asignación de tipo de perfil es voluntaria y no constituye verificación de identidad.

El siguiente bloque B04–B06 conserva su alcance: vocabulario de renovación/autosubida, exposición promocional, favoritos/sitemap y otras superficies. Esta matriz no acepta capacidad, operación ni beta completa. B00 mantiene auditoría exhaustiva residual; G01–G08 y usuarios/proveedores/pagos reales permanecen separados.
