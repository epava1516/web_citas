# B07 — diagnóstico de coste de filtros combinados

Prerregistro240,2026-10-22. B07 abierto,8de18. Continúa la equivalencia239 de [cobertura214](214-cobertura-vigente-b07-20261022.md); no repite esa batería ni sustituye el contrato16§16.

Instrumento: tests/beta_combined_filter_cost_diagnostic.py. Un caso pequeño100perfiles,dosmunicipios70/30,20derechosTop/Premium emitidos por servicios nativos con eventos sintéticos. Atributos explícitos60mujer/en+10hombre/fr y20mujer/en+10hombre/fr. No personas,proveedor,pagos odistribución nacional reales. Producto sin cambios.

Dos fases fresca/pendiente,dos modos orgánico/promocional,ESEN. Seis rutas: mayoritaria mujer/en/photography páginas1,2,3; minoritaria mujer/en/photography primera; mayoritaria hombre/fr/photography primera; mayoritaria mujer/fr/photography vacía. Municipio,tipo,idioma hablado ytexto simultáneos.48observaciones,cinco controles porobservación=240peticiones,48calentamientos y48observaciones SQL/render separadas,total336peticiones secuenciales. No afirmar p95SLO con cinco controles.

Antes de cada fase/modo: oráculo territorial nativo ypredicados de campos nativos fuera de ventana,además mapa de patrocinio nativo elegible. Cada lectura compara IDsordenados,recuento yetiquetas contra ese esperado. No discovery.candidates ni resultadosHTTP como oráculo. La fase pendiente pausa un promocionado yretira un orgánico coincidentes; dosmarcas/generaciones deben permanecer iguales después de todas las lecturas. Sin reparación,worker oTCP acreditados.

Cada control registra wall yCPU del proceso pytest/client incluyendo comprobaciones de firma; no CPU de PostgreSQL ni latencia de red. Instrumentación sólo en otra petición: execute_wrapper agrega duración de driver yfase render/other,sinSQLni parámetros; wrapper temporal de discovery.render recoge duración inclusiva. El render incluye consultas/esperas; no sumar driver+render como fases exclusivas ni atribuir causalidad del overhead. Sin cProfile,caché ni cambio de autoridad. Fixture,oráculos ylecturas de marcas fuera de ventanas.

Runnerfocusedserial,PostgreSQL17/Redis7.4 propios,snapshotfixture ybrokeraislado,timeout900s,native-source existente. Tras grafo255 yrecibos,congelar fuentes completas yesteprotocolo porbytes/SHA. Resultado PASS sólo acepta instrumento/equivalencia;inspeccionar distribución de costes yestimar ampliación antes de escalar. No900HTTP automático. Artefacto beta-combined-filter-cost.json enrunner,JUniteigualdad de fuentes,limpieza real yTelegram requeridos antes de modificar.

B07-240: diagnóstico SQL/render combinado100 preparado;48observaciones,240controles yfirmas nativas con etiquetas. Ejecución pendiente,sin capacidad ni cierre;8de18,B07 abierto.


## Resultado240 auditado

B07-240: diagnóstico combinado100 auditado PASS/135,506s;48observaciones separadas,240controles,firmas nativas ypatrocinio equivalentes. SQL17–35consultas,render inclusivo mediano30–35ms porgrupo. Fuentes1697/producto628/limpieza/Telegram verificados;sin capacidad,8de18,B07 abierto.

Corrida20261022-124640-64fba8a8,unPASSsinfallos,errores niomisiones.336lecturas:48calentamientos,240controles y48observaciones instrumentadas. Fuentes1697iguales prerregistro/runner/árbol yprotocolo215porbytes/SHA antes de editar,628producto sin cambios,PostgreSQL17/Redis7.4,compilaciónnativa ylimpieza real contenedores/temporal/PID. TelegramCIyauditoría confirmados. Artefacto beta-combined-filter-cost.json ycombined240-audit.json conservan valores crudos yhuellas.

| Fase/modo | Mediana wall de60controles | Máximo control | Consultas porobservación | Mediana render inclusivo |
| --- | --- | --- | --- | --- |
| Fresca/orgánico |142,197ms|313,347ms|17–33|30,964ms|
| Fresca/promocional |159,958ms|387,898ms|18–34|30,013ms|
| Pendiente/orgánico |150,654ms|326,560ms|18–34|32,453ms|
| Pendiente/promocional |162,197ms|370,702ms|19–35|35,033ms|

