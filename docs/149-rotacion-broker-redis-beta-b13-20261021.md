# B13 — Rotación de credencial Redis y transporte Kombu

Estado: PASS Redis/Kombu propio, B13 abierto y siete de18puntos cerrados. Complementa [rotación PostgreSQL/Django148](148-rotacion-credencial-postgresql-beta-b13-20261021.md).

Un contenedor Redis7.4 propio, sin persistencia en disco y con TCP loopback efímero, contiene un usuario ACL sintético y un namespace privado. El administrador de la fixture conserva canal independiente; no se lee .env ni se toca broker normal. La política sintética restringe claves y canales por prefijo y deniega comandos peligrosos/administrativos. No se presenta como política ACL de producción universal para todos los recorridos Celery.

## Secuencia a verificar

1. Abrir cliente y productor Kombu con credencial antigua; dejar un mensaje JSON sintético pendiente y controles de datos propio y ajeno.
2. Añadir la credencial nueva y retirar la antigua del usuario. Comprobar acceso nuevo con la nueva y rechazo de autenticación nueva con la anterior. Revisar si el cliente ya autenticado permanece operativo: el cambio de contraseña no debe confundirse con terminación de clientes.
3. Terminar desde el administrador el cliente anterior identificado por ID. Su reconexión con contraseña almacenada antigua debe fallar. Cerrar el productor propio anterior y crear transporte con credencial nueva.
4. Publicar un segundo mensaje en el mismo namespace, consumir y hacer ACK de ambos en orden y verificar cola vacía. No FLUSHDB, borrado de namespace, regeneración de cola ni descarte de pendientes para simular recuperación.
5. Comprobar control propio, clave ajena intacta, rechazo de acceso ajeno/FLUSHDB y misma política de comandos/claves/canales. Cerrar conexiones, retirar el contenedor propio y verificar ausencia y Telegram terminal.

## Procedimiento operativo y límites

Coordinar ventana y canal administrativo; distribuir credencial privada a procesos que cargan REDIS_URL y recrear sus conexiones de broker. No ampliar ACL ni borrar pendientes ante un error de autenticación. Identificar el ámbito de clientes propios antes de terminarlos: un CLIENT KILL general sobre servicios compartidos no queda autorizado. Verificar consumo/ACK y la outbox PostgreSQL antes de restablecer el servicio; conservar el namespace normal durante una rotación de credencial. La generación nueva de cola de una restauración aislada es un procedimiento distinto y conserva los controles de144.

El ensayo cubre Redis y el transporte real Kombu usado por Celery, no una recarga de worker Celery en ejecución ni tareas de negocio entregadas a un proveedor. El ACK observado no constituye garantía general de exactly-once; la idempotencia de los dominios mantiene sus pruebas propias. Sin PostgreSQL en este caso porque no consulta datos de aplicación; la outbox/worker y su recuperación PostgreSQL están en141/146 y no se vuelven a acreditar por este ensayo.

Preparación: un caso sin skips, fuentes y grafo congelados antes de ejecutar. Credenciales aleatorias sintéticas sólo en memoria; propiedades JUnit y Telegram contienen resultados, nunca contraseñas o URLs autenticadas. B13 mantiene pendientes clasificación HMAC por dominio y otros secretos; custodia e infraestructura reales corresponden al gate de apertura B17.

## Resultado terminal

1PASS/0FAIL/0ERROR/0SKIP,4.031sJUnit (13,01s mostrados por pytest con aviso). [Auditoría terminal](evidencias/b13-redis-rotation-terminal-audit-20261021.json): seis propiedades de autenticación, cliente anterior, reconexión rechazada, cola Kombu, claves/ACL y limpieza confirmadas; fuentes actuales y TelegramPASS verificados. Sin negativo en esta ejecución.

La retirada de la contraseña antigua no cerró el cliente autenticado existente. CLIENT KILL por su ID lo terminó, y su reconexión con la contraseña almacenada anterior fue rechazada. El transporte nuevo consumió y confirmó ambos mensajes —anterior y posterior a la rotación— en el mismo namespace, sin descartar la cola. El control ajeno quedó intacto, el usuario no pudo leerlo ni ejecutar FLUSHDB, y comandos/claves/canales ACL conservaron su política.

Producto existente intacto: prueba nueva y documentación, ningún cambio de REDIS_URL normal, worker, proveedor o credencial real. Los controles PostgreSQL/outbox se conservan en sus ensayos propios y no se suman a este único caso. Falta completar otros secretos y la clasificación persistente HMAC por dominio; B13 sigue abierto7/18.
