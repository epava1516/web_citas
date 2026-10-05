# Rectificación de cuenta — contrato de implementación

Estado: implementación parcial de CR-09. Fuente/propuesta y confirmación de destino verificadas en su alcance. Primera ejecución solo de cuenta verificada; regresión conjunta, escenarios restantes, limpieza y runtime pendientes. Complementa docs/16; no sustituye los pendientes de exportación, conservación, limitación/oposición, comunicaciones y cierre. No activa proveedores ni producción.

## Ámbito e identidad

La cuenta afectada es `person.subject`, acreditada por el procedimiento del expediente. No usar por sustitución al gestor individual, propietario de agencia, editor o autor de la solicitud. Si falta una cuenta vinculada o existe discrepancia de identidad, requiere evaluación explícita; no crear, vincular ni transferir una cuenta automáticamente.

Campos corregibles: nombre, apellidos y correo. El nombre de usuario generado durante registro es un identificador técnico; no convertir este recorrido en cambio de identidad interna. No admitir contraseña, roles, permisos, MFA, estado de actividad, titularidad o representaciones en el diccionario de corrección. Diferenciar cuenta del sujeto y contactos públicos del anuncio.

## Propuesta y revisión cruzadas

Integrar un bloque de cuenta en la propuesta cifrada existente, consulta auditada de fuente, revisión independiente, comunicación previa y ejecución. Formularios y resultado ES/EN. No aplicar datos en la propuesta, lectura, revisión o envío del aviso. Identidad, cuenta, versión de gestión, derechos y fuente de credenciales se revalidan bajo locks; nunca confiar en una instancia leída antes de esperar.

La fuente debe incluir los campos de cuenta revisados y una estampa del estado de autenticación, sin entregar contraseña, secreto MFA ni tokens. Cambios entre propuesta, comprobación, lectura y ejecución invalidan el material anterior. La corrección de cuenta sola no debe clonar una revisión de anuncio, desarchivar fotografías ni alterar tarifas/contactos/publicación por arrastre.

## Cambio de correo

Normalizar como registro e inicio de sesión y respetar unicidad PostgreSQL sin distinguir mayúsculas. Una comprobación de ámbito no demuestra control del nuevo buzón. Exigir confirmación específica del destino, ligada a cuenta/propuesta/fuente vigentes, antes de ejecutar el cambio. Token impredecible, almacenado por digest, caducidad y uso único; GET no lo consume, POST exige CSRF. No añadir enlaces o valores secretos a logs, plantillas del gestor ni respuestas públicas.

La comunicación previa y su recepción siguen ligadas al canal acreditado anterior. No sustituir destinatarios históricos por el correo propuesto. Cuando el canal anterior ya no sea accesible, conservar una excepción explícita para evaluación del procedimiento; no declarar automáticamente recibido un aviso. Adaptador local de prueba claramente identificado, sin afirmar entrega externa real.

Comprobar disponibilidad del correo también en ejecución: otra cuenta puede reservarlo después de proponerlo. Resolver colisiones como conflicto revisable, sin cambios parciales ni revelación pública de la otra cuenta. No dejar la cuenta sin canal confirmado por una aplicación incompleta.

## Ejecución y efectos

Aplicación atómica, versionada, motivada e idempotente sobre el mismo sujeto. Un replay idéntico no reescribe datos posteriores; uno incompatible se rechaza. Preservar hechos históricos y su disposición por finalidad, sin duplicar datos en cada aviso.

Al cambiar correo, invalidar los enlaces de verificación/recuperación anteriores y revocar sesiones mediante la versión de cuenta existente. Mantener el secreto MFA; si el procedimiento exige una nueva sesión, comprobar otra vez MFA en el siguiente acceso. El token de confirmación del destino queda consumido al aplicarse. Registrar resultado mínimo y comunicaciones pertinentes sin exponer datos anteriores al gestor de un perfil ajeno.

Incluir las nuevas referencias en inventarios y fuente de acceso/supresión, sin crear autorreferencia que invalide el propio plan. La respuesta final requiere hechos de ejecución y comunicaciones; no cerrar el expediente por haber enviado una propuesta.

## Evidencia de aceptación requerida

