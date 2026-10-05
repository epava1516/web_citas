# Ejecución y levantamiento por finalidad: publicación

Estado: entrega parcial de CR-09 verificada localmente mediante regresión conjunta y corrección dirigida; CI de entrega pendiente. Continúa CR-09, sin sustituir sus condiciones de aceptación. Referencias: docs/25, docs/58–62 y contrato16.

## Problema comprobado al iniciar la integración

`processing_execution.execute` solo ejecuta `account_preferences` y exige cuenta del sujeto. `PrivacyPublicationHold` ya protege el perfil mediante `validate_submission`, pero representa una cautela del expediente, no una decisión completa por finalidad. Su levantamiento actual admite restriction/object/rectify y no identifica una decisión aprobada restrict/cease. Añadir publication al formulario sin distinguir ese origen permitiría un levantamiento sin las condiciones específicas de oposición.

## Contrato de integración

1. Publication requiere expediente enlazado a Person; un expediente exclusivamente de cuenta debe rechazarla sin escribir acciones ni medidas. No exigir cuenta de sujeto para publicación: una persona representada sin cuenta conserva sus derechos.
2. Mantener revisión independiente del plan, comprobación vigente, asignación, MFA, recusación, fuente y autorización posteriores a esperas. Solo ejecutar la decisión restrict/cease aprobada para publication.
3. Asociar la ejecución a una medida persistente de publicación mediante referencia explícita y protegida; conservar modo y fecha de revisión de la decisión. El fundamento jurídico sigue siendo el aprobado por humanos en el plan cifrado; no inferirlo de una etiqueta técnica.
4. Pausar una publicación visible, limpiar disponibilidad e invalidar formularios de ciclo de vida. Conservar revisión aprobada, fotos, tarifas y contactos. Otros estados no deben convertirse en published ni destruir datos.
5. Reutilizar la guarda central para ficha, fotos, búsqueda, envío, aprobación, renovación y disponibilidad. La medida pertenece a Person, sobrevive a cambios de gestor y no alcanza a otros perfiles de la agencia.
6. Selección mixta publication/account_preferences: una transacción, una acción auditada, todas las medidas o ninguna. Cuenta del sujeto obligatoria únicamente cuando se seleccionan preferencias. Reintento exacto devuelve la misma ejecución; otra clave no duplica la finalidad del mismo plan.
7. Diferenciar cautela anterior y medida por finalidad. Ningún levantamiento genérico puede liberar la segunda sin verificar su decisión original. Conservar las cautelas existentes durante la transición.
8. Levantamiento por finalidad: consulta auditada del plan original, revisor independiente, fundamento explícito, propuesta comunicada, recepción y comprobación renovada. Cease exige nueva instrucción atribuible al sujeto y revisada; ni una fecha vencida ni una nota del moderador bastan. Liberar solo la medida seleccionada y nunca republicar automáticamente.
9. Calendario operativo: mostrar modo, vencimiento de revisión y seguimiento; el vencimiento no desactiva medidas. Cambiar fecha o estado invalida propuestas dependientes mediante versión/fuente.
10. Incluir medida, vínculo de ejecución y operaciones de seguimiento en inventarios y fuentes correspondientes sin introducir circularidad con lecturas del propio expediente. No descifrar fundamentos para enumerar dependencias.
11. Interfaz privada ES/EN: ofrecer publication solo en ámbito de perfil; explicar conservación, bloqueo y solicitud abierta. GET no muestra resultados ni razones; POST exige CSRF y cabeceras privadas, incluidos errores.

## Evidencia de aceptación necesaria

- Preparar, consultar, revisar y ejecutar planes reales del procedimiento usando datos sintéticos y PostgreSQL; proveedor de identidad simulado declarado.
- Perfil con cuenta, persona representada sin cuenta, agencia con dos perfiles y rechazo de ámbito exclusivamente de cuenta.
- Restrict y cease; selección mixta, rollback tras fallo, replay exacto y duplicado con otra clave.
- Comprobar exposición y todas las rutas centrales incluso con status forzado a published; traslado no evade bloqueo.
- Levantamiento restrict/cease con recepción y comprobación renovada; impedir el atajo del levantamiento cautelar y conservar otras medidas activas.
- Carreras PostgreSQL observables con modificación de autoridad, fuente, aprobación o medida durante espera; validar estado posterior y ausencia de efectos parciales.
- Navegador móvil ES/EN: ejecutar, recargar, volver por GET, rechazos de permiso/CSRF y ausencia de desbordamiento.
- Migraciones con datos previos, regresión conjunta, Docker app/worker/Beat, salud y coincidencia de fuentes. Ninguna prueba aislada acepta CR-09 entero.

La implementación debe completar estos puntos como un mismo flujo vertical antes de declarar publication ejecutable. Las demás finalidades y el resto del contrato permanecen pendientes.

## Primera integración backend

Migración0073 incorpora ProcessingExecution.publication_hold protegido y único. execute admite publication solo para perfil, usa la decisión restrict/cease del plan aprobado y crea medida bajo la misma transacción. Reutiliza la guarda central, pausa estado publicado, limpia disponibilidad y versiona ciclo de vida. Preferencias conservan sus requisitos de cuenta. privacy_release rechaza medidas vinculadas a esta ejecución: su levantamiento específico aún no está disponible. El formulario sigue ofreciendo solo preferencias hasta completar el flujo vertical.

Cuatro pruebas PostgreSQL correctas50,74s, sesión88545 terminal0: nueva prueba de publicación y tres de preferencias. Evidencia: [inicial](evidencias/publicacion-finalidad-inicial.json). Ruff, coherencia de migraciones y diff-check correctos. No prueba de navegador/carrera de publicación ni aceptación común; Docker principal sigue0072. Próximo levantamiento específico, calendario/inventario y variantes antes de exponer publication en UI.

Ampliación:11 pruebas correctas107,73s PostgreSQL (4 variantes restrict/cease y selección simple/mixta +7 regresiones cautelares). [Evidencia](evidencias/publicacion-finalidad-variantes.json). La primera invocación usó un nombre de archivo inexistente y terminó exit4 sin ejecutar pruebas; se corrigió el nombre tras confirmar estado terminal. Después se corrigió respuesta de GET del levantamiento genérico: captura ValidationError y devuelve409 privado, en lugar de error500. Nueva batería HTTP4 variantes en sesión35237 terminal0:4 correctas54,12s PostgreSQL; rechazo409/no-store y medida activa verificados. [Evidencia](evidencias/publicacion-finalidad-http.json).

