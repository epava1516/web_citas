# B07 — Modo específico beta HTTP contractual

Estado: modo implementado, focales auditados y calibración real188completada; ningún ensayo900s lanzado. B07 abierto, ocho de dieciocho puntos cerrados.

Los dos cortos acotados [184](184-corto-beta-cuotas-beat-20261021.md) y [186](186-confirmacion-unica-corto-acotado-b07-20261021.md) pasan por separado y agotan la confirmación prevista. El modo measure existente sigue siendo entrega de expedientes; no se reutiliza como beta900.

## Implementación y criterios

Nuevo selector exclusivo beta-http-contractual en el handoffVPS y controlador. Requiere topología owned8CPU/objectdelivery, imagen inmutable y todas las fronteras DB/broker/kernel del corto. Incompatible con funcional/corto/preflight/expedientes/perfiladores; ningún cambio de cuotas, servicios normales ni producto. Propagación CAPACITY_BETA_HTTP_CONTRACTUAL a fixture, estadísticas, rol runtime y servidor; mismos cuatro workers sync/un hilo/timeout60, Celeryprefork2 y Beat reales.

Escenario900s/20RPS/18000dinámicas,10000perfiles/2000derechos nativos, mezcla tercios listado/búsqueda/ficha ESEN alternando. Quince borradores distintos del anunciante sintético, creados por ORM nativo antes de refresh; mismo multipart sintético separado en t=0,60,…,840s, como el arnés contractual histórico. No quince reintentos sobre una misma foto: cada borrador debe terminar con una Photo y un UploadAttempt accepted/duplicate, no repeat. Sin reutilizar preparación mutable entre ejecuciones.

Corto y funcional conservan sus tamaños, rutas, una subida y resultados anteriores. El largo registra beta_http_contractual y workload_checks propios. PASS específico BETA_HTTP_CONTRACTUAL_PASS_NOT_GLOBAL, FAIL válido BETA_HTTP_CONTRACTUAL_FAIL, generador/contabilidad inválidos INVALID_BETA_HTTP_CONTRACTUAL; setup incompleto conserva ERROR. No confundir salida0 con aceptación B07.

Mismos límites del generador10/25/100ms, cero omitidas, timeout65/drain70, errores<1%, p95observable<800ms, contabilidad reconciliada, pendientes ventana≤20 y finales0. Quince subidas302 y persistencia de cada una. Tiempo máximo de workload+drain970s; límite del paso pytest3600s para preparación nativa y servidor; vida app4200s, sin ampliar recursos. Mismas lecturas frías, faseBeat+5s y GC antes del reloj sinfreeze; mismos observadores declarados, sin profiler de solicitud.

## Verificación antes de carga

Primero revisar exclusividad/handoff/recursos mediante pruebas focales, guardas de fixture y estadísticas, con PostgreSQL real donde corresponda. Refrescar AST y semántica dirigida antes del hito y conservar negativos. Después preparar una calibración funcional real de las quince subidas sobre quince borradores y su circuito de persistencia, sin esperar900s ni presentarla como carga contractual. Su mecanismo y temporización se fijarán antes de ejecutarla; no reducir espaciado del ensayo contractual ni convertir esa calibración en SLO.

Antes del largo: preregistrar comando definitivo, fuentes/imagen/protocolo y recursos, comprobar avisos y ausencia de entornos propios anteriores. Estimación preparación observada unos14min más15min de carga y drenaje, no horas; mantener goal activo dentro del presupuesto. FAIL/INVALID/ERROR detienen secuencia; no relanzar por expiración de observación. No ejecución automática por este documento.

Limitaciones: una sola distribución municipal no cubre diversidad territorial, filtros combinados, páginas profundas, backlog ni PRODUCTION/checked; pendientes de la [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md). Las series por servicio/edad de colas siguen pendientes según su alcance. CPU total incluye preparación; memoria es cota conservadora, no pico simultáneo; overhead de observadores no aislado. Scope genérico heredado no acredita aceptación global. No proveedores, publicación, participantes reales, N3 ni aceptación beta por este modo.

## Focales terminales auditados

Invocación inicial rechazada por falta de --native-source antes de crear entorno o ejecutar pytest; exit2 y aviso Telegram enviado. Se corrigió la invocación, sin cambios de código ni repetición de casos ya ejecutados.

Run `20261021-201857-e26aa1eb`:33PASS/0FAIL/0ERROR/0SKIP,64,196sJUnit. [Auditoría](evidencias/b07-beta900-focal-20261021-audit.json) verifica fuente congelada, tres modos beta exclusivos, cuotas, rol runtime real PostgreSQL, estadísticas y transporte;628app/config/templates idénticos, contenedores/temporal/procesos retirados y Telegram terminal enviado. No atribuir a estos casos ejecución del largo ni de quince subidas reales: esa calibración sigue pendiente.

El grafo previo183 incorpora AST cambiado y semántica de este protocolo. Las pruebas no cambian umbrales ni aceptan B07; siguiente trabajo es fijar el modo funcional de quince subidas y validar persistencia real antes de preparar el lanzamiento900s.

Estado posterior: [188](188-calibracion-quince-subidas-beta-b07-20261021.md) verifica24focales y quince ingestiones reales sobre quince borradores; preparación del protocolo definitivo900s pendiente. Sus fuentes runtime coinciden con su focal y los33anteriores conservan su corte, no una única batería34/57. No900ejecutado ni aceptaciónB07.
