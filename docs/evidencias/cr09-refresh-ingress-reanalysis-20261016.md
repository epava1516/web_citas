# Relectura temporal de la captura existente

Sin carga nueva ni cambios de producto: análisis offline de `20261016-031208-ec0fd4c3`, captura instrumentada histórica. Script reproducible/resultados y SHA256 de archivos de entrada en `artifacts/cr09-refresh-ingress-reanalysis-20261016`. Origenmonotónico real3841084,000926732, no objetivoBeat anterior (diferencia202,469ms).

| Hecho de la misma captura | Tiempo desde origen |
|---|---:|
| Primer refresco que limpia1marca |0,539–1,104s|
| Segundo refresco que limpia1marca |1,475–2,084s|
| 58muestras posteriores de Dirty, hasta60s |0marcas en todas|
| Peticiones emitidas tras2,084s y antes15s |258;103 tardan≥0,8s|

| Cohorte existente | Espera media emisión→WSGI | ServicioWSGI medio |
|---|---:|---:|
|0–5s|829,518ms|229,978ms|
|5–10s|624,982ms|184,378ms|
|10–15s|328,910ms|191,699ms|
|15–60s|217,730ms|191,256ms|

El sampler1Hz puede perder marcas breves y el final de tarea sólo da una cota de limpieza. La cola acumulada durante el trabajo inicial puede prolongar el retraso después de limpiar; no refuta influencia del upload. Sí impide afirmar que una marca persistiera durante los15s o que eliminar invalidaciones garantizase el objetivo. No nueva métrica p95 ni comparación causal con clean.

Un cálculo exploratorio FIFO con tiempos de servicio fijados ofreció margen con6servidores, pero fija precisamente el servicio que cambia al añadir procesos: no es predicción ni evidencia de capacidad. El [contraste real4/6](cr09-sync-headroom-20261016.md), con beneficio modesto y p95 inconsistente, sigue vigente y no queda invalidado por el cálculo; no justifica otro ensayo deworkers. No aplicar simulación como verificación real.

Siguiente rendimiento requiere atribución de coste de servicio/arranque bajo límites, preservando invalidación conservadora y sin barridos de concurrencia, relajación SLO ni repetición ciega del FAIL. El muestreo externo/cProfile previos conservan sus alcances; no asumir que repetirlos sin una pregunta nueva aporta evidencia. CR09/N3 siguen abiertos.
