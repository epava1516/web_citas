# Análisis de duraciones y paralelismo de pruebas

Estado: análisis histórico completado, sin nueva batería ni cambio de producto. Ocho de18cerrados.

La comparación funcional [124](124-comun-afectado-paralelismo-beta-20261020.md) conserva363PASS en ambos brazos: pytest624,180s con2procesos y349,882s con4;43,95%menos observado, un único par sin causalidad/reproducibilidad global. Ya existen aislamiento por trabajador, snapshots y orden de archivos completos por duración. Default6 intacto; funcional4 explícitos, capacidad serial y sin otra batería simultánea.

Se analizan sólo los timings existentes de la [regresión125](125-regresion-funcional-correctiva-beta-20261020.md), ejecución195459-bacfc549. Sus siete fallos y122SKIP históricos permanecen: no es una aceptación de la candidata actual. [Artefacto](evidencias/test-duration-opportunities-20261021.json) identifica la huella del origen,3460casos/567archivos y16596,395s sumados de setup/call/teardown. Esa suma cuenta tiempo de casos concurrentes; no es duración de reloj del runner.

Un reparto LPT idealizado de archivos enteros con esos pesos produce4149,101s para4procesos, cerca del límite teórico4149,099s y de los4168,465sJUnit observados. No reconstruye la distribución real por trabajador, ni incorpora sobrecoste/contención/cachés. La comparación indica escaso margen aparente en el equilibrado de ese corte, no una mejora medida. La estimación6procesos2766,068s no es un tiempo alcanzado ni justifica adoptar6sin evaluar memoria y PostgreSQL.

Los archivos más pesados son rights_access_coverage_store24casos/913,527s y portability_large_closed_flow1caso/831,232s. El segundo conserva1500revisiones sintéticas y1511inspecciones en un recorrido nativo completo: partirlo o reducir filas cambia el escenario y no es una optimización equivalente. Los tiempos históricos no atribuyen todavía coste a una función concreta.

Prioridad: medir preparación y operaciones dominantes de esos casos antes de cambiar fixtures; conservar persistencia, permisos, concurrencia y servicios reales. La preparación de carga ya usa bulk_create/bulk_update para perfiles y servicios create_order/receive_event para derechos: no sustituir esos servicios por inserciones directas sin demostrar equivalencia del alcance. No nuevos recursos, umbrales relajados, casos eliminados ni ganancia prometida.

Análisis efectuado leyendo artefactos durante la preparación de169, sin otra batería/build/refresco de grafo; resultado guardado y avisos INICIO/fin de Telegram confirmados. No cuenta como test PASS. La documentación se incorpora tras terminal, limpieza y auditoría de169.
