# CR09: proyección con filas pendientes validadas en la lectura

Ejecución `20261016-075521-6674bd02`, base `8d72065`. **No integrar por este resultado:** la reducción no alcanza el 10 % fijado antes del ensayo. Se conserva como diagnóstico, sin cambio de producto, triggers o bloqueos.

## Algoritmo experimental y equivalencia

Dentro del RR propio y con censo/versionado completo, el brazo mantenido excluye todas las marcas Dirty. El brazo nativo contiene únicamente IDs pendientes que la regla acaba de validar, con fecha y relevancia obtenidas de las fuentes actuales. UNION ALL une conjuntos disjuntos y conserva orden/recuento/paginación; la guardia final sigue íntegra. Fuera de ese dominio permanece la ruta anterior. Es distinto del UNION de IDs aplicado a la población general y rechazado en 004909.

Antes de medir: `075201-7d923ec0`, **1 PASS / 66,94 s / 40 comparaciones** de cuerpos, IDs ordenados, recuento y páginas inicial/intermedia/última. Cuatro transiciones: borrador privado con marca controlada, publicado→pausado, pausado→publicado, cambio de texto/fecha nula; listado/búsqueda ES/EN. Las marcas/generaciones permanecen. El primer fixture `074956-4864e029` falló antes de comparar porque un borrador vacío no producía la marca esperada; se preservó y se añadió una marca explícita controlada, sin modificar el algoritmo. No es una prueba de subida real ni de invalidación de Photo.

## Comparación

10.000 anuncios sintéticos, PostgreSQL real propio, WSGIHandler sin Client ni captura de contexto; una marca controlada constante. A/B código actual idéntico; C prototipo. Tres bloques ABC/BCA/CAB, seis calentamientos y 16 medidas por brazo/ruta: 288 medidas. Conexión calentada por brazo, PID constante, planes observados fuera del reloj. GC normal en requests; colección explícita sólo antes del calentamiento para aislar basura del brazo anterior. No perfiladores.

| Ruta Dirty1 | Referencia A/B, wall medio | Prototipo | Cambio wall | Cambio CPU |
|---|---:|---:|---:|---:|
| Listado ES | 315,30 ms | 295,89 ms | −6,16 % | −2,93 % |
| Búsqueda EN | 349,77 ms | 325,82 ms | −6,85 % | +2,78 % |

A/A es estable con la cota previa del 10 % en wall/CPU en ambas rutas. Los tres bloques reducen wall en cada ruta. El candidato respeta la cota CPU, pero no el ahorro wall ≥10 % exigido en ambas rutas. No se rebaja ese umbral después de ver el resultado. Esto acredita una reducción aislada en este fixture, no un ahorro suficiente según el criterio previo ni una mejora del p95.

El test termina **1 PASS, 228,90 s**, 0 fallos/errores/exclusiones, por paridad y diagnóstico completado; `eligible_for_integration=false` expresa la decisión. Las respuestas mantienen cuerpos nativos, 200/no-store, ruta observada esperada en 132 llamadas por brazo y marcas/generaciones intactas. El JSON conserva medias, controles, preparación y SQL counts; las 288 muestras están en el artefacto local `dirty-projection-roi.json`.

## Límites y continuidad

La marca se fuerza durante toda la comparación sin el calendario de Celery/Beat: puede exagerar el peso de esta ruta respecto al escenario contractual. No se suman porcentajes con otros ensayos. No hay concurrencia, revisión N2 integral, carga HTTP nueva ni aceptación N3. Los triggers conservadores y la corrección RateForm del producto permanecen. Último p95 limpio: 1,013029795 s, sin nueva medición.

Fuentes congeladas y JUnit verificados independientemente; controlador/hijo identificados por PID/start_ticks terminados, temporal retirado, contenedores propios ausentes y cgroup vacío. Límites habituales conservados: controlador 4 CPU/3584 MiB/swap0/512 tareas, PostgreSQL 1 CPU/1536 MiB y Redis propio. Sin producción, proveedores ni Claude nuevos.

La búsqueda comunitaria incluyó [Stack Overflow sobre refresco e invalidación](https://stackoverflow.com/questions/23906977/refresh-a-materialized-view-automatically-using-a-rule-or-notify); aporta contexto, no una solución confirmada para este algoritmo. Las garantías usadas se contrastaron con [PostgreSQL 17, Repeatable Read](https://www.postgresql.org/docs/17/transaction-iso.html#XACT-REPEATABLE-READ) y la [API UNION de Django](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#union). La evidencia de equivalencia y rendimiento es exclusivamente la ejecución local descrita.
