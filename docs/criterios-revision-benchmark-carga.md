# Criterios de revisión del benchmark de carga

Acordados con el usuario en conversación lateral el 2026-10-07. Complementan la revisión de evidencias; no sustituyen el contrato vigente, no modifican una ejecución activa y no aceptan CR09 ni aumentan su porcentaje por sí mismos. La cola operativa permanece en docs/17-seguimiento-desarrollo.md.

El escenario contractual permanece: 10.000 anuncios sintéticos, PostgreSQL, 20 peticiones dinámicas/s durante 900 s, mezcla de listados/fichas/búsquedas y cargas simultáneas limitadas, p95 <800 ms y errores inesperados <1 %. Registrar la mezcla real; no adoptar automáticamente 50/25/20/5 ni incluir uploads dentro de las 18.000 peticiones dinámicas si el escenario vigente los define aparte. No publicar, contratar proveedores ni utilizar datos reales.

## Corrección y diagnóstico

Preservar exactamente publicación, privacidad, representación, permisos, documentación, visibilidad, filtros, orden promocional, recuento y paginación. Favorecer condiciones SQL equivalentes cuando sea posible. No recortar candidatos antes de validar ni cambiar silenciosamente a navegación por cursor.

Comparar antes/después con el mismo dataset, seed, entorno, mezcla y nivel de instrumentación. Registrar estado frío/caliente por separado. Usar muestras 10/100/1.000/10.000 para estudiar escalabilidad cuando los gates y costes permitan; reutilizar evidencia válida y marcar medidas ausentes como no medidas. Un timeout es evidencia de fallo, no una latencia completada comparable.

La matriz debe distinguir consultas/request, crecimiento de consultas por candidato, Listings materializados, objetos relacionados materializados, validaciones residuales, tiempo SQL, tiempo total y, si se instrumenta explícitamente, tiempo de validación y renderizado. No interpretar total menos SQL como tiempo de validación Python. El número de consultas no tiene un límite arbitrario de 15 o 20: revisar su crecimiento y justificar los lotes necesarios.

Medir el coste de materialización después de reducir N+1; no asumir que impedirá necesariamente el objetivo contractual. Overfetch no garantiza trabajo acotado si el rechazo residual es alto y no resuelve por sí mismo recuentos exactos. Una proyección persistente de elegibilidad requiere dependencias completas e invalidación o actualización que evite exposición tras revocaciones, restricciones y expiraciones; no introducirla sin esas garantías y pruebas.

## Checkpoint de atribución del coste restante

Ampliación acordada en conversación lateral el 2026-10-07. Aplicar a la próxima medición diagnóstica compatible con las fuentes congeladas y gates vigentes, sin interferir en un ensayo activo. Las observaciones anteriores acreditan reducción fuerte del N+1 hasta100 candidatos y listados HTTP de10000 candidatos de aproximadamente34–39s; estas muestras no son directamente equivalentes. No atribuyen todavía la mayor parte del coste a SQL, materialización, validación o renderizado.

Antes de elegir otro refactor de backend o repetir la carga contractual como diagnóstico del coste, obtener una matriz comparable100/1000/10000 con el mismo entorno, fixture/seed, rutas, estado de cachés y nivel de instrumentación. Reutilizar evidencia previa solo para las métricas realmente medidas. No incorporar columnas nuevas retrospectivamente ni convertir un timeout en duración completada. Una corrección independiente del generador puede avanzar sin atribuirle mejoras del backend.

| Candidatos | Queries | SQL acumulado | Listings materializados | Relaciones materializadas | Validaciones Python | Render/serialización | Total request |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | | | | | | | |
| 1000 | | | | | | | |
| 10000 | | | | | | | |

Medir dos capas: tiempo end-to-end del request y eventos internos instrumentados. Registrar ejecución de SQL, materialización de Listings y relaciones por tipo/procedencia, número de validaciones y, cuando se mida directamente, duración de validación y render/serialización. Definir el alcance de cada contador: objetos creados no equivalen necesariamente a entidades únicas ni a filas SQL. Marcar métricas ausentes como `not_measured`.

La evaluación lazy del ORM puede ejecutar SQL durante validación, prefetch o renderizado. Registrar alcance y posibles solapamientos de los temporizadores; no sumar intervalos anidados como si fueran fases exclusivas ni exigir que su suma coincida con el total. Tiempo SQL acumulado debe indicar método y alcance, incluida la ejecución/fetch que realmente observe el instrumento. Total menos SQL no equivale a tiempo de validación ni permite atribuir por sí solo coste a Python.

Presentar las consultas dominantes agrupadas por patrón normalizado y ordenadas por tiempo acumulado, con `query_pattern`, `calls`, `total_time` y `mean_time`. No persistir valores de usuarios, IDs, teléfonos, textos ni parámetros; redactar también literales SQL, no solo parámetros separados. Definir normalización, unidades y población. Distinguir `rows_returned`, `rows_affected` y `rows_examined`/`rows_scanned`; publicar cada métrica solo si su significado y medición son fiables. No inferirlas de objetos ORM o de un `rowcount` ambiguo. Una métrica no disponible queda `not_measured`.