## Consulta original para levantamiento específico

publication_purpose_release.inspect aplica locks de ámbito/medida, permisos release_purpose_restriction y respuesta, revisión independiente, asignación/lecturas/comprobación actuales. Registra RightsAction cifrada antes de descifrar la decisión publication del plan original; valida firma del plan y huella de revisión, ámbito y modo. Devuelve solo esa decisión y conserva la medida. No hay propuesta ni ejecución de levantamiento todavía, ni ruta nueva.

Pruebas: primer ensayo4 fallidas52,67s por permiso verify_rights_scope omitido en fixture; segundo4 fallidas54,17s por UUID de proof no serializable en auditoría cifrada. Permiso de fixture y conversión explícita a texto corregidos, sin reducir controles. Final4 correctas53,67s PostgreSQL, sesión22072 terminal0; [evidencia](evidencias/publicacion-finalidad-consulta.json). Se prueban reasignación y comprobación simulada nuevas, consulta/replay y persistencia de medida en cuatro variantes. Próximo propuesta específica con causa y nueva instrucción del sujeto para cease, recepción y ejecución atómica independiente.

## Propuesta específica parcial

Migración0074 añade ground, purpose_read y resume_message a PrivacyHoldReleaseProposal, compatibles con propuestas cautelares anteriores. publication_purpose_release.propose exige consulta auditada del mismo actor/versión/prueba/fuente/medida; restrict exige restriction_resolved y cease nueva instrucción posterior atribuible al sujeto o canal anónimo comprobado. Emite progreso minimizado dentro de transacción, conserva la medida y obliga a nueva comprobación. Reintento exacto devuelve propuesta original.

Cuatro pruebas PostgreSQL correctas57,34s, sesión56799 terminal0: propuesta restrict y replay en selección simple/mixta; cease sin nueva instrucción rechazado, medidas conservadas. [Evidencia](evidencias/publicacion-finalidad-propuesta.json). Ruff y coherencia de migraciones correctos. Falta camino cease válido, endurecimiento ante evidencia dañada, recepción y ejecución específica, calendario/inventarios/UI/Docker y aceptación conjunta. No aceptar levantamiento completo.

## Ejecución de levantamiento parcial

publication_purpose_release.execute comprueba firma de propuesta, actor independiente, actualidad/fuente, propuesta última, recepción por canal y nueva prueba posterior. Revalida decisión original y fundamento restrict/cease, libera solo el hold seleccionado, mantiene el anuncio pausado, limpia disponibilidad/versiona ciclo y deja el expediente reviewing/unverified. Reintento exacto no duplica acción.

Cuatro pruebas PostgreSQL correctas55,42s, sesión82181 terminal0. [Evidencia](evidencias/publicacion-finalidad-levantamiento.json). Camino restrict completo verificado en simple/mixta con rechazo previo a recepción, acuse público, nueva prueba simulada, ejecución/replay y preferencias conservadas. Las dos variantes cease solo verifican rechazo sin nueva instrucción: camino positivo pendiente. Pendientes además evidencia dañada/permisos tardíos/carreras/UI/calendario/inventarios/Docker y aceptación común.

## Oposición y consulta dañada

Camino cease con nueva instrucción anónima enviada por acuse público, nueva prueba simulada y consulta/propuesta/recepción/ejecución/replay comprobado en selección simple/mixta.4 pruebas PostgreSQL correctas57,14s (sesión33593 terminal0). La prueba por canal anónimo no demuestra identidad real; la comprobación sigue simulada. [Evidencia](evidencias/publicacion-finalidad-oposicion.json).

Se controla InvalidToken de la consulta cifrada antes de proponer. Nueva batería4 correctas57,60s (sesión26167 terminal0) incluye ciphertext deliberadamente dañado, rechazo ValidationError y ausencia de propuesta/liberación; después restaura fixture para completar flujo válido. [Evidencia](evidencias/publicacion-finalidad-robustez.json). No equivale a ensayo de corrupción operativa. Pendientes todavía permisos/fuente tardíos, carreras, interfaz/móvil, calendario/inventario y Docker/común.

## Fuente de inventario

El inventario de perfil incluye action/proof/ground/snapshot de sujeto/estado previo de PrivacyPublicationHold y purpose_read/ground/resume_message/source de su propuesta. El inventario de cuenta incluye publication_hold_id en ProcessingExecution existente. No aumenta el número de modelos seleccionados de cuenta ni descifra fundamentos.

Se comprueba cambio del ground de propuesta mediante mutación de fixture y restauración antes de continuar flujo válido: la fuente cambia y no entrega REASON.6 pruebas correctas74,08s PostgreSQL, sesión44989 terminal0 (4 variantes publication y2 regresiones dependencias de cuenta). [Evidencia](evidencias/publicacion-finalidad-inventario.json). No prueba todavía todos los campos individualmente ni inventario integral. Pendientes calendario/UI/carreras/sin cuenta/Docker y aceptación conjunta.

## Integridad adicional

La propuesta valida firma de RightsAction de lectura además de su snapshot cifrado. La decisión original exige outcome approved, actor de revisión distinto del preparador y source de revisión igual al plan.4 pruebas correctas60,99s PostgreSQL, sesión56145 terminal0, con firmas alteradas y aprobación cambiada a rejected inyectadas/restauradas en fixture y caminos válidos completos. [Evidencia](evidencias/publicacion-finalidad-integridad.json). No acredita carreras ni firma íntegra de aprobación/permisos tardíos del aprobador original. Próximo integración operativa/calendario/interfaz y pruebas de concurrencia; todavía pendiente ámbito sin cuenta y Docker0074.

## Firma completa de aprobación original

La consulta/decisión reconstruye la firma de revisión original con plan, versión, operación, motivo cifrado, outcome approved y huella del plan; exige operación processing_review y mismo expediente que la ejecución. Firma alterada en fixture restrict rechazada; se restaura para completar flujo válido.4 pruebas PostgreSQL correctas61,58s, sesión19477 terminal0. [Evidencia](evidencias/publicacion-finalidad-firma-aprobacion.json). No verifica aún cambios de permisos del aprobador durante espera ni carreras; calendario/UI/ámbito sin cuenta/Docker/regresión común siguen pendientes.

