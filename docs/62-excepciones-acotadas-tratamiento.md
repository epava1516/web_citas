# Excepciones acotadas a restricciones de tratamiento

Fecha: 2026-10-05. Estado: preparación en implementación/verificación; revisión independiente, consumo y aceptación pendientes. CR-09 sigue abierto. Complementa docs58–61; no sustituye el levantamiento comunicado de docs60.

## Problema verificado

`purpose_restrictions.require_unrestricted` deniega la supresión de preferencias en `erasure_execution.execute` cuando existe cualquier medida activa de `account_preferences`. Las rutas ordinarias de favoritos también deniegan lectura, alta y eliminación. Ningún consumidor admite actualmente una excepción. La comprobación exige transacción y bloqueo del sujeto; estos controles se conservan.

Una supresión concreta solicitada posteriormente no debe conceder permiso general para consultar o modificar favoritos. Tampoco puede ignorar una segunda medida activa del mismo sujeto y finalidad. La conservación solicitada para una reclamación puede impedir la eliminación: autorizar requiere valoración humana del fundamento y alcance, no deducir consentimiento de la existencia de un formulario.

Fuente primaria consultada: [AEPD, limitación del tratamiento](https://www.aepd.es/preguntas-frecuentes/1-tus-derechos/2-tus-derechos-de-proteccion-de-datos/FAQ-0112-que-es-el-derecho-a-la-limitacion-del-tratamiento-de-datos), consultada 2026-10-05. La AEPD explica la suspensión cautelar y la conservación para reclamaciones. Las reglas técnicas siguientes son decisiones de ingeniería; no constituyen interpretación jurídica acreditada. La revisión jurídica de producción sigue pendiente. EUR-Lex devolvió verificación antirrobot en esta consulta; no registrar ese acceso como texto normativo verificado.

## Autoridad y alcance

Implementar propuesta, consulta auditada, aprobación independiente y consumo, con motivos y fundamento cifrados. La primera operación conectada será `erasure_execute` para `account_preferences`, dentro del procedimiento de supresión existente. No sustituye las demás finalidades pendientes del contrato.

La propuesta se vincula a sujeto, expediente de supresión, plan, versión del expediente, finalidad, conjunto completo de medidas activas y versiones de esas medidas. La firma incluye todos los propósitos de la ejecución solicitada y su fuente vigente. Una medida nueva, un seguimiento que cambia versión, un levantamiento, una modificación del plan o de la fuente invalidan la autorización pendiente. No basta con señalar una sola restricción.

Registrar fundamento concreto, referencia a entradas pertinentes del expediente y motivo minimizado. Diferenciar limitación y oposición; no reutilizar automáticamente la categoría de levantamiento ni convertir una petición posterior en autorización. El revisor debe leer el expediente vigente, las respuestas y los fundamentos de las medidas mediante consultas auditadas antes de aprobar. Una decisión de conservar pendiente o incompatible impide conceder permiso para borrar.

La aprobación requiere permiso específico, MFA/sesión actuales, ausencia de conflicto de interés y actor diferente del proponente. Revalidar asignación, ámbito y prueba proporcional vigente. Exponer aprobación o rechazo explícitos; el rechazo no permite consumo. Una aprobación no modifica `PurposeRestriction.active`, fechas ni versiones de las medidas.

Validez técnica máxima de 24 horas, configurable únicamente hacia un intervalo más corto en el primer flujo. Este límite no es un plazo legal. Un único consumo, sin token de excepción reutilizable por el navegador. No introducir un parámetro `force` o `ignore_restrictions` en servicios.

## Consumo transaccional

Añadir referencia opcional a la autorización en la operación de supresión. Incluirla en su firma idempotente. Sin restricciones, seguir el camino existente; con restricciones, exigir la aprobación exacta del conjunto vigente y la operación prevista.

Respetar el orden de bloqueos del expediente y sujeto que ya utiliza la supresión. Bloquear medidas y autorización en orden estable después del sujeto. Comprobar de nuevo permisos, prueba, versiones, fuente, expiración y estado después de cualquier espera. La comprobación del permiso puntual se realiza después de validar inventario, plan y decisiones actuales, antes de borrar.

Crear la acción de ejecución y registrar el consumo dentro de la misma transacción que la supresión. Un error posterior revierte tanto el consumo como la eliminación y la acción. Un reintento exacto devuelve el resultado original; otra clave no consume de nuevo. La autorización se liga a la acción ejecutada y no se borra al terminar.

Los favoritos ordinarios continúan bloqueados. El canal de derechos, autenticación y tratamientos de seguridad mantienen sus controles separados. Ninguna excepción concede acceso a modelos de agencia, datos de terceros ni otra finalidad. La supresión conserva su condición parcial y sus demás restricciones de alcance.

## Interfaz y evidencia de aceptación pendientes

Pantalla privada ES/EN desde el expediente: GET solo metadatos; POST para consulta auditada, propuesta y revisión. Motivos, referencias y fundamentos únicamente en la respuesta a una consulta autorizada, con `private, no-store`, CSRF y exclusión de indexación. No exponer contenido privado en enlaces, parámetros GET ni logs. Errores de versión o fuente devuelven conflicto sin efectos; falta de permiso se deniega.

Verificar con PostgreSQL y navegador móvil ES/EN: propuesta→consulta→aprobación independiente→supresión→reintento. Las restricciones deben permanecer activas y los favoritos ordinarios continuar denegados después de consumir.

Casos obligatorios: aprobación propia, otro sujeto/plan/expediente, segunda restricción no revisada, nueva medida, versión modificada, fuente alterada, prueba o permisos revocados durante espera, expiración, rechazo, cifrado corrupto, claves incompatibles y fallo posterior al consumo. Concurrencia real de dos conexiones: doble consumo, supresión frente a alta de medida y consumo frente a revocación/revisión. Observar bloqueos reales; no sustituir estas carreras por estados precargados.

La aceptación exige regresión conjunta de restricciones, levantamiento, calendario, supresión y favoritos; migración/runtime Docker app-worker-Beat comprobados y fuentes coincidentes. Identidad externa continúa simulada hasta contar con proveedor real; no declarar cumplimiento jurídico ni CR-09 completo por esta entrega.

## Preparación implementada, todavía sin permiso de tratamiento

Migración0072 añade propuesta, lectura y revisión como registros separados. La revisión tiene resultado aprobado/rechazado, propuesta única y consumo ligado a una acción única; una restricción de base de datos impide consumir un rechazo. Los servicios de revisión y consumo todavía no están implementados.

`purpose_exceptions.propose` exige permisos frescos/MFA/COI, expediente de supresión asignado vigente, inventario comprobado y plan firmado sin ejecutar. Bloquea el sujeto y todas sus medidas activas de preferencias; verifica ámbito y conflicto en los expedientes de origen. Registra la acción antes de descifrar los planes originales, conservando solo sus decisiones pertinentes en la propuesta cifrada. Incluye versión, fuente, plan y finalidades de ejecución; expiración técnica24h. Preparación/replay no alteran medidas, datos o expediente. La acción `exception_prepare` se excluye solo de la fuente del mismo procedimiento de supresión para evitar autoinvalidación.

Ruta privada `purpose_exception_prepare`: `/es|en/moderation/rights/<uuid:case_id>/exceptions/<uuid:plan_id>/prepare/`, GET/POST, formulario key/version/purposes/basis/reason; enlace desde supresión. GET muestra formulario sin fundamentos; POST correcto muestra identificador/expiración y declara que revisión/consumo siguen pendientes.403 permisos/CSRF,400 validación de formulario,409 conflicto del servicio; respuesta privada sin caché. No modifica la guarda `require_unrestricted` ni concede excepciones a favoritos.

Primera batería28307 terminó1:2 fallidas39,07s por consulta de ámbitos inexistentes directamente en ErasurePlan. Corregida a inventory__person/inventory__account_subject_id. Repetición42452 terminó0:2 correctas36,81s PostgreSQL. Prueba usa ejecución real local de restricción y un nuevo expediente real local de supresión con comprobación explícitamente simulada. Reproduce propuesta/replay, firma incompatible, permiso revocado y plan alterado, conservando favoritos y denegando supresión. No verifica aprobación independiente ni consumo.

Ampliación49932 terminal0:6 conjuntas correctas66,35s PostgreSQL, sin fallos/errores/skips; preparación/HTTP/CSRF/replay/GET sin fundamentos y restricción efectiva anterior verificadas sobre la misma fuente. Evidencia `evidencias/excepciones-preparacion-regresion.json`.0072 no aplicada al runtime normal; pendiente navegador móvil/carreras, integración de lectura/revisión/consumo e inventario de nuevas evidencias. No aceptar CR09 ni esta entrega completa por la preparación.
