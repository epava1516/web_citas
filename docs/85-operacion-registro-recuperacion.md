# Operación del registro de recuperación

Actualizado documentalmente: 2026-10-09. Instrucciones locales de recuperación; no autorización de producción. [Diseño84](84-restauracion-sin-reintroduccion.md), [recursos87](87-recursos-locales-recuperacion.md), [evidencia/componentes88](88-matriz-cierre-derechos.md). Custodia/autoridad externa, entorno/RPO-RTO y aceptación integral en [matriz83](83-auditoria-pendientes-cr09.md); estado único en [seguimiento17](17-seguimiento-desarrollo.md).

Comprobación/aplicación, destrucción física y limpieza de sesiones ya tienen implementación y ensayos locales reales PostgreSQL/medios sintéticos. Ejecutar exclusivamente sobre entorno de recuperación aislado, con autoridad vigente, exposición y entregas externas detenidas. `RECOVERY_MODE` bloquea HTTP/tareas de negocio según sus guards, pero exige reiniciar los procesos y no aísla CDN/proveedores por sí mismo. No reabrir hasta reconciliar los recursos exigidos.

## Claves y almacenamiento

El operador debe proporcionar `RECOVERY_ENCRYPTION_KEY` (clave Fernet) y `RECOVERY_SIGNING_KEY` (clave independiente de al menos32 bytes, codificada base64). Inyectarlas por el mecanismo reservado del entorno: no argumentos CLI, Git, ejemplos con valores reales ni logs. No hay claves automáticas para estos comandos. Conservar las claves necesarias fuera del conjunto de copias que se restaura y definir rotación/retención antes de producción.

El adaptador local exige directorios existentes con permisos0700 y archivos0600. Separar registros y checkpoint; mantener ambos fuera del backup de negocio que se está restaurando. Esta separación local no acredita supervivencia ante pérdida del servidor ni custodia externa. Para producción falta una autoridad de checkpoint vigente independiente: una firma válida no detecta por sí sola que alguien ha restaurado también una versión antigua de esa autoridad.

Inicializar genesis es una operación explícita de preparación de un registro nuevo. Un checkpoint ausente durante recuperación es un error, no una orden de reinicialización. El productor no crea el checkpoint externo automáticamente.

## Comprobación sin aplicar efectos

En una base/directorio de recuperación aislados, con exposición pública, workers/Beat de negocio y entregas externas detenidos, ejecutar:

```bash
uv run python manage.py check_recovery_ledger \
  --records-directory /ruta/reservada/registros \
  --checkpoint-directory /ruta/reservada/autoridad \
  --backup-ledger UUID_DEL_MANIFIESTO \
  --backup-sequence SECUENCIA_DEL_MANIFIESTO \
  --backup-head SHA256_DEL_MANIFIESTO \
  --expected-ledger UUID_DE_AUTORIDAD_VIGENTE \
  --expected-sequence SECUENCIA_DE_AUTORIDAD_VIGENTE \
  --expected-head SHA256_DE_AUTORIDAD_VIGENTE
```

Estos valores proceden del manifiesto de backup verificado. El comando no verifica todavía por sí mismo dicho manifiesto ni implementa el aislamiento operativo; son condiciones que debe cumplir el ensayo. No sustituirlos por los valores más recientes para omitir operaciones posteriores al backup.

El comando verifica cadena/cifrado/checkpoint, estructura tipada de todos los recibos y propiedad de las referencias existentes en PostgreSQL. Devuelve solo número de eventos y marcadores `effects_applied:false` y `publication_authorized:false`. Falta de clave/checkpoint o evidencia inválida debe mantener aislamiento. Un resultado correcto no demuestra que los efectos estén reaplicados, los archivos estén eliminados ni que pueda reabrirse la web.

## Exportación y reintentos

El productor persiste una única representación cifrada/firmada por evento. El exportador local confirma primero el registro/checkpoint durable y después `exported_at` en PostgreSQL. No hay atomicidad entre archivos y base: si falla la confirmación DB, los archivos pueden existir. Un reintento verifica exactamente ese registro y confirma sin duplicarlo. Una base retrocedida respecto al checkpoint independiente exige reconciliación; no sobrescribir ni reiniciar el registro para desbloquearla.