## Primera interfaz privada

Ruta publication_purpose_release con formulario ES/EN de consulta/propuesta/ejecución y referencias explícitas de lectura/propuesta/mensaje. GET solo formulario; POST inspect muestra decisión seleccionada en esa respuesta y reinicia formulario. Permisos/MFA/recusación y respuestas privadas existentes se conservan. No se ofrece aún publication en formulario de ejecución inicial ni enlaces operativos hasta calendario/aceptación.

4 pruebas PostgreSQL correctas61,90s, sesión64303 terminal0, cliente Django: GET sin fundamentos/no-store, POST inspect por interfaz, siguiente GET limpio, cuatro variantes backend. [Evidencia](evidencias/publicacion-finalidad-interfaz.json). Check Django/ruff correctos. No navegador móvil ni POST proposal/execute de interfaz ni CSRF específicos todavía; continuar esos controles y calendario/ámbito sin cuenta/carreras/Docker.

## Flujo HTTP completo

El formulario exige read_id para propose y proposal_id para execute, devuelve400 con referencia ausente.4 pruebas PostgreSQL correctas61,61s, sesión72717 terminal0: POST de propuesta y ejecución por interfaz, replay HTTP y backend, CSRF403 y entrada incompleta400 en cuatro variantes restrict/cease simple/mixta. [Evidencia](evidencias/publicacion-finalidad-interfaz-flujo.json). Se conserva acuse real local y prueba de identidad simulada. Esto es cliente Django, no navegador móvil ni revisión visual ESEN. Próximo calendario/integración de ejecución inicial, carreras/ámbito sin cuenta y Docker/regresión conjunta.

## Regresión dirigida conjunta

28 pruebas PostgreSQL correctas245,17s, sesión90363 terminal0: publication4, preferencias3, cautela7, levantamiento por finalidad12 y dependencias cuenta2. [Evidencia](evidencias/publicacion-finalidad-regresion.json). No es aceptación integral de CR09.

Fallo histórico CI65bc2d4 de recarga en test_browser_appeals corregido esperando contenido observable tras envío, conservando recarga/verificación de persistencia. Prueba local Chromium/PostgreSQL1 correcta31,63s, sesión24270 terminal0; [evidencia](evidencias/reclamacion-navegacion.json). No CI nueva verde ni prueba móvil de publication.

## Runtime Docker0074

Build app/worker/Beat terminal0 (34738); parada91700, migrate46596 y recreación94307 terminaron0. PostgreSQL local aplicó0073/0074. Check Django y migrate--check correctos;9 fuentes iguales host y tres servicios, UID10001 y health200. Proveedores de derechos/avisos/confirmación disabled comprobados. [Evidencia](evidencias/publicacion-finalidad-runtime.json). No acepta producción ni acredita proveedor real/ejecución de nuevas tareas; pendientes calendario/ámbito sin cuenta/carreras/móvil y aceptación común.

## Persona sin cuenta de sujeto

Dos pruebas PostgreSQL correctas43,16s, sesión28641 terminal0: restrict/cease reutilizan flujo HTTP completo con Person.subject null antes del enlace al expediente y de comprobar ámbito. Plan/revisión/ejecución y levantamiento conservan derechos sin cuenta; comprobación de identidad simulada. La desvinculación es preparación sintética de fixture, no baja real de cuenta. [Evidencia](evidencias/publicacion-finalidad-sin-cuenta.json). No selección mixta ni navegador; pendientes calendario/concurrencia/móvil/aceptación conjunta. Código funcional/runtime no cambiados.

## Fechas persistentes de revisión0075

PrivacyPublicationHold incorpora version1, purpose_review_on e initial_purpose_review_on. Nueva ejecución publication conserva fecha aprobada en ambas; source de propuesta e inventario incluyen campos. Cautelas existentes conservan null; no se inventa plazo ni se levanta por vencimiento. Falta cola/seguimiento auditado y tratamiento explícito de medidas publication anteriores sin fecha.

11 pruebas PostgreSQL correctas119,99s, sesión28230 terminal0:4 variantes publication con fecha/version y7 cautelares. [Evidencia](evidencias/publicacion-finalidad-fechas.json). Docker sigue0074;0075 solo probada en base de pruebas. Pendientes seguimiento/cola, invalidación por cambio de fecha probada aisladamente, móvil/carreras/aceptación conjunta.

## Seguimiento operativo auditado

publication_purpose_calendar.follow_up exige permiso review_purpose_calendar, ámbito/asignación/lecturas/prueba vigentes y versión de medida. Fecha futura dentro de90 días, inicial conocida; RightsAction guarda snapshot/motivo cifrado, incrementa versión y cambia solo fecha vigente. Reintento exacto único; ni desactiva medida ni cambia fecha inicial. Cola/UI e historial auditado paginado pendientes.

Primero1 fallo32,02s por operation superior a20 caracteres; corregido a pub_cal_follow. Final1 correcta33,79s PostgreSQL, sesión56931 terminal0: fecha14 días/version2/initial preservada/active/replay y flujo posterior restrict. [Evidencia](evidencias/publicacion-finalidad-seguimiento.json). Sin carreras ni invalidación de propuesta probada aisladamente; Docker sigue0074.

## Seguimiento desde interfaz

Formulario de publicación incorpora follow_up, versión de medida y fecha. Campos obligatorios según operación; POST invoca servicio auditado y refresca versión de formulario sin liberar medida. La pantalla sigue exigiendo permisos de levantamiento además del permiso de calendario para follow_up; acceso exclusivo de operadores de calendario pendiente.1 prueba PostgreSQL correcta33,32s, sesión73870 terminal0, cliente Django: POST seguimiento, fecha/version/initial/active/replay y flujo restrict posterior. [Evidencia](evidencias/publicacion-finalidad-seguimiento-http.json). Cola/historial/móvil/carreras/Docker0075 y común pendientes.

## Separación de permiso de calendario

Vista permite operador review_purpose_calendar sin release_purpose_restriction, conservando revisión/ejecución general/MFA/recusación de ámbito. Formulario solo muestra operaciones autorizadas; POST de levantamiento sin permiso403. Servicio mantiene autorización fresca y requisitos de ámbito/asignación/prueba.1 prueba PostgreSQL correcta32,97s, sesión64790 terminal0: retira permiso de levantamiento, GET solo follow_up, execute403, follow_up200, lo restaura para terminar flujo posterior. [Evidencia](evidencias/publicacion-finalidad-rol-calendario.json). Cola/historial/móvil/carreras/Docker y aceptación conjunta pendientes.

