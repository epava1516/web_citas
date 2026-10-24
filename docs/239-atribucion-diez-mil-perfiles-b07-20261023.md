# B07 — Atribución explícita a diez mil perfiles

## Evidencia y decisión

El diagnóstico268 de 100 perfiles y el269 de 1.000 están auditados PASS, con 192 y 224 lecturas respectivamente. El269 tardó 531,770 s de JUnit, incluyendo preparación y oráculos. No se repiten. Para completar la escala explícita de la mezcla final falta 10.000. La única edición del instrumento añade ese parámetro; el cuerpo de función y los casos anteriores permanecen idénticos, comprobados por reversión exacta y AST. Esta comprobación estática no acredita ejecución nativa.

## Protocolo270

Ejecutar una vez `tests/beta_committed_attribution_diagnostic.py::test_committed_attribution[10000]` mediante `scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --fixture-snapshots --isolate-test-broker --timeout 10800`. PostgreSQL 17, Redis 7.4 y compilación nativos. CI ordinario serial: no representa las cuotas kernel 8 CPU/8 GiB del contractual, TCP ni concurrencia.

Fixture sintética: 10.000 perfiles distribuidos 7.000/3.000, 2.000 derechos; mutaciones confirmadas de 14 exclusiones, 9.986 visibles y 1.991 patrocinios. Refrescos previo al plan y posterior, estadísticas y oráculo nativo fuera de las ventanas. Cero marcas pendientes antes y después. No datos reales ni proveedor externo.

Primera/intermedia/última página por municipio y texto vacío/photography, ES/EN: para 6.986 visibles páginas 1/146/292; para 3.000 páginas 1/63/125. Veinticuatro rutas de listado/búsqueda y cuatro fichas de extremos protegidos. Cada ruta tiene una lectura de calentamiento, cinco controles separados, una instrumentada y una posterior a restaurar los parches: 28/140/28/28, total 224.

Contar `Model.from_db` con guardia de ausencia de overrides y calibración nativa de una instancia Listing antes de limpiar el contador; instancias por modelo, llamadas de validación de binding, filas escalares de publicación, SQL del driver por fase, render inclusivo y CPU del proceso. Mantener paridad de IDs, orden, recuento y etiquetas en cada petición; identidad exacta de funciones y descriptor restaurada, contadores inmóviles en lectura posterior. No sumar filas escalares a ORM ni render a SQL; otros modelos no prueban relaciones recorridas, llamadas no son decisiones independientes, SQL del driver no es CPU PostgreSQL. Cinco controles por ruta son descriptivos, sin SLO percentil ni mejora causal.

## Presupuesto y relevo

Límite protector de 10.800 s para pytest; los controles nativos previos de 10.000 tardaron 4.333,792–7.128,003 s de JUnit con otras fixtures o ventanas. El coste269 es evidencia de preparación de otra escala, no una extrapolación lineal de latencias. No ejecutar otras baterías ni observadores a la vez. No repetir corto262 ni contractual265. No modificar producto para acelerar el diagnóstico.

Antes de lanzar: Ruff, prueba estática y actualización dirigida del grafo con AST sólo del instrumento, semántica de los documentos modificados y encabezado17, sellado y enlaces, todos con recibo Telegram. Congelar fuentes completas, bytes del protocolo, grafo y helpers. Wrapper, watcher, callback y compactador persistentes con PID/start_ticks/sesión/argv verificados; aviso de inicio y prepausa confirmados. Pausar el mismo objetivo; la shell solicita compactación durante la espera, avisa al terminar y lo reactiva conservando objetivo y consumo, sin sondeos del modelo.

Tras terminar, auditar antes de editar las fuentes congeladas: igualdad prerregistro/lanzamiento/runner/árbol, protocolo original, JUnit y JSON, distribución, 28 rutas, 224 lecturas, contadores, paridad, restauración, PostgreSQL/Redis/compilación, pasos, limpieza real Docker/PID/temporal, Telegram y callbacks de compactación/reactivación. Preservar FAIL/ERROR antes de corregir; un fallo del auditor no autoriza repetir la carga. PASS sólo acredita este diagnóstico, no capacidad ni cierre B07. Recursos por servicio a 10.000 siguen separados y pendientes.

B07-270 preparado: atribución explícita a 10.000 perfiles, 28 rutas y 224 lecturas; protocolo y límite protector de 10.800 s. Sin cambios de producto ni aceptación de capacidad. Ocho de 18 puntos cerrados; B07 abierto.


## Resultado270 auditado

B07-270 auditado: atribución explícita a 10.000 perfiles PASS; 224 lecturas en 28 rutas, paridad nativa y restauración verificadas. Fuentes 1.702/producto 628 intactos y limpieza confirmada. Ocho de 18 puntos cerrados; B07 abierto.

Corrida `20261023-035257-16e33ffa`: un caso PASS en 4.810,166 s de JUnit. Auditoría `artifacts/beta-promotion-fix-20261020/attribution270-audit.json`, anterior a estas ediciones: igualdad de las 1.702 fuentes entre prerregistro, lanzamiento, CI y árbol, protocolo original intacto, PostgreSQL 17/Redis 7.4 y compilación nativos; contenedores, procesos y temporal ausentes, Telegram confirmado. Solicitud de compactación reconocida durante la pausa y reactivación automática del mismo objetivo con consumo conservado, sin sondeos del modelo.

Fixture sintética de 10.000 perfiles, 2.000 derechos, 14 exclusiones, 9.986 visibles y 1.991 patrocinios. Veinticuatro rutas de listado/búsqueda y cuatro fichas, ES/EN. Páginas 1/146/292 para 6.986 visibles y 1/63/125 para 3.000; texto vacío/photography. Por ruta: calentamiento, cinco controles, instrumentación y control posterior a restaurar parches. Paridad nativa de IDs, orden, recuento y etiquetas; sin marcas pendientes, identidades restauradas y contadores inmóviles tras restauración.

Listados/búsquedas: 34 SQL, 2–24 instancias Listing, 43–200 instancias de otros modelos, 4–48 llamadas de binding y 2–24 filas escalares; mediana descriptiva de 120 controles 336,156 ms. Cuatro fichas: 22 SQL, una instancia Listing, 20 de otros modelos, dos llamadas de binding y una fila escalar; mediana de 20 controles 49,560 ms. ORM no equivale a sujetos o relaciones recorridas; llamadas no son decisiones independientes, SQL del driver no es CPU PostgreSQL y render inclusivo no se suma a SQL. Cinco controles por ruta no acreditan SLO ni mejora causal. CI ordinario, sin crédito TCP, concurrencia, worker ni capacidad kernel 8 CPU/8 GiB.

La atribución explícita queda observada a 100/1.000/10.000 con 268/269/270. No se repitieron 100/1.000, corto262 ni contractual265. Pendiente: recursos por servicio a 10.000 tras la corrección259 del observador; preservar el negativo257 con cero muestras. Estudiar protocolo, reutilización y presupuesto antes de ejecutar. Sin cambios de producto ni nuevas invocaciones Claude V1; ocho históricas y consumo preservados. Objetivo general activo, sin aceptación beta global.
