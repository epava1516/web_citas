# N09A — prerregistro de autoridad durante una espera de recuperación

Diagnóstico antes de cualquier corrección de aplicación. N09 sigue abierto,8/13bloques aceptados. Continúa [418](418-n09-inventario-descomposicion-20261026.md), base71860c7. El grafo inicial tiene2.036fuentes exactas y SHA256 `85abc817117601103d390fbebcc3073a1a32d804b2fc43c30f738091f7b903de`. No se repiten los testigos válidos por documentación; MOD09 restante sigue diferido y no se activa proveedor.

## Condición de fuente e hipótesis comprobable

Se han leído `apps/safety/notice_operations.py:66–150` y `apps/safety/media_operations.py:35–106`. Las recuperaciones comprueban `allowed(user)` o `can_recover(user)` antes de esperar locks de expediente/medio y vuelven a consultar ámbito usando el objeto de usuario existente. No se observa una recarga del operador/permiso después de la espera. Las pruebas originales de revocación localizada retiraban el permiso antes de otra petición HTTP; la concurrencia de recuperación comprueba idempotencia, no la revocación durante espera.

Esto es una **hipótesis**, todavía sin FAIL ejecutado: una petición ya admitida podría reutilizar su caché de permisos después de que otro actor revoque la autorización en base de datos. No se modifica el producto ni se extrapola a todos los139IDs antes de probarlo. La revisión de reportes ya tiene un helper de autoridad fresca; no se presupone que proteja estos servicios distintos.

## Dos casos de diagnóstico

1. `route:R_notice_recover`, tipo report: fixture nativa de aviso agotado, operador con MFA y permisos de gestionar entrega/revisar expediente. Petición POST real del Client EN, mientras otra conexión mantiene el lock del `Report`. Revocar `manage_notice_delivery` sólo cuando PostgreSQL confirme que el backend de la petición está esperando un lock; después liberar y observar resultado.
2. `route:R_media_erasure_recover`: fixture nativa de trabajo agotado ligado a un expediente, operador independiente con MFA y permisos de derechos/borrado. POST real EN mientras otra conexión bloquea el `Blob`; revocar `manage_media_erasure` durante la espera confirmada y liberar.

Usar PostgreSQL desechable real del runner, ejecución serial y dos conexiones, fixtures sintéticas y almacenamiento local. No parchear servicios, autenticación, permisos, managers, reloj ni SQL de negocio. `execute_wrapper` puede observar la conexión y el backend PID antes de la sentencia; `pg_stat_activity` confirma `wait_event_type=Lock`, no un sleep fijo ni una falsa barrera. El PID se obtiene de la conexión efectiva, no de una conexión anterior que el Client pudiera cerrar. Preparar sesión/CSRF habituales sin emitir credenciales o secretos.

Esperas internas finitas: hasta15segundos para observar el bloqueo y hasta45segundos para resolver la petición una vez liberado, liberación en finally y cierre de conexiones/hilos. El runner impone un timeout externo. No se alteran bloqueos o entidades de producción ni se conectan MCP a credenciales descubiertas.

## Oráculos, evidencias y criterio

La admisión inicial debe ser legítima y la revocación debe estar confirmada antes de liberar el bloqueo. Resultado requerido: **403**, permiso retirado y cero nuevo registro de recuperación/acción, sin modificar intentos, versión, estado, errores o referencias del trabajo/aviso. Usar snapshots de campos escalares de las filas de dominio pertinentes, retenidos localmente; exportar sólo hashes, conteos y estados mínimos. La revocación de permisos es el único cambio externo deliberado y no se compara como fila de negocio.

Registrar aun si falla: caso/ruta, bloqueo real observado, rol de operador inicial, permiso revocado, status final, conteos de acciones, cambios de dominio por hash, duración de petición y de espera observadas, limpieza de hilos/conexiones. No registrar payload, motivo privado, correo, rutas de ficheros ni credenciales. Los tiempos incluyen la espera inducida: no son latencia normal, p95 ni una comparación de rendimiento.

Si el código actual devuelve302 y cambia el dominio tras la revocación confirmada, conservar el FAIL original y tratarlo como defecto funcional de autoridad que debe corregirse. No convertirlo en xfail, reducir el oráculo o presentarlo como PASS de latencia. Si ya deniega, conservar evidencia y descartar la hipótesis. Cualquier defecto del instrumento se distinguirá y corregirá sin repetir las pruebas válidas ajenas al alcance invalidado.

Antes de ejecutar: revisión acotada con Django Expert/Reviewer, AST del instrumento y semántica de este prerregistro/seguimiento, comprobación del grafo y congelación completa. Sólo se seleccionarán los dos casos nuevos; el código de aplicación permanece71860c7. Tras el resultado, una corrección de producto necesitará una ficha específica de cambio, revisión de autoridad fresca y regresión pertinente de recuperación, replay, conflicto y privacidad. No se decide todavía su implementación.

Toda ejecución y su resultado terminal se notificarán por el Telegram configurado, comprobando el recibo y la limpieza. Este diagnóstico no cierra N09; las52rutas de derechos,48IDs asíncronos y los demás compartidos mantienen su revisión y disposición pendientes.
