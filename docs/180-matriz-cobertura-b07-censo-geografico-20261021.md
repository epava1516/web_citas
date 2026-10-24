# B07 — Cobertura de evidencia y corrección del censo geográfico

Estado: corrección de metadata focal auditada; B07abierto. Ocho de18cerrados. Esta matriz contrasta[108](108-linea-base-beta-b07-20261020.md),[roadmap103](103-roadmap-beta-clasificados-20261020.md) y requisitos vigentes; no redefine aceptación ni convierte planificación en evidencia.

Cobertura vigente: [matriz actual, corte259](214-cobertura-vigente-b07-20261022.md). La tabla siguiente conserva el corte histórico inicial; consultar la matriz actual para pendientes.

## Defecto y corrección

El manifiesto de `20261021-170829-cac4e830` declara10000publicados pero geography suma9999: su fuente recorría únicamente filas con agencia, omitiendo la publicación individual. No es desaparición de un perfil de la carga; es censo incompleto. Se conserva el manifiesto original y el FAILde latencia1241,749ms, sin reescritura ni reclasificaciónINVALIDretroactiva.

`tests/beta_promotional_load_fixture.py` agrupa ahora todas las publicaciones por municipio en una consulta separada, declara geography_scopeyexigesumaigualpublished. Mantiene selección comercial de agencia, llamadascreate_order/receive_event, distribución de derechos y población. No cambia código de producto. El contadorSQLdepreparación gana una consulta de metadata: las30213consultas históricas de179permanecen como referencia de ese corte, no como contador esperado del fixture nuevo.

Corrida `20261021-180020-335274c4`:2PASS/0FAIL/0ERROR/0SKIP,53,905sJUnit sumados por caso. [Auditoría](evidencias/b07-geography-metadata-focal-20261021-audit.json) confirma prueba de dos municipios:1individual+9agencia=10publicados y2derechos nativos; finalizador conserva5guardasnegativas/8tablas y huellas de dominio. Fuente congelada,628app/config/templatesiguales, contenedores/temporal/PIDretirados y Telegramconfirmado. No carga grande nueva ni aceptación de diversidad nacional.

## Matriz de cobertura al cierre de este corte

| Requisito de B07 | Evidencia disponible | Límite o pendiente |
| --- | --- | --- |
| Versión y fuentes | Huellas por runner; aplicación628idéntica en el focal y último corto | Herramientas/fixtures han evolucionado; no presentar todos los cortes como una única candidata ejecutada |
| Inventario100/1000/10000 | Diagnóstico histórico de108y sus auditorías; último corto10000/2000 | Matriz histórica no es TCP ni aceptación actual de todos los escenarios |
| Emisión comercial nativa | Órdenes/eventos sintéticos por servicios reales;2000derechos en177 | Sin proveedor, cobro o verificación real de personas |
| Censo territorial completo | Defecto9999/10000identificado; focal corregido10en2municipios | 184verifica10000sumados en el manifiesto grande; distribución representativa pendiente |
| Distribución territorial | Cohorte grande comparte municipio/agencia/foto; focal dosmunicipios | No distribución nacional ni cobertura de una mezcla territorial representativa |
| Estados orgánico/promocional/backlog | Doce escenarios históricos108y pruebas de retirada posteriores | No una matriz TCPactual con todos los estados y carga |
| Filtros combinados y páginas profundas | Diagnóstico secuencial histórico con ciudad/idioma y última página | Falta mezcla TCPactual preregistrada y percentiles fiables para estas rutas |
| Listado/búsqueda/ficha ESEN | 177controlCIy184cortoacotado:1200dinámicas sinerrores;184p95432,620ms | 177FAILválido por p95;184PASSnumérico, 186confirmaciónúnicaPASS381,841ms;900s/otrosescenarios pendientes |
| Generador/contabilidad/upload | Auditoría177:generador válido, cero omitidas/finalespendientes, upload302persistido | 177ventana20;184ventana3/final0 y generador válido, sin aceptación global |
| Primeraslecturas y capturas separadas |177conserva frías, observadores opcionales apagados;176instrumentado separado | PASSinstrumental no reemplaza control limpio ni aísla overheadcausal |
| CPU/memoria/colas por servicio | Perfil porfunción/proceso y límites sync175–176; calibración181 con series propias10perfiles | OcupaciónhandlernoesCPU; faltan series CPU/RSS porservicio y edad de colas con mezcla y volumen requeridos |
| Hardware/cuotas | Manifiesto177:8CPU/afinidad8, RAMhostaprox23GiB, servicios propios enhostcompartido | El CI histórico conserva su ámbito;182kernel,183calibracióny184primer corto10000/2000en8CPU/8GiB; 186confirmaciónúnicaPASS; mezclas adicionales pendientes |
| PRODUCTION/checked | Existen validaciones de configuración y simuladores declarados | No escenario de capacidad equivalente ejecutado ni proveedorreal; no simularlo como verificación real |
| Contractual900s | Modo187/protocolo189 ejecutado:18000dinámicas/15uploads | INVALID189 por generador143,154ms; no aceptación. Cliente corregido191 y calibrado192;193/194 pasan cortos individualmente, sin900automático |
| Integridad de artefactos y limpieza | Auditorías por corte y recibosTelegram | No equivalen a aceptación global ni reutilización automática entre fuentes diferentes |

## Siguiente evidencia necesaria

Revisar primero los colectores de recursos existentes y sus límites de propiedad para preparar captura de servicios propios sin enumerar o atribuir cargas ajenas. Calibrar únicamente un escenario funcional pequeño si se necesita corregir el instrumento; no otro corto60spara volver a medir el mismo FAIL. Después fijar mezcla territorial/filtros/páginas/estados y presupuesto de recursos antes de cualquier comparación nueva. Cada alcance debe conservar testigos y costes de instrumentación explícitos.

La hipótesis de estructura de historial179queda rechazada por ahorro insuficiente; no se reactiva para avanzar esta matriz. B08–B11 conservan sus requisitos; no se cierran por documentación, grado del grafo o refactor cosmético. Sin proveedores, publicación ni datos reales.

Actualización terminal189:900s ejecutados pero INVALID por máximo generador143,154ms>100ms. No acredita capacidad;18000éxitos/15uploads y p95375,277ms son descriptivos. [Auditoría](evidencias/b07-beta-http-900s-invalid-20261021-audit.json). Sin repetición automática; B07 abierto.

Actualización194: cliente corregido191, calibración192 y dos cortos193/194 auditados individualmente PASS.194:1200éxitos/0errores/p95461,745ms/ventana6/final0; única confirmación consumida. Censo10000/10000 completo pero un municipio; diversidad territorial y demás pendientes de esta matriz permanecen abiertos. No tercer corto ni900automático. Véase [confirmación194](194-confirmacion-corto-cliente-corregido-b07-20261021.md).

Actualización196: preparación opcional7/3 verificada con10perfiles, visibilidad nativa y filtros ciudad ESEN por IDs/recuento;3PASS en PostgreSQL real. Sin activación TCP ni representatividad nacional; distribución grande y filtros combinados/páginas profundas siguen pendientes. Véase [preparación196](196-preparacion-territorial-explicita-b07-20261021.md).

Actualización197: equivalencia funcional PostgreSQL10/100 auditada4PASS; a100, reparto70/30 y20páginas ciudad/conysintexto/ESEN con IDs y recuentos exactos, sin duplicados. No oráculo independiente de ranking, escala1000/10000 ni TCP; estas carencias siguen pendientes. [Evidencia197](197-filtros-paginacion-territorial-b07-20261021.md).

