# B12 — Recuperación del outbox con prefork propio

Estado: verificación local de recuperación completada; B12 sigue abierto.

Se ejecutará la tarea real deliver_safety_notices en un trabajador Celery prefork de dos procesos, con PostgreSQL y Redis de pruebas y cola única. El adaptador sigue siendo un simulador local; no confirma entrega externa. Producto y esquema no se modifican.

El fallo se inyecta una sola vez mediante creación exclusiva de un marcador compartido entre hijos del trabajador diagnóstico. El aviso se crea mediante el recorrido de dominio existente de reclamación y resolución. Se comprobarán persistencia de retry, attempts1, ausencia de recibos y snapshot scheduled1/due0. Una segunda tarea inmediata debe procesar cero avisos.

Se espera el backoff real de sesenta segundos sin cambiar timestamps ni congelar el reloj. Después se envía manualmente otra tarea: debe producir un único recibo simulado, attempts2, estado simulated y limpiar error y fecha de próximo intento. Una cuarta tarea no debe duplicar el recibo.

Los cuatro eventos del cuerpo de tarea deben indicar succeeded, distinguiendo el contador retry del primer intento del éxito de entrega simulada posterior. El canal agregado no debe incluir destinatarios ni texto de excepción.

Fuentes: scripts/probe_notice_recovery.py y tests/test_notice_worker_recovery.py. Ejecución prevista por run_local_ci, workers1, selección de este caso y siete casos de transporte acotado; se conservarán XML, fuentes congeladas, resultado, limpieza y recibo Telegram.

Límites: no prueba Beat, caída abrupta del worker, proveedores, coste normal/RSS, rotación desplegada ni aceptación B12. B07 sigue pendiente de capacidad. El protocolo no reduce B00 ni B07–B17.

## Resultado terminal

234058-4b2f9db3:8PASS/0FAIL/0ERROR/0SKIP,111,857sJUnit. Un caso nuevo de recuperación y siete de transporte. [Auditoría terminal](evidencias/b12-prefork-outbox-terminal-audit-20261020.json): fuentes congeladas comparadas de nuevo, producto intacto respecto232949, PostgreSQL/Redis y temporal eliminados, procesos del runner/pytest y tres PID observados del prefork ausentes, TelegramPASS confirmado.

Verificados el fallo único, retry persistido, snapshot programado, rechazo del reintento prematuro, espera natural de sesenta segundos, recuperación con único recibo y ausencia de duplicación posterior. Los cuatro eventos distinguen éxito del cuerpo y resultado de entrega. El warning AlwaysEagerIgnored corresponde a send_task: esa API usa el broker real aun cuando los tests configuran eager; no se ejecutó la tarea mediante .run ni .delay eager.

Este resultado acredita recuperación ante fallo del adaptador local simulado, no entrega externa, planificación Beat ni recuperación de caída abrupta. Coste normal/RSS, rotaciónruntime, ventanas/salud del receptor y umbrales/runbook siguen pendientes. No aceptación B12 ni nueva capacidadTCP.