- Recorrido ES/EN desde propuesta auditada hasta ejecución y resultado persistido, con datos sintéticos.
- Sujeto particular y sujeto representado por agencia; gestor/editor nunca reemplazan la cuenta del sujeto.
- Cuenta no vinculada, suprimida, fuente obsoleta, permiso/MFA revocado y conflicto de interés.
- Correo inválido, reservado con distinta capitalización y reservado durante espera; atomicidad PostgreSQL.
- Confirmación ausente, caducada, ajena, consumida o vinculada a otra versión; GET inocuo y POST CSRF.
- Sesiones y enlaces anteriores inválidos después del cambio, sin desactivar MFA ni publicar contenido.
- Reintentos, dos ejecutores concurrentes y cambio de cuenta mientras una operación espera locks.
- Inventarios/copia/comunicaciones reflejan el ámbito correcto y no exponen secretos o datos de terceros.

Las pruebas de buzón o identidad simuladas se registrarán como simuladas. El mecanismo local no acredita cumplimiento jurídico integral ni los gates de producción.


## Avance de implementación — registro histórico

Módulo de fuente y validación en desarrollo: usa únicamente cuenta de person.subject y bloquea User dentro de una transacción; no sustituye por el gestor. Campos autorizados nombre/apellidos/correo, correo normalizado y unicidad comprobada; contraseña, roles, username y demás campos técnicos rechazados. Fuente de autenticación por HMAC, sin leer para entregar contraseña o secreto MFA. Ninguna de estas funciones aplica cambios.

Pruebas PostgreSQL52543 en curso. Falta integrar propuesta/formularios/consulta/revisión/comunicación/ejecución, confirmación de destino, sesiones/tokens e inventarios según este mismo contrato. No se declara implementación completa ni verificación de identidad real.


Fuente/validación52543 terminal0:2 correctas25,76 s PostgreSQL, sin fallos/errores/omisiones. Sujeto de agencia distinto de propietario, cuenta no vinculada/suprimida, cambios de credenciales, ausencia de contraseña en fuente, whitelist, capitalización/colisión y no mutación verificados. Sin pytest activo. Siguiente integrar bloque de cuenta en fuente/propuesta auditada y pantallas con los controles definidos, después confirmación de nuevo buzón y ejecución. Funciones actuales todavía sin uso en recorrido público; no aceptación CR09.


Fuente y propuesta integradas en desarrollo: HMAC liga estado de cuenta/credenciales; preview solo devuelve los tres campos corregibles. El formulario de rectificación ofrece bloque de cuenta, validado y cifrado en la propuesta. Cambio de origen exige nueva consulta. Cuenta sola no exige una revisión del anuncio para validar propuesta; no muta datos. Ejecutar cuenta sigue rechazado explícitamente mientras falta confirmación del destino y ejecución integral. Batería31331 de22 pruebas en curso; falta ajustar orden del lock User antes de referencias Revision/Blob, comprobar pantallas/revisión independientes y completar resto del contrato. No actualizar runtime ni declarar recorrido completo.


La batería previa terminó22 correctas177,19 s. La carrera adicional reprodujo inversión de orden (1 fallida22,90 s): una fuente esperando User ya retenía Revision. Se corrigió leyendo cuenta al inicio de source_snapshot, antes de Revision/Blob.4 pruebas de cuenta92284 en curso verifican NOWAIT y credenciales frescas tras espera observada en PostgreSQL. No se acredita todavía recorrido completo, confirmación de destino ni ejecución.


Cuenta92284 terminal0:4 correctas39,92 s PostgreSQL, sin fallos/errores/omisiones. NOWAIT sobre Revision/Blob disponible mientras lector espera User; tras liberar obtiene HMAC de nuevas credenciales, sin contraseña en fuente.22 anteriores no se suman ni equivalen a regresión común de la corrección final. Sin pruebas locales activas. Próximo confirmación del correo ligada a propuesta/sujeto/fuente, token de uso único por POST y entrega local simulada; después ejecución/comunicaciones/SSR móvil/inventario/runtime y aceptación. Claude3/3; sin nueva delegación.


## Confirmación del destino en desarrollo

Registro safety0058 con propuesta/sujeto/acción/fuente, digest del token y del destino, plazo24h y fechas de confirmación/consumo/revocación. Contenido de entrega local cifrado; no se envía correo externo, no aparece enlace en pantalla del moderador. Backend desactivado por defecto; simulación expresamente prohibida en producción. El plazo24h es técnico de enlace, no política final de conservación jurídica.

