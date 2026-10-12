# MOD-08 — Plan y evaluación del hash SQL de lectura — 2026-10-11

Autorización: «traza un plan de acción discutiéndolo con el notebook y aplícalo». Alcance finito; no reanudación de la aceptación general ni publicación.

## Plan discutido y aplicado

1. Cambiar exclusivamente los hashes calculados al leer EVENT y las siete tablas fuente. Cualificar funciones `pg_catalog`, normalizar `created_at` tipado a UTC y conservar exactamente JSONB/texto/UTF8/SHA256. Productores, DDL, triggers, head locks, pipeline, lecturas y reglas frescas intactos.
2. Contrastar con las funciones originales del productor en PostgreSQL: siete familias no vacías, tombstone permitido, doce combinaciones TimeZone/DateStyle, JSON/Unicode/nulos/microsegundos/DST y search_path hostil. Ejecutar regresiones de cadena, rol runtime, concurrencia, pipeline y lote.
3. Comparar HTTP TCP completo: Gunicorn2 sync, LOGIN restringido y 1500 revisiones/~16MiB proyectados. Sembrar 64 lotes por servicios reales, cerrar conexiones y crear una plantilla privada en PostgreSQL propio. Cada petición medida usa un clon idéntico de esa historia y commits normales. Controles originales mediante constantes parcheadas sólo en WSGI de tests, sin flags productivas, rewrite de driver, outer rollback ni instrumentación SQL. Warm POST de ambos workers, veinte muestras por variante con orden ABBA/BAAB; eliminar cada clon antes del siguiente.
4. Retener sólo si equivalencia/seguridad pasan y el resultado justifica el cambio; documentar ruido, límites y cualquier resultado negativo. No convertir el escenario parcial en aceptación contractual 2s/5s.

## Revisión crítica de NotebookLM

Consulta y respuesta completas conservadas en `mod08-notebook-inline-plan-*20261011.*`. La consulta correctiva explicita nuestro plan y desacuerdos. Notebook respalda una prueba finita, pero sus propuestas no constituyen evidencia.

Correcciones locales: las funciones actuales son LANGUAGE SQL, no PL/pgSQL; 28.8/18.817ms son sumas de medianas separadas, no tiempo conjunto. `directory_snapshot.seed_or_restore` sólo restaura el bootstrap del directorio: no usarlo para historia aprobada. TEMPLATE conserva datos/secuenciadores/estadísticas, no garantiza buffers compartidos idénticos. Health no calienta el flujo de lote: usar POST real. Incluimos EVENT además de siete sources. No hay pérdida del parseo textual de timestamp en la candidata: lee la columna timestamptz tipada con AT TIME ZONE UTC; las pruebas de zonas hostiles son pertinentes y se ejecutan.

## Incidencias preservadas

- 20261011-123126-4205bb41: runner ERROR antes de pytest por import sin ordenar del test nuevo; corregido.
- 20261011-123205-18050eaa: 49 PASS/12 FAIL; el test nuevo intentaba crear un tombstone con motivo no permitido. El guard lo rechazó correctamente; sustituido por `expired_payload_purged`.
- 20261011-123430-59b17418: interrumpido deliberadamente antes del benchmark tras ocho fallos del test nuevo en fetch de timestamps con DateStyle SQL/German. Las comparaciones SQL de hashes ya habían pasado; psycopg no admite esos DateStyle en su loader textual. Separamos equivalencia SQL bajo esos formatos de validación completa con formato ISO soportado. No atribuimos esa limitación del driver a la candidata ni declaramos PASS el runner interrumpido.

## Resultado y decisión

Runner `20261011-123640-097bae75`: **78 PASS, 0 fallos/errores/skips**, 248.26s JUnit. Las 1171 huellas coincidían antes de editar documentación; contenedores PG/Redis y Gunicorn propios ausentes comprobados independientemente. Historia inicial de cada clon: 548 eventos y 256 lecturas de cobertura. Cada petición confirmó por una conexión independiente cuatro lecturas y ocho eventos nuevos tras commits normales. Selección 16777586 bytes; dos workers calientes y usados por ambas variantes. Fuente productiva de la candidata completa conservada en [patch retirado](mod08-inline-candidata-retirada-20261011.patch).

| HTTP TCP, 20 muestras/variante | Original | Inline |
|---|---:|---:|
| Mediana | 797.984 ms | 789.795 ms |
| p95 nearest rank | 819.964 ms | 829.377 ms |
| Desviación estándar | 17.778 ms | 33.032 ms |
| CPU de hilo WSGI, mediana | 456.246 ms | 451.137 ms |

p95 usa el elemento ceil(0.95×20)=19 de las veinte muestras ordenadas. No representa el p95 histórico de 383 lotes. Datos y límites completos en [JSON](mod08-inline-http-20261011.json). Workers: original 10/10 muestras, inline 9/11. En diez bloques contrabalanceados, ocho tienen media favorable y dos desfavorable, pero el efecto es pequeño e irregular; no se demuestra una mejora fiable del extremo p95 ni se atribuye causalmente toda la diferencia a CPU SQL.

**RECHAZADA como cambio productivo.** La mediana mejora 8.189ms (~1.03%) y p95 empeora 9.413ms (~1.15%), con mayor dispersión. Esta evidencia no justifica duplicación SQL productiva para el bloqueo original. `apps/safety/evidence_chain.py` restaurado byte por byte de HEAD; no modificación de producción retenida. Sin caché de autoridad ni omisión de controles. No aceptación 2s/5s ni reanudación de MOD08 general.

Después de restaurar, la candidata queda en `tests/capacity_chain_inline_candidate.py`: construye exclusivamente las dos funciones lectoras a partir del código original, con sustituciones AST comprobadas y parches sólo en tests; no modifica el driver ni transacciones. El benchmark HTTP histórico usó la candidata productiva del patch y controles de constantes test-only; no se ha repetido HTTP con el helper posterior. Gate posterior `20261011-124558-a4d43659`: **28 PASS/0 fallos/errores/skips**, 20.36s, 1172 huellas exactas y PG/Redis retirados verificados. Prueba equivalencia, validación completa con el helper y restauración de instrumentación; no añadir esos 28 al resultado de 78 como aceptación conjunta.

## Segunda opinión sobre los resultados

NotebookLM recibió resultados, método, ruido, límites y nuestra decisión propia. Coincide con el rechazo prudente. [Consulta íntegra](mod08-notebook-inline-resultados-consulta-20261011.txt) y [respuesta íntegra](mod08-notebook-inline-resultados-respuesta-20261011.json). Cualquier siguiente diagnóstico propuesto permanece hipótesis pendiente, sin aplicación automática ni aceptación por esta opinión.


Revisión propia de la segunda opinión: N=20 no demuestra determinísticamente la ausencia de beneficio; demuestra que aquí no lo acreditamos. Restar CPU de hilo WSGI a wall TCP mezcla perímetros: esa diferencia no es una fase medida. Los 16.7MiB son bytes proyectados, no una medida del tráfico PostgreSQL; no atribuir el residuo a ese volumen. `execute`/`fetchall` tampoco separan automáticamente ejecución del servidor, transporte y adaptación: psycopg puede recibir resultados durante execute. Un perfil puntual puede orientar funciones costosas, pero no promete identificar una causa única ni separar CPU de PostgreSQL/red/GIL/locks. El diagnóstico propuesto por Notebook queda sin ejecutar en este encargo finito.
