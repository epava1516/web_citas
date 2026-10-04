# Conservación y limpieza de cargas preparadas

Estado: implementación local de limpieza técnica en CR-09; aceptación integral de conservación y derechos pendiente. Esta entrega no fija plazos jurídicos, no acredita proveedor externo y no sustituye una decisión de supresión.

## Ámbito y referencias

Una fotografía preparada pertenece a un expediente y tiene validez técnica máxima de 24 horas, limitada por la comprobación de ámbito. La caducidad o el descarte impiden su uso; la limpieza examina si sus archivos todavía tienen otras dependencias.

`MediaPreparationCleanup` enlaza un único `Blob`, guarda estado, motivo técnico, intentos, siguiente intento, fecha de terminación y rutas cifradas mientras el borrado esté pendiente. El inventario de supresión incluye ahora sus metadatos y `RightsRectificationPhotoUpload`, además de Photo, Revision y Blob. No entrega rutas cifradas ni imágenes desde el inventario. Una nueva dependencia o un cambio en esas filas invalida el inventario anterior.

## Decisión técnica automática

| Dependencia | Comportamiento |
| --- | --- |
| Carga activa del mismo archivo, incluso en otro expediente | Conservación y nueva comprobación |
| Otra fila Blob que referencia la misma ruta de original o derivado | Conservación; una ruta compartida tampoco puede borrarse |
| Referencia ordinaria, incluida una revisión histórica o una corrección aplicada | Conservación; nunca borrar por caducidad de preparación |
| Expediente con cualquier propuesta de rectificación | Conservación preventiva del conjunto de cargas de ese expediente |
| Resolución de coincidencia, restricción o copia privada referida | Conservación de evidencia |
| Supresión jurídica en curso o terminada | La tarea de supresión conserva la responsabilidad; no competir por los archivos |
| Solo cargas descartadas/caducadas, sin las dependencias anteriores | Limpieza de original y derivado |

Las propuestas están cifradas. El worker conserva todas las cargas del expediente si hay una propuesta y evita descifrar material privado fuera de una consulta auditada. Esta regla es conservadora: la decisión final de conservación de evidencias y su retirada por finalidad continúa pendiente; no es autorización para conservar indefinidamente.

## Estados, tareas y fallos

La tarea `apps.mediafiles.tasks.cleanup_prepared_media` se programa cada 60 segundos. Descubre hasta 100 archivos por pasada y procesa hasta 100 trabajos vencidos. Los trabajos retenidos se vuelven a comprobar después de una hora, rotando por fecha para evitar que impidan procesar otras cargas.

Antes de tocar archivos, una transacción independiente confirma las rutas cifradas y el estado `Blob.purging`. La ingestión y el procesamiento no pueden usar ese archivo. La fase de eliminación vuelve a bloquear Blob y trabajo y comprueba dependencias. El servicio rechaza ejecutarse dentro de una transacción externa: el borrado físico no puede deshacerse con rollback.

Un fallo de almacenamiento conserva rutas, estado y reintentos; espera exponencial desde 60 segundos hasta una hora, sin abandonar silenciosamente el trabajo. Un corte del worker conserva el estado confirmado antes de borrar. El siguiente intento tolera que el primer archivo ya no exista y verifica la ausencia después de cada eliminación. La vigilancia de trabajos fallidos o retenidos se incorpora al backlog operativo; no se acredita todavía una alerta externa real.

Al completar, se vacían rutas, huellas visuales y dimensiones, se retiran las referencias preparadas y se cambia el estado a `purged`. El SHA original se sustituye por un valor aleatorio para liberar su unicidad. Una futura carga legítima de los mismos bytes crea otro Blob y pasa de nuevo por validación, comparación y moderación. Las referencias históricas siguen apuntando al objeto vacío; no recuperan acceso por esa nueva carga. No se aplica una prohibición permanente por haber descartado un archivo temporal.

La fila de trabajo y los metadatos mínimos permanecen como registro. Su conservación final, tombstones independientes de backups, restauración/reconciliación y retirada de evidencias requieren la continuación del plan de conservación de CR-09 y de operación del contrato.

## Verificación y límites

Las pruebas usan PostgreSQL, imágenes sintéticas y almacenamiento local. Incluyen archivo exclusivo, repetición idempotente, nueva carga del mismo contenido, referencia histórica compartida, otra carga activa, propuesta protegida, fallo parcial de almacenamiento, interrupción del worker antes del borrado y tras eliminar un archivo, rutas compartidas y procesamiento concurrente. La revisión de rectificación ES/EN sigue en la batería afectada. Los resultados terminales se registran en la evidencia de esta entrega; no se suman baterías con solapamiento.

Las pruebas eager no acreditan transporte real por broker. Docker ejecuta la tarea nueva por Redis y Celery reales, con eager desactivado. El probe dbfd40bf-bf2e-484b-977b-e34b53140e67 fue recibido y terminado por el worker con {queued:0, completed:0}; Beat también envió la tarea periódica. El entorno principal tenía cero cargas preparadas y cero trabajos. Se verifica transporte y registro con cola vacía; el borrado de imágenes se verifica por pruebas PostgreSQL/almacenamiento local, no por ese probe. Celery tiene task_ignore_result activado: el get del resultado devolvió None, y la recepción/terminación se contrastó en el log del worker. No acredita un proveedor externo ni ejecución por broker de un caso con archivos.


Resultado final: 35 pruebas correctas en329.86s, sin fallos/errores/skips. Baterías anteriores20 y33 se solapan y no se suman. [Evidencia normalizada](evidencias/conservacion-cargas-preparadas.json).