Solicitud desde revisión independiente requiere aprobación, prueba posterior y lectura de cambios vigente. Incrementa versión del expediente y exige nueva comprobación para ejecutar posteriormente. GET de enlace solo presenta formulario; POST con CSRF confirma destino sin aplicar corrección. Al confirmar se elimina el contenido de entrega con el enlace, conservando metadatos; reintento idéntico no reescribe fecha. Reemisión revoca registros anteriores.

Primera batería HTTP2 fallidas32,23s por longitud de operation; corregido nombre conforme a esquema existente. Repetición23628 en curso. Falta integración de ejecución, inventario/limpieza por caducidad, errores/negativos/carreras y navegador ES/EN. No afirmar entrega real o identidad verificada.


Batería HTTP/cuenta82227 terminó6 correctas53,34s, anterior al vínculo proof/inventario. Confirmación ahora conserva referencia protegida a la comprobación de ámbito que autorizó solicitarla y revalida su estado tras locks; no convierte esa referencia histórica en nueva prueba de identidad. Metadatos y contenido cifrado participan solo en HMAC interno del inventario seleccionado, sin descifrar ni proyectar enlace/destino.10 pruebas27576 en curso incluyen header no-referrer en CSRF403. No aceptar aún revocación original/concurrencia/limpieza/navegador ni ejecución del cambio de correo.


Confirmación27576:10 correctas87,58s en batería conjunta destino/cuenta/inventarios. Ampliación76047 en curso para revocación original y Chromium móvil ES/EN. Modelo0058 todavía solo aplicado en PostgreSQL de pruebas. Los resultados anteriores no se suman ni acreditan recorrido completo de ejecución, concurrencia, limpieza o entrega externa.


## URL limpia para confirmar

Las pruebas de navegador encontraron Origin null al enviar POST desde la página no-referrer. El recorrido corregido conserva CSRF: GET del enlace solo valida e intercambia la credencial a una cookie firmada HttpOnly/SameSiteStrict, limitada24h y Secure en producción, y redirige con no-referrer a una URL sin token. GET de esa URL muestra el formulario sin confirmar; solo POST con CSRF registra posesión. La página limpia usa same-origin porque su URL no contiene secreto. Nunca se confía en Origin null ni se desactiva la protección CSRF. Batería97901 en curso, sin resultado aceptado aún.


Confirmación97901 terminal0:4 correctas52,98s, sin fallos/errores/omisiones. HTTP y Chromium móvil ES/EN verifican intercambio a cookie HttpOnly, URL limpia, GET inocuo, POST CSRF y resultado persistido sin cambiar cuenta. XML /tmp/account-email-confirmation-clean-url.xml. No pytest activo; ejecución integral, limpieza, concurrencia, runtime0058 y aceptación CR09 siguen pendientes.


Ejecución26450 terminal0:1 correcta25,96s (4 excluidas), PostgreSQL/HTTP. Recorrido aprobado→confirmación simulada→comunicación/recepción→nueva comprobación→ejecución: correo aplicado, verificación fechada, session_version incrementada y confirmación consumida; anuncio sin clon/cambio de estado/lifecycle, sin aviso de datos de cuenta al gestor; replay no repite cambio. No acredita todavía nombres solos, cambios mixtos, tokens/sesiones HTTP, carreras, limpieza o runtime0058. Continuar batería conjunta afectada y escenarios faltantes antes de aceptación CR09.


Batería38545 terminal0:20 correctas269,52s, cero fallos/errores/omisiones, PostgreSQL/Chromium. Cuenta, confirmación y revisión/ejecución de rectificación anteriores pasan juntos. Ruff/check/makemigrations/diff limpios. No acredita requisitos pendientes de cuenta, limpieza o runtime ni cierre CR09.


## Limpieza técnica del enlace de entrega

La tarea purge_expired_account_confirmation_delivery selecciona hasta100 registros caducados con contenido, adquiere locks del ámbito y cuenta antes del registro y vuelve a comprobar caducidad. Solo vacía encrypted_delivery; conserva la evidencia y no interpreta caducidad como cierre del expediente. Beat programado cada60s; limpieza funciona con backend disabled. No elimina datos de backups/WAL ni sustituye conservación por finalidad. Ejecución de correo exige backend de desarrollo habilitado; producción permanece bloqueada hasta integración real autorizada. Batería36442 en curso; sin aceptación de limpieza hasta terminal ni evidencia de worker real para esta tarea.


