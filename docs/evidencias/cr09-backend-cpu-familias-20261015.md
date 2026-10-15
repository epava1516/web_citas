# CPU de familias SQL sin seguimiento de PostgreSQL

Run `132918-10ec869c`, base `f6ea528` más instrumentos:1PASS/102.18s y4controlespuros PASS.72peticiones secuenciales, seis casos×12. Contenedor propio con cuotas habituales, sin preload pg_stat_statements ni track_planning; PID SQL traducido sólo con inventario Docker propio y guardas cgroup/NSpid/starttime. Fuentes intactas; raíz/hijo/backend/temporal/PG/Redis ausentes verificados. [Recibo completo](cr09-backend-cpu-familias-terminal-20261015.json).

| CPUbackend por petición | ListadoES | ListadoEN | BúsquedaES | BúsquedaEN | FichaES | FichaEN |
|---|---:|---:|---:|---:|---:|---:|
| Total |50.000ms|50.833ms|89.167ms|96.667ms|29.167ms|26.667ms|
| Conteo |11.667ms|10.000ms|25.000ms|28.333ms|—|—|
| Página |1.667ms|1.667ms|30.833ms|32.500ms|—|—|
| Hidratación |15.833ms|14.167ms|14.167ms|15.000ms|—|—|
| Estado global |5.000ms|6.667ms|2.500ms|3.333ms|—|—|

Ficha: familia media12.5–15msCPU de5consultas, catálogo5–5.8ms de15; no se atribuye todo a guardia porque esa agrupación no mide etapas. Listado/búsqueda17consultas catalogadas por identificadores estáticos; sin exportar textoSQL/parámetros. Cada llamada execute observada en intervalos no solapados del backend; CPU fuera de execute conservada en recibo (0–4.167ms/petición, error flotante negativo próximo a cero no se interpreta como CPU negativa).

| Media CPUbackend de mezcla igual | SeguimientoPG activo anterior | Sin seguimientoPG, familias |
|---|---:|---:|
| Seis casos igual peso |58.333ms|57.083ms|

No prueba de overhead causal: ejecuciones distintas y muestra secuencial, además la segunda añade muchas lecturas /proc. Resolución100Hz, acumulación por12peticiones; no presentar precisión por consulta submilisegundo. CPU cliente/wall incorpora instrumentación y no es métrica WSGI limpia. Procesos paralelos/fondo excluidos del backend; agregados PG aparte.

Si representativa de20rps,57.083ms implicaría1.142CPU de ejecución del backend antes del fondo. No es aceptación de techo/imposibilidad presupuestaria, pero sí evidencia contra aumentar concurrencia a ciegas conPGfijado a1CPU. Las dos consultas de búsqueda consumen55.8–60.8msCPU/petición de búsqueda; su trabajo repetido es el mayor candidato acotado.

Siguiente experimento discriminante: comparar CPU y resultados exactos de conteo+página original contra una consulta que comparta esa población sobre código/datos actuales, sin activar la variante en producto ni lanzar carga HTTP. La antigua ventana fue retirada por p95 sin mejora: su FAIL permanece y no se reactiva como solución demostrada. Sólo una reducción convincente de demanda actual y controles de orden/conteo/filtros justificarían considerar otra candidata. Alternativa posterior: evitar parseo/planificación repetidos de hidratación con mecanismo de binding/prepare auditado, sin cambios globales del driver a ciegas.

Último p95 limpio16.572804s FAIL sin actualización; CR09/N3 permanecen abiertos. No se cambiaron workers, cuotas ni verificaciones.
