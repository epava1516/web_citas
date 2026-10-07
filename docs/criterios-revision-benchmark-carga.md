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

## Perfil por regla y verificación concurrente previa

Ampliación acordada en conversación lateral el 2026-10-07. Incorporar al próximo ciclo compatible con las fuentes congeladas; no modificar una ejecución activa ni reinterpretar evidencias anteriores. Una duración medida dentro de validaciones identifica un contribuyente, pero no atribuye automáticamente ese tiempo a reglas concretas ni constituye una partición exclusiva del request.

Obtener primero un perfil focalizado de10000 candidatos. Por regla registrar:

- `calls`, `inclusive_time`, `exclusive_time`, `mean_exclusive_time` y `max_exclusive_time`; p95 por llamada es opcional cuando la muestra lo permita.
- Identidad de las llamadas hijas instrumentadas y tiempo descontado para calcular el exclusivo. Describir el alcance: exclusivo respecto a hijos instrumentados, no respecto a todo el trabajo interno no observado.
- Método de cálculo que evite descontar dos veces descendientes anidados. Si hay concurrencia o intervalos solapados, explicar su tratamiento; no restar duraciones indiscriminadamente.
- Overhead estimado de instrumentación y método de estimación, preferentemente mediante comparación focalizada equivalente con/sin profiler. Si no puede estimarse fiablemente, declarar `not_measured`; no inventar una corrección ni descontarla del resultado observado.
- Clave completa de dependencia de cualquier reutilización intra-request y comprobaciones de vigencia/revocación preservadas.

Clasificar las reglas dominantes según dependencias reales: visitante/request, anunciante, anuncio, combinación anunciante/tipo y versión documental, u otras que determine el código. Dos evaluaciones solo pueden compartir resultado cuando coinciden todas sus dependencias relevantes. La etiqueta genérica representación/documentación no acredita invariancia. La reutilización permanece dentro del request y conserva las garantías vigentes ante cambios de autoridad, restricciones, expiración y revocación; no introducir caché entre peticiones ni proyección persistida sin un diseño de consistencia expresamente verificado.

Secuencia de revisión:

1. Perfil focalizado10000: localizar reglas dominantes por tiempos inclusivos y exclusivos, con límites y overhead documentados.
2. Optimizar las reglas dominantes manteniendo semántica; ejecutar gates funcionales pertinentes y negativas significativas de vigencia/revocación.
3. Repetir la matriz comparable100/1000/10000 para verificar mejora y escalabilidad; mantener separadas mediciones instrumentadas y latencia operativa sin profiler.
4. Prueba concurrente corta de30–120s como filtro diagnóstico de saturación evidente, con duración, carga, mezcla y criterios prefijados. Verificar generador y contabilidad; observar latencia, errores y colas/CPU/DB solo donde se midan. Registrar métricas ausentes y justificación concreta para continuar o corregir.
5. Si esa prueba resulta razonable conforme a sus criterios previos, ejecutar el escenario contractual20rps/900s con los requisitos y umbrales ya fijados. Una latencia aislada<1s no acredita20rps sostenidos.

La prueba corta no sustituye los900s, no cambia p95<800ms/errores<1%, no acredita capacidad contractual y no exige aceptar un nuevo SLO arbitrario. El benchmark anterior declarado INVALID conserva ese veredicto tras cualquier optimización posterior. Actualizar seguimiento con fuente, evidencia y resultados realmente observados, sin aumentos automáticos de avance ni aceptación de fase.

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
