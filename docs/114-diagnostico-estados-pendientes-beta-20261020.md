# Diagnóstico de estados pendientes todavía públicos

Fecha:2026-10-20. Estado: diagnósticos100/1000 auditados con instrumento idéntico; sin optimización aplicada. B07/B08 abiertos; producto y límites sin modificar. Continúa [108](108-linea-base-beta-b07-20261020.md), [110](110-contraste-tcp-beta-b07b08-20261020.md) y [113](113-instrumentos-diagnosticos-beta-20261020.md).

## Escenario no cubierto por el backlog anterior

publication_state._state_page admite hasta48candidatos desconocidos; con49devuelve None y razón state_unknown_over_limit. discovery.results valida entonces la población nativa completa. El baseline anterior retiraba1%deanuncios antes de la selección; esos retirados pueden quedar fuera de candidates y no acreditan el coste de49candidatos todavía públicos. Esta lectura identifica el recorrido, no demuestra aún un problema de rendimiento ni justifica elevar el límite.

## Datos, controles y equivalencia

Instrumento explícito tests/beta_unknown_backlog_diagnostic.py, parametrizado100/1000. Ejecutar primero sólo100; revisar integridad, duración y coste antes de1000. No10000hasta conocer ambos tamaños. PostgreSQL/Redis propios y un worker pytest; misma preparación sintética de20%Top/Premium mediante servicios. Sin proveedores, pagos o datos reales, ni ampliación de recursos. Agencia/foto/geografía compartidas: no distribución nacional. READ_REPAIR real desactivado, sin worker de refresco y sin tareas eager durante el ensayo.

Tras refresh_all y cero marcas se leen todas las páginas ES y se conserva sólo su firma: hash de bytes, IDs ordenados, recuento y patrocinio. Seleccionar49candidatos publicados compatibles con búsqueda synthetic y marcarlos mediante publication_state.mark, sin alterar publicación ni derechos. Exigir exactamente49marcas persistentes. Volver a leer todas las páginas y exigir igualdad exacta de firmas, sin duplicados ni omisiones, y razón real state_unknown_over_limit.

Dos fases en orden fijo: fresh y unknown49. En cada una, cuatro rutas: listado ES/EN, búsqueda EN y página intermedia ES. Por ruta: una lectura caliente, cinco controles sin instrumentos, una observación SQL y otra cProfile/contextos; las tres últimas clases de lectura están separadas. Total64+2*ceil(N/24)HTTPClient:74para100y148para1000. Cuarenta controles, ocho calientes, ocho SQL, ocho perfilados y dos recorridos completos de paginación.

En controles medir wall y CPUthread de aplicación. CPU real del backend PG identificado mediante PID SQL/propiedad Docker/cgroup/start_ticks y schedstat antes/después del bloque, fuera del reloj. Verificar conexión estable. GC normal y sin collect artificial; sin profiler, wrappersSQL o sustitución del constructor de contexto dentro de los controles.

En observación SQL registrar sólo número/duración de execute: no incluye FETCH de cursores, ni constituye CPU de PG. En la lectura perfilada, envolver constructor nativo PublicationContext, registrar cantidad de filas e intervalo inclusivo, restaurar y conservar las60funciones principales por tiempo propio/inclusivo sin argumentos, SQL ni parámetros. No sumar intervalos inclusivos superpuestos ni atribuir a un contexto todo el tiempo de petición.

## Resultado y límites

Los percentiles de cinco muestras son descriptivos: p95/p99 equivalen al máximo, no estiman cola/SLO. Orden fijo y diferencia de estado no constituyen A/A/C balanceado ni ROI de una optimización. Comparar inventario/paridad, ruta y volúmenes de contexto; localizar coste antes de proponer cambios. No elevar48/1000, truncar candidatos, cachear autoridad ni introducir reparación en GET para hacer pasar la prueba.

Guardar beta-unknown-backlog-N.json, JUnit, fases completas, fuentes congeladas, recibos Telegram y limpieza auditada. Un PASS sólo acredita integridad y equivalencia de este diagnóstico. No acepta TCP/capacidad, PRODUCTION, comprobaciones de proveedores, geografía nacional, beta ni900s. El corto112359 sigue siendo el testigo TCP vigente hasta una corrección con contraste completo.