## Regresión y runtime calendario0075

14 pruebas PostgreSQL correctas145,77s, sesión61347 terminal0: calendario1/publication4/sin cuenta2/cautelas7. [Evidencia](evidencias/publicacion-calendario-regresion.json). Build99899 y parada/migrate/recreación65739 terminal0;0075 aplicada en PostgreSQL Docker. Check/migrate--check correctos,10 fuentes iguales host/app/worker/Beat, UID10001 y health200. [Runtime](evidencias/publicacion-calendario-runtime.json). Sin cola/historial/móvil/carreras ni aceptación integral de CR09.

## Referencia persistente de eventos0076

PublicationCalendarEvent enlaza hold/action protegidos, expected_version y created_at. follow_up crea evento en la misma transacción que acción y fecha; replay no duplica. No almacena motivo en claro ni necesita descifrarlo para filtrar eventos de medida.1 prueba PostgreSQL correcta34,55s, sesión99231 terminal0, evento único/version1 y flujo posterior. [Evidencia](evidencias/publicacion-calendario-eventos.json). Historial paginado/fuente/backfill de eventos previos pendientes; Docker0075,0076 solo pruebas.

## Consulta auditada del historial

publication_purpose_calendar.history filtra eventos por medida, página50 con cursor validado dentro de esa medida. Firma incorpora versiones/prueba/fuente cifrada de filas; RightsAction auditada antes de descifrar, resultado cifrado para replay. Revalida permisos al terminar; datos corruptos/conflictos rechazan y revierten auditoría.1 prueba PostgreSQL correcta34,96s, sesión8770 terminal0: lectura de1 evento/motivo/fecha/version y replay en flujo completo. [Evidencia](evidencias/publicacion-calendario-historia.json). Límite50+2/UI/cursor inválido/permisos tardíos/corrupción todavía no probados; no aceptar historial completo.

## Paginación completa de historia

52 seguimientos mediante servicio follow_up con datos sintéticos, acciones/eventos persistidos; no52 revisiones humanas reales. Versión53, inicial y active conservados. Lectura50+2 sin solapamiento/cursor final null, replay y cursor inválido sin nueva auditoría comprobados.1 prueba PostgreSQL correcta40,93s, sesión24708 terminal0. [Evidencia](evidencias/publicacion-calendario-historia-paginas.json). Código funcional sin cambios; UI/cola/móvil/carreras/backfill/fuente y Docker0076 pendientes.

## Historial conectado a interfaz

Operación history disponible con permiso de calendario, cursor validado y POST auditado. Plantilla muestra motivos/fechas solamente en respuesta POST; GET posterior limpio. Primer ensayo falló31,43s por expectativa anterior de choices, corregida. Final1 correcta40,38s PostgreSQL, sesión15555 terminal0,50+2 por cliente Django y flujo restrict completo. [Evidencia](evidencias/publicacion-calendario-historia-http.json). No móvil; cola/carreras/fuente/backfill/Docker0076 pendientes.

## Eventos en inventario

PublicationCalendarEvent incluido por hold.person en fuente de perfil y hold.person.subject en cuenta; pk/hold/action/version/created sin fundamentos ni resultados descifrados. Cuenta45 modelos seleccionados; no inventario integral.2 pruebas PostgreSQL correctas47,75s, sesión62145 terminal0: recuento52 eventos perfil sin REASON y regresión de cuenta/circularidad propias/ajenas. [Evidencia](evidencias/publicacion-calendario-inventario.json). No HMAC específico de ciphertext de motivo por evento todavía; cola/backfill/móvil/carreras/Docker0076 y aceptación conjunta pendientes.

## Integridad opaca de motivos de eventos

Fuentes de perfil/cuenta incluyen action.encrypted_reason y payload_digest de PublicationCalendarEvent dentro de HMAC; nunca los proyectan en resultado ni descifran. Prueba inyecta ciphertext dañado en evento, constata cambio de state_digest sin bytes en proyección y restaura fixture para terminar flujo válido.2 PostgreSQL correctas47,21s, sesión8679 terminal0. [Evidencia](evidencias/publicacion-calendario-fuente-cifrada.json). No incidente real ni inventario integral; cola/backfill/móvil/carreras/Docker0076/común pendientes.

## Firma de eventos al leer historia

La consulta reconstruye firma pub_cal_follow (hold/versión expediente/versión medida/motivo/fecha siguiente) y exige operación/expediente y scope/version consistentes antes de mostrar cada evento. Firma alterada en fixture rechazada y auditoría nueva revertida; se restaura para consultar50+2 y terminar flujo HTTP.1 PostgreSQL correcta40,77s, sesión40367 terminal0. [Evidencia](evidencias/publicacion-calendario-firma-evento.json). Cola/móvil/carreras/backfill/Docker0076 y común pendientes.

## Concurrencia de seguimiento

Dos conexiones PostgreSQL con pg_backend_pid distintos/barrera actualizan misma versión con claves distintas; una aplicada/otra ValidationError, versión incrementada una vez y un nuevo evento. Completa52 eventos/historial50+2/HTTP después.1 correcta40,47s, sesión98012 terminal0. [Evidencia](evidencias/publicacion-calendario-concurrencia.json). No bloqueo observado por pg_blocking_pids ni revocación intercalada; levantamiento concurrente/móvil/cola/backfill/Docker0076 y común pendientes.

## Primera cola operativa

Ruta publication_calendar_queue, filtros due/soon/all y modo; consulta acotada101 candidatos, autorización por expediente hasta100 y cursor cifrado ligado a usuario/session/MFA/filtros con1h, keyset fecha/pk. Solo fechas y enlaces, sin motivos ni totales de casos ajenos. Primer fallo32,73s por nombre de campo duplicado, corregido. Final1 PostgreSQL correcta40,98s, sesión10995 terminal0: cola all muestra medida propia autorizada sin razón y flujo completo posterior. [Evidencia](evidencias/publicacion-calendario-cola.json). Cursor/filtros/paginación100/recusación aún no probados; no aceptar cola completa.

## Filtros y errores de cola

