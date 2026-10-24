# B13 — Continuidad y moderación, 2026-10-21

Estado: auditoría inicial y primer ensayo verificado; B13 no aceptado. Siete de18puntos cerrados, B12 local por [acta14](actas/14-beta-b12-aceptacion-local-20261021.md). Objetivo B13 íntegro del [roadmap103](103-roadmap-beta-clasificados-20261020.md).

## Matriz inicial de requisitos

| Requisito B13 | Fuentes existentes | Estado y siguiente comprobación |
| --- | --- | --- |
| Caída de worker y broker | notice_worker_recovery, recovery_task_gate, local_ci_broker; pruebas previas de fallos de adaptador | Caída real de servicios propios verificada en024508; no confundir fallo de adaptador con caída de broker |
| Revisión, denuncia y retirada urgente | urgent_report_drill, urgent_report_alerts, decisiones y B06 | Contrastar cobertura actual, retirada efectiva y runbook; no asumir que resolver por dismiss acredita retirada |
| Rotación de secretos | OP005, epochs/sesiones/MFA, keyring de objetos | Inventariar clases de secreto y ensayar rotación local sin destruir capacidad de descifrado; revocar sesión no prueba por sí solo rotación de claves |
| Restauración DB más medios aislada | recovery_pg_restore y copia cifrada BB06 | Reconciliar corte beta, permisos/derechos/sesiones/grants/publicación y aislamiento externo antes de exposición |
| Rollback de aplicación | OP009, pruebas de actualización y rollback de estáticos | Estáticos no prueban downgrade de código y esquema; auditar compatibilidad y estrategia |
| Migraciones | migraciones conservadoras y romance23–25, pruebas de upgrade | Examinar reversibilidad/datos y prohibiciones de downgrade; no borrar datos para aparentar rollback |
| Personas y cobertura de apertura | G03/G06/G07 y B17 | Pendiente real; fuera de aceptación técnica local |

La evidencia de continuidad de ejecutores de CI del2026-10-10 acredita separación de sesiones y recuperación de recursos del runner, no caída de worker/broker de la aplicación. [Operación12](12-operacion-seguridad.md) y [auditoría100](100-auditoria-seguridad-tecnica-local.md) conservan sus cortes históricos; deben reconciliarse con el contrato romántico actual.

## Ensayo preparado: caída de servicios

Dos casos en tests/test_service_continuity.py, parametrizados worker/broker. Requieren CI aislado y base test_ PostgreSQL. Cada caso crea un Redis dedicado con imagen local, puerto127.0.0.1, memoria128MiB/CPU0,25 y sin persistencia, más workers solo con cola exclusiva. No detener ni reutilizar Redis/worker normales o los del runner compartidos por otros casos.

Se obtiene una notificación mediante el flujo de resolución sintético existente. Se ajusta únicamente su antigüedad a180s como fixture; no se presenta como espera natural. Caso worker: arranque real, SIGKILL al worker, publicación a su cola sin consumidor y comprobación Redis de un mensaje pendiente. Caso broker: parada del contenedor propio, publicación falla con OperationalError y outbox PostgreSQL conserva estado queued/attempts0. Se recuperan servicios, se despacha la tarea normal cuando corresponde y se comprueba un recibo simulado, attempts1 y replay sin procesamiento adicional. No proveedor externo.

La evaluación B12 observa atraso antes y contador exigible0 después, manteniendo healthunknown. El fallo de publicación no se oculta como tarea completada. Los procesos y el contenedor propio se limpian en finally y se comprueba ausencia. No pérdida de proceso a mitad de tarea ni reboot de host ensayados; Redis sin persistencia no promete recuperar mensajes del broker, la outbox durable exige despacho normal tras recuperar.

Selección focal prevista: dos casos, un worker pytest. No batería de capacidad ni nueva comparación de paralelismo. Verificar fuente congelada, JUnit, agregados, procesos/contenedores y Telegram terminal; preservar cualquier negativo. No aceptación B13 por este ensayo aislado.

## Runbook local correspondiente

