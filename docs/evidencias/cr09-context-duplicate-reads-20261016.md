# CR09: dos construcciones de contexto en la ruta con marcas pendientes

Run `20261016-080407-6958f4f7`, base `fbe146e`: **1 PASS, 101,63 s**, 12 requests medidas con wrappers de diagnóstico. No hay cambio de producto ni nueva carga/p95.

PostgreSQL real propio, 10.000 anuncios sintéticos, WSGIHandler sin Client ni captura de contexto de tests. Limpio/una marca controlada × listado ES/búsqueda EN × tres muestras, tras seis calentamientos por modo/ruta. Se registran tiempos de constructor y ejecución SQL inclusivos, filas y comparación local de claves de catálogo. GC normal. No se exportan claves, valores ni parámetros; sólo cardinalidades/igualdad.

| Constructor | Filas | SQL por construcción | Wall medio | CPU de hilo media |
|---|---:|---:|---:|---:|
| Página limpia | 24 | 21 | 57,01 ms | 41,72 ms |
| Fila pendiente | 1 | 21 | 66,35 ms | 32,02 ms |
| Página con una marca pendiente | 24 | 21 | 98,53 ms | 75,10 ms |

En las seis muestras Dirty1, los ocho conjuntos de claves de catálogo de ambos contextos son idénticos. Cinco contienen una entrada y tres están vacíos. El grupo de SQL que menciona tablas de catálogo cuesta, inclusivamente, 8,65 ms en el contexto pendiente y 6,77 ms en el de página. Ese grupo incluye prefetch de relaciones y no identifica exclusivamente los cinco SELECT de catálogo restringido. El constructor completo incluye mucha más labor: hidratación, prefetch, estructura ORM y catálogo.

Estas fases incluyen SQL, GC y overhead; no sumar CPU/SQL ni interpretar diferencias entre modos como un efecto causal. Los wrappers observan un fixture acotado, no el calendario concurrente de upload/Beat, ni un techo de capacidad. Coincidencia de claves no prueba por sí sola igualdad de valores fuera de una instantánea común.

Las respuestas mantienen cuerpos iguales, 200/no-store y marcas/generaciones intactas. Fuentes congeladas/JUnit 1/0/0/0 y limpieza independiente verificados: PID/start_ticks terminados, temporal y contenedores propios ausentes, unidad sin MainPID/cgroup. Límites habituales de controlador 4 CPU/3584 MiB y PostgreSQL 1 CPU/1536 MiB, sin otra carga propia.

Siguiente hipótesis, aún no aplicada: para primera página del protocolo proyectable, bajo RR propio y censo vigente, preleer juntos los IDs pendientes (máximo 48) y los primeros 24 IDs fiables sin marcas. Validar pendientes nativamente para calcular el conjunto exacto; después contar/seleccionar con la lógica existente y revalidar la página nativamente. La primera página exacta debe estar contenida en ese lote de hasta 72 IDs; si falta algún seleccionado se conserva la hidratación original. Filtros no auditados, checked, páginas posteriores, transacciones heredadas y censo incompleto conservan el camino original. Debe probarse equivalencia, uso efectivo, límites y ROI antes de integrar; no se retira ninguna validación ni se introduce caché entre requests.

No aceptación CR09/N3; último p95 limpio permanece 1,013029795 s. Sin producción, proveedores ni invocaciones Claude nuevas.
