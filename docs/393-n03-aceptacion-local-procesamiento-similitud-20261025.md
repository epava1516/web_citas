# N03 — aceptación local de procesamiento y similitud

25 de octubre de 2026. Proyecto en alfa. N03 queda verificado localmente en los escenarios finitos declarados. N00, N01, N03 y N06 aceptados: **4/13 bloques obligatorios**. Base de aplicación `5f68464`, con la corrección F1 de `fa64767`; las congelaciones identifican las fuentes completas. Esta acta no acepta N07, capacidad comercial ni apertura de beta.

## Requisitos, acciones y evidencia

El contrato340 y el roadmap341 exigen medir recepción→cola→procesado→utilizable, recuperación/reintentos y detector/confirmación/registro, variando originales, densidad, retención y concurrencia. Se aplican los criterios354 y los prerregistros378/380/382/384/386/389/391. La [auditoría final](evidencias/n03-aceptacion-verificacion-20261025.json) contrasta 13 citas, cinco puentes de fuentes y los JUnit originales. El informe nativo fue un insumo comprobado por Codex, no una aceptación de tercero.

| Acción del censo338 | Cambio o decisión | Evidencia aplicable | Límite y responsables conservados |
| --- | --- | --- | --- |
| route:R_photo_upload | Ingest y autoridad conservados | [379](379-n03-a-resultado-subida-cola-real-20261025.md): POST Client→Redis→prefork2→ready, 1PASS; duplicado sin otra tarea. Seis casos de fotos incluidos en los 49PASS de [390](390-n03-f1-resultado-limite-generaciones-20261025.md) | Tiempos379 históricos; no retimados tras B/F1. Sin HTTP por socket ni navegador. N07 conserva medios/publicación |
| task:T_apps.mediafiles.tasks.process_blob | Preparado ORB en B; fences en C, reparación ready en D y máximo cuatro generaciones en F1 | [381](381-n03-b-resultado-orb-local-20261025.md): paridad exacta/46PASS; 383:33PASS; 385:37PASS; 390:49PASS con worker real; [392](392-n03-f2-resultado-crecimiento-historico-20261025.md):3PASS de retención | Ready no es aprobación. Concurrencia acotada, no capacidad HTTP. N07 conservado |
| dispatch:0:apps/core/accounts.py:235 | Sin cambio: callback de token de cuenta, no tarea de fotos | 377: aceptación N06, callback/rollback/tokens; fuente idéntica a A | Conservar N02/N06/N07/N09, N10 para transporte y N12 condicionado a proveedor. Latencia fotográfica no aplicable |
| dispatch:5:apps/mediafiles/services.py:121 | Productor on_commit conservado | 379: una publicación real y ninguna por duplicado; ingest idéntico A→actual; regresiones390 | ID histórico preservado pese al desplazamiento de líneas. N07/N09 conservados |
| dispatch:6:apps/mediafiles/services.py:121 | Mismo productor y su lambda; conservar ambos IDs censados | Mismo testigo379/390; no son dos colas o funcionalidades distintas | No duplicar muestras. N07/N09 conservados |
| dispatch:7:apps/mediafiles/tasks.py:30 | Selector ready/Exists en D y presupuesto del consumidor en F1 | 385: cohortes0/1/10/100/101, una SQL y lote≤100; 390: Beat real60s, cuatro positivos y controles; 392: crecimiento histórico | Un queued/stale agotado puede enviarse una vez para liquidarlo como failed, sin generar. N07/N09 conservados |

La [matriz final](evidencias/n03-disposiciones-finales-20261025.json) sustituye la vista de trabajo para esta aceptación; conserva nueve requisitos y seis IDs. Los documentos388 y sus matrices originales permanecen como historia: sus afirmaciones anteriores a F1 sobre ausencia de límite no describen la candidata actual.

Puentes comprobados: views, models, publication_signals y accounts son idénticos a A. Services cambia sólo detect_matches en B y process en C/D/F1; ingest permanece íntegro. Tasks cambia sólo recover_media_jobs en D; process_blob y su decorador permanecen intactos. Similitud y detect_matches actuales son los medidos en B. F2 añade sólo un instrumento. La reutilización se justifica mediante identidad y regresiones pertinentes, no por fecha o parecido de nombres.

## Antes y después: tiempos de aplicación

B es el contraste comparable de optimización: 100 originales densos y 100 coincidencias, corpus idéntico de1580874bytes, OpenCV de un hilo y RNG diagnóstico1847. Seis llamadas seriales por versión: primera aparte y mediana de cinco posteriores. Pared y CPU del hilo; no sumar estos tiempos a379 ni a QA.