Autenticación10944 terminal0:1 correcta27,72s (5 excluidas). Rechaza confirmación sin confirmar/caducada/revocada/consumida y ejecución en producción sin mutar cuenta ni crear ejecución; después aplica con confirmación vigente, invalida AccountToken, enlace reset anterior HTTP400 y sesión anterior cerrada por middleware real. MFA conserva secreto/version/estado; anuncio intacto y replay no repite cambio. Correo locmem explícitamente simulado. Ruff/check/makemigrations/diff limpios; sin pytest activo. Pendiente nombres solos, cuenta sin anuncio, cambios mixtos, concurrencia y colisiones, interfaz integral, runtime0058/worker/Beat y regresión CI final. CR09/contrato abiertos; Claude3/3.


Variantes10442 terminal0:2 correctas33,12s,6 excluidas, PostgreSQL. Nombres solos no requieren backend de correo ni confirmación, conservan cuenta salvo nombres y anuncio completo; nombres+título aplica cuenta y crea revisión draft sin aceptación editorial, pausa publicación y mantiene versión aprobada histórica. No acredita todavía cuenta sin anuncio ni correo+título ni carreras.


Carreras24979 terminal0:2 correctas31,30s,8 excluidas. pg_blocking_pids confirma espera sobre User; cambio de nombre o revocación de comprobación original durante espera deniega confirmación tras liberar, sin confirmed_at/consumed_at ni cambio de correo. PostgreSQL real, entrega e identidad simuladas. No prueba todavía dos ejecutores, colisión de correo ni limpieza concurrente. Sin pytest activo; siguiente completar estas carreras y correo+título/cuenta sin anuncio, interfaz integral y runtime antes de aceptación.


Carreras17254 terminal0:2 correctas35,61s, PostgreSQL. Dos conexiones aplican misma clave/versión con resultado único y rights_version +1; reserva de destino por otra cuenta no confirmada mientras execute espera índice case-insensitive produce conflicto y rollback de cuenta/acción/ejecución/consumo/respuesta. Bloqueo realmente observado por pg_blocking_pids. Identidad y entrega siguen simuladas; no aceptación CR09.


74037 terminal0:4 correctas54,35s PostgreSQL, sin fallos/errores/omisiones. Dos ejecutores/colisión previas pasan; correo+título aplica atómicamente, consume confirmación y deja anuncio pausado con nuevo draft sin aceptación; limpieza espera User observado y conserva entrega si caducidad cambia antes de liberar. No suma baterías ni verifica worker real. Reproducción adicional de prueba de ámbito revocada durante espera en ejecución en curso, XML /tmp/account-execution-proof-before.xml; fuente congelada.


Reproducción1422 terminal1:1 fallida25,39s,4 excluidas; execute aplicó corrección con prueba de ámbito revocada durante espera User observada. Corregido rectification_review.current: authorized_proof se revalida después de source_snapshot potencialmente bloqueante, antes de admitir cambios/consulta/revisión/comunicación/confirmación/ejecución. Batería conjunta afectada en curso /tmp/account-execution-proof-common-final.xml (cuenta/destino/carreras/rectificación); fuente congelada. No aceptación de corrección hasta terminal ni sustituir regresión CI/runtime.


Docker cuenta: build83711/migrate61400/recreate31532 terminal0; safety0058 aplicada, check limpio/migrate--check sin pendientes, UID10001, Caddy health200. Hashes review/confirmación iguales host/app/worker/Beat; backend entrega disabled. Worker ejecutó tarea08a4b59f-1a3a-4756-a300-6b7129e31cf7 con resultado0; Beat envío periódico observado. Transporte real sobre cero registros elegibles, no purga con contenido ni proveedor/identidad reales. Batería97343 sigue activa y fuente congelada; no aceptación CR09.


Batería97343 terminal0:30 correctas350,14s PostgreSQL/Chromium, cero fallos/errores/omisiones. Incluye corrección de revalidación authorized_proof tras espera real User; deniega ejecución sin mutar si prueba original se revoca durante espera. Cuenta/destino/carreras/mixto/limpieza y rectificación anteriores pasan conjuntamente. Runtime0058/check/UID10001/health200/hashes y transporte worker/Beat resultado0 verificados por separado. Falta cuenta sin anuncio accesible desde vínculo de ámbito, interfaz integral ESEN, purga no vacía worker, inventarios/exportación/retención final y CI común. No aceptación CR09/contrato/producción; no pytest activo. Claude3/3, sin delegación adicional.


