# B07 — Descomposición de la última carga corta

Estado: análisis descriptivo de169 completado, sin nueva carga ni corrección de producto. Ocho de18cerrados y900s bloqueado.

La [auditoría169](169-referencia-corta-estadisticas-completas-beta-b07-20261021.md) acredita un FAIL válido de latencia. El [análisis](evidencias/b07-short-latency-decomposition-20261021.json) une exactamente1200IDscliente/servicio sin registros duplicados o errores de parseo. Conserva todas las peticiones y agrupa ventanas por emisión real, no por finalización.

| Ruta | Peticiones | p95cliente | p95servicio Gunicorn |
| --- | ---: | ---: | ---: |
| Listado |400|1256,042ms|367,252ms|
| Búsqueda |400|1243,644ms|371,979ms|
| Ficha |400|1075,185ms|80,023ms|

Global p95cliente1234,081ms y p95servicio352,746ms. De1200peticiones,1152tardan al menos800ms en cliente; ninguna tiene servicio registrado de800ms. No restar percentiles para obtener espera. La resta por cadaIDcliente−servicio produce mediana844,193ms/p95994,329ms/mínimo1,575ms. Ese residual incluye transporte, esperas previas y fronteras de reloj; no es una medida exacta de cola/socket ni CPU.

La implementación Gunicorn instalada SyncWorker.handle parsea la petición antes de handle_request; este último inicia request_start después de pre_request y registra acceso tras resp.close. Por tanto el servicio no incluye admisión ni parseo completo. El transporte asyncio actual empieza su reloj antes de open_connection y no limita peticiones pendientes: verificar conexión/primer byte y admisión es el siguiente diagnóstico pertinente. La demora del generador válida no descarta espera en conexión o servidor.

Las seis ventanas de10s tienen p95cliente1120–1288ms, no sólo una lectura fría. El servicio agregado suma241,657s, media201,381ms; incluye finalizaciones después de60s. No convertir suma/60 en ocupación medida de workers, CPU ni demostración causal de saturación. Tampoco afirmar que la ficha está libre de coste o que una consulta concreta causa la espera.

Decisión: localizar límites conexión/admisión/respuesta antes de repetir una carga o aumentar workers; mantener4sync,20RPS,datos/SLO/criterios y FAIL originales. Cualquier instrumento deberá calibrar integridad y declarar coste/alcance; no llamar PASS a métricas de servicio en sustitución de latencia observable. No se ejecuta900s ni se adopta una optimización desde esta correlación.

La primera clasificación local buscaba una ruta /search y agrupaba las búsquedas como fichas: se detectó al contrastar rutas originales, se preservó el artefacto inicial ignorado y se corrigió a query?q=. El análisis corregido concilia400/400/400; el resultado de carga y su auditoría no cambian. No es un fallo del producto ni una nueva prueba.
