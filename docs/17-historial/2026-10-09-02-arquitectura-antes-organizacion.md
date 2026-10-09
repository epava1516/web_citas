# Arquitectura y operación

Actualizado: 2026-10-09. Estado: base técnica implementada localmente; aceptación integral, proveedores y operación de producción pendientes. El estado de entregas y runtime se consulta en [seguimiento17](17-seguimiento-desarrollo.md).

## Base acordada

El usuario acepta como base Django en monolito modular, PostgreSQL, plantillas con HTMX para interacción puntual, Celery con Redis, Pillow, almacenamiento compatible con S3, Caddy, Docker Compose, CI/CD y observabilidad. CDN según tráfico y coste. MongoDB descartado.

Las versiones y herramientas seleccionadas se registran en [ADR-001](adr/001-base-tecnica.md), `pyproject.toml`, `uv.lock` y `compose.yaml`: Django 5.2, Python 3.12 como entorno de referencia, PostgreSQL 17, Redis 7.4, Celery 5.6 y Gunicorn WSGI. La aplicación se organiza en `core`, `catalog`, `listings`, `mediafiles` y `safety`; las pantallas renderizan HTML de servidor y los recursos de interfaz se sirven localmente. Compose incluye aplicación, base, broker, worker, Beat y Caddy. Esto describe la implementación local, sin acreditar proveedores o un despliegue público.

Las evaluaciones de diseño inferiores conservan su fecha original de 2026-10-03. Sus menciones a candidatos o decisiones pendientes se subordinan al ADR, al contrato funcional y al [contrato de ejecución vigente](16-contrato-ejecucion-desarrollo.md); no reabren decisiones ya adoptadas.

## Lectura pública y estado derivado vigente

