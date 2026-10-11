# MOD-08: contadores reales de CPU

Preflight 20261011-080958-6460fb0b: una prueba aprobada, sin fallos/errores/omisiones. 1156 hashes y retirada propia verificados independientemente.43 comprobaciones locales de contrato también pasan. Cuotas intactas; lectura añadida al mismo exec de memoria tras requests cronometrados.

| Servicio | Periodos limitados, anterior | Periodos limitados, preflight nuevo | Periodos observados | CPU acumulada (s) |
|---|---:|---:|---:|---:|
| pg | No disponible | 1 | 960 | 15.071938 |
| redis | No disponible | 49 | 1571 | 1.756194 |
| app | No disponible | 63 | 1127 | 94.905478 |
| objects | No disponible | 6 | 208 | 1.076348 |
| caddy | No disponible | 117 | 134 | 1.233556 |

Contadores acumulados desde arranque hasta recogida final. Preflight/setup sin workload objetivo: no p95, ni porcentaje de espera por request, ni causa demostrada de latencia. Próxima captura/use bajo carga para contrastar. Aceptación original2s/5s/doscasos/N3 sigue pendiente.
