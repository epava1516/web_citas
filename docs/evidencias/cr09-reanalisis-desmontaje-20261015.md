# Reanálisis del estado actual y decisión acotada

Corte documental435bfeb; producto f9f404d. Solicitud: actualizar grafo, descomponer, analizar e investigar de nuevo. Este documento contrasta evidencia existente; **no hay nueva medición ni aceptación CR09/N3**. El corto limpio vigente es214838-7c455fc1, FAIL. Las referencias temporales de documentos anteriores describen sus respectivos cortes, no reemplazan este resultado.

## Estado y comparación conservada

|Métrica, mismas condiciones nominales|392c2c8 anterior|f9f404d vigente|
|---|---:|---:|
|p95 HTTP completo|0.919814s|1.118772s FAIL|
|p50 HTTP completo|0.262638s|0.234972s|
|p95 servicio Gunicorn|0.314390s|0.313042s|
|Tarea real de foto, wall|10.094089s|0.971466s|
|Peticiones >=0.8s|79|108|
|Completadas finales / errores / timeouts|1200 / 0 / 0|1200 / 0 / 0|

Un run por versión no acredita reproducibilidad ni causalidad del cambio de p95. La mejora aislada del selector se contrastó en tres tandas alternas y19controles funcionales, por eso se conserva por beneficio de medios. [Recibo limpio y limpieza](cr09-media-exists-http-terminal-20261015.json); [comparación y cohortes](cr09-media-exists-http-20261015.md). Python3.12.15, Django5.2.17, Gunicorn23.0.0, PostgreSQL17.11;4workers sync,20rps,60s,10k, Celery2+Beat y subida, recursos propios acotados. Sin perfiladores en el limpio.

El umbral sigue siendo p95<0.8s. La distancia del percentil actual al umbral es0.318772s, aproximadamente28.49% del valor actual; **no promete una reducción uniforme ni que una microoptimización de ese porcentaje baste**. Con1200casos y nearest-rank1140, deben quedar como máximo60casos en>=0.8s: hoy108; al menos48de esos casos tendrían que cruzar el umbral sin introducir otros lentos. No cambiar denominador, arranque, mezcla ni error budget.

## Desmontaje del recorrido

1. Generador programa y emite la petición; transporte, aceptación y parseo preceden WSGI. Los1200casos completan; eso no demuestra ausencia de espera.
2. Middleware, ruta y formulario producen candidatos con filtros/corte temporal exactos. Sólo candidatos originales sin filtros adicionales admiten proyección; clones y transacciones heredadas conservan camino general.
3. state_page abre snapshot propio REPEATABLE READ READ ONLY. Lee marcas dirty, limita1000y valida nativamente como máximo48desconocidos; exceso vuelve al camino nativo. No se validan10kobjetos Python en cada request.
4. La condición actual `complete = not dirty and all_state_current(...)` provoca que **una única marca dirty desactive la proyección compacta para conteo/selección del listado**, aunque el resto de estados siga vigente. Es una condición del diseño local; la necesidad de preservar visibilidad no obliga por sí sola a esa degradación global.
5. Se calcula población y página de24; se hidrata y comprueba visibilidad nativa de los seleccionados. Un fallo de guardia marca y deriva al camino seguro. Después presentación, render y transporte hasta el cliente.
6. La subida acepta bytes y devuelve respuesta; Celery procesa foto después, genera cambios y refrescos de publicación. Fin HTTP de subida y fin de proceso de foto son eventos distintos. Reducir el segundo no garantiza reducir el percentil de otras peticiones.

Fuentes directas: publication_state.py state_page/_state_page/all_state_current; discovery.py candidates; mediafiles/services.py detect_matches; tests/test_publication_projection.py. No eliminar invalidación, controles de derechos ni guardia final para hacer pasar el reloj.

## Qué demuestra la evidencia y qué no

|Pregunta|Evidencia actual|Límite|
|---|---|---|
|¿Dónde aparecen las lentas actuales?|91emitidas0–5s y17entre5–10s; ninguna después|No equivale a estabilidad de15min|
|¿Servicio o espera previa?|Limpio: media cliente menos servicio0.858548s al inicio frente0.031981s entre15–60s|Ese residuo no es exclusivamente cola de socket|
|¿Había workers ausentes?|Diagnóstico ingress anterior: los4atienden en0.102s;98.51% de espera previa de62lentas solapa4spansWSGI activos|Observadores y versión anterior; no convertir p95instrumentado0.802719en mejora limpia|
|¿Hay SQL de fondo caro?|Selector real de medios identificado y corregido; taskreal10.094→0.971s|El p95sigue fallando; no era explicación suficiente|
|¿Existe amplificación por dirty?|Código desactiva proyección; diagnóstico identifica SQLde ruta general precisamente durante dirty|Correlación y mecanismo plausible, no reparto causal completo|
|¿Es hardware o compilación Python?|No hay prueba actual de que ampliar CPU o usarCython resuelva el atasco|Portátil variaba perfil energético al enchufarlo; no atribuir diferencias al código|

