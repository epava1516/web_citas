# Diagnóstico finito de planes y expresiones de cadena

2026-10-11. Autorización del usuario: «Procede pues», tras segunda opinión de NotebookLM y correcciones propias. [Captura íntegra y verificación](mod08-chain-explain-20261011.json). Producto sin cambios; diagnóstico de SQL, no medición de mejora HTTP ni aceptación 2s/5s.

## Resultado y decisión

El contraste respalda un coste importante en evaluar/preparar las expresiones de huella, además del recorrido de filas. En el historial alto, las consultas con huellas originales son sensiblemente más lentas que leer las mismas filas sin esa expresión. El control con cálculo directo de las mismas huellas también resulta más rápido, con igualdad exacta sobre todas las filas presentes y misma estructura ejecutable de plan en los controles de cada nivel.

| Consulta en historial de 548 eventos | Filas | Original con función | Control de lectura sin hashing | Control JSONB sin función de huella | Control de huella directa |
| --- | --- | --- | --- | --- | --- |
| Eventos | 548 | 8,242ms | 0,469ms | 3,855ms | 4,954ms |
| Lecturas de selección | 288 | 7,494ms | 0,543ms | 3,445ms | 5,232ms |
| Lecturas de cobertura | 256 | 11,215ms | 0,846ms | 5,347ms | 7,262ms |

Valores de `Execution Time` del motor: mediana de cuatro capturas TIMING OFF por variante y consulta, no CPU pura. Cada fila de esta tabla es una consulta de una validación, no un request ni el total de cuatro páginas. No sumar estos deltas para prometer un ahorro HTTP. Los controles JSONB difieren en expresión/normalización y no aíslan SHA256 por sí solo.

Los ocho tiempos medianos de consulta suman aritméticamente 28,800ms en original y 18,817ms con expresión directa en el nivel alto; estas sumas NO son una ejecución conjunta medida, ni una comparación de pipeline, ni una latencia HTTP. No extrapolar a miles de eventos o al p95 histórico. La igualdad de huellas observada habilita una candidata para verificación posterior, no demuestra equivalencia general ni rendimiento productivo.

La prioridad derivada es ensayar una candidata limitada a las expresiones SQL que conserve la lectura física completa y todos los checks, antes que añadir índices arbitrarios, omitir verificaciones o cachear autoridad. Requiere verificar todas las familias/tombstones, zona horaria/formato/canonicalización, errores y concurrencia, y medir el recorrido HTTP pertinente con controles comparables. Esta ejecución no aplica esa candidata.

## Población y recorrido real

Runner `20261011-121055-8cc59a3c`; base `7e04016d8ece6cf52388e283eb06cf0a6040fd2b` con cambios locales preservados. Solo nuevos `tests/capacity_chain_explain.py` y `tests/test_capacity_chain_explain.py`. Fixture nuevo aprobado por servicios: 1500 revisiones, proyección seleccionada16777325bytes y originales WebP físicos67095050bytes, ambos dentro de ±1% de16MiB/64MiB.31lecturas de selección reales y cobertura parcial escalar. Binarios conservados, no seleccionados/revisados para entregar. Sesión/MFA/CSRF de pruebas reales; identidad simulada explícitamente.

Preparación por Gunicorn2 sync propio y 64 POST HTTP legítimos del servicio `inspect_batch`, cuatro páginas iguales por lote, UUID nuevo/200/no-store/EOF y cuatro nuevas lecturas de cobertura comprobadas cada vez. Cada lote crea ocho eventos reales; cabeza36→548. No filas/IDs de auditoría fabricados ni baseline/fallback existente. No Caddy/RustFS/cuotas contractuales, descargas, exportación ni captura completa.

En cada nivel se crea un hijo con LOGIN runtime independiente restringido, `current_user == session_user`, sin privilegios administrativos ni pertenencia al owner. Ejecuta `require_runtime_chain` completo y fresco antes de las sondas, adquiriendo la cabeza transaccional. La captura no añade eventos y se comprueba que el conteo final es idéntico. El hijo cierra su conexión antes de retirar su rol y credenciales y antes de la siguiente siembra. Presupuesto420s desde fixture preparado; ejecución/retirada129,849s, dentro del límite.

## Consultas y controles

Ocho familias: SELECT de eventos actual con columna `digest`, secuencia/enlace esperado y orden original; y las siete sentencias exactas de `_source_statements`. Por familia cuatro variantes:

- `native_hash`: SELECT actual con `rights_evidence_link` o `rights_evidence_row_hash(to_jsonb(s))`.
- `whole_row`: en fuentes conserva la fila compuesta `s` para exigir leer sus columnas; en eventos conserva todas las columnas actuales y sustituye únicamente `expected` por NULL.
- `jsonb_payload`: en fuentes `to_jsonb(s)::text` sin hashing ni normalización adicional; en eventos representación JSONB de enlace con fecha UTC, sin SHA256. Son controles de trabajo, no consultas válidas de autorización.
- `inline_hash`: mismos hashes calculados directamente con funciones de `pg_catalog`, manteniendo JSONB/UTF8/SHA256 y normalización UTC. En fuentes usa el `created_at` tipado directamente para esa normalización y evita el wrapper SQL/parseo del timestamp serializado. El contraste no separa cuánto aporta cada uno de esos cambios.

