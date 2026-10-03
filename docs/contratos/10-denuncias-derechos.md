# CR-09 — Denuncias, derechos y reclamación sin cuenta

Estado: diseño interno pendiente de implementación y verificación, conforme a contratos14/15/16. No acredita procedimiento operativo real ni revisión jurídica. CR-08 debe cerrar antes de conectar este flujo. Nuevas reglas requieren servidor y navegador conjuntamente; no tratar esta entrega como pulido frontend.

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
