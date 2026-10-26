# N08A — referencia de superficies secundarias verificada

26 de octubre de2026. Alfa, base0501b52. Run20261026-004939-72f06ea0: **3PASS/0FAIL/ERROR/SKIP**,434,775sJUnit (7min14,775s de QA). Se acepta esta referencia finita, no N08 completo:7/13bloques obligatorios. Sin cambio de aplicación ni mejora temporal atribuida. [Prerregistro409](409-n08-a-prerregistro-superficies-secundarias-20261026.md), [auditoría](evidencias/n08-a-superficies-auditoria-20261026.json), [conciliación SQL](evidencias/n08-a-contadores-sql-conciliacion-20261026.json) y [testigos anteriores](evidencias/n08-testigos-fuentes-conciliacion-20261026.json).

## Resultado, controles y alcance

1754huellas congeladas,1753del manifiesto ejecutable del runner y409verificado aparte; sources_unchanged verdadero. PostgreSQL/Redis propios reales, temporal y recursos retirados, Telegram terminalsent. Preparación eager con dos cohortes de101publicados y medios sintéticos compartidos, fuera de relojes. Documentos legales:202filas propias, sin seed, validez jurídica o contenido de operador. Datos siempre sintéticos.

300GETmedidos en50segmentos:156favoritos/26segmentos,84XML/14segmentos y60legales/10segmentos. Están dentro de322operaciones globales, nunca622; los22restantes incluyen negativos y posibles peticiones de fixtures. Oráculos de objeto/IDs/orden/paginación/contenido/enlaces/idioma real se ejecutan fuera del reloj. Un segmento contiene primera llamada y cinco posteriores del mismo tamaño, estado, página e idioma; no caché fría, p95, carga, socket, navegador, worker o proveedor acreditados.

Favoritos:0/1/10/100propios y otroactor, páginas nativas24, sin omisiones/duplicados ni enlaces ajenos; el favorito revocado persiste y sigue contando, pero no filtra título/teléfono/UUID/enlace del perfil. Snapshot de identidad/propietario/listing/created_at intacto tras GET; private/no-store y anónimo302. Sitemap:0/1/10/100/101candidatos, páginas reales100 sin patch, XML/alternates exactos según revisión pública; revocar uno no altera el índice por candidatos pero lo excluye de ambos documentos y de detalle404. Queries/página0/fuera de rango denegadas, borrador privado ausente, no-store/noindex alfa. Legales:0/1/10/100activos por idioma, orden slug/enlaces/contexto correctos, detalle público propio e inactivo/idioma ajeno404; todas las columnas de LegalDocument conservadas después de GET.

## Corrección de la auditoría SQL, sin repetir QA

El primer auditor falló al exigir igualdad entre CaptureQueriesContext y el contador global. No es un fallo funcional de los tres casos. Se preservan auditor e intento originales. Se comprobó el código instalado de Django: queries_log es deque(maxlen9000); CaptureQueriesContext usa posiciones len/slices sobre ese registro y pierde entradas al saturarse.54muestras de favoritos y44XML llegaron a cero de depuración aunque hubo trabajo SQL. Además, el registro debug incluye BEGIN/COMMIT que no son llamadas cursor.execute observadas por execute_wrapper: la primera muestra vacía de favoritos tiene15entradasdebug frente a11llamadascursor. No son dimensiones idénticas ni contadores sumables.

Se descartan **todos los contadores/tiempos SQLpropios de depuración** para el resumen, no sólo los favorables. La fuente canónica es el observador global existente scripts/http_operation_metrics.py: contador entero por connection.execute_wrapper, sin depender del registro9000. Las300muestras se emparejaron exactamente una a una por caso/ruta/GET200/orden, con pared propia mayor o igual a la interna. No hubo excepciones de petición ni errores del observador. Se conservan crudos originales y filas canónicas separadas; el contador canónico mide llamadas de cursor y su tiempo, no transacciones/filas/SQLlógicos totales. Pared/CPU/bytes propios permanecen medidos; no se modifican las respuestas ni se reejecuta la prueba para resolver este problema de observación.

## Tiempos por segmento

Pared del Client.GETcompleto y cuerpo; CPUdel proceso/SQLexecute/bytes en auditoría. CPUno es PostgreSQL. Instrumentación y depuración incluidas, no tiempo de producción. Tabla: primera/mediana de cinco/rango de cinco, con SQLcanónico global. No promediar entre filas.

