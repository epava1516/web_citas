# N06F — prerregistro de referencias de las transiciones restantes

25 de octubre de 2026. [Conciliación372](372-n06-e-conciliacion-acciones-variantes-20261025.md):20/41rutas con alguna referencia,21sin ella; N06abierto. Aplicación f03eea8, panel371adoptado, sin candidato nuevo. MOD09restante diferido por usuario367. Refresco semántico focal del protocolo/matriz/cola y congelación antes de medir; AST de aplicación e instrumento existentes preservados.

## Selección fija y motivo

Una pasada diagnóstica de once selectores originales, doce casos por la variante ES/EN de perfil. No se crean/copían pruebas, no se recortan fixtures/oráculos y no se repite por mera documentación: se obtiene referencia HTTP que antes no se registró. Selección:

- `tests/test_accounts.py::test_updated_terms_gate_retains_old_acceptance_and_supports_other_language`
- `tests/test_accounts.py::test_resend_invalidates_older_token`
- `tests/test_accounts.py::test_reset_one_use_expiry_and_existing_sessions_invalidated`
- `tests/test_verification.py::test_individual_prerequisites_persistence_phone_replay`
- `tests/test_verification.py::test_agency_direct_consent_shared_phone_and_transfer`
- `tests/test_agencies_mfa.py::test_mfa_enrollment_replay_and_recovery`
- `tests/test_agencies_mfa.py::test_two_models_editor_scope_and_revocation`
- `tests/test_manager_review.py::test_transfer_requires_current_human_review_before_readiness`
- `tests/test_agency_appeals.py::test_agency_appeal_reopens_without_verification_and_preserves_original`
- `tests/test_manager_appeals.py::test_manager_appeal_independence_persistence_and_no_auto_publication`
- `tests/test_profile_status.py::test_pending_changes_do_not_replace_published_profile_guidance`

Se reutiliza scripts/http_operation_metrics.py con --observe-http-operations. La observación cubre Client.request durante el cuerpo; las fixtures normales anteriores y las peticiones Playwright no entran. Las fixtures dinámicas dentro del cuerpo sí pueden incluir operaciones adicionales; conservar caso/ordinal/método/ruta/estado y no atribuirlas automáticamente al objetivo principal. La selección completa se conserva, incluidos efectos directos fuera del reloj.

## Datos, oráculos y presupuestos

Datos originales sintéticos, documentos/contraseñas/tokens de prueba, actores independientes, MFA y versiones, perfil pendiente junto a versión pública y estado después de transferencia. Preservar términosactualizados/aceptación anterior, reenvío que invalida token previo, reset de un uso/caducidad/sesiones viejas, consentimiento vigente, teléfono compartido con sujetos separados, no autoaprobación de transferencia/reclamación y privacidad de cambios pendientes. Edad/teléfono/correo son simuladores o entregas locales de fixture; no proveedor real. Tareas eager cuando la fixture lo establece, no prueba de cola real:359conserva ese ámbito propio.

Presupuesto diagnóstico:12PASS/0ERROR/FAIL/SKIP, cero errores del observador/excepciones inesperadas, métricas finitas/no negativas y conteos íntegros, oráculos originales completos. Los400/403/404/409/429esperados son resultados funcionales y no tasa de error de carga. Medir pared de Client.request, consultas y tiempo SQL de esa conexión. Guardar sólo campos seguros del observador: no SQL/params/cuerpos/UUID/credenciales en evidencia versionada oTelegram.

Una observación por transición/estado, sin p95/p99ni percentil agregado entre rutas. Sin candidato no se calcula mejora causal; los tiempos anteriores disponibles se muestran separados con sus límites y donde no existían se declara no medido. Antes de una corrección futura, fijar referencia equivalente, coste objetivo y contraste conforme354; no cambiar código sólo porque una transición tenga más consultas que otra.

## Ejecución y auditoría

Runner oficial serial: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --isolate-test-broker --observe-http-operations --timeout 900`, con un --testpor cada selector anterior. PostgreSQL17/Redis7.4propios, dependencias bloqueadas y herramientas nativas fijadas, sin tráfico paralelo ni cuotas dedicadas. Congelar SHA de producto/dependencias/migraciones/instrumentos/grafo/imágenes y selección antes de lanzar. Timeout900es protección por comando, no SLO. Sin repeticiones adaptativas ni reducción de casos.

Auditar selección/JUnit12casos, propiedades seguras/conteos/estados y modalidades, fuentes intactas, temporal retirado, inventario independiente sin recursos propios yTelegramterminal sent. Conservar FAIL original si aparece y corregir causa probada sin borrar evidencia. Separar duración QA de latencia. Tras auditar, actualizar372con las rutas realmente observadas; no dar por cubiertas anticipadamente las21ni todas sus variantes. Cuatro colas de revisión continúan con referencia de crecimiento pendiente y los cinco noHTTPconservan responsabilidades. Esta pasada no cierraN06ni el contrato.
