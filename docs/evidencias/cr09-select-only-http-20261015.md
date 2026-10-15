# Carga limpia tras excluir órdenes de transacción de la preparación

Run `20261015-200612-84c1b59a`, SHA `0ab41bf`: **FAIL en 184.66 s**. Misma carga: 4 procesos sync, 20 rps durante 60 s, 10k anuncios sintéticos, worker y Beat propios, una subida y preparación del GC del generador. Sin observadores, perfiladores ni tracker PostgreSQL. [Recibo completo](cr09-select-only-http-terminal-20261015.json).

Fuentes verificadas independientemente. Raíz, pytest y Celery/Beat ausentes; directorio temporal y contenedores PostgreSQL/Redis propios retirados. Unidad terminal, MainPID0 y ControlGroup vacío acreditan también que no quedan descendientes Gunicorn. Metadatos estáticos heredados pg_server_shared/normalstack se conservan como originales; no describen la propiedad real, verificada con nombres/labels y adaptador acotado.

| Métrica | Anterior 194053 | Actual 200612 |
|---|---:|---:|
| p95 completo (s) |0.8977655060589314|0.9611368430778384|
| p50 completo (s) |0.22488752426579595|0.24246060103178024|
| Pendientes al cerrar 60 s |5|5|
| Completadas finales |1200|1200|
| Errores/timeouts |0|0|
| Servicio Gunicorn p95 (s) |0.311439|0.314946|
| Peticiones >=0.8 s |71|85|

| Caso, p95 (s), 200 peticiones cada uno | Anterior | Actual |
|---|---:|---:|
| Listado ES |0.897766|0.953022|
| Listado EN |0.893532|1.034308|
| Búsqueda ES |0.998651|0.988647|
| Búsqueda EN |0.948491|0.968899|
| Detalle ES |0.766312|0.900719|
| Detalle EN |0.858274|0.905147|

No hay mejora de latencia observada: p95 aumenta aproximadamente 7.06%. Una ejecución por versión no prueba regresión causal. La corrección elimina preparación inútil demostrada (24 planes de utility→0), pero **no se presenta como optimización de p95 validada**. Se retiene provisionalmente por ese comportamiento acotado de caché, pendiente de revisión en la versión final. No se fuerzan planes genéricos en el producto.

Generador válido, 1200 emitidas y completadas, cero omisiones/errores/timeouts/pendientes finales, subida302. Todos los checks cortos pasan salvo latencia. Conservar FAIL; no repetir sin intervención justificada, no ensayo15min ni aceptación CR09/N3.

| Emisión, mismas muestras | N | p95 (s) | >=0.8 s |
|---|---:|---:|---:|
|0–5s|100|1.255537|84|
|5–10s|100|0.735150|1|
|10–15s|100|0.464278|0|
|15–60s|900|0.524192|0|

El transitorio persiste, no queda resuelto por evitar preparar SAVEPOINT/RELEASE. Próximo paso finito: aislar el coste de planificación de la hidratación con la caché ya corregida, incluyendo restauración y evitando el wrapper de transacciones extra del experimento anterior. No cambiar carga, cuotas, warmup, GC o criterio por el resultado. Las pausas GC periódicas observadas siguen siendo una hipótesis adicional, no una autorización para modificarlas a ciegas. Objetivo completo CR09→CR10→GS01→BF/BB→C activo.
