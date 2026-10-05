# Levantamiento comunicado de restricciones por finalidad

Estado: recorrido0070 de consulta, propuesta comunicada, recepción, comprobación posterior y ejecución implementado; cola por expediente, ES/EN móvil y Docker verificados localmente. Regresión conjunta final en curso antes de entrega. Depende de docs58–59; no acepta derechos ni CR09 íntegros. Calendario global y otras finalidades pendientes (docs61).0069 entregada e3ea093; su CI completa registró un fallo de sincronización Chromium, corregido localmente y pendiente de nueva regresión completa.

## Requisitos del recorrido

El ledger activo no debe desactivarse por fecha de revisión, cierre de caso, una nueva copia o modificación directa desde interfaz ordinaria. Evaluar una medida concreta por cuenta/finalidad y su modo restrict/cease, conservando las demás medidas activas. Una medida cease por oposición no se equipara automáticamente a una limitación temporal resuelta; exigir una solicitud nueva/retomada comprobada y fundamento revisado antes de permitir otra vez el tratamiento.

Se mantiene referencia al expediente original, comprobación, ejecución, autor y decisión revisada. Revisor independiente del ejecutor original, con permiso dedicado, revisión/ejecución/respuesta de derechos y MFA/sesión vigentes/COI. Reasignación canónica del caso cuando corresponda; no crear permisos implícitos por ser propietario de agencia.

Recorrido íntegro: consulta auditada de medida/decisiones actuales → propuesta motivada independiente → respuesta privada minimizada vinculada a propuesta → comunicación/recepción por canal registrado → nueva comprobación de identidad/ámbito después de propuesta y recepción → lectura completa actual de expediente/respuestas → ejecución de levantamiento de esa medida. El usuario debe conocer qué finalidad se propone reactivar; no incluir motivos internos, identificadores de moderadores, contactos de terceros o evidencia ajena.

Una confirmación simulada de desarrollo mantiene ese carácter. El acuse técnico no acredita comprensión humana, identidad real ni entrega del proveedor; no activar este procedimiento con adaptadores de prueba en producción.

## Modelo y causalidad previstos

Proposal enlaza Restriction, acción, prueba inicial, respuesta, HMAC de fuente y motivo cifrado; ejecución de release enlaza acción/prueba fresca/fecha. Mantener originales inmutables y registro de liberación separado. Unicidad de liberación efectiva por medida; propuestas reemplazadas no se ejecutan. Clave exacta idempotente, otra firma rechazada.

Fuente contempla cuenta/ámbito vigente, ledger activo/revisión/versión, decisión y ejecución originales, mensajes del solicitante y otros cambios pertinentes. No incluir la propia propuesta/aviso de forma que su creación invalide el HMAC. Comprobar por separado versión de respuestas/canal, última propuesta y recepción, prueba posterior y vigencia de lecturas. Cambiar fuente/ámbito/revocación/propuesta/aviso debe impedir ejecución sin levantar restricciones.

Locks canónicos de caso/ámbito → ejecución/medida → propuesta; adquirir User de preferencias según jerarquía existente. Revalidar permiso/COI/sesión/prueba/fuente después de esperas y antes de confirmar efectos, siguiendo corrección0069. No retener joins opcionales accidentalmente. Las operaciones de favoritos bajo User deben observar de forma atómica el estado anterior o el nuevo estado de la medida.

## Pantallas y pruebas exigidas

Cola privada por estado/vencimiento/finalidad con datos minimizados; pantalla de consulta/propuesta/ejecución ESEN, GET sin motivos/decisiones, POST auditado. En acuse privado, respuesta propia y recepción sin fundamentos internos. Resultado de levantamiento conserva solicitud abierta y no otorga excepciones para otra finalidad.

Probar medida válida, autor original/otro ámbito/no permiso/MFA revocados, falta de consulta/recepción/comprobación posterior, propuesta antigua, prueba revocada durante waits, claves repetidas/concurrentes, dos medidas activas para misma finalidad (levantar una no desbloquea la otra), preferencias preservadas, otros usuarios y canal de derechos accesibles, móvil ESEN/recarga, PostgreSQL/Docker y regresión conjunta.

Calendario operativo de medidas y registro/ejecución de excepciones acotadas siguen entregas necesarias; levantar una medida no es una excepción puntual ni decide conservación histórica. Fuente jurídica y revisión primaria de artículos18/19/21: docs58. Revisión jurídica externa permanece gate de producción.