| Superficie | Estado | Idioma | Página | Primera ms | Mediana5 ms | Rango5 ms | SQLcursor | Bytes |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
|favorites|own_0|es|1|54.442|20.153|19.802–21.111|10,11|1188|
|favorites|own_0|en|1|138.654|18.107|17.306–22.299|10|1137|
|favorites|own_1|es|1|79.949|78.676|72.111–104.516|34|1523|
|favorites|own_1|en|1|79.979|96.260|74.505–111.012|34|1473|
|favorites|own_10|es|1|644.186|737.413|671.992–798.060|241|4863|
|favorites|own_10|en|1|783.127|868.952|681.222–986.705|241|4795|
|favorites|own_100|es|1|2049.298|1774.832|1693.781–2102.804|563|10112|
|favorites|own_100|es|2|2227.577|2153.938|1866.276–2296.312|563|10137|
|favorites|own_100|es|3|1695.377|1887.027|1739.221–2468.091|563|10131|
|favorites|own_100|es|4|1876.597|1961.039|1785.484–2110.814|563|10129|
|favorites|own_100|es|5|317.244|313.235|247.105–351.491|103|2666|
|favorites|own_100|en|1|1705.888|2106.043|1957.324–2132.694|563|10011|
|favorites|own_100|en|2|2562.048|1926.374|1842.313–2202.531|563|10036|
|favorites|own_100|en|3|2025.820|2042.438|1858.990–2304.750|563|10030|
|favorites|own_100|en|4|2169.100|1967.371|1764.419–2066.429|563|10028|
|favorites|own_100|en|5|312.328|356.218|331.251–494.365|103|2610|
|favorites|own_100_one_revoked|es|1|1679.372|2132.131|1849.643–2447.707|546|10017|
|favorites|own_100_one_revoked|es|2|1913.872|1900.700|1730.129–2242.097|563|10137|
|favorites|own_100_one_revoked|es|3|1972.590|2131.920|1905.199–2523.435|563|10131|
|favorites|own_100_one_revoked|es|4|2352.243|2152.848|1902.019–2313.526|563|10129|
|favorites|own_100_one_revoked|es|5|389.178|315.741|289.651–349.510|103|2666|
|favorites|own_100_one_revoked|en|1|1952.177|1962.778|1742.432–2263.377|546|9914|
|favorites|own_100_one_revoked|en|2|2444.403|1976.561|1761.327–2115.320|563|10036|
|favorites|own_100_one_revoked|en|3|1953.106|2021.740|1852.355–2412.796|563|10030|
|favorites|own_100_one_revoked|en|4|1800.067|2184.844|2123.346–2302.365|563|10028|
|favorites|own_100_one_revoked|en|5|385.916|335.861|313.341–400.817|103|2610|
|sitemap_directory|directory|neutral|0|2.335|0.829|0.812–0.848|0|680|
|sitemap_index|candidates_0|neutral|0|4.874|3.954|3.639–4.227|1|216|
|sitemap_index|candidates_1|neutral|0|4.769|4.505|4.250–4.635|1|313|
|sitemap_listings|candidates_1|neutral|1|121.476|138.853|88.920–170.324|26|950|
|sitemap_index|candidates_10|neutral|0|6.599|4.207|4.108–4.359|1|313|
|sitemap_listings|candidates_10|neutral|1|934.349|819.605|742.547–999.589|242|8150|
|sitemap_index|candidates_100|neutral|0|4.364|3.175|2.932–4.323|1|313|
|sitemap_listings|candidates_100|neutral|1|9101.948|9177.501|8307.407–9953.695|2402|80150|
|sitemap_index|candidates_101|neutral|0|3.622|2.803|2.755–3.036|1|410|
|sitemap_listings|candidates_101|neutral|1|8184.430|8230.885|7797.178–8544.695|2402|80150|
|sitemap_listings|candidates_101|neutral|2|79.159|91.842|86.854–102.600|26|950|
|sitemap_index|candidates_101_one_revoked|neutral|0|4.726|4.340|4.156–4.977|1|410|
|sitemap_listings|candidates_101_one_revoked|neutral|1|8436.320|8775.309|8363.407–9124.172|2385|79350|
|sitemap_listings|candidates_101_one_revoked|neutral|2|72.564|71.422|69.169–101.857|26|950|
|legal_index|active_per_language_0|es|0|15.878|6.878|6.029–10.779|1|1236|
|legal_index|active_per_language_0|en|0|8.785|6.378|6.054–6.491|1|1182|
|legal_index|active_per_language_1|es|0|8.980|7.947|7.110–9.354|1|1321|
|legal_index|active_per_language_1|en|0|8.912|7.782|6.956–12.913|1|1267|
|legal_index|active_per_language_10|es|0|6.998|7.275|5.337–7.734|1|2086|
|legal_index|active_per_language_10|en|0|7.050|4.482|4.062–5.617|1|2032|
|legal_index|active_per_language_100|es|0|9.355|10.226|9.542–13.007|1|9736|
|legal_document|active_per_language_100|es|0|5.984|2.982|2.867–3.788|1|1291|
|legal_index|active_per_language_100|en|0|8.475|8.759|8.537–11.592|1|9682|
|legal_document|active_per_language_100|en|0|3.228|3.466|3.023–4.136|1|1238|

