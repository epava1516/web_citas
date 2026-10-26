# N09I — referencia local de purgas lógicas verificada

Estado: aceptada localmente la referencia finita y la decisión sin cambio de producto para los escenarios observados; N09 completo139IDs sigue abierto,8/13bloques obligatorios aceptados. Alpha/noindex. Basecf97707 y [prerregistro446](446-n09-i-prerregistro-perfil-purgas-logicas-20261026.md). No se atribuyen garantías universales por esta muestra.

Run:20261026-134953-f5d248af,6PASS/0FAIL/ERROR/SKIP,90,445sJUnit,1778huellas estables. Perfilfocused serial, parser nativo, PostgreSQL17-alpine/Redis7.4-alpine propios. Auditoría independiente propiaPASS, dominio/archivos/huellas/limpieza de contenedores/redes/volúmenes/temporal y recibosTelegram terminalPASS/auditoríaPASS comprobados. No pruebas activas de este lote.

## Referencia temporal y antes/después

| Vencidas | Fase / consumidas | Wall tarea, ms | SQL observado, ms | Sentencias | Después |
| ---: | --- | ---: | ---: | ---: | --- |
| 0 | first_batch / 0 | 3.929 | 1.413 | 1 | Sin candidata |
| 1 | first_batch / 1 | 3.767 | 1.783 | 2 | Sin candidata |
| 10 | first_batch / 10 | 4.431 | 2.379 | 2 | Sin candidata |
| 100 | first_batch / 100 | 5.991 | 4.133 | 2 | Sin candidata |
| 101 | first_batch / 100 | 8.176 | 5.194 | 2 | Sin candidata |
| 3 | skip_locked_first_batch / 2 | 8.066 | 6.149 | 2 | Sin candidata |
| 3 | after_holder_release / 1 | 2.599 | 1.321 | 2 | Sin candidata |
| 3 | idempotent_replay / 0 | 2.813 | 1.227 | 1 | Sin candidata |

Decisión: sin defecto ni cambio de optimización justificado en estos escenarios finitos; conservar la aplicación. Columna después sin candidata: no hay un segundo producto medido ni porcentaje causal. La referencia de100filas es5,991ms; primer lote de101es8,176ms, luego1en5,016ms y replay0en2,436ms. No interpretar como percentiles, límite de latencia, coste de otras tablas o rendimiento sobre cardinalidad histórica no ensayada. No se aplaza un defecto conocido por llamar aceptable a una prueba.

Medidas: catorce llamadas task.run reales instrumentadas, una muestra por fase/estado; cinco volúmenes y un caso de concurrencia. Wall incluye ejecución/transacción; SQL suma tiempos vistos por execute_wrapper y no todo el trabajo Python. Psycopg no expuso BEGIN/COMMIT en los contadores observados, por eso SELECT/UPDATE no son contabilidad completa del protocolo. Sin SQL/params/payload en evidencias. Instrumentación añade coste no cuantificado; caché no vaciada y calentada por fixture, sin carga limpia/controlada. Hardware observado después: IntelHaswell8CPUlógicos,x86_64,MemTotal23760928kB; no muestra de carga durante medición ni SLA/quotas.90,445sJUnit es QA total, no tiempo de purgar100filas; cuerpo de casos/preparación/snapshots se conservan aparte.

Oráculos:0/1/10/100/101filas vencidas más un seed nativo vigente y un pin ya purgado. Las adicionales son clones de volumen de metadatos/Actions antes de medir, con FK/versiones válidas, no nuevas ejecuciones verificadas de usuarios. Primer lote<=100IDs porPK y progresión100/1/0para101; replay0para los demás. Sólo cambian encrypted_information y purged_at; marcas dentro del intervalo, inmutables/pins/resto del dominio/through/auth/Actions/archivos iguales por hashes. En skip_locked un holder mantiene1de3vencidas, PIDdistinto termina consumiendo2mientras sigue retenida; liberar permite1y luego0. No hubo esperaLock afirmada ni se sustituyó el task por un stub. Conexiones/thread/holder cerrados.

Reutilización:25casos originalesPASS en11archivos del run20261024-094540-3a6ec8ac, cuyas funciones y asserts de purga se leyeron y enlazaron a su consumidor. Su run completoERROR por otros fallos se mantiene como tal. Archivos de prueba, taskconsumer,modelos/coremodels/crypto/settings/pyproject/uv.lock y178migraciones idénticos. Se preservan sus oráculos de vaciado, metadata/retención de evidencia emitida/legacy,100/1/0del ledger; no se repiten25casos ni se cuentan como seis nuevos. Admisión actual de productores modificados y sus dependencias no se acepta con estas pruebas históricas. Preservar178migraciones es identidad, no migraciones aplicadas en destino existente.

Equivalencia: nueve wrappers atómicos comparten AST tras normalizar modelo/campo cifrado; eso explica selección, no convierte su coste en idéntico. AccessResponseDraft además ejecuta un consumidor de borradores finales no emitidos, por expediente/ledger, con originales4casos específicos vigentes/emitidos/legacy/batch. La medida nueva sólo pertenece a CopyInformation. AliasBeat no es otra acción ni acredita cadencia60s real; separar consumidor, declaración y scheduler.

Revisión: propia Django/Celery/seguridad acotada al instrumento, consumidor y secciones de oráculos reutilizadas. Sin modificación de app, modelos, settings, migraciones, servicios o CI. Root corrigió introspección de ciphertext en aserciones y añadió hashes de inmutables/pins y tiempos separados antes de congelar; instrumento SHA f8810895358d9e8d2a930a9a445c7ebd43d27bc161bce0f59dd019d80eb23023. Reporte delegado malformado se reparó antes de aceptar propuesta; primerRuffEXIT1por archivo no integrado se conserva como fallo de preparación, no producto; RuffrevisadoPASS. No revisión o escaneo integral supuesto.

Grafo: corte previo4452082fuentes SHAa62cbf33cf7493d78b9f12ac284e20fba59e2c49da607fba960ecf2bf11f5d85; antes de medir4462084fuentes20289nodos84514relaciones983comunidades SHAfcaeaf721713aac112bf5d246c96dca60093bd378b3c46272f2afcee1f8cc67c. Cierre semántico447/17selectivo root, sin repetirAST/runtime, no reconstrucciónN15 ni semántica exhaustiva.111 preservado.

Límites: native task.run no es broker/worker/Beat ni proveedor. Se registra referencia de cardinalidad pequeña, no coste global del histórico ni prueba de todos los estados/modelos; ningún umbral nuevo inventado. Outbox/objetos/jobs/reconciliación/otrasramas/139IDs y N10/N11/N15 siguen pendientes; N02restante al final/N12–N14condicionados.15laterales preservados fuera de la entrega propia. No cerrar N09 por sumar seis perfiles, veinticinco originales o alias.
