# B12 — Eventos operativos acotados

Estado: segunda unidad verificada funcionalmente en selección40PASS; coste y operación completa pendientes. Continúa [unidad1](130-observabilidad-operativa-beta-b12-20261020.md). No cierra B12, B07 ni el contrato beta. Grafo67 previo a este incremento: SHA dcf0cc98c184a7c21a54c981d21d3a5821a29cf8f1f404547c5a8c43985cf472; actualización dirigida, no semántica global.

## Decisión y alcance

Los contadores durables de unidad1 no miden frecuenciafallback ni errores del cuerpo de tareas. La observación request-local ya existe y los hooks nativos Celery permiten añadir eventos sin leer datos de sujetos ni escribir base de datos por petición. Un task de entrega puede devolver retry/failed en su resultado aunque Celery considere ejecutado correctamente su cuerpo. Registrar ambas cosas separadamente.

`apps/core/operational_events.py` añade eventos JSON de esquema1 con timestamp numérico, nombres de evento fijos y vocabulario acotado. No recibe requests completos, IDs de tarea, argumentos, contactos, consultas ni excepciones. Los nombres de tareas reconocidas son constantes explícitas extraídas del código; cualquier nombre no registrado se convierte en other. No se importa el módulo de derechos para registrar eventos.

El middleware consume sólo `_publication_route` y status_code, sin consultas ni cambio de respuesta. Registra state/fallback, motivo conocido y claseHTTP. Sólo observa respuestas que regresan del handler con ese atributo. No mide errores posteriores de un cuerpo streaming ni todo el tráfico ni duración total. Una línea por lectura observada permite contar frecuencias únicamente en la ventana realmente recogida; no es contador global persistente por proceso.

RecoveryAwareTask conserva el rechazo de mensajes en recuperación y añade eventos ignored/succeeded/failed/retry desde hooks nativos. No registra error, traceback, task_id, argumentos ni resultado libre. Para deliver_safety_notices exclusivamente, extrae processed/simulated/retry/failed enteros0–100 y disabled booleano; valores no válidos se representan como desconocidos. El éxito de un cuerpo no acredita entrega externa. El simulador conserva su nombre.

El logger operational.events tiene handlerstderr y formato sólo mensaje, sin propagación a handlers de aplicación. Es un canal de eventos específico; no declara saneados todos los logs históricos de Celery o de terceros. Las pruebas usan exclusivamente argumentos y excepciones sintéticos. El envío es best-effort: un fallo del logger no puede alterar publicación o ejecución de negocio. Ausencia de eventos no acredita salud, ni entrega durable ni contabilidad completa.

## Destino, recursos y límites

Compose configura driver json-file y rotación1m×3 en app/worker/Beat. Es configuración de rotación, no prueba kernel de techo de almacenamiento ni confirmación de que servicios normales hayan sido recreados. No se arranca ni modifica servicio normal. Las ejecuciones nativas necesitan su propia captura/retención; esta unidad no instala archivos de logs, cron o proveedores externos.

Aún falta verificar destino efectivo y límites en runtime propio, medir coste y cadencia, definir alertas y recogida de ventanas completas, supervisar fallos del canal y pérdida por rotación. No convertir logs incompletos en tasas de toda la aplicación. No relajar recursos ni SLO del contrato. No lanzar cortoTCP por la mera existencia de instrumentación.

## Pruebas y alcance

Cinco casos nuevos: allowlist y respuesta intacta/exclusión de requests sin observación; éxito del cuerpo separado de retry de entrega; fallo de logger sin alterar ejecución; worker Celery real en cola propia con PostgreSQL y secuencia retry→failed→succeeded; recorridoHTTP real state/fallback que conserva IDs y recuento. El ensayo de worker usa tareas sintéticas heredadas y nombres other para verificar hooks y no identifica entrega externa ni reparación de un expediente. Worker y cola deben retirarse en finally.

Ejecutar también las seis pruebas de unidad1 y los controles pertinentes del gate de recuperación para comprobar que nuevos hooks no permitan ejecución de negocio en RECOVERY_MODE. Conservar freeze, limpieza y avisos terminales. Faltan pruebas reales de entrega fallida/retraso y recuperación operativa de B12, además de runbook/umbrales. La observabilidad no sustituye revocación ni elegibilidad.

La revisión de lectura no encontró defecto concreto; mantiene como incertidumbre el coste y posible bloqueo del logger síncrono. Capturar excepciones no limita la latencia del sink. El worker previsto usa poolsolo, sin acreditar pérdidas de procesos prefork. ValidaciónCompose inicial sin.env terminóEXIT1 y se conserva; validaciónestructural posterior omite resolverenvfiles, sin crear configuración privada ni arrancarservicios.

## Negativo previo a ejecución funcional

230056-65c259ae terminóERROR en RuffF811: parámetro directory del casoHTTP añadido ocultaba fixture importada. [Auditoría](evidencias/b12-events-first-preflight-negative-20261020.json):0casos funcionales ejecutados, freeze intacto, runner terminal, limpieza reportada y TelegramERRORsent. No es fallo de producto ni prueba funcional negativa. Se cambia sólo el casoHTTP a request.getfixturevalue y variable localclient; nueva selección preparada entonces, con resultado posterior al final.

## Resultado terminal y alcance

230352-2b173502:40PASS/0FAIL/0ERROR/0SKIP,73,778sJUnit. [Auditoría terminal](evidencias/b12-events-terminal-audit-20261020.json): cinco casos de eventos, seis del snapshot, dos de recuperación worker/Beat y27de privacidadlogging. Fuentes comparadas de nuevo, PostgreSQL/Redis y temporal eliminados, PIDs runner/pytest terminales, TelegramPASS confirmado. El negativo230056Ruff se conserva; no se convierte en prueba funcional ejecutada.

El worker real propio observó retry→failed→succeeded con tareas sintéticas y PostgreSQL/Redis; el recorridoHTTP comprobó state/fallback e igualdad de IDs/recuento. Los contadores específicos de entrega se comprueban en el hook con resultado sintético, no mediante un proveedor externo ni como ensayo de recuperación del outbox. Las fuentes previas cambian sólo en Compose/configCelery/configsettings y se añade el módulo de eventos; se mantienen tareas, modelos y reglas de elegibilidad.

Verificada la funcionalidad indicada; no adopción de presupuesto de rendimiento ni cierreB12. Permanecen pendientes el coste/bloqueo del sink, verificaciónruntime de rotación, observación de transporte y pérdidas, ventanas/umbrales/runbook y recuperación operativa del outbox/atraso con datos sintéticos. B07continúaFAIL y no se ejecutó nuevoTCP.
