# Carga limpia con preparación estadística explícita

Run `20261015-204103-c1ea755d`, SHA `1dd8041`: **FAIL184.28s**. [Recibo completo y casos](cr09-estadisticas-fixture-http-terminal-20261015.json), [preparación](cr09-estadisticas-fixture-http-preparacion-20261015.json). Misma carga4sync/20rps60s/10k/worker yBeat propios/una subida/generador congelado, sin observadores/perfiladores/trackerPG. Todas las peticiones iniciales incluidas.

Sólo cambió la preparación: ANALYZE de cinco tablas tras el bulk, antes de las validaciones nativas. `dataset.planner_statistics` confirma esa preparación en el manifiesto. Apps/config/templates/static idénticos a0ab41bf; no atribuir una diferencia a optimización del código de requests ni al portátil. La corrección del atasco de preparación mantiene su evidencia9PASS separada.

Fuentes idénticas verificadas, raíz/pytest/CeleryBeat ausentes; temporal yPGRedis propios retirados. Unidad terminalfailed/MainPID0/ControlGroupvacío acredita descendientes. Metadatos sharedPG/normalstack heredados conservados en resumen original y contrastados con nombre/label/adaptador propios; no acceso a servicios normales.

| Métrica | Antes200612 | Preparación corregida204103 |
|---|---:|---:|
| p95 completo(s) |0.9611368430778384|1.1267758989706635|
| p50 completo(s) |0.24246060103178024|0.23226714693009853|
| Pendientesal60s |5|3|
| Completadasfinales |1200|1200|
| Errores/timeouts |0|0|
| ServicioGunicornp95(s) |0.314946|0.313512|
| Peticiones>=0.8s |85|106|

| Caso,p95(s),200cada | Anterior | Actual |
|---|---:|---:|
|ListadoES|0.953022|1.148124|
|ListadoEN|1.034308|1.154845|
|BúsquedaES|0.988647|1.117647|
|BúsquedaEN|0.968899|1.154644|
|DetalleES|0.900719|1.042584|
|DetalleEN|0.905147|1.033815|

Sin mejora de p95 observada. Comparación entre ejecuciones con preparación distinta, no causalidad exclusiva ni reproducibilidad. Generador válido,1200emitidas/completadas,0omisiones/errores/timeouts/pendientesfinales,subida302. Todos los checks cortos pasan salvo latencia. No repetirFAIL ni avanzar15min/aceptarCR09/N3 por este resultado.

| Emisión,mismas muestras |N|p95(s)|>=0.8s|
|---|---:|---:|---:|
|0–5s|100|1.376427|89|
|5–10s|100|0.953755|17|
|10–15s|100|0.454107|0|
|15–60s|900|0.461336|0|

El transitorio de requests no queda resuelto al corregir el defecto de preparación. Que los900finales pasen no sustituye el total ni la prueba contractual. Próxima acción: revisar trazabilidad del diagnóstico corto con el criterio contractual y elegir un diagnóstico separado del transitorio desde la evidencia ya disponible, sin cambiar límites/criterios, levantar puertas, excluir arranque ni encadenar cargas especulativas. GC observado sigue siendo una contribución periódica, sin política modificada. Objetivo íntegroCR09→CR10→GS01→BF/BB→C activo.
