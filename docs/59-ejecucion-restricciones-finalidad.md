# Ejecución durable de restricciones por finalidad

Estado: implementación en verificación0069. Complementa docs58 y docs40; no acepta limitación/oposición integral, respuesta final ni CR09.

## Alcance de esta entrega

ProcessingExecution vincula acción, aprobación independiente, comprobación de ámbito, sujeto excluyente Person/User y resultado cifrado. PurposeRestriction registra cuenta realmente afectada, finalidad, modo restrict/cease, fecha de revisión y estado activo. FK PROTECT y unicidad ejecución/finalidad preservan evidencia. La fecha de revisión no es fecha de liberación ni fundamento jurídico para uso ordinario.

Primera finalidad con guardas: account_preferences. Rutas de favoritos exigen transacción/bloqueo de User y comprueban restricción vigente antes de entregar datos, crear o eliminar preferencias. HTTP409 privado/no-store, sin información del expediente ni identidad de revisores. La comprobación no elimina favoritos ni suspende autenticación, cuenta/agencia o canal de derechos. Otros usuarios mantienen acceso a sus propios favoritos. Una supresión que seleccione preferencias restringidas deniega antes de eliminar: no interpretar nueva solicitud como excepción automática a una limitación aún vigente.

## Ejecución revisada

Servidor exige permisos de revisión/ejecución/MFA/sesión frescos y COI; responsable asignado. Caso reviewing restriction/object, versiones/lecturas/prueba/fuente vigentes, plan con aprobación independiente y digest coherente. Solo ejecuta finalidades implementadas seleccionadas con operación restrict/cease; continue/review no crean medidas. Mezcla de finalidad soportada y no implementada deniega completa sin ejecución parcial silenciosa. Resultado declara partial=true/data_deleted=false y demás finalidades pendientes. Transacción crea acción/ejecución/medidas; caso sigue abierto, versión incrementa y comprobación queda unverified. Repetición exacta devuelve ejecución original sin nuevas medidas; permiso vigente sigue obligatorio.

Interfaz privada GET/POST processing_execute /es|en/moderation/rights/<UUID>/processing/<planUUID>/execute/: formulario y confirmación explícita, GET sin fundamentos. Registro visible solo tras POST correcto. Mensaje explica alcance parcial. Preparación/revisión preservan sus decisiones originales.

## Continuación obligatoria

- Verificar carreras con lectura/creación/eliminación de favoritos y supresión; permisos/prueba cambiados durante espera, ejecuciones simultáneas, historial después de tombstone.
- Móvil ESEN y regresión con favoritos/supresión/pruebas anteriores, Docker0069 y hashes de rutas/plantillas/guardas.
- Restricciones efectivas para publicación, medios, contacto, representación y otros tratamientos según decisiones. No declarar modo integral mediante un ledger sin consumidor.
- Excepciones revisadas por finalidad y ámbito con autorización minimizada, audiencia/avisos pertinentes y conservación para reclamaciones, sin desactivar una medida globalmente para efectuar una única operación.
- Levantamiento independiente, comunicación previa, comprobación fresca y ejecución; fecha o cierre de caso no levantan automáticamente medida.
- Calendario operativo de revisión de medidas, conservación propia de nuevos artefactos, inventario/copia adicional, respuestas finales y conciliación tras restaurar.

Fundamentos de procedimiento y fuentes primarias en docs58 (AEPD/RGPD artículos18/19/21). La prohibición técnica conservadora requiere excepción revisada para futura supresión; no afirma que la supresión sea jurídicamente imposible.

## Verificación activa

Migración0069 creada, no aplicada al runtime normal0068.92908 activa3 PostgreSQL /tmp/processing-execution.xml; fuente congelada hasta terminal. Ruff/diff limpios. Check/makemigrations89261 en curso. No prueba móvil, concurrente ni runtime aceptadas aún; Claude3/3.


92908 terminal1:2 correctas/1 fallida42,53s PG; HTTP/replay/CSRF/favoritos preservados y bloqueados/otro usuario/canal derechos/fecha pasada sin levantar pasan, finalidad no implementada denegada. Tercero falla antes de supresión: helper prepared_account usa RightsRequest.get sin filtro incompatible con dos expedientes. Sustituido por segundo intake público→claim→lectura→vínculo cuenta→comprobación independiente simulada→lectura vigente, preservando primer caso/medida.4805 repetición3 activa /tmp/processing-execution-final.xml; fuente funcional congelada. Check/makemigrations89261 terminal0 sin cambios, Ruff/diff limpios.0069 no runtime ni aceptación CR09.


