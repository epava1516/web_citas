# CR09: contraste de calentamiento en subida

2026-10-16, HEAD3f2c4a5 más test congelado. Run024218-36c98f77, **1PASS89,66s**. PG17.11 propio, Python3.12.15,10k sintéticos,4CPUcontrolador/1PG y límites conservados. Seis rutas públicas exactas del arnés más loginGET responden200 antes de login autenticado/draft/refresh/subida. No cambio de producto.

| CPU acumulada cProfile, ms | Frío023827 | Caliente024218 |
|---|---:|---:|
| Helper upload (petición dentro perfilador) |2019,84|262,376|
| Endpoint upload |818,39|188,930|
| ingest |102,82|140,232|
| read_upload |4,49|5,175|
| decode_image |4,35|5,011|

Filas anidadas, no sumar. Muestras únicas instrumentadas: NO reducción causal del producto, ni comparación de latencia clean. Prueba caliente:6invalidacionesPG6,136ms,302,1tarea registrada. Export externo request_wall357,943ms/callerCPU288,697ms incluye construcción/exportación de pstats después de desactivar perfilador: NO tiempo puro de petición. Esta limitación también afecta al campo externo de023827; el helper perfilado delimita petición, con overhead propio de cProfile. No modifica023338 sinperfilador.

El trabajo frío de URLConf/regex/imports casi desaparece tras sondas. Ingest sigue distribuido en ORM; no hay hotspot de decodificación que justifique Cython/mypyc. La diferencia de ingest aislada no demuestra regresión. Diagnóstico sin Celery/Beat/sockets/concurrencia, despacho registrado; calentamiento en un mismo proceso es más fuerte que seis sondas repartidas entre cuatro Gunicorn sinPID. NO prueba que el calentamiento actual sea suficiente o insuficiente. Próximo: observar sondas y primer trabajo porPID, sin modificar producto ni ocultar arranque del criterio contractual.

Artefactos artifacts/local-ci/20261016-024218-36c98f77/{upload-warm-profile.json,JUnit,source-hashes.json}. Hashes idénticos antes de editar; runner/hijo/temp/contenedores ausentes y unidad inactive/MainPID0/ControlGroup vacío. Sin productores externos/datosreales/Claude/proveedores, consumo previo intacto. Último p95clean1,173553838FAIL, sin repeticiónFAIL/900s; CR09/N3/contrato completo abiertos.