## Antes y después

| Medida / escenario | Antes disponible | Después / referencia actual | Diferencia y límite |
| --- | --- | --- | --- |
| Favoritos100, página1 ES/EN, mediana5 |N01D tenía mutaciones y pequeño listado, sin esta cohorte |1774,832/2106,043ms y563llamadasSQL por página |No base equivalente/candidato; no mejora causal |
| Favoritos100, página5 ES/EN, mediana5 |Sin base equivalente |313,235/356,218ms y103llamadasSQL |Cuatro elementos en última página, no comparar como aceleración de la primera |
| XML100candidatos página1, mediana5 |Testigo N01D usaba PAGE_SIZE1 |9177,501ms y2402llamadasSQL |Referencia nativa100; primera9101,948ms, rango8307,407–9953,695ms |
| Legales100activos ES/EN, mediana5 |Sin referencia temporal equivalente |10,226/8,759ms y1llamadaSQL |Contenido sintético, sin juicio jurídico |
| Producto / contenido / autoridad |0501b52 |Mismo código, oráculos cumplidos |No cambio ni nueva mejora de app |
| QA |Sin batería equivalente |3PASS434,775sJUnit |No duración de una acción; no sumable con77testigos históricos |

## Reutilización y siguiente contraste

Codex comprobó77resultados originales seleccionados en16módulos: favoritos3, sitemap3, SEO4, catálogo26, pedidos/sus variantes/auditoría y exposición/bump/restauración. Fuente actual de cada archivo coincide con su resultado original. Los cuatro casos elegidos de N01D sustituyen sus mismos testigos amplios, no añaden casos distintos.1507fuentes ejecutables B16 conservan1500idénticas y las siete variantes aceptadas N03/N06/N07A; el selector person_queryset permanece ASTidéntico y sólo panel difiere en agencies.py. La suite amplia declara3833, pero contiene3829testcase XML,3FAIL/0ERROR/129SKIP; no se presenta como globalmente verde. Los navegadores originales conservan su contexto155, sin atribuir nueva ejecución156. N03/N04/N05/N06/N07 y propietarios compartidos se mantienen.

La referencia identifica un coste concreto: favoritos y sitemap validan individualmente cada listing mediante publicly_visible sin PublicationContext, lo que produce563consultas para24entradas y2402para100candidatos. Ya existe validación nativa por lote en descubrimiento, con hidratación acotada y autoridad/revocación por petición. Esto justifica estudiar **un único candidato acotado** a esas dos lecturas; no se altera todavía producto. Debe conservar favoritos guardados/orden/placeholders, páginas de candidatos100, errores/retirada inmediata y todas las guardas. Evitar la revisión nula/ajena al construir contexto y validar con sus propias instancias hidratadas.

Antes de implementar: nuevo prerregistro, grafo, fuentes y criterio. Un contraste pareado puede ejecutar ambas versiones sobre la misma base/datos y los mismos estados, sin repetir las300peticiones por rutina; conservar comparación causal sólo de las muestras equivalentes. No sustituir autorización, reloj, datos o guardas por simuladores. Presupuestos354: contenido/efectos exactos, no más coste determinista, reducción estricta objetivo y tiempo comparable; conservar cualquier FAIL/inconclusión. Si no mejora claramente, se mantiene la implementación vigente y se difiere al final del desarrollo para pasar a N08B.

N08B queda pendiente: separar historial paginado25de las opciones sin paginar, catálogo/versiones50y guardas de simulación/propiedad/MFA/idempotencia; autosubida se concilia con testigos reales y su cadencia60s, sin presentar el diagnóstico histórico1scomo nativo. Falta formalizar17disposiciones y aceptación N08. Sin apertura de beta, cobros/proveedores reales ni cambios de servicios/migraciones.
