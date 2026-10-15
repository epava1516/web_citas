# Estadísticas después de carga masiva: atasco reproducido y corregido

La reproducción de la secuencia original se hizo en el worktree propio `web_modelos_cr09_native_prep_repro_20261015`, basecdc428f más el prototipo inactivo y sus ocho controles de ámbito. No se integró ese prototipo en la rama principal. Se conservan [parche del worktree](cr09-conflictos-native-secuencia-worktree-20261015.patch) e [instrumento](cr09-conflictos-native-secuencia-instrumento-20261015.py) para reconstrucción. El parche incluye la correctiva del builder; retirarla reproduce la versión roja.

[Rojo203146](cr09-conflictos-native-secuencia-reproduccion-20261015.json):8PASS/1FAIL173.25s. Estadísticas nativas después de los ocho controles: Revision yPhoto estimadas0 con una página, Match yRightsExecution desconocidas(-1). Tras clonar10k publicados, la consulta nativa elige bucles anidados dePhoto yPhoto antes de consultarMatch, estimando1fila. Coste estimado90.79, **sin JIT**. EXPLAIN sin ANALYZE no mide cuántas iteraciones ejecutó; no atribuirle100millones de filas efectivas. La ejecución se cancela a5.0025s, SQLSTATE57014. La observación inicial de más129s queda preservada por separado.

Correctiva: el generador de datos sintéticos ejecuta ANALYZE de cinco tablas propias después del bulk y antes de sus mismas tres validaciones nativas. No retira reglas, filtros, índices o constraints ni fuerza un plan. El generador ya impide producción y exige nombre de DB de pruebas propio. La carga aún no ha terminado su transacción; actualizar estadísticas explícitamente evita depender de cuándo autovacuum vea las nuevas filas.

[Verde203639](cr09-conflictos-native-secuencia-correctiva-20261015.json):**9PASS141.06s**, misma secuencia, sólo cambia `scripts/synthetic_load_dataset.py` según hashes comparados. Fuentes y limpieza verificadas independientemente por ambos runs; unidades terminales, procesos/temporales/PGRedis propios retirados. Mismo fingerprint SQL, jit=on, join_collapse_limit8, plan_cache_modeauto; ninguna política de requests modificada.

| Consulta nativa tras el bulk | Antes | Correctiva |
|---|---:|---:|
| Primera validación |Timeout5.0025s|8.047ms|
| Siguiente validación |No alcanzada|7.712ms|
| Última validación |No alcanzada|20.174ms|
| Resultado de secuencia |8PASS/1FAIL|9PASS|

El coste estimado del nuevo plan3286.76 no son milisegundos y es mayor que el estimado del plan malo. La mejora observable es que el plan con estimaciones actualizadas completa las mismas validaciones. Las dos condiciones anteriores de estadísticas pequeñas no reproducían el fallo: no se borran sus límites ni se las presenta como la reproducción.

La [documentación oficial de PostgreSQL17](https://www.postgresql.org/docs/17/populate.html#POPULATE-ANALYZE) recomienda ANALYZE tras alterar mucho la distribución, incluida una carga masiva, para evitar decisiones con estadísticas ausentes/antiguas. Sólo se adopta ese mantenimiento; no otras recomendaciones de recursos, WAL o constraints.

Integración en main: únicamente el cambio del builder verificado; se añadió metadata de retorno `planner_statistics` para que el manifiesto del siguiente ensayo identifique esta preparación. No se integra la opción genérica experimental ni cambia apps/config/templates/static. Se mantiene el worktree y los fallos originales.

**Esto corrige preparación, no acredita una mejora del código de las requests.** El siguiente corto limpio será una referencia con estadísticas preparadas explícitamente, con el mismo SLO, límites, mezcla, subida y peticiones iniciales. Conservar comparación y explicar el cambio de preparación; no atribuir una diferencia al runtime ni al portátil. Último p95limpio0.961136843sFAIL, sin ensayo15min/N3 ni aceptaciónCR09.
