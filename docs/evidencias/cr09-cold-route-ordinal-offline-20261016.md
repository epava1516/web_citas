# Reconciliación fría por worker y ruta

La revisión nativa aislada [reportada](cr09-cold-cost-review-agent-20261016.json) no propone integración. Sus observaciones son entradas para contraste, no evidencia de pruebas. Codex confirmó fuentes y alcance de escritura exclusivo del informe. Formato propio recibido, no aceptación formal del wire del contrato externo.

[Reconstrucción propia](cr09-cold-route-ordinal-offline-20261016.json):24primeras combinaciones worker/ruta en los eventos actuales;14tienen muestras posteriores del mismoPID/ruta exacta/número deSQL,10no. No equivale a mismos parámetros ni misma rama. Los preámbulos no conservan rutas; faltan cardinalidades y estructuras más allá del límite32. El upload ocupa0,427724s deWSGI enworker3519796; no constituye por sí solo explicación causal de la cola.

Estos límites impiden inferir coste frío comparando promedios con diferente trabajo. No se adoptan calentamiento, planes genéricos, uniones o ventana descartados. RULE_SOURCES ya tiene LRU; no hay evidencia temporal de su hash durante llegadas que justifique adelantarlo.

Prerregistro siguiente: único diagnóstico instrumentado de mismoescenario20rps60s/10ksintéticos/4sync/1upload/refresh ycuotas; modo opt-in SQL_SHAPES eleva límite de huellas32→128 y registra hasta8formas porhuella,64longitudes anidadas porforma, sin valores, textosSQL o claves de parámetros. Huella de ruta permite identificarpreámbulos contra manifiesto sin guardarquerystring. Overflow explícito si supera límites. Ocho pruebas de protocolo/privacidad/contabilidad aprobaron0,45s, sin DB ni recursos de aplicación.

No medición limpia ni aceptación p95. Reconciliar mismoPID/ruta/huella/cardinalidad/rama observable antesde inferir cambio; si datos no separan espera/ejecución, mantenerlo desconocido. PostgreSQL distingue estadísticas de [planificación y ejecución](https://www.postgresql.org/docs/17/pgstatstatements.html); no se equipara cursor SQL conCPU PostgreSQL. Esa extensión no se activa en este diagnóstico. Sin otra carga limpia ni900.
