# CR-09 — Denuncias, derechos y reclamación sin cuenta

Estado: CR-09 en curso; recepción/acuse web/consulta auditada implementados y verificados localmente, resto pendiente, conforme a contratos14/15/16. No acredita procedimiento operativo real ni revisión jurídica. CR-08 cerrado localmente en acta03. Nuevas reglas requieren servidor y navegador conjuntamente; no tratar esta entrega como pulido frontend.

## Entradas separadas

- Denuncia general sin registro: perfil/revisión o referencia, motivo y explicación, contacto privado opcional, declaración de buena fe. Prioridad explícita para menores, explotación y publicación sin consentimiento. No sustituir notificación formal por un formulario que omita sus requisitos: modalidad formal separada según contrato15 y revisión del texto aplicable.
- Reclamación de una persona representada sin cuenta: identificar perfil y problema, canal propio de respuesta, solicitud de retirada/revisión de representación. No exigir acceso a la agencia, crear cuenta de navegación ni pedir ayuda al gestor denunciado. Verificación proporcionada por canal propio y revisión humana; control de email/teléfono por sí solo no prueba titularidad de foto o identidad.
- Derechos sobre datos: solicitud de acceso/exportación, rectificación, retirada/supresión u otros derechos aplicables, con información suficiente y verificación proporcionada. Las decisiones jurídicas, excepciones y plazos quedan sujetos al procedimiento aprobado del operador. No afirmar borrado completo cuando solo se ha quitado exposición.

## Estados, seguimiento y protección

Caso nuevo → asignado/en revisión → espera de comprobación cuando proceda → resolución motivada; historia de cambios y vía de revisión separada. Acuse/seguimiento privado cuando hay canal de respuesta; para denuncia sin contacto ofrecer referencia privada limitada sin exponer denunciantes ni datos de otras cuentas. No historial público de denuncias.

Token de acceso/canal aleatorio, resumen mínimo, caducidad y secreto guardado como hash/HMAC; GET no consume ni ejecuta decisión. Respuestas private/no-store, sin indexación, referencia segura sin parámetros sensibles en logs. Límites por operación/contacto y fuente anonimizada conforme a contrato de acceso; protección de CSRF y texto escapado. Sin importaciones desde URL ni cargas de documentos/biometría. Una referencia de evidencia no equivale a una comprobación real.

Notificaciones simuladas explícitas en desarrollo; correo/alertas reales condicionados a proveedor y destinatarios operativos aprobados. No enviar datos de casos por integraciones externas durante desarrollo.

## Colas y responsables

Separar permisos de denuncias y derechos, MFA obligatorio, controles de conflicto de interés y asignación/resolución versionadas. Consultas a evidencia y decisiones atribuibles; identidad/contacto del solicitante nunca mostrados al anunciante denunciado. No usar staff genérico como autorización suficiente ni permitir al moderador resolver su propio conflicto.

Casos urgentes se priorizan y alertan al responsable; la observación de duplicados/bots no retrasa restricciones ante un indicio creíble. Una denuncia no produce suspensión automática indiscriminada: incorporar evaluación, motivo y evidencia mínima para restricción preventiva, con exposición pública y derivados retirados inmediatamente cuando se decide. Confirmación/levantamiento no republica por tarea antigua; revisión independiente para decisiones impugnadas.

## Acciones y exportación

Retirada/revocación se conectan con Person/gestor/revisión y ciclo de vida vigentes, invalidando formularios/tareas antiguos. No conceder titularidad a quien subió primero una foto. Exportación privada disponible únicamente tras comprobar alcance/identidad: no incluir otros modelos de agencia, denunciantes, comentarios internos, evidencias ajenas ni secretos/verificadores. Cuenta autenticada no implica derecho sobre todo un perfil de agencia. Preparar respuesta estructurada y descarga autorizada con caducidad, sin rutas de archivos públicos.

