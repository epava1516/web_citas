# Checkpoint de atribución del listado

Fuente `aedfa2db1d7b5e130e21da3cdda2315ba95fd79a`. Tres pruebas PostgreSQL correctas; fuentes, huellas de artefactos y limpieza verificadas. Ruta `/es/`, mismo seed y nivel de instrumentación. Una petición por tamaño mediante DjangoClient; no es carga TCP concurrente.

| Candidatos | Queries | SQL execute (s) | Listings creados | Validaciones (calls / s) | Render HTML (s) | Request (s) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 70 | 0.370903 | 100 | 100 / 0.197959 | 0.101740 | 1.122757 |
| 1000 | 70 | 0.538131 | 1000 | 1000 / 1.669809 | 0.069146 | 3.826421 |
| 10000 | 70 | 3.359683 | 10000 | 10000 / 18.604750 | 0.078160 | 34.650646 |

[Datos completos por modelo, procedencia, prefetch y patrones SQL redactados](evidencias/listado-coste-checkpoint0110.json). Cada patrón conserva calls, total_time y mean_time en segundos; se verificó que calls y tiempos reconciliaran con los totales SQL. Parámetros y literales sensibles no se conservan. Relaciones materializadas se registran por modelo; memberships por relación son referencias, no filas SQL ni entidades distintas.

SQL execute observa el intervalo del cursor, con comunicación/driver/buffering; no separa CPU PostgreSQL ni fetch/conversión posteriores. Supone 33,04%, 14,06% y 9,70% del request respectivamente. No alcanza la heurística prefijada de predominio del 50%; no se ejecutó EXPLAIN ni se instaló pg_stat_statements. No se concluye ausencia de coste SQL o contención bajo concurrencia.

A 10000: contexto 15,560136s; validaciones directas 18,604750s; iteración Listing 4,203557s; iteración Photo 6,993817s; prefetch de fotos 7,103854s. Iteración incluye SQL lazy/fetch/conversión/from_db; prefetch incluye iteración; contexto contiene prefetch. Validación y render pueden ejecutar SQL lazy. Estos intervalos se solapan: no sumarlos ni atribuir total−SQL a validación Python.

`rows_returned` (filas entregadas por consulta), `rows_affected` (filas modificadas) y `rows_scanned`/`rows_examined` (trabajo de lectura del motor) son not_measured. Objetos ORM y rowcount no sirven para deducirlos. CPU/waits/locks/I/O/RSS, serialización separada y materialización CPU exclusiva también son not_measured. Sin reset de cachés OS/PG; ejecución secuencial 100→1000→10000, caché Django DummyCache, host compartido e instrumentación con coste propio.

Decisión: priorizar trabajo repetido dentro de validate_submission, medido directamente, y localizar construcción/validación de formularios de detalles/contacto antes de aplicar reutilización limitada a una petición. Mantener controles completos por candidato, elegibilidad, orden, recuento y páginas de24; exigir equivalencia negativa y repetir este mismo checkpoint antes/después. Contexto sigue siendo sustancial; los contadores de objetos no prueban por sí solos predominio de materialización.

Carga contractual intacta:10000 anuncios/20rps/900s, mezcla documentada y uploads limitados, p95<800ms y errores<1%. Demora del generador p95≤10ms/p99≤25ms/máximo≤100ms, noemitidas0%, timeout65s y drain70s. El antecedente conserva INVALID; la corrección independiente del cliente no acredita una mejora del backend. Este checkpoint no emite PASS/FAIL contractual ni sustituye el próximo ensayo.

## Localización dentro de validación

Diagnóstico posterior fuente d607759: tres tamaños y misma instrumentación ampliada entre filas; PostgreSQL correcto, fuentes y limpieza verificadas. [Eventos completos](evidencias/listado-formularios-coste0110.json). A10000, constructor SnapshotDetails9,980923s/10000 llamadas, full_clean3,724850s; Contacts constructor1,099341s/full_clean1,216976s. full_clean contiene campos/clean/post_clean: no sumar estos subeventos. Request33,503094s; no atribuir su diferencia respecto a la matriz anterior a mejora del backend, que permanece intacto.

Siguiente cambio elegido: preparar campos SnapshotDetails una vez por contexto de petición y preservar campos independientes por formulario e instancia, con limpieza nativa por candidato. Evitar memoizar autorización, elegibilidad o resultados completos. Constructor domina el coste medido dentro de esa validación; no demuestra que sea el único coste del request. Condición de aceptación: equivalencia positiva/negativa, normalización e independencia de campos y comparación con esta misma instrumentación.

## Perfil por regla previo al siguiente cambio

[Fuente be3753f, perfil completo](evidencias/listado-reglas-perfil0110.json): PostgreSQL correcto, fuentes/artefactos/limpieza verificados. Una petición control30,371242s, después instrumentada35,367333s; diferencia4,996091s incluye efectos de caché/host, overhead causal not_measured, sin ajuste. Cada regla registra calls, inclusive_time, exclusive_time, mean_exclusive_time, max_exclusive_time e identidad/tiempo de hijos descontados. Solo hijos directos: descendientes no se descuentan dos veces; pruebas deterministas2 correctas. Tiempo exclusivo incluye trabajo interno no instrumentado.

