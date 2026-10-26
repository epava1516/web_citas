# N09A — corrección prerregistrada de autoridad fresca en recuperación

Antes de aplicar el candidato. N09 continúa abierto,8/13. Se conserva [420](420-n09-a-diagnostico-aviso-y-sonda-media-20261026.md) y el diagnóstico de [419](419-n09-a-prerregistro-revocacion-recuperacion-20261026.md); no se difieren defectos funcionales por aceptar los tiempos alfa. Base de aplicación71860c7, grafo previo de2.039fuentes SHA256 `c24af63aa6c2229ce61be2d5f6b49a63e1d8a70261f99451ca3f8782c6bdee37`.

## Dos defectos confirmados y fallos preservados

El lote original041859-126a93a0 conserva2FAIL/57,843sQA: aviso con espera PostgreSQL y revocación reales terminó302y creó una recuperación; medios falló antes de su sonda por una instancia stale de fixture. Se corrigió únicamente esa lectura con `refresh_from_db`, sin cambiar la aplicación ni repetir el aviso.

La repetición exclusiva de medios042943-80ced3cc produjo **1FAIL/48,210sQA**, fuentes estables,1.761huellas (1.757runner y cuatro documentos aparte), limpieza y Telegramsent. Tras `Lock` y revocación comprobados, el POST terminó302en vez de403: trabajo failed/intentos5/versión1 pasó a queued/intentos0/versión2, creó un `MediaErasureRecovery` y un `RightsAction`; blob, expediente y ejecución permanecieron iguales. Sus213,874msde petición incluyen espera inducida, no son latencia normal. La auditoría confirma dos endpoints distintos con el mismo tipo de defecto, sin convertir el primer fallo instrumental en un fallo de producto.

| Recuperación revocada durante espera real | Antes de corregir | Resultado exigido al candidato |
| --- | --- | --- |
| Aviso report |302, aviso reiniciado y+1NoticeRecovery|403, cero cambios de dominio|
| Borrado de medios |302, trabajo reiniciado y+1MediaErasureRecovery/+1RightsAction|403, cero cambios de dominio|

## Cambio propuesto, límites e invariantes

Alcance de producto: sólo `apps/safety/notice_operations.py` y `apps/safety/media_operations.py`, importación de User y un helper local de operador actual en cada módulo, más sus llamadas en `requeue`. Mantener firmas públicas, guards de ámbito/caso, cifrado, versiones, claves, intentos, errores, rutas, formularios y comportamiento de replays autorizados.

Capturar las versiones de sesión y MFA del usuario de entrada una vez. Leer una **nueva instancia User de base de datos**, sin reutilizar su caché de permisos, al admitir el servicio y otra vez después de adquirir los locks canónicos y de aviso/trabajo, antes de cualquier recuperación o replay. Exigir cuenta existente/activa/no borrada, MFA habilitado y versiones iguales a las capturadas; usar los permisos nativos `allowed`/`can_recover` sobre esa instancia. Evaluar el ámbito con el actor fresco. Denegar con PermissionDenied; las vistas conservarán su403 y no se escribirá una recuperación.

No añadir un lock nuevo del operador ni cambiar el orden de locks de dominio. Esta corrección fija lecturas de autoridad en esas fronteras; no pretende demostrar una serialización universal de cualquier modificación futura de permisos. No cambiar modelos, migraciones, settings, calendarios, backend de identidad/avisos, transporte, servicios existentes ni las demás rutas potencialmente afectadas hasta su evaluación propia. No copiar una receta de skill como prueba.

Es una corrección de autorización; las nuevas consultas de User/permisos están justificadas por el requisito de autoridad fresca. No es un candidato de rendimiento y no se promete menor SQL/tiempo. Se registrarán los tiempos disponibles antes/después como estados diferentes, sin porcentaje de aceleración.

## Selección de verificación antes de integrar/aceptar

Propuestas aisladas y revisión principal con Django Expert/Reviewer antes de integrar. Reejecutar los dos diagnósticos reales de419, sin cambiar sus oráculos de bloqueo/revocación/403/snapshots ni parchear negocio: la repetición está justificada por corregir los servicios que fallaron.

Añadir **14 negativos finitos de servicio**: cada uno de los dos servicios con un actor legítimo cuyo objeto/caché permanece anterior a la revocación; retirar permiso principal, retirar permiso de revisión, desactivar cuenta, marcar cuenta borrada, deshabilitar MFA, incrementar versión MFA o incrementar versión de sesión. Exigir PermissionDenied y snapshots de dominio intactos. Las mutaciones del operador son la preparación externa deliberada, excluidas del snapshot de negocio. Estos casos verifican reglas de acceso, no una distribución de latencia ni una segunda espera simulada.

Regresión pertinente sin editar sus instrumentos: `tests/test_notice_operations.py` (7casos) y `tests/test_media_operations.py` (6casos). Conservan recuperación válida, dos conexiones, replay que no reinicia un ciclo posterior, motivos cifrados/no expuestos, ámbito y conflicto, CSRF, producción/simulador y navegación móvil. No repetir toda la aplicación, mediosworker aceptado ni QA de exportación larga. Selección prevista total: **29casos** (2esperas+14negativos+13originales).

Preparación nativa sintética/eager fuera de los intervalos de petición, sin crédito de worker/proveedor. PostgreSQL/Redis desechables reales del runner oficial, serial por los locks. Lint antes del AST final; después semántica actualizada, corte/congelación y ejecución notificada. Guardar resultados terminales, fallos originales, snapshots mínimos, fuente antes/después, SQL/tiempos del observador y limpieza, sin payload, motivos, correos, rutas físicas ni credenciales. Comprobar todos los recibos Telegram.

Aceptar la corrección sólo con ambas esperas403sin mutación, catorce negativos denegados y regresión sin cambios no autorizados. Si algún caso falla, conservarlo, separar aplicación/instrumento y corregir el alcance afectado antes de aceptar; no reducir selección para ocultar un fallo. La aceptación de esta corrección no cierra los139IDs de N09 ni las condiciones de autoridad de otras familias identificadas sólo por fuente. El objetivo general sigue activo en alfa, sin proveedor ni apertura.
