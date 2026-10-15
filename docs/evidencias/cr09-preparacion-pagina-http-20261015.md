# Preparación de página: carga limpia integrada

Run `20261015-142404-dd21a941`, SHA `82289ea9eba44ecedc8cd6607ef48619ba634ae2`: FAIL, pytest189.83s. Una carga corta limpia, límites propios intactos,4sync,20rps60s,10k sintéticos,worker/Beat normales, una subida, generador congelado antes de llegadas; sin perfiladores,observadores ni trackerPG. Fuentes y limpieza verificadas independientemente, unidad/cgroup terminal sin descendientes, PIDraíz/pytest/Celery ausentes,temporales yPG/Redis ausentes.

| Métrica | Anterior | Candidata |
|---|---:|---:|
| p95 completo(s) | 16.572803906165063 | 7.423942404799163 |
| p50 completo(s) | 9.951848499942571 | 4.764016657136381 |
| Pendientes al60s | 280 | 140 |
| Completadas finales | 1200 | 1200 |
| Errores/timeouts | 0 | 0 |
| ServicioGunicorn p95(s) | 0.474938 | 0.410476 |

| Caso p95(s),200peticiones cadauno | Anterior | Candidata |
|---|---:|---:|
| es:listing | 16.519808 | 7.367184 |
| en:listing | 16.468016 | 7.340186 |
| es:search | 16.598714 | 7.422768 |
| en:search | 16.771010 | 7.501457 |
| es:detail | 16.413698 | 7.297851 |
| en:detail | 16.386960 | 7.271279 |

Reducción observada55.2041%, no causal ni reproducida. Sin errores/timeouts/omisiones, subida302; la cola sigue creciendo y p95 excede<0.8s. ServicioGunicorn excluye cola anterior y no sustituye latencia completa. Candidata retenida provisionalmente por exactitud68PASS y evidenciaCPU/carga; no repetirFAIL ni pasar15min/N3. Próximo diagnóstico separado debe resolver el coste restante antes de otra intervención. No se cambian cuotas/concurrencia/criterios. El diagnósticoSQL antiguo sigue útil estructuralmente pero no atribuye CPU actual a sus duraciones.