Ingeniería identifica servicio y namespace propios y captura estado durable/errores sin contactos ni payloads. Si cae worker, conservar cola y outbox, revisar causa y arrancar worker con configuración/autoridad vigentes; no marcar avisos como entregados. Si cae broker, detener reintentos operativos no acotados, preservar outbox PostgreSQL y restaurar conectividad del broker autorizado. Tras recuperarlo, ejecutar el procesador normal respetando intentos, backoff e idempotencia; comparar pendientes y recibos. Ausencia de aviso concreto no prueba salud global. No vaciar colas ajenas ni reponer mensajes históricos con autoridad caducada. Para restauración o cambios de namespace usar el procedimiento de recuperación aislada, no este ensayo de caída simple. Guardia, canal y personal reales siguen en B17.

## Primer negativo conservado

024124-de25c000:0PASS/2FAIL/0ERROR/0SKIP,67,600sJUnit. Ambos recorridos produjeron los agregados esperados de recuperación, pero fallaron al comprobar ausencia de contenedor: docker inspect devolvió no such object en minúsculas y el test esperaba No such. No se contabilizan como PASS. [Auditoría negativa](evidencias/b13-service-continuity-first-negative-audit-20261021.json): fuentes frescas, recursos ausentes y TelegramERROR verificados. Comparación de ausencia corregida sin distinguir mayúsculas y se añaden identidades de workers/contenedor al artefacto local para inspección posterior. Repetición pendiente.

## Hallazgo para el siguiente frente

En el corte inicial, apps/safety/crypto.py y apps/core/mfa.py usaban una clave Fernet por configuración. En desarrollo, si falta clave explícita, se deriva de SECRET_KEY. Cambiar únicamente SECRET_KEY en ese escenario cambia también la clave efectiva de cifrado; no equivale a una rotación segura de datos existentes. La rotación de firmas/sesiones y la de cifrado requieren ensayos y procedimientos distintos. No se ha implementado ni aceptado una rotación general por esta lectura; B13 conserva este punto abierto.

## Resultado vigente del ensayo de servicios

024508-3f025827:2PASS/0FAIL/0ERROR/0SKIP, un worker pytest,68,186sJUnit. [Auditoría terminal](evidencias/b13-service-continuity-terminal-audit-20261021.json) confirma fuentes actuales, producto idéntico al corte B12, limpieza del runner y sus servicios, ausencia de los Redis/worker del ensayo por nombre e identidades y TelegramPASS. El negativo024124 queda conservado.

[Caída de worker](evidencias/b13-service-continuity-worker-20261021.json): SIGKILL antes de consumir, mensaje en cola comprobado por Redis, notificación PostgreSQL todavía queued/attempts0. Reinicio procesa una vez. [Caída de broker](evidencias/b13-service-continuity-broker-20261021.json): contenedor detenido, publicación rechazada, pendiente conservado en PostgreSQL. Reinicio y despacho normal procesan una vez. En ambos: contador exigible1→0, attempts1, un recibo simulado, replay processed0; healthunknown. Dos procesos worker propios por caso, todos terminales, no servicio normal afectado.

No prueba fallo a mitad de tarea, reboot, persistencia Redis, envío externo ni latencia natural de detección. Antigüedad de180s es fixture explícita; el aviso de atraso y recuperación usan el evaluador real B12. La autoridad durable es la outbox; no se promete recuperar un mensaje perdido del broker sin despacho normal.

La transición limitada de cifrado se verificó después en [142](142-rotacion-secretos-beta-b13-20261021.md), con150casos únicos conciliados entre dos cortes. Continúan pendientes el censo/revalidación de HMAC, la retirada segura de claves y otras clases de secreto, además de restauración/retirada/rollback. No aceptar B13 por el ensayo de continuidad o esa fase aislada.

Actualización rollback: [145](145-estrategia-rollback-beta-b13-20261021.md) verifica lectura en un ciclo real de imágenes beta con esquema conservado; [146](146-rollback-escrituras-workers-beta-b13-20261021.md) añade tres ediciones, acciones/replays y consumo de tareas reales entre versiones. Aceptación limitada a esa pareja y relevo secuencial; no migración destructiva, tráfico concurrente ni código alfa. B13 sigue abierto por secretos/HMAC/retención restantes.

