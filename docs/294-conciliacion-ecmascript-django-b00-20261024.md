# B00-335 — ECMAScript, Django y límites del contenido capturado

Fecha: 2026-10-24. Conciliación documental y contraste estático acotado.

B00-335: 286 de 295 fuentes únicas conciliadas; quedan nueve capturas históricas del grafo. Completada la disposición de las referencias ECMAScript y Django Settings, distinguiendo navegación, cuerpos preservados y configuración local. Sin cambios de aplicación o pruebas, defecto funcional nuevo demostrado ni nueva aceptación. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Procedencia y aceptación de disposición

Ocho lectores nativos nuevos de sólo lectura cubrieron 775.218 caracteres en ocho partes, máximo tres simultáneos. Setenta intervalos contiguos de hasta 12.000 caracteres Unicode por salida; sin truncamientos de lectura declarados. Los informes guardados son extractos seleccionados del principal, no transcripciones completas. Cero nuevas invocaciones Claude V1; se conservan las ocho históricas y su consumo, sin estimación nativa.

| Captura | Fuente | Caracteres | Particiones |
| --- | --- | ---: | --- |
| ecma | `source:880n6t0z0p8qe00fj7lm` | 585080 | [0,97513), [97513,195026), [195026,292540), [292540,390053), [390053,487566), [487566,585080) |
| django | `source:k77lawoioaqsfjlcytts` | 190138 | [0,95069), [95069,190138) |

SHA256 completos comprobados:

- `source:880n6t0z0p8qe00fj7lm`: `05c765e5376ad2dec3496c1eb986c9ae1a26bd17ff3e8a8af195681a286a33c3`.
- `source:k77lawoioaqsfjlcytts`: `eb2d95dc8429fc504f667da15c2e192472497286c95962c40d37ddadc80a04b1`.

El principal cotejó ocho huellas de parte y dieciséis citas con sus contextos/fronteras. El verificador realiza dieciocho cotejos sobre esos dieciséis intervalos, verifica ambas uniones completas y revalida integridad de las 295 capturas. Cinco lectores informaron cwd antiguo, pero usaron la ruta absoluta designada; huellas y citas coinciden con ese original. No se acredita lectura adicional por imports, bibliografías o navegación.

Un informe de Django incluía una errata en la huella citada en su prosa libre y remitía él mismo al campo estructurado corregido; ese campo original coincide con la fuente y fue el utilizado para aceptar la procedencia. Algunos lectores aportaron tres citas: el extracto conserva dos y declara que no es el informe íntegro. Se preservan estas notas, sin inventar una reparación de lectura o alterar campos de parte. El primer borrador de contraste del principal confundió comillas dobles/simples de un literal; se detuvo antes de guardar contraste/ledger y se corrigió contra el archivo real, sin repetir producto.

El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) avanza de 284 a 286 disposiciones y de once a nueve pendientes. Base284 fijada por SHA256, escritura atómica y permisos conservados. Las partes no son fuentes nuevas; el verificador no sobrescribe otro corte. Artefactos `artifacts/beta-promotion-fix-20261020/b00-335-*`. La disposición completa del texto capturado no acredita un estándar completo o una integración funcional.

## ECMAScript: índice frente a cuerpos

La captura titulada ECMAScript2027 no contiene todo el estándar. Los primeros 328.853 caracteres conservan índice e interfaz; después comienza la página de cláusula25 Structured Data, que ocupa 256.227 caracteres restantes con cuerpos, enlaces, notas y pie. Se verificó directamente la transición y la URL final structured-data.html. El título no acredita ratificación, madurez de edición o soporte de motores.

Las primeras tres partes y la cola inicial de la cuarta enumeran asuntos de casi todo el estándar: tipos, conversiones, gramática, expresiones, módulos, builtins, iteradores, recursos, agentes y anexos. Esos títulos no aportan sus algoritmos. Por ejemplo, RegExp.escape e Iterator.zip son destinos de navegación; no se infieren sus reglas, disponibilidad o requisitos de producto. La lectura de la captura no incorpora las páginas enlazadas ni las reglas del modelo de memoria que sólo se citan.

Los cuerpos preservados sí cubren ArrayBuffer fijo/redimensionable, SharedArrayBuffer fijo/creciente, DataView, operaciones Atomics y JSON. Se conserva la diferencia entre algoritmos y notas/recomendaciones: límites del host, reservas sugeridas, pruebas en el entorno de destino y hints de CPU no son umbrales contractuales del servidor. Las validaciones posteriores a coerción/species y los estados detached ilustran efectos observables en esos algoritmos; no se trasladan automáticamente a autorización del backend.

La página JSON conserva parse, reviver y contexto, rawJSON, stringify/replacer, registros auxiliares, tratamiento de números no finitos, BigInt, ciclos, arrays, propiedades y escapes. Eso no establece soporte actual de rawJSON, precisión para los datos del proyecto o equivalencia con su serialización Python. ECMA-404 y otras definiciones referenciadas siguen fuera de lectura. El final cierra la página Structured Data y su navegación, no el estándar completo.

