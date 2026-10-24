# B13 — Retorno beta con escrituras y workers reales

Estado: PASS local acotado, B13 abierto y siete de18puntos cerrados. Complementa el [ciclo de lectura145](145-estrategia-rollback-beta-b13-20261021.md) y la [matriz141](141-continuidad-moderacion-beta-b13-20261021.md).

[Auditoría terminal](evidencias/b13-rollback-writes-terminal-audit-20261021.json): mismo PostgreSQL17, Redis propio y volumen privado durante actual80d66b10e1f4 → anterior980bcc133069 → actual80d66b10e1f4. IDs completos en la evidencia. Las fuentes runtime siguen iguales al corte041741;724archivos comprobados por huella fresca. No cambio de producto ni descenso de esquema.

## Operaciones verificadas

| Fase | Escritura de aplicación | Consumer real de Redis | Resultado |
|---|---|---|---|
| Actual | Crear borrador y editar detalles; pausa del anuncio | Worker de imagen anterior | Cinco mensajes antes de arrancar; estado pausado derivado y ficha/foto404 |
| Anterior | Editar el mismo borrador; reanudar | Worker de imagen actual | Tres mensajes antes de arrancar; estado público vigente y ficha/foto200 |
| Actual | Tercera edición del mismo borrador; disponibilidad | Worker de imagen actual | Tres mensajes antes de arrancar; disponibilidad guardada, estado vigente, ficha/foto200 |

Las escrituras pasan por vistas autenticadas Client WSGI con sesión sintética válida. No se presentan como navegación TCP autenticada. Las fichas ES/EN y fotos sí se consultan por TCP real entre una sonda y Gunicorn dentro de la red Docker interna:18fichas y6fotos; perfiles de consentimiento revocado y contrato histórico404 en todas las fases. No puertos públicos ni proveedores externos.

Tres acciones de ciclo de vida y seis reintentos exactos terminan con una, dos y tres acciones persistidas respectivamente; ningún replay repite el efecto. El mismo borrador conserva los títulos entre versiones, contrato romántico, tipo vacío y etiqueta explícita. Pares y revisiones/fotos aprobadas se comparan por huella antes de renovar el inventario de cambios permitidos. Personas, blobs, catálogo y migraciones permanecen iguales; ocho archivos de medios conservan bytes. Las nueve tablas se comparan entre fases contra la línea base posterior a las escrituras previstas, no se afirma que todas permanezcan inmutables durante una edición.

## Evidencia del worker y marcas de estado

Se publica explícitamente una tarea real refresh_publication_state por fase; se exige ejecución no eager, mensajes reales pendientes y marcador dirty antes del worker. Tras el consumo, se exige cola vacía, cero marcadores dirty, coincidencia de todas las columnas derivadas con expected_states de la regla nativa y éxito del identificador de tarea concreto en el log del worker. No basta un proceso activo ni se acredita con este control el encolado de todas las señales automáticas.

La pausa y reanudación cambian elegibilidad y requieren computed_at posterior a la escritura. La disponibilidad no cambia las columnas derivadas: store utiliza ON CONFLICT con WHERE IS DISTINCT FROM y conserva computed_at cuando los valores no cambian. En esa fase se exige precisamente la conservación de la marca anterior junto con consumo y estado nativo vigente. No se altera producto para producir una actualización innecesaria.

El relevo es secuencial: cola pendiente, arranque de consumidor de versión identificada, verificación y parada normal antes del siguiente cambio. No se mata un worker a mitad de tarea ni se demuestra ausencia de interrupción con tráfico concurrente. No se extiende la prueba a futuras migraciones destructivas, esquema alfa o reconciliación de grants con la imagen anterior defectuosa.

## Negativos y cierre de evidencia

Cuatro cortes negativos propios conservados: consulta de PublicationDirty usando listing en vez de listing_id; control de cola pasiva sin mensajes; espera final basada en timestamp siempre nuevo; repetición diagnóstica que acreditó dirty0/cola0 con marca anterior. El código store explica ese último resultado. Se corrigieron el arnés, la publicación explícita de la tarea y el criterio de timestamp acorde al cambio de valores, sin relajar guardias de dominio. Los dos primeros cortes no ejecutaron un worker y los dos siguientes sólo completaron las primeras dos fases; no son un ciclo íntegro PASS.

El último corte completa las tres fases. Contenedores, workers, red y volumen propios ausentes por inspección fresca; Telegram terminal PASS confirmado. Las imágenes y artefactos locales se conservan como material del ensayo. B13 mantiene pendientes dependencias HMAC transitivas, retención/custodia externa y procedimientos de credenciales/rotación restantes. Apertura y operadores reales siguen en B17.
