# Preparación de la consulta real de hidratación: CPU

Run `134051-3b8bb033`, base `3e75fa8` más test explícito:1PASS/86.51s, fuentes intactas y limpieza independiente de raíz/hijo/backend/temporal/PG/Redis. [Recibo, huella y bloques](cr09-preparacion-hidratacion-cpu-terminal-20261015.json).

Capturada en memoria la SELECT de hidratación real de páginas1/2 del directorio,7533bytes y dos conjuntos de parámetros distintos con24filas cada uno. Sin exportar SQL/parámetros/filas. Mismo backend/snapshot readonlyRR y política jitoff/joincollapse1; igualdad exacta de todas las filas en cada operación. Tres variantes,8calentamientos y tres bloques rotados de12ejecuciones por variante;108operaciones medidas,100Hz CPUbackend. Sin pg_stat_statements.

| Variante | CPU media por SELECT | CPU por bloque |
|---|---:|---|
| Client binding actual Django |10.278ms|10.833/10.833/9.167ms|
| Server binding sin preparar |11.667ms|10.833/11.667/12.500ms|
| Server binding preparado |3.889ms|3.333/4.167/4.167ms|

Una consulta preparada presente;39usos genéricos y5custom. Se ajustó prepare_threshold sólo en esta conexión desechable y se restauró a su valor anterior; cursor_factory global de la conexión no cambió. Psycopg instalado3.3.6 y código Django5.2.17 revisados: Django deshabilita preparación por defecto para compatibilidad de poolers, puede configurarse; prepare_threshold=None deshabilita incluso prepare=True, por eso el experimento lo habilita explícitamente. El cursor nativo ClientCursor no soporta preparación. [Django5.2](https://docs.djangoproject.com/en/5.2/ref/databases/#server-side-parameters-binding), [preparación Psycopg](https://www.psycopg.org/psycopg3/docs/advanced/prepare.html), [tipos de cursor](https://www.psycopg.org/psycopg3/docs/advanced/cursors.html). Documentación web Psycopg muestra rama3.3.7dev; comportamiento verificado también en fuente instalada3.3.6.

Decisión: señal suficiente para diseñar candidata **acotada a materialización de lecturas de página**, usando soporte de cursor de Django/Psycopg y restauración de atributos en finally; no cambiar configuración global, migraciones, escrituras u otras rutas sin prueba. El ahorro corresponde a esta consulta, no al request entero ni a causalidad global de host. Server binding sin preparar no mejoró CPU.

Antes de adopción: comprobar repetición de páginas con parámetros distintos, tipos/JSON/UUID/zonas horarias, invalidación de datos/reglas/catálogos y vigencia después de preparar, restauración tras éxito/excepción y conexión posterior usable; conservar RR, límites de dirty/unknown y guardia nativa. Después comparar demanda SQL/CPU actual antes de justificar carga limpia. Ningún código de producto cambiado por el experimento; último p95 limpio16.572804FAIL, sin aceptación CR09/N3.