Actualización HMAC: [147](147-consumidores-hmac-beta-b13-20261021.md) verifica17casos estáticos y383consumidores resueltos sobre308fuentes. Cobertura transitiva completa y autorización de retirada siguen false; usos dinámicos y clasificación persistente por dominio pendientes. No aceptación B13 por este inventario.

Actualización credenciales: [148](148-rotacion-credencial-postgresql-beta-b13-20261021.md) verifica un caso PostgreSQL real de PASSWORD/NOLOGIN/LOGIN, supervivencia y terminación dirigida de sesiones, ACL/datos conservados y limpieza. Sin rotación de servicios normales ni pools de aplicación acreditados. B13 conserva pendientes los otros procedimientos de secretos.

Ampliación148: mismo caso PostgreSQL reforzado1PASS3,780sJUnit añade wrapper Django con persistencia60s/health checks; backend viejo sobrevive PASSWORD, control de salud falla con credencial antigua y configuración nueva reconecta con filas intactas. Nueve propiedades juntas, no sumar como segundo caso. Recarga de procesos desplegados no acreditada; los demás secretos B13 pendientes.

Actualización broker: [149](149-rotacion-broker-redis-beta-b13-20261021.md) verifica1PASS Redis7.4/Kombu reales: nueva contraseña, rechazo de anterior, cliente autenticado sobrevive hasta terminación dirigida, dos mensajes pendientes consumidos/ACK sin cambiar namespace y claves/ACL conservadas. Sin recarga Celery desplegada ni outbox PostgreSQL acreditada por este caso. B13 conserva los otros secretos/clasificación HMAC pendientes.

Actualización dominios HMAC: [150](150-rotacion-firma-recibos-beta-b13-20261021.md),05302222PASS4workers: recibos y replay de denuncias/derechos, con/sin fallback, conservan evidencia/fechas y permiten inspección nueva auditada. Cuatro campos clasificados; canal sustitutorio del interesado y demás bindings no acreditados. B13 sigue abierto.

Actualización separación de firma: [151](151-clave-hmac-dominio-beta-b13-20261021.md) implementa SAFETY_HMAC_KEY opcional, vacío heredado; fijar el secreto anterior preserva el recibo/binding original durante rotación Django sin rehash.173casos únicos conciliados (160reuso+13correctivas), no una corrida173PASS. Clave de dominio comprometida/rotada y rollback a imagen incompatible siguen fuera de aceptación; B13 abierto.

Actualización restauración HMAC: [152](152-restauracion-clave-hmac-beta-b13-20261021.md),06150522PASS: cinco restauraciones reales, tres con firma Django nueva/pin de dominio/readers Fernet, y recibo original del par conservado en las cinco. Grants/sesiones del clon invalidados, origen preservado y limpieza/Telegram verificados; misma candidata de producto151. B13 abierto por otros pendientes, sin custodia o recuperación por compromiso acreditadas.

Actualización proxy/ledger: [153](153-autoridades-proxy-ledger-beta-b13-20261021.md) verifica clave interna y generación/purga de grants, independencia del codec y controles de checkpoint.34casos únicos(33reuso+1Caddyrepetido), no nueva corrida34. Primera corrida34PASS/1warning; conexión del hilo WSGI corregida, repetición1PASSsinwarning. Helpers/producto iguales y fuentes/limpieza/Telegram auditados. No recarga Caddy con nuevo secreto ni rollover ledger acreditados; B13 abierto.

Actualización recarga proxy: [154](154-recarga-secreto-caddy-beta-b13-20261021.md),0649295PASSsinwarnings: steady y reload reales, proxy desactualizado404sinconsumo, mismo contenedor/enlace sirve tras recarga, bytes/privacidad/replay/auditoría conservados. Recursos/Telegram verificados; no recarga backend en caliente ni rollover ledger. B13 abierto pendiente conciliación final de matriz.

Repetición sobre candidata HMAC vigente: ambos casos de continuidad PASS en070837, conservando3avisos Celery AlwaysEagerIgnored por send_task real; [matriz155 y auditoría](155-matriz-vigente-b13-beta-20261021.md). No nueva aceptación de proveedor ni rollback.
