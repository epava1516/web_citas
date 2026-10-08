# MOD05: orden del subconjunto desconocido — intervención retirada

La intervención conserva la equivalencia comprobada, pero **no cumple el efecto HTTP prefijado y se retira**. Se restauró exactamente `apps/listings/publication_state.py` de `531bd08`; el candidato probado permanece en el archivo de evidencias. No se repetirá esta variante para buscar un resultado favorable.

## Evidencia y poblaciones

[Hipótesis y criterios anteriores al cambio](mod05-orden-desconocidos-manifiesto0110.json): eliminar únicamente la ordenación de la enumeración e hidratación intermedias de candidatos desconocidos. Mantener la consulta final, filtros, ranking, orden promocional, recuento, páginas y guard nativo fresco. El umbral de efecto era una reducción de la **media HTTP de al menos 20 ms y 5 %**, en listado y búsqueda, en ambos pares y ambos fixtures. No es un SLO nuevo.

[Equivalencia PostgreSQL](mod05-orden-desconocidos-funcional-revisada0110.json): 31 casos correctos, incluida la comparación nativa y dependencias condicionales. [Contraste revisado](mod05-orden-desconocidos-ab-revisada0110.json): dos casos correctos, 240 controles TCP secuenciales, fixtures repetido/diverso de 10.000 anuncios, cuatro workers síncronos propios. Bloques antes→después→después→antes, cinco recorridos por seis rutas ES/EN en cada bloque. Cada celda familia/bloque tiene diez observaciones; cada familia/variante, veinte. Respuesta equivalente, ruta `state/trusted_state` y un desconocido en listado/búsqueda; variante realmente servida comprobada en cada request.

No hubo carga de 30/60/900 segundos. Las pruebas usan un adaptador exclusivo del entorno sintético para servir la función original congelada y el candidato, sin envolver reglas nativas. El observador WSGI común añade metadatos; su overhead causal no está medido. Los controles no incluyen profiler SQL/reglas intrusivo.

## Resultado HTTP

Reducción de media HTTP antes−después, en milisegundos:

| Fixture | Par | Listado | Búsqueda |
|---|---|---:|---:|
| Repetido | 4 bloques: 0 frente a 1 | −12,902 | −12,686 |
| Repetido | 3 frente a 2 | 17,688 | 42,994 |
| Diverso | 0 frente a 1 | −40,789 | 22,594 |
| Diverso | 3 frente a 2 | 36,844 | 77,168 |

Solo cuatro de ocho celdas cumplen conjuntamente los dos umbrales. La media agregada favorable de búsqueda no basta para aceptar el cambio: listado no reproduce beneficio en ambos pares.

Medias WSGI observadas, antes→después:

| Fixture | Listado (ms) | Búsqueda (ms) | Ficha (ms) |
|---|---:|---:|---:|
| Repetido | 353,429→351,452 | 391,135→376,226 | 99,800→107,341 |
| Diverso | 366,519→368,400 | 472,007→422,098 | 114,037→105,051 |

Con pesos 1/3, el ΔD descriptivo observado es 3,115 ms y 19,005 ms respectivamente; 20ΔD es 0,062295 y 0,380092 worker-s/s. Incluye fluctuación de ficha, cuya implementación no cambió; **no es ahorro causal aceptado ni capacidad acreditada**. Uploads/ΔU: `not_measured` en estos controles; no se sustituye la estimación del diagnóstico de recursos por estas poblaciones.

WSGI mide desde entrada al callable hasta finalizar iteración/cierre del response. En ocho controles repetidos, ese cierre ocurrió después de que el cliente completara su recepción, como máximo 0,908 ms después; no exige que ambos intervalos sean anidados. Emisión y entrada son compatibles con el reloj monotónico común del host. IDs únicos, variantes, rutas, PIDs y artefactos se verificaron independientemente.

## Lecturas y planes separados

Se capturaron las tres lecturas con mayor tiempo de `cursor.execute` por variante/fixture en una petición Client de búsqueda EN sintética, y se ejecutó EXPLAIN (ANALYZE, BUFFERS) sobre esas lecturas en transacción de solo lectura propia. La selección dominante cambia entre variantes: no son seis consultas emparejadas por identidad. Parámetros no persistidos; literales de texto del plan redactados. Se conservó el JIT observado. Estas sondas calentaron cachés antes de los controles; no se vaciaron cachés ni modificaron servicios.

En el fixture diverso, la enumeración ordenada del desconocido presenta 1,241 ms de planificación, 96,673 ms de ejecución y 61.785 shared hits; el candidato sin ordenar, 0,552 ms, 20,417 ms y 14.051 hits en el plan separado. Son ejecuciones exploratorias distintas, no una estimación reproducible de ahorro HTTP. La selección final de página continúa con 85,180/95,699 ms de ejecución en los planes antes/después y 61.776 hits en ambos. En repetido, los planes de página presentan 36,290/29,185 ms; no se extrapolan a CPU ni a todas las rutas. Recuento también permanece.

`cursor.execute` mezcla servidor, esperas y recepción, y no mide CPU PostgreSQL ni toda la compilación/conversión Python. Planificación y ejecución son campos directamente proporcionados por EXPLAIN separado. `Actual Rows` describe el nodo indicado y sus loops, no filas escaneadas ni objetos ORM. CPU por operación, validación por regla, transferencia/conversiones y render desglosados en este contraste: `not_measured`; los perfiles anteriores mantienen su propia versión/alcance y solapamientos lazy. No se calcula validación como total−SQL.

## Decisión, límites y limpieza

Retirar la modificación de producto; conservar el arnés opt-in, referencia congelada y [muestras, planes, logs y fuentes probadas](mod05-orden-desconocidos-artefactos0110.json). La preparación inicial fue cancelada sin observaciones al detectar un import ausente; [revisión](mod05-orden-ab-preparacion-revisada0110.json) conserva el hecho y su limpieza. No se presenta como fallo del backend ni se omite del historial.

La evidencia hace insuficiente la hipótesis «ordenar el subconjunto explica el coste restante». La consulta final de página conserva trabajo sustancial en búsqueda diversa; se necesita contrastar su estructura y dependencias con el código vigente antes de seleccionar otra intervención. Estos planes no prueban que domine el HTTP ni autorizan índices, prepared statements o eliminación de totales por su nombre. No se encadenan nuevas variaciones de esta intervención.

Fuentes congeladas y hashes intactos hasta la revisión terminal. Bases y medios propios ausentes con consulta independiente; los ocho PIDs de workers observados ya no existen. Gunicorn se retiró antes de archivar sus logs. Recursos normales/ajenos intactos. Sin aumento de workers, PostgreSQL, caché, despliegue ni nuevas cargas.

El diagnóstico autorizado de recursos permanece **VALID / FAIL**, D=239,186 ms y W=4,878267 worker-s/s en su propia cohorte. El gate VPS de 60 s permanece VALID / FAIL; los PASS de portátil y los FAIL/INVALID históricos conservan su alcance. CR09 abierto, goal activo por autorización del usuario, seis workers solo candidata. Los 900 s continúan bloqueados; porcentajes y contrato intactos.

[Recálculo completo](mod05-orden-desconocidos-analisis0110.json) y [script](mod05-orden-desconocidos-analisis-script0110.py).