[MOD-05](16-contrato-ejecucion-desarrollo.md#17-estado-de-publicación-almacenado--mod-05) adopta `PublicationState` y `PublicationDirty` en PostgreSQL. Los triggers invalidan el estado afectado en la transacción de escritura; la versión de reglas controla su reutilización. La lectura cuenta y pagina en una instantánea `REPEATABLE READ`, evalúa nativamente candidatos desconocidos y revalida la página antes de mostrarla. La caducidad se compara en SQL. El worker recalcula y Beat programa refresco y barrido; la reparación en GET está desactivada por defecto. Procedimientos de recálculo tras cambio de código y restauración en el [README](../README.md) y [operación85](85-operacion-registro-recuperacion.md#estado-de-publicación-tras-restaurar-mod-05).

CR09-REND-LECTURA fue aceptado localmente el 2026-10-09 en `1a10ecf` e integrado en master, sin actualizar los servicios normales. Los resultados y límites del escenario sintético, incluidos PRODUCTION/`checked`, se conservan en seguimiento17. La vía `projected_publication` fue retirada; sus referencias históricas no describen la implementación vigente. La caché de Django sigue siendo `DummyCache`; el estado derivado MOD-05 tiene las garantías propias anteriores.

## Principios

- Monolito modular inicial, con módulos de cuentas, anuncios, medios, moderación y privacidad.
- HTML renderizado en servidor o generado estáticamente para contenido público indexable.
- PostgreSQL como persistencia relacional obligatoria en integración.
- Almacenamiento de objetos para fotografías; originales y documentos de verificación privados, separados de derivados públicos.
- Cola y procesos de trabajo solo cuando los trabajos de imágenes, correo o moderación lo justifiquen.
- Buscar primero con capacidades de la base de datos; introducir motor dedicado si las necesidades y mediciones lo requieren.

## Alternativas evaluadas antes de adoptar la base — histórico

| Alternativa | Ventaja esperada | Coste a evaluar |
| --- | --- | --- |
| Django con plantillas y mejora progresiva | Gestión, permisos y administración integrados; menos servicios | Necesidades de interacción y experiencia del equipo |
| Framework TypeScript con renderizado en servidor | Interfaz interactiva y lenguaje compartido | Autenticación, administración, dependencias y operación |
| Frontend y API separados | Clientes o ciclos de despliegue independientes | Más contratos, autenticación y servicios |

No seleccionar versiones ni dependencias hasta comprobar mantenimiento, soporte, licencias, documentación oficial y compatibilidad. Usar versiones soportadas, archivos de bloqueo y proceso de actualización.

## Docker y despliegue

Docker Compose se utiliza en desarrollo local. Un despliegue externo sigue sujeto a los gates y autorizaciones del contrato; no se deduce de disponer de Compose. No introducir Kubernetes sin una necesidad demostrada.

- Imagen reproducible, construcción por etapas cuando proceda y usuario sin privilegios.
- Secretos inyectados en ejecución; nunca incluidos en repositorio o imagen.
- Base de datos sin exposición pública y datos persistentes fuera del ciclo de vida de contenedores.
- HTTPS, comprobaciones de salud y configuración por entorno.
- Entorno de pruebas separado, con datos sintéticos y protección frente a indexación.
- Automatización de comprobaciones, construcción y despliegue; migraciones ejecutadas de forma controlada.
- Reversión de aplicación compatible con el esquema: retroceder una imagen no revierte necesariamente datos o migraciones.
- Copias cifradas, restauraciones probadas, alertas y registros sin datos sensibles innecesarios.
- Definir objetivos de recuperación, pérdida de datos tolerable y disponibilidad antes de contratar infraestructura.

## Proveedores

Evaluar alojamiento, almacenamiento, CDN, correo, verificación y posibles pagos por compatibilidad explícita con la actividad y contenido, contratos de tratamiento, subencargados, transferencias internacionales, costes y reversibilidad. La ubicación europea por sí sola no demuestra cumplimiento.

No hay proveedores contratados ni presupuesto confirmado.

## Evaluación de Django: renderizado y crecimiento

Evaluación histórica del 2026-10-03, previa a la adopción de Django y las versiones del ADR-001. Se conserva el razonamiento de diseño y crecimiento; la base implementada se describe arriba.

Django genera HTML en servidor; la complejidad visual depende del HTML, CSS y JavaScript desarrollado. El renderizado en servidor facilita entregar contenido público sin depender de ejecutar JavaScript para mostrarlo, pero no garantiza posicionamiento ni buen rendimiento por sí solo.

La capacidad depende del trabajo por petición, consultas, caché, infraestructura y distribución del tráfico. No asignar una cifra de visitas soportadas sin pruebas representativas. Medir peticiones por segundo, concurrencia, percentiles de latencia, errores, consultas y uso de recursos; incluir picos y tráfico automatizado.

### Diseño para crecer

- Servir fotografías y estáticos desde almacenamiento/CDN compatible con el sector, sin pasar cada descarga por Django.
- Mantener las instancias de aplicación sin archivos o sesiones que dependan de un servidor concreto; usar persistencia y sesiones compartidas al replicar.
- Diseñar índices y paginación; evitar consultas repetidas por anuncio (N+1) mediante cargas relacionadas apropiadas.
- Cachear únicamente contenido público apto; aislar respuestas privadas y personalizadas. Invalidar cachés al retirar o modificar contenido, con límites de caducidad y procedimiento de purga.
- Procesar imágenes, correo y tareas costosas fuera de la petición web, con trabajos reintentables y límites de recursos.
- Replicar la aplicación detrás de un balanceador cuando las mediciones lo justifiquen. La base de datos compartida también necesita capacidad y límites de conexiones: añadir contenedores no elimina ese cuello de botella.
- Introducir búsqueda dedicada, réplicas de lectura o servicios separados solo cuando exista necesidad medida; considerar consistencia y retirada de contenido.

### Evolución propuesta

1. Lanzamiento: aplicación modular, base de datos, almacenamiento separado y procesos de trabajo; medir y probar carga representativa.
2. Crecimiento: optimizar consultas y caché; ampliar recursos donde se observe saturación.
3. Mayor demanda o disponibilidad: varias instancias, balanceador y servicios compartidos; revisar capacidad de base de datos y recuperación.
4. Necesidades específicas: extraer búsqueda o procesamiento de medios si aporta una mejora demostrada.

WSGI es una opción inicial para páginas HTTP convencionales. Django también admite ASGI; elegirlo según necesidades de concurrencia de E/S o tiempo real y compatibilidad del código. ASGI no convierte automáticamente un proyecto síncrono en más rápido ni reduce el coste CPU del procesamiento de imágenes.

Antes de dimensionar producción, definir volumen de anuncios y fotos, mezcla de páginas, búsquedas, escrituras, tráfico esperado y pico, presupuesto, latencia objetivo y disponibilidad. Hay benchmarks locales sintéticos, con fuentes y escenarios registrados en seguimiento17; no garantizan capacidad de producción.

Fuentes oficiales consultadas:

- [Rendimiento y optimización](https://docs.djangoproject.com/en/5.2/topics/performance/).
- [Despliegue WSGI y ASGI](https://docs.djangoproject.com/en/6.0/howto/deployment/).
- [Comprobaciones de producción](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/).

Las versiones de estas referencias no constituyen una selección de versión para el proyecto.

## Persistencia, caché y cola de tareas

Evaluación histórica del 2026-10-03. La selección vigente de PostgreSQL y Celery/Redis figura en la base acordada y el ADR; esta tabla conserva los candidatos previos.

| Componente | Recomendación | Responsabilidad |
| --- | --- | --- |
| PostgreSQL | Base de datos principal propuesta | Cuentas, anuncios, tarifas, contactos, permisos, moderación y evidencias mínimas de verificación |
| Redis | Opcional para el framework; candidato si necesitamos caché compartida o como broker de la cola elegida | Datos temporales y coordinación; no fuente única de decisiones o datos de negocio |
| MongoDB | Descartado por el usuario el 2026-10-03 | No incorporarlo al proyecto |
| Almacenamiento de objetos | Propuesto para archivos | Fotos y documentos privados separados; en PostgreSQL guardar referencias y metadatos |

El modelo confirmado contiene relaciones e invariantes: propietario de anuncio, fotos asociadas, tarifas, permisos y estados de publicación. PostgreSQL permite mantenerlos juntos. Usar tablas y restricciones para el núcleo; JSONB solo para atributos variables justificados, con validación y estrategia de consulta. PostgreSQL dispone de búsqueda de texto completo e índices; evaluar su suficiencia antes de introducir otro motor.

Redis no es requisito de Django. La elección del sistema de tareas determinará si necesitamos Redis u otro broker. Para el producto, procesar fotografías en segundo plano es recomendable desde el lanzamiento; aún no hay implementación elegida.

Si Redis mantiene caché, sus entradas deben ser prescindibles y tener TTL e invalidación; las decisiones de publicación y autorizaciones permanecen en PostgreSQL. Si actúa como broker, definir persistencia, reintentos, recuperación, trabajos idempotentes y envío posterior al commit de la transacción. No asumir durabilidad equivalente a la base de datos. Evitar que la expulsión de claves de caché elimine trabajos: separar servicios de caché y broker cuando compartan infraestructura; bases lógicas de Redis no aíslan memoria ni políticas de expulsión.

Sesiones: comenzar con persistencia en base de datos; evaluar backend con caché y persistencia si hay necesidad. Límites de abuso compartidos pueden usar Redis, pero deben definir comportamiento ante su caída y no ser la única barrera de seguridad.

Mantener PostgreSQL y Redis fuera de acceso público, con credenciales restringidas, redes controladas y cifrado cuando corresponda al despliegue. Incluir retención y eliminación también en cachés y resultados de tareas. No introducir contenido sensible completo en mensajes de trabajo si basta un identificador.

MongoDB admite modelos con documentos embebidos o referencias. Para este dominio, añadirlo junto a PostgreSQL aumentaría la operación, los respaldos, la sincronización y el trabajo de borrado sin una ventaja concreta demostrada. Esta conclusión es una valoración del proyecto, no una limitación general de MongoDB.

Fuentes oficiales:

- [Búsqueda de texto en PostgreSQL](https://www.postgresql.org/docs/current/textsearch.html).
- [Tipos JSON e índices JSONB](https://www.postgresql.org/docs/16/datatype-json.html).
- [Caché de Django y backend Redis](https://docs.djangoproject.com/en/6.0/topics/cache/).
- [Modelado de documentos en MongoDB](https://www.mongodb.com/docs/manual/data-modeling/).

## Stack complementario recomendado

Evaluación histórica del 2026-10-03. Las herramientas de aplicación y calidad ya seleccionadas figuran en ADR-001 y el lock; CDN, correo y demás proveedores conservan sus dependencias externas. MongoDB está descartado expresamente.

| Capa | Candidato | Función y criterio |
| --- | --- | --- |
| Interfaz | Plantillas Django, CSS y HTMX donde aporte valor | HTML inicial completo y actualizaciones mediante fragmentos; navegación y formularios básicos deben funcionar sin JavaScript |
| Servidor de aplicación | Gunicorn con WSGI | Candidato para HTTP convencional; verificar soporte y dimensionar workers con carga real |
| Entrada HTTPS | Caddy | Proxy y gestión automática de certificados; configurar límites y confianza en cabeceras de proxy |
| Trabajos | Celery con Redis como broker | Fotos, correo y trabajos reintentables; confirmar compatibilidad de versiones y definir recuperación |
| Procesamiento de imágenes | Pillow | Derivados optimizados, límites de píxeles y memoria, recodificación sin metadatos; no sustituye moderación |
| Archivos | Almacenamiento de objetos compatible con S3 | Separar medios públicos y privados; proveedor pendiente de evaluación |
| Distribución | CDN para imágenes y estáticos | Incorporar según tráfico/coste; compatibilidad contractual, purga y privacidad obligatorias |
| Correo | Servicio transaccional | Verificación y recuperación; configurar SPF, DKIM y DMARC y comprobar compatibilidad con actividad |
| Operación | Docker Compose y CI/CD | Entornos reproducibles, pruebas, construcción y despliegue controlado |
| Visibilidad operativa | Logs estructurados, métricas y alertas | Errores, latencias, saturación, cola y disponibilidad; limitar datos personales y elegir proveedor compatible |

HTMX y recursos de interfaz se servirán desde el propio proyecto para evitar peticiones de terceros innecesarias. Mantener URLs públicas indexables y respuestas completas al navegar directamente; los fragmentos no deben originar duplicados indexables.

Celery puede usar Redis como broker y backend de resultados. No habilitar almacenamiento de resultados sin necesidad; el estado de negocio permanece en PostgreSQL. Definir tareas idempotentes, plazos, reintentos, recuperación y trabajos fallidos antes del lanzamiento. Separar caché y broker si se introduce caché Redis, como se detalla arriba.

Pillow es candidato inicial; evaluar procesamiento alternativo solo si CPU, memoria o volumen lo justifican. Optimizar dimensiones, formatos y entrega suele aportar más que añadir servicios sin medir.

Herramientas de calidad propuestas: linter/formateador, pruebas de permisos y flujos críticos, pruebas de navegador y carga representativa. Las herramientas concretas y sus versiones siguen pendientes.

No introducir inicialmente Kubernetes, microservicios, un motor de búsqueda separado ni una SPA completa. Evaluar PgBouncer, PostGIS o búsqueda dedicada cuando haya saturación de conexiones, consultas geográficas reales o limitaciones medibles respectivamente.

Fuentes oficiales consultadas:

- [HTMX: respuestas HTML y uso](https://htmx.org/docs/).
- [Caddy: HTTPS automático](https://caddyserver.com/docs/automatic-https).
- [Celery: brokers y almacenamiento de resultados](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/).
- [Pillow: formatos de imágenes](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).

Ninguna de estas propuestas garantiza por sí sola rendimiento, seguridad o cumplimiento; validarlos sobre la implementación y el despliegue concretos.


## Caché de aplicación explícita

Decisión2026-10-06: CACHES.default usa DummyCache de Django, sin almacenamiento. No hay usos de API de caché Django en apps/config/templates/scripts revisados; no se conserva LocMemCache implícita sin política de invalidación/retención. Redis mantiene broker/tareas y persistencia existentes. Esta decisión no impide optimizar consultas, índices, imágenes o estáticos. Una futura caché de datos/respuestas deberá definir clave por autoridad/idioma/versión, exclusiones de contenido privado, TTL e invalidación por retirada/cambio de gestor/consentimiento/derechos, y verificarlo antes de activarse. Las cachés del navegador, proxies externos, backups y copia histórica del host se contabilizan por separado. [Runtime](evidencias/cache-aplicacion-runtime0110.json).
