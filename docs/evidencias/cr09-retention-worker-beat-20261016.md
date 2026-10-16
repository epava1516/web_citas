# Conservación: registro y despacho real con recursos propios

La ejecución `20261015-235821-3978e752` terminó el 16 de octubre: **1 PASS en 110,77 s**, sin fallos, errores ni omisiones. Fuente integrada `0017196` (SHA completo en el [recibo terminal](cr09-retention-worker-beat-terminal-20261016.json)); test nuevo incluido en los hashes originales y conservado después en `0b597ec`. No cambió la aplicación.

Se arrancaron Celery worker con concurrencia 2 y Beat mediante los comandos existentes, contra PostgreSQL/Redis propios y cola con generación única. Se comprobaron nombres, etiquetas y puerto del broker. Las rutas de medios y de entregas del hijo se fijaron en directorios desechables. El manifiesto previo confirmó modo no eager, recuperación desactivada, almacenamiento de objetos desactivado y avisos externos deshabilitados. No se conectó a servicios normales ni proveedores.

| Comprobación | Resultado |
| --- | --- |
| Tareas de conservación registradas | 18 |
| Tareas con intervalo de hasta 60 s publicadas por Beat y terminadas por worker | 17 |
| Cadencias modificadas | Ninguna |
| Efecto sobre anuncio sintético | Caducado, con una auditoría de expiración |
| Tarea horaria de objetos huérfanos | Registrada; despacho no observado |

Los identificadores enlazan cada publicación de Beat con la ejecución SUCCESS correspondiente, de rol worker y eager=False. Los eventos y el manifiesto efectivo están en el recibo. Un anuncio publicado vencido aporta un efecto funcional observable. No se preparó contenido vencido para las otras 16 tareas: su éxito acredita transporte y ejecución, no la eficacia de todas las purgas ni la política de conservación completa. Las pruebas directas previas mantienen su alcance separado.

Se conservan dos fallos de preparación: opción CLI reservada al benchmark HTTP rechazada antes de crear recursos; y run `235621-dcdcd4b1`, cuyo manifiesto consultaba una opción Django ausente en lugar del valor efectivo de Celery. Este último falló antes de arrancar worker/Beat, con fuentes y limpieza comprobadas. Se corrigió el instrumento, sin cambiar aplicación ni cadencias.

La revisión de aislamiento detectó antes de arrancar procesos hijos la necesidad de fijar RIGHTS_DELIVERY_ROOT y MEDIA_ROOT; quedaron explícitos en el test. El intento con error de manifiesto no arrancó worker ni Beat.

Verificación independiente final: fuentes iguales a source-hashes iniciales; controlador, pytest hijo, worker, hijos del worker y Beat ausentes; directorio temporal del runner retirado; Redis vacío antes de eliminarlo; contenedores propios ausentes; unidad exit0/MainPID0/ControlGroup vacío. Ruff, documentación, Django, migraciones y preparación nativa pasaron. Los límites existentes se conservaron.

Pendientes: política por finalidad/excepción/recurso, casos de contenido no cubiertos por pruebas aplicables y despacho horario cuando sea necesario. Esta evidencia no acepta CR09/N3, no mide rendimiento y no representa custodia u operación productiva.
