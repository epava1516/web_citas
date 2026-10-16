# Corto limpio tras integrar plantilla de detalle — FAIL

Ejecución `20261016-131431-d072699a`, SHA `be7c5d8a71efc3bf41bb159c52dad7716d2ad90e`, producto af914b9:1FAIL186,05s. p95observable **0,862172866s**, superior a0,8s. Generador válido,1200completadas/0errores/timeouts/pendientes finales,subida conforme. Fuentes y limpieza verificadas independientemente.

| Caso | Repetición anterior s | Plantilla integrada s |
|---|---:|---:|
| Global | 0.880357 | 0.862173 |
| Listado ES | 0.860301 | 0.896219 |
| Listado EN | 0.904956 | 0.835364 |
| Búsqueda ES | 0.973179 | 0.877694 |
| Búsqueda EN | 0.914257 | 0.931396 |
| Detalle ES | 0.726351 | 0.757642 |
| Detalle EN | 0.768361 | 0.727895 |

Observado global−2,07% frente0,880356520s; una sola observación no demuestra mejora reproducible ni efecto causal exclusivo. Primer ensayo anterior0,675688141sPASS sigue conservado, no sustituye esteFAIL. Misma topología4sync/cuotas/20rps60s/10k/una subida/worker+Beat/GCnormal en aplicación; sin perfiladores añadidos. [Recibo completo](cr09-detail-template-clean-20261016.json).

Las69respuestas≥0,8s corresponden todas a llegadas0–5s. p95 por llegadas:0–5=1,127027s;5–10=0,688799;10–15=0,274186;15–60=0,321410. Servicio medio0–5=0,219077s,HTTPmedio0,875951s;15–60=0,171088/0,186974s. Emparejado porID; diferencia no identifica cola exacta. Trabajo de servicio acumulado por cohorte de llegada:primersegundo6,441s/20peticiones,segundo4,817s; referencia15–20s16,920s/100peticiones. Son tiempos de servicio wall superpuestos,no CPU ni prueba de reparto exacto entre workers.

Conservar FAIL: no repetición limpia ni900. Matriz TCP actual6PASS ya documentada, no aceptación de capacidad. La captura previa de py-spy preparaba dos lecturas de referencia antes del bucle y por tanto **no capturaba primera lectura real del proceso**; no basta para atribuir este transitorio. Siguiente diagnóstico separado debe capturar primeras peticiones de proceso nuevo con preparación estática de producción, sin ejecutar solicitudes de referencia en ese hijo; no cambiar código o políticas antes de esa evidencia. CR09/N3 abiertos; imagenDocker v7 corresponde al producto anterior4d2d4a5, no al nuevoaf914b9.
