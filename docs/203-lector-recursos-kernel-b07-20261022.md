# B07 — Lector de recursos propios del entorno kernel

Estado vigente: lector y canal integrados y calibrados funcionalmente; véanse [207](204-calibracion-observador-kernel-b07-20261022.md) y [209](205-identidad-reposo-observador-b07-20261022.md). Las guardas y pendientes descritos abajo corresponden a sus cortes iniciales204–205.

B07-204 lector host de recursos kernel implementado con guardas de identidad de seis contenedores: nombre/etiqueta/ID completo/PID/startticks/cgroup y descendientes propios.15guardasPASS y RuffPASS. Aún no integrado ni calibrado con Docker; no acredita recursos por ventana ni capacidad. B07 abierto8de18.

El colector CI de [181](181-colector-recursos-servicios-beta-b07-20261021.md) y la frontera corregida en [195](195-frontera-captura-recursos-b07-20261021.md) mantienen sus controles. El controlador capacity tiene namespace PID propio: no puede aplicar directamente el lector host CI a los PID del daemon Docker. Por ello scripts/benchmark_capacity_resources.py define un lector separado para el host. Sólo acepta el conjunto exacto controller/app/pg/redis/objects/caddy y verifica pertenencia por ejecución antes de acceder a procesos. Cada snapshot revalida startticks y cgroup, recoge CPU/memoria de hojas y árboles de procesos limitados a128descendientes por raíz. Sin enumeración global, argv, entorno, SQL ni datos personales.

Las fases admitidas son before_arrivals, arrivals_and_drain e idle_after. Cada snapshot guarda inicio y fin monotónicos: las lecturas son secuenciales, no picos simultáneos. RSS puede contar páginas compartidas varias veces; memory.peak es acumulado y los hijos desaparecidos pueden no observarse. No hay atribución CPU por petición ni overhead causal medido.

Pendiente en el corte204 (resuelto por integración206 y calibraciones207/209): integrar un observador opcional en el lanzador host con identidad persistente del launcher, salida exclusiva acotada, señal de fase procedente del ensayo y cierre anterior a cleanup. Calibrar primero a10perfiles: muestra antes/durante/después, identidad de servicios, overhead y recursos del propio colector incluidos en presupuesto o declarados como observador separado. No ejecutar gran carga hasta verificar ese alcance. Los15casos unitarios prueban rechazo de metadatos ajenos, cgroup incorrecto, topología incompleta y PID/cgroup/fase cambiados; no sustituyen la calibración real.

## Canal de fases205

B07-205 canal de fases acotado implementado: historial atómico before_arrivals/arrivals_and_drain/idle_after ligado a ejecución, lectura host de máximo2048bytes por raíz app verificada antes/después.31guardasPASS y RuffPASS; sin integración ni calibración Docker, no capacidad ni cierreB07,8de18.

`scripts/benchmark_capacity_phase.py` valida orden, tiempos finitos no negativos y ejecución exacta. Señal privada con permisos0600 y sustitución atómica, sin reusar archivos existentes. El historial conserva límites aunque el observador se retrase. El lector accede únicamente a /proc/PID/root/tmp/capacity-beta-resource-phase.json tras identidad/cgroup verificados; archivo regular, sin seguir symlink final y revalidación al terminar. Las pruebas cubren el codec y lecturas mediante filesystem temporal; no equivalen a señal emitida por un ensayo Docker real.

Siguiente integración: escritor después de arrancar servidor y antes de sondas; cambio a arrivals justo antes del generador y a idle_after tras su terminal, registrar límites originales y comparar con origen/fin del ledger. El observador debe guardar tiempos de inicio/fin de cada muestra y excluir del cálculo por fase aquellas que crucen límites. No inferir fases por momento de lectura ni perder transiciones. No montar almacenamiento adicional ni ampliar cuotas implícitamente.
