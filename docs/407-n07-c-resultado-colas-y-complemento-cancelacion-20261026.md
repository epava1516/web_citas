# N07C — referencias verificadas y complemento de cancelación

26 de octubre de2026. Alfa. Run20261025-233639-833fd457: **16PASS/0FAIL/ERROR/SKIP**,136,563sJUnit. Se acepta la referencia de colas/formularios/decisiones; N07 aún abierto6/13. [Prerregistro406](406-n07-c-prerregistro-colas-revision-apelaciones-20261025.md), [auditoría](evidencias/n07-c-colas-decisiones-auditoria-20261026.json) y [conciliación de testigos/fuentes](evidencias/n07-testigos-fuentes-conciliacion-20261026.json). Sin cambios de aplicación ni mejora temporal atribuida.

## Resultado y muestreo

Ocho casos nuevos verifican cuatro colas y formularios de revisión ES/EN con108GETde cola,48GETde formulario y62controles de autoridad. IDs/orden/conteos/enlaces exactos y desaparición tras resolución; estados0/1/2, objeto/formulario correctos, idioma real y Content-Language, private/no-store autenticado, anónimo/sinpermiso/MFAobsoleta/revocación. La reactivación del idioma después de fixtures /es/ impidió acreditar EN sólo por metadatos. Otros ocho casos existentes conservaron aprobación/rechazo, concurrencia302/400, independencia, reapertura sin publicación automática, protección de contraparte y permisos/imágenes.

El journal global tiene383operaciones:322de los ocho casos con fixtures dinámicas y61de los ocho originales. Los156GETcon medida propia están dentro de383; no son539peticiones ni se suman SQL de ambos observadores. Preparación eager fuera de los relojes propios, globalcall puede contener peticiones de fixture; sin nuevo broker/worker/navegador/proveedor. FileResponse mide construcción/guardas, no nueva descarga completa; N05 conserva su referencia con cuerpo.

1756huellas congeladas:1751en el manifiesto del runner y documentos400/401/403/404/406verificados aparte. Selección/JUnit/propiedades/SQL coinciden, sin excepciones del observador. PostgreSQL propio real, recursos y temporal retirados, Telegram terminal sent y auditoría independiente PASS. La duración de QAno es latencia de la app. No carga/p95, crecimiento100 o SLA.

## Referencias actuales: primera y cinco posteriores

Cada fila: seis observaciones del mismo estado/superficie/idioma. Primera separada; no se afirma caché fría. CPUdel proceso/SQL/bytes completos en la auditoría; CPUno es PostgreSQL. No se promedian filas de estados distintos.

| Familia | Superficie/estado | Idioma | Primera ms | Mediana5 ms | Rango5 ms | SQL | Bytes lógicos |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
|moderation|queue/open|es|44.899|21.976|21.691–25.117|7,8|1200|
|moderation|queue/terminal|es|30.460|29.227|27.046–30.760|7|1096|
|moderation|review_form/open|es|230.184|93.929|85.239–104.921|19|2706|
|moderation|queue/open|en|28.405|25.599|21.789–31.205|7,8|1148|
|moderation|queue/terminal|en|31.386|32.476|31.070–33.760|7|1037|
|moderation|review_form/open|en|75.302|64.778|62.978–71.253|19|2606|
|appeal|queue/before_submit|es|39.561|24.736|21.233–29.530|7,8|1092|
|appeal|queue/open|es|29.777|28.467|26.728–38.897|9|1155|
|appeal|queue/terminal|es|30.407|28.836|23.914–31.663|7|1092|
|appeal|review_form/open|es|41.510|41.323|37.640–47.969|11|2124|
|appeal|queue/before_submit|en|46.984|33.296|27.354–36.353|7,8|1036|
|appeal|queue/open|en|23.154|20.965|20.148–25.594|9|1112|
|appeal|queue/terminal|en|19.631|36.662|32.026–44.097|7|1036|
|appeal|review_form/open|en|36.773|31.965|29.786–37.090|11|2051|
|match|queue/open|es|43.942|44.285|35.442–54.354|7|1184|
|match|queue/terminal|es|37.256|32.324|28.680–37.132|7|1106|
|match|review_form/open|es|76.522|59.183|46.449–67.483|11|2626|
|match|queue/open|en|46.622|43.920|40.411–51.137|7|1124|
|match|queue/terminal|en|36.407|31.843|30.449–48.831|7|1033|
|match|review_form/open|en|234.938|88.931|84.522–95.334|11|2514|
|photo_appeal|queue/open|es|38.896|47.284|37.803–53.200|7,8|1120|
|photo_appeal|queue/terminal|es|62.720|50.651|41.118–56.692|7|1090|
|photo_appeal|review_form/open|es|100.425|68.469|54.343–78.919|19|1960|
|photo_appeal|queue/open|en|39.934|51.947|42.407–59.626|7,8|1068|
|photo_appeal|queue/terminal|en|43.606|45.185|43.294–53.016|7|1028|
|photo_appeal|review_form/open|en|71.863|58.657|47.630–63.616|19|1890|

