# Repetición del corto — objetivo no reproducido

La repetición `20261016-104826-a7511148`, fuente62b4d35, terminó FAIL en185,56s. Generador válido,1200completadas,0errores/timeouts/pendientes finales, subida conforme. p95global0,880356520s; el primer corto0,675688141s fue PASS. No se acredita reproducibilidad y queda bloqueado el ensayo900s. [Recibo completo](cr09-detail-repro-20261016.json).

| Caso | Primer corto (s) | Repetición (s) |
|---|---:|---:|
| Global | 0.675688 | 0.880357 |
| Listado ES | 0.699499 | 0.860301 |
| Listado EN | 0.688690 | 0.904956 |
| Búsqueda ES | 0.675688 | 0.973179 |
| Búsqueda EN | 0.813765 | 0.914257 |
| Detalle ES | 0.607682 | 0.726351 |
| Detalle EN | 0.575703 | 0.768361 |

Corrección del desglose inicial: las rutas se recalculan como ended_at−emitted_at, igual que benchmark_accounting; el primer desglose usaba scheduled_at e incluía demora del generador. Sus valores originales quedan conservados en JSON. Global y veredictos nunca cambiaron.

| Llegadas | Peticiones | p95 repetición (s) | ≥0,8s |
|---|---:|---:|---:|
| 0–5s | 100 | 1.152038 | 73 |
| 5–10s | 100 | 0.646084 | 0 |
| 10–15s | 100 | 0.355741 | 0 |
| 15–60s | 900 | 0.325356 | 0 |

Fuentes, PID/start_ticks, temporal y contenedores propios comprobados independientemente. Se conserva FAIL, sin tercer intento limpio ni900. El16,32% de reducción observada frente al producto anterior1,052089655s no basta para aceptar el objetivo.

Diagnóstico offline separado: [2400IDs de ambas ejecuciones emparejados con servicio](cr09-detail-repro-offline-20261016.json). En15–60s, medias HTTP0,186030→0,187525s y servicio0,171666→0,171935s; el cambio se concentra al inicio. En1–2s mediaHTTP0,836574→1,080541s y servicio0,226870→0,242772s; residuo porID0,609704→0,837769s. No se restan percentiles ni se identifica el residuo con cola exacta. No hay causa única demostrada. La cohorte inicial exige estudiar trabajo frío/admisión sin excluirla del objetivo ni adoptar calentamiento previamente rechazado.

La matriz TCP de seis controles sigue pendiente de aplicabilidad actual; su ejecución y el ensayo largo no están iniciados. CR09/N3 y fases posteriores continúan abiertos.
