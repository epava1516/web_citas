# Análisis del bloqueo de rendimiento y DAFO — ciclo manual SQL

Corte:2026-10-07. Goal automático pausado; encargo manual de cierre vigente. Fuentes de trabajo sobre `b285aba`, con SHA de cada ejecución en sus informes; runtime normal `73d28f6` intacto. Las últimas baterías terminaron con exit0 y retirada verificada. La única cola y próxima acción están en [seguimiento17](17-seguimiento-desarrollo.md); este documento explica la decisión, no programa otro ensayo.

Se conservan íntegros el [primer DAFO](17-historial/2026-10-07-analisis-dafo-primer-corte.md) y el [DAFO anterior a estos pilotos SQL](17-historial/2026-10-07-dafo-antes-pilotos-sql.md), SHA256 del segundo `5f1c044f9865782fe1181fa0705712c2a231de3d1476c0e7006268f5d3f875fe`. Sus cifras y propuestas pertenecen a sus fuentes; no se presentan como el estado del backend nuevo.

## Conclusión actual

**El coste ha disminuido en contrastes medidos, pero CR09-REND-LECTURA sigue sin cerrar.** La causa pendiente ya no puede describirse solo como diez mil ModelForms o como un generador defectuoso. La prueba SQL suficiente evita ese recorrido cuando puede certificar los datos actuales; conserva fallback nativo para desconocidos y guard de vigencia de la página. Se han corregido lecturas concretas y búsqueda. Aun así, los controles de la ruta vigente siguen alrededor de un segundo y faltan N2/rutas, matriz común y carga válida de la implementación final.

La cadena de evidencia distingue tres hechos:

1. La preparación de valores/bindings por10.000 candidatos era costosa incluso después de reducir objetos. El [contraste SQL](evidencias/listado-sql-prueba-positiva-coste0110.json) sí comparó ambos recorridos en la misma ejecución:3,468318→1,543159s repetido y7,995887→1,564744s diverso, con oráculo nativo completo. Eso es mejora medida de ese cambio, no una estimación desde el profiler.
2. La forma SQL importa. Llevar todo a un WHERE conjunto empeoró el coste y se descartó; agrupar dependencias actuales redujo accesos repetidos. JSON estricto y búsqueda generada redujeron trabajo, pero su primer contraste no cumplió en diverso. Solo la comparación posterior aisló y confirmó el alcance local de JIT de página allí afectado. Los resultados negativos permanecen.
3. El coste actual existe también en [Gunicorn real serial](evidencias/listado-sql-runtime-serial0110.json): listados/búsquedas ESEN alrededor de0,86–1,02s en medianas de cuatro controles por ruta/fixture. No es solamente un artefacto del proceso de fixtures. GC observado tiene coste y solapamientos, pero no explica por sí solo el request. No se ha medido todavía capacidad concurrente actual.

La conexión decisiva es que **resolver el conjunto elegible completo no obliga a construir formularios por candidato, pero tampoco convierte una prueba SQL compleja en barata**. Hace falta evaluar la ruta completa y sus límites. Una reducción de contadores, una N1 correcta o una apariencia de SQL más compacta no bastan para cerrar.

## Qué se aprendió desde la segunda pausa

