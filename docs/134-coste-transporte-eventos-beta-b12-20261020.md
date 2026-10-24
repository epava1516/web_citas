# B12 — Coste normal del transporte de eventos

Estado: medición local completada con integridad verificada; no aceptación B12.

Continúa la recuperación verificada en [133](133-recuperacion-outbox-prefork-beta-b12-20261020.md). Grafo previo75:49fe3be8ab294bd7de618fb5db6ef4a898d811e65a48d359450b5056544fbd98. No modificar producto para este diagnóstico.

Se mide el emisor real publication_read y su handler acotado ante una tubería real drenada por un lector propio. El control conserva la misma serialización JSON y loggerINFO, sustituyendo únicamente el destino por NullHandler. Esto compara coste de transporte; no mide todo el coste de instrumentar una petición HTTP.

Seis intérpretes nuevos, orden null/transport/transport/null/null/transport. Cada uno realiza un evento de arranque y cien eventos a veinte por segundo, sin trabajadores simultáneos. Recoger llamadas individuales, mediana/p95/máximo, primera llamada fría, CPU del proceso incluyendo hilo escritor y vaciado, desviación de cadencia, RSS antes/después del arranque y al final; ru_maxrss se declara pico de todo el proceso, no asignación exclusiva del handler.

Criterios de integridad:101eventos recibidos por brazo transport y cero por control, vocabulario exacto, cero drops/errores/cola/inflight al vaciar, hilo escritor retirado y todos los hijos terminales. Una ejecución de integridad correcta no implica cumplir un presupuesto de rendimiento. No fijar umbrales retroactivamente para convertir una medición en aprobación.

Guardar muestras crudas y huellas de scripts/measure_operational_transport.py, emisor y handler; congelar fuentes, comparar antes/después y conservar recibo Telegram. No datos de sujetos ni líneas de eventos retenidas: sólo valores fijos y agregados.

Límites: tres procesos por brazo, microbenchmark sintético del emisor, sin inferencia de SLOHTTP, CPU de PostgreSQL, capacidad del servidor ni consumo global de cuatro workers. Coste/cadencia del snapshot, receptor operativo, rotaciónruntime, ventanas y umbrales/runbook continúan pendientes. B12 sigue abierto.

## Resultado observado

Seis procesos terminales,303eventos recibidos de303esperados en los tres brazos transport, cero drops/errores/pendientes, fuentes intactas. [Muestras crudas](evidencias/b12-normal-transport-measurement-20261020.json) y [auditoría terminal](evidencias/b12-normal-transport-terminal-audit-20261020.json):4505huellas contrastadas de nuevo, producto idéntico234058, TelegramPASS confirmado.

| Orden | Destino | p50 llamada ms | p95 llamada ms | Máximo ms | Primera llamada ms | CPU proceso s | RSS final menos inicial KiB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | null | 0.176060 | 0.229814 | 0.379026 | 0.109826 | 0.021519 | 0 |
| 2 | transport | 0.291832 | 0.450714 | 0.469281 | 2.070354 | 0.048874 | 256 |
| 3 | transport | 0.240493 | 0.329104 | 0.433044 | 0.882415 | 0.038071 | 128 |
| 4 | null | 0.187269 | 0.278791 | 0.373808 | 0.166965 | 0.024822 | 0 |
| 5 | null | 0.187289 | 0.250843 | 0.279105 | 0.104668 | 0.023834 | 128 |
| 6 | transport | 0.307368 | 0.439482 | 1.493047 | 0.575175 | 0.064106 | 128 |

El p95 del emisor con transporte oscila0,329–0,451ms frente0,230–0,279ms del control que conserva serialización. El máximo observado fue1,493ms y el arranque frío máximo2,070ms. No afirmar que todas las llamadas quedan por debajo de1ms. La variación entre procesos no permite convertir resta de percentiles en coste causal universal.

RSS final menos inicial128–256KiB con transporte, frente0–128KiB del control; no equivale a memoria exclusiva del hilo ni pico total. CPU del proceso con escritor0,038–0,064s por muestra, control0,022–0,025s; excluye al recolector padre. Ninguna muestra perdió eventos. No se ha medido concurrencia de peticiones, cuatro procesos de aplicación ni memoria total del servicio.

Resultado: PASS de integridad del experimento, sin umbral de rendimiento adoptado. El transporte añade coste medible; no se cambia producto ni se declara resuelta la capacidad. Próximo: coste/cadencia del snapshot y recogida operativa con ventanas/salud, rotaciónruntime y umbrales justificados. B12 continúa abierto.
