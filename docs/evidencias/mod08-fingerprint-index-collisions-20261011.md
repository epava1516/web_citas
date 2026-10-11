# Índice HMAC: colisiones tardías y saturación

PostgreSQL real28PASS/0fallos/errores/skips106.914s;1155hashes verificados, incluyendo4archivos exactos del commit82d088c, y limpieza independiente. Una ronda warmup por modo,9parejas alternadas,8llamadas por muestra. No mejora del request acreditada.

| Tipo | Tamaño | Escenario | CPU referencia (µs) | CPU candidata (µs) | Variación |
|---|---:|---|---:|---:|---:|
| str | 128 | same-object | 49.48 | 49.67 | +0.38% |
| str | 128 | fresh-hit | 49.24 | 50.47 | +2.49% |
| str | 128 | miss | 99.01 | 99.43 | +0.42% |
| str | 128 | collision | 97.80 | 98.62 | +0.84% |
| str | 128 | late-collision | 96.68 | 97.96 | +1.32% |
| str | 4097 | same-object | 60.09 | 60.38 | +0.48% |
| str | 4097 | fresh-hit | 70.17 | 71.15 | +1.40% |
| str | 4097 | miss | 198.69 | 199.05 | +0.18% |
| str | 4097 | collision | 199.45 | 202.25 | +1.40% |
| str | 4097 | late-collision | 199.35 | 200.88 | +0.77% |
| str | 65537 | same-object | 245.91 | 239.49 | -2.61% |
| str | 65537 | fresh-hit | 436.32 | 272.25 | -37.60% |
| str | 65537 | miss | 1736.17 | 1604.64 | -7.58% |
| str | 65537 | collision | 1724.55 | 1658.90 | -3.81% |
| str | 65537 | late-collision | 1708.25 | 1774.88 | +3.90% |
| str | 65537 | saturated-bucket | 1752.63 | 5075.34 | +189.58% |
| str | 1048576 | same-object | 3167.12 | 2890.69 | -8.73% |
| str | 1048576 | fresh-hit | 6582.02 | 3824.00 | -41.90% |
| str | 1048576 | miss | 27229.05 | 24222.18 | -11.04% |
| str | 1048576 | collision | 25677.43 | 23957.13 | -6.70% |
| str | 1048576 | late-collision | 25289.55 | 25635.04 | +1.37% |
| str | 1048576 | saturated-bucket | 26064.27 | 30730.59 | +17.90% |
| bytes | 128 | same-object | 44.65 | 45.59 | +2.11% |
| bytes | 128 | fresh-hit | 44.97 | 46.16 | +2.65% |
| bytes | 128 | miss | 91.18 | 91.53 | +0.39% |
| bytes | 128 | collision | 90.58 | 91.66 | +1.20% |
| bytes | 128 | late-collision | 90.00 | 91.26 | +1.40% |
| bytes | 4097 | same-object | 56.68 | 58.17 | +2.63% |
| bytes | 4097 | fresh-hit | 66.60 | 67.53 | +1.41% |
| bytes | 4097 | miss | 185.77 | 187.15 | +0.75% |
| bytes | 4097 | collision | 185.17 | 185.35 | +0.09% |
| bytes | 4097 | late-collision | 185.23 | 185.69 | +0.25% |
| bytes | 65537 | same-object | 226.38 | 224.15 | -0.99% |
| bytes | 65537 | fresh-hit | 384.33 | 257.94 | -32.89% |
| bytes | 65537 | miss | 1555.01 | 1437.06 | -7.59% |
| bytes | 65537 | collision | 1557.35 | 1437.82 | -7.67% |
| bytes | 65537 | late-collision | 1542.10 | 1537.30 | -0.31% |
| bytes | 65537 | saturated-bucket | 1546.72 | 4436.13 | +186.81% |
| bytes | 1048576 | same-object | 2953.29 | 2682.16 | -9.18% |
| bytes | 1048576 | fresh-hit | 5620.87 | 3261.09 | -41.98% |
| bytes | 1048576 | miss | 23450.46 | 21139.82 | -9.85% |
| bytes | 1048576 | collision | 23457.54 | 21769.91 | -7.19% |
| bytes | 1048576 | late-collision | 23572.17 | 23121.11 | -1.91% |
| bytes | 1048576 | saturated-bucket | 23638.11 | 59975.85 | +153.73% |

Umbral64KiB evita buckets para4097. Fresh-hit1MiB mantiene~42% ahorro CPU por8llamadas. Sin embargo saturación provoca+189.58% str65537,+186.81% bytes65537,+153.73% bytes1MiB. NO integrar este estado. Promoción adaptativa a diccionario exacto en segunda colisión retenida pendiente de gate. Caps/secretofresh/igualdadtotal permanecen obligatorios.