1 PostgreSQL correcta38,87s, sesión23234 terminal0: due vacío/soon perfil propio/all/cease vacío, filtro inválido400, cursor dañado400/no-store, POST405, permiso calendario retirado403. Medida activa y fecha inicial sin cambio; después flujo completo52/historia/concurrencia. [Evidencia](evidencias/publicacion-calendario-cola-filtros.json). Cursor válido/paginación100/recusación/móvil/logs y backfill/Docker0076 pendientes.

## Logs y errores privados de cola

Se añade /moderation/publication-calendar/ al filtro de logs Django y a cabeceras del middleware para errores tempranos. Gunicorn ya redacta todas las rutas /moderation/.27 pruebas unitarias correctas0,24s, sesión52332 terminal0: filtros y302/400/403/404/405 privados/noindex. [Evidencia](evidencias/publicacion-calendario-logs.json). No tráfico operativo real ni SQL; Docker no actualizado con este cambio. Cursor válido/paginación/recusación/móvil/backfill y común pendientes.

## Cola100+1

Se añaden100 medidas/ejecuciones como fixture sintético a la medida real del flujo de prueba; no100 procedimientos revisados. Cola101 devuelve100+1 sin solapamiento y cursor finalnull; token con filtros distintos rechazado400. Se retiran clones antes de continuar flujo52/historia/concurrencia.1 PostgreSQL correcta50,68s, sesión94358 terminal0. [Evidencia](evidencias/publicacion-calendario-cola-paginas.json). Otros actores/session/MFA/caducidad del cursor/móvil/backfill/Docker0076 y común pendientes.

## Vínculo de cursor de cola

Otro actor autorizado accede a cola pero no reutiliza cursor ajeno400. Tokens recifrados en prueba con session/MFA distintos/caducidad pasada/pkbooleano rechazados400; pkbool endurecido explícitamente. No falsificación externa ni espera1h ni revocación real de MFA.1 PostgreSQL correcta52,14s, sesión46730 terminal0, conserva100+1 y flujo52/historia/concurrencia. [Evidencia](evidencias/publicacion-calendario-cursor-vinculo.json). Recusación/móvil/backfill/Docker0076 y común pendientes.

## Recusación del sujeto operador

Sujeto del perfil recibe permisos review/execute/calendar y estado MFA habilitado en fixture (no alta real). Cola all no entrega medidas propias y POST de historia403; controles conservados durante paginación100+1/cursor/historia52.1 PostgreSQL correcta51,41s, sesión81907 terminal0. [Evidencia](evidencias/publicacion-calendario-recusacion.json). No variante gestor/agencia histórica ni móvil; backfill/Docker0076 y común pendientes.


## Consulta móvil ES/EN

2 pruebas PostgreSQL/Chromium correctas50,35s, sesión73931 terminal0. Login/TOTP reales con secreto sintético, viewport390x844, cola→consulta auditada, recarga POST sin duplicar RightsAction, navegación GET posterior sin motivo y sin desbordamiento horizontal. La preparación reentrante, la confusión POST/GET y la consulta ORM dentro del bucle Playwright causaron fallos previos; corregidos en la prueba, sin desactivar protección async ni cambiar autenticación. Última reproducción previa:2 fallidas46,63s. [Evidencia](evidencias/publicacion-calendario-movil.json). Seguimiento/historia/levantamiento completos en móvil, backfill, Docker0076 y aceptación común pendientes; no cerrar CR09.


## Seguimiento e historial móviles ES/EN

Se añade confirmación accesible role=status tras guardar seguimiento; aclara que la restricción sigue activa.2 pruebas PostgreSQL/Chromium correctas54,65s, sesión59467 terminal0: login/TOTP, cola→seguimiento, POST repetido sin nueva acción, historial muestra motivo solo en consulta autorizada y GET posterior limpio, consulta de decisión/replay. Verificación posterior de medida activa/version2/fecha operativa14 días e inicial7 días conservada. Viewport390x844 sin desbordamiento en historia e inspección. [Evidencia](evidencias/publicacion-calendario-movil-seguimiento.json). No levantamiento completo en móvil ni identidad real; backfill/Docker0076/regresión conjunta y CR09 íntegro pendientes.


## Runtime Docker0076

Build88473/stop42216/migrate30686/recreate52305/check37567/probe70023 terminaron exit0. safety0076 aplicada;14 hashes host/app/worker/Beat iguales, UID10001, health200 por Caddy, check/migrate--check/makemigrations--check sin incidencias. Adaptadores safety_notice/account_correction/rights_verification disabled. [Evidencia](evidencias/publicacion-calendario-runtime-0076.json). Incluye cola/logs/confirmación móvil actuales. No backfill histórico ni aceptación global ni publicación; regresión conjunta y restantes requisitos pendientes.


## Actualización de medidas anteriores: requisitos pendientes

0075 añade fechas nulas y0076 crea eventos sin reconstruir históricos. La actualización no debe tratar ausencia de fecha como caducidad ni usar la fecha actual como decisión original. Recuperar initial_purpose_review_on exclusivamente de la decisión publication del plan original, validando ciphertext, firmas, aprobación independiente y ámbitos mediante el mismo criterio que decision(). Para purpose_review_on respetar el último seguimiento auténtico, cuando exista; reconstruir eventos solamente para acciones pub_cal_follow firmadas y coherentes con hold, expediente y previous_version. Comprobar secuencia de versiones/fechas, no crear acciones retrospectivas atribuidas a un operador. Toda inconsistencia debe abortar la actualización del ámbito sin escritura parcial ni revelar motivos en salida/logs. La actualización será idempotente, no modifica active/listing/estado/plazos del expediente y necesita evidencia PostgreSQL no vacía (fechas ausentes, seguimientos previos, repetición y corrupción). Implementación y ensayo pendientes; este apartado define aceptación, no acredita recuperación ejecutada.


## Regresión integrada actual

Sesión19696 terminal0:32 pruebas correctas309,51s, PostgreSQL/Chromium; XML contrastado32 testcase,0 fallos/errores/omisiones. Publication simple/mixta restrict/cease y sin cuenta, calendario/historia/paginación/cursor/conflictos/recusación, móvilESEN y regresiones processing_execution/privacy_release/purpose_release/inventario seleccionado. [Evidencia](evidencias/publicacion-finalidad-integrada.json). No suite completa del repositorio ni aceptación CR09; recuperación de históricos, levantamiento publication completo móvil, permisos intercalados y requisitos restantes pendientes. Código funcional estable durante ejecución; runtime0076 previamente contrastado.