Contexto12,4407s exclusivos contiene ORM/prefetch sin separar en este perfil. BaseForm5,8091s exclusivos y SnapshotChoice deepcopy2,2399s/50000calls acreditan coste concreto de construcción de campos. publication_ready0,0827s/10000calls no justifica memoizar representación. Siguiente cambio: reducir trabajo de copia/configuración de campos con independencia verificada; controles por anunciante/anuncio/sujeto/gestor/versión documental/estado vigente siguen individuales. No se declaran documentación o representación invariantes.

Secuencia restante: optimización y equivalencia → matriz comparable100/1000/10000 → filtro concurrente60s prefijado en docs17 → contrato900s solo si filtro correcto. Sin aumentos de avance ni cambio del INVALID histórico.

## Coste de firmas del prefetch y corrección

[Perfil contextual3959115](evidencias/listado-contexto-reglas0110.json): signature10000calls/6,406163s exclusivos; regional_hashes10000/0,186832s. Estos campos no son consultados por el guard. Se difieren solamente en el prefetch _pv_photos; no se alteran valores ni comprobaciones de publicación. [19 pruebas PG actuales](evidencias/listado-firmas-diferidas-n1-0110.json) comprueban ausencia de lectura lazy y equivalencia ante estados/comparación/retirada, privacidad y descubrimiento.

[Matriz y perfil posterior9c6a844](evidencias/listado-firmas-diferidas-coste0110.json): cuatro casos correctos, fuentes y limpieza verificadas. Matrix100/1000/10000 request0,974027/2,776461/24,108752s,70queries cada uno; SQL0,375054/0,345650/1,730470s. En10000, contexto9,685189s y validación13,949500s, render0,046671s. Antes de este cambio, request29,382847s/contexto15,702330s/validación13,206931s: mejora de contexto observada, validación no mejora en esta muestra.

El perfil idéntico posterior no observó conversiones de firmas; prefetch6,216760s inclusive/contexto15,200100s inclusive. SQL del perfil7,977020s supera3,513686s del anterior; control operativo27,713210s frente28,732207s y profiled31,672056s frente33,082562s. Variación de ejecución/cachés/host; no presentar el ahorro de JSON como reducción idéntica de total en todas las muestras ni restar SQL para obtener validación. Objetos Blob permanecen10000; SQL rows y overhead causal not_measured. Próximo: filtro concurrente60s prefijado, no900s si falla, sin reinterpretarFAIL diagnóstico oINVALID histórico.

## Definiciones de campos y bindings independientes

[N1 c56e1d8](evidencias/listado-form-binding-n1-0110.json):20 casos PG correctos, fuente/huellas/limpieza verificadas. Solo SnapshotDetails/ContactsForm auditados comparten definiciones estáticas dentro del contexto (clase, catálogo fresco del mismo contexto, idioma y opciones/fuente fijas). Cada binding reconstruye data/instance/initial/errores/cleaned_data/bound_fields; ejecuta limpieza nativa/modelo y unique por revisión. No resultados de validación o autoridad compartidos. .details de uso directo conserva campos/widgets/QuerySets independientes. Pruebas alternan entradas válidas/inválidas y revisiones, normalizan Telegram y verifican aislamiento.

[Matriz y perfil2f081a3](evidencias/listado-form-binding-coste0110.json),4 casos correctos, mismos niveles de instrumentación respectivos:100/1000/10000 total0,966779/2,161328/17,584575s y SQL0,324834/0,331529/1,676246s,70queries cada uno. En10000, una construcción de cada formulario y10000full_clean por cada clase, validate_submission10000,8,076934s. Contexto9,081715s/render0,052465s. Anterior total24,108752s/validación13,949500s. Perfil control20,859073s/profiler23,245245s, overhead causal not_measured. Prefetch5,017926s exclusivo respecto a hijos observados/contexto4,821453s/SQL4,758966s; no partición de CPU, no deducción total−SQL. Dataset tiene títulos distintos: no se asumió igualdad de entradas ni se cachearon resultados de Details. Siguiente filtro concurrente60s con parámetros intactos antes de900s.

## FK compartidas por PK, sin decisiones compartidas

[CPU previo2a89579](evidencias/listado-prefetch-cpu0110.json) mide control17,491878s wall/15,835110s CPU del hilo; perfil23,347545/21,790201s. Picos de CPU cambian entre clases, no asignarlos a una regla estable ni atribuirlos a GC no observado. Prefetch nativo carga registros FK por PK de esta petición, nunca cache entre requests ni resultados de autoridad. Listing/Revision/Person/PhoneClaim y permisos/documento/action/grant/sujeto/manager_version/revocación/expiry se evalúan por candidato.

