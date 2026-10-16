# Corto limpio tras integrar detalle RR

Ejecución `artifacts/local-ci/20261016-104400-dcd7db55` sobre `4bf572741e1ae5c6c8273ecceb187e60551eba3e`: PASS,1prueba/187,22s. p95 global **0.675688141s**, reducción observada35,78% frente al último limpio; sin atribución causal exclusiva.

| Caso | Antes (s) | Actual (s) |
|---|---:|---:|
| Global | 1.052090 | 0.675688 |
| Listado ES | 1.077612 | 0.701276 |
| Listado EN | 1.043219 | 0.689135 |
| Búsqueda ES | 1.088525 | 0.676333 |
| Búsqueda EN | 1.184130 | 0.814752 |
| Detalle ES | 0.974921 | 0.608099 |
| Detalle EN | 0.919354 | 0.576799 |

1200programadas/emitidas/completadas, cero errores/timeouts/pendientes finales; subida exitosa. Todas las comprobaciones de validez, latencia, pendientes, subida y vaciado pasan. Sin perfiladores/observadores añadidos; mismas cuotas/20rps60s/10ksintéticos/normalrefresh. Fuentes y limpieza comprobadas independientemente. [Recibo y resumen íntegro](cr09-detail-clean-20261016.json).

PASS corresponde al criterio global del arnés; búsqueda EN individual0,814752s supera0,8s. No convertirlo en aprobación por ruta ni N3. La muestra no prueba reproducibilidad, escenario900s ni regresión común de versión final. Se prerregistra una única repetición idéntica del corto por haber cumplido; si falla se conserva y diagnostica por separado. Gunicorn del host, no latencia Docker. Sin inferencias sobre portátil/cargador.
