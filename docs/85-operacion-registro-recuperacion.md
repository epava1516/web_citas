# Operación del registro de recuperación

Estado: comprobación/exportación y aplicador inicial locales implementados; destrucción física y restauración completa pendientes. Requisitos y diseño: [docs84](84-restauracion-sin-reintroduccion.md). No es autorización para abrir producción.

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

## Trabajo necesario para restauración completa

Implementar reaplicación tipada con auditoría/idempotencia y trabajos de destrucción física recuperables, conservar terceros compartidos, invalidar sesiones/cachés y reconstruir tareas sin reenviar mensajes ni republicar. Ensayar backup y restauración reales PostgreSQL/medios anteriores a la supresión, comprobar ausencia de exposición y archivos afectados y medir RPO/RTO. No interpretar pruebas sobre una base sintética actual como ese ensayo.

Aplicador0100 inicial disponible como servicio interno, sin comando de aplicación activado. Requiere `RECOVERY_MODE=1`; ese flag bloquea HTTP Django, pero no detiene workers/Beat automáticamente. Mantenerlas detenidas y no reabrir: el resultado del servicio conserva `publication_authorized:false`. Las primeras pruebas reintroducen datos por ORM, no sustituyen el ensayo pg_dump/medios.

Motor físico0100 implementado como servicio interno que exige modo recuperación y registro independiente verificable. Primer ensayo pg_dump/pg_restore y archivos sintéticos correcto; base temporal eliminada. No hay aún comando final de reaplicación/habilitación ni ejecución real Celery/Beat de recuperación. Mantener aislamiento hasta cubrir la matriz completa.

Aislamiento0100: dos pruebas con worker y Beat reales correctas (43.420s). Worker ignora la tarea sintética en recuperación y la ejecuta con PostgreSQL en modo normal; las16 tareas de negocio registradas usan el guard. Beat elimina entradas persistidas, incluido backend_cleanup, y no despacha en recuperación. Procesos detenidos y colas de la repetición eliminadas; limpieza de cola garantizada también ante aserciones fallidas. [Evidencia](evidencias/recuperacion-worker-beat-aislamiento0100.json). Requiere reiniciar cada proceso con RECOVERY_MODE; mensajes ignorados se consumen, reconstruir solo trabajo autorizado. Runtime0099; sin aislamiento de proveedores/CDN ni aceptación CR09.

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

Operación/restauración0100:3 pruebas PostgreSQL correctas63,67s sobre la misma fuente actual (comando apply_recovery_ledger, preflight y ensayo real pg_dump/pg_restore). Rechazo de modo normal/checkpoint ausente/lote inválido antes de efectos; aplicación/borrado físico y replay sin duplicados. Restauración repetida tras corregir backoff: medios eliminados, tercero preservado, sesión antigua rechazada y DB temporal eliminada. [Evidencia](evidencias/recuperacion-operacion-restauracion0100.json). El comando mantiene aislamiento/publication_authorized:false, informa pendientes/agotados y no acredita vigencia externa del checkpoint, CDN ni RPO/RTO. Runtime0099; falta regresión integrada y entrega0100, CR09 abierto.

Entrega técnica parcial0100 preparada: batería integrada de recuperación y censo67 pruebas correctas225,62s, sin fallos/errores/omitidas;584 hashes de fuentes congeladas intactos. Docker construido y app/worker/Beat recreados; migración0100 aplicada,11 hashes idénticos host/tres servicios, UID10001, Django check/migrate-check y salud200. Proceso hijo aislado RECOVERY_MODE=1 verifica HTTP503/guard de tareas/Beat vacío sin cambiar modo del servicio normal. [Evidencia](evidencias/recuperacion-integrada-runtime0100.json). Este resumen prevalece sobre referencias anteriores a runtime0099/cambios no integrados; esas referencias conservan el momento histórico de cada prueba. No es regresión completa del repositorio ni cierre CR09. Siguiente: eventos múltiples y autoridad vigente de recuperación, cachés/colas/operación y matriz residual derechos/finalidades. CR10→GS01→BF/BB→C pendientes; CI externo sin ejecución por facturación.

