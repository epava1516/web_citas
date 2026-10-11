# Índice HMAC adaptativo: gate real

PostgreSQL real31PASS/0fallos/errores/skips106.207s;1155hashes ycleanupindependientes. Índice barato sólo>64KiB;singleton exigeigualdadtotal ysegunda colisiónretenida promueveadict exacta. Caps128/32MiB, secretofresco yscopes intactos.

| Tipo | Tamaño | Escenario | CPU referencia (µs) | CPU adaptativa (µs) | Variación |
|---|---:|---|---:|---:|---:|
| str | 128 | same-object | 83.65 | 87.77 | +4.92% |
| str | 128 | fresh-hit | 84.10 | 87.55 | +4.10% |
| str | 128 | miss | 158.60 | 157.18 | -0.89% |
| str | 128 | collision | 138.88 | 144.07 | +3.74% |
| str | 128 | late-collision | 135.32 | 136.53 | +0.90% |
| str | 4097 | same-object | 76.02 | 76.62 | +0.79% |
| str | 4097 | fresh-hit | 81.11 | 81.04 | -0.08% |
| str | 4097 | miss | 207.32 | 212.65 | +2.57% |
| str | 4097 | collision | 197.72 | 200.03 | +1.17% |
| str | 4097 | late-collision | 202.42 | 210.58 | +4.03% |
| str | 65537 | same-object | 248.52 | 243.38 | -2.07% |
| str | 65537 | fresh-hit | 422.59 | 286.97 | -32.09% |
| str | 65537 | miss | 1823.21 | 1618.42 | -11.23% |
| str | 65537 | collision | 1739.25 | 1736.25 | -0.17% |
| str | 65537 | late-collision | 1758.38 | 1776.01 | +1.00% |
| str | 65537 | saturated-bucket | 1799.58 | 1819.38 | +1.10% |
| str | 1048576 | same-object | 3209.71 | 2944.61 | -8.26% |
| str | 1048576 | fresh-hit | 5856.29 | 3487.04 | -40.46% |
| str | 1048576 | miss | 26149.63 | 23865.83 | -8.73% |
| str | 1048576 | collision | 25750.32 | 25978.61 | +0.89% |
| str | 1048576 | late-collision | 25713.27 | 26256.96 | +2.11% |
| str | 1048576 | saturated-bucket | 24094.66 | 24099.25 | +0.02% |
| bytes | 128 | same-object | 44.19 | 45.20 | +2.30% |
| bytes | 128 | fresh-hit | 44.77 | 46.05 | +2.86% |
| bytes | 128 | miss | 90.54 | 92.14 | +1.76% |
| bytes | 128 | collision | 91.17 | 92.38 | +1.33% |
| bytes | 128 | late-collision | 89.22 | 90.56 | +1.51% |
| bytes | 4097 | same-object | 56.43 | 57.87 | +2.54% |
| bytes | 4097 | fresh-hit | 66.32 | 67.81 | +2.25% |
| bytes | 4097 | miss | 185.99 | 186.42 | +0.23% |
| bytes | 4097 | collision | 188.31 | 189.24 | +0.49% |
| bytes | 4097 | late-collision | 183.25 | 186.98 | +2.04% |
| bytes | 65537 | same-object | 225.76 | 218.18 | -3.36% |
| bytes | 65537 | fresh-hit | 382.33 | 254.89 | -33.33% |
| bytes | 65537 | miss | 1585.06 | 1456.94 | -8.08% |
| bytes | 65537 | collision | 1576.20 | 1597.41 | +1.35% |
| bytes | 65537 | late-collision | 1599.67 | 1647.28 | +2.98% |
| bytes | 65537 | saturated-bucket | 1577.02 | 1580.70 | +0.23% |
| bytes | 1048576 | same-object | 2933.18 | 2766.21 | -5.69% |
| bytes | 1048576 | fresh-hit | 5629.85 | 3257.78 | -42.13% |
| bytes | 1048576 | miss | 23167.61 | 21297.50 | -8.07% |
| bytes | 1048576 | collision | 23417.93 | 23450.99 | +0.14% |
| bytes | 1048576 | late-collision | 23331.50 | 23831.38 | +2.14% |
| bytes | 1048576 | saturated-bucket | 24150.73 | 25158.69 | +4.17% |

Una ronda warmup/modo,9parejas alternadas,8llamadas/muestra. Fresh-hit1MiB CPU40.46%menosstr/42.13%menosbytes; saturación quedó+1.10%/+0.23%65537 y+0.02%/+4.17%1MiB. Diferencias pequeñas sujetasaruido, no igualdad de rendimiento demostrada. Negativos anteriores conservados. No atribuir porcentajes a request ni aceptar capacidadcompleta con microbench.

Próximo: integración local y gate conjunto dirigido con pipeline; luego captura/use con fuentes congeladas, cuotas originales y todas páginas/objetos.
