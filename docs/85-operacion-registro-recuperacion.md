# Operación del registro de recuperación

Estado: comprobación y exportación locales implementadas; restauración completa pendiente. Requisitos y diseño: [docs84](84-restauracion-sin-reintroduccion.md). No es autorización para abrir producción.

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
  --backup-head SHA256_DEL_MANIFIESTO
```

Estos valores proceden del manifiesto de backup verificado. El comando no verifica todavía por sí mismo dicho manifiesto ni implementa el aislamiento operativo; son condiciones que debe cumplir el ensayo. No sustituirlos por los valores más recientes para omitir operaciones posteriores al backup.

El comando verifica cadena/cifrado/checkpoint, estructura tipada de todos los recibos y propiedad de las referencias existentes en PostgreSQL. Devuelve solo número de eventos y marcadores `effects_applied:false` y `publication_authorized:false`. Falta de clave/checkpoint o evidencia inválida debe mantener aislamiento. Un resultado correcto no demuestra que los efectos estén reaplicados, los archivos estén eliminados ni que pueda reabrirse la web.

## Exportación y reintentos

El productor persiste una única representación cifrada/firmada por evento. El exportador local confirma primero el registro/checkpoint durable y después `exported_at` en PostgreSQL. No hay atomicidad entre archivos y base: si falla la confirmación DB, los archivos pueden existir. Un reintento verifica exactamente ese registro y confirma sin duplicarlo. Una base retrocedida respecto al checkpoint independiente exige reconciliación; no sobrescribir ni reiniciar el registro para desbloquearla.

La conexión es un servicio interno, sin endpoint público ni tarea automática activada. Falta un comando operacional de exportación con configuración explícita, supervisión y ensayo de worker cuando se adopte ese recorrido. Los límites actuales de paquete/cadena requieren diseñar paginación con checkpoints antes de excederlos; nunca truncar eventos como solución.

## Trabajo necesario para restauración completa

Implementar reaplicación tipada con auditoría/idempotencia y trabajos de destrucción física recuperables, conservar terceros compartidos, invalidar sesiones/cachés y reconstruir tareas sin reenviar mensajes ni republicar. Ensayar backup y restauración reales PostgreSQL/medios anteriores a la supresión, comprobar ausencia de exposición y archivos afectados y medir RPO/RTO. No interpretar pruebas sobre una base sintética actual como ese ensayo.
