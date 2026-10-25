# N01D — resultado de observación HTTP por operación

25 de octubre de2026. [Prerregistro350](350-n01-d-prerregistro-operaciones-http-20261025.md), candidata instrumental745b0a6, run20261025-094533-b3968c81: **11PASS,109peticiones**, sin fallos/errores/skips. No hay candidato de producto ni aceptación de rendimiento. N00aceptado1/13;N01 sigue abierto,alfa.

[Auditoría estructurada](evidencias/n01-d-operaciones-auditoria-20261025.json), [reportes originales y reproducción](evidencias/n01-d-operaciones-evidencia-20261025.tar.gz), [congelación](evidencias/n01-d-prerregistro-congelacion-20261025.json), [verificación de grafo](evidencias/n01-d-prerregistro-grafo-verificacion-20261025.json). Las ocho pruebas del instrumento precedieron al lote; sus dobles SQL no se declaran consultas PostgreSQL reales. El lote sí ejecutó Django con PostgreSQL17 propio y Redis7.4; fuentes congeladas sin cambios y contenedores retirados. Avisos terminales del runner y auditoría con entrega Telegram sent.

## Muestras y alcance

Se recogieron109operaciones con nombre de ruta resuelto, tiempos finitos y campos permitidos, sin clases de excepción ni fallos del observador. HTTP200:40,302:36,400:6,403:6,404:14,405:2,409:4,429:1. Las denegaciones estaban comprobadas por los oráculos originales: no son fallos ni tasa de error de carga. La auditoría conserva cada muestra y su agrupación por caso/método/ruta/estado.

| Caso | Peticiones observadas |
| --- | ---: |
| test_availability_pause_resume_withdraw_and_old_retry | 12 |
| test_renewal_same_id_confirmation_expiry_and_delayed_task | 6 |
| test_signup_requires_legal_and_stale_version_rejected | 2 |
| test_signup_verified_login_replay_and_no_privilege_escalation | 10 |
| test_csrf_throttle_and_token_headers | 10 |
| test_revised_version_keeps_approved_snapshot_and_reuses_bytes | 11 |
| test_rejection_preserves_public_version_and_rate_ids_are_isolated | 8 |
| test_favorites_private_idempotent_permissions_and_hidden_content | 11 |
| test_sitemap_languages_privacy_page_boundaries_and_withdrawal | 17 |
| test_private_order_form_simulation_reload_and_ownership[es] | 11 |
| test_private_order_form_simulation_reload_and_ownership[en] | 11 |

Una pasada serial y datos de fixtures originales, no una cohorte uniforme de100perfiles. Tiempo del comando pytest **102.253s**, incluido QA/preparación; no es latencia de aplicación. El instrumento mide Client.request durante call, con consultas SQL síncronas de esa conexión. Incluye peticiones que pudiera realizar un fixture cargado dinámicamente durante call; no se atribuyen automáticamente todas las observaciones al objetivo principal. Quedan fuera el setup ordinario, ORM directo, aserciones, navegador/TCP, procesos asíncronos, colas y capacidad.

## Señales para investigar

En revisión publicada, POST listing_start302 produjo116consultas/349,918ms. En rechazo/corrección hubo dos operaciones de esa ruta con116/124consultas y390,576/566,035ms. Son muestras de estados diferentes; no repetición equivalente ni regresión demostrada. Justifican estudiar hidratación, clonación y autoridad en N06 antes de proponer cambios; no retirar controles ni denominarlo N+1 sin examinar SQL/fuentes.

En lifecycle, los POST302 fueron heterogéneos:45–69consultas para mutaciones y13para reintentos exactos observados. La diferencia de trabajo forma parte del escenario; no es ganancia causal. Los detalles completos evitan mezclar petición inicial, transición y repetición. Sitemap, favoritos y pedidos conservan asimismo sus estados negativos y de retirada.

No se calcula p95/p99 ni cumplimiento de mezcla pública<800ms con este lote. Sin cuotas dedicadas, carga concurrente o control de frío/caliente, estos tiempos no son una garantía de producción. Los presupuestos por escenario y otras familias siguen pendientes; tampoco se afirma verificación de worker/Beat, entrega externa o compra real.

## Antes y después de este lote diagnóstico

Tabla de avance del lote; no cierra el bloqueN01 ni sustituye su tabla final.

| Aspecto | Antes | Después | Diferencia y límite |
| --- | --- | --- | --- |
| Mediciones por operación de esta selección | Sin base registrada en este contrato |109muestras,11casos | Nueva base instrumental; sin comparación de velocidad |
| Oráculos funcionales actuales de la selección | Fuentes revisadas, lote actual pendiente |11PASS; denegaciones y paridad comprobadas | Cobertura parcial, no todas las acciones de las familias |
| Código de aplicación | Base aceptada | Misma base; sólo runner e instrumento nuevos | Sin optimización de producto en este lote |
| Presupuesto/ganancia de rendimiento | Pendiente por escenario | Pendiente por escenario | Sin base comparable antes/después de candidato; sin porcentaje |
| Contrato | N00aceptado1/13,N01abierto | N00aceptado1/13,N01abierto | No aceptación por mera instrumentación |

Siguiente: integrar semántica de este resultado y seguimiento antes del nuevo hito; completar las fichas/bases pertinentes de las propuestas restantes, separar modalidades de navegador/servicios/jobs y fijar los presupuestos antes de comparar candidatos. Mantener objetivos MOD09 y criterios originales sin importarlos a otros endpoints.
