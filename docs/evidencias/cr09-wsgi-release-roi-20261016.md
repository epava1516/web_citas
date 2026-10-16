# CR09: ROI de liberar ciclos de contexto y modelos

Fecha 2026-10-16. Base `a18d558`. Ejecución `20261016-073631-1cb15cff`.

**Decisión: no integrar la limpieza adicional de contexto/modelos.** El control A/A es estable, pero el prototipo no alcanza el ahorro fijado antes de ejecutar. Su compatibilidad y capacidad de liberar objetos no bastan para justificar esta complejidad. La corrección privada de RateForm es común a ambos brazos y permanece en producto.

## Método y resultado

PostgreSQL real propio, 10.000 filas sintéticas, WSGIHandler nativo sin Client ni captura de contexto de tests. A y B ejecutan el renderer actual; C añade render con contexto propio y limpieza de cachés de modelos tras cerrar la respuesta. Dos rutas, tres bloques ABC/BCA/CAB, seis calentamientos por brazo y 16 medidas: 288 requests medidas. Nueva conexión por brazo, calentada y con PID constante en sus medidas; planes preparados observados fuera del reloj. GC normal durante requests; colección explícita sólo antes del calentamiento para evitar basura del brazo anterior. No perfiladores ni cambios globales de política GC.

| Ruta | Referencia A/B, wall medio | Prototipo, wall medio | Cambio wall | Cambio CPU medio |
|---|---:|---:|---:|---:|
| Listado ES | 205,60 ms | 196,03 ms | −4,65 % | −5,50 % |
| Búsqueda EN | 208,60 ms | 211,55 ms | +1,41 % | −1,30 % |

A/A discrepa menos del 10 % fijado en wall y CPU en ambas rutas. C no alcanza ≥10 % de ahorro CPU y ≥5 % de ahorro wall en ambas rutas. No se modifican los umbrales después de observar el resultado. El candidato no demuestra ROI suficiente; no se interpreta como empeoramiento universal ni se repite una carga limpia a ciegas.

El test termina **1 PASS, 176,95 s**, porque comprueba paridad y completa el diagnóstico; `eligible_for_integration=false` es la decisión de rendimiento. Las 288 respuestas conservan cuerpo nativo, status 200, no-store y exactamente 39 SQL por request. Los 132 cierres del candidato procesan 24 filas cada uno. El JSON conserva medias, controles, preparación y límites; las 288 muestras completas permanecen en el artefacto local `wsgi-release-roi.json`.

## Evidencia y límites

Fuentes congeladas contrastadas independientemente con el manifiesto, JUnit 1/0/0/0, PIDs/start_ticks terminados, temporal ausente, contenedores ausentes y cgroup vacío. Controlador afinidad 0–3/3584 MiB/swap0/512 tareas; PostgreSQL 1 CPU/1536 MiB y Redis propio bajo los límites habituales. Las puertas previas de dependencias bloqueadas, Ruff, documentación, Django, migraciones y kernel nativo pasaron.

Los 15 contratos previos de renderer (`073412-3937f45b`) y el diagnóstico de objetos no se reclasifican como demostración de ahorro. No hay Gunicorn/TCP, concurrencia, escrituras concurrentes ni prueba del SLO en esta ejecución. Último p95 limpio permanece 1,013029795 s; no hay medición nueva de p95, aceptación N3 ni cierre CR09. El siguiente análisis debe volver a los costes materiales observados, evitando prolongar variantes de esta limpieza sin evidencia nueva.