Supresión/retención requiere inventario de dependencias y motivo/plazo de conservación: fotos/huellas, autorizaciones, decisiones, eventos, favoritos, pedidos futuros y backups. Implementar ejecución/reconciliación local verificable y reflejar limitaciones externas; no resolver una solicitud con una casilla ni presentar borrado ficticio. Retenciones jurídicas definitivas son dependencia externa de producción.

## Aceptación pendiente

Formulario público ES/EN y móvil, sin cuenta; recepción en cola/acuse/estado privado; abuso/errores/CSRF/HTML/IDs ajenos y no enumeración. Reclamación de representado sin cuenta con agencia independiente y gestor afectado sin datos del solicitante. Comprobación insuficiente no permite exportación o apropiación; prueba suficiente autoriza solamente alcance propio. Restricción urgente/revocación quita ficha/fotos/búsqueda y bloquea acciones obsoletas. Concurrencia/idempotencia/versiones, revisor independiente, exportación minimizada y retirada/supresión local con historial de conservación. Documentar rutas/modelos/adaptadores definitivos al implementar y distinguir simuladores de proveedores reales.


## Revisión de fuentes primarias para implementación

Revisado el 2026-10-03 antes de implementar. La calificación del servicio y sus posibles exenciones siguen pendientes de revisión del operador/asesoría; preparar mecanismos no acredita cumplimiento completo.

