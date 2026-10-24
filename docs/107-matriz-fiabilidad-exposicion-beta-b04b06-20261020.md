# Fiabilidad de renovación y exposición — B04–B06

Fecha:2026-10-20. Estado: B04/B05/B06 aceptados técnicamente en local por [acta13](actas/13-beta-b04b06-aceptacion-local-20261020.md). Continúa el [roadmap103](103-roadmap-beta-clasificados-20261020.md), tras el [cierre local B02/B03](actas/12-beta-b02b03-aceptacion-local-20261020.md). No beta global ni apertura.

## Reglas conservadas y aclaradas

Renovar es gratuito, exige confirmación de la revisión aprobada, se abre siete días antes de caducar o tras caducidad, fija treinta días desde la renovación y actualiza fecha editorial. Conserva la pausa, persona/anuncio/revisión; no crea pedido ni Top/Premium. Retirado exige nueva revisión. Disponible ahora es opt-in de cuatro horas, sin garantía de respuesta o cita. El panel explica estas reglas ES–EN; no se han cambiado sus duraciones ni las transacciones.

Autosubida es señal comercial, no renovación: conserva vigencia, fecha editorial, revisión y versión de ciclo de vida. Intervalo/cupo diario pertenecen al snapshot del pedido, por ventana UTC e idempotencia; no cargos recurrentes. Los pedidos y pagos siguen sintéticos, deshabilitados en producción y recuperación.

Exposición sintética vigente: resultados elegibles y compatibles primero; Premium antes de Top, rotación SHA256(díaUTC/ID) dentro del tipo; veinticuatro resultados por página, sin cupo adicional de posiciones por tipo ni posición garantizada. Cada publicación aparece una vez aunque tenga varios derechos. El bloque orgánico mantiene relevancia de texto; sin texto admite la señal de autosubida. Estas son reglas de ensayo ya implementadas, no cupos o condiciones comerciales reales autorizados. La configuración comercial definitiva continúa pendiente de activación separada.

## Matriz de evidencia requerida

| ID | Criterio | Evidencia conciliada PASS local en candidata043105 |
| --- | --- | --- |
| F01 | Renovación7/30, confirmación, pausa/caducidad/retiro, reintento y carreras; nueva ordenación orgánica sin promoción | test_lifecycle y test_beta_public_surfaces: renovación ES–EN |
| F02 | Panel y vocabulario ES–EN distinguen renovar/autosubir/disponibilidad sin promesas de cita | test_beta_public_surfaces: texto del panel y navegador de lifecycle |
| F03 | Misma autoridad en listado/ficha/foto/favoritos/sitemap/promociones; retirada antes y después de refresco | test_beta_public_surfaces: doce causas por ES–EN, con/sin promociones; test_favorites/test_sitemaps y paridad de estado |
| F04 | Patrocinio explícito, filtros, desempate/rotación estable, paginación completa sin duplicados | test_promotion_exposure/test_promotion_pagination_rotation/test_promotion_public_mobile |
| F05 | Autosubida con intervalo/cupo, replay y revocación bajo locks; conserva estado editorial | test_promotion_exposure/test_promotion_bump_races/test_promotion_order_races |
| F06 | Worker y Beat reales consumen caducidad y autosubida; idempotencia y cierre de procesos propios | test_beta_exposure_worker: PostgreSQL/Redis del runner, procesos Celery propios, recibo local de tareas y logs originales |
| F07 | Modo de prueba, permisos, snapshots y recuperación no reactivan promociones excluidas | test_promotion_orders/test_promotion_order_http/test_promotion_order_mobile_agency/test_promotion_recovery |

Las doce causas iniciales son pausa, retirada, caducidad, consentimiento revocado, gestor cambiado, edad fallida, contrato heredado/desconocido, tarifa profesional, foto retirada, teléfono no verificado y catálogo ausente. Se conserva un perfil par elegible. El refresco se retrasa sólo en la preparación de la prueba: PostgreSQL y la guarda pública siguen reales. La matriz no sustituye las demás garantías de derechos y restricciones del contrato.

## Ejecución y límites

