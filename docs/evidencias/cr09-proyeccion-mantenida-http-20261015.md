# Proyección mantenida: primera carga limpia

Run `20261015-160640-172e26bf`, SHA `f93c183`:FAIL184.60s. Misma carga4sync/20rps60s/10k sintéticos/worker yBeat propios/una subida/generador congelado; sin perfiladores/observadores/trackerPG. Fuentes y limpieza verificadas independientemente; PIDraíz/pytest/Celery,temporales yPG/Redis ausentes, unidad/cgroup terminal sin descendientes. Corrección de supresión incluida, sin modificar cuota ni criterio.

| Métrica | Anterior | Candidata |
|---|---:|---:|
| p95 completo(s) | 5.004965654108673 | 1.3617929541505873 |
| p50 completo(s) | 3.8767454088665545 | 0.2835297118872404 |
| Pendientes al60s | 97 | 4 |
| Completadas finales | 1200 | 1200 |
| Errores/timeouts | 0 | 0 |
| ServicioGunicorn p95(s) | 0.406602 | 0.31365 |

| Caso p95(s),200peticiones/caso | Anterior | Candidata |
|---|---:|---:|
| es:listing | 4.966927 | 1.391529 |
| en:listing | 4.948853 | 1.396969 |
| es:search | 5.069563 | 1.393086 |
| en:search | 5.098360 | 1.412857 |
| es:detail | 4.854788 | 1.271050 |
| en:detail | 4.859124 | 1.328369 |

Mejora observada72.7912%, no causal/reproducida. Generador válido,1200completadas sin errores/timeouts/omisiones,subida302; ahora sólo falla latencia frente<0.8s, demás comprobaciones cortas pasan. Retener provisionalmente por evidencia funcional/CPU/carga, no aceptarCR09/N3 ni repetirFAIL o pasar15min. ServicioGunicorn excluye espera anterior y no sustituye latencia completa.

## Localización temporal desde los mismos datos

[Análisis](cr09-proyeccion-mantenida-cola-temporal-20261015.json), sin nueva carga ni cambio de código. Cohortes por emitted_at, todas las terminadas, nearest-rank:

| Intervalo de emisión | N | p95(s) | >=0.8s |
|---|---:|---:|---:|
|0–15s|300|1.478701|248|
|15–60s|900|0.556224|0|

Todas las248peticiones fuera de umbral se emitieron en primeros15s. Máximo posterior0.696318s. Esto localiza un transitorio; NO demuestra calentamiento SQL, subida,GC oCPU como causa ni capacidad sostenida/aceptación sólo del tramo final. La población contractual sigue incluyendo las1200iniciales. Próximo diagnóstico frío separado debe atribuirlo antes de intervenir; no cambiar warmup/carga para ocultarlo.

Metadato pg_server_shared y texto normalstack del resumen son estáticos heredados. Se conserva resumen original, corregido documentalmente frente a nombre/label/límites de instancias desechables propias del runner. No implica acceso a servicios normales. CeleryCPU observado aumenta165ticks agregados/100Hz duranteventana, sin atribución por tarea ni causalidad temporal desde esos dos cortes.