Consulta/propuesta0070 iniciadas:PurposeRestrictionRead/PurposeReleaseProposal, permiso dedicado release_purpose_restriction, revisor distinto al ejecutor original, asignación/lectura/prueba vigentes y snapshot/HMAC por medida/cuenta/mensajes/favoritos/otras medidas activas/plan original. Consulta audita antes de descifrar y valida firma histórica sin imponer fecha futura al plan antiguo. Restrict exige fundamento resuelto; cease exige mensaje nuevo del sujeto (no moderador) revisado. Propuesta emite respuesta privada fija/minimizada progress, conserva medida/caso abiertos, invalida prueba para siguiente actuación. UI GET sin fundamentos/POST inspect-propose conectada; ejecución/recepción/prueba posterior/cola/carreras/móvil/runtime pendientes.6914 terminal1:2 fallidas36,07s por operation más larga que RightsAction.max_length20; abreviadas purpose_rel_inspect/propose sin alterar columna. Check48121 terminal0/no cambios, Ruff/diff limpios. Repetición /tmp/purpose-release-proposal-final.xml activa, fuente congelada.0070 no runtime ni aceptada.


8355 terminal0:2 propias36,22s PG sin fallos/errores/skips. Consulta/propuesta HTTP, idempotencia/GET sin fundamentos, comunicación progress privada y medida activa/solicitud abierta comprobadas; autor original denegado y cambio improcedente a resume_requested rechazado. Después de terminal añadida ejecución purpose_release.execute y UIoperationexecute: selecciona propuesta concreta bajo locks, recepción del canal, prueba diferente/posterior a propuesta y acuse, última propuesta/versionrespuesta/HMAC vigentes; desactiva solo medida y guarda acción/prueba/fecha, mantiene solicitud abierta.89697 activa3 casos /tmp/purpose-release-execution.xml, fuente congelada;0070 no runtime, cola/carreras/móvil/regresión pendientes.


89697 terminal0:3 propias43,72s PG sin fallos/errores/skips. Recorrido reasignación/revisor independiente/comprobación simulada→consulta→propuesta/aviso→recepción anónima del canal→comprobación posterior→levantamiento/replay conserva favoritos y vuelve a permitir ruta ordinaria, caso sigue reviewing/unverified. Original privado no aparece GET. Tras terminal reforzada firma de propuesta almacenada y recarga del estado de prueba original después de lock de propuesta, evitando caché previa a espera. Batería conjunta6 iniciada /tmp/purpose-release-common.xml; fuente congelada. Cola/varias medidas/cease/newrequest/negativos ampliados/carreras/móvil/runtime0070/regresión final pendientes; no aceptar CR09.


98152 terminal0:6 pruebas propias66,13s PostgreSQL, sin fallos/errores/skips (/tmp/purpose-release-integrity.xml). Rechazo controlado de motivo cifrado inválido, objeto sin reason y ground alterado; restricción activa, propuesta sin liberación, versión/estado del caso, acciones y favoritos preservados tras rollback. Tres recorridos anteriores siguen pasando. Cola, varias medidas, cease/solicitud nueva, concurrencia, móvil y runtime0070 pendientes; CR09 abierto.


62750 terminal0:6 propias68,56s PG sin fallos/errores/skips (/tmp/purpose-release-queue.xml). Cola GET enlaza medida, no revela REASON, private/no-store, released vacío, filtro finalidad desconocida400 y POST405; recorridos de propuesta/levantamiento/integridad siguen pasando. Ruff/check/makemigrations--check/diff limpios;91932 terminal0/no cambios. Cola por expediente verificada HTTP; calendario global, varias medidas, cease, carreras, móvil y runtime0070 pendientes.


30039 terminal0:7 propias74,80s PostgreSQL sin fallos/errores/skips (/tmp/purpose-release-cease.xml). Cease preparado/revisado/ejecutado por servicios reales conserva medida/favoritos y rechaza dos fundamentos sin solicitud nueva, sin propuesta/respuesta. Orden de imports normalizado después de terminal; Ruff/diff limpios. No acredita aún solicitud nueva válida, autor ajeno, concurrencia, móvil ni runtime0070; CR09 abierto.


63122 terminal0:10 propias91,12s PostgreSQL sin fallos/errores/skips (/tmp/purpose-release-new-request.xml). Mensaje real POST canal→nueva lectura/comprobación simulada→consulta→propuesta: sujeto autenticado y portador anónimo admitidos bajo comprobación/revisión; moderador autenticado rechazado sin propuesta/respuesta. En los tres casos medida permanece activa; comunicación nunca libera por sí sola. Recorridos previos/integridad/cola/cease pasan conjuntamente. Ruff/diff limpios. Levantamiento posterior de cease, varias medidas, carreras, móvil y runtime0070 todavía pendientes.


