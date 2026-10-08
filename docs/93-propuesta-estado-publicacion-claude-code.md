# Propuesta técnica: estado de publicación almacenado con invalidación por triggers

Fecha: 2026-10-08. Autoría: **Claude Code** (CLI de Anthropic), modelo **Claude Opus 5.5** (`claude-opus-5-5`), a petición directa del usuario («investigación profunda, experimenta y estudia una solución» para el bloqueo de CR09). Base: `8f461b9`. Código del prototipo en la rama local `cc/publication-state` (worktree `../web_citas-cc-proto`), **sin integrar**.

Naturaleza: diagnóstico medido y prototipo verificado localmente. **No** es aceptación de CR09-REND-LECTURA, R5/R6, N3, GS-01 ni de ningún gate. Contradice la orientación vigente de MOD-04 («no añadir caché persistente ni proyección persistida como parche en este ciclo»), por lo que adoptarla requiere una modificación de contrato autorizada por el usuario (candidata **MOD-05**). Los criterios de [revisión del benchmark](criterios-revision-benchmark-carga.md) ya prevén esta vía si se aportan «dependencias completas e invalidación o actualización que evite exposición tras revocaciones, restricciones y expiraciones», con pruebas. Esta propuesta intenta satisfacer exactamente esa condición. Mediciones completas en [evidencia](evidencias/cc-estado-publicacion-20261008.json).

## 1. Diagnóstico medido

Entorno: Python 3.12.15, Django 5.2.17, PostgreSQL 17 de `compose.yaml`; base `test_promotion_gate_cc` creada con `seed_demo` + `populate(10000)` + `ANALYZE`. Mediciones en proceso con `django.test.Client` (mediana) salvo donde se indica carga HTTP.

| Petición (10 000 anuncios) | Vía rápida actual (desarrollo) | Vía nativa actual (**la que usa producción**) | Prototipo |
| --- | ---: | ---: | ---: |
| Listado | 377–418 ms | **12,2–12,4 s** | 157–168 ms |
| Búsqueda | 380–405 ms | 12,5–12,6 s | 172–185 ms |
| Ficha | 67 ms | 80 ms | 75 ms |

Causas observadas:

1. **Coste proporcional al catálogo en cada lectura.** La regla de publicabilidad (`moderation.publicly_visible` → `validate_submission` + formularios) se evalúa en cada petición para todos los candidatos antes de contar y paginar. La vía rápida la traduce a una sola sentencia SQL que tarda ~172 ms de ejecución y ~17 ms de planificación para 10 000 filas: los joins terminan hacia los 40 ms y el resto se va en evaluar las pruebas de contenido por fila (regex, JSON, subconsultas). Componer esas expresiones en el ORM cuesta además ~100 ms de Python.
2. **Producción nunca usa la vía rápida.** `projected_publication.supported()` devuelve `False` con `settings.PRODUCTION`, con el filtro `checked` y con promociones. En esos modos el listado cuesta ~12 s por petición: con 4 workers es una capacidad de ~0,3 peticiones/s, frente a las 20 exigidas.
3. **Huella de definiciones por petición.** `definitions_digest()` cuesta ~14 ms y se calcula dos veces por petición (~28 ms del presupuesto de ~200 ms). Además depende del bytecode: un parche de Django o Python 3.13, admitido por `pyproject.toml`, desactiva la vía rápida sin aviso.
4. **JIT de PostgreSQL.** Las lecturas de `PublicationContext` con subconsultas correlacionadas activan la compilación JIT: 200 filas tardan 2,6–2,7 s con JIT y 134–171 ms sin él. El proyecto ya lo desactiva localmente en `page_read`; la vía nativa general no lo hace.

Bajo carga (Gunicorn con 4 workers síncronos, 20 peticiones/s durante 60 s, generador propio), el código actual en su vía rápida da **p95 31,7 s**: solo 773 de 1200 peticiones terminan dentro de la ventana y la cola tarda 33,6 s en vaciarse. Es coherente con el FAIL registrado en el seguimiento.

## 2. Diseño

Idea: la publicabilidad solo cambia cuando cambian datos (o el código y la configuración, o el tiempo). Se calcula al escribir y se guarda; la lectura la consulta con SQL indexable. La exactitud se protege con tres reglas:

- **Invalidación en la base de datos, no en la aplicación.** Un trigger de sentencia por evento (INSERT/UPDATE/DELETE con tablas de transición, más TRUNCATE) en **cada una de las 33 tablas** que lee la regla nativa marca los anuncios afectados en `listings_publicationdirty`, dentro de la misma transacción que el cambio. Ninguna ruta de código (vistas, admin, `bulk_update`, SQL crudo, tareas) puede saltárselo. La lista sale del SQL que ejecuta realmente `publicly_visible` (30 tablas capturadas), más `catalog_postalcode`, su M2M y `catalog_zone`.
- **Un resultado guardado solo se usa si es fiable.** `PublicationState` (resultado sin la caducidad, más los flags de `checked`) se usa si el anuncio no está sucio y se calculó con la versión de reglas vigente: un hash de `definitions_digest()`, `PRODUCTION` y `VERIFICATION_PROVIDER`, calculado una vez por proceso. Si no, el anuncio es «desconocido» y se evalúa **con la regla nativa en la propia petición**. La caducidad siempre se compara en SQL.
- **El recalculador solo afecta al rendimiento.** `refresh()` toma lotes con `FOR UPDATE SKIP LOCKED`, evalúa con la regla nativa sin modificarla y solo borra la marca si su `generation` no cambió. Una escritura concurrente reinsertará la marca: el upsert atómico de PostgreSQL espera al bloqueo del recalculador y la deja pendiente. Hay una prueba específica de esta carrera.

Lectura (`state_page`):

1. **Reparación en lectura.** Si hay pocos anuncios sucios, la petición recalcula hasta 24 en una transacción corta propia. Así un cambio lo paga una sola petición y no todas, y no hace falta esperar al worker.
2. **Instantánea única.** Una transacción `REPEATABLE READ READ ONLY` comparte la lectura del conjunto sucio, los desconocidos, la evaluación nativa de esos desconocidos, el recuento y la página.
3. **Población.** Población = (estado fiable y elegible, no sucio, con `checked` aplicado sobre flags) ∪ (desconocidos visibles según la regla nativa). Se cuenta y se pagina en SQL con filas estrechas. `DISTINCT` solo se aplica si hay joins multivaluados (categorías o servicios).
4. **Guarda nativa de la página.** Las 24 filas se hidratan y revalidan con `PublicationContext` y `publicly_visible`, como hace la vía proyectada actual. Si alguna falla, se marca y se usa la vía existente.
5. **Respaldos.** Con más de 48 desconocidos entre los candidatos, o más de 1000 sucios en total, se delega en la vía existente. Las promociones, que solo existen en modo de pruebas, también siguen en la vía existente.

Archivos del prototipo: `apps/listings/models.py` (dos modelos), `apps/listings/migrations/0015_publication_state.py` (tablas, 132 triggers, autovacuum agresivo en la tabla de sucios, marcado inicial de todo), `apps/listings/publication_state.py` (versión de reglas, recálculo, reparación, lectura), una integración de 10 líneas en `discovery.results` y `tests/test_publication_state.py`.

## 3. Verificación realizada

**Exactitud** (PostgreSQL real, `seed_demo`):

- Equivalencia byte a byte del HTML con la vía nativa en ES/EN para 7 combinaciones de consulta (texto, página 2, `checked` simple y múltiple, filtro), en modo normal y con `PRODUCTION=True`, antes y después del recálculo.
- 16 mutaciones semánticas, cada una sin recálculo previo y después de él: consentimiento revocado, edad fallida, teléfono no verificado, agencia pendiente, autorización eliminada, comprobación fallida, anuncio pausado, caducado, texto con URL, tarifa inválida, foto retirada, blob fallido, categoría inactiva, ciudad inactiva, categoría desvinculada y sustitución de condiciones de publicación.
- Completitud: toda tabla que la regla nativa lee en ejecución tiene trigger. Esta prueba falla automáticamente si alguien añade una dependencia sin cubrirla.
- Tablas de `safety` (retención por privacidad, restricción, reintroducción, subida de rectificación y la cadena propuesta → revisión → notificación → ejecución → disposición): cada eslabón marca el anuncio correcto por sí solo. Se comprueba con filas mínimas bajo FK diferidas y reversión.
- Carrera entre recalculador y escritura concurrente: el anuncio queda sucio y no se expone.
- Regresión funcional del proyecto: 64 pruebas de descubrimiento, ciclo de vida, favoritos, denuncias, restricciones, SEO, sitemaps, liberación por finalidad, promociones y dependencias de validación, incluidas 7 de navegador Chromium. Todas pasan junto con las 21 propias.

