# N09M — referencia local de alertas y retención verificada

Estado: referencia finita y decisión de conservar la aplicación aceptadas localmente para los escenarios observados. N09 sigue abierto, con sus 139 IDs pendientes de disposición final; hay 8/13 bloques obligatorios aceptados. Alpha/noindex. Base 57b3826 y [prerregistro454](454-n09-m-prerregistro-alertas-retencion-20261026.md).

Run: 20261026-161023-9fa5983d, 13 PASS, sin FAIL/ERROR/SKIP, 169,955 s JUnit y 1.782 huellas estables. Runner focused serial, parser nativo, PostgreSQL17-alpine y Redis7.4-alpine propios. Auditoría independiente propia PASS: 30 fases Task.run, 215 alertas insertadas, 867 seguimientos nuevos, 219 selecciones de plan, 216 actualizaciones de contador y dos observaciones de fallo esperadas. Filas previas, dominio, medios, fuentes, conexiones y limpieza de contenedores/redes/volúmenes/temporal verificados. Telegram terminal y auditoría PASS con recibo sent. No queda ninguna prueba activa de este lote.

## Referencia temporal y antes/después

Resultado urgente: alertas creadas. Resultado de retención: planes seleccionados / seguimientos programados / planes fallidos. Una programación de seguimiento no equivale a revisión humana.

| Familia/volumen | Fase | Resultado | Tarea, ms | SQL, ms | Sentencias | Después |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| urgent/0 | first_batch | 0 | 5.538 | 2.337 | 1 | Sin candidata |
| urgent/0 | idempotent_replay | 0 | 4.876 | 2.243 | 1 | Sin candidata |
| urgent/1 | first_batch | 1 | 15.965 | 8.128 | 5 | Sin candidata |
| urgent/1 | idempotent_replay | 0 | 3.196 | 1.377 | 1 | Sin candidata |
| urgent/10 | first_batch | 10 | 43.049 | 28.435 | 41 | Sin candidata |
| urgent/10 | idempotent_replay | 0 | 3.381 | 1.692 | 1 | Sin candidata |
| urgent/100 | first_batch | 100 | 345.904 | 225.940 | 401 | Sin candidata |
| urgent/100 | idempotent_replay | 0 | 5.095 | 2.855 | 1 | Sin candidata |
| urgent/101 | first_batch | 100 | 535.593 | 339.934 | 401 | Sin candidata |
| urgent/101 | second_batch | 1 | 10.507 | 6.281 | 5 | Sin candidata |
| urgent/101 | idempotent_replay | 0 | 5.348 | 2.577 | 1 | Sin candidata |
| retention/0 | first_batch | 0/0/0 | 8.337 | 2.739 | 1 | Sin candidata |
| retention/0 | idempotent_replay | 0/0/0 | 10.740 | 4.719 | 1 | Sin candidata |
| retention/1 | first_batch | 1/4/0 | 23.369 | 13.343 | 20 | Sin candidata |
| retention/1 | idempotent_replay | 0/0/0 | 6.273 | 2.835 | 1 | Sin candidata |
| retention/10 | first_batch | 10/40/0 | 248.808 | 162.038 | 191 | Sin candidata |
| retention/10 | idempotent_replay | 0/0/0 | 9.258 | 3.512 | 1 | Sin candidata |
| retention/100 | first_batch | 100/400/0 | 2073.906 | 1299.510 | 1901 | Sin candidata |
| retention/100 | idempotent_replay | 0/0/0 | 7.995 | 3.118 | 1 | Sin candidata |
| retention/101 | first_batch | 100/400/0 | 2212.659 | 1394.008 | 1901 | Sin candidata |
| retention/101 | second_batch | 1/4/0 | 21.505 | 11.984 | 20 | Sin candidata |
| retention/101 | idempotent_replay | 0/0/0 | 12.776 | 5.050 | 1 | Sin candidata |
| urgent/3 | while_holder_active | 2 | 26.078 | 16.466 | 9 | Sin candidata |
| urgent/3 | after_release | 1 | 14.320 | 7.690 | 5 | Sin candidata |
| urgent/3 | idempotent_replay | 0 | 3.624 | 1.917 | 1 | Sin candidata |
| retention/3 | while_holder_active | 2/8/0 | 61.073 | 35.935 | 39 | Sin candidata |
| retention/3 | after_release | 1/4/0 | 21.634 | 12.166 | 20 | Sin candidata |
| retention/3 | idempotent_replay | 0/0/0 | 10.798 | 4.250 | 1 | Sin candidata |
| retention/3 | first_batch | 3/7/1 | 45.996 | 24.490 | 38 | Sin candidata |
| retention/3 | invalid_retry | 1/0/1 | 7.574 | 3.524 | 4 | Sin candidata |

Decisión: conservar la aplicación. El perfil de 100 alertas tarda 345,904 ms con 401 sentencias; el primer lote de 100 del caso101, 535,593 ms con 401. El perfil de 100 planes programa 400 seguimientos en 2073,906 ms con 1901 sentencias; el primer lote de 100 del caso101, 2212,659 ms con 1901. Son estados distintos y N=1 por fase, sin comparación de versiones ni mejora causal. No se ha demostrado un defecto o incumplimiento que justifique una candidata marginal. No trasladar un presupuesto HTTP al trabajo de calendario.