## Corte100 y decisión de ampliar

Primer intento134006-ce9df949:0PASS/1FAIL/0ERROR/0SKIP antes de medir, por guarda que consultaba una opción Django inexistente. [Negativo auditado](evidencias/b07-unknown100-guard-negative-20261020.json), fuentes/limpieza/Telegram1792503677184854467-206584 confirmados; sin payload ni medición. Se corrige únicamente la guarda a config.celery.app.conf.task_always_eager efectiva, sin activar tareas eager ni cambiar producto o protocolo.

Correctiva134354-1406b5a1:1PASS/0FAIL/0ERROR/0SKIP,80,20s pytest,74HTTPClient; cinco páginas completas iguales,37lecturas state/trusted_state y37fallback/state_unknown_over_limit,49marcas persistentes. [Auditoría](evidencias/b07-unknown100-audit-20261020.json) recalcula firmas, muestras, CPU y rutas; fuentes congeladas/limpieza/Telegram1792503945501113221-230465 confirmados antes de editar.

| Ruta | Mediana fresca ms | Mediana49pendientes ms |
| --- | ---: | ---: |
| Listado ES |163,152|392,377|
| Listado EN |178,154|364,587|
| Búsqueda EN |180,067|359,242|
| Intermedia ES |172,119|401,193|

CPUthread mediana fresca117–133ms y fase posterior234–279ms; CPUbackend real media por lectura21–26ms y76–85ms. Observación SQL separada33execute frente47, sin FETCH. Contextos perfilados de24filas frente100+20derechos. Son observaciones inclusivas separadas, no tiempos sumables ni prueba de N+1; no atribuir toda la latencia al constructor.

La integridad y duración permiten ampliar sólo a1000 con idéntico instrumento y recursos, sin otra batería. El resultado100 no demuestra escalado a1000/10000 ni aceptación TCP. Límites48/1000 y READ_REPAIR permanecen intactos; no se aplica una optimización.

## Corte1000 auditado

134917-d6b37058:1PASS/0FAIL/0ERROR/0SKIP,302,01s pytest,148HTTPClient;42páginas por recorrido,74lecturas state/trusted_state y74fallback/state_unknown_over_limit,49marcas persistentes. [Auditoría](evidencias/b07-unknown1000-audit-20261020.json) recalcula firmas/CPU/rutas y verifica SHA idéntico del instrumento y dependencias respecto100. Fuentes/limpieza/Telegram1792504490594297092-263817 confirmados antes de nuevas ediciones.

| Ruta | Mediana fresca ms | Mediana49pendientes ms |
| --- | ---: | ---: |
| Listado ES |193,099|2037,348|
| Listado EN |191,541|2006,302|
| Búsqueda EN |236,419|1998,118|
| Intermedia ES |181,285|1990,282|

CPUthread mediana fresca119–154ms y fase posterior1740–1785ms; CPUbackend real media31–47ms y163–180ms. Execute observado33/47sinFETCH, contextos24 frente1000+200. En perfil ES, contextos1,424s/0,337s inclusivos y guardas1200llamadas; esos intervalos están instrumentados, se superponen con sus hijos y no sustituyen controles. El trabajo Python crece con la población validada, no sólo con49marcas. No atribuirlo todo a SQL ni declarar una prueba de N+1 por contar dos contextos.

Se conserva el producto original y no se amplía aún a10000. La siguiente propuesta debe reducir trabajo con las mismas garantías y contraste prefijado. El estudio de reutilización del segundo contexto queda como hipótesis secundaria no ensayada; el frente prioritario es evaluar el conjunto pendiente completo sólo bajo censo comprobado e instantánea propia, con guardas y fallback completo para otros casos.

La hipótesis prioritaria se prerregistra en [115](115-contraste-segunda-fase-nativa-beta-20261020.md). Los resultados100/1000 y el recorrido original permanecen en sus cortes; no se reinterpretan como aceptación de esa copia experimental.
