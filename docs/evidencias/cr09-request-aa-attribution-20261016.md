# Atribución separada de variabilidad A/A

Run064636-34211373,HEADfd83979 másinstrumento/prerregistro.1PASS136,04s/96reads exactos. Reutiliza cuerpoAA sincopiarlo, mismoscupos4CPUcontroller/PG1 ydatos10kpropios. ObservaciónejecuciónSQLwall/GCcallbackwallCPU/rusageTHREAD, sinSQLtexto/params niGCpolicychange. Testselecciona96medidas separadasdewarmups,0GCinacabado/callbackretirado. NoHTTPconcurrente/p95/aceptación.

| Media porrequest | Nuevaconexión | Persistente6warmups |
|---|---:|---:|
|Wallms|384,955|215,577|
|CPUhiloms|193,720|135,963|
|SQLwallinclusivoms|179,411|76,377|
|GCwallms|18,855|18,211|
|GCCPUms|18,385|17,649|
|Cambioscontextovoluntarios|91,79|68,77|
|Cambioscontextoinvoluntarios|29,75|19,79|

Gruposposthoc dentrodelmodo, mezclanrutas/bloques; asociación,noexperimento causal:

| Grupo | Wallms | CPUms | SQLinclusivoms | GCwallms |
|---|---:|---:|---:|---:|
|Nuevaconexión12rápidas|311,37|150,78|149,81|3,34|
|Nuevaconexión12lentas|476,59|251,47|219,11|63,43|
|Persistente12rápidas|169,98|108,16|60,05|3,11|
|Persistente12lentas|288,55|195,34|88,51|63,71|

GCvaría materialmente ycoincide conmayorCPU/latencia. Noexplicatodala diferencia,nodemuestraGCúnicocuelloSLO nioptimizaciónaceptable. SQL/GC/CPUsolapan,no sumarlos; númerosSQLincluyenespera/driverplanificación,noCPUPG. Contextswitches no equivalen a presiónCPU atribuida ni retrasosmedidos. Instrumentaciónperturba; nocausalidadfrenteAAanterior.

Siguienteatribuirgeneración/lifetime/ciclosfuentesdeobjetosantesdeconsiderargc.freeze/deshabilitarGC. Corregirciclosdemostrados puede ofrecerbeneficiomantenible; noaplicarajusteglobalsinseguridad/recursos/pruebascarga. LoscallbacksobservanGCdelprocesoactual; nopruebanlaspausasdelHTTPconcurrenteanterior.

Intentoprevio064520-d1991b7e fallóRuffI001antespytest,originalcopiadoantesfix/importsordenadosúnicocambio; frozen/cleanupverificados yfallopreservado. Enactualfuentecongeladaidéntica/runnerhijotemporalcontenedoresausentesindependientemente/unidadinactivecgroupvacío. ReciboJSONadjuntocon96muestrasemparejadas,artefactosrun. Sinprod/Claude/proveedores/mediciónp95nueva;últimoclean1,013029795FAIL/CR09N3goalenterosabiertos.