| Evidencia | Qué permite concluir | Qué no permite concluir |
| --- | --- | --- |
| [Prueba SQL positiva, N1](evidencias/listado-sql-prueba-positiva-n1-final0110.json),15PG | Equivalencia del subconjunto suficiente probado, IDs/páginas y desconocidos nativos. | Seguridad universal de cualquier regla futura o de toda entrada Unicode. |
| [Conjunto WHERE](evidencias/listado-sql-conjunto-coste0110.json),2PG | Igualdad funcional, pero tiempos peores:1,488/1,409s→2,166/2,046s. | Que cualquier SQL por conjuntos mejore automáticamente. |
| [Dependencias agrupadas](evidencias/listado-sql-dependencias-coste-final0110.json),2PG | Efecto prefijado cumplido:1,504→1,053s y1,583→1,044s. | Ahorro sumable con pilotos de otra fuente, ni mejora de producción. El runner se recuperó tras interrupción; exit status no recuperado. |
| [Perfil bulk](evidencias/listado-sql-perfil-actual0110.json),2PG |280construcciones/modelos, consultas y validación/eventos observados con fuente propia. | Los exclusivos invasivos no son tiempo disponible para ahorrar en controles. |
| [Búsqueda/JSON N1](evidencias/listado-sql-busqueda-json-n1-0110.json),19PG | Vector generado equivalente al original, writes/rank/páginas y JSON de tipos/formas probados. | Coste de escritura/almacenamiento, cambio de diccionarios o aceptación de derechos/inventarios sin regresión pertinente. |
| [JIT de página](evidencias/listado-sql-busqueda-json-jit-coste0110.json),2PG | Tres variantes separan A→C combinado y B→C política local. Efecto material completo en ambos fixtures. | Que el JIT explique todos los tiempos, ni que haya ahorro donde no se activó. |
| [Página certificada N1](evidencias/listado-sql-pagina-certificada-n1-0110.json),10PG | Evaluación SQL completa antes de count/página; unknown/duplicado devuelve población completa. Páginas, huella y revocación conservadas en casos probados. | Capacidad o ventaja suficiente solo por transferir24IDs en vez de10.000. |
| [Página certificada, coste](evidencias/listado-sql-pagina-certificada-coste0110.json),2PG | Menores medianas en muestras, pero criterio previo de efecto incumplido en ambos fixtures. | Aceptación del piloto. Queda fuera de ruta por defecto y se conserva explícitamente para diagnóstico. |
| [Atribución SQL/preparación](evidencias/listado-sql-coste-restante0110.json),2PG | Predicados PlainText muestran delta marginal relevante; Telegram no. Preparación/compilación medidas directamente. | Omitir textos no es un backend correcto, ni mide CPU PostgreSQL o validación Python. |

Las suites son independientes: no se suman como una N2 común. Manifiestos, fallos iniciales y decisiones completas permanecen en la [cronología](17-historial/2026-10-07-pilotos-sql-manuales.md) y sus evidencias originales.

## Atribución restante y decisión

El [último diagnóstico prefijado](evidencias/listado-sql-coste-restante-manifiesto0110.json) capturó el queryset real de la ruta completa y preparó tres lecturas aisladas: original, omisión de PlainText y omisión de Telegram. Todas leen10.000 filas sintéticas válidas; las omisiones nunca sirven HTTP ni se adoptan como reglas. Coincidir sobre datos válidos no demuestra equivalencia sobre datos inválidos.

| Medición, segundos | Repetido contractual | Descripciones/Telegram únicos |
| --- | ---: | ---: |
| SQL execute completo, mediana |0,393499|0,371840|
| SQL execute sin PlainText, mediana |0,262852|0,245970|
| Delta PlainText emparejado, mediana |0,136002|0,119367|
| Pares favorables PlainText |4/4|4/4|
| Delta Telegram emparejado, mediana |0,037223|−0,023028|
| Construcción sin evaluar población, mediana |0,031214|0,024723|
| Compilación aislada del SQL completo, mediana |0,020165|0,018293|
| HTTP plain, mediana |1,027227|0,889131|
| HTTP con observer focalizado, mediana |1,020711|0,886620|

El grupo PlainText supera≥0,05s y3/4pares; Telegram no. La omisión puede cambiar plan y orden de evaluación: sus deltas son marginales de esas lecturas, no duración pura de cada regex y no se suman. El delta de medianas tampoco sustituye la mediana de deltas emparejados usada para decidir.

En los HTTP observados, compilación152calls/exclusivo mediano0,065081/0,056175s, clonado de Query694calls/0,008345/0,007677s y construcción de condiciones157calls/0,029741/0,025994s. Cada exclusivo descuenta hijos instrumentados directos una sola vez. Inclusivos recursivos se solapan. Las medianas por método no forman una partición sumable del request. Compatibilidad numérica del observer cumplida, no overhead causal. Huella/body/count/ruta permanecen iguales; la observación de ruta no acredita la completitud de la huella.

**Decisión técnica:** mantener el recorrido SQL conservador que ya mostró efecto; descartar como mejora suficiente la transferencia compacta aislada. El siguiente candidato justificado es reformular la comprobación SQL de textos conservando longitud, obligatoriedad, alfabeto permitido y exclusiones de contactos, con comparación contra la expresión anterior y validación nativa. Reunir condiciones redundantes puede ser un candidato; se ha preparado como candidato con control legado y N1 prefijada, todavía sin resultado funcional ni de coste en este corte; no se presupone su ahorro. Su efecto posible tampoco explica por sí solo todo el coste restante: hay que contrastar el request completo y rechazarlo como solución suficiente si sigue lejos del presupuesto.