Agregados descriptivos de rutas distintas, no comparación causal entre modos ni p95SLO. La mayor mediana porruta fue pendiente/promocional ES,mujer/en,municipio mayoritario,página2:224,858mswall/149,218msCPUdelproceso en controles;otra petición instrumentada35consultas/42,332msdriver/31,337msrender. No restar esas cifras tomadas en peticiones diferentes ni inferir CPUPostgreSQL ocausa exclusiva.

Todas las firmas verifican IDsordenados,recuento ypatrocinio nativo;vacío ytercerapágina incluidos. Dosmarcas/generaciones permanecen iguales después de GETpendientes. Sin reparación niworker/TCP/capacidad acreditados. El incremento240 no modifica producto,nooptimiza consultas por un recuento aislado yno repite239.

Decisión siguiente: preparar un único contraste de crecimiento1000 con las mismas combinaciones,primera/intermedia/última ajustadas al recuento ypresupuestos preregistrados;no asumir coste constante desde100. Adaptar fixture/mapa de derechos/oráculo de forma explícita antes de ampliar. El oráculo recorre población nativa fuera de ventana yla preparación crece;estimar duración yusar shellpersistente/Telegram/pausa/compactación/reactivación para esperas largas. No10000ni900HTTPautomáticos,sin repetir100para buscar mejores tiempos.


## Prerregistro241 — crecimiento a1000

B07-241: diagnóstico combinado1000 auditado PASS/499,952s;48observaciones,240controles y336lecturas con IDs/recuento/patrocinio nativos equivalentes. Fuentes1697/producto628/limpieza/Telegram verificados;compactación yreactivación automática del mismo goal confirmadas. Sin capacidad ni cierre;8de18,B07 abierto.

Fuente beta_combined_filter_cost_diagnostic.py parametrizada exclusivamente100/1000. Ejecutar sólo test_combined_filter_cost[1000];no repetir100 tras su auditoría240. Preparación700/300;atributos600mujer/en+100hombre/fr y200mujer/en+100hombre/fr.200derechos sintéticos;mapa nativo comprueba cantidadcount/5 yeligible fresco,sin helper limitado a20ni proyección/caché. Páginas mayoritarias calculadas por recuento nativo:primera,intermedia ceil(last/2),última;se esperan1/13/25 para600o598resultados,en vez de1/2/3. Los otros trescasos conservanminoritaria positiva,masculino/frpositivo ycruce mujer/frvacío.48combinaciones,48calentamientos,240controles y48observaciones separadas,336peticiones. Pausa un promocionado yretira un orgánico coincidentes;dosmarcas/generaciones intactas tras GET. FirmaID/recuento/patrocinio nativo verificada en cada lectura.

Sin cambio de producto,GC,autoridad oinstrumentación SQL/render. El mapa comercial sustituye sólo el helper con assert20por el mismo recorrido nativo a200;el caso100 mantiene cálculo1/2/3y20derechos. No se acredita nueva corrida100 ni se exige repetirla sólo por parametrizar crecimiento. Ruff ygrafo257 antes de congelar. Un runnerfocusedserial PostgreSQL17/Redis7.4 propios,native-source existente,snapshotfixture ybrokeraislado. Timeoutpytest2400s;no cambiar presupuestos de latencia de producto ni llamarlo entorno kernel8CPU8GiB:es diagnóstico en hostcompartido con topologíaCI.

Estimación de planificación:240tardó135,506sJUnit a100,con preparación/oráculos fuera de las ventanas;1000puede requerir varios minutos odecenas por consultas nativas/preparación. No garantía lineal ni coste de producto inferido desde preparación. Timeout2400s es límite del instrumento,no aceptación de rendimiento. Registrar fases yduraciones reales antes de decidir10000. Ningún10000ni900HTTPautomático.