Sustitución firmada0100 corregida en workspace: recibos nuevos incluyen campo opcional replacement UUID en fotos compartidas, ligado a redacción y distinto de todos los blobs originales. Se reconstruye exactamente ese sustituto vacío y privado; datos/archivos/huellas/dimensiones o referencias de otro perfil impiden aplicación. Recibos anteriores sin campo conservan redacción aislada; cadenas históricas sin trazabilidad pueden rechazar de forma segura y no se infiere autorización. Preflight proyecta enlaces autorizados en memoria entre eventos sin escribir sustitutos/auditorías. Resultados separados:20 pruebas iniciales65,97s,4 de preflight/ownership63,38s y14 finales142,05s de seguridad/medios/eventos/secuencia real. [Evidencia y versiones](evidencias/recuperacion-sustitucion-firmada0100.json). Sustituto eliminado antes del ensayo para representar su ausencia en copia vieja; se recuperan dos ejecuciones autorizadas con identidad sintética, tercero preservado y borrado exclusivo real. Runtime b50e69f no actualizado; falta regresión integrada y entrega. CR09/contrato abiertos.

Entrega de sustitutos0100 verificada:76 pruebas conjuntas correctas306,30s, sin fallos/errores/omitidas;587 hashes congelados intactos. Docker app/worker/Beat recreados con corrección;5 hashes afectados coinciden host/tres servicios, UID10001, check/migrate-check y salud200 correctos. [Evidencia](evidencias/recuperacion-sustitutos-integrada-runtime0100.json). Prevalece sobre estados anteriores de corrección no integrada/runtime b50e69f. CR09 sigue abierto, estimaciones orientativas82%/56% sin recalcular; siguiente matriz residual y operación/cachés/autoridad vigente. No aceptación global ni producción.

Preflight de sustitutos0100: reproducción2 fallos/2 correctas63,63s confirma que comprobación previa aceptaba sustituto poblado o referenciado por otro perfil mientras aplicación lo rechazaba. Validación única validate_empty_replacement incorporada a ownership/preflight y reaplicación.8 pruebas correctas97,35s; errores sin salida de éxito ni cambios DB, compatibilidad antigua y secuencia válida de dos eventos conservadas. [Evidencia](evidencias/recuperacion-preflight-sustitutos0100.json). Corrección solo workspace, runtime c004262; siguientes vigencia independiente del checkpoint/cachés/operación/matriz residual. CR09 y contrato abiertos.

## Referencia independiente vigente

Los comandos check_recovery_ledger y apply_recovery_ledger exigen expected-ledger/sequence/head además del checkpoint del backup. Obtenerlos de la autoridad operacional independiente antes de recuperar; no derivarlos del archivo que se está validando ni de la copia restaurada. RecoveryStore compara bajo el mismo lock la identidad exacta del checkpoint firmado con la referencia esperada antes de descifrar/aplicar efectos. Firma válida con checkpoint antiguo o distinto se rechaza. Si el registro avanza mientras se recupera, mantener aislamiento y obtener una referencia vigente mediante procedimiento controlado; no ignorar la discrepancia. El mecanismo local verifica una referencia suministrada, no acredita su procedencia/vigencia externa ni reemplaza contratación/custodia de una autoridad fuera del servidor.

Referencia independiente0100 implementada en workspace: comandos check/apply exigen expected-ledger/sequence/head; RecoveryStore compara exactamente la referencia suministrada con checkpoint firmado bajo lock antes de verificar/descifrar sufijo.19 pruebas correctas88,27s; rollback firmado válido se rechaza con referencia más reciente y diferencias ledger/head/sequence también. Incluye validación compartida de sustitutos y secuencia de dos ejecuciones. [Evidencia](evidencias/recuperacion-checkpoint-independiente0100.json). No acredita procedencia/vigencia de una autoridad externa; custodia independiente operacional pendiente. Runtime c004262, fuente no entregada; CR09 y contrato abiertos. Cifras82/56 retiradas como medición vigente conforme docs86.

Entrega de autoridad0100 verificada:80 pruebas conjuntas correctas320,56s, sin fallos/errores/omitidas;587 hashes congelados intactos. Docker actualizado app/worker/Beat;4 hashes afectados coinciden host/tres servicios, UID10001, Django check/migrate-check y salud200 correctos. [Evidencia](evidencias/recuperacion-autoridad-integrada-runtime0100.json). Prevalece sobre estado anterior de checkpoint esperado/preflight solo workspace. Referencia independiente obligatoria en CLI; procedencia/custodia externa pendiente. CR09 abierto; seguir recursos locales y matriz residual, CR10→GS01→BF/BB→C pendientes. Cifras82/56 retiradas como medición vigente; seguimiento por requisitos en docs83/86.
