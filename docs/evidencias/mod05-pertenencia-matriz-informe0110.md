# MOD05: matriz del cambio de pertenencia conservado

**12 casos PostgreSQL/Client/TCP correctos; matriz cerrada localmente. No es un gate de carga.**

[Manifiesto previo](mod05-pertenencia-matriz-manifiesto0110.json), [revisión independiente](mod05-pertenencia-matriz-revisada0110.json), [recálculo](mod05-pertenencia-matriz-analisis0110.json), [originales/fuentes](mod05-pertenencia-matriz-artefactos0110.json). 454,70s pytest / 456,72s runner. Fuente de producto2dd4ca5; parche probado del arnés únicamente conserva los logs originales tras retirar cada servidor. El archivo y manifiesto registran huellas exactas.

## Preparación y alcance

Se reutiliza la equivalencia de9PG y el contraste480TCP de la intervención aceptada. Esta matriz usa el mismo helper de población, preparación oficial refresh_publication_state con VACUUM/ANALYZE e instrumentos que la matriz anterior. Dos fixtures: repetido y diverso; este último cambia descripciones, alternativas y telegram válidos, pero mantiene fotos, teléfono y otras relaciones compartidas. No representa diversidad general. Estados al día y native_unknown=0 durante estas mediciones, a diferencia del contraste dirty=1. No se suman poblaciones.

Por celda, Client: warm1, cinco controles sin profiler y un request perfilado en /es/ y /en/?q=photography. TCP: warmup y cinco controles secuenciales por seis rutas ES/EN,30porcelda/180total, cuatro workers síncronos propios. Las reglas, modelos, SQL y render se instrumentan en Client aparte. Overhead causal de wrappers, post_init y observador WSGI no cuantificado. Sin cargas30/60/900, cambios de recursos, caché ni servicios ajenos.

El contador de39queries típico permanece al crecer candidatos; el primer listado perfilado de100 registra42 en ambosfixtures, no crecimiento por candidato. No se ha atribuido esa diferencia de eventos a una operación concreta. Se conservan las muestras de cada celda; los perfiles no son promedios de sus controles.

## Medias WSGI observadas

Cada familia tiene10observaciones/celda, cinco por cada ruta ES/EN con peso1/2. D usa las tres medias con pesos1/3, no medianas.

| Fixture | Candidatos | Listado ms | Búsqueda ms | Ficha ms | D ms | 20D worker-s/s |
|---|---:|---:|---:|---:|---:|---:|
| diverse | 100 | 298.951 | 275.262 | 121.511 | 231.908 | 4.638159 |
| diverse | 1000 | 210.874 | 213.299 | 102.845 | 175.673 | 3.513451 |
| diverse | 10000 | 237.579 | 280.303 | 102.150 | 206.677 | 4.133543 |
| repeated | 100 | 315.754 | 275.371 | 146.992 | 246.039 | 4.920779 |
| repeated | 1000 | 224.150 | 210.372 | 104.439 | 179.654 | 3.593077 |
| repeated | 10000 | 274.924 | 285.065 | 105.319 | 221.770 | 4.435395 |

Upload/U y W total: not_measured en esta matriz. No trasladar el único upload histórico a estas poblaciones. A10000, 20D es superior a cuatro incluso antes de uploads: es una comprobación aritmética de viabilidad usando controles secuenciales, no una prueba de estabilidad/saturación ni CPU. No se declara una mejora causal frente a matrices anteriores ejecutadas en otro momento ni se resta el ΔD del contraste dirty del D histórico cargado. Las celdas100 más lentas que1000 muestran variación entre poblaciones/procesos; no se interpreta como escalado inverso del algoritmo.

## Perfil actual de10000

