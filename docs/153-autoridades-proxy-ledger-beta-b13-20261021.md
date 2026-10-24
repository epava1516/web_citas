# B13 — Autoridades del proxy y ledger de recuperación

Estado: PASS local por evidencia combinada, B13 abierto7/18. Complementa [matriz141](141-continuidad-moderacion-beta-b13-20261021.md), [clave de dominio151](151-clave-hmac-dominio-beta-b13-20261021.md) y [restauración152](152-restauracion-clave-hmac-beta-b13-20261021.md).

## Autoridades diferentes

| Clase | Alcance | Procedimiento local y límite |
|---|---|---|
| Firma Django | Sesiones, tokens de cuenta, OTP/MFA recovery y tokens proxy breves | Reautenticación/reemisión normal; las sesiones con fallback requieren su política explícita. No cambia cifrado si las claves son explícitas. |
| SAFETY_HMAC_KEY | Recibos y bindings de dominio | Pin exacto anterior permite rotar Django sin rehash. Una clave de dominio distinta no migra evidencia; cambio durante lote se rechaza con rollback. |
| MFA/SAFETY_ENCRYPTION_KEY | Sobres cifrados de aplicación | Activa nueva escribe; readers anteriores leen, sin recifrar filas. No retirar mientras haya copias no censadas. |
| Credenciales DB/Redis | Apertura de conexiones de servicio | Cambiar contraseña no termina necesariamente clientes existentes: cerrar/recrear propios, terminar sólo los identificados y comprobar reconexión/ACL/datos/cola. |
| RIGHTS_DELIVERY_PROXY_SECRET | Autenticación de Caddy hacia endpoint interno | Rotar coordinadamente backend y proxy; cabecera antigua rechazada antes de consumir grant. No es la clave que firma el token de entrega. |
| RIGHTS_DELIVERY_GENERATION | Invalida namespace lógico de grants | Cambio rechaza grants anteriores, no borra bytes por sí solo; ejecutar purga y conservar auditoría. La autorización del expediente/exportación es distinta del grant transitorio. |
| Claves cifrado/firma RecoveryLedger | Registros externos y checkpoint de recuperación | Mantener claves propias de su cadena. Sustituirlas no convierte registros antiguos; una clave incorrecta debe fallar y no descifrar antes de verificar integridad. No se implementa rollover de autoridad aquí. |

## Ensayo nuevo del proxy

Dos casos PostgreSQL con HMAC de dominio explícito: rotación sólo de credencial interna, y credencial más generación. Se crea copia/grant mediante fixtures normales y se conserva la fila de descarga original. La cabecera antigua debe404 sin consumo ni purga. Con generación igual, cabecera nueva autoriza el token existente una vez. Con generación nueva, el token anterior debe404, permanecer sin consumir y perder bytes tras purga; un POST autorizado con clave nueva crea descarga/grant nuevos válidos. Reintento del token consumido404, y auditoría original intacta.

Es Client WSGI del endpoint interno y lectura real de caché local, no una recarga Caddy acreditada por esos dos casos. Se incluye el testigo TCP Caddy existente para transportar bytes y bloquear replay/ruta cruda; el cambio de credencial durante un reload de Caddy no se atribuye a ese testigo sin ensayarlo.

Para operar: coordinar mantenimiento, distribuir el secreto interno nuevo por canal privado a backend y proxy, recrear/cargar configuración y comprobar rechazo de la anterior. Si hay que invalidar URLs pendientes, cambiar generación y purgar bytes del ámbito propio; no borrar auditoría ni asumir que eso revoca la autorización de una exportación. No actualizar sólo un archivo de entorno suponiendo recarga automática del proceso.

## Ledger y conciliación de B13

