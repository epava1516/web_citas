# B12 — Coste del snapshot y rotación propia

Estado: snapshot medido y rotación/lectura propias verificadas; no aceptación B12.

Grafo previo79:3c0d4f352db92e8843b292b1332b6950ab8068fab17f4de2f438e3faef807045. Continúa [ventanas135](135-informes-ventanas-eventos-beta-b12-20261020.md). No cambios en producto ni servicios normales.

## Snapshot PostgreSQL

Diagnóstico explícito tests/beta_snapshot_cost_diagnostic.py, sólo con LOCAL_CI_ISOLATED_BROKER_RUN y PostgreSQL de pruebas, salida en artifacts/local-ci/<run_id>/snapshot-cost.json. Primero vacío y después10000marcas PublicationDirty y10000ReportNotice sintéticos:4000due/2000scheduled/2000exhausted/2000failed. Filas instrumentales, sin afirmar autorización o entrega de un caso de dominio. Una primera llamada, cinco calentamientos y treinta llamadas medidas por estado; observaciónSQL separada, CPU cliente, RSS antes/después y pico de todo el proceso. No confundir execute con tiempo de fetch ni CPU cliente con CPU PostgreSQL. Las otras tablas permanecen vacías.

Ejecutar mediante run_local_ci workers1, junto a seis snapshot y nueve ventanas:16casos previstos. Conservar muestras crudas, selección, fuentes congeladas, XML, limpieza y recibo Telegram. Sin adoptar umbral retroactivo ni extrapolar a todas las cardinalidades.

## Rotación y lectura Docker propias

scripts/probe_operational_rotation.py usa una imagen postgres:17-alpine ya cacheada, resuelta a ID inmutable y --pull=never. Contenedor con nombre/etiqueta propios, sin red, raízreadonly, tmpfs1MiB,64MiBmemoria/1CPU; sin montar archivos del daemon ni modificar su configuración. Validar Compose actual y HostConfig json-file/max-size1m/max-file3 del contenedor nuevo.

Docker documenta que los cambios afectan a nuevos contenedores y desaconseja acceder a archivos internos del driver: se utilizarán sólo inspect/logs/wait/rm por API. [Referencia oficial](https://docs.docker.com/engine/logging/drivers/json-file/). La prueba no acredita un techo físico de disco medido ni recrea app/worker/Beat.

Un evento inicial demuestra que docker logs --follow ya está leyendo antes de liberar50000eventos sintéticos, con el último marcador task_result failed. Ese marcador es una línea de diagnóstico, no una tarea real ejecutada. Comprobar50001eventos ordenados y únicos recibidos por el lector, mientras la lectura posterior conserva sólo el sufijo tras rotación. Comparar la última ventana de360timestamps sintéticos mediante el agregador real y detectar un fallo observado. Los timestamps sirven como secuencia sintética, no como reloj operativo.

Ejecutar tras terminar y auditar la selección de PostgreSQL, sin mediciones simultáneas. Retirar lector/contenedor y confirmar ausencia por nombre/etiqueta; conservar configuración y agregados, no líneas de logs. El informe mantiene coverageunverified/healthunknown. Una única ráfaga propia no acredita continuidad universal ni recuperación del receptor tras reinicio.

Salida de este corte: medidas de coste y evidencia local de rotación/lectura, no aceptación B12. Persisten cadencia y presupuestos operativos justificados, receptor/salud y ventanas conciliadas bajo fallos, umbrales/respuesta y runbook. B07 sigue pendiente y no se lanza capacidadTCP.

## Preparación corregida

Primer corte000530-c4de4b06:15PASS/1SKIP/0FAIL/0ERROR; diagnóstico omitido porque el runner filtra variables heredadas. No hay medida de coste en ese corte. [Auditoría de omisión](evidencias/b12-snapshot-cost-skipped-audit-20261021.json): fuentes/limpieza/terminal/Telegram comprobados. Se corrige sólo el diagnóstico para usar el identificador de broker aislado ya suministrado y escribir en su directorio propio; el runner y sus filtros permanecen intactos. La medición y rotación continúan pendientes.

## Snapshot verificado y primer negativo de rotación

000850-e3f5a3b2:16PASS/0FAIL/0ERROR/0SKIP,63,557sJUnit. [Auditoría terminal](evidencias/b12-snapshot-cost-terminal-audit-20261021.json) y [muestras crudas](evidencias/b12-snapshot-cost-20261021.json): producto intacto respecto235519, fuentes contrastadas de nuevo, procesos/contenedores/temporal ausentes, TelegramPASS confirmado.

| Filas dirty y avisos por tabla | Mediana ms | p95 ms | Máximo ms | Primera llamada ms | SELECT en observación separada |
| --- | --- | --- | --- | --- | --- |
| 0 | 46.677 | 106.640 | 115.567 | 92.313 | 31 |
| 10000 | 78.400 | 121.083 | 133.964 | 91.076 | 31 |

p95 local106,640ms vacío y121,083ms con10000marcas+10000avisos. RSS antes/después sin incremento observado en ambos estados; no acredita pico de memoria exclusivo ni coste de todas las tablas pobladas.31SELECT y33sentencias capturadas por observación separada; no convertirlas en CPU del servidor. No presupuesto de cadencia adoptado todavía.

Primera rotación terminóEXIT1 por timeout al esperar follower.wait15s. [Auditoría negativa](evidencias/b12-rotation-first-negative-20261021.json): fuentes intactas, contenedor/lector propios ausentes y TelegramEXIT1 confirmado. No hay artefacto de cantidad recibida en ese intento: no inferir causa del atasco ni recepción completa.

Segundo protocolo: tras terminar productor, esperar los50001eventos ordenados con plazo y rechazo explícito de huecos; detener lector por el controlador en vez de exigir terminación espontánea. Conservar contadores y tipo de error también si falla; comprobar retiro de lector/contenedor. Snapshot no se repite por cambiar sólo este instrumento. Rotación y aceptación B12 siguen pendientes.

## Rotación y lectura verificadas

Segundo intento:50001/50001eventos recibidos en orden por el lector propio, retirada explícita al completar el conteo. Docker29.8.1 y HostConfig json-file con max-size1m/max-file3 comprobados. La consulta posterior por API conservó10174eventos, timestamps sintéticos39827–50000 y1387739bytes de contenido, frente al histórico completo recibido en vivo. Son bytes de salida de API, no tamaño físico de archivos.

[Resultado de rotación](evidencias/b12-rotation-20261021.json) y [auditoría terminal](evidencias/b12-rotation-terminal-audit-20261021.json): fuentes contrastadas de nuevo, controlador/lector terminales, contenedor propio ausente y TelegramPASS confirmado. Sin volúmenes persistentes ni mountsbind, imagen cacheada fijada aID y sin acceso a archivos del daemon. Servicios app/worker/Beat normales intactos.

La última ventana coincide en lectura continua y consulta posterior:359lecturas,35fallback y un marcador sintético de tarea fallida; cero líneas malformadas. El agregador conserva coverageunverified y healthunknown. El cierre explícito del controlador evita depender de la terminación espontánea del CLI; no demuestra la causa exacta del primer timeout ni cuánto había recibido aquel intento.

Resultado acotado: coste del snapshot y circuito local de rotación/lectura acreditados. No despliegue, caída o reinicio del receptor, alerta a responsables ni techo físico de almacenamiento medido. Los negativos de omisión y timeout permanecen. Siguiente incremento: integrar señales durables y ventanas en una evaluación administrativa con umbrales justificados y runbook ejecutado, preservando desconocido cuando la cobertura no se acredita. B12 y B07siguen abiertos; no nuevoTCP.
