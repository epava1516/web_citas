# Gate del pipeline de filas fuente

PostgreSQL17 real:79PASS,0errores/fallos/skips,473.610s,6archivos.1154 hashes y limpieza PG/Redis independientes. Pruebas: head lock desde autocommit, mismos resultados/ticket, corrupción primera/última, primer SQLSTATE y rollback/conexión reutilizable, snapshots frescos con cambio committed entre sentencias, recorder y fallbacks anidados/incompatibles, regresiones de cadena/runtime/sellos.

| Microbenchmark 7 filas | Serial | Pipeline | Reducción | Muestras |
|---|---:|---:|---:|---:|
| Mediana (ms) | 7.204861 | 5.977017 | 17.04% | 20 por variante |
| Peak Python trazado (bytes) | 5294 | 23877 | No ahorro | 1 por variante |

Dos parejas warmup descartadas;20parejas alternadas, siete filas/703bytes de payload. No representa request grande ni cuotas. Tracemalloc excluye libpq; máximo RSS179128KiB es acumulado de proceso, no peak de operación. Capacidad completa doscasos/N3 y memoria fullsize pendientes.

Cambian únicamente siete SELECT independientes de filas fuente, con parámetros/resultados completos y snapshots por sentencia. Todo head/ticket/trust/eventos/enlaces anterior permanece serial. Recorder activo, pipeline anidado o incompatible conservan serial. No nueva función de confianza ni caché de autoridad.
