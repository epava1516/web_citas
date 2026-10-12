# CR09: diagnóstico parcial de regresión secuencial

Ejecución `20261012-200723-11216b4a`, SHA
`5f649908f76b0b7ae07e45295887fe0e5e675a42`, iniciada a las 20:07 UTC.
Estado de este corte: activa; no resultado terminal, aceptación CR09 ni N3.
El registro original es `artifacts/local-ci/20261012-200723-11216b4a/pytest-reports.jsonl`.
Cada fallo se escribe y sincroniza a disco antes del JUnit terminal.

Un trabajador, afinidad CPU 0–3, host 3584 MiB, swap 0, 512 procesos.
PostgreSQL propio: CPU 1/afinidad 4, 1536 MiB, WAL máximo 256 MiB;
Redis propio: CPU 0,2/afinidad 5, 128 MiB. Mismos cuatro casos/familias
excluidos por el perfil regression; no cambiar su alcance para obtener PASS.
Con un RustFS de 512 MiB y Caddy de 128 MiB, la suma de límites de estas
instancias es 5888 MiB, por debajo de 6 GiB; no representa consumo medido.

## Fallos observados hasta 21:25 UTC

| Caso | Fallo conservado | Condición para la correctiva |
| --- | --- | --- |
| `test_capacity_chain_inline_http::test_inline_committed_http_clones` | `SnapshotBusy` al retirar clon: PostgreSQL muestra conexión viva | Diagnosticar cierre/sincronización de conexiones propias; mantener rechazo de DROP ante conexión viva y prohibición de terminarlas |
| `test_capacity_paths_http::test_paths_partial_benefit_committed_http_clones` | Mismo `release` compartido y `SnapshotBusy` | Verificar ambos consumidores del helper; no presentar un arreglo aislado como regresión completa |
| `test_capacity_revision_http::test_revision_projection_partial_benefit_committed_http_clones` | Mismo `release` y `SnapshotBusy` | Incluir este consumidor en la verificación de limpieza |
| `test_capacity_scalar_consumers_http::test_scalar_consumers_committed_http_clones` | Mismo `release` y `SnapshotBusy` en variante control | Verificar también la variante control; no atribuirlo exclusivamente a la candidata inline |
| `test_capacity_stability_http::test_stability_twenty_committed_http_clones` | Mismo `release` y `SnapshotBusy` | Incluir estabilidad entre los consumidores del helper |
| `test_capacity_object_preflight::test_owned_object_proxy_and_purge_worker_gate` | Ajuste `CAPACITY_PREFLIGHT_ONLY` ausente en CI general | Definir explícitamente entorno exigido; conservar las aserciones de topología real en preflight; una omisión fuera de contexto no acredita ese gate |
| `test_contract_http_load::test_contract_arrival_rate_http_with_limited_uploads[functional]` | Opción `--gate-timings-output` no registrada | Cargar el plugin existente `scripts.catalogue_gate_timings` y proporcionar salida propia; volver a ejecutar el caso completo |
| `test_diagnostic_baseline_pg::test_actual_original_approval_roundtrip_and_config_rejection` | COPY de `listings_publicationdirty` encuentra clave duplicada | Verificar restauración exacta frente a triggers de publicación que insertan filas derivadas; conservar FK, integridad y estado final de triggers |

Los cinco diagnósticos HTTP alcanzan la inspección independiente de commits
antes de fallar en `release`. El WSGI cierra su conexión antes de publicar el
recibo y el inspector usa un contexto psycopg que cierra al salir. Esto delimita
la revisión de sincronización, pero no demuestra aún una causa única ni una
correctiva verificada. No se modifica producto por estas trazas.

El restaurador desactiva únicamente `rights_evidence_record` durante COPY.
La migración `0015_publication_state` instala triggers que insertan en
`listings_publicationdirty`; la interacción con la copia de la tabla derivada
es una causa candidata de su duplicado, todavía pendiente de reproducción
dirigida. No aplicar desactivación global de triggers ni retirar restricciones
para conseguir una restauración aparentemente válida.

Los casos omitidos que requieren el controlador de capacidad deben seguir
registrados como omisiones. La evidencia del ciclo MOD08 anterior conserva sus
propios SHA y resultados; no convertirla en una batería común sobre este SHA.

