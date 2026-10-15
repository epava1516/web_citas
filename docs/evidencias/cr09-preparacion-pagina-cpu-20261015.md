# Preparación de página: CPU integrada

Run `20261015-142111-875169c8`, base `e1a5050`: 1 PASS, 103.05s. Fuentes congeladas y limpieza de procesos, backend, contenedores y temporales verificadas independientemente. Mismo diagnóstico que `20261015-132918-10ec869c`: 72 peticiones sintéticas, seis casos, sin pg_stat_statements.

| CPU backend por petición | Antes ms | Ahora ms |
|---|---:|---:|
| listing es | 50.000 | 56.667 |
| listing en | 50.833 | 38.333 |
| search es | 89.167 | 81.667 |
| search en | 96.667 | 82.500 |
| detail es | 29.167 | 27.500 |
| detail en | 26.667 | 22.500 |

Media 57.083→51.528ms observada; no atribución causal ni p95. Hidratación en los tres casos de página calentados pasa de14–15ms a5–5.833ms. El primer listado ES incluye el calentamiento del umbral y no mejora en CPU total. Fichas no usan la nueva preparación y también varían: no atribuir toda la diferencia al cambio. Cuantización100Hz, doce peticiones/caso y lecturas proc añaden incertidumbre/overhead. La ejecución no demuestra capacidad.

Los 60 controles ampliados y la reducción acotada justifican una única carga corta limpia, límites intactos, sin observadores/perfiladores/estadísticas PG. El p95 anterior16.572804s sigue siendo FAIL; pendiente nueva evidencia. Sin aceptación CR09/N3 ni repetición salvo cumplimiento.
