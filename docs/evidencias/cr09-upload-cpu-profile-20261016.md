# CR09: perfil CPU de subida aislada

HEAD8350269 más test diagnóstico congelado. Primer intento023718-503d8d64: ERROR de Ruff imports, antes de pytest; conservado y corregido sólo instrumento. Segundo023827-9f139f01: **1 PASS93,23s**. Python3.12.15/PG17.11 propios,10k sintéticos,4CPU controlador/1PG y límites existentes.

cProfile usa time.thread_time, sólo durante una petición Django test client. Sin workers/tareas asíncronas ejecutadas; idénticas limitaciones del diagnóstico anterior. Registra nombres/ubicaciones/contadores/tiempos, no payload, SQL ni parámetros. Artefacto upload-cpu-profile.json. La instrumentación multiplica fuertemente el coste y no debe compararse con clean/p95.

| Función/fase instrumentada | CPU acumulada ms |
|---|---:|
| Petición completa upload helper | 2019,84 |
| import_module | 888,63 |
| LocaleMiddleware.process_request | 853,43 |
| Endpoint upload | 818,39 |
| regex_helper.normalize | 508,97 |
| ingest | 102,82 |
| read_upload | 4,49 |
| decode_image | 4,35 |

Filas anidadas/solapadas: NO sumar. regex normalize1033llamadas; principal self116,03ms. El perfil incluye arranque frío de URLConf/regex/imports. Por eso los382ms CPU del diagnóstico anterior NO son prueba de CPU de ingest ni de imagen; inferencia causal retirada expresamente. El arnés HTTP realiza seis sondas previas y loginGET, así que no se traslada este arranque a la carga sin prueba porworker. Siguiente: diagnóstico de subida con calentamiento equivalente, y comprobar si quedan rutas/reverse pendientes en cada worker; evitar precarga especulativa.

Fuentes congeladas verificadas antes de editar; runner/hijo/temporal y contenedores propios ausentes. Ambas unidades terminales. Fallo Ruff no cuenta como test ejecutado. Sin producto modificado ni nueva métrica p95. Último clean1,173553838FAIL, CR09/N3/contrato completo abiertos. Sin Claude/proveedores/producción, consumo anterior intacto.