Si SQL domina, analizar por separado las consultas relevantes con `EXPLAIN (ANALYZE, BUFFERS)` en el PostgreSQL sintético aislado. ANALYZE ejecuta la consulta: limitar este diagnóstico a las lecturas afectadas, sin mutaciones ni datos reales. Registrar fuente, consulta/plan redactados, entorno y estado de cachés; no mezclar su duración con el benchmark normal ni extrapolar filas de nodos del plan sin explicar su semántica. `pg_stat_statements` es información adicional si ya está disponible, con alcance/deltas que eviten atribuir actividad ajena; instalarlo o cambiar configuración no es requisito de este checkpoint.

Decidir el próximo cambio según evidencia directa:

- Consultas crecientes: localizar accesos repetidos y distinguir N+1 de consultas justificadas por lotes.
- Tiempo SQL dominante: revisar planes, EXISTS/subconsultas correlacionadas, joins, ordenación e índices. Pocas consultas no implican poco trabajo de PostgreSQL.
- SQL barato y materialización dominante: reducir filas y relaciones materializadas, preservando elegibilidad, orden y recuentos.
- Validaciones dominantes: reformularlas o llevar condiciones equivalentes a SQL, con pruebas de equivalencia.
- Render/serialización dominante: corregir esa capa.

No elegir paginación anticipada, proyección de elegibilidad o escalado de infraestructura únicamente por el número de objetos o de consultas. Documentar la atribución observada, limitaciones y evidencia que justifica el refactor. La carga contractual conserva sus requisitos y debe verificarse después de las correcciones pertinentes; este checkpoint no la sustituye ni acredita capacidad por sí mismo.

## Validez del experimento

Congelar antes de la próxima ejecución: fuente, dataset/seed, entorno y recursos, mezcla real, estado frío/caliente, instrumentación, timeout por petición y política de errores. Registrar workers, versiones y límites relevantes. No alterar retrospectivamente criterios tras observar resultados ni reinterpretar una ejecución previa como si incorporase este marco.

La carga debe tener planificación open-loop de 20 peticiones dinámicas/s: 18.000 programadas durante los 900 s. Registrar subidas limitadas aparte cuando corresponda. Distinguir tasa solicitada, tasa emitida y throughput completado; ninguna sustituye a las otras.

Antes de ejecutar deben quedar fijados numéricamente y justificados:

- Umbrales admisibles p95/p99/máximo de demora del generador.
- Porcentaje máximo de peticiones no emitidas sobre programadas.
- Drain/grace period fijo tras los 900 s y tratamiento de pendientes al concluir.

Este documento no inventa valores para esos tres parámetros: deben concretarse en la configuración o manifiesto revisable de la siguiente prueba, antes de iniciarla. Su ausencia impide emitir un PASS conforme a este marco.

Para cada petición registrar instantes con reloj monotónico: programada, emitida y respuesta o terminación. Demora del generador = emisión menos programación; latencia observable = terminación menos emisión; demora total = terminación menos programación. Precisar qué significa emisión en el cliente y si incluye espera en el executor/conexiones. Informar distribución y población utilizadas para percentiles, errores y timeouts; no ocultar fallos mediante percentiles exclusivos de respuestas exitosas.

Mantener identidades contables verificables, por población:

```text
programadas = emitidas + no_emitidas
emitidas = exitosas + fallidas + pendientes_al_cierre
fallidas = timeouts + otros_errores
```

Timeouts son subconjunto de fallidas. Conservar el estado al cierre de la ventana y el estado final tras el drain, sin doble conteo; cualquier pendiente final recibe clasificación explícita según la política prefijada. Declarar denominadores y umbrales estrictos del contrato. Incumplir límites de emisión/demora invalida el experimento y no debe confundirse con capacidad insuficiente demostrada del backend.

## Informe y veredictos

Informar solicitudes programadas, emitidas, exitosas, fallidas, timeouts, no emitidas y pendientes; tasas y distribución temporal que permitan detectar ráfagas de recuperación. Incluir p50/p90/p95/p99/máximo y demora del generador. Registrar CPU de aplicación/DB, conexiones, waits, locks e I/O cuando se midan, identificando métricas ausentes y costes de instrumentación.

Separar RSS baseline/pico/final de workers y PostgreSQL, número de workers y alcance/método de muestreo. RSS de proceso no es memoria/request. CPU/request o allocations/request solo se declaran con instrumentación que permita atribuirlas; no deducirlas del pico global.

- INVALID: escenario o carga aplicada incumplen las condiciones de validez; no emitir conclusión de cumplimiento contractual.
- FAIL: experimento válido que incumple p95 o tasa de errores contractual.
- PASS: experimento válido que cumple ambos objetivos estrictos.

Corrección funcional se verifica por separado y es condición para aceptar una optimización. PASS solo acredita este escenario, entorno, mezcla y estado. No prueba producción, capacidad máxima, equivalencia de tráfico con otro portal ni aceptación integral de CR09. La búsqueda posterior de saturación es un experimento distinto.

Elegir el siguiente cambio según evidencia: consultas repetidas, materialización/CPU, SQL/planes/índices/contención o concurrencia/colas. No escalar infraestructura de antemano para compensar el multiplicador de consultas.