## Recuperación histórica implementada, aceptación pendiente

publication_calendar_upgrade.restore_calendar(hold_id) es una operación de mantenimiento por medida, no una ruta web. Bloquea ámbito/medida/acciones, valida decisión original y secuencia firmada de pub_cal_follow, recupera fechas ausentes y eventos con created_at de la acción original. Rechaza discrepancias de versiones/fechas/eventos y revierte la transacción; no modifica active ni publicación ni estado/plazos del expediente. No crea acciones retrospectivas ni imprime motivos. Test PostgreSQL con flujo no vacío, ausencia de fechas/eventos, repetición y firma alterada en ejecución: sesión27951; recuperar hasta terminal. No runtime actualizado ni comando administrativo final todavía.


Recuperación27951 terminal0:1 prueba PostgreSQL correcta34,04s, sin fallos/errores/omisiones. Fechas ausentes recuperadas del plan firmado; dos eventos reconstruidos con timestamps originales; repetición sin cambios y firma alterada rechazada sin fechas ni eventos parciales. Medida activa/version3/fechas conservadas y flujo posterior completo. [Evidencia](evidencias/publicacion-calendario-recuperacion.json). No ensayo de migración entre esquemas ni comando administrativo/runtime final; CR09 abierto.


## Comando operativo de recuperación

Uso local: `uv run python manage.py restore_publication_calendar ID` valida una medida concreta y previsualiza recuperaciones dentro de una transacción revertida. `uv run python manage.py restore_publication_calendar ID --apply` conserva la recuperación validada. No requiere ni crea una identidad de moderador: es mantenimiento por administrador con acceso a la configuración y base del proyecto, no una operación HTTP. Salida JSON solo applied/dates_restored/events_restored; errores genéricos sin motivos/ciphertext. Repetir después de aplicar devuelve cero cambios. No ejecutar sobre todas las medidas indiscriminadamente; identificar el ID del ámbito a recuperar y revisar evidencia válida. Prueba ampliada2943 en ejecución sobre PostgreSQL no vacío: previsualización sin persistencia, aplicación, corrupción e ID ausente. Resultado terminal pendiente; Docker todavía sin este comando.


Comando2943 terminal0:1 PostgreSQL correcta34,65s, sin fallos/errores/omisiones. Preview no conserva fechas ni eventos, --apply recupera dos eventos con timestamps originales, repetición no cambia datos; ID inexistente y firma alterada producen CommandError genérico sin motivos. Flujo posterior completo conservado. [Evidencia](evidencias/publicacion-calendario-comando.json). Migración entre esquemas, Docker/común actualizados y demás requisitos pendientes.


## Ensayo entre esquemas en ejecución

Test ampliado91513 utiliza MigrationExecutor sobre la base PostgreSQL de pruebas no vacía. Primera transición0074→0076: medida/plan/aprobación existentes, esquema anterior sin fechas; recuperación toma fecha original firmada. Segunda0075→0076: dos seguimientos firmados existentes, versión3 y fechas conservadas en esquema anterior sin tabla de eventos; reconstrucción posterior de eventos. Se restaura0076 en finally para evitar contaminar otras pruebas si falla el ensayo. No usa base operativa ni datos reales. XML/tmp/publication-calendar-schema-upgrade.xml/log/tmp/publication-calendar-schema-upgrade.log; resultado terminal pendiente.


Ensayo91513 terminal0:1 PostgreSQL correcta37,04s. Ambas transiciones0074→0076 y0075→0076 ejecutadas con datos existentes y modelos históricos contrastados; medida activa conservada, fechas originales y dos acciones firmadas preservadas, eventos reconstruidos con timestamps originales. Preview/--apply/idempotencia/firma alterada y flujo posterior correctos. [Evidencia](evidencias/publicacion-calendario-migracion.json). Base de pruebas únicamente; Docker con servicio/comando nuevo y aceptación restante pendientes.


Controles tras ensayo: Ruff global correcto, makemigrations--check sin cambios y diff-check correcto. Format--check global detectó15 migraciones no normalizadas: se normalizaron solo0074/0075/0076 de esta entrega;12 migraciones históricas ajenas siguen pendientes de formato. CI exige Ruff lint/check/makemigrations/pytest, no format global. Normalización actual sin cambio semántico de operaciones; nueva imagen Docker debe incluirla junto a recuperación.


## Recuperación incluida en Docker

Build41028/recreate39092/check37323/probe61943 terminal0.21 hashes host/app/worker/Beat coinciden incluyendo recuperación, comando, paquetes y migraciones normalizadas;UID10001,health200,check/migrate--check correctos, adaptadores de entrega disabled. manage.py restore_publication_calendar --help disponible en app; no recuperación aplicada sobre base operativa. [Evidencia](evidencias/publicacion-calendario-recuperacion-runtime.json). Pruebas de recuperación sobre PostgreSQL de test registradas antes; resto CR09/móvil completo/autoridad intercalada/entrada inicial publication/aceptación pendientes.


## Navegación conectada en verificación

Enlace al calendario de publicación desde cola de derechos condicionado por permiso calendario; retorno a cola desde calendario y navegación detalle→calendario/consulta del expediente. View pasa can_calendar para no ofrecer retorno calendario a operadores sin ese permiso. Prueba móvil ES/EN ampliada37973 en ejecución desde cola de derechos, con filtro all y navegación de vuelta antes de seguimiento/historial/consulta. XML/tmp/publication-calendar-navigation.xml/log/tmp/publication-calendar-navigation.log. Recuperar misma sesión hasta terminal sin editar fuente ni reiniciar por observación. Docker todavía anterior a enlaces.


Navegación59846 terminal0:2 PostgreSQL/Chromium móviles ES/EN correctas56,07s. Derechos→enlace calendario→filtro all→detalle→retorno por enlace→filtro all→misma medida, seguido de seguimiento/historia/consulta/replays/GET limpio. Primera37973 terminal1:2 fallidas107,66s por esperar medida futura tras retorno al filtro due predeterminado; corregido el recorrido de prueba seleccionando all, sin cambiar filtro funcional. [Evidencia](evidencias/publicacion-calendario-navegacion.json). Docker aún anterior a enlaces; levantamiento completo móvil/autoridad intercalada/aceptación pendientes.


