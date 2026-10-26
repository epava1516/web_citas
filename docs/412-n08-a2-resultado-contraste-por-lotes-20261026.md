# N08A2 — optimización nativa por página aceptada localmente

26 de octubre de2026. Alfa, base7107363 y fuentes completas congeladas. Se acepta el único candidato de [411](411-n08-a2-prerregistro-contraste-por-lotes-20261026.md) para las dos lecturas medidas; **N08 sigue abierto y el total continúa7/13**. Run20261026-014812-0d85aaca:13PASS/0FAIL/ERROR/SKIP,321,638sJUnit. [Auditoría](evidencias/n08-a2-contraste-auditoria-20261026.json). No se abre beta ni se añade proveedor/cobro real.

## Problema, cambio y preservación

Favoritos y sitemap ejecutaban publicly_visible por cada listing, con cientos/miles de consultas repetidas. Favorites.index ahora hidrata únicamente los listings de su página con PublicationContext nativo, que ya utilizaba descubrimiento. Valida la instancia hidratada y asigna esa misma relación en memoria para la plantilla, sin save. Sitemaps.listings hidrata sólo el slice actual de candidatos. Páginas vacías o de un elemento conservan el camino original; los demás handlers y los helpers de autoridad no cambian.

Se conservan login/métodos/locks de usuario, cuenta/sesión/propósito, private/no-store y visibilidad fresca; favoritos de otro actor no se mezclan. Los favoritos sin revisión aprobada permanecen como placeholders y no entran en el constructor; una revisión de otro listing no se publica por contexto. Paginador24/orden/conteos incluye los guardados no disponibles. Sitemap conserva count/orden/páginas de candidatos100antes de visibilidad, XML/idiomas/alternates y denegaciones. Cada petición crea su contexto; no se cachean decisiones o filas entre peticiones. No hay cambios de modelos, migraciones, settings, calendarios, transporte, servicios o helpers compartidos. AST de todos los demás handlers y decoradores se verificó idéntico.

## Contraste y oráculos

Las dos versiones se ejecutaron con el mismo PostgreSQL, datos, Client/sesión/cookies entrantes, rutas, middleware y helpers reales. Fuente de referencia exacta de7107363794b378be3fe71e69998f83d9230888f2, SHAvalidado por módulo, compilada con importaciones/decoradores originales; la candidata es la fuente real importada y congelada. Se verificó en cada petición que resolve devolvía el callback seleccionado y se restauró al salir. No se doblaron autorización, validación, datos, reloj o SQL. Esta selección de versiones no acredita HTTPpor socket ni proveedor.

72GETobjetivo:seis segmentos×dos versiones×seis observaciones. Orden de versiones alternado por ordinal, primera separada de cinco posteriores. Normal y una persona revocada fuera de relojes, página1de100favoritos ES/EN y XML100candidatos.118GETinstrumentados nuevos en total:72objetivo,42controles en el caso principal y cuatro de dos negativos ES/EN. Están dentro de167operaciones Clientglobales de los13casos; no son285eventos. Las peticiones de navegador real tienen su propio alcance y no forman parte del contador Client.

Paridad completa de status/headers/cookies/HTMLnormalizado, XMLexacto por bytes y snapshots persistidos de Favorite/Listing/Revision/Person. Sólo se normalizan los valores de inputs CSRF y nonce real conocido si existe; las cookies conservan atributos y valores por hash salvo secreto CSRF y su Expires rodante. No se eliminan diferencias arbitrarias ni se compara sólo tamaño. Los contadores execute_wrapper propio/global coincidieron uno a uno para118GET; no se suman ni dependen de queries_log9000. Ningún error de petición/observador. Oráculos y snapshots fuera del reloj.

## Antes y después: misma población, estado y etapa

Pared Client.GETy cuerpo, primera/mediana5/rango5. CPUdel proceso, no PostgreSQL. SQLson llamadas cursor; no transacciones/filas ni simulación de consulta. En cada segmento se exigió antes del candidato al menos50%menos SQL y20%menos mediana de pared, sin aumento de CPUmediana. Todos cumplen.

