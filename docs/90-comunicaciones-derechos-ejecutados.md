# Comunicaciones de derechos ejecutados

Fecha: 2026-10-06. Desarrollo local, CR09 abierto. Estado y próximo paso únicos en [seguimiento17](17-seguimiento-desarrollo.md).

## Evaluación y revisión

`apps/safety/rights_communications.py` reutiliza el ledger cifrado RightsAction y los validadores de destinatarios. Admite supresión, limitación y oposición conservando el tipo de derecho. La fuente se vincula al expediente, sujeto, ejecución más reciente, efectos actuales y canal; una ejecución registrada no prueba entrega a terceros.

Para perfiles, candidatos de representación, publicaciones y accesos históricos del propio sujeto. Para cuentas, accesos de expedientes de esa cuenta; ser propietario de una agencia no autoriza incluir a sus modelos. Los accesos del expediente actual no se incorporan recursivamente: permanecen como laguna explícita. El corte de accesos históricos es la ejecución; cambios posteriores requieren evaluación operacional y no quedan acreditados por este inventario.

Cada candidato y cada laguna necesita resultado, motivo y evidencia. El historial de un rol no demuestra divulgación. «Comunicado» exige acuse registrado del destinatario aplicable a esta fuente. La fuente actual no incorpora notificaciones: ese resultado se rechaza. No reutilizar acuses de rectificación como prueba de entrega de otro derecho.

La persona asignada propone; otro operador con permisos vigentes consulta y revisa. La auditoría se registra antes de descifrar la propuesta. Se comprueban la fuente vigente, versiones del expediente/respuestas, canal, integridad, sesión y MFA del autor y del lector. Las claves permiten replay idéntico y rechazan cuerpos distintos. La retirada de permisos se comprueba contra la base de datos, aunque el objeto recibido tenga permisos cacheados.

Una revisión favorable puede confirmar que quedan tareas pendientes; no acredita comunicación completa, no cierra el derecho y no incrementa la versión del expediente. Los registros de evaluación/revisión no son borradores finales: la purga0109 no acredita su conservación jurídica integral.

## Trabajo todavía necesario

- Consulta auditada del inventario por el autor antes de evaluar y pantallas privadas con CSRF.
- Notificación interna por destinatario, contenido revisado, autorización y acuse propios de la ejecución; gestionar destinatarios históricos sin canal autorizado.
- Consumo de la revisión y sus pendientes en el material revisado y la respuesta final, invalidación ante cambios y replay de emisión.
- Registro de procesadores/destinos externos y demostración de entregas/fallos cuando exista transporte autorizado. No enviar mensajes externos ni contratar proveedores en esta fase.
- Pruebas de aislamiento entre sujetos, variantes de agencias, concurrencia y recorrido HTTP/móvil antes de aceptar el componente integrado.

## Verificación local

`tests/test_rights_communications.py` ejecuta operaciones de supresión/limitación/oposición reales sobre PostgreSQL con identidades sintéticas. Verifica propuesta/replay, independencia, consulta auditada antes de descifrado, revisión/replay, rechazo de permisos retirados y preservación del expediente abierto. No verifica identidad externa ni entrega de comunicaciones. Los resultados terminales y el alcance exacto se registran en el seguimiento/historial.
