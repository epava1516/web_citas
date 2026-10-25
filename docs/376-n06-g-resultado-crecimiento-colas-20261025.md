# N06G — resultado de crecimiento y autoridad de cuatro colas

25 de octubre de 2026. [Prerregistro375](375-n06-g-prerregistro-crecimiento-colas-20261025.md), candidata e4343f5, sin cambio de aplicación. Ejecución20261025-164827-8ac10d37: **8 PASS, 0 FAIL/ERROR/SKIP**,240peticiones medidas y128controles de autoridad. Se verifican40combinaciones cola/idioma/tamaño, primeras llamadas separadas y mediana/rango de cinco posteriores. Las cuatro colas mantienen7consultas en todas las cohortes0/1/10/100/101. No aparece N+1ni coste de consultas por elemento en el escenario declarado; decisión justificada sin cambio de código.

[Auditoría](evidencias/n06-g-colas-auditoria-20261025.json), [reproducción](evidencias/n06-g-colas-reproduccion-20261025.tar.gz). Poblaciones incrementales dentro de cada caso, no frío independiente por tamaño. Datos/propietarios/agencias/personas sintéticos; creación/bulk fuera del reloj. No acredita proceso humano ni proveedor real.

## Referencia temporal: crecimiento, sin candidato

No había referencia de estas colas en los lotes conciliados. Son medianas de cinco observaciones posteriores enmsdeClient.get;1y100realizan trabajos útiles diferentes, por lo que no se calcula mejora atribuible. Se conservan las40filas completas, primera/mediana/rango/CPU/SQL/bytes en evidencia. La tabla muestra también101para hacer visible el límite100; no representa paginación completa ni cardinalidad productiva ilimitada.

| Cola | Idioma | Antes equivalente | 1registro(ms) |100registros(ms)|101registros(ms), muestra100|SQLen todas las cohortes|Mejora atribuible|
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| agency_appeal | EN | No medido | 14.643 | 26.184 | 27.742 | 7 | No evaluable |
| agency_appeal | ES | No medido | 22.131 | 37.833 | 38.197 | 7 | No evaluable |
| manager | EN | No medido | 15.148 | 31.133 | 28.210 | 7 | No evaluable |
| manager | ES | No medido | 17.716 | 18.416 | 20.972 | 7 | No evaluable |
| manager_appeal | EN | No medido | 18.203 | 23.819 | 27.147 | 7 | No evaluable |
| manager_appeal | ES | No medido | 15.379 | 27.181 | 32.003 | 7 | No evaluable |
| organization | EN | No medido | 26.862 | 24.196 | 34.600 | 7 | No evaluable |
| organization | ES | No medido | 16.859 | 17.121 | 32.681 | 7 | No evaluable |

## Corrección y límites

Pasan IDsyorden exactos de los primeros100elegibles, enlaces efectivamente renderizados, exclusión de fila cerrada/resuelta/no pendiente más antigua y exclusión del elemento101. Se conservan actor sin permiso403, anónimo302, sesiónMFAobsoleta302al reto y permiso retirado403, sin enlaces privados en las denegaciones comprobadas. Son permisos de listados; la independencia de una decisión individual conserva los oráculos específicos de374, no se infiere de ver una cola.

Fuentes1737huellas intactas hasta auditoría, selección exacta, métricas finitas/no negativas. PostgreSQL17/Redis7.4 propios y nativos fijados; sin carga paralela/cuotas dedicadas/medición de memoria por petición. Inventario independiente vacío, temporal retirado yTelegramterminal del runner confirmado. QA de consola61,84s; JUnit y paso del runner se conservan en evidencia, separados de latencia. No p95/p99ni capacidad de producción desde cinco muestras.

La conciliación alcanza41/41rutas con alguna referencia temporal en los escenarios elegidos. Eso no equivale a todas sus ramas/métodos/actores o a una regresión global actual. La aceptación del bloque se decide por requisitos, paridad y disposiciones, en [377](377-n06-aceptacion-local-cuenta-panel-representacion-20261025.md), no por el mero conteo. MOD09restante diferido por usuario367; alfa, sin apertura/proveedores nuevos.