[N1 actual21 casos PG](evidencias/listado-fk-compartidas-n1-0110.json) verifica100candidatos, identidad compartida por PK, revocación individual aislada y agencia fallida en contexto nuevo. [Matriz y perfil0f96c87](evidencias/listado-fk-compartidas-coste0110.json):4 casos correctos y limpieza.100/1000/10000total0,891744/2,007792/15,584915s;74queries/SQL0,279214/0,308064/1,297713s. Cuatro lotes FK adicionales evitan objetos repetidos, noN+1. Agency1/Acceptance2/Document3/Municipality6/Province7/Region5/Blob2 por caso frente miles anteriores; son objetos, no filas SQL.10000validaciones/contexto7,752570s/validación7,410128s/render0,064007s. Control18,577181s wall/13,934498s CPU frente17,491878/15,835110s antes: CPU baja, wall sube, no mejora uniforme. Overhead causal/DBCPU/GC not_measured. Repetir filtro60s prefijado antes de900s; capacidad aún no acreditada.


## Limpieza focalizada de campos, sin mejora global acreditada

[N1 570de99](evidencias/listado-field-clean-cache-n1-0110.json):22 casos PG correctos, equivalencia, normalización por binding, salidas mutables independientes y entrada int/str separada. Reutilización limitada a Field.clean exitoso del prototipo de formulario de este contexto; clave incluye clase, idioma, instancia/configuración/validators del campo, catálogo fresco y entrada tipada completa con orden de listas. Excluye title; errores/entradas no admitidas pasan por limpieza nativa. clean_<campo>, Form.clean y validación de modelo se ejecutan por candidato, igual que elegibilidad/consentimiento/grant/documento/vigencia/revocación. Ninguna decisión documental o de representación compartida por nombre.

[Matriz/perfil d054292](evidencias/listado-field-clean-cache-coste0110.json):4 casos PG correctos y fuentes/artefactos/limpieza comprobados, misma instrumentación de tiempos con nuevo contador hits/misses (antes not_measured).100/1000/10000 total0,854359/1,900190/15,765501s,74queries, SQL0,301978/0,282475/1,856407s.10000contexto7,601364s/validación7,696159s/render0,064075s,10000validaciones;219978hits/22misses. Títulos únicos permanecen; otros campos clonados comparten entradas, no extrapolar tasa de hits al tráfico real.

Perfil Details._clean_fields10000calls:wallinclusive/exclusive1,832492s,mean0,000183249s/max0,001843893s; CPUexclusive1,822286s frente2,08976s anterior. Sin hijos instrumentados dentro de esta regla; no implica ausencia de trabajo interno. Reporte conserva hijos directos descontados una vez para todas las reglas, no resta descendientes otra vez. Control18,203370s wall/14,024448s CPU vs anterior18,577181/13,934498s; profiler23,405015/19,271369s. Matriz total10000 empeora respecto15,584915s anterior, validación7,696159 vs7,410128; ahorro focalizado no mejora global acreditada. Una muestra por caso, cachés/host y coste del contador/profiler; control response retenido, overhead causal not_measured, sin corrección aritmética. No total−SQL como validación. SQL no domina≥50%: EXPLAIN no activado; filasSQL/DBCPU/waits/locks/IO/GC/p95porregla siguen not_measured.

Siguiente filtro60s prefijado, sin instrumentación interna de reglas; comparar validez y saturación, no capacidad contractual. Mantener INVALID histórico y contrato20rps/900s sin cambio. Si no supera criterios, documentar motivo y detener escalado a900s; siguiente refactor requiere evidencia específica nueva del contribuyente residual.


## Filtro concurrente posterior terminal

[Fuente f2fbd93, informe y ledger](evidencias/benchmark-short-field-clean-cache0110.json):60s/10000anuncios/20rps/1200programadas,6rutas ES/EN/4workers/1upload302. FAIL diagnóstico con generador válido:1200emitidas,18éxitos/1182timeouts,0omitidas/pendientes finales,1182pendientes al cierre>20. Generador p952,848475ms/p994,829423ms/max8,630807ms, límites10/25/100ms intactos. p95observable65,002971s, errores98,5%,elapsed124,972380s incluyedrain. Verificación independiente de ledger/contabilidad/manifest/fuentes/huellas/limpieza completa. No900s; no nueva conclusión contractual, INVALID anterior intacto. No atribuir variación de demora del generador al backend ni concluir cuello por tiempos parciales del servidor.

Siguiente decisión: no elegir otro refactor de autoridad/modelo todavía. validate_submission exclusivo CPU2,500647s/10000calls y Details._post_clean1,546589s localizan contribuyentes, pero el primero contiene predicados y construcción no desglosados. Perfil focalizado equivalente de esos eventos antes de compartir resultados o alterar ejecución; registrar sus dependencias reales y negativas. _post_clean contiene validación nativa por modelo, no omitirla por semejanza de datos. Reutilización Field.clean sigue candidata local: ahorro focalizado medido sin mejora global, no desplegada/aceptada como capacidad. Ninguna reducción de paginación/elegibilidad/orden/recuento autorizada por este FAIL. Concurrencia: queries/SQL/materialización/validación/render/CPU/RSS/DBwaits/locks/IO not_measured; no sustituir con la matriz síncrona.
