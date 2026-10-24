# B00 — Fuentes técnicas capturadas: paralelismo y lectura de planes

Estado: dos textos capturados leídos completos y procedencia verificada tras el terminal del corto184. Lectura durante su preparación, sólo artefactos ignorados y notas; sin cambios de fuente/docs/grafo, SQL o pruebas concurrentes. [Prueba de procedencia](evidencias/b00-two-technical-source-provenance-20261021.json) comprueba identidades, bytes, rangos sin huecos e inventario capturado295. No se afirma que ése sea el censo actual ni que todo el corpus esté auditado.

## Fuentes y alcance

| Fuente capturada | Identidad | Lectura |
| --- | --- | --- |
| pytest-xdist How-tos | source:h52j6688qvhzuunooyww |13090caracteres, rango0–13090|
| PostgreSQL17 UsingEXPLAIN | source:yr9ylkxrvnkzi4qrrtd1 |46172caracteres, rangos0–16000–32000–46172|

Hashes completos y capturas crudas quedan identificados en la prueba. Son dos fuentes distintas de las onceUXde174; trece en el subconjunto identificado UX+técnico, no trece de un corpus global aceptado. No se comprobaron versiones onlineactuales, erratas o páginas enlazadas no incluidas en full_text. No se alteraron fuentes/notas/notebooks originales.

## Disposición de la lectura

La[guía capturada de xdist](https://pytest-xdist.readthedocs.io/en/stable/how-to.html) identifica trabajadores y sesiones, describe fixtures ejecutadas por trabajador y un ejemplo de coordinación mediante fichero/bloqueo. El ejemplo no demuestra que las bases mutables o credenciales de este proyecto puedan compartirse. Los títulos de procesos son ayuda visual, no interfaz estable. Esta página no mide rendimiento ni cubre todos los algoritmos de reparto. Se conserva aislamiento por trabajador; no se adopta caché compartida ni cambio de workers por esta lectura.

El[capítulo capturado de PostgreSQL17](https://www.postgresql.org/docs/17/using-explain.html) distingue costes estimados arbitrarios de tiempos reales, valores inclusivos y promedios porloops. rowsrepresenta salida, no filas físicas leídas directamente; LIMITyselectividad pueden cambiar planes o truncar ejecuciones. ANALYZEejecuta la consulta y añade sobrecoste; la red queda fuera y conversión se mide si se pideSERIALIZE. Leer esos ejemplos no identifica el coste del cursor real ni demuestra escalado. No se ejecutó SQL ni se adoptaron hints, índices o ajustes del planner.

Estas fuentes apoyan interpretar límites de evidencia ya exigidos por el contrato. No introducen requisitos de producto, versiones de librerías, presupuestos o optimizaciones aceptadas. B00conserva su residual exhaustivo; B07conserva sus mediciones y condiciones propias. La procedencia documental no acredita código, accesibilidad, investigación con personas ni aceptación beta.