La conexión es un servicio interno, sin endpoint público ni tarea automática activada. Falta un comando operacional de exportación con configuración explícita, supervisión y ensayo de worker cuando se adopte ese recorrido. Los límites actuales de paquete/cadena requieren diseñar paginación con checkpoints antes de excederlos; nunca truncar eventos como solución.

## Aplicación aislada y destrucción física0100

El comando `apply_recovery_ledger` reutiliza las opciones y claves de la comprobación. Exige `RECOVERY_MODE=1` y conexión sin transacción externa. Reiniciar cada proceso con el modo explícito, mantener exposición y entregas externas detenidas; el flag no aísla CDN ni proveedores. Ejecutar únicamente en la base/directorio aislados de recuperación:

```bash
uv run python manage.py apply_recovery_ledger \
  --records-directory /ruta/reservada/registros \
  --checkpoint-directory /ruta/reservada/autoridad \
  --backup-ledger UUID_DEL_MANIFIESTO \
  --backup-sequence SECUENCIA_DEL_MANIFIESTO \
  --backup-head SHA256_DEL_MANIFIESTO \
  --expected-ledger UUID_DE_AUTORIDAD_VIGENTE \
  --expected-sequence SECUENCIA_DE_AUTORIDAD_VIGENTE \
  --expected-head SHA256_DE_AUTORIDAD_VIGENTE \
  --media-limit 100
```

La cadena completa y los recibos tipados se validan antes de aplicar cambios DB. La destrucción física vuelve a verificar la autoridad independiente y las referencias compartidas; el lote admite1–100 trabajos. El JSON informa `applied`, `media_completed`, `pending_media_jobs`, `exhausted_media_jobs` y siempre `publication_authorized:false`. Un lote completado no acredita reconciliación de cachés, recursos externos ni aceptación para reabrir. Repetir contra la misma autoridad para procesar el resto; trabajos fallidos conservan backoff y presupuesto de cinco intentos, sin reiniciarlos al repetir el comando. Trabajos agotados requieren investigación reservada y una reparación controlada, no reinicio automático.

Un error puede ocurrir después de confirmar los efectos DB o borrar parte de los archivos. No hay rollback de archivos ni atomicidad entre DB y almacenamiento. Mantener aislamiento, revisar auditoría privada y repetir con la misma autoridad tras resolver la causa. No regenerar genesis/checkpoint ni recuperar colas antiguas para desbloquear. Una firma válida de un checkpoint local no demuestra su vigencia externa; esa autoridad operacional sigue pendiente para producción.

## Referencia independiente vigente

Los comandos check_recovery_ledger y apply_recovery_ledger exigen expected-ledger/sequence/head además del checkpoint del backup. Obtenerlos de la autoridad operacional independiente antes de recuperar; no derivarlos del archivo que se está validando ni de la copia restaurada. RecoveryStore compara bajo el mismo lock la identidad exacta del checkpoint firmado con la referencia esperada antes de descifrar/aplicar efectos. Firma válida con checkpoint antiguo o distinto se rechaza. Si el registro avanza mientras se recupera, mantener aislamiento y obtener una referencia vigente mediante procedimiento controlado; no ignorar la discrepancia. El mecanismo local verifica una referencia suministrada, no acredita su procedencia/vigencia externa ni reemplaza contratación/custodia de una autoridad fuera del servidor.

## Destrucción de sesiones restauradas

Después de reconciliar los recibos verificados, ejecutar `clear_recovery_sessions` en la misma base aislada con las opciones records-directory, checkpoint-directory, backup-ledger/sequence/head y expected-ledger/sequence/head usadas para aplicar el registro. Exige RECOVERY_MODE=1 y backend de sesiones DB; cada recibo debe coincidir con una RecoveryApplication cifrada y su digest, alcance y sujeto. Una auditoría ausente/corrupta impide borrar sesiones.

