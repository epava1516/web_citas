# Diagnóstico de proyección y contraste Claude — 0110

Fuente medida `63ca87a`. PostgreSQL sintético propio;4 casos correctos547,23s, SHA/fuentes/limpieza revisados. [Evidencia completa](evidencias/listado-proyeccion-coste-diversidad0110.json). Los informes Claude son propuestas revisadas; estas medidas pertenecen a Codex y no aceptan CR09.

## Matriz comparable

Cada variante/cantidad conserva la misma base para native-control, native-profile, projected-control, projected-profile, en ese orden. `/es/`, DjangoClient, página24, DummyCache; cachés OS/PG compartidas no vaciadas. Control sin profiler y perfil son poblaciones distintas: no cruzar sus tiempos para atribuir fases. Una muestra por modo; diferencia perfil−control incluye overhead y efecto de cachés, overhead causal `not_measured`.

| Variante | N | Ruta | Queries | SQL execute s | Control s | Perfil s | Listings construidos | Otras construcciones | from_db calls |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| contractual | 100 | native | 74 | 0.417 | 0.692 | 2.082 | 100 | 790 | 890 |
| contractual | 100 | projected | 89 | 0.224 | 0.754 | 2.013 | 24 | 471 | 294 |
| contractual | 1000 | native | 74 | 3.789 | 4.771 | 14.027 | 1000 | 7090 | 8090 |
| contractual | 1000 | projected | 88 | 4.126 | 4.416 | 8.300 | 24 | 2268 | 291 |
| contractual | 10000 | native | 74 | 5.710 | 14.456 | 86.574 | 10000 | 70090 | 80090 |
| contractual | 10000 | projected | 88 | 7.126 | 10.262 | 34.699 | 24 | 20268 | 291 |
| diverse | 10000 | native | 74 | 4.627 | 13.772 | 87.288 | 10000 | 70090 | 80090 |
| diverse | 10000 | projected | 88 | 7.216 | 22.282 | 140.604 | 24 | 20268 | 291 |

Queries son llamadas cursor.execute. SQL acumulado contiene driver/servidor/I/O y overhead del profiler, excluye fetch; no es CPU de PostgreSQL. Patrones normalizados, `calls`, `total_time`, `mean_time` y objetos por modelo/procedencia están completos en el JSON; literales/comentarios/binds se redactan, parámetros nunca se guardan. `post_init` cuenta construcciones, incluidas instancias transitorias de Revision/Rate; `from_db` cuenta llamadas de hidratación, sin inferir filas SQL. Ejemplo proyectado10000:24Listing/24Person/24PhoneClaim,10025Revision/10024Rate construidos,291calls from_db agregadas; no son20292filas SQL. Desglose de origen DB por modelo y entidades únicas: `not_measured`.

## Validación y reglas

Observación `sys.setprofile` síncrona sin reemplazar atributos de reglas; paridad de cuerpo/count/página y ruta con/sin profiler obligatoria. Validación nativa directamente observada en validate_submission; pruebas positivas por candidato en positive se informan aparte, no se suman como partición del request.

| Variante | N | Ruta | validate_submission calls / inclusive s | positive calls / inclusive s | Render inclusive s |
| --- | ---: | --- | --- | --- | ---: |
| contractual | 100 | native | 100 / 0.498 | not_applicable | 0.255 |
| contractual | 100 | projected | 24 / 0.131 | 100 / 0.206 | 0.289 |
| contractual | 1000 | native | 1000 / 3.697 | not_applicable | 0.314 |
| contractual | 1000 | projected | 24 / 0.109 | 1000 / 1.975 | 0.295 |
| contractual | 10000 | native | 10000 / 37.373 | not_applicable | 0.288 |
| contractual | 10000 | projected | 24 / 0.097 | 10000 / 17.599 | 0.262 |
| diverse | 10000 | native | 10000 / 38.654 | not_applicable | 0.264 |
| diverse | 10000 | projected | 24 / 0.108 | 10000 / 122.046 | 0.278 |

Por cada regla el JSON registra calls, inclusive/exclusive, mean/max exclusive, CPU de este hilo y cada hijo instrumentado descontado. Se resta solo el hijo directo una vez, nunca sus descendientes otra vez; reconciliación comprobada independientemente. Exclusive es relativo a estos hijos, incluye trabajo no instrumentado. No hay p95 por llamada. Iteradores registran segmentos de yield, no objetos únicos. SQL, fetch lazy, construcción, validación y render pueden solaparse; SQL no es hijo descontado por este profiler y puede quedar en exclusive del llamador. No atribuir ese exclusive íntegramente a Python ni total−SQL a validación.

En contractual10000 proyectado: __init__ inclusive15,417s/exclusive15,367s, positive17,599s/3,443s, Model.__init__20292calls/exclusive8,715s; native_content30000calls/exclusive4,114s; huella2calls/inclusive0,291s. La construcción del contexto incluye lecturas primitive-values/fetch y SQL, no es materialización exclusiva. En diverso, BaseModelForm.__init__20006calls/exclusive62,825s es el mayor evento exclusivo, incluye construcción/copia e internos no instrumentados. No atribuirlo a deepcopy concreto sin otro perfil.

## Diversidad y decisión

El caso diverso conserva reglas, autoridad, fotos, relaciones, idiomas y whatsapp booleano; añade sufijos alfabéticos válidos a descripciones y10000Telegram únicos válidos. El control nativo confirmó10000elegibles y la proyección conservócount/cuerpo/página1 antes de aceptar cifras. La matriz no recorre417páginas: la población ordenada y páginas1/2/3 con mutaciones se verificaron en la regresión50; esta limitación queda explícita. Proyección:10000positivas/0fallback, pero Details/Contacts pasan de1/1 limpiezas completas a10000/10000; tarifas2 en ambos. Control proyectado22,282s frente a nativo13,772s en diverso, mientras contractual proyectado10,262s frente a nativo14,456s. La repetición sobreestima la ventaja observada; no representa distribución real ni demuestra robustez ante ella.

