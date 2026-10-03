# Evidencias de desarrollo

## Inicio y BASE, 2026-10-03

Usuario autorizó ejecutar contrato completo. Baseline: 18 documentos de planificación, ningún código ni Git. Se inicializa Git local sin commits; documentación preservada. AGENTS.md referencia contrato de delegación externo para próximas sesiones.

Python host 3.9 no compatible: uv usa Python 3.12.13 local; imagen 3.12-slim resolvió 3.12.15. Django resuelto 5.2.17; versiones exactas en uv.lock. Compose levantó PostgreSQL17 y Redis7.4 con healthchecks reales. Migraciones y bootstrap legal ejecutados sobre PostgreSQL. Imagen Docker inicial construida no-root; verificación integrada final en curso.

BASE sigue parcial: fixtures de agencia/modelos y contratos restantes se completarán al existir sus modelos. No cobertura territorial nacional ni datos reales.

## Delegación Claude 1/3

Tarea cr01-security-design, CLI2.1.288, contrato1.0.1, 300 segundos máximos, propuesta sin herramientas. Adaptador devolvió exit66: STATUS complete incompatible con UNRESOLVED_ISSUES no vacío. Resultado rechazado; no ejecución de pruebas ni modificaciones atribuibles a Claude. Sin reintento. Codex revisa posibles escenarios y verifica implementación localmente. Evidencias brutas permanecen fuera del repositorio en arquitectura_codex/.ai/results; no son aceptación.

## CR-01 en verificación

Implementación: cuentas con correo único case-insensitive PostgreSQL, contraseña Argon2, aceptación versionada, confirmación/recuperación/reenvío, CSRF, throttle, sesiones y políticas no-store. Legal SSR ES/EN con textos sintéticos explícitos. Modelo de tokens con huella de usuario y consumo transaccional. Documento de interfaces en contratos/01-cuentas-legal.md.

Pruebas detectaron y corrigieron política de referer sobrescrita por middleware y no-referrer incompatible con Origin/CSRF en Chromium (usamos same-origin). Tests de email ejecutan transacciones reales para comprobar callbacks on_commit. Concurrencia usa conexiones independientes y cierre explícito.

Suite CR-01: 16 passed en 14.47s, PostgreSQL17 y Chromium headless. Incluye dos idiomas móvil, confirmación GET sin consumo, recuperación, invalidación/replay/concurrencia, legal actualizado, email case-insensitive y fallos SMTP indistinguibles. Ruff/check/makemigrations limpios; pip-audit sin vulnerabilidades conocidas. No auditoría independiente de seguridad.

Smoke Docker real: /health/ ok, HTML200 y CSS200 detrás Caddy, UID10001(app), worker Celery respondió pong. Puerto8080 ya ocupado por servicio ajeno: se eligió18080, sin tocar servicio existente. Primer smoke se lanzó antes de arranque completo; segunda inspección confirmó procesos y respuestas. Compose es local, no despliegue público.

## CR-02
Agencias, personas y asignaciones con aislamiento servidor; invitaciones por email limitadas y consumibles, revocación inmediata; MFA TOTP cifrado, recuperación hash y bloqueo replay. Tres pruebas de integración permisos/MFA pasan junto a CR-01: 19 passed en19.08s. Recorrido navegador específico agencia/MFA completado: añade dos personas y conserva datos tras recarga. Suite ampliada final: 21 passed en24.11s, incluido consumo concurrente de código de recuperación e imposibilidad de eludir actualización legal cambiando al idioma de traducción antigua. BASE fixtures completos todavía pendiente. Interfaces en contratos/02-agencias-mfa.md.

No afirmar cierre del proyecto ni preparación de producción.