Notificación formal: explicación fundamentada, localización exacta, nombre y email, y declaración de buena fe. La excepción a nombre/email se refiere a los delitos indicados en los artículos3–7 de la Directiva2011/93/UE; no equivale a que cualquier reporte de un menor esté automáticamente exento. El art16 también prevé acuse cuando hay contacto y comunicación de decisión/recurso. Fuente: [DSA, art16, BOE](https://www.boe.es/buscar/doc.php?id=DOUE-L-2022-81573).

Consecuencia técnica: la denuncia general puede ser anónima; la modalidad formal conserva sus elementos y permite declarar la excepción pertinente sin pedir detalles gráficos o archivos. La comprobación de email para consultar información privada no debe bloquear recepción/tramitación de una notificación válida ni confundirse con comprobación de hechos. Canal urgente siempre disponible aunque falten elementos de la modalidad formal.

Derechos: art12 RGPD establece respuesta en un mes desde recepción y, cuando proceda, extensión motivada de hasta dos meses más comunicada dentro del primero; art15.4 protege derechos de terceros en la copia. Fuente: [RGPD arts12/15, BOE](https://www.boe.es/buscar/doc.php?id=DOUE-L-2016-80807). Diseñar vencimiento por mes natural, no treinta días fijos; petición de aclaraciones no reinicia el reloj automáticamente. Prórroga exige motivo/evento/aviso, no cambio silencioso de estado. Procedimiento definitivo sujeto a revisión jurídica.

La identidad se comprobará de forma proporcionada; no se exige copia de DNI por defecto. Información adicional solo cuando sea necesaria ante dudas razonables, sin habilitar subidas de documentos por este diseño. Fuente: [AEPD, identificación al ejercer derechos](https://www.aepd.es/preguntas-frecuentes/1-tus-derechos/3-identificacion-con-dni/FAQ-0108-para-el-ejercicio-de-estos-derechos-es-necesario-facilitar-la-copia-del-dni). OTP acredita control del canal, no identidad ni titularidad por sí solo.


## Recepción pública implementada, ampliación parcial

Nueva app safety y migración0001. GET/POST /safety/report/ sin registro ni aceptación de contrato de cuenta; disponible también si una sesión existente tiene email sin confirmar o aceptación antigua. Formulario key(UUID)/receipt_secret(43 caracteres aleatorios URLsafe)/target firmado(opcional)/mode general-formal/reason/reference/explanation20–4000/name120/email/exception/good_faith. Formal requiere nombre/email salvo excepción declarada; siempre referencia exacta y buena fe. La declaración no acredita hechos ni decide automáticamente aplicabilidad de la excepción.

Ficha enlaza target firmado de Listing/revisión exacta con vigencia2h y referencia pública, sin consulta a URLs externas. Formulario genérico sirve para una referencia sin confirmar existencia de un perfil privado. POST válido302 a acuse privado; error400, repetición incompatible409, límite20 intentos/15min por fuente HMAC429. Reintento exacto conserva un solo Report/acuse; concurrencia PostgreSQL verificada.

Report conserva metadatos mínimos/actor opcional/referencia interna; nombre/email/explicación/referencia/declaraciones quedan en encrypted_payload Fernet con SAFETY_ENCRYPTION_KEY dedicada obligatoria en producción. Desarrollo deriva clave con propósito separado; no evidencia de claves/proveedores reales. receipt_digest HMAC y payload_digest evitan guardar secreto de seguimiento en claro y detectan replay incompatible. Rotación/restauración de claves y retención siguen B-B.

GET /safety/receipt/{UUID}/{secret}/ válido30d solo muestra recepción/fecha/estado; enlace inválido/caducado404, ningún nombre/email/texto de denuncia. No ejecuta decisión ni verifica identidad. private/no-store, noindex/nofollow y Referrer-Policy same-origin; logs Gunicorn, django.request y django.server ocultan ruta/secreto de safety. Variables/POST sensibles se ocultan al reportero de errores.

GET /moderation/reports/ exige review_report/MFA; cola ordenada priorizando menores/explotación/no consentimiento, excluye autor y conflicto con perfil/gestor. La ampliación inicial solo entregaba metadatos; la consulta de evidencia se incorpora en el apartado siguiente. Decisión y alerta real siguen pendientes. Acuse web implementado; entrega de notificaciones, triage, asignación, resoluciones/restricción/reclamación, derechos/exportación/supresión y revisión sin cuenta todavía pendientes. No interpretar esta ampliación como mecanismo DSA/RGPD completo.

Pruebas: cuatro iniciales servidor/concurrencia/Chromium sin cuenta passed25.33s; once conjuntas report/logs passed23.29s; diez finales caducidad/clave/privacidad de logs passed9.17s. Ruff/format/check/migraciones/diff-check limpios. Datos sintéticos; sin comunicaciones externas.

## Consulta privada auditada, ampliación parcial CR-09

GET/POST `/moderation/reports/{UUID}/` exige permiso `safety.review_report`, MFA habilitado y versión vigente en sesión; un rol o un botón visible no concede acceso. GET solo entrega metadatos y formulario. POST requiere `purpose` de10–200 caracteres; registra ReportAccess (responsable, caso, motivo y fecha) en la misma transacción que descifra los datos. La respuesta privada muestra referencia, explicación, nombre/contacto y excepción declarada; una visita GET posterior vuelve a ocultarlos. Entrada inválida400, falta de permiso o conflicto403; middleware redirige302 a alta/desafío MFA cuando falta verificación vigente, y la vista vuelve a exigirla; cambio de agencia entre comprobación inicial y bloqueo409; caso inexistente404. No cambia estado ni decide hechos.

Report conserva agencia/gestor particular de la aceptación de publicación, sujeto de la verificación aprobada de esa versión y manager_version. Son referencias internas, no parte del token público firmado. El autor registrado, sujeto y gestor originales no pueden consultar; tampoco miembros de la agencia original aunque estén revocados, ni responsables actuales del perfil. La agencia original y el perfil se bloquean antes de revalidar acceso; bloqueo del caso usa `FOR UPDATE OF safety_report` para no bloquear lados opcionales de joins PostgreSQL. La agencia que cambia antes del bloqueo del perfil exige recarga. Datos históricos enlazados sin snapshot confiable quedan excluidos de consulta ordinaria; no se reconstruye su gestor con información actual.

Migración0002 y ReportAccess implementados. Auditoría con FK protegidas: no se ha definido todavía el procedimiento final de conservación, seudonimización y borrado; estos requisitos siguen en derechos/B-B. La identificación automática de conflictos se limita a las relaciones conocidas: una referencia escrita manualmente no identifica un perfil, y un email anónimo no acredita identidad. Triage debe enlazar/verificar referencia y gestionar recusación antes de resolver; pendiente, no presentar este acceso como resolución completa del riesgo.

Cabeceras private/no-store, noindex/nofollow y referrer same-origin también en consulta. Logs Django request/devServer ocultan identificadores de `/moderation/reports/`; Gunicorn ya oculta `/moderation/`. Motivo y variables sensibles se excluyen del reportero de errores. No enviar datos a proveedores ni mostrar expediente al denunciado o al público.

Pruebas previas de esta ampliación: la primera batería detectó `FOR UPDATE` inválido sobre joins opcionales (2 fallos,7 correctas); corregido y repetido:9 pruebas PostgreSQL/Chromium pasan42.47s. La siguiente ampliación pasa13 pruebas en23.70s, incluida intercalación controlada de cambio de gestor entre comprobación y bloqueo, consulta móvil auditada y logs. Esa intercalación reproduce una transición en PostgreSQL; no se declara ensayo de carga o carrera multiusuario completa. Regresión final de permisos/MFA/logs y cierre de evidencia registrados en docs/18. CR-09 continúa: triage/decisiones/avisos/revisión y derechos sin cuenta/exportación/supresión pendientes; Docker sigue con CR-08.

Verificación final de consulta:18 pruebas pasan36.45s sin skips (permisos, MFA, historial de conflictos, cambio intercalado, Chromium móvil, logs). Las dos expectativas iniciales de MFA se corrigieron a302 a alta/desafío, conforme al middleware vigente; no se debilitó autorización. No es la regresión común completa de CR-09.

## Asignación y restricción persistente — verificación local parcial

Migración0003 añade versión/asignación de Report, acciones idempotentes y Restriction. Ruta GET/POST `/moderation/reports/{UUID}/decision/`: permiso específico/MFA/COI, key UUID, versión del caso, operación claim/restrict/dismiss y motivo privado20–2000. Restricción liga además manager_version y revisión aprobada actuales. GET no decide ni revela denunciante. POST válido302, entrada400, conflicto/versiones/reintento incompatible409, permisos403 (o302 a MFA por middleware). Motivo cifrado con clave safety; no se copia al estado público/acuse ni al anunciante.

Claim: received→reviewing, asignado al moderador y versión incrementada. Restrict/dismiss: solo responsable asignado, caso reviewing y consulta de evidencia auditada por ese responsable. Restrict exige perfil identificado, revisión aprobada actual y gestor vigente; no se aplica una referencia genérica directamente a un perfil. Dismiss no borra expediente ni libera restricciones procedentes de otras denuncias. Reintento exacto conserva acción/versión y no repite efectos; key global reutilizada con otro payload/caso/actor es conflicto. Agencia(s)→Person→Listing→Report serializa decisión con transferencia/publicación; cambio previo de agencia requiere recarga.

Restrict crea una restricción independiente ligada a la publicación, versión y acción; pausa si estaba publicada, limpia disponible y aumenta versión de ciclo de vida. Validación central de publicación comprueba restricciones activas: ficha/fotos/búsqueda y aprobación/reanudación/renovación/disponibilidad quedan bloqueadas. Cambiar simplemente status a published no evita este filtro. La cuenta no se suspende automáticamente y la restricción no identifica por sí misma quién es titular de imágenes.

Esta ampliación no incluye todavía enlace de referencias manuales, reasignación, espera de comprobaciones, avisos, historia legible con consulta auditada ni reclamación/revisor independiente/levantamiento. Solo las operaciones de revisión independiente descritas más adelante pueden resolver una restricción; no existe levantamiento automático por tarea ni por devolución a cola. No se considera CR-09 cerrado. Retención definitiva y operación real siguen pendientes; las pruebas de esta ampliación se registran en docs/18 al obtener resultado terminal.

Pruebas de esta ampliación:24 conjuntas con denuncias/ciclo de vida passed105.49s;13 finales de decisiones/consulta passed65.29s con Chromium móvil y carreras PostgreSQL; límite foto/búsqueda con estado publicado forzado passed10.47s. Revisión actual visible en pantalla de decisión. No sustituye la regresión común completa ni aceptación de CR-09.

## Triage: enlace de referencia manual — verificación local parcial

La misma ruta de decisión admite operación `link` y campo opcional `link_listing_id` (UUID del anuncio). No consulta ni descarga URLs: el responsable compara la referencia original y justifica manualmente el enlace mediante motivo privado. Requiere caso reviewing asignado a ese responsable, versión vigente y consulta auditada previa. Solo enlaza un caso todavía sin perfil, contra una revisión aprobada existente; un anuncio sin revisión publicada no es un destino válido. Guardar un enlace no prueba hechos, identidad ni consentimiento, no restringe y no cambia la carga cifrada original de la denuncia.

Agencia actual y agencia de la aceptación histórica→Person→Listing→Report se bloquean antes del enlace. Se toman revisión/gestor/agencia/particular/sujeto del destino y se vuelve a comprobar COI antes de persistir. Un responsable actual, sujeto o miembro incluso revocado de la agencia original recibe403; toda la asociación y su acción se revierten. Casos ya enlazados no se cambian silenciosamente a otro perfil. Versión obsoleta, destino inexistente/no aprobado o enlace previo409; formato400. Reintento exacto conserva una acción; concurrencia no sobrescribe el enlace ganador.

ReportAction conserva operación/motivo cifrado/huella del payload (incluido destino únicamente para link, manteniendo semántica de reintentos previos de claim/restrict/dismiss). No hace falta nueva migración. Pantalla de decisiones permite introducir ID del destino; después del enlace muestra revisión/gestor actuales para continuar evaluación. Restricción sigue siendo una operación independiente con su propio head/versión, no efecto automático de link.

La recusación de identidad anónima no demostrada y el procedimiento humano de corrección/reasignación/revisión siguen pendientes. Un enlace motivado por moderador no convierte una referencia en prueba externa ni acredita titularidad. Resultados terminales de servidor/concurrencia/Chromium se registran en docs/18; no cierre CR-09.

Verificación terminal:9 iniciales passed43.06s y11 finales passed54.00s, PostgreSQL/Chromium sin skips. Incluye dos enlaces concurrentes a destinos distintos (una asociación/acción) y editor original revocado tras traslado (403/sin enlace). No regresión común completa ni aceptación final de CR-09.

## Recuperación de asignaciones — verificación local parcial

Operación `unassign` en la pantalla de decisión: exige los permisos `safety.review_report` y `safety.manage_report_assignment`, además de MFA vigente y ausencia de COI. Migración0004 declara el permiso de coordinación; no se concede por rol staff ni automáticamente a todos los moderadores. Devuelve únicamente un caso reviewing con responsable a received/sin asignación. Requiere key/version/motivo cifrado; registra acción y aumenta versión. No necesita leer identidad/evidencia para recuperar una asignación administrativa, y no entrega esos datos en la respuesta.

Un coordinador independiente puede recuperar el caso cuando el responsable original pierde permiso, MFA o resulta implicado; después otro moderador autorizado lo acepta con claim. Autor/sujeto/gestor relacionado tampoco pueden coordinar su propio caso. Casos dismissed/restricted y casos sin asignación no se reabren por unassign. Ninguna restricción se libera mediante esta operación. Reintento de la misma devolución después de una nueva asignación no vuelve a quitarla; se conserva el efecto original.

La versión y bloqueo transaccional compartidos serializan devolución frente a una resolución: solo una operación del mismo estado gana. Historial y restricciones permanecen. No sustituye reclamación, revisión independiente o levantamiento; reasignación es organización del trabajo. Verificación terminal de móvil/permisos/reintentos/concurrencia en docs/18; CR-09 sigue abierto.

Verificación terminal de recuperación:8 iniciales passed42.26s y10 finales passed54.12s sin skips. Chromium móvil incluye devolución/reclaim; concurrencia real PostgreSQL frente a restricción. Evidencia local, no procedimiento humano operativo ni regresión común completa.

## Historial privado de acciones — verificación local parcial

La consulta POST auditada del expediente muestra acciones atribuidas (ID interno del responsable, fecha, operación, versión anterior y motivo descifrado). GET no entrega motivos/historial; tampoco acuse del denunciante ni público. Comparte permission/MFA/COI, bloqueo y registro ReportAccess con la consulta de evidencia. Texto escapado, cabeceras privadas/no-store/noindex; no se incluyen emails, credenciales o enlaces a cuentas de otros moderadores.

Cada consulta entrega hasta50 acciones, más recientes primero por PK estable, con `action_before` opcional (entero positivo hasta bigint). Si hay más, botón «Registrar consulta y ver acciones anteriores» envía otra consulta con motivo/cursor y deja otra auditoría. Cursor siempre filtra dentro del mismo Report: no sirve para leer acciones de otro caso. GET posterior oculta todo y reinicia consulta. Un cursor permite seguir hacia atrás sin duplicación ante nuevas acciones posteriores; para ver acciones nuevas volver a consultar desde el inicio.

No es un recorte definitivo de historia: anteriores siguen accesibles mediante cursor. El ID y motivo internos no forman parte de la respuesta al anunciante/notificante. Retención y seudonimización siguen pendientes; atribución no justifica conservar indefinidamente. No añade migración ni notificaciones/revisión externa. Verificación de escape/privacidad, más de50 acciones reales de asignación/devolución y navegador móvil en docs/18.

Verificación terminal de historia:9 conjuntas con consulta passed42.76s y3 finales passed22.05s sin skips. Navegador móvil recorre50+2 acciones y comprueba ocultación por GET; preparación usa52 operaciones reales de asignación/devolución, no eventos simulados como prueba de ejecución. No regresión común completa CR-09.

## Revisión independiente interna de restricciones — verificación local parcial

Migración0005 declara permiso `safety.review_restriction` y guarda Restriction.review_action/reviewed_at. Operaciones `uphold` y `lift` en ruta de decisión: ambos requieren review_report/review_restriction, MFA y COI, versión del caso y revisión/gestor actuales, motivo privado y una consulta auditada posterior a la restricción o a su última revisión. El autor de la restricción y el último revisor no pueden decidir la siguiente revisión. Reintento exacto no ejecuta otra revisión ni altera su fecha.

Solo casos restricted/upheld con restricción activa admiten revisión. Uphold mantiene activa y estado upheld; lift desactiva solo esa restricción y cambia estado a lifted. La acción nueva y la restricción/caso se guardan en transacción con locks de agencia/perfil/anuncio/caso/restricción. Acciones históricas permanecen aunque review_action señale la revisión más reciente. Ambas operaciones invalidan formularios viejos de ciclo de vida y limpian disponibilidad; no cambian automáticamente el anuncio a published. La reanudación posterior del gestor exige validador completo, otras restricciones/coincidencias/respuesta de verificación/consentimiento/fecha vigentes.

Cola de moderación muestra restricted/upheld únicamente a quienes tienen permiso de revisión independiente, además de received/reviewing. El formulario sigue enlazado a la consulta auditada. Falta de permiso o revisor implicado403; consulta insuficiente/estado o snapshot obsoleto409. El levantamiento de un caso no levanta otra restricción sobre el mismo anuncio y no concede identidad/titularidad de fotos.

Esta es revisión interna de moderación, no la vía completa de reclamación del denunciante/anunciante/persona sin cuenta. Solicitud pública, avisos/motivos minimizados y seguimiento de recurso siguen pendientes. No acredita procedimiento jurídico ni operación humana real. Verificación terminal de servidor/móvil/otras restricciones en docs/18; no cierre de CR-09.

Verificación terminal de revisión interna:9 iniciales passed48.17s y9 conjuntas con asignación passed49.93s; límites concurrentes11.04s y permiso insuficiente10.31s. Móvil con otro usuario/MFA verifica lift y ficha404 sin republicación; otra restricción conserva bloqueo. No regresión común completa CR-09 ni vía pública de reclamación.
