# Candidata índice HMAC: primera medición

26PASS/0errores/fallos/skips,91.589s en PostgreSQL real.1155 hashes y limpieza independientes. Una ronda warmup y9parejas alternadas por escenario,8 llamadas por muestra con HMAC nativo real. No representa latencia del request.

| Tipo | Tamaño | Escenario | CPU anterior (µs) | CPU candidata (µs) | Variación |
|---|---:|---|---:|---:|---:|
| str | 128 | same-object | 49.01 | 49.87 | +1.76% |
| str | 128 | fresh-hit | 48.44 | 49.22 | +1.61% |
| str | 128 | miss | 99.26 | 100.88 | +1.63% |
| str | 128 | collision | 101.08 | 101.52 | +0.44% |
| str | 4097 | same-object | 64.59 | 68.68 | +6.33% |
| str | 4097 | fresh-hit | 71.25 | 72.09 | +1.17% |
| str | 4097 | miss | 207.15 | 207.72 | +0.27% |
| str | 4097 | collision | 205.39 | 225.31 | +9.70% |
| str | 1048576 | same-object | 3263.49 | 2969.22 | -9.02% |
| str | 1048576 | fresh-hit | 5732.21 | 3327.83 | -41.95% |
| str | 1048576 | miss | 24541.32 | 24256.92 | -1.16% |
| str | 1048576 | collision | 25712.63 | 23669.23 | -7.95% |
| bytes | 128 | same-object | 45.36 | 45.68 | +0.72% |
| bytes | 128 | fresh-hit | 45.79 | 47.75 | +4.27% |
| bytes | 128 | miss | 91.86 | 93.70 | +2.01% |
| bytes | 128 | collision | 92.38 | 94.56 | +2.37% |
| bytes | 4097 | same-object | 56.78 | 64.83 | +14.18% |
| bytes | 4097 | fresh-hit | 68.62 | 67.46 | -1.69% |
| bytes | 4097 | miss | 187.70 | 192.63 | +2.62% |
| bytes | 4097 | collision | 198.54 | 196.10 | -1.23% |
| bytes | 1048576 | same-object | 2969.64 | 2720.19 | -8.40% |
| bytes | 1048576 | fresh-hit | 5760.67 | 3315.25 | -42.45% |
| bytes | 1048576 | miss | 25746.25 | 22835.73 | -11.30% |
| bytes | 1048576 | collision | 23376.20 | 21360.35 | -8.62% |

No integrar todavía. Entradas4097 muestran regresión, especialmente bytes same-object(+14.18%). Fresh-hit1MiB mejoró~42%, sin extrapolar al request. Revisión adversarial detecta que collision actual difiere al principio; añadir diferencias tardías antes de decidir. Ajustar umbral para reservar buckets a entradas mayores.
