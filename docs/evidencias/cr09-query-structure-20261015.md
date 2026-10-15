# Reutilización acotada de estructura de consultas, sin resultados almacenados

Experimento separado en web_modelos_cr09_query_structure_20261015, base61c2353. El prototipo dirty anterior no se incorpora. publication_query conserva la misma anotación sobre la consulta del caller; sólo separa la construcción de expresiones SQL en un helperLRU8porversiondocumento. No almacena QuerySets evaluados, personas, documentos, decisiones ni resultados. Cada contexto sigue consultando el documento vigente, cada annotate resuelve copias y cada ejecución lee valores actuales. Se mantiene conteo/selección, snapshot, dirty y guardiafinal. No cambia dependenciascongeladas/cuotas/GC/PGpolíticas.

Referencia técnica: fuente instaladaDjango5.2.17 BaseExpression.resolve_expression copia la expresión; Subquery.copy clona Query; Query.resolve_expression clona y resuelve aliases para el caller. [Fuente oficialDjango5.2](https://github.com/django/django/blob/stable/5.2.x/django/db/models/expressions.py). Sólo las expresiones concretas actuales, sin funciones custommutables oparámetrosruntime adicionales. No confundir reutilizar estructura con el caché de resultados de [QuerySet evaluado](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#when-querysets-are-evaluated).

Run221542-4b2005b5, **1PASS108.51s**, [recibo](cr09-query-structure-comparison-terminal-20261015.json). PostgreSQL/Redispropios, sintéticos10k, límites habituales. Se extrae publication_queryoriginal de61c2353 como referencia.16combinaciones dequeryshape/documentoversion incluidonull producen SQLyparamsexactos.6casos delector completo,3bloques alternos y3repeticiones/brazo, caché vacía y conexión nueva al inicio de cada brazo:108lecturas, count eIDsordenados iguales. Incluyeconstrucción,SQL,cobertura,validacióndesconocidos e hidratación/guardia. Fuente congelada idéntica, root/child/temporal/containerspropios ausentes yMainPID0/ControlGroupvacío.

|Mediawall aislada, noHTTP/p95|Original|EstructuraLRU|
|---|---:|---:|
|Listado limpio|236.60ms|206.70ms|
|Búsqueda limpia|217.07ms|231.65ms|
|Sin resultados limpio|67.14ms|58.77ms|
|Listado dirty1|346.18ms|302.50ms|
|Búsqueda dirty1|416.82ms|340.82ms|
|Sin resultados dirty1|103.62ms|88.31ms|

Medias porbloqueconjunto original→estructura:245.83→209.00ms,232.32→198.25ms,215.57→207.12ms. Beneficio conjunto en3bloques, pero búsqueda limpia empeora; no uniforme ni prueba bajo concurrencia. Controles de frescura/aislamiento/rotación/privacidad/concurrencia en curso, aún no integración. Sólo si satisfacen garantías cabría medir una carga limpia; último p95vigente1.118772FAIL, CR09/N3 abiertos.

## Verificación e integración local

[Controles](cr09-query-structure-controls-terminal-20261015.json):23PASS236.07s, contexto/frescura/dependencias/proyección/paginaciónESEN/expiración/carrera/esupresión. Testnuevo de rotación inicialmenteomitíalanguage; se fortalecefixture de sustituciónreal conidiomacorrecto/desactivación/restauración deactivos,2PASS50.35s adicionales (mismos2casos, no25únicos). Producto idéntico en ambas ejecuciones; fuentes/limpieza verificadosindependientemente. Resoluciónconcurrente4threads no mezclaSQL/params; anotacionesaplicadas ysubquery independientes deplantilla; límite8verificado. Integrado localmente bf2f13f, sóloestructuraconsultas ytests; sinprototipodirty. Sigueuna carga corta limpia única yrepetir sóloPASS.
