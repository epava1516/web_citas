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

Doce controles unitarios preparados: identidad propia válida y rechazo de run,
nombre, etiqueta, puerto, host, DB, detenido, ausencia de ámbito/override,
credenciales y query. Docker/Redis son observados con dobles en esos controles;
no se declaran verificación real de servicios. Ruff y diff --check PASS.
Todavía no se ejecutó pytest ni gate HTTP de esta correctiva.

Condición de salida: controles y gate funcional con servicios propios reales,
fuentes congeladas y limpieza; luego gate contractual pertinente, secuencial,
sin perfiles ni cambios especulativos. No rebaja criterios ni acepta N3.
