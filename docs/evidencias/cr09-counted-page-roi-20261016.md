# Recuento y primera página con ventana — descartado

Ejecución110813-05a92cd3, fuenteaf07872:1PASS196,88s por paridad/compleción del diagnóstico,288lecturas medidas y108warm; **eligible_for_integration=false**. Fuentes y limpieza comprobadas independientemente. [Recibo](cr09-counted-page-roi-20261016.json).

| Caso | Media actual A/B | Media prototipo | Cambio wall | Cambio CPU |
|---|---:|---:|---:|---:|
| /es/ | 216.314ms | 221.481ms | +2.39% | +3.81% |
| /en/?q=synthetic | 271.824ms | 268.598ms | -1.19% | +1.55% |

A/Aestable en wall/CPU ambas rutas. Sólo1/3bloques de no-regresiónwall por ruta; SQL44→43 ambas. No cumple ahorro>=10%ambasrutas, ni consistencia mínima2/3. No rebajar umbrales después de medir. Se conserva el prototipo sólo como evidencia opt-in, no integración ni nueva carga limpia.

La ventana elimina unSELECT pero obliga a materializar el recuento en la consulta de página. Este experimento prueba el efecto total observado; no atribuye el resultado a un nodo sin plan comparativo. El diagnóstico previo de planes secuenciales no era una medición de ahorro del cambio. No insistir con variantes especulativas.

P95limpio vigente:primerPASS0,675688141s/repeticiónFAIL0,880356520s. No cumplimiento reproducible,900s bloqueado. MatrizTCPactual/N3/CR09integral pendientes. Las40comparaciones previas (incluyen población0/1/79/80) no equivalen a N2completa ni a aceptación del algoritmo.

Siguiente análisis: reconciliar el trabajo frío todavía atribuible a cada worker y los límites de preparación estática frente al diagnóstico de ciclo de vida rechazado. Usar los registros existentes antes de otro cambio; no reabrir planes genéricos, uniones o ventanas descartadas sin evidencia distinta.
