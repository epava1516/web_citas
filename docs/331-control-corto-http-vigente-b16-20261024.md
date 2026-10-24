# B16-368 — Control corto HTTP de la candidata actual

Los [nueve casos dispuestos en330](330-conciliacion-exclusiones-b16-20261024.md) no verifican carga HTTP sostenida. La plantilla pública cambió tras el corte B07 y el p95histórico no mide la candidata actual. Se prepara el control corto con el instrumento vigente de mezcla combinada; no se repite la regresión funcional completa ni se optimizaQA.

## Protocolo congelable

Reutilizar opciones de combined291 —20261023-112344-928b8f94— con fuentes e intérprete actuales: run_capacity_environment.py --object-delivery --beta-http-short --beta-http-territorial --beta-http-combined-filters --beta-http-combined-population 10000 --cpu-budget 8. Base de runtime local inmutablef50e2f01874ebbd1147261160c6058c64bf2e8d26d50b2446c7549d2692b947b, ya validada en preflight361 y medida362; no retag/build/latest. Su diferencia con la imagen histórica impide atribuir una mejora exclusiva al código, pero no aceptar o rechazar la medida vigente según sus propios criterios.

Un solo test_owned_beta_http_calibration, sin omisiones. Población10000sintética, mezcla territorial/comercial/combinada del instrumento vigente,96slots de rutas; conservar controles nativos y coherencia antes/después. Ventana corta60s a20peticiones dinámicas/s:1200respuestas y subida limitada según instrumento. No cambiar mezcla, selección, pesos, GC, instrumentación, umbrales o contabilidad para facilitarPASS. Sinprofiler niotrotrabajopropiocompetidor. No usar datos reales ni proveedores.

Conservar8CPU/8GiB agregados, swap0 y almacenamiento propio≤20GiB; PostgreSQL17/Redis7.4/S3/proxy/Gunicorn4sync/workerBeat reales del controlador. Objetivos contractuales p95servidor<800ms y errores inesperados<1%, criterios de generador10/25/100ms, timeout65s/drain70s y resto del gate completo del marco vigente. Un fallo de infraestructura/contabilidad haceINVALID; un incumplimiento válido conservaFAIL. No trasladar elFAILshortantiguo aPASS por esta ejecución nueva.

## Espera persistente y retorno

El comparable completo tardó5718,356sJUnit, unos95minutos, además de preparación externa. La ventana60s no equivale a la duración total: sembrar/revisar/censar datos y comprobar68páginas tiene coste fuera de carga. Es referencia aproximada, no garantía. El lanzador conserva sus límites de tiempo oficiales; no reiniciar por observación agotada.

Antes de lanzar: fuente completa, protocolo/grafo/spec/helpers porSHA, selección esperada y relevo; comprobación estática y reciboTelegram. Lanzar en sesión persistente constdinDEVNULL y logs privados. ConfirmarPID/start_ticks del supervisor, runner/controlador y watcher/resumer/compactor; enviarTelegram previo indicando pausa y prueba persistente. Después pausar explícitamente el mismo goal. La shell notifica terminal tras limpieza y reactiva el mismo objetivo/creación/consumo, con marcador de cancelación respetado. Compactar al quedarpaused/idle; unACK no acredita compactación completada.

## Auditoría posterior y límites

Al retorno, antes de editar fuentes: comprobar originalreport/JUnit/errores/omisiones, manifiestos y protocolo, población/mezcla/contabilidad/generador, latencias y criterio completo, cuotas/peaks/noOOM, archivo y limpieza independiente, recibos y disparadores. Fuentes o proceso aún vivos implican esperar el mismo trabajo, nunca duplicarlo. ConservarFAIL/INVALID y diagnosticar antes de otra carga.

El corto no acredita900sni aceptaB16. No lanzar automáticamente la contractual al terminar: primero auditar e interpretar resultado y necesidad. Permanecen dos exclusionesHTTPpor conciliar,14/18puntos cerrados y proyecto enalfa. Grafo completo/diferencial de inventario y disposiciones finales pendientes. Estado de este documento: prerregistro, sin resultado ni lanzamiento acreditado todavía.
