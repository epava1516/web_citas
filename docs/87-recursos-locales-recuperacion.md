# Recursos locales y aislamiento tras restauración

Estado: implementación parcial, no autorización para reabrir. Matriz de aceptación docs83 y operación docs85.

| Recurso | Implementación/configuración actual | Pendiente |
| --- | --- | --- |
| Sesiones Django | Backend DB por defecto; comprobación de épocas de cuenta/MFA; sesión antigua rechazada en ensayo pg_restore | clear_recovery_sessions implementado/probado en workspace; falta entrega y ensayo integral, no confundir rechazo de acceso con borrado físico de django_session |
| Caché Django | Configuración por defecto en memoria local; búsqueda estática no encuentra uso explícito de django.core.cache en app | Documentar y verificar reinicio de todos los procesos/ausencia de caché persistida; futuras cachés deben tener namespace y reconciliación |
| Redis broker | Prefijo por proyecto/generación en workspace; pruebas Redis y worker/Beat correctas | Entrega, cambiar generación bajo aislamiento y reconstruir solo trabajo autorizado; no recuperar colas antiguas ni flush global |
| Resultados Celery | Resultados ignorados en aplicación; backend Redis solo activado por probes sintéticos | No interpretar probes como almacén de resultados productivo; inventariar si se habilita futuro backend |
| Beat | Calendario vacío en recuperación y entradas persistidas eliminadas en ensayo real | Reiniciar con modo/generación correctos y reconstruir calendario desde configuración validada |
| Proxy Caddy | Sirve estáticos y reverse_proxy; sin configuración de caché de respuestas | Verificación operacional del entorno final; CDN/proxy externo no acreditado |
| Logs | SafeAccessLogger omite query y sustituye rutas privadas; logs fuera de base restaurada | Política de conservación/redacción/operación y pruebas; no borrar evidencia o logs de otros proyectos indiscriminadamente |
| Backup/medios | Ensayo real PostgreSQL/archivos sintéticos y autoridad esperada implementados | Custodia externa vigente, capacidad/RPO/RTO y procedimiento integral |

TASK_QUEUE_GENERATION debe provenir del estado operacional retenido fuera de la copia de negocio. La primera adopción cambia el namespace respecto al broker antiguo sin prefijo: no migra ni elimina mensajes anteriores. Registrar esa transición, mantener aislamiento y reconstruir las tareas apropiadas desde datos reconciliados. Configurar exactamente la misma generación en todos los productores, workers y Beat; reiniciarlos antes de reabrir. Una generación nueva no garantiza por sí sola que las tareas que se reconstruyan estén autorizadas.

Sesiones locales0100 en workspace:clear_recovery_sessions exige modo recuperación y backend DB, autoridad independiente y coincidencia de recibos con auditoría de reaplicación; elimina todas las sesiones de la base aislada sin descifrar/devolver contenidos.8 pruebas correctas46,84s (comando/preflight/namespaces Redis); rechaza modo normal, ausencia de reaplicación y auditoría corrupta; replay0. [Evidencia](evidencias/recuperacion-sesiones-locales0100.json). Operación global de recuperación, no supresión individual; moderadores también deben autenticarse de nuevo. Guardar JSON agregado como evidencia reservada. Runtime036a1a0, sin commit ni aceptación integral.

Entrega recursos locales0100 verificada:86 pruebas conjuntas correctas313,03s, sin fallos/errores/omitidas;589 fuentes intactas. Docker actualizado;2 hashes afectados idénticos host/app/worker/Beat, UID10001, namespace clasificados:v1:/cola clasificados confirmado en tres servicios, Django check/migrate-check y salud200. [Evidencia](evidencias/recuperacion-recursos-integrada-runtime0100.json). Cola antigua por defecto observada0 antes de transición; ninguna purga/flush/migración automática. Destrucción de sesiones solo ejecutada en tests aislados, no runtime normal. Prevalece sobre estados de código sin entregar; CR09 abierto. Siguiente matriz de derechos/finalidades, no nueva ampliación de recuperación salvo requisito/fallo concreto.
