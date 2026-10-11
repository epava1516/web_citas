# MOD-08: cuatro lectores rechazados tras medir

Captura 20261011-073025-e9a3cb1c y uso 20261011-075925-06fbddf7 terminales, una prueba aprobada por ejecución, cero fallos/errores/omisiones,1156hashes y retirada propios verificados cada vez.

| Métrica | Anterior (s) | Cuatro lectores (s) | Reducción | Muestras | Objetivo (s) |
|---|---:|---:|---:|---:|---:|
| TCP lote p95 | 3.753392 | 3.726545 | 0.72% | 383 | 2 |
| generation | 42.731399 | 43.228051 | -1.16% | 1 | 120 |
| final_preparation | 15.433019 | 15.169601 | 1.71% | 1 | 30 |
| final_inspection | 3.160195 | 4.130940 | -30.72% | 1 | 30 |
| final_approval | 4.049159 | 4.503030 | -11.21% | 1 | 5 |
| closure | 16.237231 | 16.063862 | 1.07% | 1 | 30 |
| json_download | 6.930455 | 7.741606 | -11.70% | 3 | 5 |
| binary_download | 7.317947 | 8.645426 | -18.14% | 8 | 5 |

Negativos indican empeoramiento. JSONn3/binario n8 nearest-rank p95 igual al máximo; insuficiente para aceptación. Etapasn1 no son p95. No causalidad individual demostrada por dos ejecuciones; evidencia insuficiente para aceptar mayor concurrencia. Se restaura versión de dos lectores, conservando candidata y mediciones. Cambio TCP no atribuible a lectores de exportación.

| Memoria global, cota conservadora | Anterior (GiB) | Cuatro lectores (GiB) |
|---|---:|---:|
| capture | 1.917 | 1.863 |
| use | 2.714 | 2.808 |

Sin swap ni OOM; cota global bajo6GiB incluye cache/tmpfs y techo controlador, no pico simultáneo ni RSS app. No aceptación completa dos casos/N3/2s/5s.
