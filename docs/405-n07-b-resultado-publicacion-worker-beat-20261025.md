# N07B — resultado de publicación con worker y Beat reales

25 de octubre de2026. Alfa, base4ebc067. Run20261025-225301-8e9ac820: **1PASS/0FAIL/ERROR/SKIP**,118,068sJUnit. Se acepta esta referencia finita de publicación, **no todo N07**, que sigue abierto6/13bloques obligatorios. Sin cambio de aplicación ni optimización marginal forzada. [Prerregistro403](403-n07-b-prerregistro-publicacion-worker-beat-20261025.md), [corrección404](404-n07-b-correccion-instrumento-publicacion-20261025.md), [auditoría independiente](evidencias/n07-b-worker-beat-auditoria-20261025.json), [primer fallo conservado](evidencias/n07-b-primer-fallo-auditoria-20261025.json) y [alcance correctivo](evidencias/n07-b-alcance-instrumento-corregido-20261025.json).

## Efectos y autoridad comprobados

Cohorte sintética100publicados/102Listings totales, preparación eager y refresh directo fuera de medida. PostgreSQL/Redis propios, worker real prefork2con rol restringido y Beat con entradas nativas30/60s sin acelerar. Siete mensajes ejecutados SUCCESS/noeager en dos hijos reales y siete comprobantes current_user/PID; cuatro identidades de proceso propias terminadas. Rol/credenciales/runtime privado retirados, claves ajenas preservadas y cero claves nuevas fuera del namespace propio. Contenedores/redes/volúmenes/temporal propios ausentes; Telegram terminal sent y auditoría PASS.

FaseA: un pause real tras commit emitió refresh mientras el worker estaba ausente. Ficha/foto/favorito denegados inmediatamente, favorito guardado sin enlace y cinco páginas ES/EN con99IDs únicos, sin el pausado; marca aún pendiente. Después del arranque, el worker vació la marca y los102estados coincidieron con el oráculo nativo en todas las nueve STATE_COLUMNS.

FaseB: QuerySet.update y rawSQL pausaron dos perfiles y caducaron otro, sin nuevas emisiones de señales del harness. Tres marcas pendientes, denegaciones inmediatas y cuatro páginas ES/EN con96IDs únicos antes de iniciar Beat. READ_REPAIRdesactivado de forma nativa, sin parchearlo. Beat emitió dos refresh y un expiry; se registró una sola acción expire, actor sistema, revisión/versión correctas y cero marcas finales. No se esperó a Beat para retirar exposición pública.

FaseC: sweep enviado manualmente detectó una elegibilidad almacenada alterada deliberadamente; marcó un divergente y un refresh manual lo reparó. Igualdad nativa de los102estados al final de cada fase. Esta llamada **no** acredita la cadencia horaria3600s de sweep.

Los18GETde paginación comprueban los objetos/conteos/IDs del contexto público en ES/EN; la continuidad entre esa selección y las tarjetas se conserva mediante las fuentes/testigos de N04, no una nueva inspección universal del HTML. Ficha/foto/favoritos de esta ejecución usan EN. El reparto de otros filtros y superficies conserva sus testigos/propietarios. No se convierten estas muestras en todos los estados o39PASSindividuales.

## Tiempos y coste observado

Una observación por ejecución; no medianas/p95/p99. Pared/CPU del hilo incluyen el observador de prerun y bookkeeping; los snapshots posteriores y comprobantes adicionales no se convierten en tiempo puro de servicio o CPU PostgreSQL. La preparación y los118,068s de QA quedan separados.

| Ejecución / origen | Resultado del dominio | Publicación→inicio ms | Pared del observador ms | CPU hilo ms |
| --- | ---: | ---: | ---: | ---: |
| Refresh inicial, señal real y worker deliberadamente ausente |1|4988.900|278.409|120.448|
| Primer refresh Beat |3|24.851|177.410|60.352|
| Expiry Beat |1|7.390|122.627|39.772|
| Segundo refresh Beat |1|10.529|273.180|110.411|
| Refresh emitido por el worker tras expiry |0|17.721|74.324|22.038|
| Sweep manual |1divergente|5.352|452.045|237.343|
| Refresh manual posterior |1|3.674|275.777|104.397|

