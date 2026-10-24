# B13 — Recarga real del secreto interno Caddy

Estado: PASS local de las dos variantes, B13 abierto7/18. Amplía el límite explícito del [ensayo153](153-autoridades-proxy-ledger-beta-b13-20261021.md), sin modificar producto ni proxy normal.

El testigo TCP existente ahora ejecuta steady y credential-reload. La primera conserva el flujo de transporte. La segunda activa una clave de dominio explícita antes de crear las fixtures y mantiene esa autoridad mientras rota sólo RIGHTS_DELIVERY_PROXY_SECRET.

## Secuencia observable

1. Crear copia/grant mediante el POST autorizado habitual, levantar WSGI de prueba y Caddy propio con la credencial inicial, y esperar health sin consumir el grant.
2. Dar al backend la clave interna nueva mediante override de fixture. El Caddy todavía configurado con la anterior debe devolver404; comprobar grant sin consumo/purga y bytes originales presentes.
3. Ejecutar caddy reload dentro del contenedor propio con el valor nuevo por entorno del proceso de recarga, sin ponerlo en argv. Se usa su administración local dentro del contenedor; no se publica puerto administrativo ni se modifica un Caddy ajeno.
4. Verificar el mismo ID de contenedor. El mismo URL pendiente debe entregar exactamente los bytes esperados con cabeceras privadas, sin ETag; HEAD, replay y ruta cruda deben seguir rechazados. Una sola fila de descarga y consumo del grant una vez.
5. Retirar Caddy y detener servidor/hilo WSGI; cerrar conexiones del hilo mediante el arnés corregido en153, comprobar ausencia del contenedor y ausencia de advertencias de teardown.

Se ejerce TCP real y recarga real de Caddy. La actualización del backend es una configuración de fixture en el proceso WSGI; no demuestra recarga de variables de entorno de un Gunicorn desplegado. La discrepancia inicial404 es un fallo cerrado esperado durante mantenimiento, no una promesa de cero interrupciones. En un destino con administración deshabilitada, el procedimiento operativo debe usar la recreación/configuración autorizada que corresponda y comprobarla por separado.

Selección focal prevista5casos:2Caddy y3proxy/ledger de153. Se mantienen el rechazo de clave anterior sin consumo, la purga por generación y la independencia de claves del ledger. Claves/recibos y datos únicamente sintéticos; no valores ni URL secretos en propiedades JUnit o Telegram. Las fuentes y grafo se congelan antes de ejecutar; conservar negativos y verificar recursos y aviso terminal. Este ensayo no acredita custodia, rollover del ledger ni apertura externa; B13 no se cierra por prepararlo.

## Resultado terminal

064929-b822d7ff:5PASS/0FAIL/0ERROR/0SKIP/0warnings,58,402sJUnit,4workers. [Auditoría terminal](evidencias/b13-caddy-secret-reload-terminal-audit-20261021.json): dos transportes Caddy reales y tres casos proxy/ledger pasan juntos; sin negativos en esta ejecución.

La variante de rotación comprobó404 con el proxy desactualizado, grant sin consumo ni purga y bytes presentes; reload aceptado, mismo ID de contenedor y mismo enlace pendiente entregado con bytes/cabeceras correctos. Después, replay y ruta cruda404 y una sola fila de descarga. Se ejercitó HMAC de dominio explícito. Ambas variantes verificaron cierre de hilo WSGI y retirada de Caddy, sin advertencia de DB. Los tres casos de153 conservaron sus resultados de clave/generación/auditoría e independencia del ledger.

Producto existente igual a la candidata151–152; fuentes actuales, recursos/procesos/temporal propios ausentes e inventario Caddy de prueba vacío confirmados; TelegramPASS verificado. Se cierra el hueco local de recarga de secreto Caddy señalado en153. No se declara recarga en caliente del entorno del backend, cero interrupciones, custodia real o rollover de claves de ledger. B13 continúa abierto7/18 hasta revisión de la matriz restante.
