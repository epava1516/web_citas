# MOD-08: planes de los lectores actuales frente al productor, 2026-10-12

Diagnóstico separado del FAIL HTTP, mismo SHA388c991 y recursos8CPU propios.
JUnit1PASS771,444s,0fallos/errores/skips,launcherEXIT0. Historia36→2468,304lotes
reales aprobados por servicios; selected16777325bytes/originals67095050bytes.
Flujo parcial escalar con identidad/verificador simulado; no binarios/exportaciones
ni p95 contractual. LOGIN restringido/exclusivo, trust y validación completa
frescos, cabeza bloqueada,0otras conexiones activas del mismo login.

Cada nivel ejecuta5rondas rotadas por variante con EXPLAIN ANALYZE TIMING OFF.
native_hash es el productor escalar antiguo; set_hash es el lector actual.
inline es control diagnóstico, no aplicada a producción. Outputs exactos antes
de planes; catálogo/estadísticas y formas reales conservados. Function Scan del
helper difiere de los controles, por lo que no se atribuye todo a un único opcode.

| Consulta / filas tardías | Escalar / mediana | Por conjunto / mediana | Reducción |
| --- | ---: | ---: | ---: |
| events / 2468 | 38.858 ms | 27.188 ms | 30.03 % |
| safety_rightsportabilityread / 1 | 0.797 ms | 0.926 ms | -16.19 % |
| safety_rightsportabilityreview / 1 | 1.012 ms | 1.153 ms | -13.93 % |
| safety_rightsportabilityselectionread / 1248 | 32.369 ms | 20.710 ms | 36.02 % |
| safety_rightsportabilityselectionreview / 2 | 0.771 ms | 0.905 ms | -17.38 % |
| safety_rightsportabilityimageread / 0 | 0.041 ms | 0.365 ms | -790.24 % |
| safety_rightsportabilitycoverageread / 1216 | 36.352 ms | 25.111 ms | 30.92 % |
| safety_rightsportabilitycoveragereview / 0 | 0.060 ms | 0.383 ms | -538.33 % |

Las familias pequeñas/vacías tienen sobrecoste: no ocultarlo bajo los tres
conjuntos grandes. En el nivel temprano, cuatro controles anteriores retienen
su estructura ejecutable; el helper mantiene Function Scan y materialización.
No se han añadido índices, ANALYZE manual, flags del planner ni relajado límites.

| Historia | Suma de 8 medianas escalar | Suma de 8 medianas por conjunto | Cambio |
| --- | ---: | ---: | ---: |
| 36 eventos | 4.189 ms | 5.877 ms | 40.30 % aumento |
| 2468 eventos | 110.260 ms | 76.741 ms | 30.40 % reducción |

Esa suma es aritmética de consultas aisladas: NO una validación conjunta,
NO tiempo de request, NO ahorro que se pueda multiplicar por llamadas para
prometer p95. El ahorro real de historia grande es consistente con menor coste
de expresiones/llamadas/normalización; se sigue leyendo y hasheando cada fila.

[Muestras, planes y metadatos](mod08-vps-planes-lectores-20261012.json).
Original completo conservado en artifacts/vps-preparation/sql-bulk-diagnostic-private.json;
JUnit original en artifacts/capacity-environment/20261012-133355-c56f5505.
Fuentes1418/archivo/cleanup independientes PASS,pico superior1581178880bytes,
no error. SQL15s/hijo90s/preparación1200s y topología sin cambios.
No nueva aceptación de capacidad/global/N3.
