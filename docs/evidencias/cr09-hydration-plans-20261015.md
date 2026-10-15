# Desagregación SQL de hidratación con datos sintéticos

Ejecución `20261015-233344-af8d3970`: **1 PASS /87,69s**, PostgreSQL propio17.11, kernel native-sealed, Python3.12.15 y cuotas anteriores. Fuente de aplicación SHA3a88118; test explícito añadido sin commit durante ejecución, incluido en source-hashes.json y posteriormente conservado en commit aislado `cbdaba3`. [Recibo](cr09-hydration-plans-terminal-20261015.json). No cambio de producto ni ensayo HTTP nuevo.

El diagnóstico recorre state_page real con10k sintéticos, limpio/dirty1 y listado/búsqueda, dos repeticiones. Captura272ejecuciones SELECT y39formas; EXPLAIN ANALYZE BUFFERS JSON una vez por forma, antes de otros recorridos. La repetición de EXPLAIN calienta caches: no comparación fría/causal. Replays con jit=off/join_collapse_limit=1 explícitos, no equivalen a todos los planes originales ni reproducen preparación del driver por conexión. SQL/planes completos sólo en artefacto sintético propio.

Se relaciona exactamente huella31a87e7d…4134 con hidratación principal: selección de24 Listing con Revision/Person/PhoneClaim y anotaciones Exists de autoridad. El caller263 también incluye prefetch; por eso su suma no representa una consulta única.

| Consulta principal, contextos diferentes | Tiempo |
| --- | ---: |
| Captura concurrente, entradaWSGI0–5s,55ejecuciones | media53,891ms |
| Captura concurrente, entradaWSGI15–60s,600ejecuciones | media11,782ms |
| EXPLAIN aislado, planificación | 5,330ms |
| EXPLAIN aislado, ejecución | 5,550ms |

Ventanas agrupadas por entradaWSGI en esta tabla, no por emisión como el informe anterior. No sumar p95 ni atribuir diferencia a un índice o a CPU. El plan principal devuelve24filas y883shared hit blocks/0read blocks. Dos variantes dirty con DISTINCT: planificación10,985/8,946ms y ejecución2,252/2,866ms, una fila. Selección/count general de candidatos aún recorre población: ejecución30,268/22,801ms para listado y24,379ms búsqueda en este replay; no basta por sí sola para explicar un HTTP de más de1s.

La evidencia no avala otro cambio especulativo. Falta atribuir la amplificación inicial bajo concurrencia: esperas reales del backend/ejecución frente a scheduling/transporte. Siguiente instrumento debe correlacionar actividad y wait_event **del PostgreSQL propio** durante la misma ventana, sin perfiles de aceptación ni tocar servicios normales; comprobar antes capacidades/permisos. EXPLAIN distingue planificación/ejecución y tiene sobrecoste propio según [PostgreSQL17](https://www.postgresql.org/docs/17/using-explain.html).

Fuente congelada verificada antes de commit del test; controlador/hijo/temporal/contenedores propios ausentes; unidadMainPID0 yControlGroupvacío. check_docs pasa. No medición de p95 nueva, sin aceptaciónCR09/N3.
