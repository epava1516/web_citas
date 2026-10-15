# Selector de medios: beneficio real y p95 todavía incumplido

Run214838-7c455fc1, SHAf9f404d, **FAIL184.82s**. [Terminal y limpieza](cr09-media-exists-http-terminal-20261015.json). Mismos4sync/20rps60s/10k/Celery2+Beat/subida/cuotas, sin observadores/profilers; generador freeze anterior. Fuente congelada idéntica yprocesos/temporal/contenedores propios retirados, unidadMainPID0/ControlGroupvacío. No repetirFAIL ni15min/N3.

|Métrica limpia|392c2c8 anterior|f9f404d EXISTS|
|---|---:|---:|
|p95 completo|0.919814s|1.118772s|
|p50 completo|0.262638s|0.234972s|
|p95 servicioGunicorn|0.314390s|0.313042s|
|Procesamiento real taskfoto|10.094089s|0.971466s|
|CPUthread taskfoto|0.582698s|0.557832s|
|Completadasfinales|1200|1200|
|Errores/timeouts|0/0|0/0|
|Requests>=0.8s|79|108|

Tarea foto mejora90.38% observada; efecto aislado del selector ya se verificó en tres tandas con datos idénticos. **No resolvió p95**: empeora21.63% observado entre dos runs, sin atribución causal. Retener por beneficio real del procesamiento/CPUbackend y19controles, no como aceptaciónHTTP.

|Cohorte por emisión|p95 anterior|p95 actual|Lentas anterior→actual|
|---|---:|---:|---:|
|0–5s|1.207005s|1.281048s|79→91|
|5–10s|0.709048s|0.881254s|0→17|
|10–15s|0.454854s|0.383550s|0→0|
|15–60s|0.599950s|0.387142s|0→0|

Se conservan1200filas porID de servicio ycliente,0erroresparse. Medias servicio0–5=.227827s y15–60=.181786s; residual cliente−servicio .858548s/.031981s, no cola exclusiva. Las9requests iniciales con servicio>0.4s son d-3/6/7/8/9/12/13/14/15, todaslistado/búsqueda; no fichas. Servicioindividual .410899–.663560s. Dirty1se observa0.382/1.381s y0a2.382; refrescosreales0.390–0.987y1.171–1.686s. No basta para declarar única causalidad, pero coincideconrama que abandona proyección alhaberunaúnicamarca.

La mejora de medios no elimina la interacción de diseño: cobertura global limpia es requisito actual para la proyección, precisamente mientras el escenario exige escrituras concurrentes. Siguiente investigación acotada: probar en worktree aislado si, con cobertura/versionado completo ysnapshot propioRR, se puede usar proyección para filas limpias y combinar sólo los dirty validados nativamente, conservando ranking/fechas/count/paginación/guardia. No ignorar dirty ni borrar marcas. Antes de integración, comparación real con camino actual y escenarios positivos/negativos; si no conserva semántica oahorro, descartar. Sin barrido deparámetros ni cambioGC/hardware.
