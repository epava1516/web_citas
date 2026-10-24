# B14-351 — Guardia de inicio de contacto

B14 sigue abierto y13/18puntos cerrados. Se observa una discrepancia: phone_confirm rechaza producción o VERIFICATION_PROVIDER distinto de simulator; phone_start sólo rechaza producción. En desarrollo con proveedor no integrado puede crear un reto/inutilizar el anterior y enviar correo de simulación antes de que la confirmación falle.

Reproducción prevista: seis casos GET/POST por future-provider, cadena vacía y simulator con espacio. Se crea primero un reto válido mediante simulador explícito, se cambia la configuración y se exige503 sin nuevo reto, invalidación del anterior, correo adicional o PhoneClaim. PostgreSQL y correo locmem explícito; ningún proveedor o mensaje a un sujeto real. Un worker, timeout1200s; no aceptación de SMS real.

La [preparación157](157-preparacion-adaptadores-beta-b14-20261021.md) ya especifica puertos futuros y minimización. Este cambio no selecciona proveedor ni implementa un adaptador: busca que inicio y confirmación rechacen la misma configuración no integrada antes de efectos de simulación. Mantener fallos de reproducción y comprobar resultado/limpieza/Telegram antes de corregir. La evidencia de distintivos y operación real continúa pendiente.

## Corrección del instrumento de reproducción

Primera ejecución085456-ae24d24e:6fallos antes de llegar a la guardia, por esquema no preparado al solicitar dinámicamente transactional_db sin marca django_db. Fuentes intactas, limpieza y Telegram confirmados; no acredita el defecto de aplicación. Se añade la marca explícita de PostgreSQL transaccional conservando las seis aserciones y sin tocar la aplicación.

## Reproducción válida y corrección preparada

Reproducción válida085745-6f0ef8c9:6FAIL/0ERROR/0SKIP,49.403sJUnit,1722fuentes intactas, limpieza y Telegram confirmados. GET devuelve200; POST302 crea otro reto, consume el anterior y añade correo. El primer lector JUnit asumió un atributo type inexistente: se corrigió para comprobar el mensaje de aserción503 conservando XML y fallos originales. Aplicada sólo la misma condición que phone_confirm: PRODUCTION o proveedor distinto de simulator rechaza503 antes de efectos. Verificación posterior prevista12casos: seis nuevos y seis existentes de verificación.

## Resultado verificado

Corrección090124-aaa54693:12PASS/0FAIL/0ERROR/0SKIP,58.779sJUnit,1722fuentes congeladas verificadas. Las seis aserciones nuevas pasan junto a los seis controles existentes. Sólo cambia la condición de proveedor de phone_start; archivo reconstruido exactamente desde el snapshot previo mediante esa sustitución. PostgreSQL/temporales/PID propios limpios y Telegram confirmado.

[Negativo válido](evidencias/b14-phone-gate-negative-audit-20261024.json), [corrección](evidencias/b14-phone-gate-corrected-audit-20261024.json) y [primera ejecución que no alcanzó la guardia](evidencias/b14-phone-gate-first-instrument-failure-20261024.json). No convertir el fallo de preparación ni los seis negativos reales en PASS retrospectivos. La comprobación JUnit corregida sólo interpreta el formato real: los XML no se modifican.

La regresión mantiene simulación local de contacto y edad, reenvío invalidante, consumo único, actores no autorizados, transferencia, revocación, carrera entre gestores y rechazo de retos tras cambio de proveedor. Las seis aserciones nuevas comprueban el reto previo y el número de correos, no sólo el estado HTTP. Reversión acotada: retirar la segunda condición de phone_start; no restaurar el módulo entero sobre otros cambios. No se añade proveedor, dependencia, migración o nuevo procedimiento acreditado.

## Distintivos: predicados y límites de evidencia

Lectura de verification_services.real_checks y listings.presentation; esta tabla es un inventario de código, no una prueba externa de cada distintivo.

| Distintivo | Predicado de código | Límite |
|---|---|---|
| Edad comprobada | Última comprobación del proveedor configurado distinto de simulator; procedimiento age-v1, passed, sujeto y manager_version actuales | No hay adaptador real conectado; una fila sintética con esos campos no acredita mayoría de edad real, identidad o seguridad de una cita |
| Control del contacto confirmado | PhoneClaim verificado, sms-v1 y gestor individual/agencia coincidente | Control del canal, sin garantía de identidad, fiabilidad o entrega de otros mensajes; OTP por correo del simulador permanece simulator-v1 |
| Comprobación de agencia | Agencia actual passed con organization-v1 | Requiere procedimiento y evidencia reales autorizados; no acredita cada perfil o intención romántica |
| Etiquetas simuladas | Procedimiento/proveedor de simulación reconocido por presentación | Mantener Edad: simulada, Contacto: simulado y Agencia: comprobación simulada; no convertirlas en distintivos reales |

La prueba de identidad de derechos usa rights-simulator-v1 y no sustituye esas verificaciones públicas. La elegibilidad añade autorización vigente, revisión del gestor y retirada: un distintivo no anula esas reglas. No cambiar etiquetas o procedimientos desde configuración para aparentar integración.

## Estado B14 y siguiente frontera

La preparación157 mantiene el contrato futuro de inicio/eventos idempotentes, firma/frescura/vinculación, revocación, minimización, timeout y resultado desconocido. La outbox actual sigue siendo simulador con reintentos propios, no transporte real. Un backend SMTP que arranca no demuestra entrega; aceptación remota no equivale a recepción. Permanecen pendientes selección y autorización separadas de proveedores, pruebas reales de cada procedimiento/canal, fallos/reconciliación operativos y sus responsables. B14 sigue abierto;13/18puntos cerrados, objetivo completo activo.