Siguiente optimización elegida: reducir construcción de formularios por contenido diverso, comparando la estrategia de binding privado y campos del guard nativo con la proyección. Antes de aplicarla, perfilar hijos no observados de BaseModelForm.__init__ y demostrar equivalencia del binding/campo/normalización y clave completa; no quitar textos/contactos del memo ni llamarlos invariantes. Reutilización estrictamente intra-request: idioma, identidad del catálogo/configuración de campos auditados y datos completos tipados; autoridad/documento/grant/check/phone/expiry/revocación se verifican por candidato sobre datos actuales, jamás se memoizan como representación genérica. Lectura actualT1 y guardnativo de páginaT2 conservan el alcance del diseño; no se acredita linealizabilidad de toda la población ante cambios concurrentes fuera de la página. No hay mejora de ese próximo cambio medida ni aplicada.

SQL alcanza como máximo49,708% del request instrumentado (proyectado1000), por debajo del criterio prefijado≥50%; no se ejecutó EXPLAIN en esta matriz y no se atribuye dominio a PostgreSQL. La consulta principal projected10000 observó4,413s cursor.execute, motivo para diagnóstico focalizado adicional, no para inventar plan/DBCPU o cambiar índices. pg_stat_statements no utilizado. `rows_returned`, `rows_affected`, `rows_scanned`, DB CPU/RSS/waits/locks/IO, allocations/request y overhead causal: `not_measured`.

## Filtro concurrente

La matriz verifica funcionalidad/diagnóstico, no INVALID/FAIL/PASS de capacidad. Proceder al filtro ya prefijado60s/10000/20RPS/1200dinámicas/4workers/1upload, mezcla1/3listados/búsquedas/fichas ESEN; generador10/25/100ms,0%omitidas, timeout65s/drain70s; p95<800ms/errores<1%, pendientesventana≤20/final0. Observar ruta sin envolver reglas, mantener ausencias explícitas.900s solo si cumple todos los criterios. INVALID contractual anterior intacto. No atasco resuelto, producción aceptada ni avance porcentual por estas mediciones.

Resultado del filtro `98f35ea`: [evidencia](evidencias/listado-proyeccion-concurrente-corta0110.json). Generador válido (p95/p99/max2,619/3,905/17,250ms,0omitidas),1200emitidas/54éxitos/1146timeouts/0pendientesfinales,1upload302. p95observable65,001932s/error95,5%/1153pendientes al60s: **FAIL**, no900s.106cierres dinámicos200 del servidor no equivalen a54éxitoscliente.72proyectados con10000positivas/0fallback/24hidratos: p95WSGI9,207139s, SQLexecute5,786469s, CPUhilo4,018974s, render0,073532s;34fichas nativas completadas.1094emitidas sinruta completada capturada quedan not_measured. SQL acumulado/WSGIacumulado51,475% activa ahora el criterio≥50%: diagnóstico separado readonly de lecturas dominantes en nueva base sintética, sin añadirlo retrospectivamente a la matriz. La decisión contractual debe distinguir SQL/driver/fetch/construcciones de contexto; la construcción de Forms domina el diverso, no se presume que cierre el contractual donde solo hay1Details/1Contacts.

## Lecturas SQL y siguiente piloto

[EXPLAIN separado](evidencias/listado-proyeccion-sql-planes0110.json), fuenteab6ab1c,1PGcorrecta61,14s; nueva base sintética10000/SQLwrapperligero/sinprofiler/post_init.88queries/SQLexecute1,523743s/Clienttotal5,242400s; ruta projection10000positivas/0fallback/24hidratadas. No es equivalente al perfil anterior o a los workers concurrentes; diferencia de total no se atribuye a backend nuevo, no hubo cambio de aplicación.

Después del request se ejecutaron3lecturas readonly conEXPLAINANALYZEBUFFERS. La consulta values principal observó0,671255s cursor.execute; planplanning12,200ms/execution736,073ms, rootUnique10000rows/1loop y sortexternalmerge6520kB, tempread815/write816blocks, sharedhits503062/read0. TresLimit latestcheck tienen10000loops cadauno; son loops internos, no queries/red o rows_scanned. Travelthrough vacío:cursor0,244743s versusplanplanning6,535ms/execution0,038ms; Services:cursor0,237745s versusplanplanning4,981ms/execution3,080ms. Son ejecuciones distintas sobre cachés calientes: no restar para atribuir CPUcliente/driver puro. Planrows son streams por nodo/loop en ese EXPLAIN, no filas medibles del request normal; buffers del plan no acreditan IOglobal o memoria/request. No aumentar work_mem, cambiar índices o eliminarDISTINCT sin equivalencia y evidencia de ahorro.

Siguiente optimización contractual seleccionada como piloto: reducir preparación de grandes listas de parámetrosUUID en consultas de relaciones, manteniendo exactamente los IDs capturados por la fase inicial. Medir adaptación/binding/execute/fetch antes/después y comprobar alternativa con parámetroarrayUUID válido contraIN, incluyendo vacíos/duplicados/ajenos. No reemplazar ese snapshot de IDs por subquery viva que reevalúe candidatos en otro momento; no anticipar paginación o cambiar elegibilidad/orden/count. El resultado del piloto todavía es not_measured. La construcción de formularios diversos sigue una regresión secundaria medida, sin presumir que su corrección resuelva el contrato repetido. Nuevos perfiles/gates/matriz y filtro prefijado antes de900s; elFAIL corto y elINVALID contractual anterior permanecen.
