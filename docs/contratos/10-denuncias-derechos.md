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