**Rendimiento** (Gunicorn con 4 workers, 20 peticiones/s, generador de lazo abierto propio sin subidas, procesos con nice 5):

| Escenario | Peticiones | Errores | p95 | Vaciado de cola |
| --- | ---: | ---: | ---: | ---: |
| Código actual (vía rápida), 60 s | 1200 | 0 | 31,7 s | 33,6 s |
| Prototipo, 60 s | 1200 | 0 | 343 ms | 0,23 s |
| Prototipo, 120 s, 2 escrituras/s, sin reparación en lectura | 2400 | 0 | 6,3 s | 5,6 s |
| Prototipo, 120 s, 2 escrituras/s, con reparación en lectura | 2400 | 0 | 487 ms | 0,35 s |

La tercera fila es instructiva: sin reparación, cada anuncio sucio añade 45–80 ms a cada listado (un `PublicationContext` completo). Eso empuja la ocupación por encima del 100 % y la cola se dispara. Es un precipicio de capacidad, no un fallo de exactitud.

## 4. Límites y riesgos

- **No es el arnés contractual.** Las ventanas son de 60–120 s, sin uploads, con un solo host y con procesos de nice 5. R5 y R6 siguen sin ejecutarse con este código. La ocupación estimada es de ~70 %: el margen es menor del deseable si el host oficial es más lento, que es lo que sugieren sus medianas de 0,6–0,7 s.
- **Cambios globales.** Un documento legal o un cambio del catálogo marcan todos los anuncios. Mientras haya más de 1000 sucios, la lectura delega en la vía existente, que en producción tarda ~12 s. El recálculo completo cuesta 14,9 s en un proceso y se puede repartir entre varios workers gracias a `SKIP LOCKED`. Recomendación: recalcular dentro de la misma operación administrativa (transacción o mantenimiento programado) o mapear con precisión las tablas de catálogo (categoría → revisiones que la usan) en lugar de marcar todo.
- **Despliegue.** Una nueva versión de reglas deja todo desconocido hasta recalcular. El procedimiento debe ejecutar `refresh` con el código nuevo antes de dirigir tráfico, o versionar el estado por clave compuesta.
- **Restauraciones.** `pg_restore --disable-triggers` o `session_replication_role=replica` omiten los triggers. Tras una restauración hay que marcar todo (añadirlo al runbook de recuperación). `TRUNCATE` sí está cubierto.
- **Tiempo.** Solo `expires_at` depende del reloj y se evalúa en SQL. Si en el futuro una regla usara `now()` para otra cosa, habría que tratarla igual.
- **Escrituras en peticiones GET.** La reparación en lectura escribe estado derivado durante peticiones GET. Se puede desactivar (`PUBLICATION_STATE_READ_REPAIR=0`) a cambio de depender del worker.
- **Pruebas que cambian de expectativa.** Varias pruebas de la vía proyectada afirman `route == "projection"`; el contenido coincide, pero la etiqueta pasa a `state`. Hay que adaptarlas o retirar la vía proyectada si se adopta esta.
- **Riesgo nuevo de catálogo grande.** `SearchForm` pinta todas las opciones geográficas en cada listado. Con el catálogo real (~8 000 municipios) será un coste dominante independiente de esta propuesta.

## 5. Siguientes pasos propuestos

1. Decisión del usuario sobre MOD-05: adoptar el estado almacenado con estas garantías, o mantener MOD-04.
2. Si se adopta: integrar con una tarea Celery de recálculo (on_commit + Beat como red de seguridad), comando de gestión `refresh_publication_state`, paso de despliegue y de restauración, mapeo preciso de catálogo, adaptación de las pruebas de ruta y retirada o congelación de `projected_publication`/`sql_publication`.
3. Reducir margen: pintado del formulario de búsqueda (~40–50 ms), hidratación de página (~15 ms de SQL) y omitir la consulta de desconocidos cuando el conjunto sucio esté vacío.
4. Ejecutar R5 con el arnés oficial y, solo con PASS, R6, sin sumar estas mediciones a las suyas.
