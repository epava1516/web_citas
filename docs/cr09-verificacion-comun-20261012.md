# CR09 — correspondencia de verificación común

Fecha: 2026-10-12. Versión reservada `bd5a81f`; ejecución propia
`20261012-165613-ee1f4787`, perfil regression. Este documento fija cómo revisar
su resultado, no declara pruebas pasadas ni aceptación. La única cola sigue en
[seguimiento17](17-seguimiento-desarrollo.md). Requisitos: [contrato16](16-contrato-ejecucion-desarrollo.md)
y [matriz83](83-auditoria-pendientes-cr09.md); límites históricos: [matriz88](88-matriz-cierre-derechos.md).

## Requisitos, recorrido observable y evidencia exigida

Los nombres de nodo identifican ejemplos críticos cuya implementación se ha
contrastado. Cada archivo aporta además sus variantes/negativos; no se limita
la batería a estos ejemplos ni se acepta un bloque desde un solo nodo.
Todos los resultados comunes siguientes están **pendientes del JUnit terminal**.

| Bloque | Recorrido observable | Pruebas concretas de la versión común | Límite y decisión de aceptación pendiente |
| --- | --- | --- | --- |
| Acceso/portabilidad y respuesta privada | Preparador y revisor distintos; contenido exacto, cierre, descarga y replay; perfil/cuenta ES/EN | `test_rights_access_coverage_store::test_integrated_access_closes_and_downloads_a_reviewed_scoped_resource_fixture`, `::test_integrated_access_concurrent_closure_has_one_response_and_notice`; `test_rights_portability_response_mobile::test_mobile_final_response_preparation_and_independent_decision`; archivos de cierre/descargas/objetos | Fixture revisado verifica mecanismos; no acredita las 23 fuentes históricas ni identidad real. Descarga de una parte no es solicitud completa. |
| Derecho/finalidad/autoridad | Prueba vigente, representación, revocación, ejecución revisada y denegación; respuesta exacta con pendientes explícitos | `test_erasure_final`, `test_processing_final`, `test_rectification_final_localization`, `test_rights_verification`, `test_rights_actions_revocation_races`, `test_purpose_exception_late_authority` | La respuesta parcial no se transforma en derecho completo. Revisar finalidad y decisión por escenario; no ocultar criterios ausentes con progress. |
| Conservación por finalidad | Calendario/planes, vencimiento, seguimiento separado, purga/reintentos y autoridad después de espera | `test_retention_reviews::test_plan_schedules_all_retained_purposes_and_reconciliation_is_idempotent`, `::test_private_audited_independent_followup_preserves_original_plan_and_deadlines`; `test_retention_review_races::test_permission_revoked_during_observed_wait_prevents_disclosure`; `test_rights_final_draft_retention`, `test_rights_export_retention` | Parámetros sintéticos no fijan plazos jurídicos; scheduling productivo se acredita aparte. |
| Restauración PG/medios/comercial | Dump antiguo y medios propios, checkpoint independiente, aplicación de supresión y estado comercial no reactivado | `test_recovery_pg_restore::test_old_pg_dump_and_media_cannot_reintroduce_erased_data`; `test_promotion_recovery::test_real_restore_preserves_commercial_evidence_without_reactivating_erased_promotion`; familia recovery | Leer propiedades de tiempos/RPO/RTO y alcance real del fixture. No extrapolar capacidad/cadencia/custodia a producción. |
| Sesiones/cachés/colas/logs | Sesión caducada retenida sin capacidades; correo redactado; origen exacto y bloqueo de histórico incompleto | `test_rights_access_coverage_store::test_integrated_access_includes_retained_expired_session_without_capabilities`, `::test_integrated_access_includes_console_mail_without_authentication_link`, `::test_historical_log_selection_uses_audited_package_review_and_blocks_full_close`; familias scoped/retained/RDB/AOF | [Auditoría de cobertura](evidencias/cr09-auditoria-cobertura-comun-20261012.md): desconocidos necesarios siguen pendientes. No asociación por texto/conteos ni censo vacío ficticio. |
| Comunicaciones/destinatarios | Lectura y decisión independientes, aviso interno, consulta/acuse, serialización, gestor anterior sin autoridad y ES/EN | `test_rights_communications::test_review_is_independent_exact_audited_and_never_implies_delivery`, `::test_same_execution_delivery_serializes_and_old_authority_cannot_read`, `::test_mobile_recipient_assessment_source_is_audited_in_both_languages`; `test_historical_communication_candidates` | Revisar lagunas por escenario. Un aviso interno no acredita contacto/entrega externos; no borrar pending por aprobación favorable. |
| Urgencia/escalado | Primario revocado, suplente con autoridad, consulta auditada, decisión terminal y replay | `test_urgent_report_drill::test_urgent_owner_revocation_escalates_to_authorized_substitute`, `::test_report_decision_rechecks_revocation_after_scoped_locks`; alertas/cola | Simulacro sintético interno; reconocer no equivale a resolver ni prueba cobertura humana real. |
| Expedientes grandes | Contenido, autoridad, bytes, etapas y recursos del escenario extremo | [Medición MOD08](evidencias/mod08-lectura-fresca-medicion-20261012.md), código c92fe64; controles de integridad/objetos/generación permanecen en regresión | Rendimiento aceptado provisionalmente por MOD09, raw FAIL conservado y deuda mejorable. No repetir por rutina ni usar esa excepción para aceptar seguridad/N3. |
| Aceptación integral y seguridad común | Todos los criterios necesarios, versión común, regresión, pruebas reales y trazabilidad; revisión de huecos | JUnit completo del gate; `test_rights_enforced_validation_seal::test_complete_enforced_login_validation_creates_and_replays_seal`, `::test_current_tamper_acl_or_proof_expiry_cannot_use_enforced_seal`, `::test_enforced_held_seal_still_rejects_real_external_object_corruption`; `test_object_repository_stream_read` | PG/Login/RustFS/Caddy reales cuando el caso los requiere. Verificar ejecución, skips y recursos; archivos o inspecciones estáticas no prueban PASS. CR09/N3 siguen abiertos. |

