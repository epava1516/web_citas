# CR09 — corto limpio después de integrar agrupación

Run `20261016-091632-958b115a`, fuente `1a0a4d588305e1a54b7bea0210964386978c6fcb`. Resultado **FAIL por latencia**,1FAIL186,68s; generador válido (`invalid_reasons=[]`),1200solicitudes previstas/emitidas/completadas,0errores/timeout/pendientes finales, subida302. Cuatro pendientes al terminar la ventana, todos drenados. No se repite el fallo ni se ejecuta el ensayo largo.

| Métrica | Corto anterior | Actual |
|---|---:|---:|
| p95 HTTP | 1,013030s | 1,052090s |
| p95 servicio Gunicorn | 0,300505s | 0,297714s |
| Completadas | 1200 | 1200 |
| Errores | 0 | 0 |

La diferencia de p95 HTTP es +3,86% observada; no se atribuye causalmente a la agrupación, RateForm, hardware ni a la imagen con una sola comparación entre cortes. El ahorro secuencial previo no demuestra ahorro en la cola concurrente. Los percentiles HTTP y servicio tienen poblaciones/mediciones propias y no se restan para obtener un percentil de cola.

| Caso | Muestras | p95 HTTP |
|---|---:|---:|
| /es/ | 200 | 1.077612s |
| /en/ | 200 | 1.043219s |
| /es/?q=photography | 200 | 1.088525s |
| /en/?q=synthetic | 200 | 1.184130s |
| /es/listing/<synthetic-id>/ | 200 | 0.974921s |
| /en/listing/<synthetic-id>/ | 200 | 0.919354s |

Percentil por rango más próximo (`ceil(n*0.95)-1`), recalculado de las muestras retenidas; el global coincide exactamente con el informe del arnés.

| Ventana de llegada | Solicitudes | p95 HTTP | >=0,8s |
|---|---:|---:|---:|
| 0–5s | 100 | 1.303286s | 91 |
| 5–10s | 100 | 0.949415s | 39 |
| 10–15s | 100 | 0.498828s | 0 |
| 15–60s | 900 | 0.353078s | 0 |

Entorno: Python3.12.15/Django5.2.17/Gunicorn23/PG17.11, kernel hostnative-sealedca3c3885…,4sync/Celery2+Beat y refresco normal,10ksintéticos/20rps60s/1subida, generatorfreeze igual al corto anterior. Sin perfiladores ni observadores deworkers; permanece el colector de estado1Hz y su coste no está causalmente cuantificado. Presupuestos propios anteriores conservados. El manifest contiene texto heredado sobre PG compartido; el runner y recibos de contenedores acreditan PG propio en esta ejecución, sin afirmar aislamiento del host frente a toda actividad externa.

Fuentes congeladas comprobadas antes de documentar; procesos controlador/hijo por PID/start_ticks terminados, contenedores y temporal ausentes, cgroup vacío. Imagenv6 verificada aparte, no es la topología de esta carga host. Fallo y muestras conservados; [recibo y resumen](cr09-first-page-batch-clean-20261016.json).

Siguiente: diagnóstico separado de muestras ya retenidas (distribución temporal, correspondencia por ID entre cliente y servicio y estado/refresh), sin repetir cargas ni proponer otro cambio hasta delimitar la causa. No aceptación CR09/N3 ni global.
