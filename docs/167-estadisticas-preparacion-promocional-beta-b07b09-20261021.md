# B07–B09 — Estadísticas tras la preparación promocional

Estado: diagnóstico terminal auditado; tres estimaciones obsoletas detectadas, sin cambio de producto ni aceptación de capacidad. Ocho de18cerrados y TCP112359FAIL vigente.

164observa variación de CPUbackend en búsqueda sin causa aislada. El generador actual analiza cinco tablas después del bulk, pero crea también usuarios/personas/representaciones/verificaciones/categorías y después2000pedidos/derechos, y reconstruye estado público. No hay ANALYZE explícito final de estas tablas en la preparación promocional. Autovacuum puede actualizar algunas: no afirmar que están obsoletas sin medir.

La [documentación PostgreSQL17](https://www.postgresql.org/docs/17/populate.html#POPULATE-ANALYZE) recomienda ANALYZE tras cambios sustanciales de distribución. Aquí sólo se estudia esa operación en la DB sintética propia; no adoptar las otras opciones de quitar constraints/índices, cambiar WAL, memoria o autovacuum. La correctiva histórica del generador ya se conserva y no se reescribe como una mejora nueva del producto.

## Protocolo previo

beta_post_fixture_statistics.py:1000perfiles/200derechos por servicios sintéticos reales, publicación reconstruida/cero pendientes. Capturar recuentos y SHA256 de filas ordenadas sin persistir datos, estimaciones reltuples y metadata de pg_stat_all_tables. Separar estimaciones, contadores y cardinalidades reales; los contadores pueden actualizarse con retraso.

Dos etapas en orden fijo: preparación actual y ANALYZE explícito posterior de coreUser/Person/RepresentationAction/VerificationCheck, PromotionOrder/Entitlement, PublicationState y relación Revision.categories. No tocar filas de dominio. Ambas etapas usan backend nuevo por ruta,1warm+6controles de listadoES/búsquedaEN:28HTTPClient, bytes/IDs/count1000/página24/patrocinio idénticos. CPUthread y CPU real de backend propio identificado por namespace/cgroup/startticks. Sin wrappers/profiler en relojes.

Después de cada lectura, fuera del reloj, capturar pg_prepared_statements con hash de SQL/familia y contadores generic/custom, sin SQL/params. Metadata de tablas antes/después de cada etapa. Verificar los mismos checksums de dominio en ambas y estimaciones finales de las ocho tablas dentro de2%o1fila. No forzar obsolescencia ni desactivar autovacuum para obtener un resultado.

Es diagnóstico de preparación en orden fijo: calentamiento, tiempo y trabajo de fondo no están aislados, y no se acredita mejora causal de HTTP. Si las estimaciones iniciales ya son correctas, conservar ese resultado. Antes de cualquier cambio del builder/capacidad se necesita revisar qué demuestra, y conservar antiguoFAIL como válido: no reinterpretarlo ni acreditar SLO por esta muestra.

Ruff/grafo dirigido/freeze; PostgreSQL real,1worker/timeout900s, sin otra batería. JUnit/artefacto/huellasruntime726/identidades/cleanup/PIDs/Telegram auditados antes de editar. Sin nuevoROI de candidatos rechazados ni reducción de umbrales.

## Resultado auditado

150930-c255683e:1PASS/0FAIL/0SKIP,131,35spytest sin warnings;28HTTPClient1000/200. [Auditoría](evidencias/b07-post-fixture-statistics-20261021-150930-c255683e-audit.json):artefactoSHA/JUnit,726runtimeintactos/freeze/identidadesCPUbackend/cleanup/PIDs/Telegramterminal confirmados, auditoría enviada.

Tres estimaciones iniciales superan el margen2%: PromotionOrder y PromotionEntitlement121frente200filas reales; PublicationState−1frente1002. El estado público contiene también las dos filas no publicadas de la semilla; count1000 es la población pública, no el total de la tabla. Las otras cinco tablas objetivo ya tenían estimaciones correctas. ANALYZE de las ocho tarda32,544ms y deja estimaciones dentro del margen. Las once huellas de filas de dominio permanecen iguales en ambas etapas.

Medianas observadas antes/después: listado213,550/169,868ms,CPUapp123,917/112,529ms,CPUbackend43,935/38,359ms; búsqueda215,910/205,391ms,CPUapp141,096/132,584ms,CPUbackend51,290/49,999ms. Orden fijo, variación/cachés/trabajo de fondo no aislados: no ahorro causal de producto ni nuevoSLO. Contadores prepared tras seislecturas:generic44/custom75y17statements, mismo patrón en cuatro backends. La transición hacia planes genéricos aparece sin cambiar política; no prueba que causara la variación164.

Decisión: preparar finalización explícita de estadísticas después de la preparación promocional completa y refresh, sólo en DBs sintéticas propias. Requiere pruebas de alcance/filas/metadata y calibración funcional antes de un nuevo corto. No cambiar apps, permisos, cuotas, índices, constraints, política de planes o SLO; no declarar INVALID el antiguoTCPFAIL ni llamar a esta preparación optimización del runtime. La implementación y sus gates se documentarán aparte. Ocho de18cerrados.
