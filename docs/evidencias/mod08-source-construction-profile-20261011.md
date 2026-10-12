# MOD-08 — Coste de construcción de la fuente — 2026-10-11

## Resultado y decisión

Diagnóstico acotado autorizado por «Procede», después de la deliberación con NotebookLM. Runner `20261011-130102-8286f2c3`: **5 PASS/0 fallos/errores/skips**, 98.47s JUnit. 1176 huellas exactas comprobadas antes de editar documentación; PostgreSQL/Redis y Gunicorn propios ausentes verificados independientemente. Código productivo intacto.

La candidata de valores primitivos para categorías/servicios/travel areas **no queda justificada en este fixture**: no destaca una carga material de creación de esos modelos. No generalizar a relaciones más densas ni atribuir todo el tiempo de consulta a modelos. Se cierra por ahora esta rama, sin aplicar otro microparche.

Pista siguiente: algoritmos puros de recorrido de hojas y selección (`scalar_fields`, RFC6901, `pointer_value`) dentro de `compile_coverage`/`project_selected`. Hay frecuencia observada y código verificable, pero el profiler distorsiona demasiado los tiempos para prometer ahorro. Su coste limpio y una posible sustitución iterativa requieren un experimento separado; no ejecutado ni integrado en este encargo.

## Método y trazabilidad

[Datos completos](mod08-source-construction-profile-20261011.json). Fixture propio sintético de 1500 revisiones, selección 16777172 bytes, aprobación mediante servicios con 31 lecturas paginadas reales y cobertura parcial escalar. Historial generado por 64 POST reales: cabeza 548 eventos y 256 lecturas de cobertura. Plantilla privada PostgreSQL con conexiones cerradas; cada muestra usa un clon idéntico, nueva conexión y commits normales. Verificación independiente tras cada muestra: cuatro lecturas y ocho eventos nuevos. Dos workers Gunicorn sync con POST de calentamiento comprobados; las tres muestras resultaron servidas por el mismo PID 175903.

Sólo tres peticiones medidas: control/perfilada/control. Preparación y warmups excluidos de las cifras. No Caddy/RustFS/cuotas contractuales, concurrencia de carga ni descargas binarias. No comparación con p95 histórico de 383 lotes ni aceptación 2s/5s.

| Muestra | TCP hasta cuerpo completo | WSGI | CPU de hilo WSGI |
|---|---:|---:|---:|
| Control anterior | 812.239 ms | 811.169 ms | 428.554 ms |
| Perfilada | 1882.635 ms | 1950.134 ms | 1563.754 ms |
| Control posterior | 796.736 ms | 795.745 ms | 425.883 ms |

La intrusión es grande. No restar el diferencial como overhead causal medido ni ajustar el resultado perfilado para inventar un tiempo limpio. La salida del scope prepara estadísticas y restablece aliases después del yield: TCP puede completar antes de ese trabajo y WSGI lo incluye. Los dos relojes no cubren el mismo perímetro.

## Spans de aplicación, sólo muestra perfilada

| Fase | Calls | Wall inclusivo | CPU inclusivo | Wall exclusivo | CPU exclusivo |
|---|---:|---:|---:|---:|---:|
| source_init | 1 | 468.332 | 387.032 | 0.119 | 0.116 |
| source_copy | 1 | 425.327 | 362.969 | 41.811 | 41.794 |
| batches_active_next | 1501 | 378.769 | 319.893 | 307.828 | 262.916 |
| source_fingerprint | 2 | 37.451 | 1.743 | 0.445 | 0.442 |
| source_context_exit | 1 | 26.802 | 9.895 | 0.114 | 0.113 |
| canonical_bytes | 1705 | 69.732 | 69.635 | 69.732 | 69.635 |
| fingerprint | 363 | 25.534 | 25.564 | 25.534 | 25.564 |
| render | 1 | 34.469 | 34.399 | 34.469 | 34.399 |
| validate_chain | 4 | 80.186 | 28.400 | 56.194 | 24.713 |
| sql_execute_driver | 423 | 404.473 | 107.741 | 404.473 | 107.741 |

Duraciones ms. Exclusivo significa descuento de hijos observados en este árbol, no CPU de servidor ni una fase físicamente aislada. `batches_active_next` excluye suspensión entre yields, pero incluye carga/adaptación/hidratación de revisiones y agrupación, además de trabajo no observado: **no equivale a coste ORM puro**. `sql_execute_driver` excluye fetch/sync, puede incluir recepción/adaptación durante execute y no separa ejecución PostgreSQL del transporte. Pequeñas discrepancias CPU/wall son posibles por orden de captura y callbacks del profiler; no atribuirlas a una espera negativa.

