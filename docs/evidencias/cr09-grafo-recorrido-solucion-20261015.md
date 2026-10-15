# Grafo actualizado, recorrido y candidata para el transitorio

Corte de producto `c2114cdfddb333c88ef6e526c6bd22b6d06c3e09`. Orden solicitado: actualización del grafo, lectura del recorrido, investigación de solución. Esta revisión no ejecuta una carga ni acredita una mejora nueva de p95. CR09/N3 permanecen abiertos.

## Actualización del grafo

`graphify update . --no-cluster`, extracción semántica nativa de los 41 Markdown cambiados de docs, validación de rutas/líneas/endpoints y `graphify cluster-only . --no-viz --no-label`. Copia anterior y recibos locales en `artifacts/graphify-update-c2114cd/`; salidas consultables en `graphify-out/graph.json` y `GRAPH_REPORT.md`.

| Corte del mapa | Nodos | Aristas |
|---|---:|---:|
| Anterior | 10650 | — |
| Actualización estructural, antes del merge semántico | 10971 | 45413 |
| Grafo final simple, semántica incorporada | 11094 | 44212 |

Se añaden 123 nodos y 67 aristas semánticas con procedencia. Los recuentos de aristas previos y posteriores al grafo simple no son equivalentes: el merge/export de NetworkX conserva una arista por par; no usar este mapa como inventario exhaustivo de todas las relaciones paralelas. Salud final: cero extremos ausentes/colgantes, 130 autorrelaciones; 163 nodos semánticos anteriores sin fuente conservados y marcados `legacy_unattributed`, no usados como prueba. Dos capturas SQL históricas sin parser `tree_sitter_sql`; 216 archivos sin extractor clasificado. No se afirma cobertura semántica de todo el corpus: se renovaron estos 41 documentos y la capa estructural que admite la herramienta.

476 comunidades; ejemplos de cohesión bruta: comunidad unseal 0.03 y fingerprint 0.03. Hubs: User, unseal, RightsAction, fingerprint, Person; son centralidad del mapa, no consumo de CPU. Las conexiones sugeridas con Photo/representación son INFERRED y requieren lectura de fuente. La consulta amplia produjo 519 nodos y se truncó a 72: se completó la lectura directamente en los módulos, sin tratar la salida truncada como recorrido exhaustivo.

Coste AST: sin LLM. Dos agentes nativos semánticos; consumo de tokens no expuesto por la herramienta. Los ceros del esquema de los fragmentos no constituyen consumo medido. Se conserva consumo histórico.

## Request de listado, paso a paso

1. Cliente emite HTTP → admisión por Gunicorn sync → entrada WSGI. El diagnóstico previo observa demora emisión→WSGI, pero no distingue TCP, scheduling y cola de aceptación. No atribuir todo ese intervalo a PostgreSQL ni a Python.
2. Django aplica middleware, resuelve ruta e idioma. `apps/core/views.py:home` llama a `apps/listings/discovery.py:results`.
3. `SearchForm` valida filtros y página. `candidates` construye población. `publication_state.state_page` abre su propio snapshot REPEATABLE READ/READ ONLY cuando puede; dentro de una transacción heredada conserva las reglas originales.
4. Lee dirty y cobertura/versionado. Sólo si corresponde utiliza la proyección mantenida; conserva población nativa/fallback en otros casos. Cuenta y selecciona hasta 24 IDs, con caducidad, búsqueda, ranking y orden.
5. Hidrata esos IDs con `PublicationContext`. Lecturas concretas usan preparación SELECT y JIT/join scoped con restauración; PostgreSQL mantiene auto para elección de planes. La guardia nativa valida las filas seleccionadas antes de exponerlas. No hay caché de resultados públicos.
6. `PagePresentation` prepara atributos/fotos; Django renderiza HTML. Respuesta `Cache-Control: no-store`; cliente recibe el cuerpo. El servicio Gunicorn excluye la espera anterior al worker y no sustituye el tiempo completo.

La ficha sigue otra ruta: `moderation_views.public_detail` obtiene anuncio/revisión, ejecuta `publicly_visible` con preparación acotada y renderiza. No imponerle las conclusiones de conteo/proyección del listado.

## Evidencia y límites

El último [corto limpio](cr09-estadisticas-fixture-http-20261015.md) sigue siendo FAIL: 1200 peticiones completadas, cero errores y las 106 de al menos 0.8s emitidas durante 0–10s. No se ha medido otra versión en esta revisión. El [diagnóstico de workers](cr09-arranque-worker-diagnostico-20261015.md) localiza mayor SQLwall temprano y GC gen2 material también durante régimen posterior; los tiempos inclusivos se solapan. No demuestra una causa única.

La auditoría del harness confirma que short es diagnóstico concurrente de 60s y measured contractual de 900s. El gate corto exige los objetivos de latencia/error y límites de pendientes antes de continuar; no se cambia ni se extrapola un p95 de 60s al de 900s. Hay seis sondas frías existentes; no se añaden sondas ni se excluye el arranque para conseguir PASS.

## Investigación y decisión

