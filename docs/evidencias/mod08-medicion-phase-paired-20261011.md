# Diagnóstico con fases emparejadas

Un caso sintético completo. No acredita aceptación de dos casos ni N3. Instrumentación añadida; no cambio productivo ni ganancia atribuible. Captura y uso terminales, un test PASS cada uno, 1153 hashes por ejecución verificados y recursos propios retirados.

| Métrica | Anterior (s) | Nueva (s) | Variación de tiempo | n | Objetivo (s) |
|---|---:|---:|---:|---:|---:|
| Listado TCP completo | 3.802134 | 3.934962 | +3.49% | 383 | 2 |
| generation | 43.225665 | 43.903684 | +1.57% | 1 | 120 |
| final_preparation | 14.573323 | 15.234616 | +4.54% | 1 | 30 |
| final_inspection | 3.421777 | 4.196300 | +22.64% | 1 | 30 |
| final_approval | 3.927704 | 3.952883 | +0.64% | 1 | 5 |
| closure | 15.481998 | 15.531436 | +0.32% | 1 | 30 |
| json_download | 6.906630 | 7.812455 | +13.12% | 3 | 5 |
| binary_download | 7.485222 | 7.710310 | +3.01% | 8 | 5 |

n=1 es muestra individual, no p95. Con n=3/n=8, p95 nearest-rank coincide con el máximo y es evidencia limitada. Listado: 383 requests conservados, 383 con fases completas.

Mismo request del p95 TCP, ID187: WSGI 3.933473s, CPU del hilo 1.932104s; 447 ejecuciones SQL, wall SQL 1.763513s y CPU SQL 0.135818s. Se solapan: no sumar. CPU incluye bibliotecas nativas; SQL wall incluye espera/desplanificación y excluye fetch/adaptación.

| Fase | CPU exclusiva (s) | Wall exclusivo (s) | SQL | Wall SQL (s) |
|---|---:|---:|---:|---:|
| batch | 0.027983 | 0.196351 | 14 | 0.165540 |
| page | 0.104019 | 0.238848 | 84 | 0.149764 |
| record | 0.116775 | 0.623720 | 84 | 0.523379 |
| baseline | 0.001102 | 0.001138 | 0 | 0.000000 |
| unseal | 0.152171 | 0.157203 | 0 | 0.000000 |
| source | 0.208164 | 0.530880 | 20 | 0.064372 |
| compile | 0.066393 | 0.067922 | 0 | 0.000000 |
| authorize | 0.118476 | 0.254616 | 93 | 0.147047 |
| validate_selection | 0.095329 | 0.157791 | 20 | 0.058153 |
| validate_assessment | 0.215805 | 0.755873 | 88 | 0.566107 |
| assessment_evidence | 0.001430 | 0.001451 | 0 | 0.000000 |
| selection_evidence | 0.023085 | 0.038420 | 20 | 0.019224 |
| audited_images | 0.037035 | 0.088565 | 16 | 0.055579 |
| checked_images | 0.017046 | 0.017326 | 0 | 0.000000 |
| read_image_blob | 0.110365 | 0.115746 | 0 | 0.000000 |
| content_digest | 0.221806 | 0.232581 | 0 | 0.000000 |
| batch_projection | 0.050506 | 0.051473 | 0 | 0.000000 |
| canonical_bytes | 0.188227 | 0.196572 | 0 | 0.000000 |
| fingerprint | 0.143806 | 0.152039 | 0 | 0.000000 |

Las fases exclusivas incluyen SQL y trabajo no observado. No atribuir automáticamente el residuo a Python.

Siguiente candidata en revisión: trasladar nueve SELECT secuenciales de confianza de runtime a PostgreSQL conservando snapshots, cortocircuitos y evidencia del sello. Interfaz booleana sola rechazada; no implementada ni medida.
