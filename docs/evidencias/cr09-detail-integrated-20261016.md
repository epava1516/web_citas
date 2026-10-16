# Integración del detalle público — 2026-10-16

La selección integrada `20261016-102816-814fe5d0` terminó con **46 pruebas aprobadas**, cero fallos, errores u omisiones; JUnit443,597s. [Recibo con fuentes y verificación independiente](cr09-detail-integrated-20261016.json).

El detalle abre una transacción propia REPEATABLE READ READ ONLY antes de hidratar y mantiene ese snapshot hasta renderizar. Si hereda una transacción, conserva la ruta nativa. Es un cambio explícito de semántica en la transacción propia; no se eliminan validaciones ni se decide acceso mediante PublicationState.

La selección cubre dos transiciones atómicas adversariales y sus controles negativos RC, cuatro ámbitos de aislamiento y restauración,19 comparaciones de paridad, seis guardas de usuario, contexto compartido, discovery, nueve límites de agrupación, propiedad de revisión y planificación. Los controles negativos RC reproducen deliberadamente la exposición del prototipo rechazado. No representan comportamiento aceptado del producto.

El primer intento integrado conserva su fallo de contaminación del parche render y su interrupción controlada. La correctiva modifica sólo el arnés y repite toda la selección. El producto mantiene el mismo hash entre ambos intentos.

Fuentes, desaparición de procesos identificados, temporal y contenedores propios fueron comprobados independientemente. PostgreSQL real y datos sintéticos; sin producción. El ROI previo corresponde a agencia y clon de agencia; individual está cubierto funcionalmente, sin medición ROI propia. No hay nueva métrica p95: el último corto limpio sigue en1,052089655s, FAIL frente a<0,8s. Esta selección no acredita regresión completa de versión final, N3 ni cierre CR09.
