# B12 — Evaluación administrativa y runbook local

Estado: evaluación corregida verificada con9casos ejecutados+17reutilizados; cierre completo B12 pendiente.

Grafo previo83:bd27636b36af1546516688363cec477b875da0df7eb7c64293c71f7193d96164. Continúa [coste y rotación136](136-coste-snapshot-rotacion-beta-b12-20261021.md), [ventanas135](135-informes-ventanas-eventos-beta-b12-20261020.md) y [operación12](12-operacion-seguridad.md). Sin cambios en autoridad, tareas de dominio, esquema o proveedores.

## Evaluación

operational_assessment combina snapshot PostgreSQL fresco con una ventana JSONL opcional, usando el mismo cargador regular acotado de operational_events_report. Sólo emite códigos, severidades, ámbitos fijos y agregados; nunca nombres de archivos, contactos o datos de sujetos. Errores de entrada/DB producen mensaje fijo y ninguna salida JSON parcial. Sin archivo se señala event_window_missing; no se rellena una ventana con ceros para inferir salud.

status puede ser action_required, attention_required o unknown. health=unknown y coverage=unverified permanecen incluso tras recuperar una cola. Código de salida0 significa informe construido, no salud ni ausencia de incidencias. No endpoint, scheduler, envío de alertas o reparación automática. Lectura manual por el ejecutor local; operador/guardia reales continúan pendientes de G03/G06/G07 y B17.

Uso: python manage.py operational_assessment --input ARCHIVO_JSONL --start INICIO_EPOCH --end FIN_EPOCH, sustituyendo límites por la ventana UTC real. Sin esos tres parámetros se obtiene evaluación durable con ausencia de eventos explícita. No repetir muestras solapadas ni ejecutar dos recolectores locales a la vez.

## Umbrales de atención local v1

Son presupuestos de observación, no sustituyen SLO públicos ni plazos jurídicos o de entrega. Se derivan de cadencias numéricas actuales de Beat; configuración ausente, duplicada, no numérica o con argumentos no contemplados produce schedule_policy_unknown. No adivinar otra cadencia en recuperación.

| Señal | Criterio | Fundamento y respuesta |
| --- | --- | --- |
| Muestreo administrativo | Cadencia recomendada60s, terminar una llamada antes de otra | Baseline136 p95 local121,083ms con10k+10k; no es un compromiso de CPU servidor |
| Coste snapshot | Atención desde1s de duración | Presupuesto prerregistrado1/60del intervalo (1,67%de ocupación temporal del muestreador), con margen sobre baseline; no límite de CPU ni SLOHTTP |
| Publicación pendiente | Edad≥2×cadenciarefresh+presupuesto nominal del bucle | Hoy2×30+50=110s; atención ante dos oportunidades más bucle configurado, no garantía de duración dura |
| Aviso exigible | Espera desde elegibilidad≥2×cadenciadelivery | Hoy120s; un aviso programado aún no exigible no dispara atraso |
| Avisos failed/exhausted y trabajos failed/missinglease | Al menos1 | Error explícito; inspección, sin reenvío ni reautorización ciegos |
| Lease vencida | Al menos1 | Atención, verificar autoridad y reconciliación antes de actuar |
| Temporal vencido sin purga | Edad desde vencimiento≥2×cadenciatarea | Hoy120s en los modelos observados; contenido físico se comprueba aparte |
| Borrador final no emitido | Edad desde creación≥24h+2×cadenciaaccessdraftpurge | Hoy86520s; la tarea responsable es purge_expired_access_response_drafts |
| Evento taskfailed/HTTP5xx/deliveryfailed | Al menos1observado | Error observado, sin presentar tasas globales ni asumir que todos los fallos son iguales |
| Reintento delivery/task, marcador transportgap, entrada desconocida | Al menos1observado | Atención al backend o al canal; no sumar contadores acumulados de procesos no identificados |
| Fallback | Informativo; atención si reason indica límite de estado | Sin umbral porcentual inventado; invalid_search no equivale a saturación |
| Ventana no actual | Fin más antiguo que60s o futuro más de1s | Recoger ventana nueva, manteniendo cobertura no verificada |