Próximo paso: conservar nuevos fallos, resultado terminal, motivos de omisión,
eventos de memoria, huellas de fuentes y limpieza. Después reproducir y
verificar las correctivas necesarias antes de valorar cierre integral.

## Caso largo completado, corte 22:36 UTC

El journal registra setup/call/teardown PASS para
`tests/test_portability_large_closed_flow.py::test_large_history_native_approval_closure_and_binary_delivery`.
Recorre 1500 revisiones sintéticas y el flujo nativo completo. El cuerpo del
test dura 1602,514297 s; setup 0,004565 s y teardown 0,518811 s. Es duración
de integración, no p95 HTTP, capacidad, nueva mejora temporal ni N3.

| Evidencia | Corte anterior | Corte actual |
| --- | --- | --- |
| Resultado de este caso sobre SHA común | En ejecución | PASS en sus tres fases |
| Duración call sobre este SHA | Sin resultado | 1602,514297 s |
| Resultado de la batería completa | Pendiente | Sigue pendiente |

Los ocho fallos previos permanecen conservados. No sumar este PASS aislado
con otras versiones para declarar aceptación integral.

## Deadlock funcional observado, corte 22:45 UTC

`tests/test_privacy_publication_holds.py::test_approval_race_cannot_republish_held_profile`
falla con `DeadlockDetected`/`OperationalError`. PostgreSQL registra a las
22:44:48 UTC una espera circular entre la inserción de
`safety_privacypublicationhold` (su trigger intenta marcar `listings_publicationdirty`)
y otra transacción en COMMIT. La traza original del servidor propio se conserva
en `artifacts/vps-preparation/cr09-regression-sequential/privacy-deadlock-postgres.log`,
con permisos 0600; no se publica su contenido completo.

Este es un fallo funcional de concurrencia que debe reproducirse y corregirse;
no reducirlo a un problema de instrumentación. La revisión incluye el refresco
de publicación: reclama filas dirty con FOR UPDATE y luego escribe estado
derivado, mientras operaciones del dominio bloquean Person/Listing antes de
marcar dirty. La causa exacta del COMMIT concurrente y sus locks debe confirmarse
con reproducción dirigida. No asumir exposición indebida a partir de un deadlock
ni aceptar supresión del error/reintentos ciegos como corrección de privacidad.

Las cuatro candidatas de instrumentos se preparan separadamente en
`codex/cr09-instrument-correctives-20261012`, commit `b29ab90`; sin pruebas
PostgreSQL ni integración. La regresión mantiene SHA `5f64990` intacto.

## Décimo fallo: navegación móvil de promociones

El diario registra fallo de
`test_mobile_dashboard_order_simulation_reload_and_layout[es]` en
`tests/test_promotion_order_mobile_agency.py:69`: `Page.reload: Protocol error
(Page.reload): Not attached to an active page`, después de pulsar Simular
resultado. El test solicita reload sin esperar la respuesta visible posterior
al envío. Es candidato a una carrera de navegación; la causa no está confirmada
y no demuestra por sí sola un fallo de pago o de persistencia. Conservar el fallo
y reproducir el selector con comprobación de la respuesta antes y después del
reload, sin capturar ni ocultar errores del navegador.

## Fallos undécimo y duodécimo: inventario de scripts JSON-LD

Los dos idiomas de
`test_browser_jsonld_remains_inert_and_readable_under_csp` fallan únicamente en
la aserción final de cero scripts distintos de JSON-LD: el DOM contiene uno.
Las comprobaciones anteriores de alias malicioso como dato, ausencia de
`SEO_PWNED` y ausencia de violaciones CSP pasaron en esos casos antes del fallo.
La plantilla base incluye el helper local diferido `form-errors.js`.

En la rama correctiva, `354ea5b` exige exactamente ese recurso estático, defer y
ausencia de contenido inline, manteniendo los controles de seguridad existentes.
Es una candidata pendiente de reproducción y verificación del DOM real; no se
integra por inspección de plantilla ni se considera PASS la regresión original.
El ajuste móvil español se conserva aparte en `c81679a`.
