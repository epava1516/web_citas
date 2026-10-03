# Arquitectura y operación

Actualizado: 2026-10-03. Estado: base tecnológica aceptada; versiones, proveedores, dimensionamiento y detalles operativos pendientes.

## Base acordada

El usuario acepta como base Django en monolito modular, PostgreSQL, plantillas con HTMX para interacción puntual, Celery con Redis, Pillow, almacenamiento compatible con S3, Caddy, Docker Compose, CI/CD y observabilidad. CDN según tráfico y coste. MongoDB descartado.

Esta aceptación sustituye el estado de propuesta de esos componentes en las evaluaciones históricas que siguen. No aprueba automáticamente Gunicorn, proveedores o herramientas no concretadas. Las alternativas se conservan como contexto de la evaluación. Seguimos en planificación, sin implementación autorizada en esta fase.

## Principios

- Monolito modular inicial, con módulos de cuentas, anuncios, medios, moderación y privacidad.
- HTML renderizado en servidor o generado estáticamente para contenido público indexable.
- PostgreSQL como candidata para persistencia relacional.
- Almacenamiento de objetos para fotografías; originales y documentos de verificación privados, separados de derivados públicos.
- Cola y procesos de trabajo solo cuando los trabajos de imágenes, correo o moderación lo justifiquen.
- Buscar primero con capacidades de la base de datos; introducir motor dedicado si las necesidades y mediciones lo requieren.

## Alternativas por evaluar

| Alternativa | Ventaja esperada | Coste a evaluar |
| --- | --- | --- |
| Django con plantillas y mejora progresiva | Gestión, permisos y administración integrados; menos servicios | Necesidades de interacción y experiencia del equipo |
| Framework TypeScript con renderizado en servidor | Interfaz interactiva y lenguaje compartido | Autenticación, administración, dependencias y operación |
| Frontend y API separados | Clientes o ciclos de despliegue independientes | Más contratos, autenticación y servicios |

No seleccionar versiones ni dependencias hasta comprobar mantenimiento, soporte, licencias, documentación oficial y compatibilidad. Usar versiones soportadas, archivos de bloqueo y proceso de actualización.

## Docker y despliegue

Propuesta: Docker Compose para desarrollo y posible despliegue inicial en un servidor si el volumen y la disponibilidad requerida lo permiten. No introducir Kubernetes sin una necesidad demostrada.

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

Evaluación del 2026-10-03. Recomendación actual: Django con plantillas y mejora progresiva es una opción adecuada para el directorio. Sigue siendo propuesta, no una selección aprobada.

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

Antes de dimensionar, definir volumen de anuncios y fotos, mezcla de páginas, búsquedas, escrituras, tráfico esperado y pico, presupuesto, latencia objetivo y disponibilidad. No hay benchmark realizado ni capacidad garantizada.

Fuentes oficiales consultadas:

- [Rendimiento y optimización](https://docs.djangoproject.com/en/5.2/topics/performance/).
- [Despliegue WSGI y ASGI](https://docs.djangoproject.com/en/6.0/howto/deployment/).
- [Comprobaciones de producción](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/).

Las versiones de estas referencias no constituyen una selección de versión para el proyecto.

## Persistencia, caché y cola de tareas

Evaluación del 2026-10-03. Estado: recomendaciones pendientes de acuerdo.

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

Actualizado: 2026-10-03. Propuestas pendientes de selección de versiones, compatibilidad y aprobación. MongoDB sí está descartado expresamente.

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