El snapshot conserva oldest_age_seconds desde creación y añade oldest_due_wait_seconds al grupo due mediante Min(Coalesce(next_attempt_at,created_at)), en la misma consulta. Esta distinción impide atribuir a un worker la antigüedad previa de un reintento recién exigible. Se repetirá el diagnóstico de coste porque cambió el agregado; la medida136 permanece histórica.

## Respuesta local y límites

1. Capturar ventana y snapshot mediante el comando; registrar sólo códigos y agregados. Confirmar origen/intervalo del archivo y estado del lector por separado. Si faltan señales o el comando falla, no emitir allclear.
2. inspect_receiver_schema, inspect_receiver_and_collect_new_window y collect_new_window: revisar formato y lector, marcar intervalos incompletos, recoger ventana nueva. inspect_sink_and_mark_window_incomplete: comprobar destino y rotación; no borrar la evidencia de pérdida ni sumar acumulados. Circuito Docker propio verificado en136, sin afirmar despliegue.
3. inspect_worker_then_reconcile_publication: comprobar worker/Beat y marcas, ejecutar sólo la tarea normal con sus guardas en el entorno autorizado; comparar cola antes/después. No eliminar marcas manualmente para ocultar atraso ni alterar elegibilidad pública.
4. inspect_outbox_worker_and_backend e inspect_outbox_without_forcing_delivery: diferenciar cuerpo succeeded de entrega retry/failed, distinguir programado de exigible y conservar backoff/idempotencia. keep_simulator_disabled_in_production exige mantener el bloqueo; proveedor real requiere B14 y autorización independiente.
5. inspect_task_without_blind_replay, inspect_export_authority_and_lease e inspect_application_errors: inspeccionar causa y autoridad; no reponer ni reenviar automáticamente por el evento de error. Reintento autorizado sólo a través de los servicios existentes.
6. inspect_purge_and_physical_storage_separately: reconciliar vencimiento lógico y tarea responsable; comprobar objetos físicos aparte. El snapshot no acredita borrado físico.
7. inspect_schedule, inspect_observation e inspect_sampler_before_increasing_frequency: verificar configuración y coste antes de ampliar frecuencia. No crear solapamiento para disimular un muestreador lento.
8. Tras corregir, guardar evidencia mínima del incidente y obtener ventana posterior al punto de recuperación, además de reconciliar trabajo durable. No declarar sano el servicio completo porque desaparezca una alerta concreta.

## Prerregistro de verificación

Selección26casos:8assessment+7snapshot+9ventanas+1coste+1worker. PostgreSQL/Redis aislados, workers1, fuentes congeladas y notificación terminal. Nueve casos nuevos respecto al corte anterior; el caso worker existente añade evaluaciones y segunda recuperación.

Ensayo del outbox: tarea real en prefork2 con adaptador simulador que falla una vez; detectar delivery_retry_observed sin task_failed_observed ni atraso falso por creación. Esperar backoff natural60s, recuperar recibo simulado único y evaluar nueva ventana posterior a recuperación, conservando healthunknown.

Ensayo publicación: marcar listings de la fixture y asignar edad de300s como inyección controlada; no son cinco minutos reales de espera. Detectar publication_backlog_old, ejecutar refresh_publication_state real en el mismo worker y verificar cola0 y desaparición de esa señal. No borrar marcas para fabricar recuperación. Conservar assessment-outbox-runbook.json agregado, sin IDs ni logs de sujetos.

Repetir treinta medidas snapshot vacío/10k+10k y comparar el presupuesto local1s, sin confundir PASS de integridad con aceptación de rendimiento. Auditar XML, hashes actuales, limpieza y recibos antes de registrar resultado. Este protocolo no cierra por sí solo B12, B13 ni el objetivo beta; capacidades y operación real pendientes conservan su alcance.

## Resultado del primer corte y corrección de cobertura

