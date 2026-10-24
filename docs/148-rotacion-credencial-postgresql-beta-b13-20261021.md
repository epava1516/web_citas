# B13 — Rotación de login PostgreSQL y conexiones existentes

Estado: PASS local PostgreSQL propio; B13 no aceptado, siete de18puntos cerrados. Complementa [141](141-continuidad-moderacion-beta-b13-20261021.md) y [censo147](147-consumidores-hmac-beta-b13-20261021.md).

La salida local de B13 exige runbooks ensayados. La custodia, operadores, contraseñas y canales de la infraestructura de destino pertenecen a la salida externa B17; no se presentan como operativos por superar un contenedor de prueba. La prueba nueva usa PostgreSQL17 propio, rol y tabla sintéticos, TCP loopback efímero y volumen de datos tmpfs. No modifica el servicio normal ni ejecuta initialize_rights_runtime sobre él.

## Procedimiento local que se va a verificar

1. Separar el administrador/migrador y el login de servicio, como exige compose.runtime-role.yaml. Identificar la DB y el rol exactos y disponer de canal administrativo independiente; conservar inventario de permisos y datos de control sin extraer secretos.
2. Preparar la nueva credencial por un canal privado y coordinar la ventana de mantenimiento de los clientes del rol. No volver a una imagen con configuración secreta anterior como supuesto rollback automático.
3. Usar NOLOGIN como cierre temporal de nuevas conexiones cuando corresponda al corte controlado. Esa operación y el cambio de PASSWORD no deben asumirse como terminación de sesiones ya establecidas.
4. Actualizar credencial de forma privada, comprobar rechazo de la anterior al abrir conexiones y acceso con la nueva cuando LOGIN esté habilitado. El ensayo también comprueba el cierre NOLOGIN y su reapertura; no es una transición productiva con tráfico concurrente.
5. Cerrar/recrear pools y clientes propios y terminar desde la conexión administrativa los backends anteriores identificados. Seleccionar sólo el ámbito propio y mantener el canal administrativo. No usar indiscriminadamente un terminador global sobre servicios ajenos.
6. Verificar nueva conexión, consulta de control, permisos restrictivos y filas conservadas. Confirmar que la conexión anterior terminada ya no consulta y que el control nuevo permanece operativo. Restablecer servicio sólo tras esas comprobaciones y registrar resultado minimizado.

## Alcance de la prueba

Un caso de integración real: login viejo válido; cambio de contraseña; nueva contraseña válida/antigua rechazada; conexión antigua todavía activa; NOLOGIN impide nuevas conexiones pero conserva las ya abiertas; terminación del backend antiguo revoca esa conexión; LOGIN vuelve a permitir acceso nuevo. El rol no gana superusuario, creación de DB/roles, replicación o bypass RLS; SELECT sigue autorizado e INSERT sigue denegado sobre la tabla de control. Credenciales aleatorias sintéticas, nunca incluidas en propiedades JUnit ni Telegram.

El caso demuestra el mecanismo de login y conexión, no el cierre de pools Django desplegados, credencial Redis, proxy de grants, proveedor de objetos, ledger independiente o identidad de operadores reales. Las garantías del rol de aplicación se verifican separadamente mediante el inicializador y sus pruebas; una tabla sintética de SELECT no sustituye toda esa matriz ACL. PostgreSQL obligatorio sí se ejecuta en este caso, sin simulador ni skip.

Antes de la ejecución se refresca el grafo y se congelan prueba y fuentes relacionadas. Conservar cualquier negativo, verificar retirada del contenedor y recibo Telegram terminal. B13 mantiene pendientes la clasificación persistente HMAC y los procedimientos restantes de secretos; este ensayo no autoriza retirar claves históricas.

## Resultado terminal

1PASS/0FAIL/0ERROR/0SKIP,3.944sJUnit (12,72s mostrados por pytest con aviso). [Auditoría terminal](evidencias/b13-pg-login-rotation-terminal-audit-20261021.json): las seis propiedades de cambio de contraseña, cierre/reapertura LOGIN, sesión vieja, terminación dirigida, nueva sesión/ACL/datos y retirada del contenedor son verdaderas. Fuentes frescas y recibo TelegramPASS confirmados. No negativo en esta ejecución.

La conexión vieja siguió operativa tras PASSWORD y NOLOGIN; la terminación explícita de su PID la revocó. La nueva conexión de control sobrevivió, LOGIN volvió a aceptar la nueva contraseña y no se añadieron filas ni privilegios. Producto existente intacto frente al corte041741: sólo prueba nueva y documentación. No rotación de credenciales normales ni validación de pools desplegados.

B13 sigue abierto por clasificación persistente HMAC y procedimientos restantes de secretos/credenciales. La custodia y el personal reales no se dan por probados en local y mantienen su gate B17. Siete de18puntos cerrados.

## Ampliación preparada: conexiones Django

La configuración vigente usa CONN_MAX_AGE=60 y CONN_HEALTH_CHECKS=True, sin pool psycopg configurado. Se amplía el mismo caso con DatabaseWrapper aislado y settings copiados, apuntando exclusivamente al puerto de PostgreSQL propio; el alias default no se modifica ni conecta. Tras PASSWORD, la conexión persistente debe seguir con el mismo backend. Después de terminarlo, el control de salud debe cerrar la conexión inútil e intentar reconectar: con credencial antigua se espera error de autenticación; actualizando la configuración privada del wrapper debe abrir un backend distinto y conservar filas. Pendiente de ejecución; no se afirma recarga automática de variables de entorno de procesos desplegados.

## Resultado de reconexión Django

Caso ampliado:1PASS/0FAIL/0ERROR/0SKIP,3,780sJUnit (13,20s mostrados por pytest con notificación). [Auditoría ampliada](evidencias/b13-django-reconnect-terminal-audit-20261021.json): las seis comprobaciones PostgreSQL anteriores y las tres de conexión Django pasan juntas en la misma ejecución. Es el mismo caso reforzado, no dos casos únicos sumados. Ningún negativo en esta ampliación.

DatabaseWrapper utilizó la configuración vigente de persistencia60s/health checks y un alias/host/puerto exclusivos del PostgreSQL sintético. Tras rotar PASSWORD, su backend siguió igual. Después de terminarlo, close_if_unusable_or_obsolete reinició el control de salud; cursor detectó el backend caído y la reconexión con contraseña antigua fue rechazada. Cambiar PASSWORD en la configuración del wrapper permitió un backend nuevo con las mismas filas. No se tocó el alias default ni se demostró recarga en caliente de configuración del proceso.

Procedimiento: distribuir la credencial privada nueva y recrear los procesos de aplicación/worker/Beat que la cargan al inicio; cerrar conexiones persistentes del ámbito propio y comprobar conexiones nuevas antes de restablecer el servicio. Una variable cambiada en un archivo o almacén no modifica por sí sola settings ya cargados. El ensayo verifica la capa de conexión, no una actualización externa con clientes reales o garantía de cero interrupciones.

Producto existente intacto; fuentes actuales, contenedor retirado y recibo TelegramPASS verificados. Ya no queda sin probar la reconexión del wrapper Django en local; despliegue, custodia y operadores reales conservan B17. Otros secretos y clasificación HMAC de B13 siguen pendientes,7/18cerrados.
