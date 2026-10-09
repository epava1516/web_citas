# MOD05: gates en topología normal (worker y Beat reales)

**Gate de 60 s PASS completo y contractual de 900 s PASS (intento 2) en `normal_worker_beat` con 4 workers sync.** El intento 1 del contractual fue INVALID por el GC del proceso cliente. CR09 sigue abierto hasta la aceptación del usuario; los porcentajes no cambian.

Autorizaciones expresas del usuario, 2026-10-08: «Autorizo el gate de 60 s en normal_worker_beat» y «Autorizo cualquier prueba de aquí en adelante». Trabajo de Claude Code (Claude Opus 5.5). [Manifiesto prefijado](mod05-gate-normal-manifiesto0110.json) y [runner](mod05-gate-normal-runner0110.py).

## Escenario

- **Topología:** decisión del usuario de ejecutar el gate en `normal_worker_beat`. Worker (`--concurrency=2`) y Beat propios con los comandos de compose y el calendario completo.
- **Aislamiento:** Redis db 15 propia, verificada vacía antes y después. Fase de Beat fijada: llegadas 5 s después de un tick observado.
- **Gunicorn:** 4 workers sync, como en todos los gates.
- **Arnés:** `tests/test_contract_http_load.py` con el modo opt-in `WEB_MODELOS_REFRESH_MODE=normal_worker_beat`. Por defecto mantiene el escenario eager anterior.
- **Fuente:** `c82a746` más la corrección local de la marca sin señal y las fuentes de arnés de esta preparación, sin commit. Las huellas quedan congeladas en el manifiesto de cada ejecución y su ausencia de cambios se verificó al terminar.
- **Criterios:** los del contrato y el gate vigentes, sin cambios.

## Calibración `functional`

- **Intento 1, INVALID solo por `generator_delay_p99`:** una emisión (t=1,75 s) se retrasó 28,6 ms; el resto ≤3 ms. No coincide con el GC del cliente ni con el muestreador. Con 60 muestras, p99 = máximo. 60/60 correctas, upload 302, refresco y limpieza correctos. ([artefactos](mod05-gate-normal-functional-intento1-artefactos0110.tar.gz))
- **Repetición única** registrada en el manifiesto antes de ejecutarla. **Intento 2: PASS**, p99 del generador 3,5 ms. ([artefactos](mod05-gate-normal-functional-intento2-artefactos0110.tar.gz))

## Gate de 60 s: PASS completo

[Artefactos originales](mod05-gate-normal-short-artefactos0110.tar.gz).

| Criterio | Exigido | Observado |
|---|---|---|
| Generador y contabilidad | válidos, reconciliados | p95/p99/máx 2,24/3,77/12,37 ms; reconciliado; 0 no emitidas |
| Dinámicas | 1.200 | 1.200/1.200 correctas, 0 errores, 0 timeouts |
| p95 observable | < 800 ms | 621,6 ms (p50 254,8; p99 776,0; máx 855,9) |
| Pendientes en el cierre de la ventana | ≤ 20 | 5 |
| Pendientes finales | 0 | 0 |
| Drain | ≤ 70 s | 60,13 s transcurridos en total |
| Upload | 302 | 302 (0,38 s) |

- **Por familia:** media/p95 en ms de listado 315/656, búsqueda 322/674 y ficha 204/527. Servicio Gunicorn p95 322,7 ms.
- **Refresco:**
  - 7 ejecuciones (beat 3, worker 3, web 1) con 1,10 s de pared y 0,34 s de CPU. 3 marcas limpiadas en 0,26–0,35 s.
  - Muestras con sucios: 2/60. Secuencia de marcas +10. `process_blob` en el worker: 4,81 s de pared, 0,57 s de CPU.
  - CPU de los procesos worker/Beat durante las llegadas: 1,62 s.
- **Limpieza:** bases retiradas, medios eliminados, PIDs de web/worker/Beat ausentes, Redis db 15 vacía y fuentes sin cambios. El aviso `owned_processes_with_output_path_absent=False` lo causó mi propio bucle de espera, cuyo comando contenía la ruta de salida; la comprobación posterior no encontró procesos.
- **Margen:** p95 0,62 s y p99 0,78 s, menos holgura que en los bloques de 30 s. El host estaba compartido, con carga ajena ≈4–5 de 8 cores.

## Contractual de 900 s

**Intento 1: INVALID** ([artefactos](mod05-contractual-normal-intento1-artefactos0110.tar.gz)). La única causa fue `generator_delay_max` de 121,27 ms (límite 100 ms): una recolección gen-2 de 169 ms del GC del proceso cliente, en t≈801,6 s, solapa 120,3 ms del retardo de `d-16032` y afecta a las dos emisiones siguientes. Solo 2 de 18.000 emisiones superaron 25 ms. El resto de valores observados también cumplían: 18.000/18.000 correctas, 0 errores, p95 0,486 s, 15/15 uploads. El veredicto se conserva como INVALID, no PASS ni FAIL.

**Corrección del instrumento cliente, registrada en el manifiesto antes del intento 2:** `WEB_MODELOS_GENERATOR_GC_FREEZE=1`, opt-in en `scripts/benchmark_gc_observer.py`. Tras el `gc.collect(2)` previo ya existente, `gc.freeze()` dejó 184.107 objetos del fixture en la generación permanente. El GC siguió habilitado con umbrales 700/10/10. No cambian servidor, escenario, criterios ni umbrales del generador.

