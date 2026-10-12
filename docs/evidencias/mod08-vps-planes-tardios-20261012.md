# MOD-08: planes SQL del historial tardío en VPS

## Resultado

Las ocho consultas actuales de cadena se observaron en dos niveles reales del
mismo expediente sintético: 36 y 2468 eventos. En este corpus caliente no aparece
un acceso a filas que justifique un índice nuevo: domina la expresión de hash
respecto a recuperar las filas. La estructura ejecutable de planes y filas es
igual entre los cuatro controles dentro de cada nivel; cambia entre niveles.
No se modifica la aplicación ni se acredita reducción del p95 HTTP.

| Consulta | Filas iniciales / tardías | Función original inicial | Función original tardía | Control de hash directo tardío | Control sin hashing tardío |
| --- | --- | --- | --- | --- | --- |
| Eventos | 36 / 2468 | 0.665 ms | 33.832 ms | 19.661 ms | 1.946 ms |
| SelectionRead | 32 / 1248 | 1.168 ms | 37.818 ms | 21.781 ms | 2.257 ms |
| CoverageRead | 0 / 1216 | 0.117 ms | 36.060 ms | 23.243 ms | 2.997 ms |

Execution Time del motor: medianas de cuatro EXPLAIN TIMING OFF por variante y
consulta, no CPU pura ni requests. El control sin hashing no satisface la
validación y nunca se propone para producción. El directo conserva las huellas
en este corpus, pero además usa created_at tipado y evita el wrapper SQL:
no atribuir todo el delta al inlining ni sólo a SHA256.

Las sumas aritméticas de las ocho medianas tardías son109.927ms en original y
66.605ms en directo. No constituyen una ejecución conjunta medida, ni tiempo de
pipeline, ni un ahorro HTTP de43.322ms. No multiplicarlas por cuatro para
prometer una reducción del request. La candidata directa retirada anteriormente
no se restaura por este resultado: necesita beneficio HTTP demostrado en VPS.

## Ejecuciones, incidencias y limpieza

| Ejecución | SHA | JUnit | Resultado del controlador | Launcher |
| --- | --- | --- | --- | --- |
| 20261012-111350-eba253e3 | 431149ce1e151185f0b1329b7d4a3c9bb27f319b | 1 FAIL, 532.004s | ERROR: presupuesto de preparación | Exit1, preservado |
| 20261012-112648-cc0ad6f8 | db5243756521281b1cb815048920606458ac81d7 | 1 PASS, 805.570s | SQL_PLANS_DIAGNOSTIC_NOT_CAPACITY | Exit1: etiqueta nueva no reconocida |

Primer fallo: se aplicó a304lotes el tope420s de la prueba antigua64lotes. Se
conservó, con planes iniciales36eventos; no se declara que alcanzó el tardío.
La variante64 conserva420s. Para la explícita304 se fijó1200s finitos de
preparación, dentro del límite9000s del runner; no cambian cuotas, SLO,
15s por SQL ni90s por hijo. Preparación/experimento final698.583s.

La segunda prueba completó ambas capturas, hashes y conteos sin fallos/errores/
skips. El launcher devolvió1 porque la lista final del controlador omitía la
etiqueta de éxito SQL recién añadida. Se corrigió sólo esa clasificación y se
verificó su expresión real de retorno para SQL diagnóstico/Error/fallo SLO,
con Ruff PASS. No se editan los recibos antiguos ni se declara un launcher0
que no ocurrió; no se repite una carga de13min para comprobar una etiqueta.

Auditorías independientes antes de editar fuentes:1415archivos idénticos en
cada ejecución, archivos sin problemas y contenedores/red/volumen propios
ausentes. Memoria conservadora propia1498865664/1494065152bytes, bajo6GiB.
Sin intervención en servicios existentes. PostgreSQL17.11, Python3.12.15,
kernel native-sealed existente, mismo perfil propio8CPU/8GiB/storage20GiB.
Imágenes y controles completos en recibos privados. No nueva imagen ni cambios
a sus etiquetas. Preparación Ruff/documentos y122tests rápidos PASS; tras
corrección de plazo6tests de separación/wrapper PASS. No invocaciones Claude.

