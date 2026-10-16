# Matriz TCP tras integrar plantilla de detalle

Fuente af914b9; ejecución20261016-130840-c816996c: **6 PASS en287,00s**. DEBUG=0 explícito, PostgreSQL propio/nativo sellado, cuatro workers sync. Cinco lecturas por ruta/caso,180medidas; cuerpos, estado200, objetivo firmado y ruta state comprobados. Fuentes/PID/temporales/contenedores verificados independientemente.

Medias HTTP en ms, controles secuenciales tras preparación; no son p95 de capacidad ni comparación causal con histórico DEBUG1.

| Fixture | Anuncios | Listado ES | Listado EN | Búsqueda ES | Búsqueda EN | Detalle ES | Detalle EN |
|---|---:|---:|---:|---:|---:|---:|---:|
| repeated | 100 | 174.22 | 182.33 | 175.82 | 162.18 | 79.30 | 67.05 |
| repeated | 1000 | 244.64 | 203.68 | 228.87 | 198.31 | 72.38 | 69.50 |
| repeated | 10000 | 243.21 | 195.72 | 236.57 | 224.77 | 89.94 | 80.36 |
| diverse | 100 | 180.19 | 201.02 | 192.95 | 187.19 | 83.88 | 76.93 |
| diverse | 1000 | 173.11 | 185.06 | 168.99 | 158.43 | 65.74 | 67.75 |
| diverse | 10000 | 216.37 | 171.43 | 206.37 | 185.23 | 72.18 | 81.31 |

[Recibo y muestras](cr09-detail-template-tcp-matrix-20261016.json). Metadatos ligeros de fronteras WSGI, sin perfiladores SQL/reglas; su overhead no está cuantificado. No Beat/subida/concurrencia contractual. Siguiente corto limpio20rps60s/1200peticiones/10k/una subida/worker+Beat/GCnormal en aplicación; repetir una sola vez únicamente siPASS. No aceptaciónCR09/N3.
