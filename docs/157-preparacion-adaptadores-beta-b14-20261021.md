# B14 — Preparación de interfaces y límites de integración

Estado: interfaces preparadas y corrección de configuración verificada localmente; B14 abierto. [Roadmap103](103-roadmap-beta-clasificados-20261020.md), [contrato03](contratos/03-verificacion-representacion.md), [contrato10 histórico](contratos/10-denuncias-derechos.md) y [gates de apertura](actas/11-preparacion-produccion-pendiente-20261019.md).

Fuentes actuales: [edad/procedencia](../apps/core/verification_services.py), [contacto](../apps/core/verification.py), [outbox](../apps/safety/notice_delivery.py), [tarea](../apps/safety/tasks.py), [programación/configuración](../config/settings.py), [comunicación interna revisada](../apps/safety/communication_notices.py). El párrafo temprano de contrato10 que dice que no existe worker/Beat describe su fase parcial: la tarea y Beat60s están implementados para el simulador. Este estado posterior no acredita transporte externo.

Interfaces de proveedor especificadas; no hay integración externa nueva. La corrección de configuración se describe al final. No se añaden datos reales, compras, publicación o mensajes a sujetos. Inventario de fuentes conciliado después del resultado terminal auditado del contraste B08. No hay nueva prueba de proveedor.

Edad: inicio idempotente ligado a VerificationCheck, sujeto y manager_version. El adaptador futuro debe aportar referencia opaca autenticada y eventos únicos por proveedor, procedimiento real, resultado normalizado pending/passed/failed, plazo, validación de firma/frescura y vinculación exacta. No recibir documentos de identidad, biometría ni raw payload como nueva obligación de esta preparación. Conservar sólo evidencia minimizada autorizada. Revocación posterior es operación auditada propia: no sobrescribir un evento terminal ni reutilizar un callback obsoleto. Inicio y procesamiento reales aún no están implementados; cambiar VERIFICATION_PROVIDER no los crea.

Contacto: separar envío de OTP de comprobación del canal. Aceptación de un mensaje por un transporte no acredita control del teléfono. El contrato de confirmación conserva sujeto/gestor/rights_version, plazo, intentos, consumo único y reenvío invalidante. Elegir si OTP es propio o del proveedor sólo al diseñar la integración seleccionada. Los códigos de prueba enviados por correo conservan simulator-v1 y no pueden generar sms-v1.

Agencia: organization-v1 exige procedimiento/evidencia específicos; no se obtiene convirtiendo una revisión simulada en etiqueta real. Alcance real y revisión del operador se seleccionan aparte.

Comunicaciones: definir puerto de envío con identificador estable de outbox y generación, destino/plantilla mínimos, timeout acotado y clasificación de resultado (aceptado, rechazo definitivo, fallo transitorio o resultado desconocido). Una aceptación remota no es recepción por el usuario. Timeout tras aceptación remota necesita reconciliación o idempotencia del proveedor antes de reintentar; una transacción PostgreSQL no deshace un envío externo. No conectar por sustitución directa de simulated_adapter sin diseñar esa frontera. Mantener cifrado, separación de permisos y supresión de payloads/destinatarios/excepciones en logs. Intentos5/backoff60s del simulador son conducta actual, no política real aceptada por un proveedor inexistente.

Revocación y restauración: claves de callback/canal independientes cuando se implemente el puerto; eventos de gestor antiguo, sujetos retirados, destinos revocados y generaciones restauradas deben rechazarse o reconciliarse antes de salida. RECOVERY_MODE junto al aislamiento externo y la generación deben bloquear transporte real. No reabrir por un flag ni atribuir pruebas de simulador a proveedor.

Matriz futura de contrato: doble inicio exacto/conflictivo; callback firmado inválido/vencido/duplicado/cruzado/terminal; transferencia y revocación concurrentes; envío aceptado/rechazado/transitorio/desconocido; recuperación tras timeout sin duplicar; separación entre aceptación y entrega; no envío con entorno/recovery/generación incorrectos; privacidad de logs y destino actual. Primero tests locales de puertos con dobles explícitos; después prueba real sólo tras selección/autorización. Documentar ambos alcances separados.