## Recorrido móvil de cuenta

Pruebas ESEN integran cuenta en revisión de cambios mixtos: consulta auditada, aprobación independiente, solicitud de destino SSR, confirmación en navegador anónimo mediante entrega expresamente simulada, nueva comprobación y consultas, comunicación/recepción/ejecución. Validación posterior exige correo aplicado, versión de sesión incrementada y token consumido; sigue revisión de destinatarios y avisos del gestor del contenido editorial. En revisión, display_account limita proyección a tres campos autorizados con etiquetas humanas, sin datos técnicos; GET no presenta valores. Batería20479 en curso, sin aceptación todavía. Identidad y entrega siguen simuladas.


20479 terminal1:2 móviles fallidas72,16s (9 excluidas). Ejecución mixta correo+fotografías preparadas denegaba «Selected images expired or unavailable»: apply de cuenta modificaba source/baseline antes de available para fotos staged. Movida aplicación de cuenta después de preparar/clonar selección editorial y antes de modificar person/lifecycle, en misma transacción; colisiones o confirmación inválida siguen revirtiendo todo. Repetición /tmp/account-mobile-integral-final.xml en curso; fuente congelada, no aceptación hasta terminal. El test empieza con propuesta creada por helper backend real, no prueba aún escritura de propuesta por navegador móvil.


Primera edición de orden no aplicada por AssertionError (formato multilinea); prueba12852 detenida explícitamente, terminal2/KeyboardInterrupt sin resultados completos. Después de terminal, cambio aplicado realmente: prepare editorial/selección de staged intactos y apply cuenta justo antes de alias/person/lifecycle, mismo atomic. Repetición75883 /tmp/account-mobile-integral-after-order.xml activa, fuente congelada; no afirmar corrección verificada hasta terminal.


75883 terminal0:2 móviles ESEN correctas76,12s (9 excluidas). Orden de aplicación corregido permite correo+fotos staged en mismo atomic; revisión/confirmación simulada/nueva comprobación/lecturas/comunicación/recepción/ejecución y evaluación de destinatarios/avisos pasan. Modelo recibe correo/session_version+1 y confirmación consumida. La propuesta inicial sigue preparada por servicios backend reales, no escritura móvil. Nueva regresión conjunta afectada pendiente antes de Docker/commit. No entrega/identidad externas ni cierre CR09.


Docker corrección móvil: build8870/recreate81441 terminal0, check/migrate--check limpios sin migración nueva, UID10001/health200. Hashes account/execution/review iguales host/app/worker/Beat, incluye display y orden de aplicación corregido. Ruff/diff limpios. Batería45758 aún viva:10 cuenta/destino correctas dentro de suite30, concurrencia/revisión en curso; fuente congelada, sin commit ni aceptación antes de terminal.


45758 terminal0:30 correctas361,44s PostgreSQL/Chromium, cero fallos/errores/omisiones; incluye display y corrección correo+staged junto a cuenta/confirmación/carreras/revisión. Docker final ya verificado. Añadidas2 pruebas de escritura de propuesta por formulario móvil ESEN: login/MFA→GET sin valores→consulta auditada→editar bloque cuenta→propose→resultado/reload→GET sin valores, sin mutar User/anuncio. Batería /tmp/account-mobile-proposal.xml en curso, solo ampliación de pruebas; no aceptar hasta terminal ni sumar con30 como suite32.


1173 terminal0:2 propuestas móviles ESEN correctas36,12s (4 excluidas), Chromium390x844. Login/MFA reales, GET sin valores, consulta auditada de cuenta del sujeto, escritura de bloque account, propuesta cifrada persistida, resultado/reload y GET posterior sin valores. Sin mutación de User/session_version ni clon editorial.30 comunes361,44s prueban fuente funcional actual por separado; no sumar suites como32. Docker/hash/check/health200 verificados, solo pruebas/documentación añadidas después. Sin pytest activo. Cuenta sin perfil/docs51, purga worker con contenido, copia/inventarios/retención/comunicaciones/cierre y contrato completo pendientes; CI anteriores activas.
