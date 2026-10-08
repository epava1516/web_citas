# Análisis estático del repositorio — Claude Code

Fecha: 2026-10-08. Autoría: **Claude Code** (CLI de Anthropic), modelo **Claude Opus 5.5** (`claude-opus-5-5`), en sesión interactiva solicitada directamente por el usuario. Código analizado: `8f461b9`, árbol limpio.

Naturaleza: revisión técnica de lectura. **No** es aceptación de ningún CR, GS-01, fase ni gate, **no** ejecuta pruebas y **no** modifica código de aplicación. No se invocó mediante `scripts/claude-task` ni lo aplicó Codex; conforme a AGENTS.md, Codex conserva la decisión sobre aplicar o descartar cualquier hallazgo. Sin datos reales, proveedores ni publicación.

## Método y límites

- Grafo Graphify 0.9.64 generado con `graphify update .` (solo AST, sin LLM): 2037 archivos, 7620 nodos, 34454 aristas, 309 comunidades, sin ciclos de importación. Salida en `graphify-out/` (ignorada por git).
- Lectura completa: `config/`, `compose.yaml`, `Dockerfile`, `Caddyfile`, CI, modelos y flujos principales de `core`, `listings`, `mediafiles`, `catalog`; en `safety`: modelos, `crypto`, `rights` (entrada/recibo/cola), `rights_scope`, `views` (denuncias), `erasure_execution`, `notices`, `notice_delivery`, `tasks`; plantillas base/listado, estáticos, estructura de pruebas y scripts.
- Documentación leída: README, docs/README, contratos 14 y 16 completos, seguimiento17 (estado, próximo trabajo, dependencias, avance, reglas), matriz88 (estado y recorridos), extractos de 01/03/05/10 y contratos 01/05.
- **No leídos línea a línea:** la mayoría de los ~86 módulos `rights_*`, `contratos/10` completo, matriz83, evidencias.
- **Sin ejecución:** en la máquina actual no hay `uv` ni `.venv` y el Python del sistema es 3.14 (fuera de `>=3.12,<3.14`). Ningún hallazgo se ha reproducido; todos requieren verificación N1 antes de actuar.

## Arquitectura observada

Django 5.2 monolítico con plantillas HTML (sin API; HTMX no se usa todavía), PostgreSQL 17, Celery/Redis (worker concurrencia 2, Beat con 18 tareas cada 60 s), Caddy como proxy y Gunicorn con 2 workers.

| Área | Archivos | Líneas aprox. | Responsabilidad |
| --- | ---: | ---: | --- |
| `apps/safety` | 294 | 48 500 | Denuncias, reclamaciones, siete derechos, retención, recuperación, censo Redis/logs |
| `apps/listings` | 44 | 5 000 | Anuncio/revisiones, moderación, ciclo de vida, descubrimiento, proyección SQL |
| `apps/core` | 38 | 4 800 | Cuentas, MFA, agencias, verificación/representación, legal |
| `apps/catalog` | 23 | 1 900 | Catálogo, geografía, promociones sintéticas |
| `apps/mediafiles` | 19 | 1 700 | Blob/Photo, derivados, similitud, borrado físico |
| `tests` | 435 | 76 500 | 1153 tests; 167 archivos con Playwright; ~9 500 líneas de experimentos de rendimiento |

Patrones consistentes: orden de bloqueos agencia→persona→anuncio→revisión con `select_for_update`; versiones optimistas (409) y claves UUID idempotentes; `seal`/`unseal` Fernet para datos sensibles y `fingerprint` HMAC para comparación; lectura privada solo por POST auditado con motivo; conflicto de interés y MFA vigente en cada decisión; cabeceras `no-store`/`noindex` y filtro de logs en rutas privadas.

Nodos con más conexiones: `User`(655), `unseal`(427), `RightsAction`(408), `Person`(320), `fingerprint`(317), `Revision`(297), `seal`(275), `RightsRequest`(269), `canonical`(190), `Listing`(184).

## Hallazgos

Ordenados por impacto estimado. «Documentado» indica que el seguimiento o los contratos ya lo recogen; se incluye por su efecto concreto.