Fuentes primarias consultadas: [Python 3.12, gc](https://docs.python.org/3.12/library/gc.html) y [Gunicorn, hooks y preload](https://gunicorn.org/reference/settings/). La documentación actual de Gunicorn se contrastó con el paquete 23.0.0 instalado: `workers/base.py:135–143` carga WSGI, llama a `post_worker_init`, marca booted y entra en el bucle. El hook existe en nuestra versión; no se adoptan opciones de versiones posteriores.

Candidata concreta para un diagnóstico finito: una única `gc.collect(2)` después de inicializar WSGI en cada worker y antes de su bucle de servicio, conservando collector automático y umbrales. Permite comprobar si basura de inicialización y el contador gen2 contribuyen al transitorio. Debe medirse el coste de inicialización, primeras peticiones completas, GC durante régimen y memoria; no basta comprobar que se invoca el hook. Aún no está implementada ni demuestra ahorro. WSGI inicializado tampoco garantiza que todos los imports perezosos/plantillas estén cargados.

No adoptar `gc.freeze()` del generador en el servidor por analogía: Python documenta que los objetos congelados quedan fuera de futuras colecciones. Una aplicación con objetos mutables/referencias posteriores necesita comprobar duración de vida y memoria; el generador sintético y el servidor tienen funciones distintas. Tampoco cambiar umbrales o desactivar GC. `--preload` altera la carga antes del fork y exige revisar conexiones/hilos/recursos heredados: no combinarlo con la candidata de un solo factor.

Prueba propuesta y criterio de descarte: comparación pareada de procesos web nuevos, misma mezcla/datos propios, todas las primeras peticiones incluidas; startup collect frente política actual, sin cambiar SQL ni concurrencia. Instrumentación sólo en diagnose y coste total de inicio registrado. Si el beneficio temprano no aparece o se intercambia por memoria/pausas posteriores, descartar sin una nueva carga limpia. Si sí aparece y conserva semántica/recursos, integrar la candidata y ejecutar un solo corto limpio; repetir una vez sólo si pasa. No se promete reducción concreta ni aceptación de CR09.

## Resultado del diagnóstico de inicialización y cambio de dirección

Run `20261015-210315-f19b2774`: **1 PASS125.84s**, 180 peticiones secuenciales en seis procesos Python nuevos, tres bloques alternos, PostgreSQL propio. Es Django test-client con su propio handler, no worker Gunicorn ni admisión concurrente. Se incluyen todas las primeras peticiones. Inicialización cronometrada sólo en `get_wsgi_application`, no todo el arranque Python. Cuerpos de listados/búsquedas idénticos por hash; fichas comprueban estado/header, no igualdad universal del token firmado. [Recibo y agregados](cr09-startup-gc-terminal-20261015.json).

| Medida en esta comparación aislada | Actual | Collect al inicializar |
|---|---:|---:|
| CPU media de las primeras 6 peticiones/proceso |190.8315ms|178.1829ms|
| CPU media de las 30 peticiones/proceso |120.3725ms|117.9014ms|
| Wall medio de las primeras 6 |290.6101ms|278.2110ms|
| Wall medio de las 30 |190.1316ms|186.0166ms|
| CPU adicional media del collect inicial |0ms|41.4151ms|
| Eventos gen2 durante peticiones, tres procesos/brazo |9|6|
| CPU GC acumulada durante peticiones, tres procesos/brazo |1019.7846ms|850.9919ms|

El bloque1 empeora CPU inicial179.6061→186.1905ms; los otros dos mejoran. El ahorro medio por request es pequeño y la preparación agrega coste, con entorno secuencial/observadores. **Candidata descartada para producto**, sin otra carga limpia. No se infiere p95, memoria sostenida ni arranque completo mejorado. El freeze_count inicial del intérprete es375 y permanece igual, no cero.

Se conservan dos fallos del instrumento: [primero](cr09-startup-gc-instrumento-fallo-20261015.json) sin stderr suficiente y [segundo](cr09-startup-gc-instrumento-guard-fallo-20261015.json) que localiza la aserción incorrecta de freeze_count cero antes de peticiones. Correcciones: configuración DB/media explícita como el harness propio, excepciones sólo tipo/frames, comparación del freeze_count contra su valor inicial. No son fallos de rendimiento del producto; no ocultarlos ni contarlos como ensayos comparativos completos. Fuentes y limpieza verificadas independientemente en los tres terminales.

La lectura posterior encuentra un mecanismo distinto y concreto: `memoize_publication_field_clean` guarda `field.clean` como método ligado dentro de la función que vuelve a asignar al campo. Esto crea `campo → función → método ligado → campo`; el generador recursivo local de claves también se referencia a sí mismo. La [prueba roja](cr09-memo-lifetime-red-20261015.json), con un CharField Django real, demuestra retención añadida hasta GC frente al campo nativo sin memoizador.

Correctiva local: referencia `WeakMethod` al método original, convertida en referencia fuerte local durante cada llamada; prototipo/formulario siguen siendo dueños del campo. Clave recursiva trasladada a helper de módulo. Callables desconocidos que no soportan WeakMethod conservan validación nativa sin memoización. No hay caché entre requests, freezer ni cambio de umbrales. [Python 3.12 WeakMethod](https://docs.python.org/3.12/library/weakref.html#weakref.WeakMethod) documenta la reconstrucción del método mientras existen objeto y función. La guardia de vida útil no demuestra que todos los ciclos de Django desaparezcan ni que éste sea el único cuello. Verificación funcional en curso; efecto p95 no medido.

Verificación terminal de la correctiva `20261015-210754-2f34f0ea`: **18 PASS189.87s**, [recibo](cr09-memo-lifetime-green-20261015.json). Incluye vida útil/callable desconocido, contexto de validación, dependencias actuales y proyección. Fuentes congeladas idénticas, procesos/temporal/contenedores propios retirados; unidad MainPID0/ControlGroup vacío. Se acredita eliminación del ciclo añadido en el campo probado y semántica de los casos ejecutados, no desaparición de todos los ciclos ORM ni mejora p95. Se autoriza técnicamente un único corto limpio conservando población, cuotas, arranque y criterios. Si FAIL, conservar y diagnosticar aparte; si PASS, una repetición idéntica. No adelantar 15min/CR09/N3.
