# Corrección preparada de broker del gate HTTP

Base 79db964; rama codex/cr09-load-owned-broker-20261014 en worktree aislado.
Propiedad exclusiva: scripts/run_local_ci.py,
tests/test_worker_capacity_comparison.py, tests/test_benchmark_owned_redis.py,
y este recibo. No integración mientras el bloque 3 siga activo.

El runner añade dos switches explícitos, limitados a focused/1 worker; normal
refresh exige selección del contrato HTTP. Registra ambos en resultado, activa
normal_worker_beat y transmite URL del Redis efímero, nombre y run al hijo.
La preparación opcional de GC afecta al cliente, conservando criterios.
No se heredan switches desde el entorno del servidor.

El helper valida run, nombre exacto, esquema/host/DB0 sin credenciales/query,
Docker Running/etiqueta y puerto publicado exactos antes de construir cliente.
Se usa ese mismo helper antes de worker/Beat y en la limpieza de su broker.
No se conecta al Redis normal del puerto fijo desde la nueva vía CI.

Doce controles de identidad preparados: identidad propia válida y rechazo de run,
nombre, etiqueta, puerto, host, DB, detenido, ausencia de ámbito/override,
credenciales y query. Docker/Redis son observados con dobles en esos controles;
no se declaran verificación real de servicios. Ruff y diff --check PASS.
Todavía no se ejecutó pytest ni gate HTTP de esta correctiva.

Condición de salida: controles y gate funcional con servicios propios reales,
fuentes congeladas y limpieza; luego gate contractual pertinente, secuencial,
sin perfiles ni cambios especulativos. No rebaja criterios ni acepta N3.


Revisión nativa sólo lectura de 0045214: no encontró defecto bloqueante.
Root comprobó orden de validación antes de Popen worker/Beat y reutilización
del helper en limpieza. Revisión estática no demuestra ejecución real.
Se añaden siete negativos CLI: perfil incorrecto, archivo incompatible,
workers paralelos, selección mixta, ausencia de selección y GC fuera de
focused. Comprueban SystemExit2 antes de cualquier comando de servicio.
Total preparado 19 controles; pytest sigue pendiente. Propagación y limpieza
reales requieren gate functional con los switches nuevos, no otro mock.

Salvaguarda posterior: si LOCAL_CI_POSTGRES_CONTAINER identifica una ejecución
CI, owned_redis exige override y run antes de cualquier fallback. Nuevo negativo
ci_missing_scope; total actual 20 controles preparados. Fuera del CI propio se
conserva el contexto histórico del experimento; esta entrega sólo ejecutará la
vía CI verificada. Ruff/diff-check PASS, pruebas reales pendientes.