Un caso estático adicional verifica que cambiar claves de firma/cifrado de aplicación no altera la capacidad del codec independiente para leer su cadena ni los bytes de los registros. Se ejecutan también codec/store existentes: rechazo de claves incorrectas, integridad antes de descifrado, checkpoint independiente contra rollback, identidad, archivos perdidos/alterados y permisos/symlink. No inventar un rollover a clave nueva ni copiar el checkpoint viejo como autoridad de otra cadena.

La salida local del roadmap exige runbooks ejecutados, fallos detectados, restauración aislada y retirada efectiva. La custodia, infraestructura de destino, canales y personas reales se acreditan para apertura en B17/G03/G06/G07. No bloquear o aceptar B13 por exigir que el software descifre sin claves perdidas: ese supuesto requiere custodia/recuperación de claves; tampoco declarar esa custodia probada por conservarlas en memoria de una fixture. Quedan explícitos los límites de cambio/compromiso de dominio y de las cadenas de ledger.

Antes del ensayo se refrescan fuentes/grafo y se congela la selección. Contabilizar por separado casos PostgreSQL, codec/filesystem y transporte real; conservar negativos y comprobar limpieza y Telegram terminal. Este documento no cierra B13.

## Primera ejecución y cierre del hilo WSGI

062952-6b0fa133:34PASS/0FAIL/0ERROR/0SKIP,56,266sJUnit, una advertencia al borrar la DB del worker que ejecutó Caddy: permanecía una conexión del hilo WSGI. [Auditoría del corte](evidencias/b13-proxy-ledger-warning-20261021.json): fuentes/limpieza final del runner/TelegramPASS confirmados; no se presenta como ejecución sin advertencias.

El arnés del testigo Caddy ahora cierra iterable de respuesta y conexiones Django en finally dentro del hilo servidor. No se cambia persistencia de conexiones del producto ni se desactiva la advertencia. Preparar repetición del caso afectado; los33PASS restantes sólo serán reutilizados tras comprobar igualdad de producto, fuentes, helpers y demás AST de la fuente tocada. No sumar la repetición como caso único nuevo.

## Resultado vigente

063731-2d193e08:1PASS/0FAIL/0ERROR/0SKIP,45,783sJUnit, sin advertencias. [Aceptación acotada](evidencias/b13-proxy-ledger-scoped-acceptance-20261021.json):1caso Caddy repetido y33PASS reutilizados =34casos únicos; no ejecución nueva única de34. La fuente anterior se conservó con huella exacta; sólo cambió la función Caddy, con helpers y demás AST/bindings del módulo idénticos y todas las demás fuentes iguales.

Los dos casos PostgreSQL nuevos verifican credencial anterior denegada sin consumo, credencial nueva con un uso y auditoría original intacta. Con generación nueva también hay rechazo de URL antigua, purga física y grant nuevo por descarga autorizada. El caso independiente conserva lectura y bytes del ledger al cambiar claves de aplicación. Los30casos codec/store existentes conservan sus resultados; no suman evidencia de rollover de claves propio de ledger. El testigo Caddy transporta bytes reales y bloquea replay/ruta cruda, pero no se acredita recarga de su secreto durante ejecución.

La advertencia de la primera ejecución queda preservada. El cierre explícito de conexiones en el hilo WSGI elimina esa advertencia en el caso repetido; el runner confirmó retirada de contenedores, procesos y temporal propios. Inventario actual de contenedores Caddy de prueba vacío; fuentes actuales y Telegram terminal verificados. Producto existente intacto; sólo se añadió prueba y se corrigió arnés. B13 sigue abierto7/18, con recarga de secreto Caddy, límites de autoridad y revisión final de su matriz explícitos.

El límite de recarga Caddy se amplió después en [154](154-recarga-secreto-caddy-beta-b13-20261021.md):5PASS en una ejecución común, con reload real del secreto, mismo contenedor/grant y rechazo previo sin consumo. La evidencia de153 conserva su propio alcance anterior; el rollover del ledger y los controles externos no reciben aceptación por esa ampliación.
