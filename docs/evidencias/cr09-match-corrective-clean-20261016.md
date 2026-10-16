# Directorio tras corregir lectores Match: medición corta FAIL

Run020854-c2b568f1,SHAfca1af035289a255e4d38df03bed9106ecf0b832,**1FAIL184,69s**. Correctivac6951ab/migración0020 vigente. [Recibo terminal](cr09-match-corrective-clean-terminal-20261016.json). Mismo arnésVPS4sync,10000sintéticos,20rps60s,1subida,Celery2+Beat,generadorfreeze,cuotas propias ykernel native-sealed. Sinperfiladores,observadores deworkers niotrotrabajopropio. Imagenv3 previamenteconstruida/verificada porseparado.

| p95 HTTP s | Referencia003849 | Corregido020854 |
| --- | ---: | ---: |
| Listado400 | 0,946483378 | 1,188380264 |
| Búsqueda400 | 0,966422417 | 1,192133600 |
| Ficha400 | 0,803473564 | 1,081087531 |
| Mezcla1200 | 0,904873942 | 1,173553838 |
| ServicioGunicorn1200 | 0,303094 | 0,305278 |

La nueva ejecución resulta máslenta enHTTP, sin identificar causa exclusiva ni regresión causal de0020 desdeuna ejecución porversión. P95deHTTP yservicio son distribuciones distintas: no restarlos para calcular cola. La corrección se conserva por el defecto de exactitud reproducido; no se rebaja el umbral<0,8s ni se oculta el FAIL. No repetición limpia/900s después deeste fallo; siguiente diagnóstico separado debe acotar coste yocupación inicial.

| Cohorte por emisión | n | p95 referencia s | p95 corregido s | >=0,8s referencia/corregido |
| --- | ---: | ---: | ---: | ---: |
| 0–5s | 100 | 1,242400969 | 1,412958052 | 71/92 |
| 5–10s | 100 | 0,636066987 | 1,111202272 | 0/52 |
| 10–15s | 100 | 0,279104561 | 0,485325240 | 0/0 |
| 15–60s | 900 | 0,375783078 | 0,355471389 | 0/0 |

144lentas,todasemitidasprimeros10s. Eltramoestablemejor no sustituye alconjunto. PublicationSampler1Hz:referencia dirty1a0,304/1,303s,dirty0a2,303s;corregido dirty1a0,457s,dirty0a1,457s. No demuestra ventanaexacta niduración causal delretardo; no presupone que el nuevofanout sea el cuello exclusivo.

1200programadas/emitidas/completas,0errores/timeouts/omisiones/finalpendientes;1196completas/4pendientes alcierre60s,las4drenadasdentroplazo. Subida302. Generadorválidop951,997ms/p992,898ms/max8,156ms. Sólo falla latencia, no validez/transporte de datos: transport_verdict rawincluyeelSLOy diceFAIL, no contradecirlo con unaaceptación global.

Python3.12.15,Django5.2.17,Gunicorn23,PG17.11,kernelhostca3c3885…idéntico alreferente,fuente9cecbd34…. [Imagenv3](cr09-docker-native-v3-20261016.md) usa binario2caa578c…deGCC12,hostGCC11: ambas identidades registradas, no igualdadbinaria niperformanceDocker inferida. No diferencias delportátil atribuidas al código.

Fuentes congeladas iguales;controlador/pytest/Celery capturadosausentes,temporalretirado,PG/Redispropiosausentes,unidadMainPID0/ControlGroupvacío. Gunicornstop finalafirmado y cgroupvacío;sin inventarioposteriorindependientedePIDporworker. Rawpg_server_shared/limits sonleyendasheredadasincorrectas; eladaptadormuestra contenedorespropios limitados. Rawtrial_resource_stoppedregistradoantesdefinalstop; preservar juntoaindicadoresfinales ylimpiezaindependiente. Logs/resumen/JUnit/manifestenartifacts/local-ci/20261016-020854-c2b568f1/.

CR09/globalN3 y el contrato completo siguen abiertos. Sin repetición/ensayo especulativo ni aceptación por smoke de entrega.
