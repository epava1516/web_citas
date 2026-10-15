# Hidratación genérica integrada: descartada

La caché de utility ya estaba corregida. Se añadió temporalmente una opción `generic_page_plan=False` al helper y se activó sólo en el brazo experimental. Captura/configuración/restauración de plan_cache_mode se integraron en las mismas tres sentencias que gestionan jit/join_collapse_limit: sin transacciones ni roundtrips adicionales. No se activó por defecto ni se ejecutó una carga limpia con esta opción.

## Ejecución conjunta: preparación interrumpida

`20261015-201228-c483dd66`: ocho controles de ámbito/restauración pasan, incluidos error SQL, transacción heredada con force_custom_plan y alcance cerrado. Después, la preparación de10k sintéticos queda en una consulta nativa de `publicly_visible → unresolved_matches.exists`, antes de activar ningún brazo. Dos snapshots del PG propio observaron SELECT activo106.79s/129.49s, sin wait_event, texto truncado a1023bytes. No se conservan SQL ni parámetros.

`py-spy0.4.1`, instalado mediante uv tool aislado (lock y entorno de aplicación intactos), confirma el stack en `synthetic_load_dataset.populate:78`, fuera del candidato. [Stack](cr09-integrated-generic-preparacion-stack-20261015.json). Codex interrumpió el runner propio por PID/startticks verificados y comprobó fuentes/limpieza. [Terminal](cr09-integrated-generic-preparacion-terminal-20261015.json):8PASS parciales y diagnóstico interrumpido; no sumar como9PASS ni afirmar causa resuelta. La sensibilidad a la preparación conjunta queda pendiente, no se borra por ejecutar luego aislado.

## Comparación aislada

`20261015-201922-f147caaa`: **1PASS120.87s**,180peticiones reales ES/EN, tres bloques alternos, conexión nueva por brazo, sin calentamiento ni primeras peticiones descartadas. Igualdad de HTML/target firmado, status200/no-store y restauraciónauto después de cada petición. Fuentes y limpieza independientes. [Recibo y observaciones](cr09-hidratacion-generica-integrada-cpu-terminal-20261015.json).

| CPU PG media por petición | Automático | Genérico hidratación |
|---|---:|---:|
| Primeras6 por conexión |63.333ms|60.000ms|
| Peticiones7–18 |39.722ms|39.167ms|
| Peticiones19–30 |32.222ms|31.111ms|
| Todas30 |41.444ms|40.111ms|

| Bloque, CPU PG media | Automático | Genérico hidratación |
|---|---:|---:|
|0|39.333ms|36.667ms|
|1|43.667ms|43.000ms|
|2|41.333ms|40.667ms|

Primeras6 del bloque2 empeoran61.667→66.667ms; rangos se solapan, cuantización100Hz. Mayor CPU inicial de Python en primer brazo sigue siendo un sesgo, no atribuir diferencia de CPU app a la política. Ambos terminan con42planes, frente82/100 del experimento anterior: la corrección de utility evita esa ocupación. Ejecuciones finales genéricas/custom450/200 frente505/145. Cambiar la política transforma ejecuciones de planes, pero no aporta ahorro material y consistente de CPU suficiente para justificar complejidad ni otra carga.

**Decisión: rechazar y retirar la opción experimental del producto.** Se restauraron exactamente desde HEAD los tres archivos modificados, después de verificar el terminal y guardar el [parche del prototipo](cr09-hidratacion-generica-integrada-prototipo-20261015.patch). Base `cdc428f` más ese parche reproduce las fuentes medidas; conservar hashes del runner. No reset/stash ni trabajo ajeno afectado.

Producto queda en política automática, umbral inmediato y SELECT-only. Último p95 limpio0.961136843s FAIL, sin nueva carga/15min/N3. Próxima investigación acotada: explicar el plan nativo que atascó la preparación conjunta y sus dependencias, con límites diagnósticos y EXPLAIN separado; no confundir con detección de duplicados FAISS ni con el p95 ya medido. Las pausas GC siguen registradas, sin política modificada. Objetivo íntegro CR09→CR10→GS01→BF/BB→C activo.
