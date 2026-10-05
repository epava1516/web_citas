# Calendario y revisión de conservación por finalidad

Estado: implementación en verificación. Complementa docs/26–27, docs/40 y docs/53–56. No acepta conservación integral, limitación/oposición ni cierre CR09.

## Fundamento y separación de decisiones

El principio de limitación de conservación exige vincular el tiempo necesario a las finalidades; una fecha de calendario no proporciona por sí sola fundamento para seguir tratando datos. Fuentes primarias consultadas2026-10-05: [RGPD, artículo5.1.e](https://eur-lex.europa.eu/legal-content/ES/ALL/?uri=CELEX%3A32016R0679) y [principios de tratamiento AEPD](https://www.aepd.es/preguntas-frecuentes/2-tus-obligaciones-como-responsable-del-tratamiento/4-los-principios-del-tratamiento/FAQ-0207-que-principios-debo-cumplir). La limitación del tratamiento tiene su procedimiento específico: [AEPD](https://www.aepd.es/preguntas-frecuentes/1-tus-derechos/2-tus-derechos-de-proteccion-de-datos/FAQ-0112-que-es-el-derecho-a-la-limitacion-del-tratamiento-de-datos).

RetentionReview materializa cada finalidad retain/review del plan con fecha original, próxima revisión operativa, responsable y versión. Se crea en la misma transacción del plan; unicidad plan/finalidad y operación restringida. Erase/redact no generan revisiones de conservación. La fecha original y la decisión cifrada del plan permanecen intactas; actualizar seguimiento no amplía conservación ni vencimientos de derechos y no rehabilita un plan de supresión vencido.

## Consulta y seguimiento

Rutas privadas ES/EN: GET /moderation/rights/retention/ con filtros due/soon/all y paginación50, GET/POST /moderation/rights/retention/<review_id>/. Requieren review_rights_request, permiso específico review_retention y MFA actual; aplican COI del expediente incluso con cuenta ya suprimida. GET ofrece metadatos, sin fundamentos/motivos. El responsable inicial es autor del plan; la revisión independiente asigna responsabilidad de siguiente seguimiento a su autor.

POST inspect requiere lectura auditada completa y actual del expediente y sus respuestas, versiones de caso/revisión, clave y motivo minimizado. Se crea evento de auditoría antes de descifrar/disponer la finalidad y seguimientos previos paginados de50 en50. Todas las páginas actuales deben consultarse antes de seguimiento. Resultado de consulta cifrado permite replay del mismo snapshot, sin entregar notas añadidas después mediante una clave antigua. El registro se confirma antes de entregar respuesta; fallos revierten evento/operación.

POST follow_up exige consulta previa de esa finalidad por el mismo revisor y versiones/HMAC actuales; autor distinto al creador del plan. Registra razón cifrada, próxima fecha operativa futura acotada por365 días técnicos, responsable, fecha y versión; mantiene pendientes las decisiones de procesamiento. Esa cota no es un plazo legal. Permisos/MFA/sesión se recargan tras locks y se revalidan antes de responder. Clave repetida retorna misma actuación, cambio de firma/versiones/fuente deniega; motivos no se entregan al acuse público.

## Conciliación y límites

reconcile_retention_reviews, programada cada60s en Beat, crea entradas ausentes para planes históricos con fechas o calendarios parcialmente perdidos; retention_purpose_count se registra en plan y comparación por subquery identifica faltantes sin sobrescribir entradas existentes, por lotes100 y locks SKIP LOCKED OF self. get_or_create no sobrescribe seguimientos existentes. Plan cifrado inválido o firma incoherente no se utiliza y se cuenta failed sin exponer cuerpos; no borra ni cambia fechas. Una transacción evita creación parcial durante una tanda de plan.

El calendario mantiene seguimiento después de suprimir acceso a cuenta o cerrar estado de solicitud, sin adquirir nueva autoridad para exportación/rectificación/supresión. Falta completar decisiones de conservación restringida sobre datos reales del alcance, evidencias/otras dependencias, reconciliación de restauración, limitación/oposición y respuestas finales. Los artefactos nuevos de consulta/seguimiento requieren su propia conservación auditada; no ampliar recursivamente la fuente del plan actual.

## Verificación en curso

Migración0066 creada sin aplicar al runtime normal. Primera batería53282 terminal1:9 correctas/2 fallidas103,47s, incluyendo7 planes previos. Ambos fallos antes de HTTP: el test enviaba None como campo multipart. Corregido para omitir fecha en inspect. Fuente reforzada después de terminal para recargar permisos/MFA, auditar antes de descifrar y guardar snapshot cifrado de consulta/historial.

31719 en curso4 propias PostgreSQL, XML /tmp/retention-reviews-final.xml. Pruebas móviles/concurrencia y regresión afectada pendientes. Tarea invocada directamente en pytest no acredita worker/Beat; ensayo operativo no vacío pendiente. Docker actual e3d7d46 anterior a0066, no runtime ni CR09 aceptados.

31719 terminal0:4 propias45,91s. Tras terminal, historial paginado/snapshots inmutables/lectura completa requeridos añadidos;25089 terminal0:5 propias51,53s. Conciliación parcial reforzada con retention_purpose_count en plan0066 y subquery de recuento;5677 terminal0:6 propias58,80s, sin fallos/errores/skips. Repara entrada perdida sin cambiar seguimiento existente. No sumar baterías; fuente actual necesita carreras/móvil/regresión/runtime/worker no vacío. Test de carreras preparado y arrancado /tmp/retention-review-races.xml; fuente congelada hasta terminal.0066 sin runtime, CIe3d7d46/37255516267 confirmada in_progress.


Calendario0066: carreras recuperadas por XML terminal /tmp/retention-review-races.xml,2 correctas32,242s sin errores/fallos/skips. Móvil69451 /tmp/retention-mobile.xml:2 correctas41,43s ESEN Chromium390x844, login/MFA real→consulta actual→calendario→consulta auditada→seguimiento independiente→reload sin motivos→consulta de historial; sin overflow, una actuación y originales/plazos intactos. Makemigrations58726 terminal0 sin cambios; Ruff/diff limpios. No sumar baterías separadas. Docker0066/workerBeat no vacío/regresión común y conservación integral permanecen pendientes.


Calendario operativo: script aislado scripts/probe_retention_calendar_worker.py preparado; Ruff limpio. Build34693 terminal0 app/worker/Beat; no recreate runtime normal aún. Probe19325 confirmada activa, salida /tmp/retention-calendar-worker.log, base/cola temporal retention_calendar_probe_*; no reiniciar por demora. Regresión49427 confirmada activa20 casos /tmp/retention-calendar-common.xml, fuente funcional congelada. CI37255516267/e3d7d46 y37254868083/5d9110f completed success confirmado por gh; no acreditan calendario0066 actual. Pendiente normalizar logs/resultados CI.


Calendario0066 verificado localmente:49427 terminal0,20 conjuntas172,50s PostgreSQL/Chromium sin fallos/errores/skips. Probe19325 terminal0:worker crea2 y replay0; Beat automático crea segunda tanda,total4; originales/auditoría conservados, sin cambios de cuenta ni identidad aprobada. Base temporal ausente confirmada PostgreSQL. Runtime build43515/recreate4039/check66611/hash5178 terminal0,0066 aplicada,12 fuentes iguales host/app/worker/Beat,UID10001/health200/proveedores disabled. Ruff global limpio tras ordenar imports0066 (sin cambio semántico), collectstatic130 sin cambios. Evidencias calendario-conservacion-{regresion,worker,runtime}.json. CI anteriores normalizadas:5d9110f604p2020,34s y e3d7d46606p1710,65s; anteriores al calendario. Conservación integral/limitación/oposición/copia integral/respuestas finales y CR09/contrato permanecen abiertos.