El primer tramo incluye2,072s de antigüedad previa acumulada durante las verificaciones, más el arranque posterior; publicación→inicio4,989s y vaciado observado5,375s no son una latencia normal de cola. En faseB, antigüedad antes de Beat1,992s; las tres marcas aparecieron despejadas con cotas superiores observadas33,675–33,701s desde marcado. Primer refresh31,506s tras iniciar el proceso Beat, intervalo entre sus dos emisiones29,991871s. Expiry se emitió61,494s tras iniciar Beat y la acción se registró64,572947s después de la fecha vencida, incluyendo preparación/arranque. Son observaciones finitas, no SLA ni una garantía de retraso máximo.

Snapshots de marcas no forman un censo atómico de trabajo. El segundo refresh devolvió1con snapshots0→0, coincidiendo con expiry concurrente; no se usa ese0como ausencia de trabajo ni se suman las ventanas como si fueran una contabilidad global. La igualdad final nativa y el vaciado se verificaron aparte.

## Antes y después del lote

| Medida / escenario | Antes disponible | Referencia nueva | Diferencia y límite |
| --- | --- | --- | --- |
| Código de aplicación |4ebc067con corrección N07A |Mismo producto |Sin candidato ni mejora causal de código |
| Mantenimiento directo |N01C/349:271,738ms,102Listings/98marcas, comando con VACUUM/ANALYZE |Refresh worker278,409ms/1marca;177,410ms/3marcas |Etapas, carga y observación diferentes: no comparables como ganancia |
| Cola con worker ausente |Sin esta referencia equivalente |4988,900ms hasta inicio;5374,698ms hasta vaciado observado |Espera/arranque deliberados incluidos; sin porcentaje |
| Cola con worker vivo |Sin muestra equivalente de este lote |24,851/7,390/10,529ms para los tres mensajes Beat |Estados/tareas distintos; sin agregado ni p95 |
| Intervalo refresh / expiry |Configuración30/60s; no SLA de efecto |Refresh29,991871s entre dos ticks; expiry61,494s desde spawn |Una ventana nativa, no acelerar cadencias ni prometer latencia |
| Sweep / refresh manual |Oráculos funcionales, sin esta medida de servicio |452,045/275,777ms, un divergente |Referencias actuales separadas, no optimización ni prueba horaria |
| Retirada durante retraso |Testigos funcionales/SQL/directos previos |18GETcompletos ES/EN y denegaciones con marcas aún presentes |Nueva evidencia asíncrona seleccionada; no todas las superficies |

## Fuentes, errores y trabajo restante

Codex contrastó1754huellas de congelación:1750en el manifiesto del runner y cuatro documentos verificados aparte, selección/JUnit/JSON coincidentes, siete publicaciones/ejecuciones/roles completas y limpieza propia. La primera ejecución224510-1359e09b conserva1FAILFieldError47,249sQA antes del worker; no se reescribe como PASS ni defecto de producto. Se corrigieron cinco lookups del instrumento y su observación de limpieza en excepción. También permanecen los errores previos de lint/importación y del alcance documental del auditor, con sus recibos.

N07 mantiene la conciliación de39IDs, revisión/apelaciones y sus referencias de servicio, y las funciones compartidas con N09/N10. Se conservarán los testigos equivalentes con identidad justificada; no se repetirá toda QA por documentación. N03/N04/N05/N06 y N07A mantienen sus ámbitos, MOD09 restante al final y optimizaciones marginales aplazadas por el usuario. El proyecto permanece en alfa; sin proveedor, carga/Internet/TCP pública o apertura acreditados por este lote.
