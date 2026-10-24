# B07 — HTTP mixto con mil perfiles

B07-247 auditado: ERROR de arranque PostgreSQL antes de ejecutar pruebas HTTP. Fuentes y limpieza verificadas; compactación y reactivación del mismo objetivo confirmadas. Causa pendiente; 8 de 18, B07 abierto.

## Evidencia previa y runtime

El control246 acredita plan contrafactual100/1000, rollback lógico, cuatro censos nativos completos por escala y 44 páginas en PostgreSQL17 real. El control237 acredita HTTP mixto100. Ninguno acredita HTTP mixto1000; ésta es la siguiente ampliación funcional, no repetición del mismo caso.

Se reutiliza la imagen local inmutable `sha256:6936424d8c105237645efd3424be6ef31c74f7cb32904db3c963ddf9a7e1f44e`. El controlador y la aplicación montan el worktree actual en lectura y ejecutan su intérprete: los archivos de tests de la capa de imagen no gobiernan esta ejecución. Verificar imagen disponible, rutas de montaje e instrumento actual; preservar el producto628 del corte B13. No reconstruir ni descargar imágenes sin necesidad. Servicios normales y sus datos quedan fuera de la topología propia.

## Protocolo fijado antes de medir

Una única ejecución de `scripts/run_vps_capacity.py beta-http-functional --territorial --service-resources --backlog --mixed-states --backlog-population 1000 --cpu-budget 8 --app-image sha256:6936424d8c105237645efd3424be6ef31c74f7cb32904db3c963ddf9a7e1f44e`.

Exigir recursos kernel agregados8CPU/8GiB, swap0 y almacenamiento acotado original, PostgreSQL17/Redis7.4 reales propios, Gunicorn con cuatro workers, Celery/Beat y carga HTTP local. Datos exclusivamente sintéticos y promociones de prueba; ninguna verificación externa real. Congelar fuentes CI completas, protocolo por bytes/SHA y SHA del grafo antes de lanzar. No editar durante la ejecución ni ejecutar pruebas concurrentes.

Dataset1000: dos ciudades700/300, 200 derechos, 14 exclusiones (siete estados × orgánico/promocionado), dos derechos inactivos con perfiles visibles y dos detalles de carga protegidos. Plan contrafactual con rollback de campos/derechos y marcas vacías, sin reiniciar secuencia; aplicación real con14 generaciones posteriores. Visibilidad nativa posterior986 y191 patrocinios elegibles.

Comprobar24 páginas frescas y24 reparadas (primera/intermedia/última, dos ciudades, texto vacío/photography y ES/EN), más dos páginas pendientes de la ciudad mutada y28 detalles excluidos404 ES/EN. Comparar IDs, orden, recuento y etiquetas con referencia nativa; conservar marcas por GET. La selección no cubre todas las páginas. No exigir que los dos perfiles con derechos inactivos aparezcan en las páginas muestreadas: su visibilidad se comprueba nativamente.

Alinear con el tick original Beat5s, comprobar mutación y verificaciones pendientes antes del siguiente slot sin trasladarlo. Carga funcional3s:60 lecturas dinámicas,20 por categoría, ES/EN30/30, una subida sintética persistida. Esperar42 slots territoriales/30 rutas únicas para1000 y42 probes fríos; auditar contra constructor de rutas actual. Todas las respuestas dinámicas200 y subida302, sin fallos, omitidos, timeouts ni pendientes. Mantener límites del generador p95≤10ms/p99≤25ms/máximo≤100ms, timeout65s y drain70s. Una violación conserva resultado inválido; no repetir automáticamente para obtener verde. Latencias HTTP descriptivas de3s no acreditan SLO contractual.

Reparación observada desde mutación≤45s, tarea nativa correlacionada por identidad y generación, cola vacía al terminar. Conservar ejecuciones no emparejadas como limitación. Recursos: identidades de los seis servicios, muestras por fase, tres muestras finales de reposo, preparación y coste del observador excluidos del presupuesto medido; no imputarles coste cero. Timeout del controlador2400s, vida aplicación3000s y presupuestos de preparación/captura existentes sin cambios.

Auditar informe/JUnit/manifiestos congelados, imagen y montajes, producto628, slots y respuestas, coherencia del plan, marcas/reparación, cuotas kernel, recursos y limpieza real de contenedores/red/volumen/temporal/procesos. Confirmar recibos Telegram CI/global/callback y compactación aceptada antes de documentar resultado. Si falla, auditar y preservar el negativo antes de corregir; no aceptar una propiedad nominal sin sus aserciones y datos.

Persistir shell, watcher, callback y compactor, verificar PID/start_ticks y Telegram de inicio y prepausa. Pausar el mismo objetivo mientras continúa la prueba; shell solicita compactación y reactiva ese mismo objetivo conservando consumo al terminar, sin sondeos del modelo pausado. Guardar relevo antes de pausar.

PASS sólo acredita HTTP funcional mixto1000 con alcance observado; B07 sigue abierto. No habilita mezcla10000 ni900s automáticamente, ni acepta beta global o proveedor real.

## Resultado247 y auditoría terminal

Ejecución `20261022-142928-e887dac1`: ERROR previo a pytest, PostgreSQL detenido y treinta comprobaciones de disponibilidad fallidas. No se ejecutó el escenario HTTP. El observador terminó con ValueError y cero muestras; recursos no acreditados. Auditoría `artifacts/beta-promotion-fix-20261020/mixed247-negative-audit.json`: 1699 fuentes congeladas coincidentes y producto628 intacto; protocolo original conservado por bytes/SHA; ausencia actual de contenedores, volumen y red comprobada por nombre exacto. Telegram terminal, compactación y reactivación del mismo objetivo confirmados.

Los eventos históricos Docker consultados no devolvieron registros; no permiten inferir causa ni OOM. El contenedor fue eliminado y no se capturó su estado de salida antes de limpiar. Siguiente paso: conservar estado terminal de servicios antes de eliminarlos y diagnosticar el arranque propio, sin repetir carga para obtener verde. La primera auditoría falló por exigir «no such» también para redes; se conservó y corrigió para admitir «not found» con salida no cero. Sólo se repitió la auditoría, que pasó y notificó Telegram.
