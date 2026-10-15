# Consulta nativa de conflictos: estadísticas acotadas

La observación original201228 mostró una consulta nativa atascada más de129s durante populate, antes del candidato. La causa todavía no está demostrada. Se añadieron instrumentos aislados con EXPLAIN sin ANALYZE, límite5s por consulta, settings y planes sin SQL ni parámetros. Producto y benchmark sin cambios.

Se probaron dos condiciones finitas sobre10k sintéticos: estadísticas de fixture pequeño analizadas para cuatro tablas; y el mismo estado dejando Match vacío sin analizar. La segunda conserva reltuples=-1 paraMatch, la primera0. No son afirmaciones sobre las estadísticas originales, que no se capturaron.

| Diagnóstico | Resultado | Ejecución de4consultas | JIT en planes |
|---|---|---:|---|
|202526-477b3817, cuatro tablas analizadas|1PASS63.73s|4.18–10.04ms|No|
|202757-d29b7941, Match sin estadísticas|1PASS65.72s|4.92–14.29ms|No|

[Recibo analizadas](cr09-conflictos-native-stats-analizadas-terminal-20261015.json), [recibo Match desconocidas](cr09-conflictos-native-stats-desconocidas-terminal-20261015.json). Fuentes y limpieza independientes verificadas por ejecución. Cuatro SELECTs de2676bytes/9parámetros, mismo fingerprint por condición. Coste estimado después del bulk3398.99 y3409.17 respectivamente; valores de coste no son milisegundos. EXPLAIN añade planificación, de modo que estos tiempos secuenciales no sustituyen p95/capacidad.

Resultado: ambas condiciones completan y **no reproducen ni resuelven** el atasco. No aplicar ANALYZE al benchmark como supuesto arreglo, no forzar jit ni cambiar consulta por una causa no demostrada. Siguiente paso: reconstruir en worktree aislado la secuencia original de8controles y observar la preparación con estadísticas nativas intactas, límite5s y mismo SQL. No barrer parámetros adicionales. El fallo conjunto original sigue pendiente para N3; el aislamiento no lo cierra.

Tras verificar la segunda ejecución se amplió la captura de errores del instrumento para registrar también excepciones del cursor psycopg raw durante EXPLAIN; no cambia el producto ni resultados ya medidos. Último p95 limpio0.961136843s FAIL; CR09→CR10→GS01→BF/BB→C activo.