| Acción / escenario / medida | Antes | Después | Diferencia y límite |
| --- | ---: | ---: | --- |
| Detector denso100, pared primera |15,522s|12,901s|−16,9% observado; una muestra por versión |
| Detector denso100, pared mediana5 |14,954175s|12,729232s|−2,224943s / −14,878%; rangos14,761–15,314→12,455–13,287s |
| Detector denso100, CPU del hilo mediana5 |11,992421s|10,128819s|−1,863602s / −15,540%; rangos11,761–12,367→9,960–10,524s |
| Extracciones ORB / SQL / Match por llamada |200/1012/100|101/1012/100|99 extracciones menos; SQL y Match iguales, paridad de todos los campos MatchResult y método/score |
| Subida nueva: petición Client / entrada→ready observado (379,n=1) |Sin base equivalente|170,196ms /1393,651ms|Mejora no evaluable; referencia histórica sin retimar tras B/F1 |
| Subida nueva: publish→inicio / process en worker (379,n=1) |Sin base equivalente|4,622ms /1087,446ms|No evaluable; cola quiescente y prefork2, sin TCP/p95/SLA |
| Duplicado exacto: petición (379,n=1) |Sin base equivalente|81,640ms /20SQL /0 tareas nuevas|No evaluable; transición distinta de la subida nueva |
| Selector D: primeras cohortes |Referencia3–6ms|Candidata9–23ms|Coste mayor visible; contraste funcional, no ensayo de aceleración. Una SQL conservada |
| F1: ACK real de mensaje agotado (n=1) |Sin base equivalente|59,277ms|No evaluable: antes hacía trabajo prohibido; ACK SUCCESS conserva Blob failed4 |
| F1: primera publicación Beat / publish→ready de cohorte (n=1) |Sin pareja comparable|61,352s /1,267s|No evaluable; calendario60s, no CPU ni SLA |
| Detector con histórico0→10→100: mediana5 por cohorte |156,429ms(0)|175,145ms(10) /202,129ms(100)|Mismo código y distinta población: no aceleración causal.22SQL/1confirmación/1Match constantes |
| Callback de cuenta dispatch:0 |No aplica a fotografía|Sin nueva medida fotográfica|Asignación compartida conservada; no inventar latencia de fotos |

El testigo histórico327 separa atribución: detector1000 originales/cinco positivos3,199770s; detector100 densos14,392127s. Una llamada por cohorte, comparador caliente y firmas listas. En densidad alta: CPU de confirmación6,368067s, registro protegido3,709945s y comparación de firmas0,067510s. Estas medidas motivaron B; no son sus tiempos posteriores ni una distribución de carga. La reutilización fue verificada en379 y no exigió repetir por frescura.

Memoria B: pico Python de primera llamada6228745→6267437bytes (+38692), compensación acotada permitida en380 por la vida del preparado; mediana posterior6016090→6010513bytes. RSS máximo273356→273208KiB. Tracemalloc no abarca toda memoria nativa. F2 conserva corpus119478bytes y RSS high-water de proceso≈204MiB. Topes diagnósticos128MiB/1GiB cumplidos; no son presupuestos del servicio completo.

## Correcciones, negativos y suficiencia

- C: dos FAIL originales por escritura de generaciones antiguas, preservados. Los fences de attempts/started_at impiden escribir sobre otra generación y conservan el fallo propio posterior al derivado.
- D: cuatro FAIL originales de ready sin firma, histórico sólo, mezcla actual/histórico y original ausente, preservados. La candidata permite progresar a los actuales y deja fallo explícito cuando falta el original.
- F1: ocho FAIL y tres PASS originales, preservados. El guard bajo bloqueo impide una quinta/sexta generación antes de I/O, respeta cuarto intento, lease vigente y comparación de ready válido. Conserva contadores heredados y errores previos. CR05 sigue siendo un máximo por Blob, no sólo por mensaje.

La verificación pertinente actual390 tiene49PASS:11 de presupuesto,37 regresiones y el arnés real worker/Beat. Incluye FileNotFound con tres reintentos y esperas reales, ValidationError sin retry, Beat nativo60s, cohorte de cuatro y otro mensaje agotado sin generación. Prefork2 y SQL con rol restringido; no eager declarado como transporte real.

F2 tiene3PASS/18 llamadas: crecimiento histórico ortogonal con corpus y resultado exactos entre cohortes; ledger, revisiones, Blob y bytes intactos. La concurrencia se representa mediante dos conexiones PostgreSQL/barreras para generaciones y borrado/nuevo referente, alta concurrente del flujo de fotos y prefork2 real. Son intercalados definidos; no carga HTTP simultánea ni historial ilimitado.

Se conservan negativos geométricos, preparado inválido, fallback, bajo detalle, privacidad del original, EXIF, retirada y autoridad. Sin índice ni recorte oculto de candidatos. Todos los lotes tienen congelación, terminales originales, limpieza y Telegram sent. Codex volvió a inspeccionar JUnit, propiedades y fuentes. Las baterías independientes no se suman como una sola ejecución integrada.

El primer auditor final falló por usar la clave JSON actions en vez de census_action_dispositions; se preservó y corrigió antes del PASS. No se repitieron pruebas funcionales. Los301,561s de QA49casos y51,734s de QA3casos no son latencias de aplicación.

## Coste residual y continuación

Confirmación y registro crecen con los positivos reales. En F2 aumenta el tiempo observado con histórico sin aumentar las22SQL. El selector correcto cuesta más; esperas de retry y calendario Beat se separan del trabajo CPU. Los tiempos actuales son aceptables en alfa: se registra el coste y se avanza sin otra optimización marginal. Cualquier optimización sin mejora clara queda para el final del desarrollo; no se elimina trabajo obligatorio de corrección.

N03 queda aceptado localmente con estos límites. MOD09/N02 permanece diferido al final; N07/N09/N10 y B14/B15/B17 conservan sus obligaciones o condiciones. No se acredita80 000fotos, p95 universal, proveedor ni apertura. N11 conciliará la candidata integrada; N15 reconstruirá una vez el grafo antes del diferencial final del inventario, conservando111 e IDs.

Siguiente punto: N04, listado/búsqueda/ficha, familiasI01–I05. Partir de los testigos discovery de N01 y disponer cada elemento censado antes de cambiar producto.