## Ejecución recibida móvil en prueba

Se distingue en pantalla propuesta registrada de levantamiento ejecutado (anuncio pausado). Test64908 móvil ES/EN con login/TOTP reales y datos sintéticos intercepta ejecución tras acuse y nueva prueba de ámbito del flujo común; navegador realiza POST con la misma clave de idempotencia y recarga, navegación GET sin motivo. Identidad y recepción preparadas por flujo HTTP sintético, no proveedores reales ni propuesta/acuse completos móviles todavía. XML/tmp/publication-release-mobile.xml/log/tmp/publication-release-mobile.log; recuperar sesión hasta terminal, fuente estable mientras corre.


Primera64908 terminal1:1 fallida/1 correcta52,49s; browser execute/replay visible, caso ES falló al leer response.context[proposal] del cliente externo que capturó contexto GET anidado con proposalNone. Prueba común ajustada para elegir último contexto de respuesta, sin alterar autorización ni ejecución de app. Nueva98050 activa: XML/tmp/publication-release-mobile-final.xml/log/tmp/publication-release-mobile-final.log; no aceptación hasta terminal.


98050 terminal1:2 fallidas49,93s; último contexto era widget sin proposal. Se reemplaza dependencia de señales de plantilla por mensaje de resultado en cuerpo HTTP y propuesta persistida/released_at/released_proof_id; conserva verificación de replay y estado privado. Nueva27548 activa con los mismos2 casos; recuperar hasta terminal, no editar código durante ejecución.


Ejecución27548 terminal0:2 PostgreSQL/Chromium móviles ES/EN correctas54,68s. restrict recibido/nueva comprobación sintética, login/TOTP reales, POST/replay/GET limpio/estado ejecutado, anuncio pausado y expediente abierto/no verificado. [Evidencia](evidencias/publicacion-levantamiento-movil.json). Propuesta/acuse aún preparados por cliente HTTP, no recorrido completo móvil; cease móvil/autoridad tardía/UI inicial/aceptación restantes pendientes. Contrato interno normalizado añadido en [contratos/09](contratos/09-publicacion-finalidad.md).


## Propuesta y acuse móviles en ejecución

37857:2 casos ES/EN en Chromium390x844. Casos previos inválidos conservan rechazo original; prevalidación de propuesta válida dentro de transacción revertida, luego creación real desde navegador con login/TOTP, POST y recarga idempotente. Acuse en contexto anónimo separado mediante enlace privado localizado. Prueba continúa con nueva comprobación sintética y ejecución del servicio por cliente HTTP. XML/tmp/publication-proposal-receipt-mobile.xml/log/tmp/publication-proposal-receipt-mobile.log; recuperar hasta terminal sin modificar fuente. No propuesta falsa aceptada por prevalidación ni identidad real acreditada. Propose_ui comprueba cuerpo HTTP/propuesta persistida para evitar contexto ambiguo de render anidado.


Propuesta/acuse37857 terminal0:2 correctas/2 no seleccionadas56,27s PostgreSQL/Chromium ES/EN. Propuesta válida creada por navegador y recarga conservada; acuse mediante enlace privado en contexto anónimo separado, nueva prueba de identidad sintética y posterior ejecución HTTP con anuncio pausado/expediente abierto. [Evidencia](evidencias/publicacion-propuesta-acuse-movil.json). Ejecución móvil cubierta por casos distintos27548; no afirmar mismo recorrido completo ni variante cease/nueva instrucción ni proveedor real. Contrato interno09 y restantes requisitos abiertos.


## Variante cease móvil en ejecución

Se parametrizan propuesta/acuse y ejecución móviles por restrict/cease, y el formulario del navegador aporta resume_message_id cuando existe nueva instrucción revisada. Batería69204 selecciona solo4 casos cease ES/EN; restrict ya dispone de evidencias previas, no se repite aquí. Mensaje inicial del sujeto y nueva prueba de identidad preparados mediante cliente HTTP sintético; propuesta/acuse y ejecución se prueban en recorridos separados. XML/tmp/publication-cease-mobile.xml/log/tmp/publication-cease-mobile.log. No aceptación hasta terminal; autoridad intercalada/unión de recorrido/UI inicial pendientes.


Cease69204 terminal1:2 correctas/2 fallidas/4 no seleccionadas74,09s. Ejecución pasó; propuesta/acuse no ejecutó preparación navegador porque la vista conservaba referencia importada de caso anterior. Se parchean explícitamente servicio y referencia de vista por caso (execute/propose), evitando contaminación entre pruebas y asegurando POST navegador real en cada variante. Nueva45870 activa con4 casos cease ES/EN; XML/tmp/publication-cease-mobile-final.xml/log/tmp/publication-cease-mobile-final.log; no aceptación hasta terminal.


Cease45870 terminal0:4 correctas/4 no seleccionadas90,23s PostgreSQL/Chromium ES/EN, referencias de vista parcheadas por caso. Propuesta y acuse anónimo por navegador, ejecución navegador en casos separados, referencia a nueva instrucción revisada, replay y privacidad conservados. [Evidencia](evidencias/publicacion-oposicion-movil.json). Mensaje/proof sintéticos HTTP; no proveedor real ni recorrido único. Nueva34220 activa: espera PostgreSQL sobre propuesta observada con pg_blocking_pids y permiso revocado; XML/tmp/publication-release-race.xml/log/tmp/publication-release-race.log. No aceptar carrera hasta terminal.


Carrera34220 terminal0:1 PostgreSQL correcta33,76s. Dos conexiones/espera real pg_blocking_pids sobre propuesta; permiso cacheado antes de espera y retirado antes de liberar bloqueo. Operación PermissionDenied, medida activa/propuesta sin released_at/recuento acciones intacto/clave rechazada ausente; permiso restaurado y flujo posterior válido completo. [Evidencia](evidencias/publicacion-levantamiento-revocacion.json). No mutaciones proof/sesión/fuente durante espera ni autoridad real. Sin cambios funcionales del servicio; variantes restantes/UI inicial/aceptación pendientes.


## Autoridad/fuente durante espera: variantes en ejecución