Selección focalizada inicial preregistrada en `artifacts/beta-exposure-20261020/focused-selection.json`. Fuentes congeladas, PostgreSQL/Redis propios, navegador donde interviene. El worker usa exclusivamente la base de pytest y una cola de la generación aislada del caso; procesos y Beat se retiran en finally y sus recibos/logs se conservan en el directorio del runner. Un `.run()` síncrono no cuenta como worker real. La configuración temporal de Beat de un segundo es de ensayo, no la frecuencia productiva. La configuración sintética de autosubida1440min/1diario se fija antes del pedido; no altera snapshots emitidos. Para disponer de una ventana ya iniciada se preparan fechas sintéticas dos días atrás; en la candidata común se conserva exactamente la duración del pedido al desplazar ambos extremos. No es evidencia de cobro o recepción real. El cambio legítimo de día UTC no se convierte en falso duplicado.

Verificar resultado terminal, todos los selectores y variantes, cero fallos/omisiones en el alcance de aceptación, igualdad de fuentes, limpieza y recibo Telegram. Conservar negativos y corregir sin debilitar autoridad ni criterios. Después conciliar una candidata común afectada y los siete criterios antes de cerrar B04–B06. La línea de base/capacidad y las optimizaciones permanecen en B07–B11; operación B12–B14 y aceptación global B16 no quedan acreditadas por estos ensayos.

## Primer resultado focalizado

Ejecución040943-5635ec36:61PASS/0FAIL/0ERROR/0SKIP, nueve selectores, PostgreSQL/Redis/Chromium reales locales. [Auditoría focalizada](evidencias/b04b06-focused-terminal-audit-20261020.json): fuentes iguales de nuevo, servicios/temporal/procesos del runner retirados y recibo Telegram confirmado. El worker y Beat propios terminaron con código0; cuatro tareas explícitas constan como completadas en el log original, Beat despachó caducidad y comprobación de autosubida, y el estado editorial permaneció igual. La configuración de1440min/1diario pertenece al fixture, no a una oferta real.

Antes de la candidata común se ajusta únicamente el fixture temporal para conservar la duración exacta del derecho al preparar su inicio histórico. No cambia código de negocio. La selección común afectada `artifacts/beta-exposure-20261020/common-selection.json` incorpora veinte selectores: permisos/HTTP/agencias/pedidos, carreras, restricciones de privacidad/fotos, estado derivado y restauración comercial, además de los focalizados. Ese artefacto local es ignorado; el resultado del runner conservará la selección literal. No sumar las ejecuciones como una batería única. B04–B06 siguen abiertos hasta conciliar F01–F07 con candidata común y sus límites.

## Resultado común y conciliación terminal

Candidata `20261020-043105-4bdc27be`: **139PASS/0FAIL/0ERROR/0SKIP**, veinte selectores y dos workers. [Auditoría común](evidencias/b04b06-common-terminal-audit-20261020.json) conserva por F01–F07 las aserciones revisadas y los nodeids ejecutados. Fuentes comparadas de nuevo, contenedores/temporal/procesos retirados y Telegram entregado. Worker y Beat reales terminaron con código0; cuatro tareas explícitas completadas, una caducidad por worker y otra por Beat, autosubida única y relectura por Beat; vigencia/fechas/revisión editorial conservadas. Derecho sintético de diez días conserva duración del snapshot.

Negativo041902:136PASS/3ERROR/0FAIL/0SKIP, conservado en [evidencia negativa](evidencias/b04b06-common-negative-041902-20261020.json). La fixture compartida conflict enviaba consentimiento de publicación dev-1, rechazado correctamente. Ahora consulta el documento activo; no se relajan guardas. [Correctiva042802](evidencias/b04b06-corrective-terminal-audit-20261020.json):24PASS/0FAIL/0ERROR/0SKIP para fixture y sus seis consumidores directos; limpieza/fuentes/Telegram auditados. La candidata común posterior incluye los tres casos afectados. No sumar ejecuciones como una sola batería.

F04 verifica paginación completa con cuarenta perfiles y veintiocho patrocinados, filtros de texto y rotación diaria ES–EN, con patrocinio móvil visible. La prioridad entre varios derechos de un mismo anuncio se revisó en código: ranked mantiene una entrada por anuncio y elige la prioridad superior; el fixture de paginación concede un derecho por perfil patrocinado. No se atribuye a ese fixture una variante de derechos solapados.

**B04–B06 aceptados en su alcance técnico local.** B00 residual y B07–B17 siguen pendientes; B15 opcional. Capacidad, operación y beta global requieren sus criterios propios. Sin proveedores, pagos o datos reales ni apertura.
