# Supresión de identidad y acceso de cuenta

REQ-CR09-ACCOUNT-ERASURE-01. Implementación local parcial de CR-09, sometida a las mismas comprobaciones de identidad, ámbito, permisos, MFA, recusación, lectura auditada, versión y fuente del ejecutor de supresión.

La finalidad `account` admite ejecutar una decisión `erase` únicamente si también se ejecutan `authentication` y `account_preferences`, y la publicación se suprime en esa operación o ya consta suprimida. No permite eliminar una cuenta que conserva otras responsabilidades: propiedad o pertenencia a agencias, otros perfiles particulares o asignaciones de editor, grupos/permisos individuales o privilegios de personal/administración. El inventario incorpora estas dependencias y un cambio posterior invalida el plan.

Se vacían nombre y apellidos, correo original, nombre de usuario, verificación de correo, último acceso y secreto MFA; se reemplazan los identificadores únicos por valores aleatorios sin contacto entregable. La cuenta queda inactiva, con contraseña inutilizable y rol visitante. `User.account_erased_at` deja constancia persistente. Se conservan el ID y las relaciones de auditoría; esto no constituye anonimización integral de todos los registros del sistema. Tokens, códigos de recuperación y favoritos propios desaparecen; los favoritos de otros usuarios no se eliminan.

La transacción bloquea la cuenta, invalida versiones de sesión/MFA y aplica los ámbitos relacionados. La misma clave de acción devuelve la ejecución original sin generar otro marcador. El expediente sigue abierto: otras finalidades requieren decisiones y ejecución propias.

Confirmación de correo y recuperación de contraseña vuelven a comprobar la cuenta y el token bajo bloqueo. Un token borrado mientras la petición esperaba produce un error controlado, sin reactivar la cuenta. Emisión de tokens, alta/confirmación MFA, creación de agencia/perfil y aceptación de invitaciones comprueban la marca de supresión bajo bloqueo para impedir escrituras tardías en estos recorridos.

La migración `core0015` añade la marca de supresión. Las pruebas usan PostgreSQL, cuentas sintéticas y verificación de identidad simulada identificada; no acreditan proveedores reales ni cumplimiento jurídico por sí solas.

Pendientes: supresión o conservación justificada de otras relaciones y evidencias, cuentas con responsabilidades múltiples, archivo reservado y plazos definitivos, comunicaciones a destinatarios, conciliación de restauraciones/backups y respuesta final del derecho. La marca local no acredita eliminación en copias externas. CR-09 y la entrega completa siguen pendientes.

Refuerzo final con nombre/apellidos y secreto MFA cifrado no vacíos: primera ejecución1 failed18.13s por sesión de fixture sin binding MFA (redirige correctamente al desafío); preparación corregida con binding de sesión sintético. Repetición1 passed18.30s, acredita vaciado efectivo y revocación posterior. No altera código funcional; navegador de moderador sí ejecuta login y TOTP reales locales. Ruff/format/check/makemigrations/diff-check limpios.
