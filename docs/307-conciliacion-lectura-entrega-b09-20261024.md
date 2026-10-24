# B09-346 — Conciliación de lectura, entrega y observación

B07 está aceptado por acta16 y B08 por acta18. B09 ya dispone de corrección SQL verificada en305 y entrega diferida contrastada en306; sigue abierto hasta conciliar sus requisitos. Once de18puntos cerrados, B15 opcional. El grafo410 está revalidado antes del hito; el alcance conserva AST dirigido y semántica seleccionada.

## Evidencia revisada y falta concreta

- Consultas/hidratación: antes30/210consultas para10/100denuncias; después10/10con mismo instrumento. Siete casos previos y18posteriores, conflictos y controles privados preservados. No índice ni caché entre peticiones.
- Imágenes: antes8fotos/135824bytes inicialmente; después1/11110en cuatro contextos de Chromium155, con ocho fotos y cuerpos idénticos al recorrerlas, primera inmediata y404tras pausa. Tres casos posteriores. No calidad/formato/almacenamiento cambiados ni LCP/capacidad acreditados.
- Activos: siete fuentes69312bytes incluyendo HTMX/licencia no cargados en las fichas medidas. CSS/JS servidos en esas fichas13374bytes, sin cambios; los scripts pertinentes ya están diferidos. No atribuir a la ruta bytes vendorizados que no carga ni extrapolar al proxy productivo.
- Observación existente B12: snapshot agrega trabajo durable y edad; declara no medidos broker/worker/frecuenciafallback. El informe de ventana calcula fracción de fallback sólo sobre eventos observados y mantiene coverageunverified/healthunknown. Fuentes de snapshot/events/window y sus pruebas coinciden con el corte B12actual022632; el test HTTP de emisor se ejecutó en un corte anterior con paginador después modificado. Para evitar acreditar esa integración como actual sin testigo, se comprobará de nuevo el recorrido HTTP→evento→ventana junto con backlog real persistido.

## Prerregistro final de observación

Nuevo test_read_delivery_observation.py:una petición state y otra fallback por1001marcas huérfanas sintéticas con límite real1000, sin monkeypatch del límite ni del emisor. IDs/recuento permanecen iguales. Snapshot PostgreSQL propio de sólo lectura debe observar1001marcas y su edad calculada, dejando la cola intacta. Los dos eventos reales capturados del logger alimentan summarize_window: dos observados, un fallback, fracción0,5, cobertura no verificada y salud desconocida. No se acredita todo el tráfico, transporte durable del log, worker, reparación ni1001escrituras de dominio.

Selección de tres casos, tres archivos, dos workers y timeout600s por comando: el nuevo integrado, test_operational_snapshot.py::test_due_notice_boundary_and_private_values_never_emitted y test_operational_window.py::test_empty_unknown_route_and_private_or_malformed_rows_never_imply_health. PostgreSQL/Redis propios. No se repite la batería B12 ni la carga contractual; hay una incertidumbre específica de integración actual y privacidad/ausencia de observación que resolver.

Tras fuentes/JUnit/limpieza/Telegram, se decidirá B09 por cada literal del roadmap. Ninguna suma de cortes será declarada candidata conjunta B16, toda la etapa3, beta global o producción. Los presupuestos contractuales originales no se relajan y las muestras de tiempos aislados no se usarán como mejora causal.

## Observación actual verificada

Ejecución20261024-070525-bd417543: tres PASS, sin fallos, errores u omisiones;86,196s sumados JUnit y1717fuentes congeladas. El [testigo actual](evidencias/b09-current-read-observation-20261024.json) observa1001marcas y240,204317s de edad, dos lecturas HTTP y un fallback. El límite real sigue1000. Estado/fallback mantienen IDs/recuento. Snapshot y lectura dejan la cola intacta; la ventana declara sólo entrada observada, cobertura no verificada y salud desconocida. Los controles de privacidad de snapshot y ausencia de observación pasan. Fuentes630producto coinciden con la regresión de galería, limpieza Docker/temporal/proceso y Telegram confirmados.

## Decisión por requisito

B09 aceptado técnicamente en local. La [matriz literal](evidencias/b09-local-requirement-acceptance-matrix-20261024.json) identifica seis obligaciones del roadmap, razón de aceptación y huellas. El requisito de índices es condicional: ninguno se añade ni se acredita plan no ejecutado.

| ID | Resultado y alcance |
| --- | --- |
|R01|N+1 confirmado y corregido:30/210→10/10consultas, mismo instrumento.|
|R02|Sin índice o migración nuevos; no EXPLAIN/beneficio físico inventados.|
|R03|Lectura estrecha de cola y selección SQL con autoridad equivalente; no cambio especulativo del render backend.|
|R04|Imágenes y activos revisados con cuerpos reales; carga diferida evita inicialmente siete fotos en el escenario elegido, sin nuevas variantes.|
|R05|Mismos bytes/dimensiones/orden/URLs/alt/CSS, primera inmediata, recorrido móvil y404tras pausa; permiso/MFA/COI privados preservados. Sin WCAG global nuevo.|
|R06|Backlog durable y fracción de fallback observada probados en integración actual; no cobertura/salud/worker/Internet inferidos.|

Hay24testigos distintos entre18+3+3casos posteriores en sus cortes y siete previos de autoridad, además del diagnóstico SQL343. No son una sola batería24PASS ni candidata común B16. Se conservan el primer instrumento de galería fallido y su corrección de contexto asíncrono; no se aceptó aquella ejecución como rendimiento o fallo de aplicación.

## Presupuestos, reversión y residual

Los criterios B07 aceptados y sus cuotas/mezcla se conservan; no se ejecuta nueva carga contractual ni se relaja p95/errores para aceptar conteos de consultas o cuerpos. Los workers/calor de caché difieren entre ensayos, por lo que las muestras temporales no acreditan mejora causal. Menos sentencias no significa trabajo SQL o memoria constantes. Una biografía larga/Chromium no representa todos los visitantes; si se recorren todas las fotos se transfieren los mismos cuerpos que antes.

La reversión se limita a los cambios propios de cola/helper y al atributo condicional de galería, documentados en305/306. No se restaura un módulo completo del usuario ni se modifica pipeline/almacenamiento. Es un mecanismo definido, no rollback desplegado. Las variantes de imagen, compresión y caché siguen siendo posibles candidatas si otro escenario demuestra beneficio; no son cambios obligatorios adoptados sin evidencia.

Doce de18puntos cerrados: B00–B09 y B12–B13. Pendientes B10–B11 y B14–B17, B15 opcional. B16 exige candidata y regresión conjunta pertinentes, sin sumar cortes como aprobación global; B17 mantiene apertura/operación externa separada. Esta acta no cierra toda la etapa3. Próximo B10: revisar extremos de exportación/similitud preservando MOD09 provisional y sin adoptar FAISS/Hamming sin corpus y paridad.