No hay evidencia para priorizar Telegram, quitar la huella, eliminar validaciones, sustituir la compilación por caché, aumentar workers ni escalar PostgreSQL. La preparación medida es relevante en su alcance, pero no explica por sí sola el segundo completo; no se obtiene esa conclusión restando SQL al total.

**Resultado posterior del candidato textual:**9PG de equivalencia correctas148,41s;950textos×4configuraciones,797positivos nativos y3003unknowns. El [contraste completo](evidencias/listado-sql-texto-unificado-coste0110.json) de2PG228,65s no cumple ambos fixtures: repetido falla (2/4parejas), diverso cumple (3/4). Se restaura la forma legada; no se presenta como mejora aceptada. La expresión más corta no resolvió el coste completo.

**Hipótesis acotada siguiente:** un índice parcial ordinario sobre IDs cuyo contenido queda fuera de la prueba suficiente puede cambiar el acceso físico sin almacenar una decisión de publicación. La consulta conserva el predicado; PG mantiene el índice al escribir. Autoridad/documentos/revocación siguen frescos y los unknowns siguen nativos. Solo un prototipo en base propia, comparando forma porfila, conjuntos sin índice y conjuntos con índice, puede separar ese mecanismo de una mera reformulación. No se ha adoptado migración ni ruta nueva ni se conoce su ahorro HTTP. Mantener límites de planes/prepared statements y costes de escritura; condiciones técnicas en [documentación PG](https://www.postgresql.org/docs/16/indexes-partial.html), prefijación en seguimiento17.

**Prototipo del índice, resultado:** [evidencia SQL](evidencias/listado-sql-indice-texto-probe0110.json) cumple efectos combinado y físico en ambos fixtures, cuatro parejas favorables. Los planes muestran uso real de los dos índices. Igualdad de vectores completos y mantenimiento por escrituras/rollback comprobados; no HTTP todavía. Se prepara integración con expresión versionada compartida y migración propia, N1 antes del contraste completo. Este resultado supera la incertidumbre del mecanismo SQL, no el bloqueo de capacidad.

**Contraste HTTP del índice:** [2PG](evidencias/listado-sql-indice-texto-coste0110.json), equivalencia correcta pero criterio conjunto insuficiente: repetido4/4parejas, diverso2/4. Medianas diversas más bajas no cambian ese resultado. Opción por defecto vuelve a row proof; candidato/index migration aún experimentales. El mecanismo SQL demostrado no acredita consistencia de ahorro HTTP ni capacidad. La nueva incertidumbre es la distribución directa del coste dentro del request y su variación; el árbol de llamadas/GC se prefija en seguimiento17 sin otra modificación backend.

**Nueva atribución directa:** [árbol de llamadas](evidencias/listado-sql-arbol-coste-http0110.json),2PG;10271decodificaciones timezone/request, inclusivo≥0,05s en4/4muestras de ambos fixtures. La captura ORM descarta una fecha de orden que DISTINCT obligó a devolver. Candidato: conservar DISTINCT/orden/población en SQL y limitar transferencia a identificadores canónicos/bool, materializando UUID al consumirlos. No es recortar candidatos. GC se solapa y varía, pero no se atribuye causalmente a esos objetos; perfil mediano1,218/1,250s frente a plain0,822/0,888s, overhead sustancial. N1 y contraste del mecanismo pendientes; requisitos completos intactos.

## DAFO actualizado

| Dimensión | Evidencia actual | Consecuencia para consolidar |
| --- | --- | --- |
| Fortalezas | Oráculos de IDs ordenados/count/páginas; negativas fuera de página; wrappers/helpers y revocación concurrente; PG aislado y SHA; controles emparejados repetidos/diversos; veredictos negativos conservados. | Permiten probar un cambio con protección funcional y rechazarlo por coste. Reutilizar evidencias válidas y completar una N2 común cuando exista un candidato viable. |
| Debilidades | Ruta aún≈1s; conjunto completo se comprueba en cada request; huella finita y subconjunto SQL conservador; varias implementaciones experimentales; R3/R4 actuales pendientes. | Evitar sumar microganancias de fuentes diferentes y acumular alternativas como código aceptado. Desconocidos válidos pueden ir a una ruta nativa costosa; medir ese límite y los modos excluidos explícitamente. |
| Oportunidades | Coste marginal de PlainText localizado; búsqueda ya puede usar un vector derivado coherente; reglas compartidas y autoridad fresca preservables sin persistir elegibilidad. | Contrastar simplificación equivalente y coste total. Separar contenido de autoridad solo cuando sus dependencias lo permiten, manteniendo fallback y guard. |
| Amenazas | Fixture diverso modifica descripciones/Telegram, pero no cubre todas las lenguas/formas; Unicode no certificado y modos PRODUCTION/checked/promociones pueden seguir nativos; carreras READ COMMITTED, deriva de reglas y diccionarios; profiler invasivo. | No extrapolar al producto completo. Recuento y paginación antes de exposición, pruebas de vigencia/revocación y reporte de rutas/costes son condiciones de cierre. |

Cruce: fortalezas–oportunidades, usar el oráculo para simplificar el predicado medido; debilidades–oportunidades, juzgar la ruta completa y no un nombre del profiler; fortalezas–amenazas, conservar casos adversarios y autoridad actual; debilidades–amenazas, mantener el bloque abierto si el fixture favorable no cubre una ruta declarada. La repetición de datos puede favorecer reutilización, pero el contraste diverso controla solo las dependencias efectivamente variadas.

## Arquitectura y límites funcionales

La ruta ordinaria actual captura IDs/prueba suficiente de toda la población, evalúa desconocidos nativamente antes de contar/paginar, hidrata24 y vuelve a comprobar la página con autoridad actual. La alternativa compacta evaluaba igualmente todo antes de reducir transferencia, pero no se acepta como mejora suficiente. Las consultas usan READ COMMITTED: no hay una instantánea atómica de todo el request. El guard y la recomputación nativa ante cambios confirmados permanecen.

`search_document` es una columna generada a partir de título/descripciones/lengua con la misma expresión de pesos y configuraciones. No guarda autoridad ni elegibilidad. La base la recalcula con cada escritura de sus entradas; cambios externos de diccionarios/configuraciones de texto requieren regeneración y no están acreditados. Migración aplicada solo en bases sintéticas propias. Su efecto sobre copias e inventarios de derechos debe entrar en R3.

La huella comprueba cadenas efectivamente ejecutadas, incluidos wrappers `functools.wraps`, y helpers auditados. No se usa `inspect.unwrap` para declarar transparente un cambio semántico. Es un detector finito de cambios revisados, no una garantía sobre cualquier monkeypatch posible. Observar «projection» no prueba que esa huella cubra toda nueva regla.

`rows_returned`: solo longitudes de fetch explícito en sentencias aisladas del último diagnóstico; la sentencia compacta incluye una cabecera auxiliar aparte de IDs. Construcciones ORM, referencias y segmentos de iteración no son filas SQL. Rows_affected/scanned, CPU/RSS/waits/locks/IO PostgreSQL, overhead causal, costes de escritura/almacenamiento y capacidad actual: `not_measured`. Los perfiles por regla/render/modelos anteriores conservan su fuente; esas métricas no se midieron en el último diagnóstico focalizado. SQL execute incluye driver/servidor/esperas/buffering y excluye el fetch explícito posterior; no es CPU PostgreSQL. Nunca total−SQL como validación Python.

## Aceptación pendiente

Con4workers sync/20RPS,0,2s medios por request es una referencia de ocupación antes de margen/uploads. No es nuevo SLO ni prueba de capacidad, y las medianas seriales no son demanda media concurrente. Los controles actuales siguen claramente lejos; por eso no se repite una carga larga para demostrar de nuevo el desfase.

N2 y rutas sobre una fuente común → matriz100/1.000/10.000 con instrumentos equivalentes y controles → corta20RPS/60s →900s solo con PASS completo. El FAIL corto anterior y el INVALID contractual se conservan. Contrato10.000/20RPS/900s/18.000, ESEN1/3listado–1/3búsqueda–1/3ficha,15uploads1/min; p95<800ms y errores<1%. Corta1.200dinámicas/1upload302; generador0noemitidas, demora p95≤10/p99≤25/max≤100ms, timeout65s, drain≤70s, pendientes al cierre≤20/final0. FAIL o INVALID bloquean el contractual.

No se declara cerrado CR09-REND-LECTURA, CR09, ni producción. Porcentajes65,375% y CR09 72,50% intactos. El grafo enlaza estas fuentes y diferencia observación de hipótesis; un recorrido no demuestra causalidad.
