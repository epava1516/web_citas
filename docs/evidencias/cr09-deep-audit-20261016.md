# CR09: auditoría profunda de contexto, medición y adopción — 2026-10-16

## Dictamen del corte

No está demostrado un p95 inferior a 0,8 s. La agrupación de primera página sigue siendo un prototipo en tests. Su ahorro secuencial justifica continuar estudiándolo, pero la revisión adversarial encontró una regresión HTTP 500 reproducible. Se corrigió el índice común de PublicationContext y se verificó esa corrección; no se ha integrado todavía la agrupación ni ejecutado una nueva carga limpia. CR09 y la aceptación global permanecen abiertos.

Base Git del diagnóstico: `89e07566376d5b4ea9a3e7d629ee666b3f4c59ba`; los recibos de fuentes congeladas identifican además los cambios locales exactos de cada ejecución. Árbol de trabajo propio `web_modelos_mod08_vps`. El producto, el prototipo y la imagen Docker no son versiones intercambiables. La imagen v5 anterior no contiene las correcciones recientes de vida del RateForm ni la corrección actual del índice de revisiones.

## Despiece del recorrido

1. La petición puede esperar antes de entrar a WSGI. Esa espera forma parte de la latencia del cliente, aunque no figure como tiempo de una consulta o de una función Django.
2. Django valida idioma, filtros y protocolo de consulta. La selección abre un snapshot PostgreSQL REPEATABLE READ de solo lectura cuando es propietaria de la transacción; una transacción heredada no adquiere automáticamente esa garantía.
3. El censo y las versiones determinan si puede utilizarse el estado calculado. Los elementos Dirty se comprueban contra las reglas nativas actuales. El estado calculado no sustituye la autoridad del dominio.
4. Se obtiene población, total y página con orden nativo. Se hidratan anuncios, revisiones, relaciones y catálogo; construir objetos, QuerySets y formularios consume CPU además del SQL.
5. El guard final vuelve a comprobar los anuncios seleccionados. Se renderiza la respuesta localizada y se envía al cliente. El GC y las asignaciones pueden contribuir al coste observado.

El diagnóstico previo mostró cola inicial y cuatro workers ocupados/equilibrados; no apoya aplicar sin más una solución de workers ociosos de otro sistema. Tras el refresco inicial quedó Dirty vacío en las observaciones disponibles, mientras persistían peticiones lentas: eso no demuestra que Dirty durase quince segundos. Los tiempos anidados de wrappers no se suman como fases independientes. Tampoco se puede atribuir toda la diferencia a SQL, GC o hardware de forma exclusiva.

## Comparación de evidencia ya existente

No son métricas nuevas de este corte; se recapitulan para impedir mezclar escenarios.

| Escenario | Referencia | Candidato | Lectura válida |
|---|---:|---:|---|
| Último corto limpio, p95 HTTP | objetivo <0,800 s | 1,013030 s | FAIL; no corresponde al prototipo agrupado |
| Agrupación, media WSGI ES secuencial | 296,927 ms | 215,397 ms | −27,46%, con Dirty forzado durante el ensayo |
| Agrupación, media WSGI EN secuencial | 356,180 ms | 287,287 ms | −19,34%, mismo alcance limitado |
| Agrupación, CPU ES | 175,646 ms | 130,138 ms | −25,91%; no atribución exclusiva a SQL |
| Agrupación, CPU EN | 193,542 ms | 150,513 ms | −22,23%; no atribución exclusiva a SQL |
| Consultas de esa agrupación | 64 | 44 | Menos consultas en ese fixture; no prueba de p95 |

Fuentes: `cr09-first-page-batch-roi-20261016.md/json` y seguimiento17 para el corto limpio `025813-e0755597`. Llegar desde 1,013030 hasta 0,800 s exige aproximadamente 213 ms, o 21,03% menos respecto al valor observado; el criterio exige bajar estrictamente del umbral. No puede aplicarse el porcentaje de una media aislada al p95 concurrente para declarar cumplimiento.

