# CR09: ingreso con preparación estática verificada

Run031208-ec0fd4c3,SHA9c9dead,1FAIL190,62s. FlagCLIprepare-static transmitido explícito,4static_ready de4PIDantesorigen. 1200inicio/finWSGIdistintos coincidencon1200dynamicemitidos/successful,0errores/pending/timeouts/omisiones,invalid_reasons vacío. Python3.12.15/PG17.11/nativeca3c,4sync/controlador4CPU/PG1CPU y límites conservados. ObservadorSQL/GCactivo,no clean/noaceptación.

| Medición | p95 total s |
|---|---:|
| Últimoclean025813|1,013029795|
| Diagnósticohookverificado031208|1,101181666|
| Objetivo|<0,800|

Diferenteinstrumentación,no causalidad/mejora/regresión entrecolumnas. Captura0307230,929214190NOteníahookyno validaba intención;falloprevio conservado.

| Cohorte | HTTP media ms | Emisión→WSGI media ms | WSGI media ms | CPUhilo media ms | SQLinclusive media ms |
|---|---:|---:|---:|---:|---:|
|0–5s|1060,180|829,518|229,978|107,435|110,171|
|5–10s|810,071|624,982|184,378|98,336|76,498|
|10–15s|521,154|328,910|191,699|97,701|78,209|
|15–60s|409,695|217,730|191,256|100,368|78,633|

SQL/GCsolapados,diferencias no fasesexclusivas. Emisión→WSGI incluyecliente/TCP/scheduling/admisión,no medida exactacola kernel. Ocupación observada4workerssimultáneos:4,842753s/4,932289s/4,917746s/38,789937s respectivamente. Intersección sumada porrequest entre suesperapreWSGI e intervaloscon4ocupados:98,710%/98,588%/98,173%/98,361%. Incluyeupload/preludios observados;sin actividad fueraWSGI,intervalos calculados corteWSGIstart/end. Asociaciónfuerte deesperaconocupación,no prueba exclusivacausal. La preparación no elimina el problema deadmisión.

PrimerasdinámicasWSGIporPID:552752d-1236,248ms/552775d-2251,875ms/552797d-9797,121ms(SQL525,627ms)/552799d-0237,108ms. UploadHTTP556,684ms. NoHTTPrepeat/900s. Siguiente analizarcuálesconsultasytrabajoinclusivo mantienenlosworkersocupados;no barridociego deworkers niquitarcontroles.

Datos load-summary-parsed.json/cohorts-parsed.json/benchmark-samples.json/worker-events-raw en artifacts/local-ci/20261016-031208-ec0fd4c3. Fuentecongeladaigual;runner/hijo/temp/contenedoresausentes;unidadfailed/MainPID0/ControlGroupvacío;finalstopGunicorn/worker/beatTrue yRedisvacío. Sinproducción/datosreales/proveedores/Claude,consumopreviointacto. ImagenDockerhookpendiente,CR09/N3/contratoenterosabiertos.
