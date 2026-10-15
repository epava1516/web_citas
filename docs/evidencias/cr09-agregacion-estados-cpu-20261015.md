# Agregación global de estados: hipótesis descartada

Run `20261015-150653-5082a7f3`, base `fe5b4c5` más diagnóstico:1PASS85.64s. Fuente congelada y limpieza independiente verificadas. PostgreSQL propio,10k sintéticos, límites previos, sin tracker/carga concurrentes. Cuatro casos actuales/ineligible/stale/missing, vacío separado;8calentamientos+3bloques alternos×12por variante. Resultado booleano igual a la comprobación original por join en cada snapshotRR de sólo lectura.

| CPU por comprobación(ms) | Original | Una pasada |
|---|---:|---:|
| current | 2.778 | 2.778 |
| ineligible | 2.500 | 2.500 |
| stale | 1.667 | 2.222 |
| missing | 3.056 | 3.333 |

Los planes confirman una sola pasada por estados en la agregación nueva frente a dos en la original, pero no ahorro de CPU en el caso habitual y coste mayor en excepcionales. En stale, la consulta original cortocircuita y no ejecuta los conteos; la agregación debe recorrer el conjunto. CPU100Hz y EXPLAIN son instrumentos distintos: tiempos de plan no equivalen a CPU.

Decisión: DESCARTADA antes de producto. No se altera all_state_current, no se lanza carga HTTP ni repetición, no se reclama mejora p95. Último limpio5.004966sFAIL permanece. No se amplía garantía a transacciones heredadas/FK aplazadas. [PostgreSQL17](https://www.postgresql.org/docs/17/functions-aggregate.html) documenta bool_and/COALESCE y coste proporcional del conteo exacto; menos recorridos por sí solo no prueba menor demanda.

La investigación siguiente debe centrarse en el trabajo dominante de población/búsqueda sin reactivar propuestas retiradas ni añadir modelos/cache/proyección antes de justificar su coste y exactitud.
