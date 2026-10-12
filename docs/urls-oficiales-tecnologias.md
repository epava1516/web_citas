# Documentación oficial de tecnologías: configuración, diagnóstico y operación

Comprobado el 2026-10-11 para `web_citas` (HEAD `7e04016`). Complementa [el inventario de tecnologías](tecnologias.md). Se han comprobado **176 enlaces oficiales** de **43 áreas tecnológicas**, siguiendo redirecciones y registrando el título servido. La verificación acredita acceso HTTP en este corte, no compatibilidad completa de cada instrucción con el runtime ni disponibilidad futura.

## Cómo elegir la documentación

Las versiones de las bibliotecas proceden de `uv.lock`; las imágenes y parámetros de `Dockerfile`/`compose.yaml`. Python de aplicación es 3.12 en la imagen (rango >=3.12,<3.14), aunque el Python del equipo es 3.14.7. uv de Docker es 0.11.6, distinto de uv 0.12.23 del equipo. Docker29.8.2, Compose5.6.0 y Git2.53.0 corresponden al equipo, no son versiones fijadas por el repositorio.

Priorizar documentación del patch exacto, después su serie y, si no existe archivo accesible, consultar el código/documentación del tag exacto junto con la guía oficial actual. `stable`, `latest`, `main` y sitios sin selector son dinámicos. Un HTTP200 no demuestra que la versión solicitada sea la servida: se conserva el título real y se señalan redirecciones.

Casos detectados: la URL Celery `v5.6.3` sirve páginas tituladas 5.6.2; la URL boto3 `1.43.108` redirige a documentación `latest` cuyo título observado es1.43.111. Se incluyen los tags exactos oficiales para contrastar. Las URLs HTML de Gunicorn23.0.0 no están disponibles y se sustituyen por documentación fuente del tag23.0.0. Pillow12.3.0, SciPy1.18.1 y pytest9.1.1 utilizan fallback oficial cuando la ruta exacta no está disponible; se aporta además fuente fijada por tag. Las guías de Redis son actuales: comprobar opciones contra7.4, no asumir capacidades de versiones superiores.

RustFS está fijado por digest, sin versión semántica acreditada en este inventario. Caddy2 y PostgreSQL17/Redis7.4 son series de imagen, no un patch fijado por digest. El paquete `redis` Python6.4.0 es distinto del servidorRedis7.4. La documentación S3 explica el protocolo compatible; no acredita contratación de AWS.

Este archivo es un **catálogo de URLs y criterios de versión**. Su carga en Gemini Notebook no importa automáticamente el contenido completo de los sitios enlazados. Las fuentes del código local y su seguimiento siguen determinando qué está implementado y aceptado. No se han cambiado dependencias, servicios ni objetivos MOD-08.

## Rutas de consulta por problema

| Problema | Referencias útiles de este catálogo |
| --- | --- |
| Arranque, dependencias o versión Python incompatible | Python/venv, uv troubleshooting/lock, Docker builds, psycopg instalación, Pillow dependencias. |
| Errores SQL, bloqueos, timeouts o consulta lenta | PostgreSQL EXPLAIN/actividad/bloqueos/logs, psycopg transacciones/errores, Django optimización. |
| Migraciones y estado derivado de publicación | Django migraciones, PostgreSQL triggers/transacciones; contrastar reglas MOD-05 locales. |
| Worker desconectado, tarea atascada o Beat duplicado | Celery configuración/Redis/workers/Beat/monitorización; Redis persistencia/latencia. |
| 502, timeout WSGI o descarga privada | Gunicorn settings/FAQ, Caddy reverse_proxy/forward_auth/logging, Docker logs. |
| S3, autenticación de objetos o retries | django-storages S3, boto3 configuración/credenciales/retries/errores, RustFS estado. |
| Corrupción, AEAD o integridad | cryptography AES-GCM/Fernet, Python hashlib, fuentes de orjson/BLAKE3; preservar contexto y verificación local. |
| Imagen inválida o diferencias de coincidencia | Pillow formatos/Image, OpenCV imgproc, ImageHash, NumPy ABI, SciPy. |
| Fallo nativo o ABI de kernel | Cython compilación/debugging, GCC, Python imagen y manifiesto local de kernel. |
| Prueba intermitente, proceso colgado o navegador ausente | pytest fallos/fixtures, pytest-django bases, xdist workers, Playwright trace/debug/browsers. |
| MCP no disponible o login de Notebook | Codex configuración/MCP, README e issues del CLI de Gemini Notebook. |

## Referencias por tecnología

### Python

Versión o ámbito local: **3.12 imagen; >=3.12,<3.14 proyecto**.

