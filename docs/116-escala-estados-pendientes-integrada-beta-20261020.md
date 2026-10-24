# Escala del recorrido integrado con anuncios pendientes

Fecha: 2026-10-20. Estado: escalas100/1000/10000 auditadas PASS de integridad y paridad, con todos los manifiestos de fuentes idénticos; sin aceptación de capacidad. Continúa [115](115-contraste-segunda-fase-nativa-beta-20261020.md); no sustituye su contraste A/A/C ni los negativos de TCP.

Se conserva sin editar el diagnóstico114 del fallback anterior. El nuevo instrumento explícito tests/beta_integrated_pending_scale_diagnostic.py exige la fuente publication_state.py SHA282f88e5af3c3f49f618aaf9bf3c5949e0d038f7699bfe6ca79ac880998703c6 y límites48/1000. Poblaciones sintéticas100,1000,10000; derechos20%Top/Premium por servicios, sin proveedor/pagos/datos personales reales. Ejecutar100 primero, auditar antes de1000 y auditar antes de10000. Sin otras baterías ni ediciones durante cada medida. Si se descubre una espera de horas, aplicar el relevo persistente y aviso previo autorizados, sin fingir finalización.

Cada población: refrescar y leer todas las páginas del listadoES como referencia fresca. Medir cuatro rutas —listadoES, listadoEN, búsquedaEN synthetic y página mediaES— con un calentamiento, cinco controles, una observaciónSQL y una de cProfile/contextos. Marcar49candidatos todavía públicos compatibles con synthetic, leer todas las páginasES y exigir bytes/IDs/orden/recuento/patrocinio idénticos a la referencia fresca; repetir las cuatro rutas. Toda petición mantiene state/trusted_state o state/trusted_state_extended_unknown según fase, con49pendientes y sin worker de refresco ni reparación en GET. No se fuerza fallback para completar población a10000.

Total por población:40controles+8warm+8SQL+8perfiles+dos recorridos paginadosES;74HTTP/5páginas a100,148HTTP/42páginas a1000,898HTTP/417páginas a10000. Guardar firmas de todas las páginas, firmas/hash de controles, razones y recuentos de rutas, marcas persistentes, configuraciónGC y contadores de CPU. Aplicación: CPU del hilo; PostgreSQL: backend físico identificado por SQLPID y propiedad del contenedor/cgroup/start_ticks, schedstat antes/después fuera de relojes. Ningún profiler ni wrapperSQL en controles. DíaUTC constante y GC normal.

Las ocho observaciones registran execute sin FETCH, filas/tiempo inclusivo de contextos y funciones de cProfile sin argumentos/SQL. No sumar inclusivos, confundir execute con CPU/tiempoSQL completo ni cinco máximos con estimación robusta de p95/p99. El orden fresco→pendientes es fijo y descriptivo, no una nueva comparación causal balanceada ni aceptación de un presupuestoTCP. El ROI causal de1000 pertenece a115 y sus controles separados.

Límites: paridad paginada completa sólo en listadoES; listadoEN/búsquedaEN comprueban primera página entre fases y ES también página media. La referencia de escala es el recorrido fresco integrado, con guarda nativa de cada página; no una reconstrucción nativa independiente de toda la población10000. La referencia nativa completa corresponde a la regresión focal100 y contraste1000 de115, sin extrapolar esa cobertura. Agencia, geografía e imágenes compartidas no acreditan distribución nacional. No CPU/RSS de todo el servicio, proveedores reales, capacidad ni aceptación beta. El corto limpio20RPS sigue FAIL;900s bloqueado.

Cada resultado necesita JUnit, fuentes congeladas comparadas de nuevo, auditoría independiente, limpieza y recibo terminalTelegram confirmado. PASS del diagnóstico significa integridad y paridad en su alcance, no cumplimiento del cortoTCP ni cierre automático deB07/B08.

## Matriz ejecutada y auditada

| Perfiles | Ejecución | HTTP | PáginasES por fase | Medianas frescas, cuatro rutas | Medianas con49pendientes |
|---|---|---:|---:|---:|---:|
|100|151704-9021253a|74|5|141–172ms|336–367ms|
|1000|151920-dfa7ff40|148|42|171–199ms|357–398ms|
|10000|152335-d79269bd|898|417|262–350ms|473–587ms|

Cada ejecución:1PASS/0FAIL/0ERROR/0SKIP, PostgreSQL/Redis reales locales, GC normal,49marcas persistentes. Auditorías b07-integrated-pending-100/1000/10000-audit-20261020.json verifican cada firma/ID/etiqueta, todos los tamaños de páginasES, controles y CPU del backend propio; fuentes actuales comparadas de nuevo antes de editar, recursos retirados y recibos terminales1792509533767498935-796733/1792509772714895288-811694/1792511107648271632-839041 entregados. En10000, JUnit1258,785s y paso pytest1261,353s; no atribuir ese tiempo de batería a latencia de petición.

La matriz b07-integrated-pending-matrix-20261020.json confirma igualdad completa de los tres manifiestos de fuentes, no sólo producto o instrumento. Todas las páginasES frescas y con pendientes son idénticas por tamaño, sin duplicados/omisiones. En las cuatro rutas observadas, fresco hidrata24filas; pendientes primera página73+24 y página media49+24: máximo97 independiente de estas tres poblaciones. No se convierte esa observación en RSS del servicio ni en equivalencia nativa independiente10000. Los intervalos de la tabla son mínimos/máximos de medianas por ruta, no p95 ni presupuesto bajo concurrencia.

Estos datos amplían la evidencia de escala del producto integrado; el ROI causal balanceado cercano al80% pertenece al caso1000 de115. No hay baseline nativa completa49pendientes a10000 para reclamar un porcentaje de mejora allí. El corto limpio20RPS sigue FAIL; B07/B08 y beta continúan abiertos. El siguiente testigo necesario es la regresión funcional amplia de117, separada de capacidad.
