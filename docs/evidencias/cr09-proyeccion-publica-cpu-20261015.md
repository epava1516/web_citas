# Proyección temporal pública: CPU de población

Run `20261015-151258-1e4327aa`, base `6229f90` más diagnóstico:1PASS93.41s. Datos sintéticos propios,10kpublicaciones. Fuente congelada y limpieza independiente verificadas; tabla temporal eliminada explícitamente y backend/raíz/pytest/temporales/PG/Redis ausentes. No cambia modelos, migraciones, consultas de producto ni servicios normales.

Experimento: copia estática a tabla pg_temp validada con listing_id,estado/versión,expires_at,published_at y vector de búsqueda. Índice temporal de orden y ANALYZE; no afirmar idéntico estado estadístico físico de ambas representaciones. Referencia: Paginator de la población real capturada de state_page; ambas variantes comprueban conteo e IDs ordenados en cada operación contra página guardada. Siete casos,4warmups+3bloques alternos×8operaciones×2variantes=336operaciones medidas; snapshotRR de sólo lectura por caso. CPU de backend100Hz.

| Caso | CPU actual conteo+página(ms) | Temporal(ms) |
|---|---:|---:|
| listado,página1 | 7.500 | 2.083 |
| listado,página2 | 8.333 | 2.500 |
| photography,página1 | 40.417 | 10.417 |
| photography,página2 | 44.583 | 9.583 |
| synthetic,página1 | 40.833 | 9.583 |
| synthetic,página2 | 37.917 | 10.417 |
| zzznomatchproof,página1 | 5.833 | 5.417 |

Resultado material frente a variantes descartadas: listados ahorran5–6ms y búsquedas con coincidencias27–35ms en este experimento. Sin coincidencias cambia poco. No son tiempos de request ni p95 ni prueba causal universal del join aislado: difieren representación física/estadísticas/índice, además del SQL.

La copia estática NO es válida para datos vivos. No hubo mutaciones entre copia y lectura; no se midió mantenimiento, almacenamiento sostenido, concurrencia, permisos, filtros generales, caducidad durante solicitudes ni ventanas de refresco. El último limpio5.004966sFAIL se conserva, sin nueva carga.

Siguiente diseño por justificar: ampliar la PublicationState ya existente con campos de lectura mínimos, no crear otro subsistema. Conservar versión de reglas, dirty transaccional, reclamación por generación del refresher, sweep, caducidad evaluada al leer, guardia nativa de la página seleccionada y fallback. Activación sólo sobre población limpia conocida y snapshot propioRR; transacciones heredadas, filtros no soportados, clones de QuerySet, datos ausentes u obsoletos mantienen vía original. Analizar copia de campos en expected_states/store, versión y migración, fixtures/clones, orden/ranking exactos y pruebas de cada cambio relevante antes de implementar/medir carga. Ni cambiar cuotas ni relajar exposición para ganar rendimiento.