- [Referencia](https://docs.python.org/3.12/). Serie 3.12. Título servido: «3.12.15 Documentation».
- [Entornos virtuales](https://docs.python.org/3.12/library/venv.html). Serie 3.12. Título servido: «venv — Creation of virtual environments — Python 3.12.15 documentation».
- [Logging](https://docs.python.org/3.12/howto/logging.html). Serie 3.12. Título servido: «Logging HOWTO — Python 3.12.15 documentation».
- [Diagnóstico de bloqueos](https://docs.python.org/3.12/library/faulthandler.html). Serie 3.12. Título servido: «faulthandler — Dump the Python traceback — Python 3.12.15 documentation».
- [Perfilado](https://docs.python.org/3.12/library/profile.html). Serie 3.12. Título servido: «The Python Profilers — Python 3.12.15 documentation».
- [hashlib/HMAC](https://docs.python.org/3.12/library/hashlib.html). Serie 3.12. Título servido: «hashlib — Secure hashes and message digests — Python 3.12.15 documentation».
- [Temporales](https://docs.python.org/3.12/library/tempfile.html). Serie 3.12. Título servido: «tempfile — Generate temporary files and directories — Python 3.12.15 documentation».

### Django

Versión o ámbito local: **5.2.17**.

- [Documentación](https://docs.djangoproject.com/en/5.2/). Serie 5.2. Título servido: «Django documentation | Django documentation | Django».
- [Configuración](https://docs.djangoproject.com/en/5.2/ref/settings/). Serie 5.2. Título servido: «Settings | Django documentation | Django».
- [Checklist de despliegue](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/). Serie 5.2. Título servido: «Deployment checklist | Django documentation | Django».
- [PostgreSQL](https://docs.djangoproject.com/en/5.2/ref/databases/). Serie 5.2. Título servido: «Databases | Django documentation | Django».
- [Transacciones](https://docs.djangoproject.com/en/5.2/topics/db/transactions/). Serie 5.2. Título servido: «Database transactions | Django documentation | Django».
- [Migraciones](https://docs.djangoproject.com/en/5.2/topics/migrations/). Serie 5.2. Título servido: «Migrations | Django documentation | Django».
- [Rendimiento SQL](https://docs.djangoproject.com/en/5.2/topics/db/optimization/). Serie 5.2. Título servido: «Database access optimization | Django documentation | Django».
- [Seguridad](https://docs.djangoproject.com/en/5.2/topics/security/). Serie 5.2. Título servido: «Security in Django | Django documentation | Django».
- [Sesiones](https://docs.djangoproject.com/en/5.2/topics/http/sessions/). Serie 5.2. Título servido: «How to use sessions | Django documentation | Django».
- [Contraseñas](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/). Serie 5.2. Título servido: «Password management in Django | Django documentation | Django».
- [Logging](https://docs.djangoproject.com/en/5.2/topics/logging/). Serie 5.2. Título servido: «Logging | Django documentation | Django».
- [Estáticos](https://docs.djangoproject.com/en/5.2/howto/static-files/). Serie 5.2. Título servido: «How to manage static files (e.g. images, JavaScript, CSS) | Django documentation | Django».
- [Pruebas](https://docs.djangoproject.com/en/5.2/topics/testing/). Serie 5.2. Título servido: «Testing in Django | Django documentation | Django».
- [Troubleshooting](https://docs.djangoproject.com/en/5.2/faq/troubleshooting/). Serie 5.2. Título servido: «Troubleshooting | Django documentation | Django».

### PostgreSQL

Versión o ámbito local: **17-alpine**.

- [Configuración](https://www.postgresql.org/docs/17/runtime-config.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: Chapter 19. Server Configuration».
- [Conexiones y autenticación](https://www.postgresql.org/docs/17/client-authentication.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: Chapter 20. Client Authentication».
- [Concurrencia](https://www.postgresql.org/docs/17/mvcc.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: Chapter 13. Concurrency Control».
- [Bloqueos](https://www.postgresql.org/docs/17/explicit-locking.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: 13.3. Explicit Locking».
- [EXPLAIN](https://www.postgresql.org/docs/17/using-explain.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: 14.1. Using EXPLAIN».
- [Estadísticas y actividad](https://www.postgresql.org/docs/17/monitoring.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: Chapter 27. Monitoring Database Activity».
- [Logging](https://www.postgresql.org/docs/17/runtime-config-logging.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: 19.8. Error Reporting and Logging».
- [Backup/restauración](https://www.postgresql.org/docs/17/backup.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: Chapter 25. Backup and Restore».
- [Autovacuum](https://www.postgresql.org/docs/17/routine-vacuuming.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: 24.1. Routine Vacuuming».
- [Triggers](https://www.postgresql.org/docs/17/triggers.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: Chapter 37. Triggers».
- [Errores SQLSTATE](https://www.postgresql.org/docs/17/errcodes-appendix.html). Serie 17. Título servido: «PostgreSQL: Documentation: 17: Appendix A. PostgreSQL Error Codes».

### psycopg

Versión o ámbito local: **3.3.6**.

- [Instalación](https://www.psycopg.org/psycopg3/docs/basic/install.html). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «Installation - psycopg 3.3.7.dev1 documentation».
- [Transacciones](https://www.psycopg.org/psycopg3/docs/basic/transactions.html). Documentación 3 dinámica: contrastar con tag 3.3.6. Título servido: «Transactions management - psycopg 3.3.7.dev1 documentation».
- [SQL seguro](https://www.psycopg.org/psycopg3/docs/api/sql.html). Documentación 3 dinámica: contrastar con tag 3.3.6. Título servido: «sql – SQL string composition - psycopg 3.3.7.dev1 documentation».
- [Errores](https://www.psycopg.org/psycopg3/docs/api/errors.html). Documentación 3 dinámica: contrastar con tag 3.3.6. Título servido: «errors – Package exceptions - psycopg 3.3.7.dev1 documentation».
- [Parámetros](https://www.psycopg.org/psycopg3/docs/basic/params.html). Documentación 3 dinámica: contrastar con tag 3.3.6. Título servido: «Passing parameters to SQL queries - psycopg 3.3.7.dev1 documentation».
- [Fuente fijada](https://github.com/psycopg/psycopg/tree/3.3.6). Código/versiones oficial. Título servido: «GitHub - psycopg/psycopg at 3.3.6 · GitHub».
- [Incidencias](https://github.com/psycopg/psycopg/issues). Código/versiones oficial. Título servido: «Issues · psycopg/psycopg · GitHub».

### Celery

Versión o ámbito local: **5.6.3**.

- [Configuración](https://docs.celeryq.dev/en/v5.6.3/userguide/configuration.html). Versión exacta si accesible. Título servido: «Configuration and defaults — Celery 5.6.2 documentation».
- [Django](https://docs.celeryq.dev/en/v5.6.3/django/first-steps-with-django.html). Versión exacta si accesible. Título servido: «First steps with Django — Celery 5.6.2 documentation».
- [Redis broker](https://docs.celeryq.dev/en/v5.6.3/getting-started/backends-and-brokers/redis.html). Versión exacta si accesible. Título servido: «Using Redis — Celery 5.6.2 documentation».
- [Workers](https://docs.celeryq.dev/en/v5.6.3/userguide/workers.html). Versión exacta si accesible. Título servido: «Workers Guide — Celery 5.6.2 documentation».
- [Beat](https://docs.celeryq.dev/en/v5.6.3/userguide/periodic-tasks.html). Versión exacta si accesible. Título servido: «Periodic Tasks — Celery 5.6.2 documentation».
- [Monitorización](https://docs.celeryq.dev/en/v5.6.3/userguide/monitoring.html). Versión exacta si accesible. Título servido: «Monitoring and Management Guide — Celery 5.6.2 documentation».
- [Optimización](https://docs.celeryq.dev/en/v5.6.3/userguide/optimizing.html). Versión exacta si accesible. Título servido: «Optimizing — Celery 5.6.2 documentation».
- [FAQ/diagnóstico](https://docs.celeryq.dev/en/v5.6.3/faq.html). Versión exacta si accesible. Título servido: «Frequently Asked Questions — Celery 5.6.2 documentation».
- [Fuente y documentación de referencia](https://github.com/celery/celery/tree/v5.6.3). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «GitHub - celery/celery at v5.6.3 · GitHub».

### Redis servidor

Versión o ámbito local: **7.4-alpine; 7.4**.

- [Configuración](https://redis.io/docs/latest/operate/oss_and_stack/management/config/). Guías dinámicas; comprobar disponibilidad de opciones en 7.4. Título servido: «Redis configuration | Docs».
- [Persistencia RDB/AOF](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/). Guías dinámicas; comprobar disponibilidad de opciones en 7.4. Título servido: «Redis persistence | Docs».
- [Latencia](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/). Guías dinámicas; comprobar disponibilidad de opciones en 7.4. Título servido: «Diagnosing latency issues | Docs».
- [Monitor de latencia](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency-monitor/). Guías dinámicas; comprobar disponibilidad de opciones en 7.4. Título servido: «Redis latency monitoring | Docs».
- [Memoria](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/). Guías dinámicas; comprobar disponibilidad de opciones en 7.4. Título servido: «Memory optimization | Docs».
- [Seguridad](https://redis.io/docs/latest/operate/oss_and_stack/management/security/). Guías dinámicas; comprobar disponibilidad de opciones en 7.4. Título servido: «Redis security | Docs».
- [Fuente fijada](https://github.com/redis/redis/tree/7.4). Código/versiones oficial. Título servido: «GitHub - redis/redis at 7.4 · GitHub».
- [Incidencias](https://github.com/redis/redis/issues). Código/versiones oficial. Título servido: «Issues · redis/redis · GitHub».

### redis-py

Versión o ámbito local: **6.4.0**.

- [Cliente Python](https://redis.readthedocs.io/en/v6.4.0/). Versión exacta. Título servido: «redis-py 6.4.0 documentation».
- [Conexiones](https://redis.readthedocs.io/en/v6.4.0/connections.html). Versión exacta. Título servido: «Connecting to Redis - redis-py 6.4.0 documentation».
- [Retry](https://redis.readthedocs.io/en/v6.4.0/retry.html). Versión exacta. Título servido: «Retry Helpers - redis-py 6.4.0 documentation».

### Gunicorn

Versión o ámbito local: **23.0.0**.

- [Settings/timeouts/logging](https://github.com/benoitc/gunicorn/blob/23.0.0/docs/source/settings.rst). Documentación fuente oficial fijada en tag23.0.0; sitio HTML anterior no accesible. Título servido: «gunicorn/docs/source/settings.rst at 23.0.0 · benoitc/gunicorn · GitHub».
- [Despliegue](https://github.com/benoitc/gunicorn/blob/23.0.0/docs/source/deploy.rst). Documentación fuente oficial fijada en tag23.0.0; sitio HTML anterior no accesible. Título servido: «gunicorn/docs/source/deploy.rst at 23.0.0 · benoitc/gunicorn · GitHub».
- [Workers y diseño](https://github.com/benoitc/gunicorn/blob/23.0.0/docs/source/design.rst). Documentación fuente oficial fijada en tag23.0.0; sitio HTML anterior no accesible. Título servido: «gunicorn/docs/source/design.rst at 23.0.0 · benoitc/gunicorn · GitHub».
- [FAQ/diagnóstico](https://github.com/benoitc/gunicorn/blob/23.0.0/docs/source/faq.rst). Documentación fuente oficial fijada en tag23.0.0; sitio HTML anterior no accesible. Título servido: «gunicorn/docs/source/faq.rst at 23.0.0 · benoitc/gunicorn · GitHub».
- [Fuente y documentación de referencia](https://github.com/benoitc/gunicorn/tree/23.0.0). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «GitHub - benoitc/gunicorn at 23.0.0 · GitHub».

### Caddy

Versión o ámbito local: **2-alpine; patch sin fijar**.

- [Configuración](https://caddyserver.com/docs/caddyfile). Documentación 2 dinámica. Título servido: «The Caddyfile — Caddy Documentation».
- [Reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy). Documentación 2 dinámica. Título servido: «reverse_proxy (Caddyfile directive) — Caddy Documentation».
- [Forward auth](https://caddyserver.com/docs/caddyfile/directives/forward_auth). Documentación 2 dinámica. Título servido: «forward_auth (Caddyfile directive) — Caddy Documentation».
- [Estáticos](https://caddyserver.com/docs/caddyfile/directives/file_server). Documentación 2 dinámica. Título servido: «file_server (Caddyfile directive) — Caddy Documentation».
- [Logging](https://caddyserver.com/docs/caddyfile/directives/log). Documentación 2 dinámica. Título servido: «log (Caddyfile directive) — Caddy Documentation».
- [CLI/validación](https://caddyserver.com/docs/command-line). Documentación 2 dinámica. Título servido: «Command Line — Caddy Documentation».
- [Errores frecuentes](https://caddyserver.com/docs/faq). Documentación 2 dinámica. Título servido: «faq — Caddy Documentation».

### Docker/Compose

Versión o ámbito local: **Equipo Docker29.8.2/Compose5.6.0; imagen Python3.12-slim**.

- [Compose](https://docs.docker.com/compose/). Documentación dinámica. Título servido: «Docker Compose | Docker Docs».
- [Referencia Compose](https://docs.docker.com/reference/compose-file/). Documentación dinámica. Título servido: «Compose file reference | Docker Docs».
- [Variables](https://docs.docker.com/compose/how-tos/environment-variables/). Documentación dinámica. Título servido: «Environment variables in Compose | Docker Docs».
- [Arranque y healthchecks](https://docs.docker.com/compose/how-tos/startup-order/). Documentación dinámica. Título servido: «Control startup and shutdown order in Compose | Docker Docs».
- [Volúmenes](https://docs.docker.com/engine/storage/volumes/). Documentación dinámica. Título servido: «Volumes | Docker Docs».
- [Logs](https://docs.docker.com/engine/logging/). Documentación dinámica. Título servido: «View container logs | Docker Docs».
- [Recursos/cgroups](https://docs.docker.com/engine/containers/resource_constraints/). Documentación dinámica. Título servido: «Resource constraints | Docker Docs».
- [Troubleshooting](https://docs.docker.com/engine/daemon/troubleshoot/). Documentación dinámica. Título servido: «Troubleshooting the Docker daemon | Docker Docs».
- [Build multi-stage](https://docs.docker.com/build/building/multi-stage/). Documentación dinámica. Título servido: «Multi-stage builds | Docker Docs».

### uv

Versión o ámbito local: **0.11.6 Docker;0.12.23 equipo; 0.11.6 imagen**.

- [Configuración](https://docs.astral.sh/uv/concepts/configuration-files/). Documentación dinámica. Título servido: «Configuration files | uv».
- [Lock y sync](https://docs.astral.sh/uv/concepts/projects/sync/). Documentación dinámica. Título servido: «Locking and syncing | uv».
- [Docker](https://docs.astral.sh/uv/guides/integration/docker/). Documentación dinámica. Título servido: «Using uv in Docker | uv».
- [Python](https://docs.astral.sh/uv/concepts/python-versions/). Documentación dinámica. Título servido: «Python versions | uv».
- [Troubleshooting](https://docs.astral.sh/uv/reference/troubleshooting/). Documentación dinámica. Título servido: «Troubleshooting | uv».
- [CLI](https://docs.astral.sh/uv/reference/cli/). Documentación dinámica. Título servido: «Commands | uv».
- [Fuente fijada](https://github.com/astral-sh/uv/tree/0.11.6). Código/versiones oficial. Título servido: «GitHub - astral-sh/uv at 0.11.6 · GitHub».
- [Incidencias](https://github.com/astral-sh/uv/issues). Código/versiones oficial. Título servido: «Issues · astral-sh/uv · GitHub».

### RustFS

Versión o ámbito local: **Digest1803faef5762…; no versión semántica acreditada; digest fijado**.

- [Documentación](https://docs.rustfs.com/). Documentación dinámica; contrastar con digest desplegado. Título servido: «RustFS Documentation».
- [Comprobación de estado](https://docs.rustfs.com/en/operations/status-check). Documentación dinámica; contrastar con digest desplegado. Título servido: «Status Check».
- [Fuente fijada](https://github.com/rustfs/rustfs/). Código/versiones oficial. Título servido: «GitHub - rustfs/rustfs: RustFS is an open-source, S3-compatible high-performance object storage system supporting migration and coexistence with other S3-compatible platforms such as MinIO and Ceph…».
- [Incidencias](https://github.com/rustfs/rustfs/issues). Código/versiones oficial. Título servido: «Issues · rustfs/rustfs · GitHub».

### django-storages

Versión o ámbito local: **1.14.6**.

- [S3/configuración](https://django-storages.readthedocs.io/en/1.14.6/backends/amazon-S3.html). Versión exacta. Título servido: «Amazon S3 - django-storages 1.14.6 documentation».

### boto3/botocore

Versión o ámbito local: **1.43.108/1.43.108; 1.43.108**.

- [Configuración](https://docs.aws.amazon.com/boto3/latest/guide/configuration.html). Versión exacta boto3; redirección observada, no asumir versión exacta. Título servido: «Configuration - Boto3 1.43.111 documentation».
- [Credenciales](https://docs.aws.amazon.com/boto3/latest/guide/credentials.html). Versión exacta boto3; redirección observada, no asumir versión exacta. Título servido: «Credentials - Boto3 1.43.111 documentation».
- [Retries](https://docs.aws.amazon.com/boto3/latest/guide/retries.html). Versión exacta boto3; redirección observada, no asumir versión exacta. Título servido: «Retries - Boto3 1.43.111 documentation».
- [Errores](https://docs.aws.amazon.com/boto3/latest/guide/error-handling.html). Versión exacta boto3; redirección observada, no asumir versión exacta. Título servido: «Error handling - Boto3 1.43.111 documentation».
- [S3](https://docs.aws.amazon.com/boto3/latest/reference/services/s3.html). Versión exacta boto3; redirección observada, no asumir versión exacta. Título servido: «S3 - Boto3 1.43.111 documentation».
- [Fuente y documentación de referencia](https://github.com/boto/boto3/tree/1.43.108). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «GitHub - boto/boto3 at 1.43.108 · GitHub».
- [Fuente y documentación de referencia](https://github.com/boto/botocore/tree/1.43.108). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «GitHub - boto/botocore at 1.43.108 · GitHub».

### Pillow

Versión o ámbito local: **12.3.0**.

- [Image/validación](https://pillow.readthedocs.io/en/stable/reference/Image.html). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «Image module - Pillow (PIL Fork) 12.3.0 documentation».
- [Instalación/dependencias](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «Basic installation - Pillow (PIL Fork) 12.3.0 documentation».
- [Formatos](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «Image file formats - Pillow (PIL Fork) 12.3.0 documentation».
- [Fuente y documentación de referencia](https://github.com/python-pillow/Pillow/tree/12.3.0). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «GitHub - python-pillow/Pillow at 12.3.0 · GitHub».

### OpenCV

Versión o ámbito local: **4.14.0.94 paquete**.

- [Referencia](https://docs.opencv.org/4.13.0/). Serie4.x dinámica; patch del wrapper distinto del core; redirección observada, no asumir versión exacta. Título servido: «OpenCV: OpenCV modules».
- [Image processing](https://docs.opencv.org/4.13.0/d7/dbd/group__imgproc.html). Serie4.x dinámica; patch del wrapper distinto del core; redirección observada, no asumir versión exacta. Título servido: «OpenCV: Image Processing».

### NumPy

Versión o ámbito local: **2.5.3**.

- [Referencia](https://numpy.org/doc/2.5/). Serie2.5. Título servido: «NumPy documentation — NumPy v2.5 Manual».
- [Troubleshooting imports/ABI](https://numpy.org/doc/2.5/user/troubleshooting-importerror.html). Serie2.5. Título servido: «Troubleshooting — NumPy v2.5 Manual».

### SciPy

Versión o ámbito local: **1.18.1**.

- [Referencia](https://docs.scipy.org/doc/scipy/). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «SciPy documentation — SciPy v1.18.0 Manual».
- [FFT](https://docs.scipy.org/doc/scipy/reference/fft.html). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «Discrete Fourier transforms (scipy.fft) — SciPy v1.18.0 Manual».
- [Fuente y documentación de referencia](https://github.com/scipy/scipy/tree/v1.18.1). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «GitHub - scipy/scipy at v1.18.1 · GitHub».

### argon2-cffi

Versión o ámbito local: **25.1.0**.

- [Configuración/API](https://argon2-cffi.readthedocs.io/en/25.1.0/api.html). Versión exacta. Título servido: «API Reference - argon2-cffi 25.1.0 documentation».
- [Parámetros](https://argon2-cffi.readthedocs.io/en/25.1.0/parameters.html). Versión exacta. Título servido: «Choosing Parameters - argon2-cffi 25.1.0 documentation».
- [FAQ](https://argon2-cffi.readthedocs.io/en/25.1.0/faq.html). Versión exacta. Título servido: «Frequently Asked Questions - argon2-cffi 25.1.0 documentation».

### cryptography

Versión o ámbito local: **50.0.2**.

- [Instalación](https://cryptography.io/en/50.0.2/installation/). Versión exacta. Título servido: «Installation — Cryptography 50.0.2 documentation».
- [AES-GCM/AEAD](https://cryptography.io/en/50.0.2/hazmat/primitives/aead/). Versión exacta. Título servido: «Authenticated encryption — Cryptography 50.0.2 documentation».
- [Fernet](https://cryptography.io/en/50.0.2/fernet/). Versión exacta. Título servido: «Fernet (symmetric encryption) — Cryptography 50.0.2 documentation».
- [FAQ](https://cryptography.io/en/50.0.2/faq/). Versión exacta. Título servido: «Frequently asked questions — Cryptography 50.0.2 documentation».

### Cython

Versión o ámbito local: **3.0.12**.

- [Compilación](https://cython.readthedocs.io/en/3.0.x/src/userguide/source_files_and_compilation.html). Serie3.0. Título servido: «Source Files and Compilation — Cython 3.0.12 documentation».
- [Depuración](https://cython.readthedocs.io/en/3.0.x/src/userguide/debugging.html). Serie3.0. Título servido: «Debugging your Cython program — Cython 3.0.12 documentation».

### pytest

Versión o ámbito local: **9.1.1**.

- [Configuración](https://pytest.org/en/stable/reference/customize.html). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «Configuration - pytest documentation».
- [Fixtures](https://pytest.org/en/stable/how-to/fixtures.html). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «How to use fixtures - pytest documentation».
- [Fallos/hangs](https://pytest.org/en/stable/how-to/failures.html). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «How to handle test failures - pytest documentation».
- [Fuente y documentación de referencia](https://github.com/pytest-dev/pytest/tree/9.1.1). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «GitHub - pytest-dev/pytest at 9.1.1 · GitHub».

### pytest-django

Versión o ámbito local: **4.14.0**.

- [Configuración](https://pytest-django.readthedocs.io/en/latest/configuring_django.html). Documentación dinámica. Título servido: «Configuring Django settings — pytest-django documentation».
- [Base de datos](https://pytest-django.readthedocs.io/en/latest/database.html). Documentación dinámica. Título servido: «Database access — pytest-django documentation».
- [FAQ](https://pytest-django.readthedocs.io/en/latest/faq.html). Documentación dinámica. Título servido: «FAQ — pytest-django documentation».

### pytest-xdist

Versión o ámbito local: **3.8.0**.

- [Distribución](https://pytest-xdist.readthedocs.io/en/stable/distribution.html). Documentación dinámica. Título servido: «Running tests across multiple CPUs — pytest-xdist documentation».
- [Workers](https://pytest-xdist.readthedocs.io/en/stable/how-to.html). Documentación dinámica. Título servido: «How-tos — pytest-xdist documentation».

### Playwright Python

Versión o ámbito local: **1.63.0**.

- [Navegadores y dependencias](https://playwright.dev/python/docs/browsers). Documentación dinámica. Título servido: «Browsers | Playwright Python».
- [Configuración de pruebas](https://playwright.dev/python/docs/test-runners). Documentación dinámica. Título servido: «Pytest Plugin Reference | Playwright Python».
- [Trace viewer](https://playwright.dev/python/docs/trace-viewer). Documentación dinámica. Título servido: «Trace viewer | Playwright Python».
- [Debugging](https://playwright.dev/python/docs/debug). Documentación dinámica. Título servido: «Debugging Tests | Playwright Python».
- [CI](https://playwright.dev/python/docs/ci). Documentación dinámica. Título servido: «Continuous Integration | Playwright Python».

### Ruff

Versión o ámbito local: **0.16.10**.

- [Configuración](https://docs.astral.sh/ruff/configuration/). Documentación dinámica. Título servido: «Configuring Ruff | Ruff».
- [Linter](https://docs.astral.sh/ruff/linter/). Documentación dinámica. Título servido: «The Ruff Linter | Ruff».
- [Formato](https://docs.astral.sh/ruff/formatter/). Documentación dinámica. Título servido: «The Ruff Formatter | Ruff».
- [Fuente fijada](https://github.com/astral-sh/ruff/tree/0.16.10). Código/versiones oficial. Título servido: «GitHub - astral-sh/ruff at 0.16.10 · GitHub».
- [Incidencias](https://github.com/astral-sh/ruff/issues). Código/versiones oficial. Título servido: «Issues · astral-sh/ruff · GitHub».

### HTMX

Versión o ámbito local: **2.0.11**.

- [Referencia](https://htmx.org/docs/). Documentación dinámica2.x; tag fija fuente. Título servido: «</> htmx ~ Documentation».
- [Logging/diagnóstico](https://htmx.org/api/). Documentación dinámica2.x; tag fija fuente. Título servido: «</> htmx ~ Javascript API».
- [Eventos](https://htmx.org/reference/). Documentación dinámica2.x; tag fija fuente. Título servido: «</> htmx ~ Reference».
- [Fuente fijada](https://github.com/bigskysoftware/htmx/tree/v2.0.11). Código/versiones oficial. Título servido: «GitHub - bigskysoftware/htmx at v2.0.11 · GitHub».
- [Incidencias](https://github.com/bigskysoftware/htmx/issues). Código/versiones oficial. Título servido: «Issues · bigskysoftware/htmx · GitHub».

### Web HTML/CSS/JavaScript

Versión o ámbito local: **Sin paquete versionado**.

- [HTML](https://html.spec.whatwg.org/multipage/). Estándares normativos, no frameworks añadidos. Título servido: «HTML Standard».
- [CSS](https://www.w3.org/Style/CSS/). Estándares normativos, no frameworks añadidos. Título servido: «Cascading Style Sheets».
- [ECMAScript](https://tc39.es/ecma262/). Estándares normativos, no frameworks añadidos. Título servido: «ECMAScript® 2027 Language Specification».

### Git

Versión o ámbito local: **2.53.0 equipo**.

- [Configuración](https://git-scm.com/docs/git-config/2.53.0). Versión exacta. Título servido: «Git - git-config Documentation».
- [Fetch](https://git-scm.com/docs/git-fetch/2.53.0). Versión exacta. Título servido: «Git - git-fetch Documentation».
- [Worktrees](https://git-scm.com/docs/git-worktree/2.53.0). Versión exacta. Título servido: «Git - git-worktree Documentation».

### GitHub Actions

Versión o ámbito local: **Workflow manual; acciones según yaml**.

- [Configuración](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax). Documentación dinámica; redirección observada, no asumir versión exacta. Título servido: «Workflow syntax for GitHub Actions - GitHub Docs».
- [Servicios](https://docs.github.com/en/actions/tutorials/use-containerized-services/use-docker-service-containers). Documentación dinámica; redirección observada, no asumir versión exacta. Título servido: «Communicating with Docker service containers - GitHub Docs».

### Codex

Versión o ámbito local: **Herramienta de ingeniería; versión no inventariada**.

- [Configuración](https://learn.chatgpt.com/docs/config-file/config-basic). Documentación oficial dinámica; redirección observada, no asumir versión exacta. Título servido: «Config basics | ChatGPT Learn».
- [MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). Documentación oficial dinámica; redirección observada, no asumir versión exacta. Título servido: «Model Context Protocol | ChatGPT Learn».

### Claude Code

Versión o ámbito local: **Herramienta de ingeniería; versión no inventariada**.

- [Configuración](https://code.claude.com/docs/en/settings). Documentación oficial dinámica. Título servido: «Settings files and precedence - Claude Code Docs».
- [Troubleshooting](https://code.claude.com/docs/en/troubleshooting). Documentación oficial dinámica. Título servido: «Troubleshooting - Claude Code Docs».

### ImageHash

Versión o ámbito local: **4.3.2**.

- [Fuente/README](https://github.com/JohannesBuchner/imagehash). Fallback oficial dinámico; URL exacta original no accesible. Contrastar versión indicada.. Título servido: «GitHub - JohannesBuchner/imagehash: A Python Perceptual Image Hashing Module · GitHub».
- [Issues/diagnóstico](https://github.com/JohannesBuchner/imagehash/issues). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «Issues · JohannesBuchner/imagehash · GitHub».

### PyOTP

Versión o ámbito local: **2.10.0**.

- [Fuente/README](https://github.com/pyauth/pyotp/tree/v2.10.0). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «GitHub - pyauth/pyotp at v2.10.0 · GitHub».
- [Issues/diagnóstico](https://github.com/pyauth/pyotp/issues). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «Issues · pyauth/pyotp · GitHub».

### orjson

Versión o ámbito local: **3.13.0**.

- [Fuente/README](https://github.com/ijl/orjson/tree/3.13.0). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «GitHub - ijl/orjson at 3.13.0 · GitHub».
- [Issues/diagnóstico](https://github.com/ijl/orjson/issues). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «Issues · ijl/orjson · GitHub».

### blake3

Versión o ámbito local: **1.0.11**.

- [Fuente/README](https://github.com/oconnor663/blake3-py/tree/1.0.11). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «GitHub - oconnor663/blake3-py at 1.0.11 · GitHub».
- [Issues/diagnóstico](https://github.com/oconnor663/blake3-py/issues). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «Issues · oconnor663/blake3-py · GitHub».

### pip-audit

Versión o ámbito local: **2.10.1**.

- [Fuente/README](https://github.com/pypa/pip-audit/tree/v2.10.1). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «GitHub - pypa/pip-audit at v2.10.1 · GitHub».
- [Issues/diagnóstico](https://github.com/pypa/pip-audit/issues). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «Issues · pypa/pip-audit · GitHub».

### Graphify

Versión o ámbito local: **0.9.64**.

- [Fuente/README](https://github.com/Graphify-Labs/graphify/). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «GitHub - Graphify-Labs/graphify: Turn any codebase, with its docs, SQL schemas, configs, and PDFs, into a queryable knowledge graph. A /graphify skill for Claude Code, Cursor, Codex, and Gemini CLI…».
- [Issues/diagnóstico](https://github.com/Graphify-Labs/graphify/issues). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «Issues · Graphify-Labs/graphify · GitHub».

### Gemini Notebook CLI/MCP

Versión o ámbito local: **0.15.4**.

- [Fuente/README](https://github.com/jacob-bd/gemini-notebook-mcp-cli/tree/v0.15.4). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «GitHub - jacob-bd/gemini-notebook-mcp-cli at v0.15.4 · GitHub».
- [Issues/diagnóstico](https://github.com/jacob-bd/gemini-notebook-mcp-cli/issues). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «Issues · jacob-bd/gemini-notebook-mcp-cli · GitHub».

### librdb

Versión o ámbito local: **bc5f295c98b40c2c33099d9d72ab30ce9e595dc7**.

- [Fuente/README](https://github.com/redis/librdb/tree/bc5f295c98b40c2c33099d9d72ab30ce9e595dc7). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «GitHub - redis/librdb at bc5f295c98b40c2c33099d9d72ab30ce9e595dc7 · GitHub».
- [Issues/diagnóstico](https://github.com/redis/librdb/issues). Fuente oficial fijada si tag accesible; incidencias dinámicas. Título servido: «Issues · redis/librdb · GitHub».

### Linux/GCC

Versión o ámbito local: **Herramientas de build/kernel; versión no inventariada**.

- [Fuente y documentación de referencia](https://docs.kernel.org/admin-guide/cgroup-v2.html). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «Control Group v2 — The Linux Kernel documentation».
- [Fuente y documentación de referencia](https://gcc.gnu.org/onlinedocs/). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «GCC online documentation - GNU Project».

### S3

Versión o ámbito local: **Protocolo compatible; no proveedor contratado**.

- [Fuente y documentación de referencia](https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio. Título servido: «Welcome - Amazon S3».

### Gemini Notebook

Versión o ámbito local: **Servicio externo; no versión local**.

- [Fuente y documentación de referencia](https://support.google.com/gemininotebook/answer/16215270). Fuente oficial exacta si tag; documentación dinámica en kernel/GCC/S3/servicio; redirección observada, no asumir versión exacta. Título servido: «Add or discover new sources for your notebook - Computer - Gemini Notebook Help».

## Importación directa en el cuaderno — 2026-10-11

El usuario confirma plan **Plus**: se aplica el límite oficial de **100 fuentes por cuaderno**, aunque `nlm usage` devolvió una etiqueta interna Pro. Se añadieron **50 URLs seleccionadas**, correspondientes a42áreas tecnológicas, a las50fuentes existentes (incluida la URL de configuración Django5.2). Total verificado: **100fuentes**; las50nuevas tienen estado listo (`2`). La importación utiliza `source_add` con `source_type="url"`/`urls`, vía el CLI `nlm source add --url`, en lotes de5, no archivos con enlaces.

Selección: una referencia útil por área, más transacciones/optimización Django, EXPLAIN/monitorización PostgreSQL, workers Celery, latencia Redis y estándares concretos CSS/JavaScript. Se omiten páginas genéricas de incidencias y repeticiones; se mantienen todas las fuentes previas del proyecto. Para dependencias sin documentación exacta se conservan las notas de ámbito/versión del catálogo. El catálogo completo de176URLs permanece como referencia; no se importaron176páginas.

Se comprobó además contenido textual en una muestra de tres nuevas fuentes: configuración PostgreSQL11.299caracteres, PyOTP12.892 y referencia Compose63.674. Esta muestra no acredita cobertura de enlaces secundarios de las50páginas. Una URL importa esa página, no un sitio entero; el índice puede remitir a páginas que no son fuentes del cuaderno. No se ha contratado ni cambiado el plan.

El cuaderno está en el límite operativo100/100. Para futuras incorporaciones habrá que consolidar o sustituir fuentes existentes conservando su contenido; este corte no elimina fuentes. [Evidencia, selección y fuentes importadas](evidencias/notebook-urls-importadas-20261011.json).

## Evidencia y mantenimiento

[Registro de comprobación](evidencias/urls-oficiales-tecnologias-20261011.json): URL solicitada, URL final, HTTP, título y rutas exactas no disponibles cuando se usó fallback. La comprobación no modifica configuraciones ni realiza una auditoría de vulnerabilidades. Actualizar este catálogo tras cambiar `uv.lock`, imágenes, herramientas de build o versiones de interfaz.