Elimina todas las filas `django_session` de esa base, sin descifrar ni devolver contenidos. Es una operación global de restauración: visitantes, titulares y moderadores deben autenticarse de nuevo; no supresión individual de un titular. Conservar el JSON agregado `sessions_deleted`/`publication_authorized` como evidencia reservada. Repetir devuelve0 si no reaparecieron sesiones; no toca cuentas/anuncios ni otras bases. El resultado nunca habilita publicación ni sustituye reconciliación de cachés o recursos externos.

## Transición del namespace del broker

La primera entrega de TASK_QUEUE_GENERATION cambia del namespace sin prefijo a clasificados:v1: y cola por defecto clasificados. Mantener las colas antiguas fuera del consumo; no migrar automáticamente sus mensajes ni usar FLUSHDB/FLUSHALL. Si hay mensajes pendientes, inventariar cantidades y reconstruir únicamente las operaciones todavía autorizadas desde DB reconciliada mediante sus reglas/idempotencia. Una generación nueva necesita ser diferente de la última utilizada antes de restaurar, y quedar retenida fuera del backup; v1 es solo el valor inicial, no el valor para todas las recuperaciones.

## Estado de publicación tras restaurar (MOD-05)

El estado de publicación almacenado (`listings_publicationstate`) y sus marcas (`listings_publicationdirty`) se mantienen mediante triggers. Una restauración completa con `pg_dump`/`pg_restore` recupera datos, estado y marcas de la misma instantánea consistente, y los triggers se crean después de cargar los datos. Una restauración solo de datos, selectiva, con `--disable-triggers` o con `session_replication_role=replica` puede dejar estado incoherente. En todos los casos, antes de salir de `RECOVERY_MODE` y servir tráfico, ejecutar:

```sh
python manage.py refresh_publication_state --all
```

Marca toda la población y la recalcula con la regla nativa y el código desplegado, en una sola transacción. El barrido horario (`sweep_publication_state`) es solo una red de seguridad posterior, no sustituye este paso.

## Historial de implementación y ensayos

[Copia íntegra anterior](17-historial/2026-10-09-85-operacion-registro-recuperacion-antes-organizacion.md): conserva estados parciales, comandos e informes de la entrega0100 y posteriores, sin reescribir sus veredictos. Esta reorganización no ejecutó recuperación, borrado, migraciones ni ensayos. [Inventario de copias](historial-documentacion.json).

## Verificación en el CI propio —2026-10-09

Se adaptó la prueba de dump/restore para usar el servidor de la conexión de ensayo, sin invocar el Compose normal. El runner identifica su contenedor PostgreSQL desechable; el test valida nombre y puerto contra su conexión antes de ejecutar herramientas PG17. Fuera del runner se requieren clientes PostgreSQL locales y la conexión de prueba explícita. La base restaurada tiene nombre único y se elimina con comprobación de ausencia.

[Final N2](evidencias/restauracion-ci-mod05-final-20261009.json):2 recorridos PG/medios/comercial PASS,60,57s en conjunto,0 skips, fuentes iguales y recursos retirados. Conserva dump SHA256, inventario completo de medios, corte absoluto/edad máxima y tiempos de restaurar medios/PG/reconciliar; objetivos de diseño RPO1h/RTO8h cumplidos en estos pequeños fixtures, sin acreditar cadencia/capacidad de producción. Checkpoint independiente sintético, autoridad incorrecta rechazada, supresión reaplicada, medios propios retirados y archivos restantes exactos, otro sujeto y evidencia comercial preservados sin reactivar promoción.

El recorrido crea deliberadamente estado derivado incoherente con triggers desactivados solo en la base restaurada propia, marca toda la población y verifica los triggers activos durante reconciliación. Después ejecuta realmente `refresh_publication_state --all` antes de salir de recuperación: marcas vacías, versión vigente y anuncio suprimido no elegible/404. Primera pasada falló por una referencia inversa mal escrita en el nuevo test; los dos intermedios PASS no reunían todavía todo el inventario/comando durable. Se conserva cada resultado; únicamente la pasada final acredita este alcance. N3 común, custodia y operación productiva siguen pendientes.
