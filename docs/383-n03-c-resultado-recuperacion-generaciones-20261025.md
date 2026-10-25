# N03C — recuperación y aislamiento entre generaciones

25/10/2026. Alfa, N03 abierto, N00/N01/N06 aceptados3/13. Se adopta la corrección funcional ampliada conforme382, con33PASS finales y preservación del comportamiento de fallo propio tras generar el derivado. Los tiempos actuales aceptables y el diferimiento de optimizaciones marginales no eliminan esta corrección de concurrencia.

## Fallo reproducido y corrección

Referencia20261025-181549-690b123b: runnerERROR con2FAIL/0ERROR/0SKIP de pytest,42,686sJUnit,fuentes intactas. Dos conexiones PostgreSQL y barreras deterministas: worker antiguo adquiere lease; se induce caducidad del timestamp en DB; otro genera ready; al salir el antiguo reemplaza el derivado o cambia ready→failed. Los dos FAIL permanecen como evidencia; no se etiquetan PASS por ser esperados. No se esperaron tres minutos ni se simularon la base o los locks; se controlaron decode y el fallo OSError deliberado.

process conserva attempts y started_at de su lease. Al readquirir el lock sólo escribe si statusprocessing e intento/timestamp siguen siendo suyos. El UPDATE de fallo exige intento/timestamp propios y statusprocessing/ready, para conservar el fallo propio después de generar el derivado. Trabajador tardío no reemplaza archivos ni deshace ready, borrado u otro intento. No cambia elección de candidatos, detector, presupuesto de generación, cola ni configuración. Diff restringido a process; resto del AST de services idéntico, incluido ORB aceptado381. No se repite el benchmark del detector por un cambio ajeno a su implementación.

| Intercalación | Antes, referencia | Después, candidata |
| --- | --- | --- |
| Antiguo termina tras nueva generación | Reemplaza derivado nuevo: FAIL | Conserva derivado nuevo y ready: PASS |
| Antiguo falla tras nueva generación | ready→failed: FAIL | Conserva ready/errorvacío: PASS |
| Identidad de generación nueva | Intento2 existe pero no protege escrituras | Intento2/started_at/derivado preservados |

Primera candidata20261025-181844-c30b0964:32PASS/0FAIL/ERROR/SKIP,188,641sJUnit, conservada. Revisión posterior añadió un caso de fallo propio de comparación tras guardar ready y conservó su estado failed/reintento original mediante condición processing/ready de la misma generación. Candidata final20261025-183022-372b5094:33PASS/0FAIL/ERROR/SKIP,188,723sJUnit:16nuevos+11preparation_cleanup+6photos. El caso adicional inyecta OSError únicamente en comparación, comprueba failed/attempt1/derivado existente y recuperación ready/attempt2; no declara fallo de transporte real. Original intacto ante fallo de lectura, failed/attempt1 recuperable y restauración a ready/attempt2/WebPsinEXIF/firmas; replayready no regenera. Lease fresco omite/caducado recupera. Erasing/erased/purging/purged no abren storage ni resucitan. Cohorte mixta conserva fallidos0/3 y descarta agotados4/frescos;readyincomplete repetido por2Photo sólo se envía una vez,retirados/completados fuera. Lote101 continúa al resolver primer100;no promesa de orden/fairness. Once originales conservan retención de evidencia/referencias,pathscompartidos,fallo parcial,interrupción de limpieza,carrera con nuevo referente y procesado que no recrea purga. Seis flujos originales conservan privacidad/EXIF/duplicado/recorte/límites/alta tardía.

## Tabla de tiempos del selector

Milisegundos de recover_media_jobs.run, PostgreSQL real y delay capturado en memoria. Primera+5posteriores por cohorte, mediana/rango. No mide entrega al broker, worker, Beat, latencia del usuario ni espera de caducidad. tasks.py no cambia: no hay ganancia temporal afirmada ni anterior comparable. La referencia de carreras mide corrección, no este tiempo;188,641s/188,723sQA tampoco son latencia de aplicación. La tabla corresponde únicamente a la candidata final; no mezclar muestras de ambas pasadas.

| Queued | Antes | Primera después, ms | Mediana después, ms (rango) | SQL | Envíos capturados |
| --- | --- | ---: | ---: | ---: | ---: |
| 0 | Sin referencia comparable | 5.991 | 1.554 (1.520–1.603) | 1 | 0 |
| 1 | Sin referencia comparable | 3.020 | 1.704 (1.534–1.801) | 1 | 1 |
| 10 | Sin referencia comparable | 5.887 | 3.550 (3.359–3.997) | 1 | 10 |
| 100 | Sin referencia comparable | 6.588 | 3.831 (3.399–4.078) | 1 | 100 |
| 101 | Sin referencia comparable | 4.385 | 2.940 (2.632–3.757) | 1 | 100 |

## Auditoría y pendientes

1741huellas intactas en cada ejecución; entre referencia y primera candidata sólo cambia services.py; la final añade el caso16 y la anotación de seguimiento, explícitos en sus congelaciones. El código de aplicación continúa restringido a process. Grafo actualizado antes de cada congelación: protocolo semántico focal y AST real, sin tratar AST como semántica completa. Revisión nativa sólo lectura n06e_coverage_review ayudó a localizar la carrera; Codex reprodujo y verificó. PostgreSQL/Redis propios, namespaces aislados, contenedores/volúmenes/redes/temp retirados por inventario independiente y los tres avisos terminales Telegram sent. Prerregistro y referencia preservados; sin datos reales ni proveedores.

Lint inicial del instrumento falló por fixture/import y se corrigió antes de ejecutar; recibos conservados. El auditor posterior esperaba31casos por conteo manual erróneo: JUnit contiene32 (11retención, no10). Se corrigió el auditor y verificó32sin repetir pruebas funcionales; error y recibo retenidos. Esto no fue un fallo de aplicación. La repetición final sí fue necesaria por ampliar fuente/oráculo y conservar el fallo propio: no se buscó un tiempo favorable. El helper AST de ampliación falló con nodos de decoradores sin fuente; un verificador detectó la huella antigua de aplicación. Se corrigió la atribución, se rehízo el stage y se verificó el grafo antes de congelar la final; errores conservados, sin publicar grafo inválido.

N03/N07 siguen abiertos: reproducir por separado el posible no progreso de readyincomplete cuando sus fotos ya no son elegibles o carece de firma; una lectura de fuente no es un fallo runtime verificado. Conciliar reintentos/backoff y recuperación por broker/worker/Beat reales: envío capturado/direct process no los acredita. Reutilizar testigos sólo con identidad y ámbito comprobados; no cerrar por conteo. No abrir otra hipótesis marginal del detector. MOD09 restante diferido al final del desarrollo por usuario. Sin apertura de beta/producción.
