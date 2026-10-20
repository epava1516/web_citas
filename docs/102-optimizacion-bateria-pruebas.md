# Optimización de la batería — investigación aislada, 2026-10-19

Estado: integrada y verificada por regresión final común3656casos, sin fallos; detalles históricos y limitaciones debajo. Base09093c4, worktree test_optimization aislado; C fue interrumpido deliberadamente para priorizar la optimización, conservando1071PASS/6SKIP/0FAIL parciales; capacidad no iniciada. Grafo AST de pruebas/dependencias actualizado antes de analizar y preparar verificación; sin semántica documental completa ni nuevo consumo Claude.

El caso large_closed_flow tardó1652s, de ellos1604s en1511inspecciones nativas/191899consultas de esa etapa, según JUnit del primer C. No es latencia HTTP limpia. Semillas y aprobación/cierre/entrega ocuparon una fracción menor; no bajar1500revisiones ni sustituir el servicio por mocks para ganar tiempo.

La aplicación tiene inspect_batch con máximo4páginas, cada una con su registro/validaciones, contexto por petición y comprobación fresca al salir. La candidata usa esa vía ya existente sólo en la preparación del caso grande. Conserva todas las páginas requeridas, verifica orden y registros persistidos de cada lote, mantiene aprobación/cierre/replay/JSON/WebP/ZIP/huellas y el control de caso abierto antes de cierre. El helper mantiene por defecto la vía individual para las pruebas de carreras actuales. No cambia código de producto, máximo de lote ni políticas de autoridad.

Prerregistro: tres controles PostgreSQL reales del helper batched (cuenta, perfil, perfil+binario); luego medir el caso grande completo con las mismas1500revisiones y aserciones. La colección/orden por duración tiene su evidencia aparte. No prometer porcentaje de ahorro ni equiparar prueba concurrente/disinto presupuesto a medición causal.

Control auxiliar limitado aCPU6/1536MiB/swap0/512pids,PG0,5CPU7/512MiB/128pids/Redis0,1CPU7/64MiB/64pids: presupuestos propios menores y CPU fuera del C activo. Admisión con margen de memoria del host, sin cambiar los límites/servicios del C. Avisos Telegram terminales y limpieza independiente obligatorios. Prueba completa de tiempo sin interferencia se realizará por separado; no acumular ensayos especulativos.

Control del helper:3PASS/0SKIP, fuentes/limpieza/Telegram verificados en [recibo](evidencias/test-optimization-native-batch-control-20261019.json). Segunda candidata en test_rights_copy_scope: mismas30/1280revisiones, categorías/servicios/áreas/tarifas creadas por lotes y categorías esperadas leídas una vez. Mantiene todos los asserts y la comparación completa contra el lector de referencia; constraints/triggers PostgreSQL activos. No prueba nuevas operaciones de publicación ni cambia producto. Pendiente verificación de ambos tamaños y comparación diagnóstica directa/lotes con24revisiones por fixture, presupuestos iguales y C concurrente documentado.

Los cinco controles de helpers/historia dieron PASS, sin SKIP, [recibo](evidencias/test-optimization-bulk-history-control-20261019.json). Comparación observada con presupuestos/concurrencia distintos, sin porcentaje causal ni nueva latencia de producto:

| Caso / call de pytest | Primer C,2workers/PG1CPU | Candidata auxiliar1CPU/PG0,5CPU |
| --- | ---: | ---: |
| Historia30 | 19,20s aprox. | 8,027s |
| Historia1280 | 395,03s aprox. | 9,131s |

Se detectó que el ejecutor filtra PYTEST_ADDOPTS: la ordenación del C activo y el primer diagnóstico directo no se aplicaron. Sus regresiones siguen válidas con el orden ordinario, pero no prueban dicha aceleración ni comparación directa. Hallazgo conservado; no modificar allowlist de entorno. Adaptador corregido con argv explícito, recibo del argv real y archivo que demuestra plugin cargado. Preflight de cinco casos sólo colección pasó, sin ejecución funcional.

