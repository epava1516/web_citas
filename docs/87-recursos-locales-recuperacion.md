# Recursos locales y aislamiento tras restauración

Actualizado documentalmente el 2026-10-09. Estado: recursos locales entregados en los alcances documentados; custodia, operación externa y aceptación integral pendientes. No autorización para reabrir. [Matriz83](83-auditoria-pendientes-cr09.md), [operación85](85-operacion-registro-recuperacion.md) y [seguimiento17](17-seguimiento-desarrollo.md).

| Recurso | Implementación/configuración actual | Pendiente |
| --- | --- | --- |
| Sesiones Django | Backend DB por defecto; épocas de cuenta/MFA y comando clear_recovery_sessions entregado con evidencia local0100 | Aceptación operativa integral; distinguir rechazo de acceso de borrado físico y ejecutar limpieza solo en recuperación aislada |
| Caché Django | DummyCache sin almacenamiento desde la decisión2026-10-06; estado derivado de publicación MOD-05 en PostgreSQL con invalidación propia | Reconciliar procesos/estado derivado tras restaurar según operación85; futuras cachés deben tener namespace, retirada e invalidación verificadas |
| Redis broker | Prefijo por proyecto/generación entregado; pruebas Redis y worker/Beat documentadas en la entrega0100 | Cambiar generación bajo aislamiento del entorno recuperado y reconstruir solo trabajo autorizado; no recuperar colas antiguas ni flush global |
| Resultados Celery | Resultados ignorados en aplicación; backend Redis solo activado por probes sintéticos | No interpretar probes como almacén de resultados productivo; inventariar si se habilita futuro backend |
| Beat | Calendario vacío en recuperación y entradas persistidas eliminadas en ensayo real | Reiniciar con modo/generación correctos y reconstruir calendario desde configuración validada |
| Proxy Caddy | Sirve estáticos y reverse_proxy; sin configuración de caché de respuestas | Verificación operacional del entorno final; CDN/proxy externo no acreditado |
| Logs | SafeAccessLogger omite query y sustituye rutas privadas; logs fuera de base restaurada | Política de conservación/redacción/operación y pruebas; no borrar evidencia o logs de otros proyectos indiscriminadamente |
| Backup/medios | Ensayo real PostgreSQL/archivos sintéticos y autoridad esperada implementados | Custodia externa vigente, capacidad/RPO/RTO y procedimiento integral |

TASK_QUEUE_GENERATION debe provenir del estado operacional retenido fuera de la copia de negocio. La primera adopción cambia el namespace respecto al broker antiguo sin prefijo: no migra ni elimina mensajes anteriores. Registrar esa transición, mantener aislamiento y reconstruir las tareas apropiadas desde datos reconciliados. Configurar exactamente la misma generación en todos los productores, workers y Beat; reiniciarlos antes de reabrir. Una generación nueva no garantiza por sí sola que las tareas que se reconstruyan estén autorizadas.

## Evolución histórica de la entrega0100

Los estados de workspace, runtime y siguiente paso de los párrafos inferiores corresponden a sus ejecuciones originales; la tabla superior distingue lo entregado de las dependencias todavía abiertas. El runtime y la reanudación actuales se consultan exclusivamente en seguimiento17.

Sesiones locales0100 en workspace:clear_recovery_sessions exige modo recuperación y backend DB, autoridad independiente y coincidencia de recibos con auditoría de reaplicación; elimina todas las sesiones de la base aislada sin descifrar/devolver contenidos.8 pruebas correctas46,84s (comando/preflight/namespaces Redis); rechaza modo normal, ausencia de reaplicación y auditoría corrupta; replay0. [Evidencia](evidencias/recuperacion-sesiones-locales0100.json). Operación global de recuperación, no supresión individual; moderadores también deben autenticarse de nuevo. Guardar JSON agregado como evidencia reservada. Runtime036a1a0, sin commit ni aceptación integral.

Entrega recursos locales0100 verificada:86 pruebas conjuntas correctas313,03s, sin fallos/errores/omitidas;589 fuentes intactas. Docker actualizado;2 hashes afectados idénticos host/app/worker/Beat, UID10001, namespace clasificados:v1:/cola clasificados confirmado en tres servicios, Django check/migrate-check y salud200. [Evidencia](evidencias/recuperacion-recursos-integrada-runtime0100.json). Cola antigua por defecto observada0 antes de transición; ninguna purga/flush/migración automática. Destrucción de sesiones solo ejecutada en tests aislados, no runtime normal. Prevalece sobre estados de código sin entregar; CR09 abierto. Siguiente matriz de derechos/finalidades, no nueva ampliación de recuperación salvo requisito/fallo concreto.
