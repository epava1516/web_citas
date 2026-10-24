# B16-353 — Ejecución de candidata funcional común

B16-353 ejecutará la candidata funcional común preparada en313:3829nodeids exactos, cuatro workers, snapshots de fixtures por worker, broker aislado y orden por duración que no elimina casos ni altera su orden interno por archivo. Se conserva el recorrido completo de1500revisiones;306casos de capacidad y11exclusiones oficiales requieren disposición separada.

## Necesidad y protocolo previo

El puente352 prueba16fuentes nuevas y20modificadas desde la regresión amplia histórica, incluidas autoridad, cifrado, recuperación y exposición; las verificaciones focalizadas posteriores ya permiten una nueva candidata común. No se lanza por escribir un plan ni para convertir negativos antiguos en PASS. Las fuentes actuales de producto coinciden con la última corrección351; sus12casos no bastan como aceptación común.

Comando: run_local_ci.py --profile regression --regression-lane functional --native-source /tmp/web-modelos-librdb-v2.4.0 --workers4 --fixture-snapshots --isolate-test-broker --duration-order-from b16-353-duration-history.json --timeout21600. El límite21600s pertenece al comando de pruebas, no a un nuevo SLO del producto. PostgreSQL/Redis propios, navegador y almacenamiento local reales donde el recorrido lo exige; servicios normales y proveedores externos no se modifican.

Historial de duración copiado con SHA:567archivos conocidos y48archivos funcionales sin ponderación previa, que reciben coste0para ordenar y permanecen en la selección. Se exigirá prueba de conjunto idéntico por los cuatro workers y se compararán nodeids con los3829prerregistrados; totalesJUnit y subreportes se conciliarán por separado. No se atribuye aceleración causal nueva a esta ejecución.

La ejecución se congela tras actualizar el grafo y preparar todos los helpers. run_local_ci.py conserva notificación terminal después de limpieza. Supervisor, watcher, compactador y reactivador persistentes guardan PID/start_ticks; el último sólo actúa sobre el mismo objetivo y createdAt, sin sustituir objective ni reiniciar consumo. Preaviso Telegram confirmado y lanzamiento vivo son requisitos antes de pausar el goal; compactación sólo con goal pausado e hilo idle.

La documentación oficial de [App Server](https://learn.chatgpt.com/docs/app-server) describe thread/goal/get,set y thread/compact/start; omitir objective conserva el consumo del goal existente. El esquema local y una lectura del goal/hilo han sido verificados; el disparador incorpora la autorización posterior del usuario del21/10descrita en AGENTS.md. Cambios de objetivo/createdAt o estados terminales no se fuerzan a active; existe cancelación explícita del disparador. No crear otro goal ni invocar un modelo para vigilar archivos. Un fallo de aviso o disparador queda registrado y no convierte pruebas en PASS.

Al volver: auditar fuentes congeladas, colección exacta, PASS/FAIL/ERROR/SKIP por separado, privacidad, limpieza real y recibos. Cada SKIP requiere disposición, nunca cuenta como PASS. No aceptación automática de B16, de recursos/capacidad o de beta por terminar esta regresión. No repetir baterías ni lanzar la fase de capacidad antes de interpretar sus resultados y necesidad. La carga limpia, restauración y preparación para usuarios mantienen sus criterios.

Confirmación del usuario2026-10-24: todavía no hay proveedores elegidos. B14 queda explícitamente pendiente de selección y autorización; esta respuesta no autoriza integración externa, contratación, envíos o uso de datos reales. B10, B15opcional y B17conservan sus pendientes.13/18puntos cerrados; objetivo completo activo antes de la pausa autorizada.
