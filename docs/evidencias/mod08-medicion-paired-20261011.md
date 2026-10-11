# Medición emparejada — 2026-10-11

Un caso sintético completo, diagnóstico. Fuentes congeladas durante captura y use;1153hashes cadauno y retirada propia independientes. Captura1PASS1537,268s;use1PASS278,264s;0fallos/errores/skips. Sin nueva optimización productiva: variación no atribuida a ganancia técnica. Doscasos/N3/objetivos completos pendientes.

| Métrica | Anterior (s) | Actual (s) | Mejora | Objetivo (s) | n |
| --- | ---: | ---: | ---: | ---: | ---: |
| Listado p95 lote completo | 3.865976 | 3.802134 | 1.65% | 2 | 383 |
| generation (single_sample_not_p95) | 44.090730 | 43.225665 | 1.96% | 120 | 1 |
| final_preparation (single_sample_not_p95) | 15.200386 | 14.573323 | 4.13% | 30 | 1 |
| final_inspection (single_sample_not_p95) | 3.664138 | 3.421777 | 6.61% | 30 | 1 |
| final_approval (single_sample_not_p95) | 4.225175 | 3.927704 | 7.04% | 5 | 1 |
| closure (single_sample_not_p95) | 16.213333 | 15.481998 | 4.51% | 30 | 1 |
| json_download (nearest_rank_p95) | 7.313810 | 6.906630 | 5.57% | 5 | 3 |
| binary_download (nearest_rank_p95) | 7.418959 | 7.485222 | -0.89% | 5 | 8 |

Misma petición en p95 TCP, ID327:TCP3.802134s/WSGI3.800317s/threadCPU2.066251s.383IDs únicos exactos; parciales incluidos, extra perfilado excluido. CPU incluye bibliotecas nativas; wall menos CPU incluye espera/desplanificación sin atribución específica. TCP menos WSGI no identifica red/cola; close puede acabar después de EOF cliente.

p95CPU separado2,089520s y WSGI3,800317s no deben confundirse con componentes sumables del p95TCP. Descargas n3/n8 nearest-rank=población pequeña, no aceptación; dos autorizaciones frescas y EOF, packs<=8MiB verificados.

La muestra extra de17fases no es la petición p95; intervalos inclusivos se solapan. Cuadro completo separado abajo.

# Muestra extra de fases: no p95, no misma petición que TCP p95

Fases inclusivas se solapan y no deben sumarse.

| Fase | Wall anterior (s) | Wall actual (s) | CPU anterior (s) | CPU actual (s) |
| --- | ---: | ---: | ---: | ---: |
| assessment_evidence | 0.001987 | 0.002203 | 0.001959 | 0.002164 |
| audited_images | 0.387853 | 0.487172 | 0.332980 | 0.395534 |
| authorize | 0.285751 | 0.254292 | 0.129602 | 0.119705 |
| baseline | 0.060547 | 0.064099 | 0.058227 | 0.062631 |
| batch | 2.599205 | 2.839859 | 1.618592 | 1.787116 |
| batch_projection | 0.059221 | 0.071210 | 0.058695 | 0.070172 |
| checked_images | 0.016768 | 0.017480 | 0.015777 | 0.016995 |
| compile | 0.077335 | 0.069956 | 0.076570 | 0.069296 |
| content_digest | 0.209870 | 0.231656 | 0.205097 | 0.223704 |
| page | 1.754128 | 1.804761 | 1.199915 | 1.212387 |
| read_image_blob | 0.084296 | 0.137339 | 0.081081 | 0.119782 |
| record | 0.913122 | 1.048099 | 0.645936 | 0.709453 |
| selection_evidence | 0.140783 | 0.125131 | 0.120996 | 0.106721 |
| source | 0.514440 | 0.669372 | 0.241027 | 0.379773 |
| unseal | 0.138807 | 0.129420 | 0.133480 | 0.126871 |
| validate_assessment | 0.117231 | 0.131889 | 0.043173 | 0.044909 |
| validate_selection | 0.277254 | 0.237587 | 0.218827 | 0.186238 |