Próximo ensayo secuencial: referencia5casos (tres controles con24históricos y función original de fixture30/1280 desde09093c4, todos sus asserts), candidata6(incluye caso completo1500/cierre/WebP/ZIP) y repetición5de controles. Mismo commit/presupuesto auxiliar, C concurrente documentado. La función de referencia se carga explícitamente del commit en la instrumentación, sin modificar producto ni fingir N3 común. Sin baseline1500 repetido innecesariamente ni rebajar ese volumen de la candidata. Cada fase debe pasar y limpiarse antes de iniciar la siguiente; se conserva cualquier fallo y se detiene la secuencia.

La ordenación pasa a herramienta versionada: --duration-order-from en el runner oficial, limitada a regresión funcional paralela, valida/copia su histórico y pasa el plugin por argv explícito. Mantiene selección y orden interno por archivo; exige recibos de todos los workers con el mismo digest de nodeids. Seis controles unitarios/CLI PASS y prueba real de plugin con22casos/dos workers PASS; ambos recibos coinciden. No aumenta workers ni modifica allowlist/capacidad/snapshots/secretos. scripts/run_local_ci.py no forma parte de las623fuentes del producto Docker, que permanecen intactas. Aplicar en la próxima ejecución integrada, no alterar el C actualmente congelado.

## Auditoría terminal de la comparativa

Referencia11PASS, candidata12PASS (incluido flujo completo1500), repetición11PASS; cero fallos/SKIP. [Recibo terminal](evidencias/test-optimization-terminal-audit-20261019.json):4310fuentes/instrumentos congelados sin cambios,623fuentes del producto iguales al Docker aceptado, PostgreSQL real, plugins por argv y recibos de carga, contenedores propios ausentes tras limpieza, sin OOM y avisos Telegram enviados. Refresco AST al corteb571bcb, sin actualización semántica documental completa.

| Caso, duración call | Referencia | Candidata | Repetición |
| --- | ---: | ---: | ---: |
| Historia30 | 16,116s | 8,269s | 8,293s |
| Historia1280 | 397,250s | 9,713s | 10,450s |
| Flujo nativo completo1500 | No repetido | 814,962s | No repetido |

La referencia comenzó con C concurrente; C se detuvo antes de la candidata. Presupuestos auxiliares iguales no eliminan este cambio de competencia del host. No atribuir causalmente todos los porcentajes al código ni extrapolar a batería completa o request p95. El caso1500 previo tardó1652,45s con otro presupuesto/historia de proceso: comparación observacional.

Los tres controles pequeños de lotes consumieron más consultas (2643/6613/7488 frente a2443/6341/7216) y no mejoraron consistentemente el tiempo. Por ello el helper conserva batched=False por defecto; sólo el flujo grande usa el servicio nativo de cuatro páginas, manteniendo1511inspecciones y todos los asserts. La preparación masiva de históricos conserva los datos y la paridad completa con el lector de referencia. Revisado el diff: no se eliminan casos ni aserciones de producto.

Integrar estas mejoras de pruebas y la ordenación explícita por duración; después ejecutar una única regresión común funcional/capacidad secuencial, sin comparativas auxiliares en paralelo. La ordenación necesita recibos reales de ambos workers; una variable de entorno no sirve como prueba de aplicación. C y Alpha siguen pendientes hasta auditar sus siete requisitos.

## Resultado de la integración común

[Acta10](actas/10-entrega-tecnica-local-alpha-20261020.md):3358funcionales+298capacidad,3526PASS+4subpruebas/130SKIP/0fallos. Ordenación por argv aplicada y dos recibos3358/digestidéntico comprobados; sin comparativa auxiliar concurrente.

| Etapa pytest | GS01anterior | Cfinal | Reducción observada |
| --- | ---: | ---: | ---: |
| Funcional | 10019,074s | 8746,145s | 12,7% |
| Capacidad | 3105,952s | 3102,344s | Sin cambio material |
| Suma | 13125,026s | 11848,489s | 9,7% /21min17s |

Diecinueve casos adicionales respecto aGS01; comparación observacional, no ensayo causal aislado. No prometer97%menos en batería por la reducción de un fixture. No nueva métrica HTTP; recursos/carga/historia de proceso limitan extrapolaciones. La capacidad serial permanece intacta. Cambios sólo de pruebas/herramienta,623fuentes producto idénticas.