Conciliación de documentación: el párrafo inicial de contratos10 dice que no hay worker/Beat. Actualmente existen tarea real, programación y recuperación de outbox simulada; conservar la fase histórica y señalar el estado posterior. No confundir ese cambio documental con un adaptador externo terminado. El defecto del backend console se reproduce y se aborda abajo; todavía no hay aceptación de una configuración real de apertura.

## Reproducción de configuración y corrección pendiente de verificar

[Negativo reproducido](evidencias/b14-production-console-negative-20261021.json): configuración production aislada sin EMAIL_BACKEND explícito permite arrancar console y escribir el mensaje sintético a su stream. Ningún envío/red/proveedor ni dato real. Es un defecto de configuración confirmado, no una filtración real observada.

Corrección preparada: production rechaza ausencia/defaultconsole, vacío, espacios y backends integrados console/filebased/locmem/dummy; desarrollo conserva su comportamiento. Mensaje fijo sin secretos. El ejemplo Compose exige EMAIL_BACKEND explícito y lo propaga a app/worker/Beat. Una clase SMTP configurada sólo se acepta para arrancar: no prueba conexión, recepción o idoneidad de proveedor/custom backend.

Verificación prevista35casos:10startup aislados,11perfilCompose sólo renderizado,6verificación local,6outbox y2localización de edad. PostgreSQL/broker propios para flujos de aplicación; ningún proveedor real. Mantener resultado y limpieza/Telegram; sólo después se acredita la corrección. No cambia el cifrado, firma HMAC ni migraciones. No se cierra B14 ni B13 por esta preparación.

## Resultado de la corrección

080733-c2d3627b:35PASS/0FAIL/0ERROR/0SKIP, sin advertencias,4workers. [Auditoría terminal](evidencias/b14-mail-guard-terminal-audit-20261021.json): diez arranques aislados, once perfiles Compose sin levantar servicios, seis casos de verificación, seis de outbox y dos localizaciones de edad. SMTP sólo configuración/import, no conexión ni envío real. Las guardias de producción fallan antes de crear transporte; el valor de desarrollo y los flujos sintéticos se conservan.

Fuentes congeladas/fresh, PostgreSQL/Redis/temporales/PIDs propios ausentes y recibo Telegram confirmados. Respecto de la imagen base HMAC66c6d381, las726fuentes runtime sólo difieren en el bloque de guardia de config/settings.py: al retirarlo se reconstruye exactamente el SHA anterior que reprodujo el defecto. Perfil/env ejemplo y pruebas cambian explícitamente por separado. HMAC, modelos, migraciones y resto de runtime intactos. No extender el PASS a un backend personalizado no revisado ni a capacidad de entrega de un proveedor.

Siguiente B13: construir esta candidata verificada y ensayar el ciclo de retorno real a la base66c6d381, con HMAC activo y backend de correo explícito permitido en ambas. La versión de retorno carece de la guardia nueva: mantener esa configuración revisada es condición del ensayo y del retorno. Este plan aún no acredita rollback ni apertura. B14 conserva pendiente la integración real tras selección/autorización, la evidencia de distintivos y la operación de comunicaciones, separadas de la corrección ya verificada.

Estado posterior: el ciclo de retorno previsto se verificó en [158](158-retorno-hmac-correo-beta-b13-20261021.md), con HMAC activo/correo explícito/escrituras/workers/recibos intactos. Sustituye el siguiente paso de ejecución indicado arriba; B14 sigue sin integración externa real ni aceptación de apertura.

## Continuación posterior — guardia de inicio de contacto

B14-351,2026-10-24: corregido inicio telefónico que aún creaba retos/correos simulados bajo proveedor no integrado en desarrollo. Seis negativos reales y doce controles posteriores; sólo cambia una condición, sin adaptador nuevo. La [guardia312](312-guardia-inicio-contacto-b14-20261024.md) conserva resultados, primera ejecución inválida y alcance de distintivos por predicados. B14 continúa abierto para selección/autorización, integración y prueba reales.

## Selección de proveedores — confirmación del usuario

Confirmación expresa del usuario2026-10-24: todavía no hay proveedores elegidos. No se interpreta como autorización de contratación, integración o envíos. B14 mantiene preparación local y queda pendiente de selección/autorización e integración/pruebas reales; el trabajo local de B16 puede continuar con simuladores explícitos.