Wrapperpersistente con stdinDEVNULL,nueva sesión yPID/start_ticks,watcherterminal,callbackRPCdel mismo goal ycompactor alpaused. AvisosTelegram inicio yprevio a pausa confirmados antes de pausar;conservar consumo yobjetivo,sincrearotro. La shellavisa terminal yreactiva mismo goal;no sondeos del modelo durante pausa. Compactar alpausar. Congelar todasfuentes/protocolo215porbytes/SHA ygrafo257. Alretomar auditarterminal/JUnit/JSON crudo,sources==prerregistro==runner==árbol,628producto,limpieza real yrecibos antes de editar. FAIL/INVALID/ERRORse preservan;no repetir para buscar verde.


## Resultado241 — crecimiento1000 auditado

Run20261022-125601-d9053223:1PASS/499,952sJUnit. Antes de editar se comprobaron1697fuentes iguales a prerregistro/launch/runner/árbol,protocolo215 idéntico por bytes/SHA,628fuentes de producto intactas,PostgreSQL17/Redis7.4 reales,limpieza efectiva de contenedores/temporal/procesos yTelegram CI/global/reactivación. CompactaciónACK yreactivación del mismo objetivo con consumo conservado confirmadas. Evidencia cruda en artifacts/local-ci/20261022-125601-d9053223/beta-combined-filter-cost.json y auditoría en artifacts/beta-promotion-fix-20261020/combined241-audit.json.

1000perfiles700/300,200derechos;48observaciones,240controles,48calentamientos y48peticiones instrumentadas separadas:336lecturas. Páginas mayoritarias1/13/25,positivos ycruce vacío;conteos0/100/200/598/600. IDs ordenados,recuentos ypatrocinio equivalentes al oráculo nativo en cada lectura. Dosmarcas/generaciones intactas después de GET,sin reparación ni worker acreditados.

Por grupos freshorgánico/freshpromocionado/pendingorgánico/pendingpromocionado,medianas de controles163,100/189,431/160,061/203,182ms;máximos354,389/407,446/378,102/392,718ms. RangosSQL17–33/18–34/18–34/19–35;medianas render inclusivo35,882/35,053/35,916/39,899ms en peticiones instrumentadas separadas. El rango de consultas coincide con100,pero esto no demuestra coste constante ni mejora causal. Sin ABBA entre poblaciones,no atribuir diferencias al tamaño únicamente;no sumar SQL yrender inclusivo ni interpretar CPU del proceso como PostgreSQL. Cinco controles por ruta son descriptivos,no aceptación SLO.

El tiempoJUnit incluye preparación y oráculos fuera de las ventanas;no es latencia HTTP. No TCP,cuotas kernel8CPU8GiB,concurrencia ni capacidad aceptada. B07 continúa abierto y8de18 cerrados. No ejecutar10000ni900HTTP automáticamente:el siguiente trabajo debe revisar cobertura contractual pendiente yjustificar una medición distinta antes de ampliar.


## Resultado260 auditado

B07-260 auditado: un PASS en 4333,792 s (72,23 minutos), 48 observaciones y 336 lecturas a 10.000 perfiles con 2.000 derechos sintéticos. IDs ordenados, recuentos y patrocinios coinciden con autoridad nativa; dos marcas pendientes permanecen intactas. Las 1701 fuentes coinciden entre prerregistro, lanzamiento, CI y árbol posterior; protocolo original y 628 fuentes de producto intactos. PostgreSQL17/Redis7.4 y compilación nativa verificados; Docker, temporal y procesos limpiados. Telegram terminal, compactación durante la espera y reactivación automática del mismo objetivo conservando consumo confirmados. Diagnóstico SQL/render, sin aceptación de capacidad; ocho de 18 puntos cerrados, B07 abierto.

Ejecución `20261022-215355-1b0072dd`; auditoría `artifacts/beta-promotion-fix-20261020/combined260-audit.json`. Medianas de controles sin instrumentación: fresco orgánico 229,904 ms, fresco promocionado 340,416 ms, pendiente orgánico 237,348 ms y pendiente promocionado 347,145 ms. Consultas por lectura: 17–35; render inclusivo mediano por grupo 35,795–40,514 ms. Son valores descriptivos de cinco controles por observación; render incluye SQL y no se suma con él. El tiempo JUnit incluye preparación y oráculos; no representa latencia HTTP. Se reutilizan 240/241 para 100/1000, sin atribuir diferencias a efectos causales del volumen. El negativo de recursos257 sigue vigente.
