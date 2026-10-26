# N09A — defecto confirmado en avisos y corrección de la sonda de medios

Resultado de [419](419-n09-a-prerregistro-revocacion-recuperacion-20261026.md), sin cambios de aplicación todavía. N09 permanece abierto,8/13. El fallo funcional debe corregirse; la instrucción de diferir optimizaciones marginales no lo difiere.

## Ejecución original y evidencia válida

`20261026-041859-126a93a0`: **2 FAIL, cero errores o skips**,57,843segundos JUnit; runnerERROR, fuentes estables durante la ejecución,1.760huellas congeladas (1.757runner y418/419/seguimiento aparte), limpieza de PostgreSQL/Redis y Telegram terminal `delivery: sent`. No se cambia este resultado por la interpretación posterior.

El caso de avisos confirmó dos conexiones distintas y espera PostgreSQL `Lock`, con el backend que mantenía el bloqueo entre los bloqueadores observados. Se retiró `manage_notice_delivery` en base y se confirmó la revocación antes del commit que liberó el expediente. La petición terminó **302**, no403, y creó un `NoticeRecovery` no autorizado:

| Estado de dominio | Antes | Después de la petición revocada |
| --- | --- | --- |
| Estado del aviso | failed | queued |
| Intentos |5|0|
| Versión de recuperación |0|1|
| Error operativo |adapter_failure|vacío|
| Registros NoticeRecovery |0|1|
| Expediente y RightsAction |Sin cambios|Sin cambios|

El dominio cambió tras revocarse el permiso; no es sólo una redirección de login o un falso bloqueo. El lock se liberó, el hilo terminó y sus conexiones se cerraron. La duración de la petición fue169,280ms, incluida la coordinación y espera inducida; los46,493sdel caso incluyen preparación y no son latencia de aplicación. No hay comparación de rendimiento ni una nueva promesa de entrega.

La lectura de `notice_operations.requeue` y el resultado son compatibles con reutilizar el usuario y su caché de permisos admitidos antes de la espera, sin una nueva lectura de autoridad después. Se necesita una corrección de autorización, preservando ámbito, cifrado, auditoría, intentos y replays legítimos. Su diseño y regresión se fijarán con evidencia; no se ha aplicado aún un candidato.

## Segundo caso: fallo del instrumento, no prueba del comportamiento de medios

El caso de medios falló en10,609santes de invocar el observador de espera. La fixture nativa `tests/test_media_operations.py:exhausted` actualiza estado e intentos con `QuerySet.update`, pero devuelve la instancia anterior del trabajo. El instrumento comprobaba esa instancia y veía `queued` en vez del `failed` persistido. No alcanzó el bloqueo, la revocación ni el POST que debía diagnosticar; no acredita todavía un defecto de recuperación de medios.

Corrección mínima del instrumento: llamar `job.refresh_from_db()` inmediatamente después de la fixture y antes de las precondiciones. No cambiar la fila preparada, guards, permisos, datos, reloj ni código de negocio; no debilitar el oráculo403/sin mutación. El cuerpo del diagnóstico de avisos y su evidencia quedan intactos.

**Selección siguiente: sólo** `tests/test_operational_recovery_authority_wait.py::test_media_recovery_denies_permission_revoked_during_actual_blob_wait`, un caso. Antes: lint acotado, AST de la corrección, semántica de este resultado/seguimiento, comprobación del grafo y nueva congelación. El producto sigue71860c7; no repetir el primer caso hasta la regresión justificada de su futura corrección de aplicación. Se mantienen las reglas de espera real, snapshots, recursos y Telegram de419.

Si la nueva sonda devuelve302con mutación después de una espera y revocación comprobadas, registrar su defecto separado. Si deniega, conservar el descarte. Nuevos fallos del instrumento se distinguirán y conservarán, sin presentarlos como errores de aplicación o PASS.

## Estado de N09 y evidencias

Auditoría local: `artifacts/recorridos-n09-a-20261026/baseline-audit.json`; fuente original, primer lint y correcciones, congelación y recibos preservados. Los otros52IDs de derechos,48asíncronos y39compartidos siguen en análisis; las condiciones de autoridad similares encontradas por lectura no son automáticamente FAIL observados. No se acepta N09 ni se repite una batería general. No proveedor, sujetos reales, beta, migración o modificación de servicios existentes.
