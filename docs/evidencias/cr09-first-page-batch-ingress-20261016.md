# CR09 — diagnóstico WSGI/SQL/GC de la integración

Run `092506-94786e8c`, base4a54d6e, **1FAIL185,89s** por umbral temporal. Es diagnóstico instrumentado, no repetición limpia de aceptación: p95HTTP1,168393379s, generador válido,1200solicitudes completas/0errores/0pendientes y subida correcta. No sustituye al p95limpio1,052089655s. No se atribuye su diferencia al producto ni se cuantifica causalmente el coste del observador.

Fuentes congeladas verificadas independientemente antes de documentar; procesos controlador/hijo porPID/start_ticks terminados, temporales y contenedores propios ausentes, cgroup vacío. Mismos límites/Python3.12.15/PG17.11/kernelhostca3c/4sync/normalrefresh/generatorfreeze. Cuatro eventos static_ready preceden al reloj de llegadas. Hay1200parejas dinámicas WSGIstart/end, IDs coincidentes con cliente y ningún error de parseo/handler; reloj coherente con emisión. [Recibo y resumen completo](cr09-first-page-batch-ingress-20261016.json).

## Qué se ha delimitado

| Llegadas | N | HTTP medio | Emisión→WSGI | WSGI | CPUworker | SQLwall | GCwall |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0–1s | 20 | 808,348ms | 472,962ms | 335,590ms | 136,980ms | 170,477ms | 17,697ms |
| 1–2s | 20 | 1186,933ms | 927,845ms | 259,385ms | 112,232ms | 129,305ms | 13,709ms |
| 2–5s | 60 | 1184,398ms | 994,378ms | 190,244ms | 98,998ms | 81,313ms | 4,161ms |
| 5–10s | 100 | 1007,166ms | 823,448ms | 183,996ms | 97,192ms | 75,190ms | 10,146ms |
| 10–15s | 100 | 439,448ms | 262,787ms | 176,910ms | 94,078ms | 72,024ms | 6,395ms |
| 15–60s | 900 | 260,023ms | 73,498ms | 186,730ms | 98,685ms | 76,422ms | 7,641ms |

SQL/GC/CPU se solapan con WSGI; no son fases independientes para sumar. SQLwall no es CPU dePostgreSQL: incluye ejecución, transporte y espera de scheduling. Emisión→WSGI incluye cliente/TCP/admisión/parsing y no es una medición exacta de cola del socket. Los primeros20cuestan más dentro deWSGI y las cohortes siguientes arrastran espera cuando ese servicio ya se acerca al régimen posterior. GC contribuye a intervalos concretos, pero estos datos no justifican desactivarlo ni atribuirle todo el transitorio.

## Preparación desigual por proceso

| PID propio | Dinámicas completas | Peticiones de preámbulo | Preámbulos conSQL |
|---|---:|---:|---:|
| 2959781 | 311 | 2 | 2 |
| 2959790 | 282 | 6 | 6 |
| 2959811 | 301 | 0 | 0 |
| 2959812 | 306 | 1 | 0 |

El preámbulo incluye health y los sondeos previos; no lleva etiqueta de ruta, de modo que no se adjudica cada sondeo concreto a unPID. SQL previo sólo aparece en dos procesos. El PID2959811 comienza con `/en/` en666msWSGI/353msSQL;2959812 comienza con búsquedaES en674ms/409ms. Eso es compatible con preparación desigual, no una prueba causal aislada: las rutas/estado/concurrencia son distintos y un proceso con preámbulo también tiene consultas lentas al comenzar.

La consulta de hidratación con huella31a87e7d… tiene8ejecuciones/409,023msSQL en llegadas0–1s frente600/5709,012ms en15–60s. Es una comparación dentro de la ejecución con parámetros/rutas variables, no un planSQL capturado ni una prueba de que una caché concreta sea responsable. El observador acota32huellas por solicitud y agrupa el resto enoverflow; no se asigna ese grupo a una tabla o fase exclusiva.

## Investigación y decisión

El hook [post_worker_init deGunicorn](https://gunicorn.org/reference/settings/#post-worker-init) se ejecuta después de inicializar la aplicación. El código instalado23.0.0 es la fuente de versión fijada para confirmar el ciclo de vida; el enlace de documentación23 no respondió en esta consulta. [Psycopg](https://www.psycopg.org/psycopg3/docs/advanced/async.html#concurrent-operations) exige crear conexiones después del fork y no compartirlas entre procesos. [Django5.2](https://docs.djangoproject.com/en/5.2/ref/applications/#django.apps.AppConfig.ready) desaconseja consultas enAppConfig.ready, pues también se ejecuta para comandos y puede encontrar migraciones pendientes. Ninguna de esas fuentes demuestra ahorro en esta aplicación.

La preparación estática actual sólo resuelve rutas/traducciones/plantillas. No garantiza conexión/catálogos/planes/recorrido de publicación inicializados en cada worker. La siguiente hipótesis acotada es evaluar preparación propia por worker **como experimento de ciclo de vida**, sin cambiar todavía producto ni el escenario contractual: registrar coste total de arranque, lecturas/snapshot/configuración restaurada y efecto en las primeras peticiones. Usar exclusivamente laDB sintética del runner, después del fork y de migraciones, con límites finitos; ningún resultado/dato de publicación debe quedar como caché compartida o sustituir validación por petición.

No se modifica el reloj ni se excluyen peticiones de aceptación para hacerlas pasar. Antes de retener una política hay que justificar su comportamiento operativo, fallos anteDB/migraciones/worker reciclado y coste de arranque; demostrar que no introduce writes inesperadas ni comparte conexiones. No resucitar force_generic_plan global: ya fue descartado por ahorro insuficiente/irregular en el diagnóstico anterior. Tampoco aumentar workers, quitar controles legales ni cambiarGC sin evidencia nueva específica.

La hipótesis todavía no es corrección demostrada. Último corto limpio sigueFAIL1,052089655s; CR09/N3/global pendientes. No nueva carga limpia hasta que exista un cambio concreto justificado y verificado. Artefacto de análisis reproducible: `artifacts/cr09-batch-ingress-analysis-20261016/analyze.py`; hashes de entradas/script incluidos en el recibo.