Antes de EXPLAIN se compara la salida completa original/directa (eventos ordenados y mapas de fuentes, con igualdad de cantidades). Se comprueban584enlaces y584huellas de fuentes sumados entre ambos niveles. `ImageRead` y `CoverageReview` no tienen filas en esta población: no están acreditadas en un corpus no vacío; tampoco hay tombstones ni mutador concurrente. No se exportan los valores de estas filas, huellas ni payloads. Los UUID de filtro de planes se sustituyen por `<synthetic-case>`.

Se realiza un warmup por variante y cuatro rondas rotadas, cada variante ocupa cada posición una vez. EXPLAIN ANALYZE/BUFFERS/VERBOSE/SETTINGS/FORMAT JSON/SERIALIZE NONE con TIMING OFF conserva tiempo total y reduce coste de temporización por nodo. Se añaden una captura nativa TIMING ON para nodos y otra nativa SERIALIZE TEXT. La igualdad de estructura ejecutable se define por tipos de nodos, joins, relaciones/índices/dirección y filas/loops de cada nodo; excluye expresiones de salida, anchos, costes y tiempos, que permanecen en los planes íntegros.

Se conservaron índices/estadísticas y no se modificaron esquema, índices, aislamiento o switches del planner. No ANALYZE manual. Se aplicó un timeout diagnóstico LOCAL15s por sentencia y90s por hijo, no límites productivos.

## Lectura de los planes y límites

PostgreSQL real17.11. Dentro de cada nivel, las cuatro variantes mantienen la estructura de ejecución observada. Entre niveles los planes cambian: el evento usa Index Scan en pequeño y Sort/Seq Scan en alto; las fuentes pasan de Nested Loop a Hash Join/Seq Scan en general. El autovacuum/autoanalyze actúa durante la siembra: las principales tablas registran dos autoanalyze en el nivel alto. Por ello no interpretar la comparación entre tamaños como crecimiento con plan fijo.

En el evento alto se estiman557filas frente548reales; en lecturas de selección284frente288 y cobertura275frente256. El ordenamiento de eventos es en memoria,210KiB en la captura temporizada, sin spill. Los recorridos de Hash Join de selección/cobertura son baratos en el control sin hashing respecto al original. No se observa una necesidad de índice nuevo en esta población de un expediente; eso no acredita planes de distribución multi-expediente distinta.

Todas las capturas tienen buffers compartidos leídos0 tras calentamiento. Esto no prueba ausencia de I/O en peticiones frías ni en carga contractual; los Seq Scan son compatibles con procesar buena parte de las filas de estas tablas pequeñas. La documentación oficial advierte sobre interpretación de planes, overhead y caché. [PostgreSQL17 — Using EXPLAIN](https://www.postgresql.org/docs/17/using-explain.html).

SERIALIZE TEXT de originales en alto mide0,475ms de conversión en eventos,0,096ms en selección y0,117ms en cobertura; no mide red ni adaptación Python. Sus tiempos provienen de una sola captura adicional por consulta y no son diferencias pareadas a sustraer de otras muestras. EXPLAIN descarta las filas resultantes; TIMING OFF sigue midiendo tiempo de ejecución total. [PostgreSQL17 — EXPLAIN](https://www.postgresql.org/docs/17/sql-explain.html).

Los planes son de consultas diagnósticas en una conexión runtime separada, no una captura EXPLAIN EXECUTE de los prepared statements del worker HTTP. Los temporizadores del motor siguen siendo wall time, no CPU de servidor aislada. No hay carga concurrente controlada ni sonda de locks. Un cambio de expresión/proyección puede influir en anchos, memoria y estimaciones incluso si coinciden los nodos/filas observados. No se han eliminado esas limitaciones con una equivalencia general.

## Verificación y cierre

**1PASS/0FAIL/0ERROR/0skips,233,992s JUnit**: una integración PostgreSQL/TCP real, sin sumar pruebas de otros runners. Gates Ruff/documentos/Django/migraciones/builder nativo pasan.1168huellas verificadas independientemente antes de actualizar documentación, cero discrepancias. El artefacto Cython validado previo se conserva; no se cambian fuentes productivas.

PostgreSQL/Redis propios etiquetados ausentes en inventario independiente; sin Gunicorn diagnóstico ni hijo EXPLAIN. Roles/credenciales propios retirados por sus contextos tras cerrar hijos, sin intervenir en servicios normales. Diagnóstico autorizado completo; MOD08 general sigue pausado y objetivos originales2s/5s pendientes.