[Diagnóstico emparejado y sus límites](cr09-ingress-diagnostico-20261015.md). SQLwall, GCwall y CPU se solapan; no sumarlos ni restar percentiles distintos. Afinidad y cuotas conservadas, sin servicios normales/producción ni datos reales.

## Alternativa investigada, todavía no aceptada

En worktree aislado web_modelos_cr09_dirty_projection_20261015, base85a5abe, hay un prototipo sin pruebas ni integración: combinar estados limpios con filas dirty validadas nativamente. Sólo con cobertura/versionado completo, snapshot propio y candidatos originales admitidos. Conjuntos disjuntos, exclusión dirty del estado almacenado, metadatos actuales para el brazo nativo, ranking/fecha/ID y count exactos; guardia final y límites intactos.

La documentación oficial permite el mecanismo, no demuestra esta implementación: [Django5.2 union](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#union) exige columnas compatibles y restringe operaciones posteriores a selección de columnas, orden, conteo y límites; [PostgreSQL17 aislamiento](https://www.postgresql.org/docs/17/transaction-iso.html#XACT-REPEATABLE-READ) explica el snapshot común. No reutilizar esta optimización en una transacción heredada de aislamiento desconocido.

Hallazgo adicional de revisión: el test existente `test_projection_is_closed_for_filters_clones_dirty_stale_and_inherited_transactions` exige actualmente ruta nativa ante dirty. El prototipo cambia deliberadamente ese contrato interno. No basta sustituir la expectativa por projection: debe acreditarse equivalencia de resultados, también negativos, antes de revisar la aserción de ruta. Además sigue construyendo y compilando parcialmente la población general antes del brazo compacto; no asumir ahorro total por leer el diff.

Prueba finita necesaria antes de cualquier integración: referencia actual frente a prototipo sobre el mismo PostgreSQL propio y datos sintéticos; count, IDs ordenados y páginas1/2/última, ES/EN, búsqueda sin resultados y texto que entra/sale, fechas empatadas/nulas, visible→oculto y oculto→visible, expiración y revocación, cobertura incompleta/versionada, límites y transacción heredada. Conservar caso de escritura/refresco concurrentes y guardia. Primero equivalencia; después coste wall/CPU en tandas alternas incluyendo hidratación/guardia, sin presentarlo como p95. Descartar si falla semántica o beneficio. Sólo tras eso cabría una carga limpia única y repetición siPASS.

## Decisión

Mantener f9f404d y su FAIL sin repetirlo automáticamente. La hipótesis prioritaria es la amplificación transitoria del trabajo de listado durante escrituras, seguida de espera acumulada; no hay todavía causa única cuantificada ni solución aceptada. La siguiente intervención justificable es verificar la alternativa aislada con el contraste anterior, no barridos de workers/GC/hardware ni eliminación de controles legales. Se conserva el prototipo separado y sin atribuirle resultados.

CR09 sigue pendiente de SLO corto/completo/reproducibilidad, trazabilidad de criterios y evidencia aplicable a una versión final común. Los4bloques históricos y recuperaciones no sustituyen N3 común tras cambios nuevos. Después siguen CR10, GS01, BF/BB yC. La excepción provisional de exportaciones MOD09 no modifica el requisito del directorio.

## Grafo y revisión documental

Grafo actualizado al corte435bfeb antes de cerrar este análisis:11167nodos/44404aristas/471comunidades, cero endpoints colgantes tras normalización. Un lote semántico adicional en el agente nativo existente graph_update_docs_1:5docs,22nodos/23aristas; tokens no reportados, consumo histórico conservado. La librería exige contadores numéricos: ceros sólo como compatibilidad interna, recibo mantiene consumo desconocido. Consulta amplia1035nodos,59mostrados, no exhaustiva; lectura directa completó análisis. 216archivos sin extractor,2SQLsin parser y nodos legacy no atribuibles conservados explícitamente. Grafo para navegación, no perfil temporal. El documento presente es evidencia posterior al corte del grafo.
