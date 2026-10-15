# Proyección mantenida: CPU integrada tras correctiva

Run `20261015-160205-09336c6a`, SHA `bb478ea` más aserciones del diagnóstico:1PASS100.58s. Fuentes y limpieza independientes verificadas. Misma instrumentación de backend propio que `145504-091e1959`,72peticiones/seis casos×12 más control inicial,sin trackerPG. Ahora se exige y registra population=projection en todos los listados/búsquedas. Sólo se añadieron esas aserciones/propiedad al diagnóstico; no cambia el código de producto.

| CPU PostgreSQL por petición(ms) | Anterior | Candidata |
|---|---:|---:|
| listing es | 60.000 | 54.167 |
| listing en | 44.167 | 31.667 |
| search es | 81.667 | 41.667 |
| search en | 81.667 | 45.833 |
| detail es | 25.000 | 20.833 |
| detail en | 11.667 | 9.167 |
| Media |50.694|33.889|

BúsquedaES count+page55.833→14.167ms; EN57.5→19.167ms. La cobertura global cuesta5.833–9.167ms y no desaparece del presupuesto. La hidratación del primer caso incluye preparación inicial; las fichas no cambian por esta candidata y también varían: no atribuir toda la diferencia al cambio. Cuantización100Hz/proc/12peticiones por caso e instrumentación impiden derivar p95 o techo de capacidad desde estas cifras.

El mantenimiento ya se ejercitó en persistencia/noop/upsert, migración instalada, sweep, generación/locks y corrección de supresión sin worker. No representa capacidad sostenida de escritura ni WAL máximo. La carga limpia siguiente incluye worker/Beat y subida normales para comprobar el escenario contractual acotado, sin observadores/perfiladores. Último limpio5.004966sFAIL intacto. Una sola carga corta nueva: si cumple, repetir una vez; si falla, conservar fallo y diagnosticar aparte. No inferir15min/N3/globalCR09 de etapas de entrega.
