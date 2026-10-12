# MOD-08: estudio de la segunda opción, consultas SQL

## Resultado

Existe trabajo SQL que crece con el historial de evidencia, pero las mediciones
disponibles no demuestran que falte un índice ni que una reescritura SQL concreta
resuelva el SLO. Antes de ensayar cambios, se revisaron las pruebas existentes:
planes de cadena, comparación inline HTTP y optimizaciones de índices/pipeline
ya integradas. No se repitió un ensayo descartado ni se cambió la aplicación.

## Evidencia del VPS

Reanálisis offline del diagnóstico nativo `20261012-031633-f088a71b` en 8 CPU,
fuente 5d90028. Los contadores se agrupan antes y después por usuario, queryid y
toplevel. La primera salida auxiliar no agrupada se conserva sin usarla como
evidencia; la salida definitiva verifica las sumas agrupadas.

| Consulta etiquetada | Filas tempranas, sumadas | Filas tardías, sumadas | Ejecución temprana | Ejecución tardía |
| --- | --- | --- | --- | --- |
| Eventos con rights_evidence_link, 4 llamadas | 340 | 9844 | 8.450 ms | 224.092 ms |
| Una familia con rights_evidence_row_hash, 4 llamadas | 226 | 4978 | 8.902 ms | 180.067 ms |

No son muestras comparables de una candidata ni latencias de request. Son
deltas del motor durante dos ventanas diagnósticas de distinto historial.
Sólo se conocen las etiquetas fijas: no se asigna el segundo queryid a una
tabla concreta sin el SQL o un mapeo confirmado. Capturas py-spy parciales;
los contadores PostgreSQL son evidencia distinta del muestreo de pilas.

La ventana tardía dura 6.178s y suma 12.239s en sentencias toplevel de todo el
rol. Una consulta sin etiqueta aporta 11.452s y 19 llamadas. No convertir ese
agregado en un tiempo del request ni en CPU exclusiva: los contadores incluyen
otros procesos con el mismo rol y consultas terminadas en la ventana que pueden
haber comenzado antes. No sumar tiempos nested a sus padres.

El backend observado aparece 98 veces idle in transaction/ClientRead tanto en
temprana como tardía; las observaciones active sin wait_event son 42 y 57.
ClientRead significa que PostgreSQL espera al cliente, no un bloqueo de filas.
No aparecen waits de tipo Lock en estas dos capturas, pero el muestreo cada
25ms puede omitir esperas cortas. Tampoco demuestra ausencia de locks general.

[Contadores, eventos agregados y límites](mod08-vps-sql-segunda-opcion-20261012.json).

## Lo que ya se investigó

[Planes existentes](mod08-chain-explain-20261011.md) sobre 548 eventos, con
historia generada por servicios, login restringido y PostgreSQL 17:

| Consulta | Original | Lectura sin hashing, control inválido para uso productivo | Hash directo equivalente en ese corpus |
| --- | --- | --- | --- |
| Eventos, 548 filas | 8.242 ms | 0.469 ms | 4.954 ms |
| SelectionRead, 288 filas | 7.494 ms | 0.543 ms | 5.232 ms |
| CoverageRead, 256 filas | 11.215 ms | 0.846 ms | 7.262 ms |

Son medianas de cuatro EXPLAIN TIMING OFF por variante, no HTTP. Las variantes
conservaban la estructura observada de planes por nivel. En ese corpus los
sorts eran en memoria, sin spill, y tras calentamiento no había lecturas de
buffers desde disco. Seq Scan/Hash Join no prueba por sí solo un índice ausente.
No extrapolar la distribución de un expediente a muchos expedientes.

[Candidata inline HTTP retirada](mod08-inline-http-20261011.md):

| HTTP del ensayo histórico, 20 muestras por variante | Original | Inline |
| --- | --- | --- |
| Mediana | 797.984 ms | 789.795 ms |
| p95 | 819.964 ms | 829.377 ms |

Se conservaron las comprobaciones y productores, con pruebas de siete familias,
zonas, formatos, Unicode, tombstones, runtime y concurrencia. El resultado
guardado no justificó la duplicación SQL productiva. Son mediciones anteriores,
no una nueva comparación VPS ni una aceptación de capacidad; los cambios de
perfil energético del portátil impiden atribuir diferencias entre entornos al
código. No restaurar esta candidata sólo por el resultado EXPLAIN favorable.

[Índices y pipeline ya verificados](mod08-index-pipeline-combined-gate-20261011.md)
forman parte del estado integrado. No proponerlos como trabajo nuevo. Pipeline
reduce rondas de comunicación, no paraleliza las sentencias de PostgreSQL.

## Mecanismo y dirección técnicamente útil

validate_chain recupera todos los eventos ordenados, comprueba enlaces en
Python y vuelve a hashear las filas físicas de siete familias. inspect_batch
puede ejecutar cuatro validaciones al inspeccionar cuatro páginas. Los propios
audits avanzan la cadena: reutilizar una cabeza anterior sin volver a validar
no conserva automáticamente las garantías. La vía existente de ChainTicket
requiere cabeza coincidente y atestación runtime fresca; no extenderla como
caché de permisos o validez.

Las funciones de hash son LANGUAGE sql, no PL/pgSQL. Sus cláusulas SET de
search_path y timezone impiden el inlining ordinario; PostgreSQL documenta
esa restricción en su [wiki de inlining](https://wiki.postgresql.org/wiki/Inlining_of_SQL_functions).
Esto explica un candidato de coste por fila, pero no su impacto HTTP.
Las SET tienen finalidad semántica y de aislamiento: no quitarlas globalmente.

La siguiente comprobación justificada sería un diagnóstico finito en VPS que
capture las ocho consultas exactas y sus planes al nivel tardío realmente
observado, diferenciando request de tareas de fondo. Reutilizar la metodología
existente y datos creados por servicios; no el esquema parcial de la prueba ORM.
Registrar por separado calls/filas, Execution Time, buffers/spill, SERIALIZE y
reloj del driver hasta consumir resultados. No sumar parent/nested ni equiparar
tiempo de execute a tiempo completo de pipeline.sync/fetch.

Sólo ante un plan problemático nuevo elegir un índice o reescritura específica.
Si los planes siguen baratos y domina recalcular/verificar evidencia, el cambio
necesario es reducir trabajo redundante con equivalencia de garantías, no
retocar índices. Validar cambios propios de cabeza, caducidad, permisos,
alteración física, rollback y concurrencia antes de cualquier medida HTTP.

Fuentes oficiales: [pg_stat_statements 17](https://www.postgresql.org/docs/17/pgstatstatements.html),
[Using EXPLAIN 17](https://www.postgresql.org/docs/17/using-explain.html),
[EXPLAIN y SERIALIZE](https://www.postgresql.org/docs/17/sql-explain.html),
[pipeline Psycopg](https://www.psycopg.org/psycopg3/docs/advanced/pipeline.html).
EXPLAIN no mide red ni adaptación Python; sus costes estimados no son segundos.
No nueva mejora HTTP medida, ni cambio productivo, ni aceptación global/N3.
