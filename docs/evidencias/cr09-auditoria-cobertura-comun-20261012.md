# CR09 — auditoría de cobertura de la versión común

Fecha: 2026-10-12. Base `de12d9bd77501943722221f84e69ee927afa58bb`.
Inspección de Codex y revisión nativa independiente `cr09_closure_audit`, sólo
lectura. Ningún test ejecutado por el revisor, ninguna modificación funcional;
no es PASS, N3 ni aceptación CR09. Cero invocaciones nuevas Claude V1.
La regresión propia `20261012-162721-b80af490` sigue siendo la fuente del
resultado conjunto pendiente.

| Requisito local | Implementación | Pruebas existentes incluidas en regresión | Evidencia todavía necesaria |
| --- | --- | --- | --- |
| Sesiones DB propias, incluidas caducadas, sin capacidades | `rights_access_delivery.session_records` | `test_rights_access_recipient_payload`, `test_rights_access_coverage_store` | Resultado común; sesiones dañadas o no atribuibles conservan límites. No ampliar a backends ausentes. |
| Caché y diferencias de recursos retenidos | DummyCache y `retained_resource_records` | `test_rights_access_recipient_payload`, `test_retained_origin_inventory` | Delimitar orígenes necesarios del escenario y decisiones independientes; DummyCache no prueba inexistencia de backups históricos. |
| Colas actuales e históricos Redis | `broker_records`, `history_records`, `retained_redis_origins.read_bundle` | `test_redis_history_scope`, `test_scoped_redis_history_origins`, `test_retained_redis_origins` | Resultado común y corte/asociación de fuentes necesarias; no convertir RDB/AOF capturados en momentos distintos en un corte íntegro. |
| Logs históricos | `log_records`, `checked_scoped_captures` | `test_scoped_log_history_origins`, `test_rights_access_coverage_store` | Procedencia/asociación/contenido y divulgación motivados para cada fuente necesaria. Mantener bloqueos ante desconocidos. |
| Comunicaciones internas por derecho | `rights_communications.snapshot`, `communication_notices.deliver/inspect_notice/acknowledge` | `test_rights_communications`, `test_rights_communications_localization` | Resultado común y delimitación de cada laguna del escenario; aviso emitido no demuestra recepción externa. |
| Gestor anterior como candidato histórico | `manager_evidence`, `authorized_targets` | `test_historical_communication_candidates` | Autoridad actual o decisión motivada por candidato; el rol pasado no autoriza comunicar datos. |

## Límite histórico conservado

Las [23 fuentes conocidas](../88-matriz-cierre-derechos.md) conservan la falta de
asociación fiable registrada: las pruebas positivas de eventos firmados/MIME no
contabilizan esos originales. No inferir asociación por UUID, texto o conteos;
no borrar `partial` o `pending`, ni fabricar exclusiones genéricas. La selección
histórica y su bloqueo de cierre son controles deliberados ya implementados.
Una fuente necesaria sin asociación acreditada mantiene pendiente ese alcance.

Las decisiones de producción —censo real, políticas jurídicas, custodios,
proveedores y recepción externa— permanecen separadas. Un fixture sintético
permite verificar mecanismos, nunca certificar esos hechos externos. La próxima
acción es revisar el resultado terminal y sus exclusiones antes de determinar
la batería común restante y cualquier corrección concreta. MOD-09 sólo dispensa
provisionalmente las latencias del escenario extremo.
