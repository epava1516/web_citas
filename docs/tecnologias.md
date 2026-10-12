# Tecnologías utilizadas

Fecha de corte: 2026-10-11. Repositorio `web_citas`, HEAD `7e04016d8ece6cf52388e283eb06cf0a6040fd2b`. Inventario contrastado con `pyproject.toml`, `uv.lock`, `Dockerfile`, `compose.yaml`, configuración y código. Las versiones de paquetes son las resueltas en el lockfile, no una comprobación de los procesos activos. El estado de aceptación se consulta en [seguimiento](17-seguimiento-desarrollo.md); el diseño en [arquitectura](02-arquitectura.md).

## Aplicación y lenguajes

Monolito modular **Django**, con módulos `core`, `catalog`, `listings`, `mediafiles` y `safety`. **Python >=3.12,<3.14** es el rango declarado; la imagen usa **Python 3.12-slim**. **HTML**, plantillas Django, **CSS** y **JavaScript** implementan la interfaz renderizada en servidor. **HTMX 2.0.11** está incluido localmente en `static/vendor/`, y se utiliza para interacción puntual, incluida la pantalla de trabajos de portabilidad. **SQL/PostgreSQL** implementa consultas, restricciones y triggers. **Cython 3.0.12** y un compilador C construyen el kernel canónico nativo en un entorno aislado; Cython no es dependencia del runtime ni se compila al importar la aplicación.

## Servicios e infraestructura

| Tecnología | Versión o selección local | Función |
| --- | --- | --- |
| PostgreSQL | `17-alpine` | Persistencia principal, transacciones, triggers y estado derivado `PublicationState`/`PublicationDirty`. Obligatorio en integración. |
| Redis servidor | `7.4-alpine`, AOF habilitado | Broker Celery y persistencia de la cola. Los estados de negocio permanecen en PostgreSQL. |
| Celery Worker / Beat | Paquete fijado en tabla inferior | Ejecución y planificación de trabajos, reconciliación y purgas. |
| Gunicorn | Paquete fijado en tabla inferior | Expone WSGI; imagen configurada con dos workers y timeout de 45 segundos. |
| Caddy | `2-alpine` | Proxy inverso, archivos estáticos y entrega privada con `forward_auth` hacia Django. |
| RustFS | Imagen fijada por digest en `compose.yaml` | Servicio local compatible con S3, perfil opcional `rights-objects`, para objetos de derechos. |
| Docker / Compose | Sin versión del ejecutable fijada aquí | Construcción de imágenes, servicios, redes y volúmenes locales. |
| uv | `0.11.6` en Dockerfile | Instalación reproducible con `uv sync --frozen --no-dev`; `uv.lock` fija paquetes. |

Las etiquetas de imágenes no fijan una versión patch inmutable; RustFS sí está fijado por digest. S3 es el protocolo de almacenamiento: usar boto3 no acredita contratación ni uso de AWS. Medios privados, estáticos y entregas tienen volúmenes separados. `DummyCache` es el backend Django actual, sin almacenamiento de respuestas; las sesiones se guardan en base de datos. Redis no es la autoridad de permisos ni una caché de respuestas activada.

## Bibliotecas del runtime

| Paquete | Versión en `uv.lock` | Uso |
| --- | --- | --- |
| `django` | 5.2.17 | Backend, ORM, migraciones, formularios, sesiones y plantillas SSR. |
| `psycopg` | 3.3.6 | Conexión de Django y herramientas SQL a PostgreSQL; extra binary. |
| `celery` | 5.6.3 | Tareas asíncronas y planificación periódica mediante worker y Beat. |
| `redis` | 6.4.0 | Cliente Python del broker; distinto del servidor Redis 7.4. |
| `gunicorn` | 23.0.0 | Servidor WSGI de la aplicación. |
| `pillow` | 12.3.0 | Validación, transformación y derivados de imágenes. |
| `imagehash` | 4.3.2 | Huellas perceptuales de imágenes para coincidencias. |
| `opencv-python-headless` | 4.14.0.94 | Comparación visual sin interfaz gráfica; no identificación biométrica. |
| `numpy` | 2.5.3 | Operaciones numéricas utilizadas por procesamiento visual y dependencias. |
| `scipy` | 1.18.1 | Soporte científico de las dependencias de procesamiento visual. |
| `django-storages` | 1.14.6 | Backend de almacenamiento compatible con S3. |
| `boto3` | 1.43.108 | Cliente S3 usado por almacenamiento y objetos privados. |
| `botocore` | 1.43.108 | Protocolos y transporte del cliente S3, dependencia de boto3. |
| `argon2-cffi` | 25.1.0 | Hash de contraseñas con Argon2. |
| `pyotp` | 2.10.0 | Códigos TOTP para autenticación multifactor. |
| `cryptography` | 50.0.2 | Cifrado autenticado AES-GCM de objetos y compatibilidad Fernet. |
| `orjson` | 3.13.0 | Serialización JSON canónica con validación previa de tipos. |
| `blake3` | 1.0.11 | Referencias de contenido versionadas; SHA-256 continúa en verificaciones físicas. |