003401-3523ed4d:26PASS/0FAIL/0ERROR/0SKIP,142,568sJUnit. [Auditoría común](evidencias/b12-assessment-common-terminal-audit-20261021.json), [runbook agregado](evidencias/b12-assessment-runbook-20261021.json) y [coste actualizado](evidencias/b12-assessment-snapshot-cost-20261021.json): fuentes contrastadas de nuevo, procesos del runner/pytest y tres identidades prefork terminales, contenedores/temporal ausentes, TelegramPASS confirmado.

Con el agregado de espera exigible, p95local80,062ms vacío y130,463ms con10kmarcas+10kavisos;31SELECT por observación y presupuesto prerregistrado1s cumplido. El muestreo local recomendado60s queda sustentado para ese corte y cardinalidades, sin garantía global de CPU ni tiempos públicos.

El ensayo real detectó delivery_retry_observed, recuperó un único recibo simulado tras60s naturales y dejó de señalar ese incidente en la ventana posterior. Detectó publication_backlog_old con edad controlada de300s y la tarea real del worker vació la cola sin borrado manual. En ambas fases finales statusunknown/healthunknown/coberturaunverified: no allclear.

Revisión posterior: una discrepancia entre configuración de recolector y worker podía omitir processor_disabled=True observado, aun existiendo trabajo exigible. [Reproducción](evidencias/b12-disabled-worker-reproduction-20261021.json) ejecutó la función de política con agregados sintéticos y SQL prohibido; devolvió unknown sin señales. No prueba de worker ni entrega. Primer arranque del helper falló por ruta de importación, conservado y notificado; segundo con raíz resuelta reprodujo la omisión sobre la huella exacta del corte26.

Se añaden notice_processor_disabled_observed (error con trabajo pendiente, informativo sin él) y notice_processor_state_unknown_observed. No se modifica el recolector ni el benchmark. Reejecutar8assessment+1worker=9casos; reutilizar estrictamente7snapshot+9ventanas+1coste=17 sólo si fuentes y dependencias de esos testigos permanecen idénticas. No presentar9nuevos+17reutilizados como una ejecución única26PASS sobre la corrección.

Pendiente: auditar el cierre completo de B12, incluido el inventario de almacenamiento que no se mide universalmente; las colas y señales de medios se amplían en [138](138-medios-purga-observabilidad-beta-b12-20261021.md). No aceptar B12 sólo por los casos de este documento ni trasladar a local la asignación real de guardia pendiente en B17.

## Corrección verificada

004837-1f715389:9PASS/0FAIL/0ERROR/0SKIP,123,041sJUnit. [Auditoría de corrección y reutilización](evidencias/b12-assessment-correction-terminal-audit-20261021.json):8assessment+1worker ejecutados,17testigos del corte003401 reutilizados con fuentes y dependencias idénticas,26nodeids únicos conciliados. No es una ejecución única26PASS sobre la versión corregida.

El único módulo de producto cambiado entre ambos cortes es operational_assessment.py; el otro cambio de runtime es su archivo de pruebas. El snapshot, los cargadores de ventana, el benchmark y todos los demás módulos de producto/scripts/fixtures se contrastaron por huella. No se repitió el coste: p95local130,463ms con10k+10k y31SELECT sigue siendo evidencia de la misma fuente de recolector, con presupuesto1s satisfecho en el corte medido.

La discrepancia de backend deshabilitado ahora produce señal explícita y action_required cuando hay trabajo pendiente; estado desconocido del procesador observado produce atención. El worker real volvió a recorrer fallo/reintento/recuperación y atraso/reconciliación de publicación. [Runbook corregido](evidencias/b12-assessment-corrected-runbook-20261021.json): un recibo simulado, cola de publicación0 tras tarea normal y salud/cobertura desconocidas conservadas.

Fuente fresca, contenedores y temporal ausentes, runner/pytest y tres identidades prefork terminales y TelegramPASS confirmados. No proveedor real ni envío automático de alertas. Evaluación y dos recorridos del runbook aceptados en este alcance local; B12 sigue abierto para su auditoría integral, con las señales de medios verificadas en [138](138-medios-purga-observabilidad-beta-b12-20261021.md) y el inventario físico universal aún no medido. B07 y el resto del objetivo beta no cambian de estado.