Medidas: el reloj de tarea rodea sólo Task.run; SQLexecute reenvía consultas reales y registra cantidades/duración, sin texto ni parámetros. SQL está incluido en el tiempo de tarea: no sumar ambos ni atribuir automáticamente el resto a CPU o descifrado. Preparación, snapshots, hashes, asserts y limpieza quedan fuera. Los 169,955 s JUnit son QA. Instrumentación con coste no cuantificado, caché calentada por fixtures y validación; sin p95, después, carga limpia o SLA. Contexto Haswell, ocho CPU lógicas x86_64, MemTotal23760928kB y FS registrado durante el run, sin observación de cuotas o carga por fase.

Alertas: seed por intake nativo y clones de metadatos con claves propias, no nuevas admisiones HTTP. Se conserva la alerta del seed y un Report de prioridad1 sin alerta. Sólo se insertan alertas de los Report seleccionados, con fecha dentro de cada llamada y acknowledgement nulo. Report completos, estados, versiones, asignación, alertas anteriores y demás modelos/medios intactos. Volúmenes0/1/10/100/101, avance100/1/0 para101 y N/0 en el resto; 215 alertas nuevas incluyendo el skip3. No hay lectura privada, asignación, resolución o entrega externa acreditada.

Retención: seed de plan nativo y clones autenticados con inventario, versión, decisiones, source y digest compatibles; K=4 finalidades retain/review en todos los perfiles de esta muestra. Cada clon supera plan_decisions actual antes de medir. Son metadatos de volumen sintético, no planes humanos nuevos. Sólo se cambia retention_purpose_count donde corresponde y se crean seguimientos con propósito/operación/fechas/responsable original, versión1 y last_reviewed nulo. No se alteran decisiones, inventarios, acciones, fechas existentes, eventos, exportaciones, cuentas, perfiles o medios; no hay borrado. 867 seguimientos nuevos y 216 contadores actualizados, con comparación exacta de columnas y huellas independientes de las etiquetas esperadas.

Mezcla: un plan válido vacío, otro parcial con una fila previa sintética de seguimiento en versión7 y otro con cuerpo inválido. Primera fase: plans3/scheduled7/failed1; segunda: plans1/scheduled0/failed1. El seguimiento previo conserva todos sus campos. El inválido queda intacto y seleccionable, de modo que vuelve a contarse como fallo; los dos failed son observaciones del mismo plan en dos pasadas, no dos defectos ni dos planes distintos. No se crea un estado persistente nuevo de retry ni se acredita una revisión humana mediante el pin sintético.

Bloqueos: en ambos consumidores un PID PostgreSQL distinto termina dos elementos mientras el holder mantiene bloqueada la tercera fila. Tras liberar, consume una y después cero. PIDs distintos, finalización durante el holder, conexiones de hilo cerradas, thread y holder terminados verificados. statement_timeout10s, future15s y cancelación/finally son límites de seguridad de QA. No es una observación wait_eventLock ni prueba de ausencia universal de esperas.

Reutilización: cinco testigos históricos PASS seleccionados de20261024-094540-3a6ec8ac, con 23 fuentes directas pertinentes idénticas: dos de backfill/lotes/rollback de alertas y tres de idempotencia, rechazo de plan manipulado y reparación parcial sin sobrescribir seguimiento. Se conserva sólo el tramo del consumidor y sus invariantes con fixture antigua; no admisión HTTP, HMAC, autoridad o revisión humana actuales. rights/fingerprint, erasure_inventory y rights_verification difieren. El presente perfil usa autenticación y fixtures nativas actuales. Las otras17pruebas quedan como historia, no22PASS actuales ni cierre transitivo global. El run antiguo completo conserva ERROR; no se repiten browser, negativos o seguimientos humanos por frescura documental.

Revisión: propia Django/Celery/seguridad, acotada al instrumento y consumidores. Root leyó348líneas de propuesta, reforzó privacidad de asserts y añadió huellas inmutables de planes/targets y conteos reales de padres/cambios. Ruff inicial I001 por un import con alias combinado, corregido sin cambio semántico; instrumento final SHA5d181385da0c5fc6660afd0e5554bb61eea5318da6d9b0647725cf79dc381188 y Ruff PASS. Reporte canónico de diez campos; complete delegado no fue aceptación runtime. Sin cambios de aplicación, esquema, configuración de producto, servicios o CI; 15 archivos laterales preservados fuera de la entrega propia.

Grafo: corte453 de2094fuentes, SHAffe88144a314873d3308c663a2e531568e0c8f09e212b6a6f2da866b3b6c5146. Antes de congelar: AST del instrumento y semántica selectiva root454/17, 2096fuentes/20487nodos/85102relaciones/996comunidades, SHA4d1d08b87da319ed0786f375a2409de00bfeb3b22e1749aec98aab2d0a97dbf3. Cierre semántico selectivo455/17 sin nuevo AST o runtime; no reconstrucción N15 ni semántica exhaustiva. Inventario111 preservado.

Límites: Task.run y PostgreSQL propios no prueban worker, Beat, proveedor, entrega de aviso, revisión humana, borrado ni garantía de retención legal. Los lotes finitos no acreditan capacidad de un histórico masivo. N09 conserva objetos, purga de exportaciones, puentes de productores y las 139 disposiciones finales pendientes; también N10/N11/N15. N02 restante al final y N12–N14 condicionados. No cerrar N09 por sumar perfiles, alertas, seguimientos o alias Beat.
