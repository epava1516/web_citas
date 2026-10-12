# MOD-08 — Puertas previas a integrar el manifiesto paginado — 2026-10-11

## Decisión

El usuario autorizó implementar, probar y aceptar si funciona. Se implementaron y midieron dos proveedores experimentales de datos en PostgreSQL real antes de añadir persistencia o conectarlos al endpoint. **Se rechaza la integración directa que conserva el contrato de fuente completa:** produce una regresión del 57,83 % en la mediana wall. No se introdujeron nuevos cambios productivos, migraciones ni caché de autoridad. Se preservan las optimizaciones previamente verificadas.

Esto no descarta universalmente una API con inventario autenticado de referencias y campos que evite reconstruir valores completos. Esa alternativa necesitaría un contrato distinto, equivalencia de cada consumidor y sus propios ensayos. No está implementada ni aceptada por estos resultados. Los objetivos de navegación2s/descargas5s continúan pendientes.

## Implementación medida

- `tests/capacity_page_manifest_physical.py`: hash fresco del contenido de las filas de todas las familias del inventario source_fingerprint. Hashes calculados en PostgreSQL, cuerpos no transferidos. Revision excluye únicamente los ocho campos ya diferidos en source_copy (incluido search_document); restantes familias se hashean completas. Es una variante conservadora de comprobación de contenidos, no una demostración de que todo posible diseño de frescura necesita este coste. Usa el esquema de atributos/manifest/chunks del prototipo y verifica contenido físico antes y después.
- `tests/test_capacity_page_manifest_physical.py`: la lectura de50filas incorpora esos dos hashes físicos; compara baseline original inspection_source. Scope sólo datos.
- `materialize_physical` y `tests/test_capacity_page_manifest_consumers.py`: alternativa que devuelve un dict ordinario completo al inspection_source existente. Una consulta masiva trae30chunks, descifra un manifiesto una vez y un header cifrado aparte; comprueba posiciones, conteos, bindings, expiración y contenido físico antes/después. El contexto original mantiene su digest HMAC completo, comprobación de mutación del objeto y bracket de deriva de base de datos. No se multiplican30veces los guards por chunk.

El consumidor actual project_selected recorre todas las filas y reconstruye valores seleccionados; compile_coverage devuelve asimismo projection. No puede recibir50filas presentadas como una fuente de1500. Esta prueba conserva esa forma de fuente. Una API explícita para validar referencias/paths y obtener sólo valores necesarios sería una implementación diferente; no se ha sustituido canonical por un contenedor lazy.

**Los proveedores siguen sólo en tests:** no reproducen todavía bloqueos, callbacks de expiración, catálogo/permisos/restore ni ciclo de retención de un proveedor productivo. Su tiempo es un límite inferior; una regresión aquí basta para rechazar esta forma sin debilitar esas obligaciones. No se presenta como integración segura ni N2 superado.

## Protocolo y resultados

PostgreSQL17 real, kernel native-sealed,1500revisiones sintéticas/16MiB, misma conexión caliente, página de50filas. Dos warmups por brazo y20paresABBA. Preparación fuera del reloj, registrada; guardas SQL/descifrado y contexto dentro. Sin profiler, cambios GC o servicios de modelos concurrentes. Prerregistro en seguimiento17 antes de cada runner; timeout180s/1worker. Criterio descriptivo de beneficio: >=15/20victorias wall/CPU, cuatro bloques wall positivos y mediana mejor. No es p95 HTTP ni prueba de capacidad contractual.

| Variante | Baseline wall | Candidata wall | Cambio | Pares wall favorables |
| --- | ---: | ---: | ---: | ---: |
| Sólo50filas + contenido físico fresco |404,347ms (0,404347s)|352,524ms (0,352524s)|−51,824ms (−12,82%)|19/20|
| Fuente completa para contrato actual |411,695ms (0,411695s)|649,771ms (0,649771s)|+238,076ms (+57,83%)|0/20|

Primera tanda: CPU230,976→10,393ms,20/20pares favorables; cuatro bloques wall positivos51,918/61,198/35,698/39,812ms. Preparación1785,431ms. Segunda tanda: CPU235,511→238,620ms,9/20pares favorables; cuatro bloques wall negativos−222,650/−251,880/−267,022/−265,045ms. Preparación1760,223ms. **No comparar causalmente estas medianas con las de la tanda anterior199→21ms**, ni restarlas de los p95 históricos. Son controles emparejados nuevos y topología de datos, sin HTTP.

- Runner `20261011-185510-406302c8`:1PASS,66,361s,0errores/fallos/skips. [Datos de etapa](mod08-page-manifest-physical-20261011.json). Runner acredita fuentes sin cambios durante ejecución. Después se añadió materialize_physical al mismo módulo: auditoría posterior detecta exactamente esa modificación conocida, ninguna app modificada; no afirmar que el archivo final sea idéntico al primer ensayo.
- Runner `20261011-185923-110820be`:1PASS,73,889s,0errores/fallos/skips. [Datos del contrato completo](mod08-page-manifest-consumers-20261011.json). Auditoría independiente1357huellas exactas antes de documentación.

PASS significa que se completó el experimento y sus aserciones de datos: equivalencia de las páginas primera/intermedia/última, objetos mutables independientes y rechazo de update de contenido físico. No prueba equivalencia de todas las familias, concurrencia, autoridad ni aceptación funcional/productiva. **El gate de rendimiento de la segunda tanda es REJECT**, aunque pytest esté verde. La variante omite aún costes productivos necesarios; no se entrega como acelerador.

## Cierre

Todos los PID de runner/pytest y contenedores PG/Redis propios de ambas tandas ausentes, comprobados independientemente. No procesos de modelos ni pruebas propias pendientes. Se conserva código experimental y evidencia para evitar repetir el mismo atajo. No commit, push, publicación, contratación o datos reales. La integración directa termina descartada; cualquier siguiente ruta debe evitar materializar la fuente completa manteniendo cada comprobación fresca de negocio y justificar sus garantías antes de conectarla.
