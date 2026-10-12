# Arquitectura y operación

Actualizado documentalmente: 2026-10-09. Describe la implementación local; [seguimiento17](17-seguimiento-desarrollo.md) fija aceptación y runtime. Decisiones técnicas en [ADR-001](adr/001-base-tecnica.md), comportamiento requerido en [contrato14](14-contrato-funcional-v1.md) y gates en [contrato16](16-contrato-ejecucion-desarrollo.md).

Inventario de versiones y funciones: [tecnologías utilizadas](tecnologias.md).

## Base acordada

Monolito modular Django con HTML de servidor, plantillas y HTMX local para interacción puntual. PostgreSQL es obligatorio en integración; MongoDB está descartado. No hay una SPA ni una API separada requerida por el contrato.

| Módulo | Responsabilidad |
| --- | --- |
| `core` | Cuentas, sesiones/MFA, agencias, representación y verificación. |
| `catalog` | Catálogo, geografía y preparación comercial de promociones/pedidos. |
| `listings` | Borradores/revisiones, moderación, publicación, descubrimiento y ciclo de vida. |
| `mediafiles` | Validación/procesado de imágenes, derivados y coincidencias. |
| `safety` | Denuncias, reclamaciones, derechos, conservación y recuperación. |

Las rutas de denuncias/derechos se declaran en [safety/urls.py](../apps/safety/urls.py) y se incluyen desde [core/urls.py](../apps/core/urls.py), con los mismos patrones, nombres y orden. Las rutas de cuentas permanecen en `core`.

| Componente | Selección y función |
| --- | --- |
| Django 5.2, Python 3.12 de referencia | Aplicación SSR; rangos permitidos en `pyproject.toml`, resolución de dependencias en `uv.lock`. |
| PostgreSQL 17 | Persistencia, integridad, transacciones, búsqueda y estado derivado de publicación. |
| Celery 5.6 / Redis 7.4 | Worker/Beat y broker; los estados de negocio permanecen en PostgreSQL. |
| Gunicorn WSGI / Caddy | HTML y proxy/estáticos locales mediante Compose. |
| Pillow / ImageHash / OpenCV headless | Derivados y comparación visual, sin identificación biométrica; [contrato de medios](contratos/05-fotografias-coincidencias.md). |
| Almacenamiento | Adaptador compatible con S3 y medios locales de prueba; originales/evidencias privados, derivados públicos sujetos a autorización. Proveedor externo pendiente. |
| Calidad | pytest/PostgreSQL, Playwright/Chromium, Ruff y pip-audit según ADR/lock; workflow existente, con CI externo pendiente según seguimiento. |

`compose.yaml` define base, broker, aplicación, worker, Beat y Caddy. Inicio, migraciones, muestras y comandos en el [README del repositorio](../README.md); no se duplican aquí. No introducir infraestructura nueva sin necesidad medida.

## Lectura pública y estado derivado vigente

