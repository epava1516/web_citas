# N01D — base por operación HTTP de recorridos sintéticos

Estado: prerregistro, sin resultados de aplicación. Contrato340/roadmap341; N01 sigue abierto, N00aceptado1/13. No cambia comportamiento de producto. El lote amplía la observación fuera de discovery; no cierra N04/N06/N07/N08 por cobertura parcial.

## Propósito e instrumentos

Medir cada llamada síncrona Django Client.request dentro de la fase call de casos originales, sin sustituir sus oráculos. Instrumento `scripts/http_operation_metrics.py`, activación optativa `scripts/run_local_ci.py --observe-http-operations`, serial focused sin observadores de carga. Sus ocho pruebas de contrato pasaron en run20261025-093832-4c48e1fc; no constituyen evidencia de latencia de aplicación. Se preservan reportes originales y auditoría local.

Captura por petición: método, nombre estático de ruta, estado HTTP, tiempo instrumentado de petición, número de consultas y tiempo de ejecución SQL; sólo clase de excepción/fallo del observador. No captura URL concreta, cuerpos, parámetros, SQL, tokens, identificadores ni mensajes de excepción. Las peticiones de fixtures solicitados dinámicamente durante call también entran: separar su interpretación; no atribuir todas las muestras a la acción principal. El setup ordinario queda fuera. El tiempo total de pytest no es latencia.

## Selección y datos

Selección exacta, preservando cuerpos/oráculos de los tests. Once casos esperados, incluyendo los dos idiomas del último selector:

- `tests/test_lifecycle.py::test_availability_pause_resume_withdraw_and_old_retry`
- `tests/test_lifecycle.py::test_renewal_same_id_confirmation_expiry_and_delayed_task`
- `tests/test_accounts.py::test_signup_requires_legal_and_stale_version_rejected`
- `tests/test_accounts.py::test_signup_verified_login_replay_and_no_privilege_escalation`
- `tests/test_accounts.py::test_csrf_throttle_and_token_headers`
- `tests/test_revised_listings.py::test_revised_version_keeps_approved_snapshot_and_reuses_bytes`
- `tests/test_revised_listings.py::test_rejection_preserves_public_version_and_rate_ids_are_isolated`
- `tests/test_favorites.py::test_favorites_private_idempotent_permissions_and_hidden_content`
- `tests/test_sitemaps.py::test_sitemap_languages_privacy_page_boundaries_and_withdrawal`
- `tests/test_promotion_order_http.py::test_private_order_form_simulation_reload_and_ownership`

Datos: fixtures sintéticos existentes, correos example.invalid, bootstrap legal y correo en memoria para cuentas; directorio y publicaciones derivadas de fixtures existentes para los demás. Sin ampliación a100perfiles ni cardinalidad uniforme inventada. Los resultados registrarán cardinalidad que pueda probarse con fuentes; no equiparar poblaciones entre casos. Roles: anónimo, visitante, titular, moderador y ajeno según cada caso. Idiomas ES/EN según selectores; pedido simulado ambos. No cobros/proveedores reales.

Oráculos: consentimiento/versiones legales; activación sólo POST y token de un uso; no escalado de privilegios; CSRF/throttle; ciclo de disponibilidad/renovación e idempotencia; instantánea aprobada durante revisión/rechazo; medios no públicos; favoritos privados, pertenencia y retirada; sitemap idiomas/paginación/retirada; pedido/entitlement simulado único y acceso propio. Las denegaciones esperadas400/403/404/405 u otras comprobadas por el caso son resultados funcionales, no tasa de errores de carga.

## Entorno, presupuesto y aceptación

Runner oficial, PostgreSQL17 y Redis7.4 locales propios, librdbv2.4.0 y dependencias bloqueadas; un worker y una pasada diagnóstica de la selección. Timeout900s por comando es protección de ejecución, no presupuesto de endpoint. Sin límite CPU/RAM dedicado, sin aislamiento de host ni concurrencia de tráfico. Cachés y calentamiento dependen del orden de casos/fixtures: registrar, no afirmar frío controlado. Procesamiento directo y servicios fuera de Client.request no quedan medidos; tampoco navegador, TCP, worker/Beat, colas ni capacidad.

Antes de ejecutar: refresco focal del grafo AST/semántico con alcance explícito, congelación de hashes completos de fuentes/instrumentos/dependencias/migraciones, imágenes/recursos y comando. Durante ejecución no editar fuentes. Auditoría posterior:11casos esperados frente a colección real, JUnit/journal, muestras por caso/ruta/método/estado, campos permitidos y escalares finitos, excepciones/fallos del observador, recursos retirados, identidad de fuentes y aviso Telegram confirmado.

No existe presupuesto universal validado para estos endpoints. Este lote establece base diagnóstica y cobertura funcional; no declara PASS de rendimiento, p95/p99 con muestras escasas, ni cumplimiento del protocolo de mezcla pública<800ms. Antes de cada candidato se fijará presupuesto por escenario con evidencia y equivalencia; mientras quede pendiente, N01 no se declara cerrado. No se importa el umbral MOD09a estos recorridos.

Reportar muestras individuales y rangos por caso/ruta, sin mezclar operaciones heterogéneas. Conservar fallos y rutas no resueltas; ninguna muestra inválida cuenta como mejora. Una futura comparación deberá conservar selección, fuentes de datos, orden y recursos, explicando variabilidad. Este prerregistro no optimiza QA ni reduce cobertura.

Al cerrar el bloque se publicará tabla antes/después con evidencia comparable o «sin base comparable». En este lote sin candidato de producto no hay ahorro causal que atribuir. El contrato sigue en alfa y las familias restantes conservan su obligación.
