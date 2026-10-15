# Lecturas públicas preparadas: carga limpia

Run `20261015-145835-6830fbfc`, SHA `9e54bb7`:FAIL190.36s. Misma carga corta4sync,20rps60s,10k sintéticos,worker/Beat propios,una subida; generador congelado antes de llegadas,sin perfiladores/observadores/estadísticasPG. Fuentes y limpieza independiente verificadas, incluido cgroup de unidad terminal sin descendientes y PIDraíz/pytest/Celery,temporales,PG/Redis ausentes.

| Métrica | Anterior | Candidata |
|---|---:|---:|
| p95 completo(s) | 7.423942404799163 | 5.004965654108673 |
| p50 completo(s) | 4.764016657136381 | 3.8767454088665545 |
| Pendientes al60s | 140 | 97 |
| Completadas finales | 1200 | 1200 |
| Errores/timeouts | 0 | 0 |
| ServicioGunicorn p95(s) | 0.410476 | 0.406602 |

| Caso p95(s),200peticiones/caso | Anterior | Candidata |
|---|---:|---:|
| es:listing | 7.367184 | 4.966927 |
| en:listing | 7.340186 | 4.948853 |
| es:search | 7.422768 | 5.069563 |
| en:search | 7.501457 | 5.098360 |
| es:detail | 7.297851 | 4.854788 |
| en:detail | 7.271279 | 4.859124 |

Reducción observada32.5835%, sin causalidad/reproducibilidad demostradas. Generador válido,1200completadas sin errores/timeouts/omisiones,subida302. Pendientes97y p95>0.8s mantienenFAIL; no repetir,15min ni N3. Retención provisional por9controles específicos+69ampliados+11privacidad y observación favorable, no suma como aceptación integral. Próximo diagnóstico separado antes de otra intervención.

Corrección de metadatos: `resources.pg_server_shared=true` y texto sobre stack normal son etiquetas estáticas heredadas del instrumento, no propiedad observada. runner.json y adaptador identifican la instancia desechable propia por nombre/etiqueta y límites; limpieza verificada independientemente. No hubo acceso a PostgreSQL productivo/normal en esta prueba. Se conserva el resumen original sin reescribirlo como evidencia de otra topología. ServicioGunicorn mide sólo servicio de filas completadas, no cola anterior ni latencia completa.
