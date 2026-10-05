# Calendario operativo de restricciones por finalidad

Estado: especificación de la siguiente entrega; no implementada ni verificada. Depende de restricciones0069 y levantamiento0070. El calendario registra atención humana, no autoriza tratamiento ni amplía conservación.

## Alcance y efectos

Cola privada global de medidas activas: revisión vencida, próximos siete días y todas; filtros de finalidad/modo. Datos mínimos de medida, expediente, responsable asignado y fecha. Excluir conflictos y ejecutor original; no exponer mensajes, teléfonos, favoritos, fundamentos o identidad del interesado. Acceso MFA/sesión vigentes y permiso dedicado de seguimiento. Conservar navegación desde expediente y enlace al procedimiento de levantamiento autorizado.

Paginación con recorrido acotado de candidatos y cursor estable, aplicando autorización antes de entregar cada fila. No cargar el ledger completo para filtrar conflictos en memoria. Un lote sin filas visibles todavía debe permitir avanzar al siguiente cursor si quedan candidatos.

Registrar seguimiento motivado y próxima revisión operativa, conservando fecha original, versión de medida, actor, fecha y motivo cifrado inmutable. Fecha futura limitada técnicamente para evitar abandono indefinido; el límite técnico no constituye plazo jurídico. Clave idempotente y versiones optimistas, conflicto409 sin cambios parciales. Consulta de motivos únicamente POST auditado; GET sin fundamentos. Historial paginado con auditoría previa, sin sobrescribir revisiones anteriores.

No cambiar active, mode, sujeto, favoritos, plazos del expediente, scope_status, pruebas, comunicaciones ni conservación. Una medida vencida continúa activa. El seguimiento no sustituye el recorrido de propuesta/comunicación/recepción/comprobación/levantamiento de docs60. Cambiar fecha/version debe invalidar propuestas que dependan de una fuente anterior; no permitir ejecutar una propuesta antigua tras seguimiento.

## Integridad y concurrencia

Locks canónicos de expediente/ámbito → medida; autoridad vigente y COI después de todas las esperas. Revalidar frente a cambio de gestor, permiso, sesión/MFA y levantamiento simultáneo. No admitir seguimiento nuevo de medida ya inactiva; replay exacto devuelve evento original sin otra mutación. Conservar trabajo/procedimientos anteriores. El calendario operativo no exige contratar un verificador externo ni simular entrega de avisos.

## Verificación y entrega

Recorrido frontend/backend ES/EN y móvil: cola → registro → recarga → historial auditado. PostgreSQL real para carreras de dos seguimientos, misma clave entre medidas, levantamiento durante espera y permisos revocados. Fechas inválidas/medida ajena/ejecutor original/no permiso/versiones antiguas sin cambios. Demostrar que favoritos siguen bloqueados y que los plazos/estado del expediente permanecen intactos.

Migración y Docker app/worker/Beat; regresión común con preparación/revisión/ejecución/levantamiento. Registrar evidencia por fuente y commit. No aceptar calendario por un cron vacío, fecha vencida o contador de tests. Tras este bloque siguen excepciones acotadas, otras finalidades, conservación histórica integral y demás pendientes de CR09.