## Decisiones: muestras individuales, no distribución

Primera coincidencia de cada ruta/status en el caso nombrado. No se agregan mutación, retry o espera de bloqueo como si fueran el mismo estado; el journal conserva todas las61operaciones originales.

| Acción / contexto | Método/ruta/status | n | Pared ms | SQL |
| --- | --- | ---: | ---: | ---: |
|Aprobación|POST/moderation_review/302|1|334.749|85|
|Rechazo concurrente aceptado|POST/moderation_review/302|1|319.818|35|
|Rechazo concurrente ya cambiado|POST/moderation_review/400|1|335.058|26|
|Reclamación inicial|POST/appeal_submit/302|1|49.739|19|
|Reconsideración independiente|POST/appeal_review/302|1|129.685|39|
|Conflicto de fotografía|POST/match_review/302|1|272.511|65|
|Imagen de pareja autorizada, sólo handler|GET/match_image/200|1|108.758|19|
|Reapertura de foto independiente|POST/photo_appeal_review/302|1|267.517|69|
|Aviso privado de restricción|GET/photo_restriction/200|1|68.841|15|

## Antes y después

| Medida | Antes disponible | Después / referencia | Diferencia y límite |
| --- | --- | --- | --- |
| Colas/formularios de estas cuatro familias |Testigos funcionales; sin esta referencia temporal |26segmentos,108+48GET; tabla anterior |Nueva referencia local, sin candidato ni porcentaje causal |
| Decisiones y guardas |Oráculos existentes, sin cronometraje de estas ramas en N01D |61operaciones originales observadas sin editar tests |Estados y concurrencia separados; n1por evento cuando corresponde |
| Producto |34c3f30, N07Aúnico cambio de views |Mismo producto |Sin optimización marginal ni cambio de formato/permiso/semántica |
| QA |Sin batería equivalente |16PASS136,563sJUnit |No tiempo de acción ni mejora de la app |

## Conciliación de evidencia previa

Codex revalidó1507fuentes ejecutables de B16:1500idénticas y siete variantes con cadena y alcance ya aceptados (runner, guardportabilidad, panel, similitud/procesado/recovery y reorder). AST conserva otras funciones y el camino de registros activos tras retirar sólo la guarda histórica de señales para comparar. Parser/hiredis nativos coinciden entre cortes.

145testigos seleccionados en22archivos tienen resultados originales comprobados y límites de versión; incluyen ocho de los16actuales, no161casos de una batería. La batería antigua3829conserva3FAILde CLI y129SKIP; no es globalmente verde. Tres SKIPde prototipos que sustituyen implementaciones SQL no reciben crédito runtime. El primer helper M2M de317tampoco acredita señal real: se conserva la posterior prueba remove/addreal. Tres controles históricos de317usan su instrumento antiguo, producto exacto y aceptación original, sin afirmar igualdad del archivo de test con el actual. La prueba antigua comercial worker/Beat conserva su calendario sintético1s, nunca se presenta como cadencia nativa.

Durante la preparación cambió docs/README.mdpor un enlace paralelo al acuerdo futuro; aparecieron dos borradores ajenos. Se conservan fuera del stage. El prefijo del índice y24citas se revalidaron literalmente, con un nodo de referencia externa; no se ingirieron los contenidos de esos borradores ni se aceptó el siguiente contrato. El primer AST detectó correctamente esa diferencia y su etapa se conserva. No hubo repetición de QApor el índice.

## Complemento funcional antes de cerrar N07

La acción unavailable está en el formulario y en el código, pero los testigos localizados ejecutaban available/pause/resume/withdraw y sólo enumeraban la opción de cancelación. Se añade tests/test_lifecycle_cancellation.py: dos casos ES/EN, sin editar producto. No es una búsqueda de ganancia de rendimiento.

Flujo previsto con PostgreSQL/Client reales y fixture directory: activar disponibilidad→cancelarla, retry exacto sin otro evento, activar una ventana nueva y repetir la cancelación antigua sin que borre esa ventana; finalmente cancelar con clave/versión nuevas. Oráculos: filtro público1→0→1→1→0, publicación/revisión/fechas editoriales conservadas, cuatro eventos nuevos, versiones y actor/gestor correctos, detalle público200. Preparación eager, sin worker/navegador/proveedor; no nueva prueba de CSRFni SLA. Medidas HTTPdel plugin como traza, no mediana entre mutación y retry.

Comando: `.venv/bin/python scripts/run_local_ci.py --profile focused --workers 1 --timeout 900 --native-source /tmp/web-modelos-librdb-v2.4.0 --observe-http-operations --test tests/test_lifecycle_cancellation.py`. Después de AST/semántica focal y congelación nueva. Conservar todo FAIL/ERROR y verificar cleanup/Telegram; no repetir los16casos ya válidos. Después se formalizarán las39disposiciones y el cierre N07, con N09/N10y demás propietarios compartidos conservados. N03/N04/N05/N06/N07A/N07Bmantienen su evidencia; MOD09 restante al final, sin apertura de beta.
