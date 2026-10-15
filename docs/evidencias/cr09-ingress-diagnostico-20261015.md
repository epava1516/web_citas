# Estado descompuesto: espera, degradación de proyección y trabajo de medios

Run `20261015-212543-8e32a890`, SHA0656357, **FAIL185.42s instrumentado**. [Terminal, comprobaciones y agregados](cr09-ingress-diagnostico-terminal-20261015.json). Producto apps/config idéntico a392c2c8; última carga limpia continúa FAIL0.919814s. El p95 instrumentado0.802719325s no es mejora/regresión comparable al limpio. Mismos límites/20rps60s/10k/4sync/Celery2+Beat/subida; hook ingress sin importar handlers ni envolver validación/render, sí SQL/GC y contadores cgroup1Hz propios. Overhead/heap marginal de observadores no cuantificados causalmente.

1200IDs dinámicos emparejados uno a uno entre cliente, WSGI y servicio Gunicorn; todos200, cero errores/omisiones/timeouts, subida302. Cero errores de parseo de eventos/servicio; cuatro workers con313/296/271/320 peticiones. Todos ya reciben trabajo en los primeros0.102s. Fuentes congeladas idénticas,10PIDs propios ausentes, temporal/PG/Redis retirados, unidad MainPID0/ControlGroup vacío. No datos/servicios normales.

|Media de las mismas peticiones por emisión|0–5s,100|15–60s,900|
|---|---:|---:|
|HTTP completo|839.46ms|244.53ms|
|Emisión→entradaWSGI|622.94ms|55.00ms|
|SpanWSGI observado|216.77ms|189.74ms|
|CPUthread dentro del span|112.87ms|106.74ms|
|SQLwall inclusivo|93.78ms|73.13ms|
|CPUthread clienteSQL inclusiva|8.46ms|7.24ms|
|GCwall solapado|10.87ms|8.20ms|

SQL/GC no son particiones independientes: se solapan con WSGI y entre sí. SpanWSGI termina al cerrar la respuesta, después de send/accesslog; la recepción puede preceder ese cierre. Residuo posterior medio≈−0.2–0.4ms y mínimo−15.28ms,1116casos negativos, no corregidos ni etiquetados como reloj roto. Identidad temporal comprobada usando las marcas de entrada/fin, no sumando percentiles. Emisión→WSGI contiene cliente/TCP/parseo/scheduling/admisión: no equivale exactamente a cola de socket.

Las62peticiones>=0.8s se emitieron0–5s. MediaHTTP956.87ms, previaWSGI714.16ms, spanWSGI242.98ms. El98.5105% del intervalo previo acumulado de esas62 coincide con cuatro spansWSGI activos, integrando solapamientos de1200dinámicas+subida; no prueba ocupación exclusiva de CPU, pero descarta que la espera sea principalmente con workers observados libres. Ningún worker faltaba durante todo el arranque dinámico.

|Cgroup propio, CPU ejecutada media en cores|0–5s,5muestras|15–60s,44muestras|
|---|---:|---:|
|PostgreSQL, afinidad a1CPU|0.92324|0.46928|
|Controller completo, afinidad4CPU|2.30853|2.18473|

PostgreSQL0throttled_periods en ambos intervalos observados; no atribuir el tiempo a cuota temporal. Controller incluye generador, workers, Celery y observadores. No equivale a CPU exclusiva de la app ni prueba de techo hardware general.

## Interacción que faltaba relacionar

La tarea real process_blob se ejecuta desde t0.352 hasta9.077:8.725s wall,0.599s CPUthread. La subida HTTP termina t0.357s, por tanto subida aceptada y procesamiento de fondo son tiempos distintos.

|Refresco real de publicación|Inicio relativo|Fin relativo|Resultado|
|---|---:|---:|---:|
|Primer refresco|0.341s|0.858s|1publicación|
|Refresco siguiente|0.862s|1.042s|0|
|Cambio de blob listo|1.213s|1.790s|1|
|Comparación de fotos terminada|9.078s|9.491s|1|

Muestreo dirty:0antes dearranque,1a0.265s y1.266s,0a2.265s; vuelve1a9.266s y0a10.265s. El origen de las marcas concuerda con publicación y ejecución reales de esas tareas; resolución1Hz no mide todos los flancos exactos.

El código `complete = not dirty and all_state_current(...)` desactiva la proyección compacta ante cualquier dirty. Se conserva validación nativa de los desconocidos; **no revalida nativamente todos los10k**, pero conteo/selección usa la población SQL general en lugar de la proyección. Se observan callers de esa ruta en d-3/6/7/8/9/15/18/19/20 al inicio y d-182/183/186/187 alrededor de9s. Ejemplo d-3: WSGI0.691s ySQLwall0.513s; d-8:0.659/0.383s. No se infiere ruta sólo de HTTP200: se contrasta rama y origen SQL. No basta esta correlación para repartir causalmente toda la espera entre trabajo de fondo y fallback.

## Aislamiento del proceso de medios

