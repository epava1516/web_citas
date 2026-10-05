# Limitación y oposición por finalidad

Estado: desarrollo en verificación; CR09 abierto. Complementa cautela de publicación, docs40/51/57. No equivale a ejecución integral ni aceptación jurídica.

## Requisitos y fundamentos

Fuentes primarias revisadas2026-10-05: [AEPD limitación](https://www.aepd.es/preguntas-frecuentes/1-tus-derechos/2-tus-derechos-de-proteccion-de-datos/FAQ-0112-que-es-el-derecho-a-la-limitacion-del-tratamiento-de-datos), [AEPD oposición](https://www.aepd.es/derechos-y-deberes/conoce-tus-derechos/derecho-de-oposicion), [RGPD artículos18/19/21](https://eur-lex.europa.eu/eli/reg/2016/679/2016-05-04/spa). Limitación y oposición requieren procedimientos diferenciados; no presuponer que toda oposición obliga a borrar cuenta o que todo registro conservado permite tratamiento ordinario. El levantamiento de limitación requiere comunicación previa; las excepciones deben motivarse por finalidad y alcance.

La cautela de publicación existente protege exposición editorial; quedan otros tratamientos. Preparar decisiones restrict/cease/continue/review para todas las finalidades del inventario seleccionado, con fundamento, ámbito, motivo minimizado y fecha de revisión futura. Fecha técnica máxima365 días no fija plazo jurídico ni sustituye plazo de respuesta.

## Preparación implementada en verificación

ProcessingPurposePlan0067 registra acción/prueba/ámbito excluyente Person o User, HMAC y plan cifrado. Servicio processing_plans.prepare exige moderador asignado, permisos de revisión/ejecución, MFA/sesión recargados, COI, lectura completa vigente de expediente/respuestas y comprobación proporcional vigente del mismo derecho. Clave exacta reproduce registro; firma distinta deniega. Cada finalidad seleccionada debe estar presente una sola vez. Snapshot declara partial=true/enforced=false; no cambia datos, publicación, fechas de solicitud ni estado del caso. Prueba de identidad sigue simulada en fixtures.

## Continuación obligatoria antes de aceptación

- Fuente estable: excluir registros generados por esta misma preparación, incluir cambios externos pertinentes y planes de otros expedientes; probar causalidad y cambio intercalado.
- Pantalla privada ESEN de preparación/consulta auditada, errores, aislamiento y recarga; no entregar fundamentos por GET.
- Revisión independiente actual por finalidad antes de ejecución; mostrar cobertura real/pending sin dar autoridad a un simple JSON.
- Registro durable de restricciones por ámbito/finalidad y autoridad de excepciones; integrar en operaciones servidor, trabajos y lecturas ordinarias. Conservación no implica autorización de uso.
- No bloquear indiscriminadamente autenticación, seguridad o canal de derechos ni alterar responsabilidades de agencias; tratamientos compartidos requieren evaluación explícita.
- Caducidad operativa no levanta restricciones automáticamente. Propuesta/revisión/comunicación previa de levantamiento, comprobación fresca y ejecuciones idempotentes.
- Inventario/retención de nuevas decisiones, avisos pertinentes, respuesta final y conciliación de restauración.
- Pruebas de concurrencia, permisos revocados durante espera, perfiles/cuentas sin perfil, móvil ESEN, worker/Docker y regresión común.

## Ejecución activa

39549: batería PostgreSQL3 casos, /tmp/processing-plans.xml. Fuente funcional congelada hasta resultado terminal.0067 no aplicada al runtime normal, aún70114b2/0066. No UI ni ejecución verificadas. No nuevas delegaciones; Claude3/3.


39549 terminal1:3 fallidas35,21s, helper de prueba consultaba fuente fuera de transacción exigida, antes de preparar plan. Helper transaccional corregido; fuente de cuenta excluye processing_prepare solo en expediente actual restriction/object para evitar autoinvalidación, operaciones ajenas siguen incluidas.69056 repetición activa3 casos /tmp/processing-plans-final.xml; fuente congelada.0067 no runtime ni preparación aceptada.


69056 terminal0:3 correctas36,34s PostgreSQL, sin fallos/errores/skips. Cuenta propia restriction/object genera preparación cifrada/parcial/no ejecutada, replay único y firma distinta denegada; no modifica datos/estado/plazos. Comprobación invalidada y usuario sujeto sin permiso denegados. Ruff global/diff limpios. No acredita UI, revisión/ejecución, causalidad completa ni concurrencia;0067 no runtime. CI calendario70114b2 run37257818467 confirmada in_progress; recuperar mismoID. Continuar pantalla/consulta versionada, fuente externa/validación robusta y demás flujo antes de cierre.


Preparación conectada GET/POST processing_prepare /es|en/moderation/rights/<UUID>/processing/: GET no revela snapshot, preview audita antes de consultar y guarda snapshot cifrado reproducible; prepare exige digest consultado vigente, decisiones y nuevo key. Replay incorpora digest a firma. processing_preview/prepare excluidos solo fuente del mismo caso restriction/object para evitar causalidad circular; otros casos permanecen observables. Validación operación no textual deniega de forma controlada.83760 terminal0:5 propias49,39s PG, incluyendo HTTP/recarga/idempotencia/digest estable tras preparar/deriva de favorito409/entrada malformada. Check5685 terminal0, no cambios de migraciones; Ruff/diff limpios. Móvil ESEN preparado en tests/test_processing_mobile.py y arrancado /tmp/processing-mobile.xml, fuente funcional congelada hasta terminal.0067 no runtime; revisión/ejecución independientes siguen pendientes.


94523 terminal0:2 móviles ESEN correctas38,77s Chromium390x844, login/MFA→lectura actual→preview de finalidades→decisiones→registro→reload sin snapshot/motivos, sin overflow. Preparación parcial/no ejecutada y caso reviewing comprobados; no sumar5+2 como suite común. Ruff/diff limpios. Ningún pytest activo. Siguiente consulta auditada/revisión independiente vigente del plan y restricciones efectivas, pruebas de fuente/permisos durante espera, runtime0067/regresión conjunta. CI70114b2/37257818467 confirmada in_progress, anterior a preparación0067.


Revisión por finalidad0068 implementada en verificación: ProcessingPlanRead/Review con acción/prueba/HMAC y permiso independiente review_processing_plan. processing_review.record bloquea caso/ámbito/plan, recarga permisos/MFA/sesión, exige comprobación vigente de mismo derecho y fuente/digest actuales; consulta audita antes de descifrar y verifica firma original de decisiones. Revisión requiere lectura vigente propia y autor diferente del preparador; única por plan/replay exacto, motivo cifrado. No aplica tratamientos ni cambia plazos/estado de expediente. Pantalla privada processing_review GET sin fundamentos, POST inspect/review. Cuenta fuente excluye lecturas del mismo expediente restriction/object y acciones processing_* para evitar autoinvalidación por consulta; esto no excluye cambios de datos o pruebas.2406 activa7 casos /tmp/processing-review-common.xml, fuente congelada.0067–0068 no runtime; falta móvil/carreras y aplicación efectiva.


2406 terminal0:7 conjuntas55,36s PG, consulta/revisión HTTP, idempotencia/recarga, autor propio denegado, firma del cifrado alterada y fuente cambiada denegadas. Check18294 terminal0/no cambios migraciones. Tras terminal reforzado: aprobado exige ninguna decisión review pendiente; rechazo motivado permitido. Prueba de deriva de fuente separada de cifrado alterado restaurando original antes de mutar favoritos.89859 repetición8 activa /tmp/processing-review-final.xml; fuente congelada. CI calendario37257818467 confirmada in_progress. Ninguna aceptación CR09 ni ejecución de tratamientos.


89859 terminal0:8 conjuntas61,44s PostgreSQL, sin fallos/errores/skips; preparación/revisión y guardas pendientes/digest/fuente/control de autor verificadas juntas. Aprobación sin inspección409, inspección idempotente y GET sin decisiones, revisión única replay, modificación de decisiones cifradas denegada sin lectura durable, deriva real de favoritos denegada con cifrado original y plan pendiente solo admite rechazo. Ruff/diff limpios. Ningún pytest activo. Siguiente móvil/carreras de revisión, finalidades perfil y ejecución efectiva de restricciones/avisos/respuesta final;0067/0068 no runtime, cambios sin commit. CR09/contrato abiertos.


Revisión ampliada:90045 terminal1,3 correctas/1 fallida44,87s PG; fuente de test bloqueaba plan→insertaba Favorite y su FK esperaba User que ya retenía revisión User→plan, inversión artificial de locks. Ensayo fuente corregido para retener User antes de cambiar favoritos; permiso/prueba/replay sobre plan ya pasaron. Bloqueo de consulta restringido OF self para no retener joins de action/proof sin necesidad.87354 activa9 casos carreras/revisión/móvil ESEN /tmp/processing-review-expanded.xml; fuente congelada. Build imágenes iniciado /tmp/processing-build.log, no migración/recreate normal antes de terminal.0067/0068 no aceptadas aún.


87354 terminal0:9 conjuntas87,08s PG/Chromium, cuatro carreras con bloqueo observado (permisos/fuente/prueba/replay), tres revisión y dos móviles ESEN. Login/MFA→lectura vigente→consulta plan→aprobación independiente→reload oculta fundamentos, sin overflow y plazos/estado intactos. Build1786 terminal0 app/worker/Beat, sin recreate aún. Nuevas variantes perfil restriction/object preparadas y arrancadas /tmp/processing-profile.xml; verificar antes de runtime/aceptación. No sumar5+9/2 como suite completa. Claude3/3; CR09 abierto.


86731 terminal0:2 variantes perfil restriction/object correctas33,29s PG; preparación y aprobación independiente conservan Person.manager_version/rights_version/agencia, Listing.estado/lifecycle y caso/plazo. Makemigrations82659 terminal0 sin cambios. Regresión propia conjunta18 casos iniciada /tmp/processing-purpose-common.xml; fuente congelada hasta terminal. Runtime migración0067/0068 iniciado con imagen actual, comprobar handles y no aceptar antes de check/hashes/recreate y batería terminal. Ejecución efectiva de tratamientos/avisos/respuesta final continúa pendiente.


Runtime0067/0068: migración49229 y recreación49018 terminal0; check/migrate--check73741 terminal0 limpios. Auditoría hashes64879 /docs/evidencias/preparacion-finalidades-runtime.json en comprobación. Regresión17962 confirmada activa18 casos /tmp/processing-purpose-common.xml; fuente funcional congelada, no reiniciar por demora ni aceptar antes de terminal. Ejecución/bloqueo de finalidades no implementados aún, interfaz declara preparación/revisión sin efectos; CR09 abierto.

64879 terminal0:11 fuentes iguales host/app/worker/Beat,UID10001,health200,0068 aplicada/proveedores disabled. Evidencia preparacion-finalidades-runtime.json.17962 sigue pendiente de terminal; cambios sin commit.


17962 terminal0:18 conjuntas137,44s PostgreSQL/Chromium sin fallos/errores/skips, fuente final preparación/revisión propia. Runtime0067/0068 y11 hashes/UID10001/health200/check/proveedores disabled verificados por separado. Ruff global/diff limpios. Evidencias preparacion-finalidades-regresion.json/runtime.json. No hay pytest activo. Preparación/revisión verificada localmente, ejecución efectiva y alcance integral/avisos/levantamiento/respuesta final siguen pendientes. Próxima entrega ledger durable por ámbito/finalidad, guardas en operaciones ordinarias y supresión para conservar material limitado, excepciones auditadas y levantamiento comunicado; no bloqueo indiscriminado de login/seguridad/canal de derechos ni expiración que levante automáticamente. CR09/contrato abiertos; Claude3/3.
