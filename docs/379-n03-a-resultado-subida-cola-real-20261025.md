# N03A — referencia real de subida, cola y procesamiento

25 de octubre de 2026. [Prerregistro378](378-n03-a-prerregistro-subida-cola-real-20261025.md), candidataf2ff718, ejecución20261025-173129-0e1fb9b8. **1 PASS, 0 FAIL/ERROR/SKIP**, dosPOSTde subida observados con broker/worker reales y oráculo original completo. Ningún cambio de aplicación ni candidato de optimización en este lote. N03abierto, N00/N01/N06aceptados3/13, alfa.

[Auditoría de resultados, fuentes y eventos](evidencias/n03-a-subida-cola-auditoria-20261025.json), [reproducción](evidencias/n03-a-subida-cola-reproduccion-20261025.tar.gz).1738huellas intactas y selección exacta; datos sintéticos, PG17/Redis7.4propios y almacenamiento local privado. Workerprefork2con rolSQLrestringido verificado por conexión independiente, no eager; padreDjangoClientcon rol migrador del arnés, no prueba de autorizaciónSQLuniversal del servidor web.

## Referencias de tiempos por etapa

Una observación por transición, primera imagen en worker nuevo y reintento idéntico. La columna anterior no tiene referencia equivalente del flujo completo. No se mezclan fixtures eager, copia deBlobya ready o latencias del detector aislado para inventar un antes/después causal.

| Etapa | Antes equivalente | Subida nueva(ms) | Duplicado exacto(ms) | Mejora atribuible |
| --- | --- | ---: | ---: | --- |
| Client.request de subida | No medido | 170.196 | 81.640 | No evaluable |
| Publicación→inicio process_blob | No medido | 4.622 | No publica otra tarea | No evaluable |
| Ejecución process_blob | No medido | 1087.446 | No publica otra tarea | No evaluable |
| Ready/comparación observados tras petición | No medido | 1223.455 | 5.188 | No evaluable |
| Entrada→ready/comparación observados | No medido | 1393.651 | 86.827 | No evaluable |

SQLen conexión de la petición:35/20para subida nueva/duplicado; no cuenta SQLdelworker. CPUdelworkerprocess_blob742,017ms;su pared incluye trabajo real de proceso/detección de este caso. El refresco de publicación emitido por la primera petición tardó65,784msypublicación→inicio3,874ms; puede solaparse. No sumar petición, espera y tareas como fases seriales. El duplicado conserva su trabajo propio y no se presenta como aceleración de la subida original.

Readyobservado incluye drenaje por sondeo y verificaciones del arnés, no el instante exacto de disponibilidad; requiereBlobreadyyPhotocomparison_complete,no aprobación/publicación. El reloj deClient.requestexcluye multipart/cliente/red/navegador yfixtures, incluye backend/middleware/ingest. NoTCP/Gunicorn/Beat/carga,memoria por petición, p95/p99ni garantía productiva de latencia.

## Corrección y limpieza

El oráculo original pasó:1Blob/1Photo,2UploadAttempt,no aprobación automática,WebPsinEXIF,acceso privado/no-store,anónimo rechazado,original no expuesto yretirada con rechazo inmediato. La primera petición publica1tarea de imagen; el duplicado0. La correlación independiente de diarios de publicación y ejecución confirma losIDstécnicos/PIDs/relojes de los trabajos medidos; el caso registra diez ejecuciones totales contando los refrescos de preparación/limpieza, no diez subidas.

No se parchearon servicios ni se simuló el estado final. Se drenó/refrescó publicación fuera de los relojes para partir de cola quiescente: no es backlog natural o mezcla de producción. Sólo tiposprocess_blob/refresh_publication_state ySUCCESSno eager, sin error del observador. PIDs/start-ticks ausentes,workercerrado con código0,rolSQL/credenciales temporales retirados,claves ajenas conservadas y cero claves nuevas fuera delnamespace. Inventario independiente sin contenedores/redes/volúmenes propios ytemporal retirado. Telegramterminal confirmado.

QAseparado:JUnit48,630s,paso delrunner50,822s;montaje/fixtures/arranque/parada/aserciones no son latencia de producto. El informe semántico inicial de preparación tuvo formato wireinválido, rechazado y corregido antes del lanzamiento, con original preservado; no fue fallo de aplicación ni se repitió el caso por ello. Una inserción auxiliar prevista en el auditor no encontró su ancla; el auditor base válido y la comprobación de eventos separada se conservaron, sin repetir las pruebas funcionales.

## Detector histórico reutilizado, sin repetición improductiva

[Verificación independiente de reutilización](evidencias/n03-a-detector-reutilizacion-verificada-20261025.json):15fuentes relevantes idénticas y mediciones delJUnitoriginal327exactas, incluidospublication_signals/instrumento/fixtures/settings/dependencias. DosPASSoriginales con3,199770sdel detector para1000distintos/cinco positivos y14,392127spara100densos/100positivos.582,988sdeQAno son tiempo del detector ni del flujo nuevo. Una llamada por cohorte,firmaslistas/comparadorcaliente; no80000fotos,historialilimitado,colaconcurrente orecuperadorindexado. No se repitió para afirmar sólo frescura.

En densidad alta se observan6,368067sCPUdeconfirmación visual y3,709945sde registro protegido, frente0,067510sde comparación de firmas. No justifica un índice por defecto ni retirar candidatos/guards. Hipótesis acotadas pendientes de ficha y referencia/candidata equivalentes:reutilizar características de la imagen origen dentro de una sola llamada del detector, ocomponer comprobaciones de exclusión manteniendo locks/frescura. No se han adoptado ni se atribuye una mejora nueva por describirlas.

Siguiente:contrastar una hipótesis concreta con paridad completa y coste demostrado, y conciliar recuperación/reintentos de errores/retención/concurrencia con sus testigos antes de aceptarN03. El duplicado idempotente no prueba autoretry deOSError. Coordinar publicación conN07;N03permanece abierto,3/13aceptados. MOD09restante diferido por usuario367;sin apertura/proveedores ni campaña general de optimizaciónQA.