## Exclusiones y evidencia todavía separada

Regression excluye exactamente short/measured de `test_contract_http_load`,
`test_rights_portability_large_history` y `test_publication_state_tcp`. Su PASS
no sustituye N3 ni ninguna carga necesaria omitida. La lectura pública conserva
su aceptación previa en su alcance; cualquier ensayo común necesario debe ser
secuencial, sin otra carga y con criterios/recursos prefijados. La excepción
MOD09 no acepta el SLO público ni convierte el historial grande en PASS.

Los experimentos optativos y sus skips no se reetiquetan como ejecutados. Las
restauraciones deben utilizar PG real propio y conservar inventario/huellas y
objetivos observados. No sumar versiones diferentes para reclamar una batería
común; documentar qué comparte la misma fuente y qué controles previos solo se
reutilizan en un alcance acotado.

CR10 dispone de mecanismos locales comerciales y pruebas en la misma suite;
no se acepta su fase desde este mapa. [Inventario GS01](97-inventario-estados-gs01.md)
y [borrador del acta](96-acta-gs01-borrador.md) siguen sin emitir. Las entradas
productivas —operador, políticas, proveedores, identidad, custodia y censo real—
permanecen separadas de la aceptación técnica local, sin publicar ni datos reales.

## Conservación actual de las fuentes conocidas

[Comprobación de ciphertexts](evidencias/cr09-origenes-historicos-preservacion-20261012.json):
los23 originales declarados conservan bytes/SHA, permisos privados y estabilidad
en esta observación. No se descifraron, no se tocó SQL ni servicios normales.
Esto permite reutilizar sus recibos en su alcance; no acredita asociación de
los registros al sujeto, no habilita cierre/entrega y no excluye ningún original.
