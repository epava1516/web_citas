# N05 — inventario y prerregistro de entrega privada y sondeos

25 de octubre de2026. Alfa,5/13; N05 abierto. Producto d6580c6, sin candidato ni cambio de aplicación. Antes del estudio se verificaron las2005 fuentes del grafo N04 final, SHA9b1a3f980bfce22002afeec709c3a1cd44c7288dae4e061c7448e4b0ea643ad4; consulta graphify y contraste con fuentes primarias. Corte focal AST/semántico, no reconstrucción global.

## Inventario y reutilización

N00 asigna137 unidades a N05: cinco rutas,129plantillas y tres JavaScript propios; no137funcionalidades independientes. Codex comprueba138 fuentes directas únicas idénticas a N00/B16. La matriz por ID conserva grupos de interfaz, autoridad, responsables y límites: no se elimina la cola larga de plantillas por no medir cada una en navegador.

| Grupo | Disposición y testigo seleccionado | Límite |
| --- | --- | --- |
| R_public_photo y galería | Conservar306/307: Chromium real ES/EN,390×844/1280×800,8fotos, bytes/hashes/dimensiones y404tras pausa | Una optimización anterior, no nuevo ahorro ni LCP/capacidad |
| R_private_photo | Medir subida/previsualización/recarga/retirada y descarga autenticada móvil ES/EN | Eager explícito para procesar la foto; N03 acredita la cola real por separado |
| R_moderation_photo / R_match_image / R_photo_reuse_image | Conservar tests de autoridad, MFA/COI/recibo de lectura donde correspondan y propietarios N07/N09 | Sus fuentes sirven el mismo derivado con FileResponse/WebP; el muestreo de bytes/I/O no sustituye sus guards ni adjudica latencia aislada a cada rol |
|129plantillas | Disposición por ID y grupos: shell, cuenta/panel, comercial sintético, descubrimiento/galería, edición/moderación, exportación y derechos/operación | Reutilizar representantes de teclado/idioma/estados; no certificar WCAG ni afirmar129renderizados nuevos |
| Tres JS propios | form-errors.js, geography.js ysearch-geography.js, sin cambios | Validación/foco y dependencias geográficas con testigos previos; no sumar HTMX vendorizado a páginas que no lo cargan |
| Sondeos de exportación | Conservar seis casos móviles ES/EN de estados ysinJS; medir eventos, intervalos y parada reales | Control de estados por servicios de dominio, no prueba de worker/proveedor o generación |

La galería corregida064310 conserva3PASS:8→1peticiones iniciales y135824→11110bytes en cuatro contextos, ocho imágenes idénticas al recorrerlas. Sus cuerpos y recursos no son tiempos de respuesta. Conservar fuentes/JUnit/propiedades originales y conciliar las variantes posteriores del process/similitud mediante sus cambios delimitados y regresiones N03; siete imágenes de esa galería son fixtures ready explícitas. No repetirla sólo por frescura.

## Cuatro casos nuevos y oráculos previos

Archivo explícito tests/test_frontend_delivery_polling_diagnostic.py; dos recorridos×ES/EN, serial, PostgreSQL/Redis propios, broker de pruebas aislado, Chromium/live_server/archivos locales. Móvil390×844; escritorio sigue representado por la galería anterior. DEBUG local y fixtures sintéticas, no modo productivo.

**Entrega privada y subida:** conservar el flujo real de login, subida nativa, preview, recarga y retirada. Observer rápido de respuestas, sin sustituir HTTP, navegador, guard o bytes. Instantánea del derivado almacenado fuera de relojes mediante hilo SQL síncrono con cierre de conexiones: WebP, sinEXIF, dimensiones y hash exacto. Imagen inicial y recargada visibles e idénticas; seis GET API autenticados, primera aparte y cinco posteriores, pared incluyendo lectura del cuerpo/IPC del cliente, bytes y headers private/no-store/nosniff. Una petición condicional positiva debe seguir200con el mismo cuerpo. Anónimo sin seguir redirecciones debe ser rechazado sin imagen; tras retirada GUI, nueva petición condicional404. Original nunca se confunde con derivado; no inventar una URL pública de original como prueba de cobertura universal.

Registrar tiempos reales de subida→preview y recarga observados por el cliente con su alcance, y tiempos de recurso de navegador si están disponibles. No llamarlos latencia exclusiva de backend ni mezclarlos con N03worker. El procesamiento eager de fixture no es ejecución real de broker. Los datos del archivo/ORM se leen fuera de Playwright o con db_sync; no desactivar la protección asíncrona de Django.

**Sondeos:** helper existente prepared/enqueue/operator, con su dispatch sustituido explícitamente sólo para control de dominio. Navegador/HTTP/HTMX sin mocks y calendario nativo every3s. Capturar al menos dos sondeos queued, un sondeo running tras claim nativo y uno rejected tras finish_attempt(rejected=True), mediante llamadas de dominio síncronas separadas. Se controla la transición terminal para medir al cliente: no se acredita causa automática de revocación, trabajo de worker ni generación de una copia.

Filtrar GET HTMX de la ruta exacta de este trabajo sin almacenar su URL/ID/cookie/razón. Registrar comienzos/finales monotónicos, estadoHTTP, bytes de cuerpos, duración/intervalos y máximo de solicitudes simultáneas. Callbacks breves; leer cuerpos cuando hayan concluido para no alterar la cadencia. Tras terminal: sin hx-get, esperar al menos6500ms y comprobar cero solicitudes nuevas y ninguna en curso. Contexto separado sin JavaScript conserva estado terminal legible sin sondeo; errores e inexistencia de export/download quedan explícitos. Recursos CSS/form-errors/HTMX realmente entregados: bytes/hash y encoding observados, sin atribuir tráfico de producción comprimido.

## Relojes, recursos y ejecución

No fijar un umbral exacto3,000s como SLO frágil; informar intervalos reales, no solapamiento y parada. Primera muestra no es caché OS fría. Tiempos de navegador/API incluyen observación y cliente; no inferir p95/p99/LCP ni capacidad de Internet. RSS high-water de proceso<1GiB y timeout900s del runner son protecciones diagnósticas. Datos sintéticos, fuentes/dependencias/nativo/imágenes y recursos declarados antes de congelar.

Comando previsto: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --isolate-test-broker --timeout 900 --test tests/test_frontend_delivery_polling_diagnostic.py`.

Antes de ejecutar: revisión independiente del borrador aislado, lint, AST del instrumento y semántica de esta ficha, congelación completa. Después: cuatro casos sin FAIL/ERROR/SKIP, propiedades completas, oráculos y fuentes intactos, navegador/contextos/hilos cerrados, recursos propios retirados, Telegram terminal sent verificado. Conservar fallos originales; no reducir oráculos para conseguir PASS. Sin pruebas generales de QA ni optimización marginal.

Este lote no acepta N05 por sí solo. Falta conciliación final de137IDs, puentes con testigos y tabla de antes/después con tiempos o falta de equivalencia. Si no hay coste que justifique candidato, disponer sin cambio necesario con evidencia; no forzar índice, caché, formato o proveedor. N07/N09/N11 conservan sus obligaciones y el proyecto sigue en alfa.