| ID | Hallazgo | Ubicación | Estado previo |
| --- | --- | --- | --- |
| CC-01 | El descubrimiento valida en Python cada candidato con formularios completos antes de paginar: coste O(N candidatos) por petición. | `apps/listings/discovery.py:230`, `moderation.publicly_visible` | Documentado (MOD-04) |
| CC-02 | La vía proyectada está desactivada con `settings.PRODUCTION`, filtro `checked` o promociones: en producción siempre se usa el camino O(N). | `apps/listings/projected_publication.py:183` | Documentado como «fallback» de modos; no destacado como bloqueo de producción |
| CC-03 | La vía proyectada depende de una huella SHA del bytecode de ~60 funciones propias y de Django. Un parche de Django, Python 3.13 (admitido por `pyproject`) o un cambio inocuo vuelven silenciosamente al camino lento; la huella se calcula dos veces por petición. | `projected_publication.py:176-191` | No encontrado en docs |
| CC-04 | `limited()` usa `REMOTE_ADDR`; detrás de Caddy es siempre la IP del proxy y todos los clientes comparten ventana: 5 altas, 10 logins o 30 subidas cada 15 min para todo el sitio. Un tercero puede bloquear el acceso general. | `apps/core/accounts.py:45-58` | Contrato 01 pospone proxy real; efecto actual en Docker no registrado |
| CC-05 | `detect_matches` recorre todos los Blob `ready` y deserializa su firma en cada procesamiento; `recover_media_jobs` lo reencola cada minuto. El índice `phash` no se usa para recuperar candidatos. | `apps/mediafiles/services.py:239` | Parcialmente (diseño de dependencias) |
| CC-06 | La cola de derechos filtra en Python con `permitted()` (consultas por expediente) antes de paginar. | `apps/safety/rights.py:385` | No encontrado |
| CC-07 | `RateWindow` (HMAC de IP) no se purga nunca: crecimiento indefinido y conservación indefinida de IP seudonimizada. Tampoco hay `clearsessions` ni purga de `AccountToken` caducados. | `apps/core/models.py:77`, `config/settings.py` (Beat) | No encontrado |
| CC-08 | Una única clave Fernet sin `MultiFernet`/identificador: rotar exige recifrar todo. En desarrollo la clave deriva de `SECRET_KEY`. | `apps/safety/crypto.py`, `apps/core/mfa.py` | No encontrado |
| CC-09 | Sin canal real de avisos: en producción el outbox queda desactivado; verificación de edad solo simulada. | `apps/safety/notice_delivery.py:46`, `apps/core/verification_services.py` | Documentado (dependencias externas) |
| CC-10 | Duplicación: 12 tareas de purga casi idénticas; ~86 módulos `rights_*` con flujos acceso/portabilidad paralelos; maquinaria de equivalencia `projected_publication`/`sql_publication` muy costosa de mantener para el beneficio medido. | `apps/safety/tasks.py`, `apps/safety/rights_*`, `apps/listings/*publication*` | — |

## Puntos sólidos

Concurrencia e idempotencia coherentes en todo el código; ausencia de enumeración de cuentas; tokens de un solo uso ligados al estado del usuario; TOTP sin repetición; validación de imágenes contra bombas de descompresión y derivados WebP sin EXIF; supresión que limpia huellas visuales y reintenta el borrado físico; CSP estricta; restricciones de base de datos para invariantes clave (un gestor por persona, un anuncio por persona, tarifa «consultar» sin importe).

## Recomendación técnica

El cuello de botella de CR09-REND-LECTURA es estructural: la regla de publicabilidad vive en Python y se evalúa por candidato y por petición; la estrategia vigente intenta demostrar en tiempo de ejecución que un SQL equivale a esa regla. Se sugiere valorar —como propuesta, sin alterar MOD-04 ni sus criterios— mantener la elegibilidad como estado verificado en escritura (columnas/índices actualizados en las mismas transacciones que hoy cambian autoridad o contenido), de modo que la lectura sea un SQL indexado con count y paginación nativos y la validación completa quede como guardia en la hidratación de la página. CC-04 y CC-07 son correcciones acotadas e independientes.

## Próximos pasos posibles

1. Preparar entorno (Python 3.12, `uv sync --locked`, `docker compose up -d db redis`) y reproducir CC-02/CC-03/CC-04 con pruebas N1.
2. Si Codex lo acepta, registrar CC-04/CC-07 como entregas independientes conforme a MOD-02.
3. Lectura completa de `contratos/10`, matriz83 y módulos `rights_*` para extender este análisis.

## Continuación — investigación del bloqueo de rendimiento (misma sesión)

A petición del usuario, Claude Code (Claude Opus 5.5) preparó el entorno local (uv, Python 3.12, PostgreSQL/Redis de `compose.yaml`), midió el bloqueo sobre 10 000 anuncios sintéticos y prototipó una solución en la rama local `cc/publication-state` (worktree `../web_citas-cc-proto`), **sin integrar** en este árbol. Confirmados con medición: CC-02 (vía de producción 12,2 s por listado), CC-03 (huella ~14 ms ×2 por petición) y un hallazgo nuevo de JIT (2,6 s frente a 0,15 s en `PublicationContext`). Propuesta, diseño, pruebas y límites: `docs/93-propuesta-estado-publicacion-claude-code.md` y `docs/evidencias/cc-estado-publicacion-20261008.json` en esa rama. Requiere decisión del usuario (MOD-05 candidata); no acepta ningún gate.