Auditoría al incorporar cifrado detectó avisos en cryptography47: actualizado a50.0.2 (versión mantenida). [Aviso oficial](https://github.com/pyca/cryptography/security/advisories/GHSA-537c-gmf6-5ccf), [release PyPI](https://pypi.org/project/cryptography/50.0.2/). Se repiten suite y build afectados. Infra delegación verify-ai:20 tests passed, gates passed; no nuevas invocaciones Claude.

Tras actualizar cryptography: suite21 passed en24.13s, Ruff limpio, pip-audit sin vulnerabilidades conocidas; imágenes app/worker reconstruidas y reiniciadas correctamente con50.0.2. Estado de entrega: CR-01/02 verificados local; siguientes CR pendientes y BASE fixtures parcial.

## CR-03, 2026-10-03
Migración0004 aplicada sobre PostgreSQL. SSR de particular, consentimientos específicos, simulador de edad y OTP, revocación y transferencia. Eventos firmados/idempotentes vinculados a gestor/sujeto; teléfonos únicos por gestor con compartición en agencia. Pruebas dirigidas7 passed en21.56s, incluido navegador móvil particular y bloqueo ante fallo/revocación; suite común y teléfono concurrente en ejecución. Campos privados no pasan a fichas públicas (estas aún pendientes). Interfaces y límites en contratos/03-verificacion-representacion.md.

Cierre local CR-03:27 passed en35.26s, sin saltos; carrera de contacto entre particulares produce un éxito y un conflicto, una sola PhoneClaim. Reenvío OTP invalida código anterior; ajeno no accede. Ruff/check/makemigrations/diff-check limpios. No prueba real de SMS/edad ni cierre del contrato completo.

## CR-04
Módulos catalog/listings, migraciones aplicadas, catálogo seed idempotente y geografía DEMO. Wizard SSR privado con controles de compatibilidad, CP, tarifas consult/fixed/from, aceptación publish y versiones de edición/gestor. Start concurrente produce una sola Listing y Revision. Campos de contacto proceden de PhoneClaim; POST no puede sustituir teléfono por otro. Prueba móvil completa de borrador con consulta y limpieza de ubicación dependiente pasa. Importador geográfico con rollback/licencia/version probado. Primera batería4 passed en6.56s, importador+navegador3 passed en8.37s. Regresión ampliada en proceso. Fotos/envío todavía pendientes CR-05/06.

Cierre local CR-04:35 passed en49.54s sobre PostgreSQL17 y Chromium, sin saltos. Model CheckConstraint probado impide fixed con amountNULL. Scope vigente completo aún no terminado; siguientes CR y gates pendientes.

## CR-05
Mediafiles: originales privados deduplicados SHA, Photo por revisión, derivados WebP recodificados sin EXIF, permisos/orden/retirada y cuotas. Celery/Redis/Beat real, recuperación persistida e idempotencia de reintentos. Similaridad regional y ORB sin reconocimiento facial. Suite común56 passed en68.68s; suites dirigidas20 passed en16.39s, incluida calibración sintética limitada. Reproducción de carga tardía durante comparación corregida y cinco tests de fotos pasan en13.43s; regresión dirigida final en curso.

Prueba Docker: una imagen geométrica sintética cargada desde app con almacenamiento privado compartido se procesó en worker, taskSucceeded en1.132s; DB confirmó ready, comparison_complete=true, derivative_present=true y attempts1. Beat recibió/ejecutó recover_media_jobs. Datos de prueba bajo cuenta inactiva synthetic-worker-probe, sin personas reales ni datos biométricos.

Delegación2/3, cr05-crop-matching: adaptador exit0, informe complete válido, ningún archivo/test ejecutado por Claude. Codex leyó fuente propuesta, integró módulo puro, adaptó serialización JSON de tuplas y validó candidatos/confirmaciones con16 tests propios. Aceptación local de propuesta acotada; no aprobación global de Claude ni sustituto de revisión independiente. Evidencia bruta externa/ignorada; módulo integrado y límites en contratos/05. Última invocación reservada para revisión final.

Cierre local CR-05: suite58 passed en74.61s sin saltos; seis pruebas de fotos passed en13.76s. Incluye coincidencia exacta global particular/agencia con distintos teléfonos y regresión de carga durante comparación. Se añaden dos pruebas de privacidad de logs passed en0.06s: borradores/fotos ocultan identificadores y no registran query strings. Ruff/check/migraciones limpios. Build Docker actualizado; no cierre técnico global ni preparación de producción.

## CR-06, primer flujo en curso

Envío de revisión y declaración explícita persistida por actor/documento/version, estado privado al recargar y bloqueo de edición/fotos posterior. Revalidación de edad, consentimiento vigente, teléfono, datos, catálogo, tarifas y procesamiento de fotos. Condiciones actualizadas requieren renovar aceptación y consentimiento directo; corregido el flujo de renovación sin cambiar gestor ni persona.

Pruebas dirigidas conjuntas:28 passed en44.53s, PostgreSQL/Chromium, sin saltos. Incluyen once pruebas de envío, recorrido móvil y regresión de borradores/fotos/representación. Primer ensayo paralelo de dos runners se interfirió en la misma base test: descartado como evidencia; repetido como un único proceso y aprobado. Primer selector de navegador confundía título con botón: corregido conforme a plantilla y recorrido pasó. Ruff/check/migraciones/diff limpios; migración0004 aplicada localmente.

CR-06 no cerrado: cola humana, agencias/transferencias, decisiones/reclamación, revisión sensible y publicación permanecen pendientes. Ningún anuncio se publica por enviar ni se afirma comprobación real de proveedores. No invocación adicional de Claude.

CR-06, comprobación de agencias: cola privada y permiso core.review_agency con MFA obligatorio incluso para revisor sin is_staff. Decisiones motivadas con referencia sintética, revisor, procedimiento y control de versión; titular/editor activo no puede revisar su agencia. Resultado simulator-v1 visible al titular y bloqueado en producción. Migración core0006 aplicada localmente; imagen Docker se actualizará junto al cierre integrado CR-06.

Cuatro pruebas de organización passed en6.71s. Recorrido navegador con contraseña/MFA y regresión de envíos/agencias:16 passed en31.87s; tras reforzar la coincidencia exacta de gestor en autorización directa,16 passed en29.69s. Sin skips. No aprobación de anuncios ni integración real de comprobación. Próximo: revisión de anuncios, transferencias, reclamación y publicación de versión aprobada.

Regresión específica de autorización ligada a gestor distinto:1 passed,11 deselected en4.93s; el envío rechaza una evidencia con manager_id obsoleto aunque coincida el contador de versión.

CR-06, anuncios: cola y revisión humana con permiso listings.review_listing/MFA y prevención de autoevaluación; decisiones motivadas y versión exacta aprobada. La aprobación vuelve a validar requisitos y rechaza coincidencias pendientes en ambas direcciones. Ficha y derivados públicos comprueban elegibilidad/caducidad; originales y borradores siguen privados. Revocación o transferencia pausa publicación dentro de la transacción y elimina disponible-ahora.

Seis pruebas servidor passed en15.69s. Recorrido navegador del moderador con contraseña/MFA, inspección de derivado, aprobación y ficha móvil pública, junto a regresión de representación:12 passed en29.67s. Regresión común:85 passed en121.91s, PostgreSQL/Chromium, sin skips. Ruff/check/migraciones/diff-check limpios; migración listings0005 aplicada localmente. Docker aún corresponde al cierre CR-05, se actualizará al cerrar CR-06 integrado.

No cierre CR-06: resolución de coincidencias, clonación/edición sensible, reclamación, revisión específica de transferencia y recorrido agencia completo siguen pendientes. Las integraciones de verificación continúan simuladas; no preparación real de producción ni publicación externa.

CR-06, revisiones y coincidencias: source_revision y approved_base; filas/catálogos/tarifas/fotos de revisión propia, Blob reutilizado y comparación exacta global también al clonar. Aceptación/exposición/contactos se reinician. IDs de tarifas ajenos se rechazan. Versiones pendientes obsoletas no reemplazan aprobaciones nuevas y se archivan con motivo para liberar cuota. Corrección de revisión rechazada conserva su contenido.

Resolución humana false_positive/distinct_people/conflict, con referencia/motivo/revisor/historia, permisos/MFA y conflicto de interés en cualquiera de las personas. SHA exacto no es falso positivo visual. Decisión cubre ambos sentidos existentes de la pareja; conflicto confirmado pausa exposición y sigue bloqueando aprobación sin suspender cuentas. Limpiar conflicto no republica automáticamente.

Primer conjunto14 passed en37.84s; dos nuevos recorridos navegador y resolución7 passed en39.73s. Regresión borradores/fotos21 passed en58.55s; después de archivar versiones pendientes obsoletas y exigir decisión explícita en formularios,21 passed en63.74s (incluye organizaciones, moderación y navegador). No skips. Un antiguo test esperaba solo una señal dirigida; actualizado para comprobar detección SHA de ambos sentidos y conservación de un único Blob. Primer test navegador intentó consultar ORM dentro del bucle Playwright: corregido para usar el ID de la URL real sin desactivar protección async; recorrido pasó.

Migraciones listings0006/0007 y mediafiles0005 aplicadas sobre PostgreSQL local. Ruff/check/migraciones/diff-check limpios. CR-06 incompleto por reclamación, revisión específica de transferencia y recorrido completo de agencia; Docker se reconstruirá al cierre integrado. No verificación real/proveedor ni producción completa. Claude continúa2/3, sin delegación nueva.

Regresión de corrección rechazada con título distinto:1 passed en6.08s; crear borrador conserva el contenido rechazado y su linaje, mientras la ficha pública conserva la versión aprobada.

CR-06 transferencia, integración parcial: manager_review_status=pending tras traslado, revisión humana con permiso/MFA, versión/motivo y registro único persona/versión. Renovar edad/autorización/contacto no habilita publicación antes de aprobar el gestor. Cinco regresiones passed en9.41s y prueba dirigida passed en5.77s. Migración core0007 aplicada. Pendientes antiguo gestor, navegador, agencias y reclamaciones; no cierre de etapa ni producción.

CR-06, conflicto del gestor anterior: la transferencia guarda snapshot previous_manager_kind/id; revisión excluye titular y editores anteriores incluso revocados. Registros legacy se contrastan con snapshots previos; origen desconocido no habilita revisión. Migración core0008 aplicada. Derivados privados del gestor exigen revisión ligada a manager_version vigente, impidiendo acceso a fotos privadas del gestor anterior tras traslado.

Regresión gestor/representación8 passed en15.97s; pruebas ampliadas de snapshot/legacy5 passed en13.48s; tras protección de fotos, conjunto gestor/fotos11 passed en23.52s, sin skips. Ruff/check/migraciones/diff limpios. Pendientes idempotencia/concurrencia del propio formulario de transferencia, navegador, recorrido completo de agencia y reclamaciones. CR-06 sigue en curso; Docker no reconstruido todavía.
