# CR09: invalidaciones durante subida aislada

2026-10-16, ejecución `20261016-023338-0173334a`, HEAD `8c9cf6d` más diagnóstico incluido en source-hashes. **1 PASS, 87,94 s**. PostgreSQL propio 17.11, Python 3.12.15, 10.000 anuncios sintéticos, controlador 4 CPU/PG 1 CPU y límites existentes. Misma imagen sintética seed782134 que la carga short.

| Medida aislada | Resultado |
|---|---:|
| Petición completa, wall | 462,970 ms |
| CPU hilo Python | 381,549 ms |
| Llamadas listings_publication_mark | 6 |
| Tiempo PostgreSQL acumulado función | 7,284 ms |
| Respuesta | 302 |
| Tareas de imagen registradas | 1 |

Django test client, sin socket HTTP, lectores concurrentes ni Celery/Beat. Despacho process_blob sustituido por registro; refresh.delay suprimido. Se ejecuta endpoint/ingest real y triggers reales. track_functions=all sólo en sesión propia; snapshots PostgreSQL forzados antes/después. La función instalada no se reemplaza. Tiempo PostgreSQL con instrumentación: no medida clean de aceptación. No se suma CPU del cliente al wall ni a CPU PostgreSQL.

En esta petición, invalidación representa aproximadamente 1,57% del wall: no explica por sí sola la mayor parte del coste. CPU del hilo Python equivale aproximadamente a 82,4% del wall. Próximo paso: atribución de CPU de la subida por separado, distinguiendo decodificación/validación de imagen y controles de acceso. No implica que ese mismo reparto ocurra con carga concurrente ni explica causalmente la cola inicial.

Último p95 HTTP clean continúa 1,173553838 s FAIL. Sin p95 nuevo ni repetición FAIL/900s. Fuente congelada verificada contra source-hashes antes de editar; runner/hijo/temporales/contenedores propios ausentes; unidad inactive/MainPID0. Sin datos reales, producción, proveedores o llamadas Claude. CR09/N3/contrato completo abiertos.

Datos y JUnit en artifacts/local-ci/20261016-023338-0173334a; resumen upload-mark-parsed.json. Diagnóstico explícito tests/test_owned_upload_mark_cost.py, excluido por guardia de ejecuciones generales.