[Probe real de process(blob) en PostgreSQL propio](cr09-media-process-cpu-terminal-20261015.json), run213605-007f9523: **1PASS91.26s**. Se ejecuta función real directamente; no se presenta como ejecución Celery/HTTP ni capacidad. Modelo/señales preparatorias sólo publican en broker propio sin worker consumidor. Bytes sintéticos del mismo seed782134. Medición de16consultas con CPU del backend identificado/validado por PIDnamespace/cgroup/startticks, resolución100Hz. Fuentes/limpieza independientes. Preparación/caches y ausencia de concurrencia difieren del task real; no presentar diferencia de tiempos como mejora de código.

|Tramo del proceso aislado|Wall|CPU Python|CPU PostgreSQL medida|
|---|---:|---:|---:|
|process(blob) completo|4.716137s|0.412329s|Sin intervalo único de backend|
|SELECT más costoso|4.181155s|0.002948s|3.890s|
|16consultas, CPUbackend acumulada|—|—|3.980s|

El SELECT principal concentra≈88.7% del wall de process y97.7% del CPUbackend acumulado observado. Su fingerprint esbedc4d09fc64d364f4b1a39d0cf074f25bea8167786be468f5371aa8e4d42329. Plan posterior estimado: Unique/IncrementalSort/MergeJoin con selección de fotos yBlob; costo1899.28, no JIT. EXPLAIN fue sinANALYZE después del proceso: no acredita loops ejecutados ni descarta absolutamente otro plan previo; **no justifica forzar jitoff**. Costo de plan no son milisegundos.

El selector actual hace Blob(ready) JOIN Photo candidata y DISTINCT de filas completas deBlob. Candidata de investigación: Blob(ready) con EXISTS de una Photo candidata correlacionada porblob_id, conservando todas las exclusiones originales de retiradas/histórico/rights-stage/rectification_upload y exclusión del blob actual. Equivalencia de conjunto: un Blob se selecciona si existe al menos una foto admisible, no por el número de fotos. Sin índices nuevos, cambios de políticaPG, checks omitidos ni caché entre requests. No cambiar record_match ni sus bloqueos/guardas. Consulta primaria: [Django5.2 EXISTS](https://docs.djangoproject.com/en/5.2/ref/models/expressions/#exists-subqueries).

Siguiente contraste finito, ya separado de cargas: tres bloques alternos del selector original yEXISTS, columnas completas eiterator original, comparación de todo el contenido porhash ordenado, CPUbackend ywall. No medir sólo IDs porque eso cambiaría DISTINCT y ocultaría su coste real. Si no hay beneficio/igualdad, descartar. Si la hay, revisar escenarios negativos/lifecycle antes de integrar y medir HTTP. No reactivarFAISS/mypyc/Cython ni ampliarhardware para este SQL sin esa evidencia.

## Contraste terminado: selector existencial

Run213949-b87873e3, **1PASS94.26s**, [recibo](cr09-media-candidates-cpu-terminal-20261015.json):10002fotos,5blobs totales incluido el excluido; ambos selectores devuelven los mismos4blobs. El fingerprint del SQL de referencia coincide exactamente con el SELECT más costoso capturado en process(blob). Tres tandas alternas, columnas completas ymismaiterator, hash de todo el contenido idéntico en las seis ejecuciones. Sin cambios JIT/sesión, fuente/limpieza independientes.

|Media del selector aislado,3tandas|JOIN+DISTINCT actual|EXISTS candidata|
|---|---:|---:|
|Wall|2.608609s|0.014625s|
|CPU Python|0.008026s|0.006042s|
|CPUbackend,contador100Hz|2.480s|0ticks medibles|
|Blobs devueltos por tanda|4|4|

Rangoswall2.479–2.852s frente0.0099–0.0216s: reducción media99.44% **de este selector**, no del request ni del proceso completo. Cero ticks no significa CPUcero ni una cota exacta de10ms para la sumauser+system. La equivalencia en este dataset no sustituye todos los escenarios de exclusión/race. Consulta candidata implementada localmente en detect_matches, conservando objeto candidates/filtros/record_match/streaming y exclusión deblobactual. En curso controles de fotos, supresión, uploads de rectificación y carreras de reutilización antes de integrar/medir HTTP.

La evidencia sugiere priorizar esta corrección acotada del selector de medios antes de introducir una proyección híbrida para dirty: la segunda alternativa añade complejidad y podría dejar de ser necesaria si desaparece la carga SQL de fondo. Sigue sin modificarse la política conservadora de invalidación. FAISS no resuelve el join de10k referencias que devuelve4blobs en este escenario; no confundir número dePhoto con número de bytes/blobs distintos. Se conserva su ponderación futura para otros perfiles de duplicados.

Controles de la candidata integrada localmente: run214348-3c6beca6 **19PASS188.93s**, [recibo](cr09-media-selector-controls-terminal-20261015.json). Incluye pipeline/foto global yrecorte, eliminación física/resurrección, rectificación privada/duplicados/staging y carreras reales PostgreSQL de reutilización. Fuentes/limpieza/unidadterminal verificadas. Único cambio de app: selector deblobs usa EXISTS; conserva todos los filtros,streaming yrecord_match. Se procede a un corto limpio único con las condiciones anteriores; repetir sólo siPASS. Sin atribuir micro99.44% alHTTP, sin aceptar CR09/N3 ni modificar cuotas/políticas.
