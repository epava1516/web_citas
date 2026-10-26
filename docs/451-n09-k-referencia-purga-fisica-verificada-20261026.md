# N09K — referencia local de purga física verificada

Estado: aceptada localmente la referencia finita del consumidor y la decisión sin cambio de aplicación para estos escenarios. N09 completo139IDs sigue abierto,8/13bloques obligatorios aceptados. Alpha/noindex; base8a71059 y [prerregistro450](450-n09-k-prerregistro-purga-fisica-entregas-20261026.md). Sin capacidad global ni entrega externa acreditadas.

Run:20261026-150235-79f3ca13,8PASS/0FAIL/ERROR/SKIP,121,924sJUnit/1780huellasestables. Runnerfocused serial/parsernativo/PostgreSQL17-alpine/Redis7.4-alpine propios. Auditoría independiente propiaPASS: ocho perfiles y diecinueve fases Task.run con archivos locales reales, una OSError controlada esperada. Dominio/medios/pines/fuentes/limpieza de contenedores/redes/volúmenes/temporal y recibosTelegram terminal y auditoríaPASS comprobados. No pruebas activas de este lote.

## Referencia temporal y antes/después

| Escenario/elegibles | Fase / filas retornadas | Wall tarea, ms | SQL, ms | Unlink, ms | Avance iterador, ms | Sentencias | Archivos retirados | Después |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| volume/0 | first_batch / 0 | 4.646 | 2.136 | 0.129 | 0.065 | 2 | 1 | Sin candidata |
| volume/0 | idempotent_replay / 0 | 6.003 | 2.838 | 0.000 | 0.070 | 2 | 0 | Sin candidata |
| volume/1 | first_batch / 1 | 5.878 | 2.802 | 0.211 | 0.079 | 3 | 2 | Sin candidata |
| volume/1 | idempotent_replay / 0 | 6.137 | 2.936 | 0.000 | 0.047 | 2 | 0 | Sin candidata |
| volume/10 | first_batch / 10 | 14.065 | 6.300 | 0.891 | 0.049 | 12 | 11 | Sin candidata |
| volume/10 | idempotent_replay / 0 | 5.359 | 2.764 | 0.000 | 0.046 | 2 | 0 | Sin candidata |
| volume/100 | first_batch / 100 | 156.949 | 82.543 | 8.541 | 0.069 | 102 | 101 | Sin candidata |
| volume/100 | idempotent_replay / 0 | 6.551 | 2.785 | 0.000 | 0.074 | 2 | 0 | Sin candidata |
| volume/1001 | first_batch / 1000 | 1717.130 | 877.189 | 82.539 | 0.082 | 1002 | 1001 | Sin candidata |
| volume/1001 | second_batch / 1 | 10.244 | 4.992 | 0.103 | 0.051 | 3 | 1 | Sin candidata |
| volume/1001 | idempotent_replay / 0 | 6.769 | 3.892 | 0.000 | 0.076 | 2 | 0 | Sin candidata |
| eligibility/4 | first_batch / 4 | 8.680 | 4.250 | 0.362 | 0.059 | 6 | 5 | Sin candidata |
| eligibility/4 | idempotent_replay / 0 | 4.682 | 2.531 | 0.000 | 0.040 | 2 | 0 | Sin candidata |
| skip_locked/3 | while_holder_active / 2 | 10.248 | 6.769 | 0.135 | 0.053 | 4 | 3 | Sin candidata |
| skip_locked/3 | after_release / 1 | 8.246 | 4.406 | 0.142 | 0.063 | 3 | 1 | Sin candidata |
| skip_locked/3 | idempotent_replay / 0 | 5.119 | 2.647 | 0.000 | 0.044 | 2 | 0 | Sin candidata |
| partial_failure/2 | second_unlink_failure / None | 5.003 | 2.361 | 0.122 | 0.000 | 2 | 1 | Sin candidata |
| partial_failure/2 | first_batch / 2 | 9.460 | 5.856 | 0.244 | 0.052 | 4 | 2 | Sin candidata |
| partial_failure/2 | idempotent_replay / 0 | 7.574 | 3.707 | 0.000 | 0.066 | 2 | 0 | Sin candidata |

Decisión: conservar la aplicación.100filas en156,949ms/102sentencias y primer lote1000del caso1001en1717,130ms/1002sentencias, seguido de1y0. No defecto funcional ni incumplimiento de presupuesto demostrado; no forzar candidata marginal. El1000limita selecciónSQL, no el conjunto de referencias retenidas ni recorrido global del directorio. Estos tamaños finitos no acreditan capacidad histórica. Sin versión posterior medida, mejora causal no evaluable; tiemposalfa aceptables según decisión vigente.