Prueba parametrizada amplía bloqueo observado sobre propuesta a proof.status failed, session_version incrementada y edit_version de revisión aprobada incrementada mientras la operación espera. Son mutaciones sintéticas de concurrencia, no decisiones humanas ni edición pública acreditada. Cada caso debe denegar sin nueva acción, conservar medida/propuesta/anuncio/versiones del expediente y restaurar fixture antes del flujo válido posterior. Selección68313 excluye caso permission previamente verificado; XML/tmp/publication-release-authority.xml/log/tmp/publication-release-authority.log. Recuperar hasta terminal sin editar fuente.


Autoridad68313 terminal0:3 correctas/1 no seleccionada56,08s PostgreSQL, esperas pg_blocking_pids observadas para proof/session/source. Denegación conserva medida/propuesta/acciones/anuncio lifecycle/expediente versión y scope; fixture restaurada y levantamiento válido posterior. [Evidencia](evidencias/publicacion-levantamiento-autoridad.json). Nueva35252 activa: formulario inicial ofrece publication en perfil, preferencias solo con cuenta identificada; pruebas HTTP restrict/cease simple/mixta/sin cuenta y regresión preferencias. XML/tmp/publication-initial-http.xml/log/tmp/publication-initial-http.log; no aceptar entrada hasta terminal.


Entrada inicial35252 terminal0:9 PostgreSQL correctas109,23s; selección publication en formulario/POST/replay,restrict/cease simple/mixta/sin cuenta y regresión preferencias, flujo posterior completo. [Evidencia](evidencias/publicacion-ejecucion-inicial-http.json). Nueva31916 activa2 móviles ES/EN: login/TOTP/checkbox publication/confirmación/POST/reload/GET limpio; XML/tmp/publication-initial-mobile.xml/log/tmp/publication-initial-mobile.log. Identidad sintética; no aceptar móvil hasta terminal, fuente estable.


Entrada móvil31916 terminal0:2 PostgreSQL/Chromium ES/EN correctas56,29s, login/TOTP/checkbox publication/confirmación/POST/reload/GET limpio/sin desbordamiento, flujo backend completo posterior. [Evidencia](evidencias/publicacion-ejecucion-inicial-movil.json). Restrict simple móvil, otras variantes HTTP; identidad sintética. Próximo regresión conjunta actual+Docker+revisión/commit/CI; no cerrar CR09 por esta vertical.


## Integración actual en ejecución

Controles9806 terminal0: Ruff global/check/makemigrations--check/diff-check correctos. Build10577 terminal0 crea imágenes actuales app/worker/Beat; no recreadas todavía para conservar entorno mientras prueba57769 está activa. Regresión57769: publication/sin-cuenta/calendario/móvil/upgrade/levantamiento/ejecución inicial/carreras/processing_execution/privacy_release/purpose_release/inventario/logs. XML/tmp/publication-current-common.xml/log/tmp/publication-current-common.log. Recuperar misma sesión hasta terminal, no editar fuente funcional ni reiniciar por timeout. Próximo runtime/revisión/commit/push/CI, resto contrato intacto.


## Hallazgo de revisión pendiente de reproducción

Las colas publication_calendar_queue y purpose_calendar_views.queue comprueban review_purpose_calendar con request.user al entrar; authorize por expediente reconsulta usuario pero solo exige permisos generales review/execute. Retirar exclusivamente permiso calendario entre entrada y autorización podría dejar visibles fechas/enlaces de la cola. Es una observación estática, no incidente ni reproducción acreditada. Reproducir retirada durante authorize, exigir autoridad calendario fresca antes de entregar resultados/cursor y comprobar403 privado sin medidas. No cambiar fuente mientras57769 esté activa; integrar corrección después del resultado terminal antes de aceptar entrega.


## Acotación del hallazgo de cola

Revisión adicional: purpose_calendar_views.queue llama purpose_calendar.permission por medida, y esa función sí exige review_purpose_calendar sobre usuario fresco. La nota estática anterior atribuía incorrectamente el mismo recorrido a ambas colas. El caso pendiente de reproducción se limita a publication_calendar_queue, que llama directamente authorize (solo permisos generales) y descarta usuario fresco. No modificar cola general por esa inferencia. Reproducir retirada después de la comprobación inicial y antes de autorización por expediente; exigir revalidación de permiso específico sin fechas/enlaces/cursor para actor revocado.57769 sigue activa, fuente sin cambios.


Regresión57769 terminal0:74 correctas545,87s, XML74 testcase/0 failure/error/skipped. Incluye27 unitarias de logs, no atribuir PostgreSQL operativo a esas unidades; integración PostgreSQL y navegador Chromium reales en sus casos. [Evidencia](evidencias/publicacion-regresion-actual.json). Reproducción68275 activa para permiso calendario retirado durante query; XML/tmp/publication-queue-revoke-before.xml/log/tmp/publication-queue-revoke-before.log. No aceptar entrega hasta resolver hallazgo.


Reproducción68275 terminal1:1 fallida33,96s, response200 tras retirar permiso calendario durante authorize; esperaba403 privado. Confirmado fallo local con datos sintéticos. Se usa usuario fresco devuelto por authorize para exigir review_purpose_calendar antes de añadir medida; falta permiso→403 privado sin resultados. Nueva88344 activa: reproducción+calendario amplio+móvil ES/EN; XML/tmp/publication-queue-revoke-final.xml/log/tmp/publication-queue-revoke-final.log. Regresión74 anterior a esta corrección; runtime debe reconstruirse.


## Entrega parcial local preparada

88344 terminal0:4 PostgreSQL/Chromium correctas100,09s, permiso revocado durante consulta→403 privado sin medidas/cursor y regresiones calendario/móvil. [Evidencia](evidencias/publicacion-cola-permiso-revocado.json). Controles39594 terminal0 Ruff/check/makemigrations/diff; build24605/recreate7105/check99010/probe58158 terminal0,24 hashes iguales/UID10001/health200/providersdisabled/migraciones coherentes/comando recuperación disponible. [Runtime](evidencias/publicacion-runtime-actual.json). Sin recuperación operativa ni publicación externa. Regresión74 previa a corrección+4 afectadas después, no sumar como única ejecución. Entrega lista para commit/push y CI íntegra; no aceptar CR09 completo. Preparación de propuesta/acuse y ejecución móviles probada en recorridos separados, identidad sintética; requisitos restantes del contrato siguen abiertos.
