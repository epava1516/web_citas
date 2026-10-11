# MOD-08: medición tras integrar pipeline y HMAC adaptativo

Fuentes congeladas e7846d7. Captura 20261011-064425-ed839a88 y uso 20261011-071449-f8adec38 terminales, una prueba aprobada por ejecución sin fallos/errores/omisiones. Verificados independientemente 1156 hashes por ejecución y retirada de recursos propios.

| Métrica | Anterior (s) | Nueva (s) | Reducción | Muestras | Objetivo (s) |
|---|---:|---:|---:|---:|---:|
| TCP lote completo p95 | 3.934962 | 3.753392 | 4.61% | 383 | 2 |
| generation | 43.903684 | 42.731399 | 2.67% | 1 | 120 |
| final_preparation | 15.234616 | 15.433019 | -1.30% | 1 | 30 |
| final_inspection | 4.196300 | 3.160195 | 24.69% | 1 | 30 |
| final_approval | 3.952883 | 4.049159 | -2.44% | 1 | 5 |
| closure | 15.531436 | 16.237231 | -4.54% | 1 | 30 |
| json_download | 7.812455 | 6.930455 | 11.29% | 3 | 5 |
| binary_download | 7.710310 | 7.317947 | 5.09% | 8 | 5 |

Un caso sintético completo. Descargas con dos autorizaciones HTTP frescas y lectura hasta EOF; JSON n3/binario n8 insuficientes para aceptación, su p95 nearest-rank es el máximo. Las métricas n1 no son p95. Valores negativos indican empeoramiento. No atribuir a cada optimización individual ni declarar aceptación completa dos casos/N3.

Navegación precisa reducir otros 1,753392s; JSON 1,930455s y binario 2,317947s para los objetivos respectivos.

| Fase exclusiva | Wall anterior (s) | Wall nuevo (s) | CPU anterior (s) | CPU nuevo (s) |
|---|---:|---:|---:|---:|
| batch | 0.196351 | 0.150354 | 0.027983 | 0.026021 |
| page | 0.238848 | 0.191141 | 0.104019 | 0.107285 |
| record | 0.623720 | 0.214935 | 0.116775 | 0.109441 |
| baseline | 0.001138 | 0.001110 | 0.001102 | 0.001070 |
| unseal | 0.157203 | 0.161807 | 0.152171 | 0.154186 |
| source | 0.530880 | 0.627122 | 0.208164 | 0.274064 |
| compile | 0.067922 | 0.076620 | 0.066393 | 0.074426 |
| authorize | 0.254616 | 0.219205 | 0.118476 | 0.119212 |
| validate_selection | 0.157791 | 0.138773 | 0.095329 | 0.098046 |
| validate_assessment | 0.755873 | 1.064649 | 0.215805 | 0.294990 |
| assessment_evidence | 0.001451 | 0.001462 | 0.001430 | 0.001429 |
| selection_evidence | 0.038420 | 0.032839 | 0.023085 | 0.022979 |
| audited_images | 0.088565 | 0.073329 | 0.037035 | 0.038169 |
| checked_images | 0.017326 | 0.019206 | 0.017046 | 0.018702 |
| read_image_blob | 0.115746 | 0.099679 | 0.110365 | 0.096034 |
| content_digest | 0.232581 | 0.308314 | 0.221806 | 0.290046 |
| batch_projection | 0.051473 | 0.054046 | 0.050506 | 0.051735 |
| canonical_bytes | 0.196572 | 0.168899 | 0.188227 | 0.163126 |
| fingerprint | 0.152039 | 0.093412 | 0.143806 | 0.091300 |

Peticiones distintas en sus respectivos p95; no percentiles independientes. Espera pipeline.sync fuera del wrapper SQL: no atribuir toda reducción aparente de SQL a menor tiempo de base de datos.

