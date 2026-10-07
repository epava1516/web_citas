# Checkpoint de atribución del listado

Fuente `aedfa2db1d7b5e130e21da3cdda2315ba95fd79a`. Tres pruebas PostgreSQL correctas; fuentes, huellas de artefactos y limpieza verificadas. Ruta `/es/`, mismo seed y nivel de instrumentación. Una petición por tamaño mediante DjangoClient; no es carga TCP concurrente.

| Candidatos | Queries | SQL execute (s) | Listings creados | Validaciones (calls / s) | Render HTML (s) | Request (s) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 70 | 0.370903 | 100 | 100 / 0.197959 | 0.101740 | 1.122757 |
| 1000 | 70 | 0.538131 | 1000 | 1000 / 1.669809 | 0.069146 | 3.826421 |
| 10000 | 70 | 3.359683 | 10000 | 10000 / 18.604750 | 0.078160 | 34.650646 |

[Datos completos por modelo, procedencia, prefetch y patrones SQL redactados](evidencias/listado-coste-checkpoint0110.json). Cada patrón conserva calls, total_time y mean_time en segundos; se verificó que calls y tiempos reconciliaran con los totales SQL. Parámetros y literales sensibles no se conservan. Relaciones materializadas se registran por modelo; memberships por relación son referencias, no filas SQL ni entidades distintas.

SQL execute observa el intervalo del cursor, con comunicación/driver/buffering; no separa CPU PostgreSQL ni fetch/conversión posteriores. Supone 33,04%, 14,06% y 9,70% del request respectivamente. No alcanza la heurística prefijada de predominio del 50%; no se ejecutó EXPLAIN ni se instaló pg_stat_statements. No se concluye ausencia de coste SQL o contención bajo concurrencia.

A 10000: contexto 15,560136s; validaciones directas 18,604750s; iteración Listing 4,203557s; iteración Photo 6,993817s; prefetch de fotos 7,103854s. Iteración incluye SQL lazy/fetch/conversión/from_db; prefetch incluye iteración; contexto contiene prefetch. Validación y render pueden ejecutar SQL lazy. Estos intervalos se solapan: no sumarlos ni atribuir total−SQL a validación Python.

`rows_returned` (filas entregadas por consulta), `rows_affected` (filas modificadas) y `rows_scanned`/`rows_examined` (trabajo de lectura del motor) son not_measured. Objetos ORM y rowcount no sirven para deducirlos. CPU/waits/locks/I/O/RSS, serialización separada y materialización CPU exclusiva también son not_measured. Sin reset de cachés OS/PG; ejecución secuencial 100→1000→10000, caché Django DummyCache, host compartido e instrumentación con coste propio.

Decisión: priorizar trabajo repetido dentro de validate_submission, medido directamente, y localizar construcción/validación de formularios de detalles/contacto antes de aplicar reutilización limitada a una petición. Mantener controles completos por candidato, elegibilidad, orden, recuento y páginas de24; exigir equivalencia negativa y repetir este mismo checkpoint antes/después. Contexto sigue siendo sustancial; los contadores de objetos no prueban por sí solos predominio de materialización.

Carga contractual intacta:10000 anuncios/20rps/900s, mezcla documentada y uploads limitados, p95<800ms y errores<1%. Demora del generador p95≤10ms/p99≤25ms/máximo≤100ms, noemitidas0%, timeout65s y drain70s. El antecedente conserva INVALID; la corrección independiente del cliente no acredita una mejora del backend. Este checkpoint no emite PASS/FAIL contractual ni sustituye el próximo ensayo.

## Localización dentro de validación

Diagnóstico posterior fuente d607759: tres tamaños y misma instrumentación ampliada entre filas; PostgreSQL correcto, fuentes y limpieza verificadas. [Eventos completos](evidencias/listado-formularios-coste0110.json). A10000, constructor SnapshotDetails9,980923s/10000 llamadas, full_clean3,724850s; Contacts constructor1,099341s/full_clean1,216976s. full_clean contiene campos/clean/post_clean: no sumar estos subeventos. Request33,503094s; no atribuir su diferencia respecto a la matriz anterior a mejora del backend, que permanece intacto.

Siguiente cambio elegido: preparar campos SnapshotDetails una vez por contexto de petición y preservar campos independientes por formulario e instancia, con limpieza nativa por candidato. Evitar memoizar autorización, elegibilidad o resultados completos. Constructor domina el coste medido dentro de esa validación; no demuestra que sea el único coste del request. Condición de aceptación: equivalencia positiva/negativa, normalización e independencia de campos y comparación con esta misma instrumentación.
