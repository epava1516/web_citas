# Censo dirty: medición limpia corta conservada como FAIL

Run `20261016-003849-cc3fd173`, SHA `6daa17049fe45779d63de391a98a284725963246`, **1FAIL182,88s**. [Recibo terminal](cr09-dirty-census-clean-terminal-20261016.json). Cuatro procesos sync, kernel native-sealed registrado y obligatorio antes de recursos; mismo escenario10ksintéticos/20rps60s/1subida/Celery2+Beat, generador congelado y cuotas propias anteriores. Sin perfiladores ni observadores deworkers. Fuentes exactas al terminar.

| p95 HTTP s,400peticiones porcaso | Referencia222515 | Censo003849 |
| --- | ---: | ---: |
| Listado | 1,267948966 | 0,946483378 |
| Búsqueda | 1,232933370 | 0,966422417 |
| Ficha | 1,149303145 | 0,803473564 |
| Mezcla1200 | 1,218890056 | 0,904873942 |

Reducción observada demezcla25,762%; una ejecución porversión, no causalidad ni reproducibilidad demostradas. Sigue incumpliendo<0,8s por0,104873942s. MantenerFAIL; no repetirciego ni iniciar900s. La mejoraaislada yparidad justifican mantener elcambio, pero noaceptarcapacidad.

1200programadas/emitidas/completas,0errores/timeouts/omisiones/pendientes finales,subida302. Generadorválido:p951,824ms,p992,745ms,máximo28,913ms. p50HTTP0,220200s,p900,511262s,p991,214725s. Gunicornserviciop950,303094s noequivalealatenciaHTTP ni separacola.

| Cohorte por emisión | Casos | p95 HTTP s | >=0,8s |
| --- | ---: | ---: | ---: |
| 0–5s | 100 | 1,242400969 | 71 |
| 5–10s | 100 | 0,636066987 | 0 |
| 10–15s | 100 | 0,279104561 | 0 |
| 15–60s | 900 | 0,375783078 | 0 |

La cola se concentra otra vez enarranque. No sustituir poblacióncompleta por cohorteestable. No atribuir alportátil/hardware ni proyectar otrocandidato sincontrastarlo. Siguiente investigación separada debe comprobar demanda restante deocupantesiniciales conesta fuente:el análisisoffline previo ylosplanes existentes orientan unknown/población,pero nosonperfil de6daa170.

Limpiezaindependiente:controlador/pytesthijo/Celeryausentes,temporalretirado,contenedoresPG/Redispropiosausentes,unitMainPID0/ControlGroupvacío. Eltesttambién declaróGunicorn detenido;no se dispone aquídelmismo registroPIDporworkerqueendxinstrumentado. ElJSONheredapg_server_sharedincorrecto:eladaptadorusócontenedorespropioslimitados. Seconservaoriginalsinreescribirlo. Docsactualizadasposteriormente,nofuentesdurantemedición. CR09/N3abiertos.
