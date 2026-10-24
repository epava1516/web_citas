# B09-345 — Entrega de galería y activos

B09 mantiene pendiente entrega de imágenes/activos y revisión de backlog/fallback. La cola SQL está corregida en305; once de18puntos aceptados. Se revalida el grafo406 antes de este hito, sin extracción global nueva. Consulta BFS orientativa truncada, seguida de lectura directa de plantillas, public_photo, Blob, process y pruebas de navegador.

## Observación actual y criterio previo

El listado ya utiliza loading=lazy. La galería de ficha no lo utiliza y puede contener ocho fotos; public_photo sirve el derivado WebP con no-store y valida publicación en cada petición. El procesado limita a1600px, calidad85, y las tarjetas/galería mantienen aspecto CSS4/5. No se presupone ahorro por cambiar codec o almacenamiento.

Se medirá una biografía larga admisible (80líneas, menos de6000caracteres) que deja la galería fuera de la pantalla inicial, en móvil390x844 y escritorio1280x800, ES/EN. Ocho imágenes sintéticas con ficheros reales: una del fixture base y siete construidas como filas ready/aprobadas/comparadas explícitas para visualización, con WebP y firmas calculadas. No se verifica aquí el flujo de subida, revisión humana, comparación entre imágenes ni proveedores. Chromium y HTTP reales con live_server/PostgreSQL; no simulador de transferencia ni prueba de Internet.

El instrumento test_gallery_delivery_diagnostic.py conserva URLs/orden, dimensiones naturales, hashes y bytes de cuerpos completos; registra solicitudes y bytes iniciales, carga de las ocho fotos al recorrer la página y cuerpos de CSS/JS. Exige carga inmediata de la primera foto sin desplazar la página, recursos200 y acceso404 después de pausar el anuncio aunque se envíen condicionales. No implica retirar bytes ya recibidos del navegador.

Primero dos casos de diagnóstico sobre plantilla original, un worker y timeout1200s por comando. La hipótesis es que se solicitan las ocho fotos inicialmente en ambos tamaños. Si se confirma, el candidato mínimo será loading=lazy sólo después de la primera foto, con archivos y backend intactos. Criterio anterior al contraste: en móvil al menos una foto fuera de pantalla deja de solicitarse inicialmente; escritorio no aumenta peticiones; al recorrer la galería siguen cargando las ocho con exactamente los mismos cuerpos, orden y dimensiones, y el acceso tras pausa sigue denegado. Si no hay reducción móvil, no se declarará ganancia ni se alterará el fixture para producirla.

Los bytes son de cuerpo decodificado del recurso, no cabeceras ni tráfico de red completo. Las dos vistas y la biografía seleccionada no representan todas las conexiones o navegadores. No se medirán LCP, CPU causal ni capacidad. El tamaño de activos y su número servirán para revisar candidatas, sin introducir límites retrospectivos.

La fuente previa de public_detail.html queda preservada. No hay cambio de plantilla, pipeline, almacenamiento o autorizaciones en este diagnóstico inicial. Tras verificar fuentes, JUnit, limpieza y Telegram se decidirá el candidato y se prerregistrará su regresión.

## Corrección del instrumento antes de medir

La ejecución20261024-062444-daa216ca produjo dos fallos por SynchronousOnlyOperation en la escritura de estado previa a navegar. Se preserva el resultado ERROR y el instrumento original; fuentes, limpieza y Telegram confirmados. No se acredita referencia de rendimiento ni fallo de la aplicación.

Las URLs y comprobaciones Client se preparan fuera de Playwright. Los cambios de estado pasan a un hilo síncrono con conexión PostgreSQL propia, commit real y cierre de conexiones. No se desactiva la protección asíncrona de Django. Se mantienen exactamente biografía, archivos, viewports, número de fotos y criterios previos. Se repiten sólo los dos casos del diagnóstico sobre la misma plantilla original.

## Referencia verificada y candidato mínimo

