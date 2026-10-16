# Control A/A: estabilidad insuficiente para efectos pequeños

Run `20261016-063941-4a423442`, HEAD0e47c53 más instrumento/prerregistro congelados.1PASS131,75s,96requests DjangoClient con código idéntico enlabelsA/B,10kdatos sintéticosPG17.11realpropio/Python3.12.15/native-sealed ylímites habituales4CPUcontroller/PG1CPU. Criterio preregistrado10%diferencia simétrica entre medianas de4reads porlabel ycelda,3bloquesalternos×2rutas×2modos. No adopción producto niHTTPconcurrente/p95.

| Modalidad | Celdas dentro10% | DiferenciaAA máxima | Mediana conjunta descriptiva |
|---|---:|---:|---:|
|Conexión nueva porrequest|2/6|30,00%|346,26ms|
|Persistente tras6warmups porlabel|1/6|27,53%|199,73ms|

**INCONCLUSO para distinguir ahorros pequeños con este método**:9/12celdas excedentolerancia aunconigualcódigo. No es regresión de app ni evidencia de un hardwaredefectuoso. Las medianas entre modos no son efecto causal estimado: orden fijo de modos ypreparación diferentes. Colddatabaseconnection no equivale a proceso/CPUcachefrío.

Todoslos96cuerposSHA exactos/status200/no-store. FríoPIDdistintocadaread, calientePIDigualalwarmup entodaslas4reads,19sentenciaspreparadas porcada12brazoscalientes. CountsSQL/GCcollections sintextos/paramsnipolíticamodificada. Fuentecongeladaidéntica, runner/hijo/temporales/contenedores propiosausentesindependientemente; unidadinactive/MainPID0. ReciboJSONadjunto; muestrascompletas/preparación/comparaciones en artifacts/local-ci/20261016-063941-4a423442/request-aa-results.json.

Siguiente:no rescatar variantesdescartadas ni lanzarotracargaFAIL. Atribuir variabilidad antesdeafirmarahorrosmarginales, conmetadatos/ventanasigualadas ypreguntaconcreta; no tuneglobal ni cambiocuotas. Conservarelúltimoclean1,013029795FAIL ycriteriosCR09/N3.

## Contraste de experiencias comunitarias

[Clubhouse](https://blog.clubhouse.com/reining-in-the-thundering-herd-with-django-and-gunicorn/) describió muchosworkersociosos ymejoródistribución conHAProxy/backendsindividuales; es relato primario del equipo, a96vCPU/144workers. En nuestra captura031208, clasificaciónporinicioWSGI15–60s:214/231/238/222requests y43,016/43,120/43,458/43,455s dewallcompleto porworker. Son sumas porcohorte de inicio, puedenextenderfuera deventana; no ocupaciónclippedexacta. No aparece aquí aquel desbalance conmayoríadeworkersociosos. Nojustificacopiararquitectura niadoptarHAProxy.

[Gunicorn3407](https://github.com/benoitc/gunicorn/issues/3407): cerrado comoduplicado, comentarista confirma reproducción23; cerradonoimplicacorregidoenversióninstalada. [RelatoGIL/GC](https://www.reddit.com/r/django/comments/1wsfgc4/found_our_django_app_was_losing_2_seconds_per/) es testimonioautorreferido noverificadoindependiente,noevidenciaparagc.freezeaquí.

Preferenciaexpresausuario: incluirStackOverfloweninvestigacióncomunitaria. [Persistencia Django65906456](https://stackoverflow.com/questions/65906456/persistent-connections-in-django) y[41816570](https://stackoverflow.com/questions/41816570/how-does-conn-max-age-work-in-django) documentan confusiónporservidordesarrollo/hilos: útilparaverificarmétodo,no demostracióncausanuestroGunicorn. [Latencia51832478](https://stackoverflow.com/questions/51832478/nginx-gunicorn-django-high-latency) trae síntomasyconsejos, sinconfirmaciónrevisadadeunacuraaplicable; no copiarworkers/timeouts. Distinguirrespuestaaceptada, sugerencia yconfirmaciónautorreproducción. Sin publicarconsultasnimensajesexternos.