Actualización198: comparador comercial independiente verifica secuencias completas de todas las páginas territoriales10/100;4PASS PostgreSQL. Comparte autoridad nativa y primitivo PostgreSQL de relevancia, no helpers de orden comercial. No cubre autosubida ni concurrencia,1000/10000 oTCP. [Corte198](197-filtros-paginacion-territorial-b07-20261021.md#resultado198).

## Equivalencia territorial199

B07-199 secuencia territorial auditada: tres runners con4+1+1PASS; escalas1000/10000 repartidas700/300 y7000/3000,24páginas seleccionadas por escala hasta30/292. Censo nativo y orden comercial de referencia verificados;628fuentesproducto intactas, limpieza y Telegram confirmados. Compactación solicitada y reactivación automática del mismo goal comprobadas. Equivalencia funcional, sin capacidadTCP ni cierreB07;8de18. Véase [protocolo y resultado198](198-escala-equivalencia-territorial-b07-20261021.md). Siguen pendientes estados/backlog, recursos por ventana y mezclaTCP territorial preregistrada.

Actualización200: B07-200 calibración TCP territorial auditada1PASS/87,533sJUnit:10perfiles7/3,14sondas200 y60dinámicas exitosas con ciclo14rutas conciliado,1upload persistido.628producto intactas/fuentes congeladas/limpieza/Telegram verificados;ERROR Ruff previo conservado. Sin capacidad grande ni cierreB07,8de18. Véase [calibraciónTCP](199-calibracion-tcp-territorial-b07-20261021.md).

Actualización201: B07-201 calibración TCP del ciclo equilibrado auditada1PASS/87,098sJUnit:60éxitos20listado20búsqueda20ficha/30ES30EN,18slots14rutas/18sondas200 y1upload persistido;10perfiles7/3.628producto/fuentes/limpieza/Telegram verificados. No entorno kernel ni carga grande ni cierreB07;8de18. Véase [mezcla en tercios](200-mezcla-territorial-tercios-b07-20261021.md).

Actualización202: B07-202 calibración territorial kernel auditada1PASS/92,397sJUnit:10perfiles7/3/2derechos,60éxitos20porcategoría30poridioma/18slots14rutas y1upload persistido.8CPU8GiBswap0/kernel, generador máximo4,346ms,628producto/fuentes/limpieza/Telegram verificados. Sin TCPgrande ni cierreB07;8de18. Véase [calibración kernel](201-calibracion-territorial-kernel-b07-20261021.md).

## Corto territorial203

B07-203 corto territorial auditado1PASS/898,983sJUnit:10000perfiles7000/3000 y2000derechos,1200éxitos0errores/p95520,383ms/ventana6/final0;42slots30URLs con secuencia completa verificada,400porcategoría600poridioma,1upload persistido. Generador3,408/6,497/29,454ms p95/p99/máximo;8CPU8GiBswap0,628producto/fuentes/protocolo/limpieza/Telegram confirmados. Compactación y reactivación del mismo goal comprobadas. PASS corto acotado, sin900automático ni cierreB07;8de18. Véase [protocolo y resultado203](202-corto-territorial-kernel-b07-20261022.md). Esta evidencia cubre mezcla territorial y páginas seleccionadas; no representa diversidad nacional ni todos los estados.

## Recursos kernel207

B07-207: calibración Docker del observador auditada 1PASS/93,336sJUnit, 10perfiles7/3 y2derechos,60éxitos20porcategoría/30poridioma y1upload.69muestras:62previas/6carga/1posterior completamente dentro de sus fases; fuentes628producto, cuotas y limpieza confirmadas. Observador host fuera de presupuesto, sin capacidad grande ni cierre B07;8de18. Véase [calibración del observador](204-calibracion-observador-kernel-b07-20261022.md). CPU por subintervalo y memoria por servicio quedan instrumentados a10perfiles; no recursos a volumen10000, edad de colas ni capacidad limpia. Una muestra final no permite CPU posterior.

## Identidad y reposo209

B07-209: identidad y reposo del observador auditados 1PASS/92,221sJUnit; seis identidades mínimas archivadas y70muestras completas62previas/5carga/3posteriores, deltaCPU posterior≈1,04s.10publicados7/3 y2derechos,60éxitos/1upload,628producto y limpieza confirmados. Diagnóstico host separado; sin capacidad grande ni cierre B07,8de18. Véase [resultado209](205-identidad-reposo-observador-b07-20261022.md). La limitación de CPU posterior del corte207 queda cubierta sólo en209; sigue pendiente volumen grande, estados/backlog y edad de colas.

## Backlog nativo211

B07-211: backlog nativo auditado 1PASS/97,329sJUnit;10preparados/9visibles, dos marcas (retirado y elegible),24páginas HTTP equivalentes y404ESEN.60éxitos/1upload; worker real repara2marcas, despacho11,775ms y marca–limpieza≤5,505s observados.628producto, cuotas, limpieza y Telegram confirmados. Funcional pequeño, sin capacidad ni cierre B07;8de18. Véase [resultado211](206-backlog-nativo-despacho-b07-20261022.md). Cubre retirado y candidato aún elegible mientras están sucios y su reparación real a10perfiles; las24páginas no equivalen a matriz grande ni a49desconocidos. Tiempos de despacho y límite superior de edad de marcas separados, no residencia exclusiva de cola.


### Control213 — equivalencia territorial49 auditada

B07-213: equivalencia territorial verificada en PostgreSQL real: 2PASS,160páginas ESEN,100perfiles por cohorte con0/20derechos,49elegibles sucios y1retirado. Instantánea propia extendida y fallback READCOMMITTED coinciden con reparación manual. Fuentes/628producto, limpieza, Telegram, reactivación del mismo objetivo y solicitud de compactación comprobados. Sin crédito de capacidad ni worker; B07 abierto,8de18. Evidencia: `docs/evidencias/b07-equivalence213-unknown49-20261022-audit.json`. No nueva batería ni repetición TCP.


### Equivalencia territorial215 — resultado

B07-215: equivalencia territorial49 auditada en PostgreSQL real: 6PASS/544páginas, cohortes100/1000/10000 con0/20%derechos. Censo nativo completo; páginas grandes primera/intermedia/última, sin recorrido exhaustivo. Instantánea propia y READCOMMITTED coinciden con reparación manual;628fuentes producto intactas. Limpieza, Telegram, reactivación del mismo objetivo y solicitud de compactación confirmados. Sin crédito de capacidad ni worker; B07 abierto8de18. Véase [protocolo y resultado](208-escala-territorial-49pendientes-b07-20261022.md) y [auditoría](evidencias/b07-equivalence215-unknown49-scale-20261022-audit.json). No reemplaza recursos a volumen, worker con backlog grande, mezcla TCP ni PRODUCTION/checked; no habilita repetir900.

### Recursos217 — resultado instrumentado

B07-217: diagnóstico territorial instrumentado auditado:1PASS/900,148sJUnit,10000publicados7000/3000 y2000derechos sintéticos;1200dinámicas exitosas y1upload. p95 observado538.876ms; generador máximo15,662ms.182muestras (62previas/117carga/3reposo), seis identidades verificadas;628producto, fuentes, cuotas8CPU/8GiB, limpieza, Telegram, compactación y reactivación del mismo objetivo confirmados. Sin aceptación de capacidad ni cierre B07;8de18. Véase [protocolo y resultado217](209-recursos-territoriales-volumen-b07-20261022.md). No sustituye el corto limpio203 ni el backlog grande con worker.

### Preparación218 — backlog escalable

B07-218: preparado backlog funcional escalable100/1000/10000 con49elegibles y1retirado;72guardas PASS y Ruff PASS. Worker/Beat nativos intactos, sin ejecución integrada nueva ni capacidad ni cierre B07;8de18. Véase [protocolo219](210-backlog-escalable-worker-b07-20261022.md).


### B07 — negativo219 y preparación220

B07-220:219 terminó1FAIL antes de carga por exceder9,877s el slot Beat+5s; fuentes, limpieza, Telegram, compactación y reactivación verificados.220 separa selección/oráculo previos del tramo mutación/HTTP;72guardas PASS, integración corregida pendiente. B07 abierto;8de18.

Véase docs/210-backlog-escalable-worker-b07-20261022.md; no nueva aceptación. Preservados los ocho consumos ClaudeV1 anteriores, sin invocaciones nuevas.


### Consolidación222 — resultado221

B07-222: integración221 auditada1PASS/152,603s con100perfiles,20derechos,50marcas y99visibles; worker real limpió50marcas,60dinámicas exitosas y1upload. Compactación solicitada y reactivación del mismo objetivo con consumo conservado verificadas; Telegram confirmado. Sin capacidad ni cierre B07;8de18.

Detalle en docs/210-backlog-escalable-worker-b07-20261022.md. Siguiente: prerregistrar funcional1000; sin10000/900automático. Histórico8invocaciones ClaudeV1 preservado, ninguna nueva.


### Corrección224 — negativo223 e integración225

B07-224:223 interrumpida por watchdog180s, sin JUnit; negativo auditado. Corregidos watchdog2400s y vida del contenedor3000s sólo para funcional backlog escalable;81guardas PASS, Ruff PASS. Slot Beat+5s y criterios intactos. Integración225 pendiente; B07 abierto,8de18.

Detalle en docs/210-backlog-escalable-worker-b07-20261022.md. Histórico8invocaciones ClaudeV1 preservado; ninguna nueva.


### Resultado225 auditado

B07-225: funcional1000 INVALID por generator_delay_p99=28,649766ms>25ms;60dinámicas y1upload correctos no validan la medición. JUnit1FAIL/0ERROR; fuentes y protocolo congelados intactos, limpieza, Telegram, compactación y reactivación del mismo objetivo verificados. Causa exclusiva no establecida; sin repetición ciega ni relajación de umbrales. B07 abierto,8de18. Diagnóstico siguiente en documento210; ninguna nueva aceptación de capacidad ni cierre de B07.


### Diagnóstico226 y prerregistro227

B07-226: diagnóstico optativo del generador separa despertar del planificador, creación de tarea e inicio HTTP; emisión y umbrales intactos.18guardas PASS/21,59s, Ruff PASS. Integración227 funcional1000 prerregistrada, aún sin resultado;8de18,B07 abierto. Desarrollo diagnóstico: sin nueva aceptación de capacidad ni de B07. Véase documento210.


## Resultado227 auditado

B07-227: funcional1000 auditada PASS,60dinámicas y1upload correctos;50marcas antes de carga, reparación nativa51→0 y24páginas reparadas. Generador p99=17,944489ms; diagnóstico sin causa exclusiva ni mejora atribuida. Fuentes, limpieza, Telegram, compactación y mismo objetivo verificados;8de18,B07 abierto.

Ensayo `20261022-092104-3a98b036`: JUnit1PASS/0FAIL/0ERROR/0SKIP,585,812s de caso. Población1000, geografía700/300,200derechos comerciales sintéticos (67premium/133top),999visibles tras retirar un perfil.42slots/30rutas,42sondas frías200;60dinámicas correctas (20listado/20búsqueda/20ficha,30ES/30EN) y1upload302persistido. HTTP p95=608,325805ms y p99=730,537891ms en carga funcional3s, no capacidad sostenida. Preparación estadística ANALYZE en cinco tablas registrada.

Se verificaron24páginas frescas, dos primeras páginas pendientes de ciudad mayoritaria sin texto ES/EN y24reparadas seleccionadas; las dos pendientes coinciden exactamente con su versión reparada. La comprobación nativa vuelve a verificar los49elegibles y la ausencia del retirado; no es HTTP exhaustivo de todas las páginas. Mutación22,564386ms; comprobación pendiente1,149873s; margen3,733922s respecto al slot original Beat+5s. La tarea web364b87d7-e498-4440-a95f-a4dcf96f8098 terminó SUCCESS, sin eager, y limpió51marcas hasta0;50de la cohorte estaban presentes antes de carga. No equiparar51 a tamaño de cohorte ni afirmar que todas las60peticiones observaron estado sucio. Publicación→inicio10,914820ms incluye el recorrido emisor/broker/despacho, sin atribución exclusiva a cola; ejecución318,975644ms. Las cotas marca→limpieza de toda la tarea abarcan0,456036–5,783021s y no identifican individualmente la cohorte en el evento.

Generador p95=2,291298ms, p99/máximo17,944489ms, límites originales conservados. Peor fila d-14: prevista0,7s, despertar0,717836588s, encolado0,717842882s y emisión0,717944489s. Descomposición17,836588ms +0,006295ms +0,101606ms; todas las61filas mantienen orden y suma, subida comparte despertar del slot. GC no solapa el peor intervalo. Esto localiza el tramo observado, no demuestra causa exclusiva del SO/CPU/event loop; sobrecoste causal no medido. El cambio226 añade diagnóstico y no acredita mejora frente al INVALID225, que se conserva.

Observador exterior al presupuesto:534muestras,525antes/6durante/3después; identidades completas de seis servicios y del proceso observador, cotas de captura y deltas CPU poscarga verificados. Espera de preparación212,712060s y vida del observador489,181513s; CPU propia10,222008s. Perfil real8CPU/8GiB/swap0/storage≤20GiB, cuatro workers/un hilo y GC sin cambios. Fuentes completas1689iguales entre prerregistro/lanzamiento/runner/árbol, protocolo congelado por bytes/SHA y628fuentes de producto intactas antes de esta edición. Limpieza real confirmada sin recursos etiquetados ni problemas de archivo.

Evidencia: artifacts/beta-promotion-fix-20261020/backlog227-audit.json y audit_backlog227.py. La primera ejecución del auditor falló por un literal de memoria PostgreSQL alterado al adaptar el identificador221a227; se corrigió sólo ese literal, se revisó el diff y la auditoría pasó sin repetir TCP. Ambos resultados terminales Telegram confirmados. Telegram de finalización, reactivación del mismo objetivo con consumo preservado y solicitud de compactación REQUEST_ACKNOWLEDGED verificados. La auditoría se ejecutó antes de editar documentación/grafo.

Siguiente: evaluar el presupuesto de preparación y observación para10000 con cohorte49+1 usando los tiempos observados y la equivalencia215; prerregistrar el siguiente ensayo sólo tras resolver su encaje temporal. No lanzar automáticamente10000 ni900, ni aceptar B07 por este PASS funcional.


## Preparación228 y protocolo de integración229

B07-228: preparación y captura separadas para backlog; oráculos nativos completos conservados.83guardas PASS/19,22s, Ruff PASS. Sólo10000 recibe preparación5400s/watchdog9000s/vida9600s; captura600s/600muestras/8MiB y criterios HTTP intactos. Integración229 pendiente;8de18,B07 abierto.

Diagnóstico de encaje: en227 la espera previa a la captura fue212,712060s y el tramo antes de llegadas duró272,076242s, con525muestras de preparación. verify_pages evalúa por separado el censo nativo de dos ciudades y dos búsquedas; prepare_backlog construye otro oráculo para la cohorte antes del tick. Estos censos son deliberadamente independientes del estado derivado. No se deduce tiempo lineal exacto a10000; sí existe riesgo concreto de agotar600muestras/600s antes de carga. El resultado215 a10000 confirma un coste de equivalencia significativo; no ejecutar un ensayo previsiblemente truncado sin ajustar su preparación.

Cambio limitado a instrumentación y control: en backlog el escritor de fases se crea tras sondas frías, páginas frescas y plan de mutación, antes de buscar el siguiente tick nativo. resource_preparation_excluded registra inicio/fin monotónicos y ámbito excluido. No representa medición de recursos de preparación ni del oráculo reparado posterior a idle_after. Ambos censos,24páginas frescas y24reparadas seleccionadas y49comprobaciones nativas finales siguen ejecutándose; no se sustituyen por resultados anteriores ni se elimina PostgreSQL real. Los modos sin backlog conservan el comienzo anterior de captura.

A10000 únicamente: espera de preparación del observador5400s, watchdog pytest9000s y vida del contenedor9600s; el watchdog exterior11500s ya existente permanece. Cotas conservadoras de control, no objetivos de latencia ni tiempos observados. A100/1000 se mantienen1800/2400/3000; a10 los controles anteriores. Captura después de la señal sigue600s/600muestras/8MiB/.5s y tres muestras de reposo. Pruebas con reloj controlado verifican preparación2000s permitida y6000s rechazada bajo5400; guardas de modos/propiedad/fases y codec cubiertas.83PASS19,22s y RuffPASS no acreditan el nuevo recorrido Docker. Producto628 intacto.

229 previsto: una integración funcional10000 territorial con servicio de recursos y backlog49elegibles+1retirado;10000publicados,7000/3000,2000derechos sintéticos,9999visibles nativos. Misma imagen6936424,8CPU/8GiB/storage≤20GiB/swap0, cuatro workers/un hilo,workerBeat nativos,READ_REPAIRfalse yGCsin cambios.42slots/30rutas esperadas pero auditar las reales;60dinámicas/3s/20RPS/1upload. Dos páginas pendientes ciudad mayoritaria sin texto ESEN y404ESEN,50marcas verificadas antes/después de404;24páginas frescas y24reparadas seleccionadas, no HTTP exhaustivo ni todas las60peticiones sucias. Slot original Beat+5s y reparación≤45s conservados. Diagnóstico226 activo sin restar intervalos a criterios del generador.

Congelar fuentes/protocolo/grafo después de comprobar documentación; ejecución persistente única con Telegram previo y terminal, pausa, compactación y reactivación automática del mismo objetivo. Antes de una nueva decisión auditar fuentes completas, propiedad, contabilidad, fases/cotas y limpieza real. Cualquier FAIL/INVALID se conserva y no permite repetir por buscar verde.229 no se ha lanzado ni constituye aceptación. No900automático; B07 sigue abierto.


## Resultado229 auditado y siguiente paso

B07-229: funcional10000 auditada PASS;60dinámicas y1upload correctos,50marcas de cohorte y reparación nativa51→0.24páginas frescas,2pendientes y24reparadas. Preparación excluida de captura verificada; generador p99=6,680589ms. Fuentes, limpieza, Telegram, compactación y mismo objetivo verificados;8de18,B07 abierto.

Ensayo `20261022-094304-a4f41580`: JUnit1PASS/0FAIL/0ERROR/0SKIP,4957,631s de caso.10000publicados sintéticos,7000/3000 en dos ciudades,2000derechos comerciales y9999visibles tras retirar un perfil.42slots/30rutas,42sondas frías200,60dinámicas200 (20listado/20búsqueda/20ficha y30ES/30EN) y1upload302persistido. HTTP p95=1141,143596ms y p99=1195,208694ms corresponden a funcional3s; no capacidad sostenida ni mejora de producto.

Cohorte49elegibles distintos más1retirado,50generaciones comprobadas.24páginas frescas y24reparadas seleccionadas; las dos pendientes de primera página sin texto de ciudad mayoritaria ES/EN coinciden exactamente con sus versiones reparadas.404ES/EN conserva marcas; el oráculo nativo comprueba elegibilidad de los49 y ausencia del retirado. No es HTTP exhaustivo ni demuestra que las60peticiones observaran estado sucio. Mutación22,382365ms, verificación pendiente1,399852s, margen3,180985s al slot original Beat+5s.

Tarea web0ab29a7f-5364-4bf3-9ed1-448043609ac9 SUCCESS nativa,51→0, sin eager ni error de snapshot;50marcas de cohorte antes de carga. Publicación→inicio8,155576ms y ejecución316,583605ms; cotas marca→limpieza0,454740–6,030352s para toda la tarea, sin atribución individual de cohorte. El evento adicional no amplía la cohorte. Contabilidad Celery parcial se conserva en backlog229-audit.json; no atribución exclusiva a cola.

Generador p95=4,346843ms y p99/máximo6,680589ms dentro de límites originales. Peor fila d-34: despertar6,513488ms, encolado0,002153ms e inicio de corrutina0,164948ms. Orden y suma de61filas y despertar compartido de subida verificados; ningún GC solapa ese intervalo. Sin causa exclusiva ni sobrecoste causal medido, sin atribuir mejora al diagnóstico226.

Preparación explícitamente excluida:3162,103745s entre marcas; precede señal de captura y nuevo tick. Espera del observador3287,495974s bajo5400s y vida3299,443838s bajo6010s; CPU propia13,072708s fuera del presupuesto. Captura24muestras (13antes/8durante/3después), seis identidades completas, deltas CPU de reposo y cotas600s/600muestras/8MiB verificadas. No se mide preparación ni oráculo reparado posterior al reposo. Perfil8CPU/8GiB/swap0/storage≤20GiB, cuatro workers/un hilo y GC conservados.

Auditorías antes de editar documentación:1689fuentes iguales entre prerregistro/lanzamiento/runner/árbol; protocolo idéntico por bytes/SHA y628fuentes de producto intactas. Limpieza Docker real y archivo sin problemas. Evidencias backlog229-audit.json y audit_backlog229.py en artifacts/beta-promotion-fix-20261020; dos comprobaciones terminales PASS con recibos Telegram confirmados. Aviso terminal y reactivación automática del mismo objetivo conservando consumo verificados; compactación REQUEST_ACKNOWLEDGED y contexto compacto recibido. No nueva batería ni repetición TCP durante auditoría.

Siguiente: contrastar la cobertura acumulada100/1000/10000 con los estados mixtos exigidos por matriz180§16 y roadmap103, y preparar el mínimo incremento que cubra sus lagunas. Las poblaciones actuales publicadas con derechos no prueban por sí solas borrador/pendiente/pausa/caducidad/revocación ni producción. No900automático; B07 y aceptación beta global pendientes. Se conserva el protocolo229 anterior como registro histórico de preparación.


## Preparación231 — estados mixtos

B07-231: preparada equivalencia PostgreSQL de100perfiles en dos ciudades;14inelegibles de siete estados, dos derechos inactivos y20derechos nativos sintéticos. Prueba pendiente, sin carga ni aceptación;8de18,B07 abierto. Véase docs/211-estados-mixtos-territoriales-b07-20261022.md.


## Resultado231 auditado

B07-231: equivalencia mixta100 auditada PASS/142,990s;60páginas ESEN,14excluidos y86visibles,marcas0→14→0. Derechos suspendido/caducado pierden patrocinio sin ocultar perfil. Reparación manual, sin carga ni worker acreditados;8de18,B07 abierto.

Corrida `20261022-111510-f00a8bb0`:1PASS/0FAIL/0ERROR/0SKIP,142,990sJUnit.20páginas exhaustivas por fase fresca/mezcla pendiente/reparada; IDs ordenados, recuentos, unicidad, etiquetas y404ESEN de14inelegibles verificados. Cada motivo se aplica a un perfil orgánico y otro promocionado: borrador, procesando, pendiente, pausado, plazo caducado manteniendo published, retirado y consentimiento revocado. Las mutaciones preparan estados directamente; no acreditan transiciones de interfaz. Derechos nativos20 antes/después; tarjetas patrocinadas sumadas en las cuatro combinaciones idioma/texto80→44→44. Siete derechos corresponden a perfiles excluidos y otros dos pierden vigencia comercial;11promociones siguen elegibles. Ambos perfiles sin derecho vigente permanecen públicos.

Proyección pendiente y reparada producen firmas idénticas; todas las lecturas mantienen IDs/generaciones de marcas. Reparación explícita manual: no worker ni Beat acreditados por este caso. Perfil100 y dos municipios sintéticos70/30, no diversidad nacional. Sin producción, checked real, TCP ni percentiles de capacidad.

Auditoría antes de editar fuentes/documentación:1690huellas iguales entre prerregistro/runner/árbol, protocolo por bytes/SHA y628fuentes de producto intactas. PostgreSQL17/Redis7.4 reales, compilación nativa, todos los pasos y limpieza Docker/temporal/PID verificados. Telegram CI y auditoría PASS con delivery sent. Evidencias artifacts/beta-promotion-fix-20261020/mixed231-audit.json y audit_mixed231.py. Se conserva Ruff inicial EXIT1 (import desordenado) y lanzamiento EXIT2 rechazado antes de pruebas por faltar native-source; corregidos sin ocultar resultados. Prueba focal ejecutada una sola vez.

Siguiente incremento: integrar esta mezcla en el escenario de observación nativa con preparación fuera del slot, sin repetir la cohorte49 ya verificada. Antes de escalar hay que medir el coste de oráculos en el caso pequeño y congelar nuevo protocolo. PRODUCTION/checked requiere un escenario separado: capacity_beta_http.verify_owned_fixture rechaza PRODUCTION y promotion_exposure.enabled deshabilita promociones sintéticas allí. La metadata sintética de las pruebas checked no prueba proveedor real. Mantener umbral48, límite1000, no READ_REPAIR, presupuestos del generador y SLO originales. B07 abierto; sin900HTTP automático.


## Protocolo232 — reparación nativa

B07-232: preparado control mixto100 con worker y Beat reales propios; comprobación pendiente completa antes del arranque, reparación observada y limpieza exigidas. Integración pendiente;8de18,B07 abierto.

Se reutiliza el caso231 y se parametriza manual/native. La variante manual conserva sus comprobaciones; native requiere opt-in normal_worker_beat sin xdist. Ejecutar sólo el selector[native], con runner oficial, --benchmark-normal-refresh, --isolate-test-broker, --workers1 y dependencia librdb fijada. No repetir manual ni10000. Watchdog900s; no ensayoHTTP900s.

La variante nativa ejecuta antes del arranque todas las páginas frescas y pendientes y404ESEN, preservando marcas. Después verifica identidad efectiva de PostgreSQL y contenedor/puerto/etiqueta de Redis propio vacío; arranca worker Celery concurrencia2 y Beat con sus comandos habituales y generación aislada. Mantiene calendario nativo y no invoca refresh_all para reparar. Desde readiness exige≤45s hasta dirty0 y evento SUCCESS no eager correlacionado por UUID con publicación Beat, cleared≥14 y sin snapshot_error. Es reparación posterior a las lecturas, no escenario concurrente ni slot Beat+5s.

Detener primero Beat y después worker; comprobar PID/start_ticks, raíces terminadas y Redis vacío. Configuración temporal de media/delivery propia; ningún servicio normal ni proveedor. Guardar mixed-worker-repair.json, ledger y propiedad JUnit. Luego repetir el mismo oráculo nativo y todas las páginas reparadas, iguales a pendientes. La lista inicial sigue100/70–30/20derechos/14excluidos/86visibles; sin cambio de producto628. Las comprobaciones de cargas229 y de umbral49 se conservan separadas. Un PASS no acepta B07 ni capacidad.


## Adaptador de lanzamiento232

B07-232: selector nativo100 autorizado de forma exacta en runner serial con broker aislado; seis guardas CLI y Ruff pendientes de recibo. Primera solicitud rechazada antes de pruebas; integración real pendiente.8de18,B07 abierto.

El runner rechazó el primer selector porque normal_refresh sólo admitía contratoHTTP; no arrancó contenedores ni pruebas. Se conserva mixed232-rejected-preregister.json y su protocolo original. scripts/run_local_ci.py admite ahora exclusivamente el selector mixto[native] bajo focused/workers1 y --isolate-test-broker; selector manual o múltiple conserva rechazo, y el contratoHTTP anterior conserva compatibilidad. Se comprueban seis fronteras CLI sin contenedores. La primera ejecución del comprobador olvidó workers1 y falló; se corrige sólo su invocación, sin aflojar runner. Congelar de nuevo fuentes/protocolo tras grafo242 y recibos.


## Negativo232 y protocolo233

B07-233: preparación de broker aislada por generación; negativo232 auditado antes del arranque del worker. Se conservan claves previas y se exige reparación Beat/worker de14marcas. Integración233 pendiente;8de18,B07 abierto.

Corrida232 `20261022-112631-585f9c23`:1FAIL/0ERROR/0SKIP,116,261s de caso; CI ERROR y Telegram sent. La guarda broker.dbsize()==0 falló antes de arrancar procesos worker/Beat. No se archivó inventario de claves en ese corte y no se atribuye su tipo. Auditoría negativa verifica1691fuentes, protocolo congelado, limpieza real y recibo antes de editar. Evidencia mixed232-negative-audit.json; no reparación nativa acreditada.

Corrección limitada a tests/mixed_state_worker.py: comprobar vacía únicamente una generación aleatoria nueva, registrar número/huellas de claves de preparación y conservarlas. Worker/Beat usan esa generación; al terminar sólo se borran sus claves. Exigir generación propia vacía, claves previas aún vivas con igual valor y ninguna clave nueva fuera de la generación. Las expiraciones previas se registran separadas; no se exige conservar TTL ni borrar preparación. No se conoce el contenido del broker negativo232 ni se convierte ese fallo en éxito.

233 repite únicamente el selector native100 afectado por esta corrección, mismo reparto70/30,20derechos,14excluidos,86visibles y60páginas previstas. Mismos comandos worker/Beat, espera≤45s desde readiness, UUIDpublicaciónBeat→ejecuciónSUCCESS, ausencia eager/snapshot_error y dirty0. Sin reparación manual en variante nativa. Mismos controles de procesos/propiedad, fuentes congeladas y Telegram. No se repite229 ni manual231, no hay carga HTTP ni SLO/capacidad acreditados. Congelar tras grafo243 y comprobar Ruff/documentación.


## Resultado233 auditado — reparación nativa de estados mixtos

B07-233: equivalencia mixta100 con Beat/worker reales auditada PASS/174,917s;60páginas,14excluidos,86visibles y reparación14→0.28,892571s desde readiness; dos claves previas preservadas. Fuentes/limpieza/Telegram verificados;8de18,B07 abierto.

Corrida `20261022-113144-9e6fe9ca`: un caso PASS, sin fallos, errores ni omisiones; 174,917 segundos JUnit. Inventario sintético de 100 perfiles, dos municipios 70/30 y 20 derechos comerciales emitidos por los servicios existentes con eventos sintéticos. Los siete motivos de exclusión se verifican tanto en perfil orgánico como promocionado: 14 excluidos y 86 visibles. Un derecho suspendido y otro caducado pierden patrocinio, conservando sus perfiles públicos. Las tarjetas patrocinadas suman 80/44/44 en las cuatro combinaciones idioma/texto.

Veinte páginas exhaustivas en cada fase fresca/pendiente/reparada, 60 en total. IDs ordenados, recuentos, unicidad, etiquetas y 404 ES/EN comprobados. Las lecturas pendientes mantienen las generaciones de las 14 marcas; firmas pendientes y reparadas idénticas. Worker y Beat se arrancan después de completar esas lecturas. No son peticiones concurrentes con la reparación ni carga TCP.

Beat publica UUID bbcaa2be-cfcf-4936-aa71-6a251bd42b2d; el worker registra SUCCESS no eager, limpia exactamente 14 marcas hasta cero y no registra error de snapshot. Publicación→inicio 6,715392ms, ejecución 258,458766ms. Reparación observada a 28,892571s desde readiness; ciclo de arranque y espera 31,947237s. Las cotas marca→limpieza son 60,905944–61,023096s porque incluyen las lecturas pendientes previas al arranque. No afirmar reparación en 45s desde mutación: este protocolo acota desde readiness y no sustituye el slot original ni la cota del caso229. Ledger: un UUID correlacionado, cero ambiguos y cero publicaciones/ejecuciones no correlacionadas en el tramo capturado; sin afirmación sobre otros tramos.

Redis propio: dos claves de preparación preservadas sin cambio de valor, cero expiradas y cero claves nuevas fuera de la generación; generación del worker vacía tras su limpieza. Dos raíces y dos hijos observados retirados. PostgreSQL y Redis efectivos verificados; sin cuotas de carga ni proveedor real acreditados. Auditoría antes de editar: 1691 fuentes iguales en prerregistro/runner/árbol, protocolo por bytes/SHA y 628 fuentes de producto intactas. Limpieza real de contenedores, temporal y procesos y Telegram terminal confirmados. Evidencias mixed233-audit.json y audit_mixed233.py en artifacts/beta-promotion-fix-20261020. Negativo232 y rechazos previos conservados.

Siguiente: perfilar en una cohorte pequeña el coste del oráculo antes de ampliar esta mezcla al HTTP acotado. Cualquier optimización debe conservar lecturas nativas frescas, pertenencia, orden, etiquetas y separación de la proyección; no adoptar PublicationContext sólo por existir en producto. La hipótesis está registrada sin cambio de oráculo. No repetir229 ni lanzar900s automáticamente. B07, producción/checked y aceptación beta global siguen pendientes.


## Preparación234 — perfil del oráculo

B07-234: preparado contraste ABBA del oráculo nativo100 con relaciones cargadas por joins; validación y derechos intactos, sin lectura de proyección ni caché. Medición pendiente y candidato no adoptado;8de18,B07 abierto. Véase docs/212-perfil-oraculo-nativo-b07-20261022.md.


## Resultado234 y adopción235

B07-234: contraste nativo100 auditado PASS/102,663s;SQL2311→1752 (−24,19%),ratio wall instrumentado0,8951 y diez llamadas equivalentes.235 activa joins nativos por defecto; verificación mixta pendiente.8de18,B07 abierto.

234: corrida `20261022-114145-d66e0ff0`, un PASS sin fallos, errores u omisiones;102,663sJUnit. ABBA fotografía en70perfiles: nativo2311consultas en6,777577/6,975994s; hidratado1752consultas en5,912341/6,398376s. Reducción de consultas24,188663%, ratio de medianas wall0,895092 (10,490760% menos en este contraste instrumentado). No causalidad de rendimiento del producto ni extrapolación exacta a10000.

Tras pausa de un promocionado, revocación de consentimiento de un orgánico y suspensión de otro derecho: ambos recorridos dan68IDs ordenados iguales con texto vacío y photography, con2225→1679consultas; término ausente da0IDs y una consulta en ambas variantes. Esa pareja vacía tarda4,870114/12,709760ms, sin mejora de latencia acreditada para búsquedas vacías. Las diez llamadas rechazaron escrituras y lecturas de tablas de proyección/marcas; las marcas y generaciones permanecieron iguales. Sin caché ni contexto de validación compartido.

Auditoría previa a edición:1692fuentes iguales, protocolo por bytes/SHA, producto628 intacto, PostgreSQL17/Redis7.4 reales y limpieza de contenedores/temporal/PID. Telegram CI y auditoría confirmados. Evidencias oracle234-audit.json y audit_oracle234.py en artifacts/beta-promotion-fix-20261020. El resultado234 se tomó con hydrate=False por defecto y no se reinterpreta tras adoptar235.

235 cambia sólo el valor por defecto de hydrate a True y actualiza la metadata del perfil para leer el valor efectivo. Mantiene escape hydrate=False para comparar con el recorrido original y no cambia autoridad, formularios, SQL de búsqueda, derechos ni orden. Verificar únicamente test_mixed_state_territorial_equivalence[manual]:100perfiles70/30,20derechos,14excluidos,86visibles,60páginas exhaustivas y etiquetas/404/lecturas sin reparación. El censo nativo directo de ese test sigue sin joins especiales ni contexto y contrasta la pertenencia con el oráculo hidratado. Reparación manual declarada; no repetir worker233 ni234 por buscar mejores tiempos.

Congelar fuentes/protocolo tras grafo246 y documentación. Un caso focal serial con PostgreSQL real y watchdog900s. No medir velocidad integral causal comparándolo sólo con el histórico231; los tiempos de ambas corridas son descriptivos.235 tampoco acepta capacidad ni B07. Después integrar mezcla al escenario HTTP acotado con oráculos nativos completos, conservando recursos/slots y negativos anteriores.


## Resultado235 — oráculo nativo

B07-235: oráculo con joins nativos adoptado; mezcla100 auditada PASS/138,360s,60páginas,14excluidos y86visibles. Contraste234:−24,19%consultas y−10,49%wall instrumentado del oráculo, sin crédito de rendimiento de producto.8de18,B07 abierto.

Corrida20261022-114654-9a751873,fuentes/protocolo/producto628/limpieza/Telegram auditados antes de editar. Evidencia artifacts/beta-promotion-fix-20261020/oracle235-audit.json; desarrollo y límites en docs/212-perfil-oraculo-nativo-b07-20261022.md. Siguiente: preparar mezcla100 en HTTP acotado con slot original y oráculos completos; sin10000ni900automáticos.


## Preparación236 — HTTP mixto100

B07-236: HTTP mixto limitado a100perfiles, planificación nativa con rollback y patrocinio comprobado.84guardas PASS/10,02s y Ruff PASS; equivalencia PostgreSQL del plan e integraciónHTTP237 pendientes.8de18,B07 abierto.

Alcance y límites en docs/213-http-estados-mixtos-b07-20261022.md; producto628 intacto. Siguiente: validar plan/reversión real antes de237.


## Resultado236 y control236b

B07-236b: plan236 auditado PASS/89.273s,20páginas y28detalles; corregida selección para proteger sólo2fichas de carga en lugar de21samples. Nuevo control del plan pendiente;8de18,B07 abierto.

Evidencia mixed236-audit.json y alcance en docs/213-http-estados-mixtos-b07-20261022.md. NoHTTP237ni900automáticos.


## Resultado236b y próxima integración237

B07-236b: plan corregido auditado PASS/88,401s;20páginas,28detalles y dos fichas protegidas. Fuentes1695/producto628/limpieza/Telegram verificados. Se prepara una única HTTP237 mixta100 persistente;8de18,B07 abierto.

Protocolo en docs/213-http-estados-mixtos-b07-20261022.md; evidencias mixed236b-audit.json/source-proof. Lanzamiento persistente237 sólo tras congelar/verificar; sin aceptación de capacidad ni900automático.


B07-237: HTTP mixta100 auditada PASS/146,680s;14excluidos,86visibles,11patrocinios,20/2/20páginas y28detalles404. Reparación observada9,808647s desde mutación. Fuentes1695/producto628/limpieza/Telegram/compactación/reactivación del mismo goal verificados. Funcional instrumentada, no capacidad;8de18,B07 abierto.


B07-238: cobertura vigente reconciliada con contrato y fuentes; mezcla237 cubre city+q, no tipo+idioma hablado+ciudad+texto. Siguiente: preparar oráculo nativo yfixture de filtros combinados antes de medir. Sin nueva batería ni cierre;8de18,B07 abierto. Véase docs/214-cobertura-vigente-b07-20261022.md.


B07-239: implementado control combinado100 con oráculo nativo, municipio+tipo+idioma hablado+texto; fases fresca/pendiente/reparada, orgánico/promocional yESEN. Ejecución PostgreSQL pendiente, sin capacidad ni cierre;8de18,B07 abierto.


B07-239: equivalencia de filtros combinados100 auditada PASS/172,393s;264páginas ESEN,orgánico/promocional,fresco/pendiente/reparado,positivos yvacíos. Fuentes1696/producto628/limpieza/Telegram verificados;sin capacidad,8de18,B07 abierto. Evidencia en docs/214-cobertura-vigente-b07-20261022.md yartifacts/beta-promotion-fix-20261020/filters239-audit.json.


B07-240: diagnóstico SQL/render combinado100 preparado;48observaciones,240controles yfirmas nativas con etiquetas. Ejecución pendiente,sin capacidad ni cierre;8de18,B07 abierto. Véase docs/215-coste-filtros-combinados-b07-20261022.md.


B07-240: diagnóstico combinado100 auditado PASS/135,506s;48observaciones separadas,240controles,firmas nativas ypatrocinio equivalentes. SQL17–35consultas,render inclusivo mediano30–35ms porgrupo. Fuentes1697/producto628/limpieza/Telegram verificados;sin capacidad,8de18,B07 abierto. Véase docs/215-coste-filtros-combinados-b07-20261022.md.


B07-242: implementado control local100 normal/PRODUCTION con filtros checked combinados ymetadatos sintéticos explícitos;equivalencia PostgreSQL pendiente. Sin proveedor real,capacidad ni cierre;8de18,B07 abierto.

B07-241: diagnóstico combinado1000 auditado PASS/499,952s;48observaciones,240controles y336lecturas con IDs/recuento/patrocinio nativos equivalentes. Fuentes1697/producto628/limpieza/Telegram verificados;compactación yreactivación automática del mismo goal confirmadas. Sin capacidad ni cierre;8de18,B07 abierto. Véase docs/215-coste-filtros-combinados-b07-20261022.md.


## Resultado negativo242b y corrección243

B07-243: negativo242b auditado: dos FAIL porque save activa reparación Celery eager del fixture antes de observar la marca. Corrección sólo del ensayo: actualización SQL conserva disparadores PostgreSQL sin emitir señal de modelo. Revalidación de los dos casos pendiente; no paridad aceptada, capacidad ni cierre; 8 de 18, B07 abierto.

Ejecución `20261022-131419-031dc7c3`: 2 FAIL, 0 ERROR/skip JUnit, 81,652 s. Fuentes1698/protocolo216 intactos y628fuentes producto iguales aB13; contenedores, temporal yprocesos del runner ausentes. Recibos de fase, terminal y reactivación enviados; compactación REQUEST_ACKNOWLEDGED. Auditoría preservada en `artifacts/beta-promotion-fix-20261020/policy242b-negative-audit.json`. El log registra refresh_publication_state inmediato tras save yel fixture photo_environment configura CELERY_TASK_ALWAYS_EAGER=True; publication_signals programa refresh por on_commit. No se cambia producto ni se atribuye este fallo al lector.

Prerregistro243: repetir únicamente el archivo completo de dos casos con los mismos100perfiles70/30, políticas, filtros, fases y aserciones, runnerfocusedserial/PG17/Redis7.4/snapshots/broker aislado/timeout1200; cambiar sólo la escritura pendiente a QuerySet.update. Conservará la marca por disparador SQL hasta reparación manual. Congelar corte y auditar antes de editar; no repetir sin causa ni aceptar por el resultado del auditor negativo.


## Resultado auditado243

B07-243 auditado: 1 PASS y 1 FAIL en 116,554 s; producción verifica 96 páginas, normal falla en el recuento nativo 69 frente a 70. Fuentes1698 y producto628 intactos, limpieza y Telegram confirmados; compactación y reactivación del mismo objetivo verificadas. B07 abierto; ocho de18 puntos cerrados.

Ejecución `20261022-132257-f359d7e1`; auditoría `artifacts/beta-promotion-fix-20261020/policy243-negative-audit.json`. Un PASS no acepta el archivo completo. El caso production recorre fresh/pending/repaired, ES/EN, cuatro variantes checked y hasta tercera página; una marca pendiente permanece tras GET, reparación manual. El caso normal termina antes de emitir su propiedad completa. No equivalencia normal completa, capacidad ni proveedor real.

Causa del recuento incorrecto del ensayo: `reference_territorial_order` llama a `publicly_visible`, que llama a `validate_submission`; `apps/listings/submissions.py:97–110` exige que la última prueba tenga estado passed, sujeto y manager_version actuales también fuera de PRODUCTION. La mutación de manager_version invalida por tanto la publicación completa en ambos modos: después de fresh quedan69 perfiles mayoritarios normales para sinchecked/contact/age+contact, y55 para age; producción55 para todas las variantes. El ensayo sobrescribe incorrectamente el decremento normal con70. Esto se deduce de la autoridad nativa y concuerda con69 observado; aún falta revalidación HTTP normal de las fases pendientes y reparadas. Siguiente corrección propuesta: conservar70/30 para fresh normal noage y restar1 después en mayoría para pending/repaired; mantener56/24 age/production y el decremento a55. No alterar producto, filtros, oráculo ni guardas para acomodar el fallo.


## Corrección y prerregistro244

B07-244: corregida sólo la expectativa del ensayo: invalidar manager_version excluye un perfil mayoritario en ambos modos y todos los filtros; normal69 o55 para age tras fresh, producción55. Revalidación de dos casos100 pendiente; sin cambios de producto, capacidad ni cierre.

Mismo archivo completo, población100 70/30, dos casos, fases, ES/EN, checked, IDs/orden/recuentos y marcas; runner focused serial PostgreSQL17/Redis7.4, snapshots, broker aislado, timeout1200. No otros cambios; congelar fuentes y protocolo, auditar resultado y limpieza antes de editar. Shell persistente con Telegram terminal, compactación y reactivación del mismo objetivo durante pausa autorizada.


## Resultado auditado244

B07-244 auditado: dos PASS en 139,130 s; normal114 y producción96 páginas, total210. Fuentes1698 y producto628 intactos, limpieza y Telegram confirmados; compactación y reactivación del mismo objetivo verificadas. B07 abierto; ocho de18 puntos cerrados.

Ejecución `20261022-133206-c545cb5f`; prueba y auditoría `artifacts/beta-promotion-fix-20261020/policy244-audit.json`. PostgreSQL17 y Redis7.4 reales locales; 100 perfiles sintéticos70/30, fresh/pending/repaired, ES/EN y cuatro variantes checked. IDs, orden, recuentos y unicidad contrastados con autoridad nativa; GET conserva la marca pendiente, reparación manual. El manager_version obsoleto excluye el perfil en ambos modos. Sin proveedor real, worker, TCP, capacidad ni configuración segura de producción acreditados. Se preservan negativos242b/243 y el primer auditor244 fallido por su supuesto incorrecto de96 páginas normales; corregido a114 sin repetir CI. Próximo trabajo: derivar del contrato y matriz la siguiente combinación pendiente antes de prerregistrar otra ejecución.


B07-245: preparada equivalencia mixta1000 con censo nativo completo, páginas inicial/intermedia/final y14exclusiones; primero regresión manual100 por extraer el helper. Ejecución pendiente; sin capacidad ni cierre,8de18. Véase docs/217-escala-estados-mixtos-b07-20261022.md.


## Resultado245 auditado

B07-245: equivalencia mixta100/1000 auditada: dos PASS,132páginas de listado,14exclusiones y86/986visibles; fuentes1699/producto628 ylimpieza verificados. Compactación solicitada yreactivación del mismo goal confirmadas. Sin capacidad ni cierre;8de18,B07 abierto.

Corrida20261022-134351-354ba097:100manual144,218s y1000manual1008,270s;1152,488sJUnit total.100recorre60páginas y1000selecciona72: inicial/intermedia/final en tres fases,ESEN ytexto vacío/photography. Censo nativo completo en ambas escalas, siete causas orgánico/promocionado, derechos suspendido/caducado sin ocultar perfil,28detalles404 por fase posterior. Marcas0/14/0 yfirmas pendientes/reparadas idénticas. Auditoría mixed245-audit.json: fuentes completas preregistro=lanzamiento=CI=actual1699, protocolo217bytes/SHA,628producto intactos,PostgreSQL17/Redis7.4 reales,compilación nativa ydos casos sin fallos ni omitidos;Docker/temporales/procesos ausentes yTelegram confirmado. Se conserva evidencia original congelada. Sin crédito worker,verificador real,TCP ni capacidad.10000noejecutado;duración no extrapolable ni latenciaHTTP.

Siguiente trabajo: estudiar el coste del helper y la cobertura mixta HTTP antes de preparar10000; la variante HTTP conserva guard100 y requiere adaptación explícita. No repetir controles ya acreditados ni lanzar10000 automáticamente.


## Integración mixta escalable 246

B07-246 auditado: 2 PASS en PostgreSQL real, 100/1000 perfiles, rollback contrafactual y 44 páginas verificadas; fuentes y limpieza confirmadas. Compactación aceptada y mismo objetivo reactivado por la shell. Sin capacidad acreditada; 8 de 18, B07 abierto. Véase [protocolo218](218-integracion-plan-mixto-escalable-b07-20261022.md).


## Resultado auditado del control 246

Ejecución `20261022-141230-c15fcc1e`: dos casos PASS, sin fallos, errores ni omitidos; 561,583 s sumados de casos. Para 100/1000 perfiles: 20/200 derechos, 86/986 visibles, 11/191 patrocinios activos, cuatro censos nativos completos y 20/24 páginas comprobadas. Cada caso acredita rollback lógico, secuencia monotónica sin reinicio, 14 generaciones posteriores y 28 detalles excluidos con 404; los GET conservan las marcas. La selección de páginas de 1000 no equivale a recorrerlas todas.

Auditoría `mixed246-audit.json`: las 1699 fuentes congeladas coinciden con lanzamiento, CI y estado posterior; protocolo original preservado por bytes y SHA, 628 fuentes de producto intactas, PostgreSQL17/Redis7.4, native-build y pasos correctos. Limpieza contrastada con Docker, temporal y procesos; recibos Telegram confirmados, compactación aceptada y reactivación del mismo objetivo conservando consumo. No se ejecutó carga TCP ni worker en esta integración y no acredita capacidad.

El siguiente trabajo es preparar y prerregistrar HTTP mixto a 1000 con imagen e instrumento verificados. No habilita 10000 ni una prueba contractual de 900 s automáticamente. B07 sigue abierto y el balance permanece en 8 de 18.


## Prerregistro HTTP mixto1000 — control247

B07-247 auditado: ERROR de arranque PostgreSQL antes de ejecutar pruebas HTTP. Fuentes y limpieza verificadas; compactación y reactivación del mismo objetivo confirmadas. Causa pendiente; 8 de 18, B07 abierto. Véase [protocolo219](219-http-mixto-mil-perfiles-b07-20261022.md).


B07-248 auditado: 44 pruebas PASS y preflight PostgreSQL/S3/Celery/Beat real PASS; limpieza y Telegram confirmados. Captura terminal añadida; causa247 desconocida, HTTP mixto1000 pendiente. 8 de 18, B07 abierto. Véase [evidencia220](220-evidencia-arranque-servicios-b07-20261022.md).


B07-249 auditado: control HTTP mixto1000 FAIL, 56 de 60 lecturas correctas y cuatro 404 en página30 de ciudad1; subida persistida. Fuentes1700, producto628 y limpieza verificados; compactación y reactivación del mismo objetivo confirmadas. 8 de 18, B07 abierto. Véase [protocolo221](221-http-mixto-mil-perfiles-observabilidad-b07-20261022.md).


B07-250 auditado: integración PostgreSQL de 100 y 1.000 perfiles PASS; censos de rutas 56/30 y 686/300, 44 páginas y rollback lógico verificados. Fuentes1700, limpieza, Telegram, compactación y reactivación confirmados. Control HTTP corregido pendiente; 8 de 18, B07 abierto. Véase [correctiva222](222-correctiva-rutas-mixtas-b07-20261022.md).


## Resultado auditado 250

Ejecución `20261022-151128-752f43f0`: dos casos PASS, sin fallos, errores ni omisiones; JUnit537.864s. Censos posteriores56/30 y686/300 obtenidos de referencias nativas antes del rollback. Cada escala conserva14 exclusiones,28 detalles404 y cuatro censos nativos;20/24 páginas,86/986 visibles y11/191 patrocinios. Restauración lógica verificada y secuencia monotónica, sin setval. Auditoría `artifacts/beta-promotion-fix-20261020/mixed250-audit.json`:1700 fuentes iguales entre prerregistro, lanzamiento, CI y auditoría; protocolo original por bytes/SHA, producto628 intacto y limpieza real de Docker, temporal y procesos. Telegram terminal enviado, compactación reconocida y mismo objetivo reactivado conservando consumo. No acredita carga HTTP, worker ni capacidad. Negativo249 conservado. Siguiente: prerregistrar control HTTP1000 con rutas corregidas; sin10000 ni900s automáticos.


B07-251 preparado: HTTP mixto de 1.000 perfiles con rutas del censo nativo posterior, tras integración250 auditada. Pendiente ejecución; 8 de 18, B07 abierto.


## Resultado HTTP mixto1000 — control251

B07-251 auditado: HTTP mixto de 1.000 perfiles PASS, 60 lecturas correctas, 50 páginas y 28 detalles excluidos404; rutas posteriores686/300 verificadas. Fuentes1700, producto628, recursos y limpieza confirmados; compactación aceptada y mismo objetivo reactivado por shell. Sin capacidad acreditada; 8 de 18, B07 abierto. Véase [evidencia223](223-http-mixto-mil-rutas-corregidas-b07-20261022.md).


## Prerregistro integración mixta10000 — control252

B07-252 preparado: integración contrafactual mixta de 10.000 perfiles y 2.000 derechos en PostgreSQL; ejecución pendiente. HTTP10000 continúa bloqueado, sin capacidad ni900s; 8 de 18, B07 abierto. Véase [protocolo224](224-integracion-plan-mixto-diez-mil-b07-20261022.md).


B07-252 auditado: integración contrafactual mixta de 10.000 perfiles y 2.000 derechos PASS en 4524,207s; 24 páginas, cuatro censos y 28 detalles excluidos verificados. HTTP mixto10000 pendiente; sin capacidad ni cierre, ocho de 18, B07 abierto.


B07-253 preparado: HTTP funcional mixto de 10.000 perfiles, 2.000 derechos y 14 exclusiones tras integración252 auditada; 79 controles PASS. Pendiente ejecución HTTP, sin capacidad ni900s; ocho de 18, B07 abierto. Véase [protocolo225](225-http-mixto-diez-mil-b07-20261022.md).


## Resultado HTTP mixto10000 — control253

B07-253 auditado: HTTP funcional mixto de 10.000 perfiles PASS; 60 lecturas, una subida persistida, 50 páginas y 28 detalles excluidos404 verificados. Fuentes1700, producto628, recursos y limpieza confirmados; compactación aceptada y mismo objetivo reactivado automáticamente. Sin capacidad acreditada; ocho de 18, B07 abierto. Véase [evidencia225](225-http-mixto-diez-mil-b07-20261022.md).


## Preparación confirmada — control254

B07-254 preparado: vía de mezcla confirmada sin rollback contrafactual, con oráculo nativo independiente; integración100 nueva y regresión100 anterior pendientes. Sin carga HTTP ni capacidad; ocho de 18, B07 abierto. Véase [protocolo226](226-preparacion-mezcla-confirmada-b07-20261022.md).


## Resultado254 — mezcla confirmada

B07-254 auditado: mezcla confirmada sin rollback contrafactual y regresión anterior100, dos PASS/168,647s; 60 páginas y 84 detalles excluidos404. Fuentes1700/producto628, limpieza y Telegram verificados. Sin HTTP ni capacidad; ocho de 18, B07 abierto. Véase [evidencia226](226-preparacion-mezcla-confirmada-b07-20261022.md).


## HTTP mezcla confirmada — control255

B07-255 preparado: modo HTTP funcional de mezcla confirmada, sin rollback contrafactual; 47 controles de guards PASS. Funcional100 pendiente, sin corto ni900s; ocho de 18, B07 abierto. Véase [protocolo227](227-http-mezcla-confirmada-b07-20261022.md).


## Resultado255 — HTTP confirmado100

B07-255 auditado: HTTP confirmado100 PASS/133,655s; 60 lecturas, una subida persistida,40páginas y56detalles404. Fuentes1701/producto628, recursos, limpieza y Telegram verificados. Corrección posterior sólo de metadatos; sin capacidad, ocho de 18, B07 abierto. Véase [evidencia227](227-http-mezcla-confirmada-b07-20261022.md).


## HTTP confirmado1000 — control256

B07-256 auditado: HTTP confirmado de 1.000 perfiles PASS en 665,019 s; 60 lecturas, una subida persistida, 48 páginas y 56 detalles excluidos con 404. Fuentes, recursos y limpieza verificados; compactación aceptada y mismo objetivo reactivado automáticamente. Sin capacidad acreditada; ocho de 18, B07 abierto. Véase [protocolo228](228-http-confirmado-mil-perfiles-b07-20261022.md).


## Escala confirmada10000 — control257

B07-257 preparado: HTTP funcional de mezcla confirmada a 10.000 perfiles, 2.000 derechos, 14 exclusiones y 9.986 visibles. Reutiliza controles válidos y no modifica producto; ejecución pendiente, sin capacidad ni 900 s. Ocho de 18, B07 abierto. Véase [protocolo229](229-http-confirmado-diez-mil-b07-20261022.md).


Corte257: [resultado confirmado10.000](229-http-confirmado-diez-mil-b07-20261022.md) funcionalPASS6059.738s/60HTTP200/una subida/48páginas56exclusiones404. Control ERROR: observador ValueError antes del manifiesto, cero muestras; recursos no acreditados y causa exacta desconocida. Compactación y autoresume mismo objetivo verificados; conservar negativo, diagnosticar instrumento antes de otra carga larga. B07 abierto; sin capacidad ni900s.


Corte258: [diagnóstico observador](230-diagnostico-inicializacion-observador-b07-20261022.md) nativo100 PASS/131.634s,21muestras/seisidentidades/cuotas/fuentes/limpieza/Telegram auditados. No explica retrospectivamente257: HTTP10000 PASS, observador ERROR/no aceptado. Siguiente hipótesis finita create/start, sin repetir10000. B07 abierto, ocho de18.


Corte259: [espera de contenedores creados](231-transicion-create-start-observador-b07-20261022.md) corregida con44testsPASS yreproducción nativa mínimaPASS, fuentes/limpieza/Telegram comprobados. No explica retrospectivamente257 ni acepta sus recursos; no requiere otra cargaHTTP idéntica. Retomar residual coste/diversidad10000. Ocho de18,B07 abierto.


## Resultado260 auditado

B07-260 auditado: un PASS en 4333,792 s (72,23 minutos), 48 observaciones y 336 lecturas a 10.000 perfiles con 2.000 derechos sintéticos. IDs ordenados, recuentos y patrocinios coinciden con autoridad nativa; dos marcas pendientes permanecen intactas. Las 1701 fuentes coinciden entre prerregistro, lanzamiento, CI y árbol posterior; protocolo original y 628 fuentes de producto intactos. PostgreSQL17/Redis7.4 y compilación nativa verificados; Docker, temporal y procesos limpiados. Telegram terminal, compactación durante la espera y reactivación automática del mismo objetivo conservando consumo confirmados. Diagnóstico SQL/render, sin aceptación de capacidad; ocho de 18 puntos cerrados, B07 abierto.

Ejecución `20261022-215355-1b0072dd`; auditoría `artifacts/beta-promotion-fix-20261020/combined260-audit.json`. Medianas de controles sin instrumentación: fresco orgánico 229,904 ms, fresco promocionado 340,416 ms, pendiente orgánico 237,348 ms y pendiente promocionado 347,145 ms. Consultas por lectura: 17–35; render inclusivo mediano por grupo 35,795–40,514 ms. Son valores descriptivos de cinco controles por observación; render incluye SQL y no se suma con él. El tiempo JUnit incluye preparación y oráculos; no representa latencia HTTP. Se reutilizan 240/241 para 100/1000, sin atribuir diferencias a efectos causales del volumen. El negativo de recursos257 sigue vigente.


## Resultado262 auditado

B07-262 auditado: corto limpio de mezcla confirmada10000 PASS;1200éxitos,0errores,p95 564,618ms,1upload persistido. Generador p95/p99/máximo 3,120/6,186/14,163ms;pendientes6 al cierre y0 finales. Fuentes1701/producto628,cuotas8CPU8GiBswap0,limpieza,Telegram,compactación yreactivación del mismo objetivo comprobados. Ocho de18,B07 abierto;sin aceptación contractual.

Ejecución `20261022-231456-319ed49a`; auditoría `artifacts/beta-promotion-fix-20261020/short262-audit.json`. Un caso PASS en 6130,126 s de JUnit, que incluye preparación y oráculos; la ventana de carga dura 60 s. Mezcla 400 listados,400 búsquedas,400 fichas y600 peticiones por idioma;42 slots y30 rutas únicas verificados contra los1200 registros. Fixture sintética con9986 visibles,1991 patrocinios ygeografía6986/3000 tras14 exclusiones confirmadas. Antes/después coinciden24 páginas por fase y56 detalles excluidos404 en total;marcas pendientes0. PostgreSQL17/Redis7.4 nativos,4workers/1thread,worker/Beat reales,GCsinfreeze. Cotas conservadoras: memoria1770422272bytes yalmacenamiento4865392640bytes;no observador host ni profiler. Protocolo original yfuentes congeladas comprobados antes de esta actualización. El negativo257 se conserva; no acredita mejora causal,capacidad PRODUCTION/checked,proveedor real ni cierre beta.


## Resultado contractual265 auditado

B07-265 auditado: contractual de mezcla final10000 PASS;900s,18000 éxitos,0 errores,p95 437,231ms y15 uploads persistidos. Generador válido;fuentes1701/producto628,cuotas ylimpieza verificadas. Telegram,compactación yreactivación del mismo objetivo confirmados. Ocho de18 puntos cerrados,B07 abierto.

Ejecución `20261023-010935-e3cb6eba`; auditoría `artifacts/beta-promotion-fix-20261020/contract265-audit.json`. Un caso PASS en7128,003sJUnit incluyendo preparación y oráculos;ventana de llegadas900s. Generador p95/p99/máximo3,252/6,351/38,478ms;pendientes7 al cierre y0 finales. Mezcla6000 listados/6000 búsquedas/6000 fichas y9000 por idioma;42slots30rutas y15borradores distintos a60s de intervalo. Fixture9986visibles/1991patrocinios tras14exclusiones;24páginas antes ydespués,56detalles excluidos404. PostgreSQL17/Redis7.4 nativos,4workers/1thread yworker/Beat reales;8CPU8GiBswap0,memoria conservadora2022838272bytes yalmacenamiento4865392640bytes. Fuentes completas,protocolo original,cuotas,readonly yausencia real de recursos/PID verificados antes de editar documentación. Sin observador host ni profiler. PASS limitado a este escenario;no acredita mejora causal,PRODUCTION/checked,proveedor real,archivos grandes ni aceptación global beta. Negativos previos preservados;sin repetición de carga ni nuevas invocaciones ClaudeV1 (ocho históricas yconsumo intactos).