71038 terminal0:11 propias98,43s PostgreSQL sin fallos/errores/skips (/tmp/purpose-release-mode-integrity.xml). Consulta rechaza modo alterado respecto a decisión original firmada y revierte auditoría parcial; recorridos anteriores pasan. Tras terminal corregida sincronización de test_browser_revised_listings: esperar resultado visible de resolución antes de reload, conservando comprobación posterior de persistencia. Reproducción afectada en verificación; CI previa permanece failure, no redefinir como verde.


83519 terminal0:2 carreras35,47s PostgreSQL sin fallos/errores/skips (/tmp/purpose-release-proposal-races.xml). Esperas observadas de dos conexiones sobre holder real: misma clave genera una sola propuesta/respuesta y versión+1; permiso revocado durante espera deniega ambas sin avisos/propuestas/versiones nuevas. Medida activa/favoritos conservados. No simular bloqueos ni sumar como regresión común; carreras de ejecución/pruebas revocadas, varias medidas, móvil/runtime0070 y aceptación común pendientes. Ruff/diff limpios.


20411 terminal0:5 carreras60,37s PostgreSQL sin fallos/errores/skips (/tmp/purpose-release-execution-races.xml). Dos propuestas idempotentes/permiso revocado y tres ejecuciones concurrentes: replay misma clave libera una vez/una acción/version+1; revocar prueba inicial o fresca durante espera observada de propuesta rechaza ambas sin acción/versiones nuevas, medida activa/favoritos intactos. Carreras verificadas sobre conexiones reales y pg_blocking_pids; status failed inyectado solo como fixture de revocación, no flujo de proveedor real. Ruff/diff limpios. Varias medidas, interfaz móvil, Docker0070 y regresión común pendientes; CR09 abierto.


67382 terminal0:2 seleccionadas36,66s PostgreSQL,10 deselected por -k (no skips), /tmp/purpose-release-multiple-measures.xml. Una medida levantada devuelve favoritos200; segunda medida sintética activa para misma cuenta/finalidad conserva favoritos409 y segundo ledger sin propuesta/alteración. No acredita segundo workflow de creación. Iniciada regresión común de12 propias+5 carreras+3 ejecución0069+2 navegador corregido; fuente congelada hasta terminal. Móvil/runtime0070/calendario/finalidades restantes y CR09 global pendientes.


15137 terminal0:22 comunes183,61s PostgreSQL/Chromium sin fallos/errores/skips (/tmp/purpose-release-joint.xml).12 levantamiento+5 carreras+3 ejecución0069+2 navegador corregido, una sola batería; evidencia normalizada con hashes docs/evidencias/levantamiento-finalidad-regresion.json. No sumar ensayos anteriores. Móvil levantamiento/runtime0070/toda regresión CR09 pendientes, última CI e3ea093 sigue failure anterior a corrección. Fuente descongelada tras terminal; continuar móvil/operación0070 sin aceptar CR09 íntegro.


12739 terminal0:2 móvilESEN49,47s PostgreSQL/Chromium sin fallos/errores/skips (/tmp/purpose-release-mobile.xml). Login/MFA/lectura/cola→consulta/propuesta→reload con última propuesta y proposal_id→recepción HTTP/nueva comprobación simulada→sesión reabierta/lectura→ejecución/reload, medida levantada/caso abierto/favoritos conservados/viewport390 sin overflow. Recepción y prueba posterior verificadas HTTP/servicio fuera del browser; no proveedor real. Vista GET recupera solo metadatos de última propuesta, nunca motivos. Regresión común anterior22 no incluye modificación vista; ampliar batería común después de runtime/verificación final.


Docker0070 verificado:build26066/migrate19342/recreate19746/check77476/hash39410/providers77064 terminal0. Migración0070 aplicada;check/migrate--check limpios,8 fuentes host/app/worker/Beat idénticas, UID10001, healthHTTP200, identidad derechos/avisos/confirmación disabled. Evidencia docs/evidencias/levantamiento-finalidad-runtime.json. Dos móvil49,47s anteriores pasan; regresión22 anterior no incluye última vista GET recuperable, ampliar común antes de commit/aceptación parcial. CR09/finalidades/calendario global/conservación integral siguen pendientes.


10389 terminal0:24 comunes221,47s PostgreSQL/Chromium sin fallos/errores/skips (/tmp/purpose-release-final-joint.xml).12 levantamiento+5 carreras+2 móvilESEN+3 ejecución0069+2 navegador corregido, sobre última vista GET recuperable y runtime0070. Evidencia normalizada actualizada docs/evidencias/levantamiento-finalidad-regresion.json; no sumar ensayos anteriores. Entrega parcial0070 lista para commit/push con identidad autorizada; siguiente docs61 calendario global, luego excepciones/otras finalidades/conservación integral y pendientes CR09 antes de CR10/GS01/BF/BB/C. CI completa nueva necesaria; CI e3ea093 anterior permanece failure.