El ensayo de agrupación utiliza tres bloques con orden rotado A/B/C, controles nativos idénticos y dos idiomas. Sus 288 lecturas medidas son secuenciales con calentamiento, no una subida real con planificación Beat ni el patrón completo de carga. El control A/A agregado satisface la regla prerregistrada; un bloque ES tiene deriva de 15,45%, limitación que debe conservarse sin inventar retrospectivamente otra regla de aceptación. Las colecciones de generación 2 difieren entre brazos: pueden mediar parte del ahorro. No hay demostración causal de que el ahorro provenga únicamente de la base de datos.

## Fallo reproducido y corrección

`Listing.approved_revision` permite una FK hacia una revisión de otro anuncio. La regla nativa rechaza ese anuncio antes de validarlo. Sin embargo, `PublicationContext.by_revision` antes indexaba todas las filas por revisión: una fila ajena podía sobrescribir a su propietaria cuando ambas se hidrataban juntas.

La prueba propia conserva el orden público y fuerza una ordenación de hidratación permitida, idéntica para ambos brazos. La referencia devuelve HTTP 200 y excluye al ajeno; el prototipo producía ValueError/HTTP 500 al validar al propietario legítimo. El caso no requiere perder una invalidación: la escritura marca Dirty mediante el trigger real. No se afirma que exista ese dato en producción ni que sea una exposición de información.

La corrección sólo incorpora al índice las revisiones que pertenecen a la fila. `row()` sigue exigiendo la misma instancia del contexto y produce ValueError ante una revisión ausente o ajena. No se captura el error para esconder al propietario ni se relajan los guards. Se comprobó que no hay otros consumidores de `by_revision` en apps/tests.

Evidencia terminal independiente:

- `083744-7fd9798c`: 1 FAIL original, conservado con fuentes.
- `084035-d87f27ed`: 11 PASS, ambas ordenaciones del alias y nueve controles previos del prototipo.
- `084413-944f88b9`: fallo de Ruff F811 en el nuevo test permanente; no llegó a pytest. Corregida la vinculación del fixture.
- `084447-32c7773e`: 14 PASS, regresión permanente en suite normal, descubrimiento público y ámbito/restauración de ajustes de consulta.

Python 3.12.15 y dependencias congeladas, PostgreSQL propio real y datos sintéticos, kernel nativo preparado por el runner. Se mantienen afinidad/controlador 0–3, memoria 3584 MiB sin swap, 512 tareas; PG propio 1 CPU/1536 MiB y Redis propio 0,2 CPU/128 MiB. No se tocó producción. Las fuentes se mantuvieron idénticas durante cada ejecución; procesos identificados por PID/start_ticks, temporales y contenedores propios ausentes al cierre. Recibo detallado: `cr09-first-page-batch-revision-alias-20261016.json`.

## Riesgos pendientes de la agrupación

La prueba de contención es condicionalmente sólida: cualquier limpio que termine entre los primeros24 debe pertenecer al prefijo24 de limpios; cualquier unknown seleccionado ya está hidratado. Requiere snapshot/censo/protocolo/orden y versiones coherentes. El fallback por selección no cubierta se conserva.

La cota72 limita padres, no hijos ni bytes. Si 24 unknown elegibles desplazan a todos los limpios, el prototipo hidrata también los primeros24 limpios que finalmente no aparecen. Un limpio con muchas relaciones legítimas de municipios/categorías/servicios puede añadir trabajo. Esa expansión está demostrada por el recorrido, pero su magnitud y posible regresión no están medidas. Falta un control sintético acotado con fanout heterogéneo y desplazamiento completo; no se afirma OOM sin medirlo.

Faltan controles dirigidos de limpios con fecha NULL, empate de fecha/rank/UUID en la frontera24/25 y mezcla intencionada de unknown válidos e inválidos. Las pruebas anteriores de límites1/24/48/49 no sustituyen estos escenarios. También hay que separar la expiración durante la petición del snapshot: RR no congela el reloj Python. La doble validación modifica instancias mediante ModelForms; las normalizaciones examinadas son idempotentes para las entradas aceptadas actuales, no una prueba general de pureza para formularios futuros.

## Investigación externa contrastada