## Método y evidencia

Se reutiliza la prueba de planes existente, adaptada al owned controller del VPS:
1500 revisiones, proyección seleccionada16777325bytes y WebP físicos67095050bytes,
±1% de16MiB/64MiB. Selección aprobada por servicios y31lecturas reales paginadas.
Se siembran304POST escalares de cuatro páginas, commits normales: cada uno añade
cuatro lecturas de cobertura y ocho eventos, comprobados. No auditorías/IDs
fabricados. Páginas repetidas, selección sólo escalar: no equivale al recorrido
completo con binarias, exportación o dos casos. Verificador de identidad simulado
explícitamente; PostgreSQL y HTTP son reales.

Gunicorn2sync propio, sin Celery/Beat de fondo ni perfiladores. Los planes se
ejecutan en otro LOGIN restringido propio y exclusivo; current_user=session_user,
sin privilegios de owner/admin y cero conexiones activas adicionales de ese
login. Atestación runtime y validación completa frescas, con cabeza bloqueada.
El niño termina antes de retirar credenciales/rol y reanudar escrituras.

Ocho consultas actuales: EVENT y siete tablas fuente. Antes de cada grupo se
compara la salida original/directa completa y su cantidad. Coinciden en ambas
capturas; ImageRead y CoverageReview permanecen vacías, no son prueba de
equivalencia con datos no vacíos de esas familias. Tampoco hay tombstones,
mutadores concurrentes o formatos/zonas hostiles en esta nueva población.

Un warmup por variante; cuatro rondas rotadas TIMING OFF; otra captura nativa
TIMING ON y otra SERIALIZE TEXT. Se conservan índices/estadísticas, sin ANALYZE
manual, índices nuevos ni switches de planner. Relojes adicionales execute/
fetch hasta consumo de resultados de una consulta nativa: incluyen cliente y
transporte, no son CPU del servidor ni latencia HTTP. No sustituir las medianas
de EXPLAIN por esa única muestra ni restar sus valores para aislar red.

## Interpretación de los planes

En inicial, eventos usa Index Scan y fuentes Nested Loop. En tardío, eventos
incluye Sort y fuentes Hash Join. Autoanalyze/estadísticas pueden cambiar con
las escrituras: no presentar el crecimiento como un único plan fijo.
Las comparaciones entre variantes sí mantienen estructura y filas observadas.

No shared read blocks ni temp read/written blocks en las rondas calentadas:
no evidencia de I/O frío o spill, pero tampoco prueba general de que nunca
existan. SERIALIZE TEXT tardío mide0.292ms para SelectionRead y0.269ms para
CoverageRead en una sola captura cada una; no mide red ni adaptación Python.
Leer las mismas filas sin el hash resulta mucho más barato; un índice no
elimina la evaluación obligatoria de las expresiones sobre las filas devueltas.

[Datos compactos, planes y auditoría](mod08-vps-planes-tardios-20261012.json).
Se eliminan Output VERBOSE repetidos del JSON versionado; las rondas, tiempos,
nodos, filtros, buffers y estadísticas siguen presentes. Completo en artifacts.

La siguiente candidata SQL sólo merece integración tras demostrar una mejora
HTTP pertinente en el VPS y conservar todas las comprobaciones. Una revisión
arquitectónica del trabajo repetido de cadena requiere demostrar equivalencia
frente a escrituras propias, cambios de cabeza, permisos, caducidad y cambios
físicos; no omitir hashes o reutilizar una cabeza antigua por supuesto.
No usar las diferencias energéticas del portátil para atribuir efectos al código.

Fuentes: [Using EXPLAIN17](https://www.postgresql.org/docs/17/using-explain.html),
[EXPLAIN/SERIALIZE17](https://www.postgresql.org/docs/17/sql-explain.html),
[Inlining SQL](https://wiki.postgresql.org/wiki/Inlining_of_SQL_functions).
Objetivos2s/5s y aceptación global/N3 siguen pendientes.
