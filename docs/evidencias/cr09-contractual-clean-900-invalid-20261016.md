# Contractual900: latencia observada favorable, generador inválido

[Recibo](cr09-contractual-clean-900-invalid-20261016.json). Ejecución152034-533fd7b3, fuente e7809dd.1FAIL1032,50s/unidad1: **INVALID**, única razón generator_delay_max. No convertir en PASS ni repetir automáticamente.

| Ensayo | p95observable | Validez |
|---|---:|---|
|Corto145039sinattach|0,738744505s|PASS;captura fallida preservada|
|Corto151456|0,720746481s|PASS|
|Contractual152034|0,351628515s|INVALIDgenerador|

18.000programadas/emitidas/exitosas,0errores/timeouts/noemitidas/pendientesfinales.15subidas correctas. Al cierre900s quedan2dinámicas y0subidas; todasfinalizadasenplazo. Generadorp951,768ms/p993,102ms, máximo113,546613ms frente≤100ms: d-2772programada138,6s/emitida138,713546613s, siguiente tambiénretrasada63,867079ms; tercera máxima22,731772ms. No omitir esaspeticionesni cambiarumbral. Cero intervalosdemoraemisión solapadosconGCregistrado; esto descarta ese solapamiento, no establece causadescheduling/host/red/otraactividad.

| Caso | Peticiones | p95observable segundos | Fallos |
|---|---:|---:|---:|
| /en/ | 3000 | 0.351859579 | 0 |
| /en/?q=synthetic | 3000 | 0.408902336 | 0 |
| /en/listing/e953864a-cd59-4acb-81dd-44ea0aa43b1d/ | 3000 | 0.217330064 | 0 |
| /es/ | 3000 | 0.367864253 | 0 |
| /es/?q=photography | 3000 | 0.383273675 | 0 |
| /es/listing/70289c7e-41dd-4c70-ad58-3b64d3eb672e/ | 3000 | 0.232897450 | 0 |

Percentiles porcaso calculados ended_at−emitted_at, mismos18000incluidoserrores/timeouts sihubiera; no scheduled_at. No extrapolaciónalhardware/cargadorni ahorrocausal por cambios: productoigualacortos. CuatroGunicornsync,workerBeatnormal,10k sintéticos,20rps900s,una subida/minuto. GCappnormal;preparaciónGCsólogenerador. Python3.12.15/dependenciascongeladas/kernel native-sealed,recibo nativo original preservado. Sinperfiladores/SQLobservers/renderwrappers.

Controlador4CPU3584MiB/PG1CPU1536MiB/Redis0,2CPU128MiB/swap0. Fuentesfrozen yrunner/hijoPIDstart_ticks/temporal/contenedoresausentes verificados independientemente. Unidadterminal1/MainPID0. Artefactoscompletosretenidos. No nuevaejecución900 niaceptaciónN3/CR09; diagnósticoseparadodelgenerador, sinrelajarcriteriosni cambiarrecursoscomo compensación.
