# B07–B09 — Atribución actual de la petición promocional completa

Estado: diagnóstico terminal auditado; atribución actual y variación importante entre controles/observaciones, sin mejora causal ni cambio de producto. Ocho de18cerrados; TCPFAIL vigente,900s bloqueado.

## Motivo y alcance

Tras descartar163, no elegir otra variante por el SELECT ordinario costoso de162. El perfil115651 del día20 ya incluye costes de promociones, hidratación/render y driver, pero varias fuentes y políticas han cambiado. El ROI156 aporta controles actuales y CPUbackend real, pero sus cuatro observaciones comerciales usan tracemalloc y no son atribución exclusiva de toda la petición. No repetir ninguno como si fuese una nueva prueba causal.

Nuevo beta_current_request_phases.py:10000perfiles/2000derechos20%Top/Premium emitidos por servicios sintéticos reales, proyección limpia/reconstruida, cero pendientes, sin READ_REPAIR. Una sola preparación, PostgreSQL/Redis propios, unworker; mismo generador de la carga contractual, con límites de agencia/fotos/geografía compartidas. Ninguna variante SQL/SetPager/barrera enlazada. No proveedor ni datos reales.

## Protocolo previo

Veinte lecturas Client HTTP: listadoES y búsquedaENsynthetic; por ruta1warm+5controles+3observaciones+1controlposterior. Todos200/no-store, count10000/página24/patrocinio presente y bytes/IDs/etiquetas iguales. Controles sin wrappers/profiler/tracemalloc/GCforzado. GC normal y política intacta.

Observaciones separadas con pila de spans wall/CPUthread: raíz, _state_page, helper comercial actual, PublicationContext, hidratación escalar,24guardas nativas, presentación inicial/24descripciones/24fotos y render. SQLexecute y ServerSideCursor.fetchmany son spans hijos separados, con conteos por padre y2000filas comerciales leídas. Exactamente1contexto24 y1helper comercial, sin medir población nativa completa. Los tiempos exclusivos se concilian con raíz por lectura; inclusivos se superponen y no se suman. Las medianas de fases tampoco tienen por qué sumar la mediana de la raíz.

CPU real del backend SQL propio identificado por PIDnamespace/contendor/cgroup/startticks: schedstat antes/después fuera del reloj HTTP, mismo backend por ruta. No inferir CPUbackend de execute/FETCH ni confundir CPUthread de pytest con CPU del servicio desplegado. Host compartido; ratios observado/control y posterior/control describen intrusión/variación sin aislar causalidad. No almacenamiento de SQL/params/argumentos ni envíos de logs/datos por Telegram.

Ruff, grafo dirigido y fuentes congeladas antes de ejecutar. Timeout de controlador1800s para preparar la fixture y diagnóstico; no cambia timeouts de peticiones ni SLO. Ejecución esperada de minutos, no prueba de horas ni pausa del goal. Auditoría terminal de JUnit/artefacto/huellas/fuentesruntime726/CPUbackend/recursos/PIDs/Telegram antes de editar. Si el instrumento falla, conservar negativo y corregir sólo defecto concreto; no repetir por ruido. No criterios de adopción ni permiso para revivir variantes descartadas por tener una fase costosa. Siguiente propuesta necesita mecanismo nuevo, paridad y ROI fijado en ambas rutas.

## Terminal auditado y límites de interpretación

142521-a7e822f9:1PASS/0FAIL/0SKIP,872,81spytest sin warnings;20HTTPClient,10000perfiles/2000derechos. Preparación825,075s, separada de las lecturas. [Auditoría independiente](evidencias/b07-current-request-phases-20261021-142521-a7e822f9-audit.json):artefacto/JUnitSHA,726runtimeintactos/freeze/identidadesCPUbackend/limpieza/temporales/PIDs/Telegram terminal verificados. Recibo de auditoría también enviado.

| Mediana de cinco controles | Listado ES | Búsqueda EN |
| --- | ---: | ---: |
| HTTPClient wall |273,873ms|817,699ms|
| CPUthread aplicación/pytest |156,723ms|184,778ms|
| CPU backend PG identificado |89,482ms|579,138ms|

Listado controles wall224/201/274/280/503ms, con CPUapp124/118/157/167/357ms aproximadamente. Búsqueda wall907/782/820/818/778ms y CPUbackend655/521/562/622/579ms. Observaciones posteriores de búsqueda406/383/427ms, CPUbackend117/158/143ms; control final542ms/CPUbackend130ms. Ratios de mediana observada/control1,219listado/0,497búsqueda; posterior/control1,143/0,663. Diferencias entre posiciones e instrumentación no aisladas: no llamarlas ahorro ni atribuirlas a wrappers, GC, caché, preparación de planes, estadísticas o actividad del host sin nueva evidencia.

## Atribución de las observaciones, no de los controles

| Mediana CPUthread exclusiva observada | Listado ES | Búsqueda EN |
| --- | ---: | ---: |
| Driver execute |14,624ms|15,325ms|
| FETCH nombrado |4,767ms|5,741ms|
| Helper comercial, sin esos hijos |26,270ms|34,547ms|
| Hidratación, sin SQLexecute |56,058ms|62,310ms|
| Resto PublicationContext |20,109ms|23,103ms|
|24guardas nativas |18,635ms|19,029ms|
| Resto selección de página |9,206ms|12,355ms|
| Render sin SQL/FETCH hijos |26,691ms|25,828ms|

Por observación:1contexto24,1helper comercial/2000filas,24guardas/24descripciones/24fotos,1render;33execute y13fetchmany. De éstos5FETCH pertenecen a derechos y8al render de selectores. Tiempo wall exclusivo de execute96,474/130,272ms y FETCH54,169/65,585ms; no son CPUbackend. La conciliación exacta se verifica por lectura; no sumar estas medianas como una petición real ni deducir una mejora posible quitando guardas.

Decisión: no hay candidato adoptado ni ROI que pueda acreditarse desde esta atribución. La hidratación muestra coste de Python que merece descomposición acotada sobre la página seleccionada, conservando filas/relaciones y reglas. La inspección de DetailsForm actual confirma que su Meta ya contiene los campos románticos: no existe aquí una eliminación pendiente de campos profesionales de base_fields que pueda suponerse como mejora. Las variantes heredadas, permisos enlazados, barreras y planes genéricos rechazados siguen rechazados.

Una siguiente investigación debe distinguir materialización ORM/precargas/compilación del SELECT del coste propio de las guardas, y explicar estabilidad antes de cualquier contraste causal. Puede estudiar una página de24con fixture menor si declara que no mide cohorte10000/2000 ni cambia requisitos; el ROI final sigue exigiendo estabilidad y beneficio en ambas rutas sobre la cohorte aprobada. B07FAIL/900sbloqueado y ocho de18cerrados se conservan.
