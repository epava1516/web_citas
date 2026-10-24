# B13 — Restauración con clave HMAC de dominio fijada

Estado: PASS local del ensayo ampliado, B13 abierto7/18. Continúa [restauración144](144-restauracion-retirada-beta-b13-20261021.md) y [separación de firma151](151-clave-hmac-dominio-beta-b13-20261021.md).

El ensayo real anterior no propagaba SAFETY_HMAC_KEY al proceso hijo restaurado. Se amplía sin modificar firmas de funciones ni eliminar controles: cuatro variantes plain/encrypted × misma clave/transición. Las variantes de transición ahora combinan readers Fernet anteriores, clave HMAC fijada al secreto sintético original y firma Django nueva. Las variantes sin transición conservan modo heredado y claves originales.

Se establecen claves sintéticas antes de generar las fixtures. Antes del backup se calculan testigos HMAC de valor sintético fijo con ambos productores de dominio; después de cambiar firma deben ser idénticos. Se pasan al clon por entorno las claves y readers, incluida SAFETY_HMAC_KEY; no se recuperan del dump ni de un servicio normal. El hijo debe verificar los testigos y, en transición, distinguir clave de dominio de firma Django. No se exporta clave o hash de clave como prueba.

Tras reconciliar ledger y medios, invalidar grants, limpiar sesiones y reconstruir publicación, el cliente WSGI aislado debe acceder al recibo original del perfil par con200 private/no-store. El secreto del recibo sintético se pasa por entorno del hijo, no por JSON de argv ni por propiedades JUnit. No servidor HTTP ni worker sobre el clon, no apertura real. El resto de controles mantiene autoridad independiente, aislamiento de DB/media/cache, desaparición del sujeto suprimido y conservación del par.

La extensión comercial existente llama el mismo ensayo con transición y backup cifrado: debe conservar su evidencia dependiente sin reactivar promociones del sujeto suprimido. Los simuladores comerciales no se convierten en pagos reales. Las bases restauradas deben eliminarse y el origen conservar su caché y sesión de control.

Selección focal prevista22casos:4restore+1extensióncomercial+9proveedorHMAC+8recibos. PostgreSQL y dump/restore reales en las cinco restauraciones; el proveedor mantiene sus casos estáticos diferenciados. Refrescar grafo y congelar fuentes antes de ejecutar; conservar negativos y conciliar resultados, limpieza y Telegram. No retirar claves, restaurar sistema productivo, acreditar custodia/offsite/PITR ni trasladar automáticamente la aceptación al rollback de imágenes incompatibles.

## Resultado terminal

061505-c5e00a3a:22PASS/0FAIL/0ERROR/0SKIP,105,889sJUnit,4workers. [Auditoría terminal](evidencias/b13-hmac-restore-terminal-audit-20261021.json): cinco restauraciones reales (cuatro variantes y una extensión comercial), nueve casos del proveedor y ocho de recibos. Sin negativo en esta ejecución.

Tres restauraciones usan firma Django nueva, clave de dominio fijada y readers Fernet anteriores; dos conservan modo heredado sin transición. Las cinco verifican testigos HMAC y recibo original del par200 privado, grants restaurados invalidados, todas las sesiones del clon eliminadas y copia/auditoría del par conservadas. Las cinco bases restauradas se eliminan. El origen mantiene su caché y sesión de control, y las huellas de medios restantes coinciden. La extensión comercial conserva su evidencia sin reactivar promociones suprimidas.

Las fuentes de producto coinciden con la candidata de clave HMAC151. Fuentes congeladas actuales, procesos/temporal/contenedores propios ausentes y TelegramPASS confirmados. publication_authorized=false en todos los clones. El recibo se consulta mediante Client WSGI durante el control aislado, sin abrir servidor o worker. No se acredita custodia de claves, offsite/PITR ni recuperación si falta o se compromete la clave de dominio. B13 sigue abierto7/18 por los pendientes de su matriz.