## Integridad, cifrado y aceleración

El almacenamiento de objetos usa **AES-GCM** y claves de datos de 256 bits; conserva lectura de registros legacy **Fernet**. **SHA-256**, **HMAC**, aleatoriedad del sistema y comparaciones seguras se usan en huellas, sellos y controles de integridad. BLAKE3 sirve para referencias canónicas versionadas y no elimina las verificaciones SHA-256 de contenido.

El kernel Cython tiene fallback Python y un manifiesto que vincula fuente, compilador, ABI y binario. Su loader utiliza primitivas Linux de `memfd` y sellado para cargar el artefacto verificado. Esta optimización local no acredita por sí sola cumplimiento de objetivos de latencia; MOD-08 continúa pausado con objetivos completos pendientes.

## Pruebas y calidad

| Herramienta | Versión en `uv.lock` | Función |
| --- | --- | --- |
| `pytest` | 9.1.1 | Pruebas funcionales, integración y contratos. |
| `pytest-django` | 4.14.0 | Integración de pytest con Django y sus bases de prueba. |
| `pytest-xdist` | 3.8.0 | Ejecución paralela de pruebas cuando el runner la configura. |
| `playwright` | 1.63.0 | Pruebas de navegador real con Chromium. |
| `ruff` | 0.16.10 | Análisis estático y formato Python. |
| `pip-audit` | 2.10.1 | Auditoría de vulnerabilidades de dependencias. |

El workflow de **GitHub Actions** está definido con `workflow_dispatch`: su existencia no prueba ejecución externa ni CI aceptado. Configura PostgreSQL 17, Redis 7.4, Chromium y construcción aislada de **librdb/rdb-cli** para verificación de formatos Redis. Las herramientas nativas de prueba conservan un manifiesto; no son servicios de la aplicación.

## Herramientas de desarrollo y documentación

**Git/GitHub** mantienen código e historial. **Graphify 0.9.64**, instalado en este equipo fuera de las dependencias de aplicación, genera un grafo AST local; el procedimiento exige `--code-only` y agrupamiento `--no-label`. Su grafo ayuda a navegar dependencias y no sustituye pruebas.

**Codex y Claude** son herramientas de trabajo de ingeniería sujetas a las instrucciones del proyecto, no dependencias de producción. **Gemini Notebook**, mediante **notebooklm-mcp-cli 0.15.4** (`nlm` y servidor MCP), contiene el cuaderno de arquitectura creado por petición del usuario. Tampoco es una dependencia de la web; sus fuentes son instantáneas sin sincronización automática.

Documentación externa: [URLs oficiales de configuración, diagnóstico y operación](urls-oficiales-tecnologias.md).

## Fuentes para actualizar este inventario

- [Dependencias declaradas](../pyproject.toml) y [versiones resueltas](../uv.lock).
- [Imagen de aplicación](../Dockerfile), [servicios](../compose.yaml) y [proxy](../Caddyfile).
- [Configuración Django](../config/settings.py) y [workflow de calidad](../.github/workflows/ci.yml).
- [HTMX local](../static/vendor/HTMX-README.md), [JSON canónico](../apps/safety/fast_canonical.py), [codec cifrado](../apps/safety/object_storage/codec.py) y [builder nativo](../scripts/build_canonical_kernel.py).
- [Procedimiento Graphify](19-graphify-analisis-local.md) y [seguimiento de aceptación](17-seguimiento-desarrollo.md).