**Intento 2: PASS contractual** ([artefactos](mod05-contractual-normal-intento2-artefactos0110.tar.gz)).

| Criterio | Exigido | Observado |
|---|---|---|
| Generador y contabilidad | p95/p99/máx ≤ 10/25/100 ms, reconciliados | 2,14/3,23/27,17 ms; reconciliado; 0 no emitidas |
| Dinámicas | 18.000, 1/3 listado/búsqueda/ficha ES/EN | 18.000/18.000 correctas, 0 errores, 0 timeouts |
| p95 observable | < 800 ms | 392,4 ms (p50 244,0; p99 475,9; máx 661,8) |
| Pendientes | 0 finales | 7 en el cierre de la ventana, 0 finales; transcurridos 905,09 s |
| Uploads | 15, uno por minuto, 302 | 15/15 con 302 (0,11–0,33 s) |

- **Por familia:** media/p95 en ms de listado 279/413, búsqueda 286/410 y ficha 169/291. Servicio Gunicorn p95 318,0 ms.
- **GC del cliente durante la carga:** pausa máxima de 29,9 ms.
- **Refresco durante el contractual:**
  - 63 ejecuciones (beat 31, worker 17, web 15) con 8,97 s de pared y 2,65 s de CPU de hilo.
  - 32 marcas limpiadas: mediana 0,23 s, máximo 0,42 s.
  - Muestras con sucios: 8/905, con la marca más antigua de 0,29 s como máximo. Secuencia de marcas +80.
  - 15 `process_blob` en el worker: 71,2 s de pared y 2,7 s de CPU.
  - CPU de los procesos worker/Beat durante las llegadas: 12,1 s.
- **Limpieza y fuentes:** bases retiradas, medios eliminados, PIDs de web/worker/Beat ausentes, Redis db 15 vacía y fuentes sin cambios. Esta vez la comprobación de procesos por ruta salió limpia.

## Cobertura de rutas (MOD-04 §16)

[Matriz](mod05-cobertura-rutas0110.json) con `tests/test_publication_route_coverage.py` (opt-in): 10.000 anuncios del fixture repetido, Client en proceso, 2 controles tras un warmup. No es TCP ni capacidad. Cada caso se compara byte a byte con la ruta nativa forzada.

| Modo / filtro | Ruta real | Equivalente al nativo | Recuento | Control medio | Nativo |
|---|---|---|---|---|---|
| Normal, listado ES | state | sí | 10.000 | 0,349 s | 13,58 s |
| Normal, búsqueda EN | state | sí | 10.000 | 0,257 s | 14,14 s |
| Normal, `checked` age | state | sí | 0 | 0,110 s | 35,29 s |
| Normal, `checked` contact+agency | state | sí | 0 | 0,142 s | 35,17 s |
| Normal, página 3 | state | sí | 10.000 | 0,814 s | 12,92 s |
| PRODUCTION, listado | state | sí | 0 | 0,116 s | 28,49 s |
| PRODUCTION, búsqueda + `checked` age | state | sí | 0 | 0,114 s | 28,14 s |
| Promociones sintéticas | fallback nativo (`synthetic_promotions`) | sí | 10.000 | 14,30 s | 14,95 s |

Limitaciones:

- **Recuento 0** con `checked` y con PRODUCTION: los datos sintéticos no tienen comprobaciones reales, y PRODUCTION rechaza el verificador simulado. La ruta y la equivalencia quedan comprobadas, pero el coste no es representativo de una población publicable.
- **Promociones:** solo existen en modo de prueba sintético (`enabled()` es falso con PRODUCTION) y mantienen deliberadamente la ruta nativa. Con 10.000 anuncios cuestan unos 14 s por petición, así que ese modo no es viable para carga. No afecta a producción.
- **Página 3:** 0,81 s, frente a 0,35 s de la primera página, en dos controles en proceso. No está en la mezcla contractual y no se ha investigado.

## Alcance

Resultados locales y sintéticos en la topología desplegada, sobre un host compartido. No acreditan producción, proveedores reales ni CDN. Los resultados en escenario eager (R5/R6 de portátil, gate VPS FAIL, diagnóstico de 30 s) conservan su escenario y su veredicto; no se comparan causalmente con estos. Los porcentajes y el cierre de CR09 requieren aceptación del usuario (docs86).

## Estado de aceptación (decisión del usuario, 2026-10-09)

Entrega en la rama `cr09-rend-lectura-normal`, sin integrar en master; porcentajes sin cambio. El cierre local queda pendiente de que Codex revise los artefactos originales y de cubrir funcionalmente PRODUCTION y `checked` con resultados positivos, reutilizando evidencia válida. La revisión preliminar no encontró resultados positivos en esos modos: pertenencia funcional da 0 con `checked`, y PRODUCTION no publica con datos sintéticos. Los PASS y los veredictos históricos se conservan. No se atribuye por separado el efecto de la topología y el del arreglo. CR09 integral y producción siguen abiertos.

**Actualización:** la cobertura positiva se obtuvo con una prueba funcional nueva, sin carga ([evidencia](mod05-cobertura-positiva0110.json)), con datos y proveedor de verificación sintéticos. Todo es idéntico al nativo y va por la ruta `state`. En PRODUCTION hay 10 anuncios en todos los filtros; en modo normal, 25, y 10 con `checked` age. Pendiente únicamente la revisión de Codex de los artefactos originales.
