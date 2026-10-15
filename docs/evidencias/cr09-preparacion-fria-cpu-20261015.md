# Preparación fría: diagnóstico pareado finito

Run `20261015-162727-7e0bcb51`, base `14dadb9` más nuevo instrumento: **1 PASS en121.14s**, sin omisiones. Fuentes verificadas independientemente, raíz/pytest ausentes, directorio temporal y contenedores propios retirados; unidad terminal inactive/MainPID0. Mismos límites del adaptador propio; sin pg_stat_statements ni perfiladores. [Recibo y180observaciones](cr09-preparacion-fria-cpu-terminal-20261015.json).

Tres bloques alternos, conexión PostgreSQL física nueva por brazo;30peticiones reales por conexión,6rutas ES/EN×5ciclos,10k sintéticos y proyección refrescada una vez. No se omite ninguna petición ni se añade calentamiento. Igualdad exacta de HTML en listado/búsqueda; en detalle se verifica firma/listing/revisión y sólo se normaliza timestamp del target. Estado200/no-store/proyección comprobados.

| Media por petición | Actual threshold5/auto | Experimental threshold0/force_generic_plan |
|---|---:|---:|
| CPU PG, primeras6 |59.444ms|51.111ms|
| CPU PG, peticiones7–18 |44.167ms|31.667ms|
| CPU PG, peticiones19–30 |35.000ms|31.667ms|
| CPU PG, todas30 |43.556ms|35.556ms|
| CPU app, todas30 |127.352ms|119.594ms|
| Tiempo secuencial, todas30 |204.632ms|183.410ms|

CPU PG media por bloque actual44.333/42.000/44.333ms frente39.667/38.000/29.000ms experimental. Cuantización100Hz, no porcentaje causal global. Primera tanda actual también incluye mayor calentamiento del proceso Python que brazos posteriores: CPU app primeras6 bloque0=219.386ms frente116.776/118.549ms bloques1/2. Alternancia no elimina ese sesgo inicial y no constituye experimento de procesos Gunicorn fríos.

Planes al final de cada brazo actual:42,240ejecuciones genéricas y200custom; tras primera petición0planes. Experimental:82,690genéricas/0custom;21planes tras primera petición. Contadoresidénticos entre bloques. La configuración es experimental de sesión, no implementación productiva: excluye coste de SET/restauración eventual y combina dos factores (umbral del driver y selección de plan PG). ClientCursor instalado fuerza Prepare.NO incluso conthreshold0; fuera del helper no activa preparación. La diferencia de cardinalidad/cache de82 frente42también debe valorarse antes de retener una política.

Hay una contribución medible compatible con planificación inicial, pero esto **no atribuye el transitorio de carga** ni acredita p95. Conexiones son frías; buffers compartidos y proceso Django permanecen calientes. No hay worker/Beat/subida concurrentes en este diagnóstico. Tampoco se ha probado distribución de parámetros rara o filtros sesgados contra planes genéricos.

Decisión: no aplicar force_generic_plan global ni declarar resuelto. Próximo paso acotado: aislar preparación inmediata con el mismo plan_cache_mode=auto dentro del helper existente, mediante comparación de solicitudes y restauración en éxito/error/anidación. Sólo si produce beneficio suficiente y conserva semántica, valorar candidato y carga limpia posterior. No barrer parámetros ni excluir arranque. Última carga limpia sigue p951.361793s FAIL; CR09/N3 abiertos.
