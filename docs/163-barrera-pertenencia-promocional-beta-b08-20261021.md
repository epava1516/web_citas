# B08 — Barrera de pertenencia exacta a población

Estado: paridad verificada, compuerta de mecanismo false; barrera descartada sin ROI ni modificación de producto. Ocho de18cerrados; cortoTCPFAIL vigente.

## Evidencia que motiva esta vía

Los planes de162 muestran trabajo repetido también en el SELECT de derechos original: población de búsqueda estimada1fila frente1000reales, rama de permisos repetida por la población exterior. Agrupar derechos en servidor no resolvió ese problema, y el prototipo SetPager sigue sin adoptar. No comparar latencia entre los planes anteriores ni atribuir el plan original lento al prototipo.

Esta variante actúa sobre la implementación actual original: conserva live_entitlements/person_queryset, streamer500, ranking/mapa Python/JSON y guarda final. Sólo compila la misma población completa sin orden como subconsulta SQL parametrizada y añade OFFSET0. Es una identidad de pertenencia sin tope ni eliminación de filtros. La hipótesis es evitar que el planificador aplane esa subconsulta de modo que vuelva a evaluar permisos por cada candidato. No se afirma eficacia antes de ver el plan.

No se leen derechos globales ni se sustituye la regla de gestión. No se añaden IDs persistentes/cachés, hints, parámetros PostgreSQL ni cambios de índices/recursos. El compilador Django genera SQL y parámetros; OFFSET0 es texto constante. Una población EmptyResultSet vuelve a la representación original; una consulta ya cortada conserva rechazo al retirar orden. Se enlaza sólo en hook de snapshot propio; transacción heredada conserva su camino original.

## Gate funcional y decisión previa

beta_membership_barrier_diagnostic.py clona en memoria la función original fijada por SHA y cambia exactamente la expresión de pertenencia. Ocho casos PostgreSQL: referencia nativa congelada con32páginas/12combinaciones, tres revocaciones, snapshot concurrente, checkedESEN y heredadoREADCOMMITTED. Cada hook compara IDs completos y ordenados de derechos de ambas consultas, sin comparar sólo totales; exige número de usos y ausencia del hook en el heredado. Ninguna comprobación sustituye los permisos por un simulador.

Antes del runner: Ruff y grafo dirigido, freeze.1worker, recursos propios y Telegramterminal, fuentes/cleanup/PIDs auditados. Después, si pasa, diagnóstico1000/200 en listado/búsqueda con misma población y snapshots propios, paridad de derechos/página y planes EXPLAINANALYZE posteriores. Si la barrera no evita la repetición, descartar esa hipótesis sin ROI10000 ni bajar umbrales. Si mejora el mecanismo, todavía requiere gate de coste y bordes antes de adoptar; conservando los criterios10%ambasrutas/controlesA/A/noempeorarCPU. No repetición de permisos enlazados156 ni derechos globales127.

## Corrección de perímetro del diagnóstico

El camino actual usa iterator500 y cursor nombrado. Los planes162 fueron EXPLAIN del SELECT ordinario; sus loops son evidencia de ese plan, no prueba de ejecución de esos mismos loops en el cursor real ni causa demostrada del TCPFAIL. El diagnóstico156 ya distinguía SELECT/DECLARE en planificación; aquí debe conservarse esa distinción con ejecución observada. Referencia primaria: [PostgreSQL17 EXPLAIN](https://www.postgresql.org/docs/17/sql-explain.html), que admite DECLARE y explica el alcance e intrusión de ANALYZE.

beta_membership_barrier_plans.py, un caso aislado tras el gate funcional:1000/200, misma población propiaRRreadonly, IDs completos de derechos y24pares de página iguales. Examina original/barrera por SELECT y por DECLARE NO SCROLL CURSOR WITHOUT HOLD mediante EXPLAINANALYZE BUFFERS TIMINGOFF, con cursor_tuple_fraction observado sin modificar. No deja cursor creado. Guarda planes redactados, no SQL/params/UUID en avisos.

Compuerta de mecanismo prefijada: al menos una ruta debe pasar de más de200loops en nodos core_agency/core_agencymember del cursor original a como mucho200en la barrera; ambas rutas candidatas deben quedar como mucho200. Si el cursor original ya evita la repetición, la hipótesis no queda justificada por los SELECT ordinarios y no pasa a ROI por este motivo. Esta compuerta no prueba10%de mejora, memoria o CPU. Conservar todo resultado, incluidos compuertafalse, discrepancias de plan y cualquier error del arnés.

## Resultado y decisión

140801-e4fad5e8:8PASS/0FAIL/0SKIP,139,82spytest sin warnings. [Auditoría funcional](evidencias/b08-membership-barrier-20261021-140801-e4fad5e8-audit.json):44comparaciones completas de IDs de derechos;32páginas/12combinaciones, revocaciones3, snapshot concurrente, checkedESEN y ausencia del hook heredado.726runtimeintactos, freeze/cleanup/PIDs/Telegram terminal y auditoría confirmados.

141118-80ad46c0:1PASS de integridad,126,90spytest sin warnings. [Auditoría de planes](evidencias/b08-membership-barrier-20261021-141118-80ad46c0-audit.json):1000perfiles/200derechos, paridad completa de derechos y24pares de página. Fuentes idénticas a la corrida funcional,726runtime intactos y recursos/procesos propios retirados; Telegram terminal/auditoría enviados. DECLARE con ANALYZE se ejecutó correctamente sin dejar cursor. cursor_tuple_fraction observado0.1, sin modificar.

| Ruta | Original SELECT | Original cursor | Barrera SELECT | Barrera cursor |
| --- | ---: | ---: | ---: | ---: |
| Listado, ms observados |2,477|2,393|8,062|8,357|
| Búsqueda, ms observados |3,908|4,365|13,374|12,323|

En los ocho planes, el máximo de loops de los nodos core_agency/core_agencymember es200. La compuerta exige reducir la repetición en el cursor original de al menos una ruta, y no ocurre: cursor_mechanism_gatefalse. No hay ROI10000/2000 ni adopción. Tiempos de EXPLAINANALYZE son observaciones aisladas/instrumentadas, no una regresión causal de HTTP ni CPUbackend.

La repetición extraordinaria del SELECT ordinario en162 no se reprodujo en este nuevo estado local ni en SELECT ni en DECLARE. No se ha aislado por qué cambió el plan entre corridas; no atribuirlo a cursor, estadísticas, autovacuum, caché u host sin evidencia adicional. Tampoco se demuestra que el plan ordinario162 fuera el plan del cursor del HTTP actual. Conservarlo como evidencia de un plan observado, sin convertirlo en causa del TCPFAIL. La siguiente optimización debe apoyarse en atribución actual del camino completo y su cursor real, no en otro arreglo de ese supuesto cuello. Ocho de18cerrados, B07FAIL sigue vigente.