| Superficie / estado / idioma | SQL antes→después | Primera ms antes→después | Mediana5 ms antes→después | Rango5 ms antes→después | Cambio pared | CPUmediana5 ms antes→después |
| --- | --- | --- | --- | --- | ---: | --- |
|favorites /normal /en|563→30|1901.546→140.279|2141.365→210.281|1956.869–2292.563→168.653–375.640|-90.180%|1330.945→140.725|
|favorites /normal /es|563→30|2318.419→212.410|2217.110→244.720|1980.253–2440.175→176.324–265.324|-88.962%|1308.087→166.811|
|favorites /one_revoked /en|546→30|2090.621→206.992|2163.705→207.346|1931.175–2503.041→148.209–245.082|-90.417%|1283.726→144.985|
|favorites /one_revoked /es|546→30|2094.232→248.213|2034.547→222.085|1782.943–2278.804→180.597–256.417|-89.084%|1236.301→147.861|
|sitemap_listings /normal /neutral|2402→18|8285.098→373.213|9009.700→375.775|8120.188–9402.498→275.209–502.600|-95.829%|5328.155→297.063|
|sitemap_listings /one_revoked /neutral|2385→18|9115.305→381.759|9292.321→277.708|8062.111–9593.571→247.944–344.182|-97.011%|5610.650→212.325|

Favoritos normales:563→30SQL (−94,671%); XMLnormal:2402→18SQL (−99,251%). No se promedian idiomas/estados. Las cifras causales son las del par dentro de la misma base; no se calculan contra410, cuya población UUID y configuración de depuración eran distintas.

| Control pequeño, una observación por versión | SQL antes | SQL después | Decisión |
| --- | ---: | ---: | --- |
|favorites /small_0 /es|10|10|Sin aumento|
|favorites /small_0 /en|10|10|Sin aumento|
|sitemap_listings /small_0 /neutral|1|1|Sin aumento|
|favorites /small_1 /es|34|34|Sin aumento|
|favorites /small_1 /en|34|34|Sin aumento|
|sitemap_listings /small_1 /neutral|26|26|Sin aumento|
|favorites /small_10 /es|241|30|Sin aumento|
|favorites /small_10 /en|241|30|Sin aumento|
|sitemap_listings /small_10 /neutral|242|18|Sin aumento|

No se atribuye distribución de tiempo a los controles n1. El resto verifica índice/página2nativos101antes/después de revocación, query y páginas inválidas, anónimo, lista del actor ajeno y revisiones nula/foreign con propietario válido presente. El placeholder sigue contando y no expone enlace/UUID del listing inválido; no se prohíbe por error un título que sí pertenece al propietario válido. Los seis objetivos mantienen el mismo contenido útil, orden, cardinalidad y bytes por par.

## Regresión, recursos y límites

Trece casos:un par completo, dos negativos ES/EN y diez originales sin editar (favoritos3, sitemap3, SEO4). Las tres navegaciones Chromium se ejecutaron con el código candidato tras restaurar callbacks. El ejecutable configurado se observó como Chromium156.0.8078.47, compilación RHEL9.8; no se acredita inmutabilidad de todo el runtime ni rendimiento del navegador. Las diez regresiones se repitieron por el cambio real de handlers, sin repetir la referencia300GETpor documentación.

1755huellas congeladas:1754del runner y411verificado aparte; sources_unchanged verdadero. PostgreSQL/Redis propios y temporales retirados, Telegram terminalsent, auditoría independiente PASS. Preparación directory/populate101eager/medios compartidos fuera de relojes, sin crédito de moderación101nativa ni worker. RSS high-water de proceso:275,926MiB en el caso pareado y hasta318,383MiB en los nuevos negativos; cumple protección1GiB. No se atribuye ese high-water a una versión o petición. Contextos acotados a la página; sin fetch de toda la población a Python.

Muestras finitas Clientinstrumentadas: no caché fría garantizada, p95/p99, SLA, carga80 000fotos, memoria/CPUdel servidor PostgreSQL, proveedor o coste humano. Los321,638s son QAde13casos y no latencia de app; tampoco constituyen un contraste causal de velocidad de QAcon434,775sdel lote410. No se suavizaron guardas ni criterios tras medir y no se encadenó otra hipótesis. La mejora clara permite conservar este candidato; las optimizaciones sin mejora clara siguen diferidas al final conforme al usuario.

## Continuación

N08B:historial de pedidos25frente a opciones sin paginar, catálogo/versiones50y guardas comerciales sintéticas; conciliar autosubida y las17disposiciones con los77testigos históricos y esta variante de dos handlers. N08no está cerrado por esta aceptación parcial. N03/N04/N05/N06/N07 y N09/N10compartidos conservan sus alcances; N11integrará la candidata y N15reconstruirá el grafo completo antes del diferencial final e inventario de relevofrontend. Sin apertura de beta o ejecución de ese futuro contrato.
