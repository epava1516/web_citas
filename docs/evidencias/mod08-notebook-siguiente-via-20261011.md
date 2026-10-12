# MOD-08 — Deliberación de la siguiente vía — 2026-10-11

Petición: «sigue deliberando una siguiente vía con el notebook». Se discutieron los resultados negativos del inline, diagnósticos previos, código actual, hipótesis propias y controles. No se inició carga ni cambio productivo.

Notebook `bb1f4634-45b7-4f41-b807-4b8502614b9d`, conversación `99c86acd-9184-4561-8d47-e5c44f4636ab`; no fuentes añadidas/eliminadas. [Consulta breve con código](mod08-notebook-siguiente-via-breve-consulta-20261011.txt), [respuesta](mod08-notebook-siguiente-via-breve-respuesta-20261011.json), [correcciones propias](mod08-notebook-siguiente-via-correccion-consulta-20261011.txt), [segunda respuesta](mod08-notebook-siguiente-via-correccion-respuesta-20261011.json). La consulta inicial extensa fue rechazada como inválida por el MCP: [texto](mod08-notebook-siguiente-via-consulta-20261011.txt) y [error preservado](mod08-notebook-siguiente-via-respuesta-20261011.json). Se redujo a 7345 caracteres; no afirmar un límite de API no verificado.

## Dirección elegida

Priorizar el coste de construir la fuente y sus proyecciones, antes de ajustar otra vez hashes SQL de cadena. La candidata inline anterior pasó equivalencia/seguridad pero no acreditó beneficio HTTP fiable y fue retirada. En otro request instrumentado, `source_copy` tuvo ~426ms wall/~253ms CPU; esa cifra orienta dónde mirar, no prueba que la causa sea ORM ni representa el benchmark HTTP de clones de ~800ms. Son distintos experimentos y perímetros.

Ya existen fuente compartida con comprobación fresca final, proyección pura acotada tras validación, memorias de fingerprints de contenido y kernel Cython de validación canónica. No presentarlos como optimizaciones nuevas ni omitir validaciones, lecturas físicas o auditorías.

## Siguiente diagnóstico propuesto, no ejecutado

Un único bloque con control limpio / perfilado / control limpio sobre clones desechables de una historia idéntica preparada con 64 lotes auditados por servicios. Dos workers sync con warm POST real, PIDs anotados, conexión y estado inicial comparables; commits normales y verificación independiente de cuatro lecturas/ocho eventos por POST. Esto orienta costes; tres peticiones no acreditan p95 ni aíslan todo el ruido térmico/de planificación. Preparación, warmups y las tres muestras se declaran aparte.

| Perímetro | Medición que se busca |
|---|---|
| `source_copy` | CPU/wall propios y árbol de hijos observado |
| `batches` | Tiempo durante `next()`, excluyendo suspensión entre yields; carga de revisiones, relaciones y agrupación |
| Instanciación/adaptación | Call counts y CPU auxiliar de modelos/conversores/iteradores; no confundir con CPU de PostgreSQL |
| Construcción del diccionario fuente | Trabajo restante tras hijos observados; no inventar fase ausente |
| `_InspectionSource.__init__` | Separar fingerprint de filas, copia y canonical/HMAC posteriores |
| Salida de `inspection_source` | Canonical/HMAC de mutación, fingerprint fresco y fallback de relectura si lo hay |
| Render y respuesta | Trabajo después del servicio, con WSGI y TCP en perímetros declarados |

`cProfile(timer=thread_time)` auxiliar sólo en la muestra perfilada, sin locals/argumentos/payloads, además de spans wall/CPU precisos. No sumar sus tiempos exclusivos al árbol de spans ni descontar el diferencial como overhead causal conocido. No separar ejecución PG, red y adaptación automáticamente usando execute/fetch. El profiler observa CPU del hilo cliente, no la CPU del servidor ni la duración de esperas. Las llamadas C/Cython pueden no ofrecer desglose interno suficiente; registrar esa limitación.

## Candidata condicionada

Si la creación de modelos de las relaciones simples resulta costosa y hay un margen de ahorro material medido, considerar `.values_list()` para categorías, servicios y zonas de desplazamiento en `rights_copy_revision_batches.batches`, con adaptación explícita de `source_copy`. Actualmente sus consumidores usan `item.slug`/`item.code`; cambiar a primitivas sin adaptarlos rompería el código. Mantener el conjunto de filas, agrupación por UUID de revisión, orden, momento de consultas y comprobación fresca final. No adelantar relaciones mutables ni añadir caché de autoridad.

Se posponen cambios sobre el bloqueo/hidratación de Revision, Photo/Blob, contactos y políticas. `contact_data` usa campos de revisión y prueba de titularidad de teléfono; `image_inventory` consume Photo/Blob con timestamps/estado/dimensiones. Si una candidata posterior los alcanza, exige conservar sus políticas y formatos, no sólo un JSON superficial parecido.

Antes de adoptar una candidata: igualdad de estructura y bytes canónicos, consultas sin lazy loads nuevos, fuentes completas y comprobaciones de drift/inserción/borrado/restauración, carreras PostgreSQL reales y comparación HTTP contrabalanceada. Ya hay pruebas pertinentes de equivalencia de batches en `test_rights_copy_scope` y de inventario/drift de fuentes en `test_rights_source_fingerprint`; verificar su cobertura para el cambio concreto.

## Correcciones a NotebookLM y salida finita

Notebook coincide tras dos intercambios, pero su opinión no verifica el arnés. `canonical_bytes` ocurre después de `source_copy`, no dentro de sus 253ms; la comprobación de mutación es antes del finally, que sólo restablece ContextVar. El gap wall/CPU puede incluir esperas, planificación y contención; los dos procesos Gunicorn no comparten GIL. `canonical_bytes` valida tipos/estructura con kernel o fallback y usa SORT_KEYS: no quitar ordenación ni guardas como atajo. Porcentajes/umbrales 35%, 30%, 40/50/25ms propuestos por el notebook no tienen evidencia y no se adoptan.

La expresión «deslinde limpio» de su respuesta corregida sigue siendo excesiva para servidor/transporte/adaptación: el diagnóstico puede localizar dónde se consume wall/CPU de aplicación, no demostrar por sí solo la causa de kernel/servidor. No declarar límites arquitectónicos por un perfil ni extrapolar al histórico de 383 lotes bajo cuotas distintas.

Un componente medido Xms sólo ofrece Xms como techo de ahorro directo en ese ciclo; ese techo no es una ganancia esperada. Del diagnóstico se selecciona como máximo una candidata justificada. Si el trabajo identificado es pequeño, el ahorro posible no justifica el cambio o no mejora HTTP en una comparación pertinente, cerrar esa rama conservando evidencia y elegir la siguiente fase observada. No encadenar microparches con promesas de alcanzar 2s/5s. MOD08 general continúa pausado.