## JavaScript actual y autoridad del servidor

Los auxiliares seleccionados de [geografía](../static/geography.js), [búsqueda](../static/search-geography.js) y [errores](../static/form-errors.js) operan sobre controles DOM, opciones/clones y foco. API DOM y comportamiento del navegador no quedan acreditados por el índice de una especificación de lenguaje. No se añadieron APIs de buffers, atomics o JSON ni se sustituyó código vendorizado a partir de esa lectura.

Las [reglas de formulario del servidor](../apps/listings/forms.py) validan relaciones entre región, provincia, municipio, CP y zona frente al catálogo. El filtrado de opciones del navegador no sustituye esa validación. Las pruebas seleccionadas describen recarga, conservación de URL, limpieza de descendientes y teclado en ES/EN; su presencia es una aserción estática, no un nuevo resultado Playwright o conformidad general.

## Django Settings: referencia frente a configuración

La captura identifica Django5.2 y conserva cuerpos de settings de núcleo, autenticación, mensajes, sesiones y estáticos. Incluye un ajuste introducido explícitamente en5.2.15; un selector con otras versiones no cambia la edición y la serie no basta para suponer compatibilidad de todos los patches. Los ejemplos de SQLite/MySQL/Oracle no modifican la obligación PostgreSQL de integración.

A partir de150.694 comienza Core Settings Topical Index y desde164.782 la navegación/patrocinio/Contents del sitio. Estos listados no acreditan cuerpos de otras entradas. Se conservaron las fronteras que dividen SECRET_KEY, los requisitos de middleware/backend/proxy y la distinción entre valores por defecto del framework y valores efectivos. No se importó settings, consultó un entorno real o abrió un archivo de secretos.

El [settings actual](../config/settings.py) declara PostgreSQL, control de DEBUG condicionado al entorno, flags de sesión y límites de memoria. La [capa de middleware](../apps/core/middleware.py) añade políticas y respuestas privadas sin caché. La declaración estática no demuestra un despliegue seguro, proxy correctamente configurado, consentimiento o cumplimiento jurídico. El ejemplo de producción exige valores de operador y un conjunto explícito de IPs privadas de Caddy; no se cargó ni desplegó.

FILE_UPLOAD_MAX_MEMORY_SIZE decide cuándo el upload deja la memoria; no es por sí solo un rechazo del tamaño máximo del archivo. El [lector de medios actual](../apps/mediafiles/services.py) aplica su límite de diez MiB y una lectura acotada de comprobación, además de validar contenido. DATA_UPLOAD_MAX_MEMORY_SIZE tiene un alcance distinto sobre cuerpo/formulario. Esas capas no se equiparan ni se reconfiguran por una recomendación genérica.

Las flags HttpOnly, SameSite o Secure no equivalen a consentimiento ni implementan las preferencias privadas de B15. La dirección de cookies para visitantes y almacenamiento privado cifrado con cuenta permanece en [contrato14](14-contrato-funcional-v1.md); formato, claves, retención y habilitación siguen pendientes. Cifrado o firma no acreditan por sí solos RGPD.

La documentación de conexiones persistentes y health checks no significa que cambiar credenciales cierre sesiones ya abiertas. El test seleccionado de rotación trata conexiones PostgreSQL propias y no sesiones web; el test de hilo ORM temporal exige su cierre incluso con conexión persistente saludable. Se leyeron sus aserciones, sin ejecutar contenedores o SQL en este corte. Análogamente, el test de configuración SMTP demuestra como objetivo no conectar ni enviar: importar/configurar un backend no acredita entrega real. Ninguno de esos textos amplía las aceptaciones previas.

## Contraste, grafo y continuación

Catorce archivos actuales y treinta literales seleccionados: settings, tres auxiliares JS, reglas de formulario, medios, middleware, ejemplo de producción, dependencias y tests de correo/conexiones/navegador/teclado. No es una auditoría completa de esos subsistemas. No se ha demostrado un defecto funcional nuevo; sin cambios de aplicación/pruebas o nueva ejecución funcional. Los proveedores y despliegue mantienen sus gates propios; no se repiten baterías por esta lectura.

Grafo388 revalidado antes del análisis e integración semántica dirigida389 de esta conciliación. Se incorporan conceptos de alcance y citas directas al código seleccionado. Sin nuevo AST global, semántica exhaustiva o HTML global; los límites de self-loops, referencias externas e inferencias se conservan.

Quedan 9 fuentes y 17,953,140 caracteres, todas capturas históricas de Graphify: informe, dos partes de nodos y seis de relaciones. Conteos no son porcentaje de esfuerzo y B00 no se cierra por completar las referencias técnicas. Nueve de18puntos beta cerrados; B15 opcional. Sin publicación, contratación, gasto o datos reales. Corte previo: [conciliación293](293-conciliacion-css-ci-backend-b00-20261024.md).
