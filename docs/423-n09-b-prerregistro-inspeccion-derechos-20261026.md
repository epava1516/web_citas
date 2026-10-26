# N09B — prerregistro de autoridad en inspección privada de derechos

Antes del diagnóstico y sin cambio de aplicación. Base09028b5, correcciones de [422](422-n09-a-correccion-verificada-recuperaciones-20261026.md) preservadas; N09 sigue abierto con139IDs y8/13bloques aceptados. Corte previo del grafo:2.042fuentes exactas,SHA256 `13bc8befc0d8eca1f5cdd562cc7f5677e546de76b8e7b782815b5424562d1efc`.

## Condición de fuente, todavía no fallo runtime

`rights.inspect` comprueba `allowed(request)` antes de `locked_case`; después de adquirir el caso comprueba ámbito con el mismo `request.user`, descifra `encrypted_payload` y registra `RightsAccess`. El guard de ámbito no sustituye una lectura actual de permisos/cuenta/MFA. El análisis de52rutas de derechos y la revisión principal señalaron esta condición; no se acepta un defecto observado sólo por semejanza con avisos/medios.

## Único diagnóstico previsto

Añadir un caso explícito, serial y no producción: operador legítimo con MFA y permiso `review_rights_request`, solicitud sintética no vinculada y sesión preparada antes de bloquear. La fixture nativa `test_rights_linking.ready` crea/asigna/inspecciona el caso; refrescar su estado antes de capturar referencia. Esa preparación puede crear su auditoría legítima previa, que debe conservarse.

La conexión principal mantiene `SELECT FOR UPDATE` de ese `RightsRequest`. Otro hilo realiza un POST real `/en/moderation/rights/<id>/` con propósito válido. Un observador SQL pasivo captura el PID efectivo del intento de lock; comprobar `pg_stat_activity`/Lock y el PID propio en `pg_blocking_pids` antes de retirar el permiso. La retirada se confirma con una nueva instancia User y se confirma transaccionalmente al liberar el lock. Sin parches de guard, ORM de negocio, descifrado ni respuesta.

Oráculo:403, snapshots de solicitud/acciones/accesos intactos, estado mínimo igual, hilo/conexiones cerrados y transacción liberada. Se reutiliza el observador de esperas de419/421; el guard de selección del nuevo archivo será propio para evitar SKIP por `__file__` ajeno. Registrar sólo conteos/huellas/estado/status/PIDs propios/tiempo de espera, nunca payload, propósito, correo o datos de sujetos. Un200con nueva auditoría tras revocación confirmada sería evidencia del defecto; fallo antes de observar espera o revocación sería instrumental y debe separarse.

## Ejecución y decisión

Django Expert/Reviewer, revisión del instrumento, lint y grafo con AST/semántica actuales antes de congelar. Un solo caso por runner oficial con PostgreSQL/Redis propios desechables, parser nativo, aislamiento de broker, observación HTTP y timeout900s. Avisos Telegram de inicio/terminal con recibos y limpieza comprobados. No repetir29casos aceptados ni QA global/exportación larga por añadir documentación.

Conservar cualquier FAIL/ERROR/SKIP original. Si se confirma, prerregistrar una corrección acotada de lectura actual de autoridad antes de descifrar/auditar y su regresión pertinente; no modificar la aplicación antes del diagnóstico. Los tiempos incluyen bloqueo inducido, no son latencia normal, mejora de rendimiento ni plazo humano. Otros posibles gaps de hold/inventario/verificación/rectificación/reclamaciones requieren su propia evaluación. N02 restante al final; N10 compartido y N12–N14condicionados, sin proveedor ni apertura.