[MOD-05](16-contrato-ejecucion-desarrollo.md#17-estado-de-publicación-almacenado--mod-05) almacena `PublicationState` y `PublicationDirty`. La regla nativa de moderación/validación sigue siendo la fuente de verdad.

1. Una escritura de dependencia marca los anuncios afectados mediante triggers en la misma transacción. Migraciones0015/0017 y `DEPENDENCY_TABLES` definen35 tablas con cuatro triggers por tabla.
2. Solo se reutiliza estado limpio de la versión vigente de reglas; código fuente/configuración versionados cambian esa versión. La caducidad se compara en SQL.
3. La lectura usa una instantánea `REPEATABLE READ` para conjunto, recuento y página. Los candidatos desconocidos se evalúan nativamente; los límites y guards activan fallback nativo.
4. La página se hidrata y revalida nativamente antes de presentarse. El recalculador con `SKIP LOCKED` y el barrido de Beat mejoran disponibilidad del estado sin sustituir la autoridad de la regla.

La reparación en GET está desactivada por defecto. [Despliegue local con código nuevo](../README.md#docker) y [restauración MOD-05](85-operacion-registro-recuperacion.md#estado-de-publicación-tras-restaurar-mod-05) incluyen recálculo antes de servir tráfico. La vía `projected_publication` fue retirada; sus diseños/mediciones se consultan solo como historia. La aceptación local de lectura y los límites de carga se registran en seguimiento17, sin acreditar producción.

## Persistencia, caché y cola de tareas

`CACHES.default` usa `DummyCache`, sin almacenamiento. MOD-05 es estado derivado en PostgreSQL con invalidación propia; no una caché de respuestas Django. Los inventarios de derechos incluyen esos registros derivados. Sesiones en base de datos, con comprobaciones de épocas de cuenta/MFA.

Redis mantiene el broker y su persistencia; resultados de tareas ignorados en aplicación, salvo probes sintéticos explícitos. Prefijo/generación y reconstrucción autorizada tras restauración en [recursos87](87-recursos-locales-recuperacion.md) y [operación85](85-operacion-registro-recuperacion.md). Bases lógicas no aíslan memoria/política de expulsión; no usar Redis como autoridad única ni recuperar colas antiguas para desbloquear.

Una futura caché deberá definir exclusiones privadas, autoridad/idioma/versión, TTL e invalidación por retirada, cambio de gestor, consentimiento y derechos, con verificación antes de activarse. Cachés de navegador/proxy/CDN, archivos y copias se inventarían por separado; no se acredita comportamiento de proveedores desde la configuración local.

## Operación y límites

Medios privados y públicos separados; recursos de interfaz servidos localmente y sin rastreadores añadidos. Mantener base/broker sin acceso público, secretos fuera de repositorio/imagen y migraciones controladas. Configuración y ensayos de recuperación no autorizan reabrir producción.

La capacidad se afirma solo para el escenario medido y su fuente; un PASS sintético no acredita proveedores, CDN, cobertura geográfica nacional ni capacidad productiva. Las decisiones externas y de definición del entorno se consultan en la [matriz única de pendientes](83-auditoria-pendientes-cr09.md). No hay proveedores contratados por esta organización.

## Historial de diseño

[Copia íntegra anterior](17-historial/2026-10-09-02-arquitectura-antes-organizacion.md): conserva evaluaciones, alternativas y fuentes consultadas desde 2026-10-03, con sus estados originales. No se reabren selecciones del ADR por un candidato histórico. Copia y huella en [inventario](historial-documentacion.json).


### Recorrido privado de rutas para cobertura — MOD08, 2026-10-11

`compile_coverage` utiliza `_scalar_paths` para enumerar rutas sin crear diccionarios
de valores que ese consumidor descarta. Conserva el recorrido recursivo, errores y
escapes del catálogo público `scalar_fields`, que permanece intacto. Un oráculo
diferencial permanente comprueba su paridad; autoridad, frescura, digests y auditoría
no se reutilizan ni se omiten. La [verificación local](evidencias/mod08-small-paths-20261011.md)
respalda unos 3ms de mejora en la etapa pura del fixture medido, sin beneficio HTTP
ni aceptación de los objetivos contractuales demostrados.


La copia de fuentes mantiene el cursor de servidor y los bloqueos de revisiones, pero difiere siete columnas internas no consumidas además de search_document. Las instancias no salen de source_copy y la salida canónica conserva equivalencia. Beneficio verificado de construcción de modelos, sin mejora HTTP concluyente ni cambios de frescura/autoridad: [evidencia del 2026-10-11](evidencias/mod08-wait-revision-20261011.md).


Investigación arquitectónica del2026-10-11: prototipo **sólo tests** de manifiestos autenticados de datos y páginas cifradas ligadas a huella física completa fresca. Hay señal de coste de etapa, pero no sustitución de fuente, autoridad o endpoint en la arquitectura vigente. Diseño/gates y limitaciones: [brainstorming y viabilidad](evidencias/mod08-brainstorm-web-20261011.md).