4805 terminal0:3 propias41,76s PG sin fallos/errores/skips. Medida propia aplica una vez/replay, conserva favoritos/identidad/sesión, bloquea GET/add/remove409, otro usuario mantiene acceso, canal derechos200; fecha revisión pasada no levanta medida. Finalidades no implementadas deniegan íntegramente. Segundo expediente real intake/claim/link/verificación simulada/fuente/plan de supresión denegado por restricción, sin ErasureExecution ni eliminación. Ruff/diff limpios. Regresión favoritos/supresión/ejecución iniciada /tmp/processing-execution-regression.xml; fuente congelada hasta terminal. Pendiente carreras/móvil/runtime0069, restantes finalidades/excepciones/levantamiento/avisos/respuesta final; CR09 abierto.


97922 terminal0:9 conjuntas77,60s PostgreSQL/Chromium favoritos anteriores/supresión de cuenta/ejecución por finalidad, sin fallos/errores/skips. Preparadas5 carreras: favoritos index/add/remove bloqueados por cuenta observan nueva medida al liberarse; ejecución misma clave única y permisos revocados durante espera rollback. Batería /tmp/processing-execution-races.xml iniciada, fuente congelada.0069 no runtime; móvil/carreras/aceptación conjunta y finalidad integral pendientes.


66192 terminal1:4 correctas/1 fallida58,33s PG. Index/remove esperan User y observan medida409; ejecución misma clave única y revocación permiso rollback pasan. Add devolvía404 antes del bloqueo: fixture elegía Listing.first por UUID y podía ser privado; helper ahora selecciona anuncio realmente publicly_visible, sin relajar guarda.4569 ampliada10 casos ejecución/carreras/móvil ESEN activa /tmp/processing-execution-expanded.xml; fuente funcional congelada. Build62545 en curso /tmp/processing-execution-build.log, no runtime0069 antes de terminal.


4569 terminal0:10 conjuntas97,32s PG/Chromium, ejecución/carreras/móvil ESEN positivos y negativos; fixture de add ahora anuncio público real. Build62545 terminal0, anterior a futuras correcciones si las hay. Añadida carrera específica de revocación de prueba durante espera sobre fila de aprobación (después de current inicial); reproducción /tmp/processing-execution-proof-wait.xml en curso, fuente funcional congelada. No aplicar0069/runtime ni aceptar fuente final antes de resolver este punto de autoridad.


27601 terminal1:1 fallo29,05s (5 excluidas), reproducción real de comprobación revocada durante bloqueo ApprovalReview: execute devolvió executed tras estado failed. Corregido processing_execution.execute: adquirir review/targetUser y volver a current (permisos/MFA/sesión/prueba/fuente) después de esos locks antes de validar aprobación/registrar medida. Imagen62545 anterior a corrección, requiere reconstrucción. Batería final11 ejecución/carreras/móvil iniciada /tmp/processing-execution-expanded-final.xml; fuente congelada hasta terminal. No runtime0069 ni aceptación CR09.


29829 terminal0:11 conjuntas105,77s PG/Chromium sobre corrección final. Incluye revocación proof durante espera ApprovalReview denegada sin ejecución/medida/version cambiado; demás carreras y móvil ESEN pasan. Build1702 terminal0 imagen corregida. Migración normal0069 y regresión completa afectada35 casos iniciadas /tmp/processing-purpose-enforcement-common.xml; fuente congelada hasta terminal, no aceptación común todavía. Runtime/hash/check finales pendientes;CR09 abierto.


Runtime0069: migración39997/recreate78191 terminal0. Check56261 y hash43686 en comprobación; evidencia restricciones-finalidad-runtime.json. Regresión27968 confirmada iniciada35 casos /tmp/processing-purpose-enforcement-common.xml, recuperar mismohandle hasta terminal y no reiniciar por demora. Fuente funcional congelada. Pendientes finalidad integral/excepciones/levantamiento/avisos/calendario de medidas/retención y resto contrato, sin aceptación CR09.

56261/43686 terminal0:check/migrate--check limpios,12 fuentes iguales host/app/worker/Beat,UID10001/health200/0069/proveedores disabled.27968 pendiente de terminal; sin commit/push de0069 aún.


27968 terminal0:35 conjuntas257,01s PostgreSQL/Chromium sobre fuente final0069, sin fallos/errores/skips. Preparación/revisión/cuentas/perfiles/ejecución/revocación tardía/concurrencia/móvil/favoritos/supresión pasan juntos. Runtime0069/12 hashes/UID10001/health200/check/proveedores disabled comprobados por separado. Evidencias restricciones-finalidad-{regresion,runtime}.json. CI calendario70114b2/37257818467 completed success616p2080,40s confirmada/log /tmp/ci-70114b2.log normalizada, anterior a0067–0069. F164550/37259279275 sigue in_progress confirmado. No pytest activo; Ruff/diff limpios. Siguiente levantamiento comunicado concreto docs60 (diseño no implementado), calendario/excepciones/otras finalidades/inventario/retención/copia integral/respuestas finales y resto CR09→CR10→GS01→BF/BB→C. Claude3/3; ninguna aceptación integral CR09/producción.