La ejecución20261024-063628-a3c582f1 verifica dos PASS, cero fallos/errores/omisiones,73,247s sumados JUnit y1716fuentes congeladas. En las cuatro combinaciones móvil/escritorio y ES/EN se reciben inicialmente las ocho fotos:135824bytes de cuerpos de imagen. Las ocho cargan y el acceso nuevo tras pausa devuelve404. Recursos de ficha app.css y form-errors.js se sirven correctamente; la auditoría conserva tamaño y hashes reales. No se modifica la biografía ni la heurística del navegador tras observar el resultado.

Se añade loading=lazy sólo a las fotos posteriores a la primera en public_detail.html. La primera conserva la política anterior; no se modifica ningún archivo de imagen, pipeline, backend, CSS, JavaScript ni almacenamiento.

Regresión prerregistrada: tres casos, dos selectores, dos workers y timeout1200s por comando. Dos del mismo test_gallery_delivery_diagnostic.py sin modificar bytes desde la referencia válida, más test_browser_discovery.py::test_mobile_search_service_modes_language_and_public_card. Este último conserva el recorrido de búsqueda/ficha con una foto y carga inmediata. El criterio de reducción móvil y no aumento de escritorio se mantiene; la comparación verificará cuerpos, dimensiones, orden, CSS/JS y denegación tras pausa.

## Resultado del contraste

La ejecución20261024-064310-28e0f5bb verifica tres PASS, cero fallos/errores/omisiones,123,754s sumados JUnit, dos workers y1716fuentes congeladas. La [referencia](evidencias/b09-gallery-baseline-audit-20261024.json), [regresión](evidencias/b09-gallery-corrected-audit-20261024.json) y [comparación](evidencias/b09-gallery-comparison-20261024.json) conservan artefactos, hashes, limpieza y recibos Telegram.

En móvil/escritorio y ES/EN, las peticiones iniciales de foto pasan de8a1 y los cuerpos de135824a11110bytes. Al recorrer la galería se reciben las ocho fotos y135824bytes totales como antes: no se reduce la calidad o el contenido entregado. URLs/orden, dimensiones, hashes, CSS/JS y respuesta404tras pausa permanecen iguales. Se cumple el criterio previo sin cambiar fixture, imágenes o heurística. La reducción es inicial y depende de la posición de galería: no se promete ahorro total si se consultan todas las fotos, LCP ni capacidad de Internet.

Sólo cambia el atributo condicional después de la primera foto. Los otros629archivos de producto de ambos cortes son idénticos; no se añaden variantes ni campos de almacenamiento. Para revertir, retirar únicamente ese atributo condicional, conservando las demás modificaciones previas del usuario.

## Revisión de activos y límites

El [inventario estático](evidencias/b09-static-source-inventory-20261024.json) contiene siete archivos y69312bytes de fuente, incluidos HTMX52.182bytes y su licencia/README. En estas fichas se entregan únicamente app.css12412bytes y form-errors.js962bytes, ambos con hashes iguales entre cortes; el script está diferido. El listado añade search-geography.js1553bytes; la geografía de formulario tiene otro script1179bytes. El HTMX vendorizado no aparece entre los recursos de estas fichas. No se elimina código vendorizado del usuario ni se atribuye su peso a una ruta que no lo carga.

Caddy se revisó como configuración, no como medición de proxy. Los cuerpos del ensayo se sirven por el live_server real con encodingidentity: no son tráfico comprimido de producción. No se adopta cambio de códec, variantes, compresión o caché a partir de estas muestras; los archivos permanecen idénticos. La revisión de backlog/fallback y la conciliación final de B09 siguen pendientes. Once de18puntos cerrados.

Decisión posterior: [acta19](actas/19-beta-b09-aceptacion-local-20261024.md) y [conciliación307](307-conciliacion-lectura-entrega-b09-20261024.md) aceptan B09 técnicamente en local; los pendientes indicados antes corresponden al corte propio de este documento.
