# Comunicaciones de derechos ejecutados

Fecha: 2026-10-06. Desarrollo local, CR09 abierto. Estado y próximo paso únicos en [seguimiento17](17-seguimiento-desarrollo.md).

## Evaluación y revisión

`apps/safety/rights_communications.py` reutiliza el ledger cifrado RightsAction y los validadores de destinatarios. Admite supresión, limitación y oposición conservando el tipo de derecho. La fuente se vincula al expediente, sujeto, ejecución más reciente, efectos actuales y canal; una ejecución registrada no prueba entrega a terceros.

Para perfiles, candidatos de representación, publicaciones y accesos históricos del propio sujeto. Para cuentas, accesos de expedientes de esa cuenta; ser propietario de una agencia no autoriza incluir a sus modelos. Los accesos del expediente actual no se incorporan recursivamente: permanecen como laguna explícita. El corte de accesos históricos es la ejecución; cambios posteriores requieren evaluación operacional y no quedan acreditados por este inventario.

Cada candidato y cada laguna necesita resultado, motivo y evidencia. El historial de un rol no demuestra divulgación. «Comunicado» exige acuse registrado del destinatario aplicable a esta fuente. La fuente incorpora las notificaciones de esa ejecución y verifica su contenido, acción de entrega y acuse firmado. Crear una notificación sin acuse no permite marcar «comunicado». No reutilizar acuses de rectificación como prueba de entrega de otro derecho.

La persona asignada consulta primero el inventario con auditoría previa al descifrado; la propuesta exige una consulta de esa misma fuente, ejecución, canal, versiones y sesión/MFA. La pantalla privada reutiliza formularios por destinatario/laguna y no abre contenido en GET. La persona asignada propone; otro operador con permisos vigentes consulta y revisa. La auditoría se registra antes de descifrar la propuesta. Se comprueban la fuente vigente, versiones del expediente/respuestas, canal, integridad, sesión y MFA del autor y del lector. Las claves permiten replay idéntico y rechazan cuerpos distintos. La retirada de permisos se comprueba contra la base de datos, aunque el objeto recibido tenga permisos cacheados.

Una revisión favorable puede confirmar que quedan tareas pendientes; no acredita comunicación completa, no cierra el derecho y no incrementa la versión del expediente. Los registros de evaluación/revisión no son borradores finales: la purga0109 no acredita su conservación jurídica integral.

## Notificaciones y respuesta final

RightsRecipientNotice (migración0110) conserva una notificación mínima cifrada por expediente, ejecución, cuenta y versión de autorización. La evaluación propone el contenido exacto y los destinatarios actuales; ambos se muestran en la consulta independiente. Solo una evaluación aprobada y vigente permite crear las notificaciones. Los replays pueden observar sus acuses posteriores, pero siguen comprobando integridad, autoridad, fuente y ejecución; no generan duplicados.

Para perfiles, el destinatario es el particular actual o el propietario de agencia y su editor asignado activo. Para cuentas, solo la propia cuenta activa no anonimizada. No se convierte un rol histórico en autorización para enviar. Un perfil con publicación eliminada conserva únicamente este aviso mínimo de la ejecución a su gestor actual; no se restituyen contenido público ni datos borrados. Si no quedan destinatarios autorizados, la entrega sigue pendiente.

El buzón muestra metadatos en GET. El contenido requiere un POST auditado y MFA vigente. La consulta y el acuse vuelven a bloquear el ámbito y comprueban destinatario/rol actual y versiones de sesión/MFA. La auditoría del acuse contiene hora, contenido, consulta y cuenta; el inventario rechaza alteraciones, incluida una modificación aislada de la hora. Un acuse no certifica la ejecución legal ni elimina las lagunas operacionales.

El borrador final incluye la fuente y evaluación revisada con su integridad, estado y recuentos. Cambios de destinatarios, entrega, acuse o evaluación invalidan el borrador anterior. Después de entregar/recibir se vuelve a evaluar la nueva fuente antes de emitir una respuesta apoyada en esa evaluación. El solicitante solo recibe estado y recuentos; no identidades, referencias privadas ni motivos de terceros. Las lagunas no resueltas mantienen la respuesta parcial y el expediente abierto.

Esta entrega interna usa PostgreSQL y el buzón de la propia aplicación. No acredita transporte externo ni identidad real. Los avisos y auditorías se preservan como evidencia; conservación/destrucción integral por finalidad continúa pendiente y la purga0109 no los cubre.

## Trabajo todavía necesario

- Gestionar destinatarios históricos sin canal autorizado y destinos/encargados externos.
- Registro de procesadores/destinos externos y demostración de entregas/fallos cuando exista transporte autorizado. No enviar mensajes externos ni contratar proveedores en esta fase.
- Pruebas de aislamiento entre sujetos, variantes de agencias, concurrencia y variantes operacionales antes de aceptar íntegramente el requisito. El alcance local0110 está verificado en PostgreSQL/HTTP/móvil y Docker.

## Verificación local

`tests/test_rights_communications.py` ejecuta operaciones de supresión/limitación/oposición reales sobre PostgreSQL con identidades sintéticas. Verifica propuesta/replay, independencia, consulta auditada antes de descifrado, revisión/replay, rechazo de permisos retirados, consulta previa del autor y preservación del expediente abierto. El recorrido HTTP incluye GET sin contenido privado, CSRF, consulta de inventario, propuesta estructurada, consulta independiente y revisión. El recorrido ampliado cubre entrega interna revisada, consulta/acuses, replay, alteración de evidencias, invalidación de borrador anterior, reevaluación y emisión privada parcial. No verifica identidad externa ni entrega fuera del buzón de la aplicación. Los resultados terminales y el alcance exacto se registran en el seguimiento/historial.


Evidencias de entrega0110: [baterías](evidencias/comunicaciones-derechos-integradas0110.json), [runtime](evidencias/comunicaciones-derechos-runtime0110.json). Fuente637e456; no reabrir el recorrido interno verificado salvo defecto/requisito concreto.


## Integración en inventarios de conservación y acceso

RightsRecipientNotice se incorpora como dependent_evidence a los inventarios de perfil y cuenta. La cuenta recoge avisos de sus expedientes y avisos recibidos por ella; un aviso sobre un modelo recibido por un propietario es evidencia de esa recepción, no autoridad sobre el modelo ni acceso automático a su contenido. El perfil recoge únicamente avisos de expedientes vinculados a esa persona. No se recorre la colección de modelos de una agencia.

La fuente de cuenta contiene75 modelos seleccionados tras esta ampliación. Metadatos de envío/acuse y ciphertext se incorporan a huellas de estado sin descifrarlos ni devolverlos en el manifiesto. Cambios propios alteran la fuente; cambios de avisos ajenos no. Los procedimientos erase/restriction/object excluyen avisos del propio expediente, como evidencia actual pendiente de contabilización aparte; el censo de acceso excluye siempre los registros del expediente actual mediante sus rutas FK. No declarar completo el derecho por esta exclusión.

[Verificación](evidencias/censo-avisos-derechos0110.json):3 pruebas de ámbito/opacidad/dependencias y7 de integración con acceso/comunicaciones. No migración, tarea, política jurídica o autorización de destrucción nuevas.
