# Cliente sintético sin HTTP: comparación de construcción

| Constructor | Mediana wall | Mediana CPU hilo |
| --- | ---: | ---: |
| boto3 | 0.101383 s | 0.099833 s |
| botocore | 0.094788 s | 0.094089 s |

Nueve ensayos alternados, sin HTTP ni profiler. No equivalencia general ni latencia request. Diferencias de user-agent, hooks y métodos transfer. No se sustituye boto3: ahorro aproximado6,6ms/cliente insuficiente para el déficit actual. Modelos/loader mutables no compartidos entre sesiones.