| Fixture / Client ruta | Queries | SQL driver ms | Request perfilado ms | Control Client medio ms |
|---|---:|---:|---:|---:|
| diverse /es/ | 39 | 93.163 | 198.544 | 290.903 |
| diverse /en/?q=photography | 39 | 167.801 | 304.264 | 336.627 |
| repeated /es/ | 39 | 90.456 | 223.939 | 251.235 |
| repeated /en/?q=photography | 39 | 147.820 | 331.625 | 281.582 |

Cada request de10000 materializa24Listing/24Revision/24Person/24PhoneClaim,24Rate,48Photo y1Blob, además de los objetos de catálogo y relaciones identificados en el JSON. Son instancias creadas observadas, no entidades únicas ni filas SQL. Details.full_clean y Contacts.full_clean registran24calls cada uno, no10000validaciones en la ruta actual.

Dominantes normalizados: calls/total_time/mean_time y fracción del driver observado están publicados por celda. El perfil incluye también SAVEPOINT/transacciones: su tiempo no se atribuye a CPU PostgreSQL. A10000, las lecturas de página/recuento/hidratación y comprobación all_state_current aparecen entre los eventos dominantes. El render observado contiene evaluación lazy y otras lecturas; no se suman intervalos anidados como fases exclusivas.

Los tiempos por regla incluyen inclusive/exclusive, calls, mean/max exclusive e hijos instrumentados descontados. Exclusive solo resta hijos directos registrados y no es CPU. p95 de reglas no medido. Los wrappers de la matriz no interceptan toda función nativa; por ejemplo publicly_visible importado directamente en publication_state no queda envuelto por cambiar el atributo del módulo moderation. validate_submission sí se mide a través de la llamada de moderation, y formas/render se miden directamente. No afirmar un perfil exhaustivo del guard.

SQL acumulado mide execute del driver, excluye fetch/conversiones fuera de ese ámbito y no equivale a planificación o CPU del servidor. SQL/validación/render pueden solaparse por lazy. No se calcula validación como total−SQL. rows_returned/affected/scanned, CPU/resources, construcción/compilación separada, planificaciónPG, overhead causal y validación no cubierta por instrumentos: not_measured. Los planes EXPLAIN de la intervención se reutilizan en su alcance propio, no como tiempos actuales de estos controles.

## Reconciliación, limpieza y decisión

180IDs únicos dentro de cada cohorte de30, rutas reales state/trusted_state/native_unknown0 en listado/búsqueda, clocks/PID y registros originales coincidentes exactamente con JUnit. Respuesta, orden y count comprobados por fingerprints y asserts de los casos; las fichas verifican firma y Listing/revision antes de canonicalizar exclusivamente el token volátil. El cierre WSGI puede seguir a la recepción completa del cliente y no se fuerza anidamiento.

Fuentes y artefactos intactos hasta la revisión. Ausencia de bases y medios comprobada independientemente; PIDs observados ya no existen. Gunicorn retirado antes de copiar logs; sin otros servidores/cargas propios ni servicios ajenos alterados. Fuentes liberadas.

El cambio conserva la equivalencia y efecto local aceptados, pero la matriz no permite afirmar que resuelva la capacidad de cuatro workers. Las validaciones de24filas ya no dominan por número sobre toda la población; no se propone repetir validaciones genéricas o ampliar el ORM por nombre. Los datos justifican considerar capacidad/concurrencia junto con trabajo evitable, sin optimizar indefinidamente ni aumentar recursos automáticamente. Cualquier nueva comparación4/6 requiere autorización renovada y una propuesta concreta sobre MOD05 actual; la comparación antigua, INCONCLUSIVE con otra implementación/entorno, no resuelve esta hipótesis.

CR09 y GS01 abiertos, goal activo, porcentajes y FAIL/INVALID/PASS históricos preservados con sus ámbitos. El diagnóstico30 y gate60 anteriores siguen VALID/FAIL. Seis workers candidata no adoptada. No gate60 ni900 ejecutados ahora; contrato20RPS900s/p95<800ms/errores<1% y umbrales íntegros. [Script reproducible](mod05-pertenencia-matriz-analisis-script0110.py).
