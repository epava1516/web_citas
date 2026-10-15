# Población de búsqueda compartida: experimento CPU acotado

Run `133514-e21fa96b`, base `f02a5fd` más test explícito:1PASS/95.50s, fuentes intactas y limpieza independiente de raíz/hijo/backend/temporal/PG/Redis. [Recibo y bloques](cr09-busqueda-poblacion-compartida-cpu-terminal-20261015.json).

Población capturada del Paginator actual tras selección/guardia nativas. Sin DISTINCT multiplicador. Un snapshot propio readonlyRR por caso; original count+página y variante COUNT OVER, mismo orden/IDs/conteo verificado en cada operación. Cinco casos, tres bloques alternando orden,8operaciones por variante/bloque:240operaciones medidas. BackendCPU utime/stime100Hz, sin extensión de estadísticas ni SQL/datos exportados.

| CPU media por operación de conteo+página | Original | Compartida |
|---|---:|---:|
| photography página1 |43.333ms|41.250ms|
| photography página2 |45.417ms|41.250ms|
| synthetic página1 |45.833ms|38.750ms|
| synthetic página2 |46.250ms|40.833ms|
| Sin coincidencias página1 |6.250ms|7.500ms|

Ahorro en coincidencias≈2–7ms por búsqueda; rangos de bloques se solapan en tres de cuatro casos. No representa una nueva solución del déficit de demanda medido ni prueba de causalidad/reproducibilidad global. Tres bloques dentro de una sola ejecución no equivalen a tres ensayos HTTP independientes. El caso vacío empeora. No prueba filtros con multiplicación, carreras ni páginas vacías fuera de rango.

Decisión: no reactivar window en producto ni lanzar otra carga HTTP desde esta evidencia. Se conserva el FAIL limpio anterior de esa variante, no se reescribe como éxito. Próxima hipótesis distinta: coste de parseo/planificación de consultas repetidas y mecanismo de preparación/binding por verificar con fuentes oficiales; ninguna modificación global de driver sin evidencia y pruebas de tipos/transacciones/invalidation.

Último p95 limpio16.572804s FAIL sin actualización; CR09/N3 siguen abiertos. No cambios de producto, workers, cuotas o semántica de publicación.