El caso [Stack Overflow sobre prefetch lento](https://stackoverflow.com/questions/42838010/django-prefetch-related-optimize-query-but-still-very-slow) describe muchas asignaciones Python pese a poco SQL y una respuesta propone `to_attr`. Es experiencia comunitaria sobre versiones antiguas, no una solución transferible automáticamente a este proyecto. Aquí ese frente ya tuvo controles propios y no basta repetirlo por reputación de la fuente.

La fuente primaria [Django #30842](https://code.djangoproject.com/ticket/30842) está cerrada como duplicada; su referencia [#20577](https://code.djangoproject.com/ticket/20577) está resuelta mediante filtrado diferido de QuerySets relacionados. El Django instalado conserva `_defer_next_filter`/`_deferred_filter` en `django/db/models/query.py`. Por tanto, no puede presentarse ese ticket antiguo como un parche nuevo ausente de nuestra versión. Esto tampoco demuestra coste cero en las relaciones actuales.

La [guía oficial de optimización Django5.2](https://docs.djangoproject.com/en/5.2/topics/db/optimization/) respalda medir antes y después y revisar la evaluación/reutilización de QuerySets. La aplicación concreta aquí es evitar dos construcciones equivalentes dentro de una petición, preservando su semántica; los números locales y las regresiones tienen prioridad sobre porcentajes publicados por terceros.

## Contrato, simplificación y siguiente decisión

No se ha demostrado que retirar requisitos de privacidad, consentimiento, autoridad o trazabilidad sea una optimización aceptable. Sí hay duplicación técnica evitable en la construcción de contextos; eliminarla requiere preservar identidad, snapshot y guards. Los caminos experimentales de validación escalar que no tienen usuarios productivos son candidatos de mantenimiento, no un ahorro temporal demostrado: no se eliminan en paralelo a esta corrección para fabricar una atribución.

Los tres informes independientes adjuntos son entradas de revisión, no aceptación automática. El hallazgo del alias ya fue contrastado; el fanout y los huecos de cobertura siguen abiertos. El grafo actualizado se cortó en89e0756 con extracción de21archivos Python y adiciones semánticas parciales de7documentos: no es una renovación semántica de todo el repositorio ni incluye todavía esta corrección/test nuevo. No representa coste cero de agentes ni documentación exhaustiva.

Orden de trabajo: terminar controles de fanout/orden/expiración; decidir la política con esos resultados; integrar sólo la variante justificada, promoviendo regresiones a suite normal; verificar aplicabilidad funcional de la versión común; preparar imagen con las fuentes reales y ejecutar el corto limpio sin perfiladores. Si cumple, repetir una vez antes del recorrido largo; si falla, conservarlo y diagnosticar por separado.

La matriz83 mantiene nueve familias de cierre y exige N3 sobre una versión integrada común. Los cuatro bloques históricos y estas pruebas focales no se suman para declarar N3. La exportación grande provisionalmente aceptada por el usuario no elimina el criterio del directorio. CR10, GS01, BF/BB y C conservan su alcance posterior. Las variaciones del portátil con cargador no se atribuyen al código.

## Ampliación: orden y relaciones fuera de página comprobados

Run `20261016-085117-b3e1def5`, base `fb4c490`, **4PASS/0fallos/0errores/0omisiones**. Fuentes congeladas, procesos por PID/start_ticks, temporales y contenedores propios verificados al cierre. Recibo `cr09-first-page-batch-order-fanout-20261016.json`.

Tres casos dirigidos preservan cuerpo, total e IDs exactos y exigen reutilización sin fallback: empate de fecha con UUID, empate de relevancia/fecha con UUID y dos fechas NULL limpias que deben preceder a las fechas no nulas. Los Dirty se sitúan expresamente alrededor de la frontera24/25 y conservan su generación.

El cuarto caso fuerza24unknown válidos seleccionados y un limpio desplazado con128municipios legítimos sintéticos. Se observa lo siguiente; son cardinalidades, no tiempos ni bytes:

| Brazo | Contextos y padres materializados | Municipios del limpio desplazado |
|---|---|---:|
| Nativo | 24pending +24seleccionados | 0 |
| Agrupado | 48padres en un contexto | 128 |

Esto confirma LOGIC-02 como expansión real del trabajo, sin demostrar regresión temporal ni consumo desproporcionado de memoria. La paridad funcional no decide el ROI: antes de adoptar hay que medir este escenario heterogéneo con el mismo control A/A y orden rotado, manteniendo recursos y GC. No se impone una cota arbitraria a relaciones del producto para rescatar el resultado. El caso cubre rank igual, no todos los ranks distintos ni expiración durante petición; esos alcances siguen diferenciados.