Medidas: wall rodea sólo task.run; SQLexecute_wrapper, unlink real reenviado y next del iterador medidos por separado. No sumar tiempos parciales para obtener wall; next no mide el cuerpo completo del scan ni todos los lstat. Una llamada unlink conmissing_ok no equivale a una baja física nueva. Preparación, snapshots y asserts quedan fuera del reloj de tarea;121,924sJUnit es tiempoQA. N1porfase, observadores con coste no cuantificado, caché calentada por creación/lectura/hash; sinp95/carga limpia/SLA/fsync ni pérdida de energía. Contexto previoHaswell8CPUx86_64/MemTotal23760928kB/FSregistrado en anexo; sin carga o cuotas observadas durante muestra.

Oráculos: seed nativo export/download/grant con fixture objectstorage deshabilitado; clones con FK/OneToOne válidos sólo aportan volumen sintético. Pines de seed/export/freshorphan extendidos siete días, sin reloj global ni autorizaciónTTL. Volúmenes0/1/10/100/1001: observar subconjunto real sin asumir ordenPK. Cada marca temporal dentro de llamada, sólo purged_at cambia; demás columnas/pines/todos modelos instalados/through/auth/sesiones/downloads/auditoría y medios fuera de root intactos por hashes. Dentro, conservar bytes/mtime/modo de referenciado/fresco/no32hex y retirar únicamente grantselegibles+huérfanoenvejecido. RowcountN+2/pines2 y directorioN+4→3 comprobados.

Matriz: cuatro criterios vencimiento de grant/generación obsoleta/exportpurged/exportexpired, padres separados para últimos dos; consume4yreplay0, sin tocar seed fresco ni padres. No representa cuatro nuevas autorizacionesHTTP ni productores admitidos.

Bloqueo: holder real mantiene un grant y su archivo envejecido; PID distinto termina2mientras sigue retenido, y retainedset protege ese archivo durante scan. Tras liberar1yreplay0. PIDs reales/conexiones/thread/holder cerrados con timeouts/cancelación/finally. No afirmar wait_eventLock, worker real ni pruebaBeat.

Fallo: OSError inyectada antes del segundo unlink de grant elegible. El primer archivo desaparece, el segundo permanece, todas las marcasSQL revierten y no empieza el scan final. Reintento normal consume2 y retira segundoarchivo+huérfano; unlinkmissing_ok tolera el primero ausente. Replay0. RetornoNone en tabla es excepción esperada, no resultado de tarea; rollbackSQL no restaura bytes. Es fallo controlado de operación, no caída abrupta/proveedor ni defecto de producto confirmado.

Reutilización: cuatro originalesPASS de run20261024-094540-3a6ec8ac,18fuentes pertinentes idénticas. Expiración/huérfanos; workerCelerysolo real despachado manualmente7,551sQA; purga de exportación elimina plaintext inmediatamente; huérfanos de objetos con RustFS local real5,461sQA/reloj sintético+2días/hooks eager/fallo-recuperación. Wholeoldrun conservaERROR; no actualadmisión de grants/transportes, Beat10s/hora, retención natural24h ni proveedor. No repetir ni contar esos testigos como ocho ejecuciones nuevas.

Revisión: propia Django/Celery/seguridad acotada al instrumento y consumidor; asserts sin revelar nombres/rutas/contenido, root propio y rechazo de symlinks en oráculos, separación SQL/FS, idempotencia y cleanupconcurrente revisados. InstrumentoSHA ddd95221a907a37d8217efae6b30056d24a52dec381e7a7ca0f3b73eefee22ce/RuffPASS. Skills laterales incorporadas según pertinencia;16disponibles/seisgruposMCPexpuestos no equivale a nuevas comprobaciones funcionales. Sin escánerglobal ni cambios de aplicación/esquema/settings/servicios/CI;15laterales preservados fuera de entrega propia.

Grafo: corte4492088fuentesSHA07f2a9f35774321031294f5dd50d1eb693073aec7f4ed1d44d224d7664a1d7ca; prerregistro4502090fuentes20387nodos84817relaciones989comunidadesSHA29531b47edfeb1088cec273425e3726d2b3433a2b992403b22366779731b0e44 antes de congelar. Cierre semántico451/17selectivo root sin repetirAST/runtime, no reconstrucciónN15 ni semántica exhaustiva;111 preservado.

Límites: nuevoTask.run/PG/FSpropios no es nuevo worker, Caddy, RustFS, broker, Beat ni proveedor. Archivo no recuperable por rollback documentado, no garantía atómica física. Retainedset/directorio sin límite global1000; N1pequeñas cardinalidades no p95/throughput. Jobs/reconciliación/otrasramas139IDs/N10N11N15pendientes; N02restante al final/N12–N14condicionados. N09 no se cierra por sumar perfiles o aliasBeat.