Cada relación tiene dos evaluaciones de materialización: Category/Service/Municipality ~13–14ms wall inclusivos/~10.8ms CPU cada familia; tras descontar SQL observado, CPU exclusiva 1.765/1.751/1.889ms respectivamente. Rate 1.587ms y Photo 4.518ms CPU exclusiva. Esos residuales no son una medición perfecta de instanciación y excluyen trabajo ocurrido dentro de execute; tampoco son ahorros esperados. El perfil global observa sólo 2010 Model.__init__ y 1993 from_db en todo el request, sin desglose por familia en esos contadores.

## CPU profiler auxiliar y lectura prudente

`cProfile(timer=thread_time)` registra sólo nombres/cuentas/tiempos, sin locals ni argumentos/payloads. El informe conserva los 100 mayores tiempos propios; no es un censo exhaustivo de toda la CPU. Funciones nativas/Cython pueden carecer de detalle interno. No sumar este árbol al árbol de spans.

| Función | Calls del profiler | CPU propia | CPU inclusiva |
|---|---:|---:|---:|
| scalar_fields | 101755 (72978 recursivas) | 101.493 ms | 147.259 ms |
| pointer_value | 9002 | 33.366 ms | 78.634 ms |
| Model.__init__ | 2010 | 21.842 ms | 72.552 ms |
| Model.from_db | 1993 | 18.858 ms | 100.158 ms |
| project_selected | 2 | 14.623 ms | 184.502 ms |
| compile_coverage | 1 | 13.334 ms | 240.489 ms |

Los call counts de generadores incluyen entradas/reanudaciones y recursión: **101755 no significa 101755 recorridos completos**. `scalar_fields` es un generador recursivo con yield from que escapa rutas RFC6901 y devuelve hojas en orden. `compile_coverage` hace una proyección y luego enumera paths por fila; hay dos `project_selected` totales en el request, no prueba de que se puedan eliminar bajo las garantías actuales. Ya existe `batch_projection` acotada tras validaciones frescas. La sonda de deepcopy del diagnóstico anterior tampoco es coste productivo inferible aquí.

El alto número de eventos hace especialmente intrusivo cProfile. Una candidata de recorrido iterativo sólo sería plausible tras medir fuera del profiler y conservar orden, escapes RFC6901, tipos, errores y momento de validación; no cachear autoridad, eliminar lecturas ni relajar comprobaciones.

## Instrumento, preservación e incidencia

Código nuevo sólo en tests: `capacity_source_diagnostic.py`, `capacity_source_wsgi.py`, `test_capacity_source_diagnostic.py`, `test_capacity_source_construction_profile.py`. Se añadió un parámetro de aplicación al helper test-only `clone_server`, conservando su valor predeterminado. Cuatro tests de forwarding/restauración/excepciones y una integración PostgreSQL/TCP real; no confundir tests de dobles con verificación de integración.

La primera tanda `20261011-125955-bb11e9dd` se interrumpió deliberadamente al detectar que el nombre elegido coincidía con el test existente `test_capacity_source_profile.py`. No hubo tests terminados (KeyboardInterrupt a los 47.93s); no se declara PASS. Se restauró ese archivo exactamente de HEAD y el nuevo se guardó como `test_capacity_source_construction_profile.py`. Cambio y consumo anteriores preservados. La tanda final tiene fuentes congeladas y resultado válido.

Resultados y opinión propia enviados a NotebookLM mediante [consulta](mod08-notebook-source-profile-resultados-consulta-20261011.txt) y [respuesta](mod08-notebook-source-profile-resultados-respuesta-20261011.json). Sus sugerencias son hipótesis, no pruebas. Este diagnóstico termina; MOD08 general y aceptación completa permanecen pausados/pendientes.

Revisión propia de la respuesta del notebook: coincide con cerrar la candidata de relaciones simples y propone traversal iterativo condicionado. Su fragmento de código NO es aplicable: define marcos de tres elementos y luego usa `top[3]`/`top[4]` y `it=top`, lo que produciría IndexError y no usa el iterador guardado. Su afirmación de equivalencia estricta no está probada: deben considerarse además profundidad/RecursionError, mutaciones durante yield y propagación de errores. El umbral de 5–10ms que vuelve a sugerir es arbitrario y no se adopta. No se copió ese código ni se inició otro experimento.
