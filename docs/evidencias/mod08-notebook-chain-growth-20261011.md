# Segunda opinión de NotebookLM sobre el crecimiento de cadena

2026-10-11. Notebook `bb1f4634-45b7-4f41-b807-4b8502614b9d`, conversación `99c86acd-9184-4561-8d47-e5c44f4636ab`. Comunicación solicitada por el usuario, sin añadir/borrar fuentes ni ejecutar nuevas cargas.

[Consulta completa con resultados, conjeturas y valoración](mod08-notebook-chain-growth-consulta-20261011.txt) / [respuesta íntegra](mod08-notebook-chain-growth-respuesta-20261011.json). Se devolvieron [correcciones técnicas](mod08-notebook-chain-growth-correccion-consulta-20261011.txt), con [respuesta conservada](mod08-notebook-chain-growth-correccion-respuesta-20261011.json). La evidencia local es el [diagnóstico medido](mod08-chain-growth-20261011.md).

## Coincidencia útil

El notebook recomienda analizar los planes de la consulta de eventos y las siete consultas de fuentes físicas antes de modificar validadores. Propone como candidatas posteriores un `UNION ALL` de fuentes y una comparación de conjuntos dentro de PostgreSQL. Ninguna candidata tiene ahorro ni equivalencia demostrados; no se aplica código productivo.

## Contraste propio comunicado

Los tiempos de aplicación no prueban que hashing/to_jsonb dentro del servidor sea el cuello dominante, ni descartan superlinealidad o transporte con dos muestras por nivel. La diferencia de aproximadamente 332ms entre los deltas de HTTP y cadena no es una fase medida. Las 28 consultas son solamente las de fuentes físicas, no todo el SQL del HTTP.

Unificar consultas no elimina automáticamente los 91ms de `pipeline.sync`: el trabajo y la espera podrían desplazarse a `execute`/`fetch`, manteniendo todos los escaneos y hashes. Un único comando cambia siete snapshots READ COMMITTED por uno; exige revisar escritores/bloqueos y medir. La etiqueta de tabla de UNION ALL añade material al resultado.

Un Seq Scan o bloques leídos no prueban que falte un índice. El código ya tiene unicidad `(request, sequence)`, relaciones OneToOne indexadas en `action` y ForeignKey de `RightsAction.request`. EXPLAIN no atribuye por sí solo una proporción exacta a cada función SQL. La documentación oficial confirma que un escaneo secuencial puede ser adecuado para tablas pequeñas, que ANALYZE incorpora overhead y que no envía las filas del resultado al cliente; SERIALIZE mide conversión, no transporte ni adaptación Python. [PostgreSQL17 — Using EXPLAIN](https://www.postgresql.org/docs/17/using-explain.html).

La base y el servidor del diagnóstico están retirados; no hay fixture de 644 eventos vivo ni snapshot disponible. El dato 344 eventos mencionado por la respuesta es incorrecto. Un nuevo ensayo requiere preparación real propia y controles comparables. SET ROLE sobre conexión propietaria no acredita la misma prueba de LOGIN independiente restringido. El SELECT de eventos propuesto por el notebook omitía la columna `digest` que utiliza el código real.

Una comparación de conjuntos debe detectar discrepancias en ambas direcciones y conservar secuencia/enlaces/cabeza/tombstones y hashes físicos. Debe vincularse al conjunto de eventos realmente validado y conservar errores/rollback/concurrencia; no equivale automáticamente a `actual == rows`. El error actual es `Evidence chain source rows changed`, no el mensaje inventado por la respuesta. Los sellos existentes no justifican un atajo en este recorrido.

No declarar SHA256/JSONB por fila un mecanismo inalterable impuesto por contrato: distinguir garantía y arquitectura actual. El contrato autoriza modernización con equivalencia y pruebas, pero esta consulta no autoriza ni demuestra otra arquitectura. No cachear autoridad ni quitar revalidaciones.

## Respuesta a las correcciones

El notebook acepta las seis correcciones y reformula su propuesta como diagnóstico pareado con/sin expresión de hash. Su frase «baseline de 4 eventos base64» es una deformación sin correspondencia con la evidencia; no hay baseline viva ni tal población. Su última propuesta se limita a siete fuentes y omite los eventos: la recomendación propia mantiene ambas familias, porque `events_execute` y `events_fetchall` también crecieron. Un contraste sin hash debe comprobar que el plan, filas y expresión realmente evaluada sean comparables; la diferencia no es automáticamente CPU pura de SHA256.

## Decisión

Siguiente paso recomendado: diagnóstico EXPLAIN finito sobre las consultas actuales, datos/historial creados por servicios, runtime separado, controles de plan/calibración/overhead y comparación pertinente de costes. UNION ALL y comparación SQL de conjuntos quedan como hipótesis posteriores a comprobar. Ningún ahorro nuevo, p95 ni aceptación 2s/5s. No cambios de producto ni nuevas pruebas en esta comunicación; MOD08 general sigue pausado.
