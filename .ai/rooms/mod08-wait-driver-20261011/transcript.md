# MOD08 ejecución fetch y pipeline: diagnóstico y candidata

Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

## 1 · user · authorization

UTC: 2026-10-11T15:38:03.685858+00:00

```text
Excepción persistenteusuario: «Sí, excepción solo para deliberar». Claude exclusivamente revisorCLI sin herramientas ni edición, consumo registrado. Nuevogoalcontinúaindicaciones aceptarbeneficiospequeños, no ampliarpermisos.
```

## 2 · codex · context

UTC: 2026-10-11T15:38:50.080388+00:00

```text
CONTINUACION MOD08. Usuario acepta mejoras pequeñas, no rebajar frescura/seguridad/SLO. Quiero una candidata fundada en coste nuevo observado, no otra propuesta genérica. Codex ejecuta; revisores sin herramientas.
Estado: mejora privada rutas conservada (20.391→17.589ms etapa, 126PASS). HTTP beneficio inconcluyente. Retiradas: memo autoridad/cadena, precargar cuerpos assessment mutables/purga, inline lector hashes SQL con cola p95 peor. No reutilizar esas vías.
Diagnóstico NUEVO terminal runner20261011-153333-078ab072: 4PASS196.69s, 1290 hashes exactos, recursos propios retirados. PostgreSQL17 login runtime separado owner, HTTP real commit verificado, no SQLite, no proveedor real. Fixture1500revisiones/16MiB, historial548eventos256lecturas; cada clon termina556/260. Un worker sync, dos warmups control, controles y observados alternados4+4. Primer arnés sin ServerCursor incompleto preservado; única corrección incluyó Cursor y ServerCursor overrides. Sin cProfile, sin SQL nuevo, sin cambiar GC; GETresolver y conexión de clon previos, scope/install y close incluidos WSGI. Spans ContextVar por función y driver, exclusivos parent-minus-children. Execute/fetch incluyen servidor/red/adaptación/planificador: NO descomposición causal kernel. Pipeline.sync nativo psycopg PostgreSQL, no Redis. No pg_stat_activity, sin medición real bytes TCP. Fetchmany1500 revisiones confirmado. Kernel nativo validado en proceso pytest, no comprobación de identidad independiente por muestra worker en este nuevo arnés. No Caddy/RustFS/cuotas/topología contractual. Historico3.753s navegación NO comparable a estos requests1.6s.
TCP ms control/observado y CPU WSGI ms:
control TCP=1675.331 CPU=935.141
profiled TCP=1563.075 CPU=857.328
control TCP=1599.547 CPU=885.415
profiled TCP=1591.386 CPU=870.175
control TCP=1626.853 CPU=883.687
profiled TCP=1738.898 CPU=993.994
control TCP=1556.864 CPU=840.957
profiled TCP=1631.956 CPU=921.892

source.driver_execute: calls=[20, 20, 20, 20]; wall_ms=[52.636, 56.112, 56.393, 52.642]; cpu_ms=[21.311, 22.674, 22.144, 20.87]; exclusive_wall_ms=[52.636, 56.112, 56.393, 52.642]
source.driver_fetchmany: calls=[25, 25, 25, 25]; wall_ms=[162.444, 175.59, 185.27, 154.767]; cpu_ms=[55.633, 58.704, 63.226, 51.238]; exclusive_wall_ms=[162.444, 175.59, 185.27, 154.767]
source: calls=[1, 1, 1, 1]; wall_ms=[295.339, 321.572, 325.128, 285.799]; cpu_ms=[156.331, 169.078, 166.495, 149.465]; exclusive_wall_ms=[80.259, 89.87, 83.465, 78.39]
runtime_trust: calls=[4, 4, 4, 4]; wall_ms=[36.66, 40.732, 37.811, 37.332]; cpu_ms=[8.634, 8.731, 7.94, 7.854]; exclusive_wall_ms=[1.814, 1.903, 1.76, 1.736]
chain_sources.pipeline_sync: calls=[4, 4, 4, 4]; wall_ms=[73.503, 68.821, 70.713, 72.067]; cpu_ms=[2.353, 2.046, 2.265, 2.56]; exclusive_wall_ms=[73.503, 68.821, 70.713, 72.067]
chain_sources: calls=[4, 4, 4, 4]; wall_ms=[79.928, 75.028, 77.461, 79.267]; cpu_ms=[7.252, 7.038, 7.463, 8.405]; exclusive_wall_ms=[2.845, 2.885, 3.07, 3.211]
validate_chain: calls=[4, 4, 4, 4]; wall_ms=[140.827, 133.688, 140.271, 145.563]; cpu_ms=[26.839, 25.02, 26.448, 29.931]; exclusive_wall_ms=[3.689, 3.36, 3.626, 4.072]
validate_assessment.driver_execute: calls=[8, 8, 8, 8]; wall_ms=[7.579, 6.902, 8.176, 8.678]; cpu_ms=[1.581, 1.319, 1.618, 1.729]; exclusive_wall_ms=[7.579, 6.902, 8.176, 8.678]
validate_assessment.driver_fetchmany: calls=[16, 16, 16, 16]; wall_ms=[0.309, 0.278, 0.321, 0.329]; cpu_ms=[0.31, 0.278, 0.321, 0.329]; exclusive_wall_ms=[0.309, 0.278, 0.321, 0.329]
validate_assessment: calls=[4, 4, 4, 4]; wall_ms=[197.817, 193.155, 199.662, 205.68]; cpu_ms=[49.7, 46.897, 49.394, 53.597]; exclusive_wall_ms=[12.126, 11.263, 12.772, 13.462]

Opinión Codex: existe coste material en fetch source (155–185ms wall,51–63CPU) y pipeline cadena(69–74wall,2–3CPU), pero no demuestra redundancia. Consolidar latest/inspection sólo toca ~8ms SQL explícito de validate_assessment, no toda espera. No memoizar9catálogo ni7tablas ni mover validación fresca. Source servercursor por lotes mantiene memoria ORM acotada; cambiar a clientcursor o subir batch_size puede perder esa garantía. JOINs geográficos traen columnas más allá de code; reducir sólo columnas que jamás consumimos sin cambiar instantánea/punto/bloqueos puede ser candidata pequeña, pero aún sin coste aislado. Catálogo model construction previo ~5ms, no asignar a estos fetch165ms ese coste. Si no hay candidata justificable, pedir UNA medición adicional finita de incertidumbre concreta, no instrumentar todo ni prometer2s.
Código real:
def source_copy(person, listing, case=None):
    if case and case.account_subject_id:
        from .rights_account_copy import source

        return source(case)
    # Same account lock as preference writers; held through snapshot generation.
    if person.subject_id:
        User.objects.select_for_update(no_key=True).get(pk=person.subject_id)
    revisions = []
    if listing:
        # Profile lock prevents a cooperating editor adding another revision mid-copy.
        records = (
            listing.revisions.select_for_update(of=("self",))
            # Generated search vectors can exceed the source text; copies never use them.
            .defer("search_document")
            .select_related("municipality", "postal_code", "zone")
            .order_by("created_at", "pk")
        )
        from .rights_copy_revision_batches import batches

        for revision in batches(records, COPY_REVISION_BATCH_SIZE):
            revisions.append(
                {
                    "revision": str(revision.pk),
                    "status": revision.status,
                    "created_at": revision.created_at.isoformat(),
                    "title": revision.title,
                    "description": revision.description,
                    "description_alternative": revision.description_alternative,
                    "profile_type": revision.profile_type,
                    "content_language": revision.content_language,
                    "categories": [item.slug for item in revision.copy_categories],
                    "services": [item.slug for item in revision.copy_services],
                    "municipality": revision.municipality.code
                    if revision.municipality_id
                    else None,
                    "postal_code": revision.postal_code.code if revision.postal_code_id else None,
                    "zone": revision.zone.code if revision.zone_id else None,
                    "travel_areas": [item.code for item in revision.copy_travel_areas],
                    "spoken_languages": revision.spoken_languages,
                    "days": revision.days,
                    "time_slot": revision.time_slot,
                    "reception": revision.reception,
                    "travel": revision.travel,
                    "contacts": contact_data(person, revision),
                    "images": image_inventory(revision),
                    "rates": [
                        {
                            "concept": rate.concept,
                            "mode": rate.mode,
                            "amount": str(rate.amount) if rate.amount is not None else None,
                            "currency": rate.currency,
                            "duration_minutes": rate.duration_minutes,
                        }
                        for rate in revision.copy_rates
                    ],
                }
            )
    subject = subject_data(person)
    return {
        "schema": "subject-profile-copy-v2",
        "partial": True,
        "simulation": True,
        "pending_review": [
            "image_content",
            "shared_contacts",
            "additional_rights_information",
            *([] if subject["subject_account"] else ["unlinked_subject_account"]),
        ],
        **subject,
        "profile": {
            "alias": person.alias,
            "created_at": person.created_at.isoformat(),
            "listing": {
                "reference": str(listing.pk),
                "status": listing.status,
                "created_at": listing.created_at.isoformat(),
                "published_at": listing.published_at.isoformat() if listing.published_at else None,
                "expires_at": listing.expires_at.isoformat() if listing.expires_at else None,
                "available_until": listing.available_until.isoformat()
                if listing.available_until
                else None,
                "approved_revision": str(listing.approved_revision_id)
                if listing.approved_revision_id
                else None,
            }
            if listing
            else None,
        },
        "revisions": revisions,
    }


@sensitive_variables()
def reviewed_copy(source, value):
    # JSONField accepts objects directly and rejects inv
"""Exact PostgreSQL UUID batches for locked copy rows and their relations."""

from itertools import islice

from django.db.models import F
from django.db.models.expressions import RawSQL

from apps.catalog.models import Category, Municipality, Service
from apps.listings.models import Rate
from apps.mediafiles.models import Photo


def batches(records, size):
    rows = records.iterator(chunk_size=size)
    while batch := list(islice(rows, size)):
        # IDs originate in the locked revision cursor; no SQL text interpolation.
        ids = RawSQL("SELECT unnest(%s::uuid[])", [[row.pk for row in batch]])
        specs = [
            ("copy_categories", Category.objects.order_by("slug"), "revision__pk"),
            ("copy_services", Service.objects.order_by("slug"), "revision__pk"),
            ("copy_travel_areas", Municipality.objects.order_by("code"), "travel_revisions__pk"),
            ("copy_rates", Rate.objects.order_by("pk"), "revision_id"),
            ("copy_photos", Photo.objects.select_related("blob").order_by("created_at", "pk"), "revision_id"),
        ]
        for attribute, queryset, relation in specs:
            grouped = {row.pk: [] for row in batch}
            for item in queryset.filter(**{relation + "__in": ids}).annotate(copy_parent=F(relation)):
                grouped[item.copy_parent].append(item)
            for row in batch:
                setattr(row, attribute, grouped[row.pk])
        yield from batch

def _source_rows_pipeline(statements, raw):
    from contextlib import ExitStack

    actual = {}
    # Same drain/translation ordering as the validation-seal replay pipeline.
    # Results are fully consumed in tab
RESPONDE conciso: (1) qué coste queda localizado sin inferir red/locks; (2) UNA candidata segura con función/statement exacto, trabajo evitado y contraejemplo de frescura/memoria, o ninguna; (3) experimento mínimo/control/criterio rechazo sin cifras de ahorro inventadas. No aceptar SQL directo por wall-CPU ni cambiar objetivos/recursos. Si sugieres narrow only/defer de relaciones requiere enumerar accesos transitivos y asegurar cero lazy-load adicional.

```

## 3 · codex · request

UTC: 2026-10-11T15:38:50.166981+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

CONTINUACION MOD08. Usuario acepta mejoras pequeñas, no rebajar frescura/seguridad/SLO. Quiero una candidata fundada en coste nuevo observado, no otra propuesta genérica. Codex ejecuta; revisores sin herramientas.
Estado: mejora privada rutas conservada (20.391→17.589ms etapa, 126PASS). HTTP beneficio inconcluyente. Retiradas: memo autoridad/cadena, precargar cuerpos assessment mutables/purga, inline lector hashes SQL con cola p95 peor. No reutilizar esas vías.
Diagnóstico NUEVO terminal runner20261011-153333-078ab072: 4PASS196.69s, 1290 hashes exactos, recursos propios retirados. PostgreSQL17 login runtime separado owner, HTTP real commit verificado, no SQLite, no proveedor real. Fixture1500revisiones/16MiB, historial548eventos256lecturas; cada clon termina556/260. Un worker sync, dos warmups control, controles y observados alternados4+4. Primer arnés sin ServerCursor incompleto preservado; única corrección incluyó Cursor y ServerCursor overrides. Sin cProfile, sin SQL nuevo, sin cambiar GC; GETresolver y conexión de clon previos, scope/install y close incluidos WSGI. Spans ContextVar por función y driver, exclusivos parent-minus-children. Execute/fetch incluyen servidor/red/adaptación/planificador: NO descomposición causal kernel. Pipeline.sync nativo psycopg PostgreSQL, no Redis. No pg_stat_activity, sin medición real bytes TCP. Fetchmany1500 revisiones confirmado. Kernel nativo validado en proceso pytest, no comprobación de identidad independiente por muestra worker en este nuevo arnés. No Caddy/RustFS/cuotas/topología contractual. Historico3.753s navegación NO comparable a estos requests1.6s.
TCP ms control/observado y CPU WSGI ms:
control TCP=1675.331 CPU=935.141
profiled TCP=1563.075 CPU=857.328
control TCP=1599.547 CPU=885.415
profiled TCP=1591.386 CPU=870.175
control TCP=1626.853 CPU=883.687
profiled TCP=1738.898 CPU=993.994
control TCP=1556.864 CPU=840.957
profiled TCP=1631.956 CPU=921.892

source.driver_execute: calls=[20, 20, 20, 20]; wall_ms=[52.636, 56.112, 56.393, 52.642]; cpu_ms=[21.311, 22.674, 22.144, 20.87]; exclusive_wall_ms=[52.636, 56.112, 56.393, 52.642]
source.driver_fetchmany: calls=[25, 25, 25, 25]; wall_ms=[162.444, 175.59, 185.27, 154.767]; cpu_ms=[55.633, 58.704, 63.226, 51.238]; exclusive_wall_ms=[162.444, 175.59, 185.27, 154.767]
source: calls=[1, 1, 1, 1]; wall_ms=[295.339, 321.572, 325.128, 285.799]; cpu_ms=[156.331, 169.078, 166.495, 149.465]; exclusive_wall_ms=[80.259, 89.87, 83.465, 78.39]
runtime_trust: calls=[4, 4, 4, 4]; wall_ms=[36.66, 40.732, 37.811, 37.332]; cpu_ms=[8.634, 8.731, 7.94, 7.854]; exclusive_wall_ms=[1.814, 1.903, 1.76, 1.736]
chain_sources.pipeline_sync: calls=[4, 4, 4, 4]; wall_ms=[73.503, 68.821, 70.713, 72.067]; cpu_ms=[2.353, 2.046, 2.265, 2.56]; exclusive_wall_ms=[73.503, 68.821, 70.713, 72.067]
chain_sources: calls=[4, 4, 4, 4]; wall_ms=[79.928, 75.028, 77.461, 79.267]; cpu_ms=[7.252, 7.038, 7.463, 8.405]; exclusive_wall_ms=[2.845, 2.885, 3.07, 3.211]
validate_chain: calls=[4, 4, 4, 4]; wall_ms=[140.827, 133.688, 140.271, 145.563]; cpu_ms=[26.839, 25.02, 26.448, 29.931]; exclusive_wall_ms=[3.689, 3.36, 3.626, 4.072]
validate_assessment.driver_execute: calls=[8, 8, 8, 8]; wall_ms=[7.579, 6.902, 8.176, 8.678]; cpu_ms=[1.581, 1.319, 1.618, 1.729]; exclusive_wall_ms=[7.579, 6.902, 8.176, 8.678]
validate_assessment.driver_fetchmany: calls=[16, 16, 16, 16]; wall_ms=[0.309, 0.278, 0.321, 0.329]; cpu_ms=[0.31, 0.278, 0.321, 0.329]; exclusive_wall_ms=[0.309, 0.278, 0.321, 0.329]
validate_assessment: calls=[4, 4, 4, 4]; wall_ms=[197.817, 193.155, 199.662, 205.68]; cpu_ms=[49.7, 46.897, 49.394, 53.597]; exclusive_wall_ms=[12.126, 11.263, 12.772, 13.462]

Opinión Codex: existe coste material en fetch source (155–185ms wall,51–63CPU) y pipeline cadena(69–74wall,2–3CPU), pero no demuestra redundancia. Consolidar latest/inspection sólo toca ~8ms SQL explícito de validate_assessment, no toda espera. No memoizar9catálogo ni7tablas ni mover validación fresca. Source servercursor por lotes mantiene memoria ORM acotada; cambiar a clientcursor o subir batch_size puede perder esa garantía. JOINs geográficos traen columnas más allá de code; reducir sólo columnas que jamás consumimos sin cambiar instantánea/punto/bloqueos puede ser candidata pequeña, pero aún sin coste aislado. Catálogo model construction previo ~5ms, no asignar a estos fetch165ms ese coste. Si no hay candidata justificable, pedir UNA medición adicional finita de incertidumbre concreta, no instrumentar todo ni prometer2s.
Código real:
def source_copy(person, listing, case=None):
    if case and case.account_subject_id:
        from .rights_account_copy import source

        return source(case)
    # Same account lock as preference writers; held through snapshot generation.
    if person.subject_id:
        User.objects.select_for_update(no_key=True).get(pk=person.subject_id)
    revisions = []
    if listing:
        # Profile lock prevents a cooperating editor adding another revision mid-copy.
        records = (
            listing.revisions.select_for_update(of=("self",))
            # Generated search vectors can exceed the source text; copies never use them.
            .defer("search_document")
            .select_related("municipality", "postal_code", "zone")
            .order_by("created_at", "pk")
        )
        from .rights_copy_revision_batches import batches

        for revision in batches(records, COPY_REVISION_BATCH_SIZE):
            revisions.append(
                {
                    "revision": str(revision.pk),
                    "status": revision.status,
                    "created_at": revision.created_at.isoformat(),
                    "title": revision.title,
                    "description": revision.description,
                    "description_alternative": revision.description_alternative,
                    "profile_type": revision.profile_type,
                    "content_language": revision.content_language,
                    "categories": [item.slug for item in revision.copy_categories],
                    "services": [item.slug for item in revision.copy_services],
                    "municipality": revision.municipality.code
                    if revision.municipality_id
                    else None,
                    "postal_code": revision.postal_code.code if revision.postal_code_id else None,
                    "zone": revision.zone.code if revision.zone_id else None,
                    "travel_areas": [item.code for item in revision.copy_travel_areas],
                    "spoken_languages": revision.spoken_languages,
                    "days": revision.days,
                    "time_slot": revision.time_slot,
                    "reception": revision.reception,
                    "travel": revision.travel,
                    "contacts": contact_data(person, revision),
                    "images": image_inventory(revision),
                    "rates": [
                        {
                            "concept": rate.concept,
                            "mode": rate.mode,
                            "amount": str(rate.amount) if rate.amount is not None else None,
                            "currency": rate.currency,
                            "duration_minutes": rate.duration_minutes,
                        }
                        for rate in revision.copy_rates
                    ],
                }
            )
    subject = subject_data(person)
    return {
        "schema": "subject-profile-copy-v2",
        "partial": True,
        "simulation": True,
        "pending_review": [
            "image_content",
            "shared_contacts",
            "additional_rights_information",
            *([] if subject["subject_account"] else ["unlinked_subject_account"]),
        ],
        **subject,
        "profile": {
            "alias": person.alias,
            "created_at": person.created_at.isoformat(),
            "listing": {
                "reference": str(listing.pk),
                "status": listing.status,
                "created_at": listing.created_at.isoformat(),
                "published_at": listing.published_at.isoformat() if listing.published_at else None,
                "expires_at": listing.expires_at.isoformat() if listing.expires_at else None,
                "available_until": listing.available_until.isoformat()
                if listing.available_until
                else None,
                "approved_revision": str(listing.approved_revision_id)
                if listing.approved_revision_id
                else None,
            }
            if listing
            else None,
        },
        "revisions": revisions,
    }


@sensitive_variables()
def reviewed_copy(source, value):
    # JSONField accepts objects directly and rejects inv
"""Exact PostgreSQL UUID batches for locked copy rows and their relations."""

from itertools import islice

from django.db.models import F
from django.db.models.expressions import RawSQL

from apps.catalog.models import Category, Municipality, Service
from apps.listings.models import Rate
from apps.mediafiles.models import Photo


def batches(records, size):
    rows = records.iterator(chunk_size=size)
    while batch := list(islice(rows, size)):
        # IDs originate in the locked revision cursor; no SQL text interpolation.
        ids = RawSQL("SELECT unnest(%s::uuid[])", [[row.pk for row in batch]])
        specs = [
            ("copy_categories", Category.objects.order_by("slug"), "revision__pk"),
            ("copy_services", Service.objects.order_by("slug"), "revision__pk"),
            ("copy_travel_areas", Municipality.objects.order_by("code"), "travel_revisions__pk"),
            ("copy_rates", Rate.objects.order_by("pk"), "revision_id"),
            ("copy_photos", Photo.objects.select_related("blob").order_by("created_at", "pk"), "revision_id"),
        ]
        for attribute, queryset, relation in specs:
            grouped = {row.pk: [] for row in batch}
            for item in queryset.filter(**{relation + "__in": ids}).annotate(copy_parent=F(relation)):
                grouped[item.copy_parent].append(item)
            for row in batch:
                setattr(row, attribute, grouped[row.pk])
        yield from batch

def _source_rows_pipeline(statements, raw):
    from contextlib import ExitStack

    actual = {}
    # Same drain/translation ordering as the validation-seal replay pipeline.
    # Results are fully consumed in tab
RESPONDE conciso: (1) qué coste queda localizado sin inferir red/locks; (2) UNA candidata segura con función/statement exacto, trabajo evitado y contraejemplo de frescura/memoria, o ninguna; (3) experimento mínimo/control/criterio rechazo sin cifras de ahorro inventadas. No aceptar SQL directo por wall-CPU ni cambiar objetivos/recursos. Si sugieres narrow only/defer de relaciones requiere enumerar accesos transitivos y asegurar cero lazy-load adicional.

```

## 4 · claude · opinion

UTC: 2026-10-11T15:40:01.656122+00:00

````text
# Opinión MOD08: candidata condicionada a un inventario previo

## (1) Coste localizado

**Hechos medidos (4 muestras, 1 worker, 4+4 alternados):**
- **Fetch de `source`**: `driver_fetchmany` va de 155 a 185 ms de wall con 51–63 ms de CPU. Unos 100–120 ms del span no son CPU del proceso. Las 25 llamadas son estables.
- **`source` exclusivo**: 78–90 ms de wall. Su CPU exclusiva, que es total menos hijos, ronda 79–86 ms (p. ej. 156,3−21,3−55,6). El tramo es prácticamente todo CPU Python y queda **fuera** de los spans de driver.
- **`chain_sources.pipeline_sync`**: 69–74 ms de wall con 2–3 ms de CPU. Es espera pura dentro del span. No discrimino si viene de servidor, red, planificador o bloqueo, y no lo atribuyo.
- **`validate_assessment`**: unos 198 ms en total. Su SQL explícito suma unos 8 ms y su exclusivo unos 12 ms. El resto está en `validate_chain` y `runtime_trust`.
- **TCP control/observado** (1557–1675 frente a 1563–1739): los rangos se solapan. La sobrecarga de la instrumentación no es concluyente, así que no la resto.

**Hipótesis no demostradas:**
- Qué fracción del fetch de `source` corresponde a la sentencia del cursor de revisiones y cuál a las 5 consultas de `batches`. Los spans no etiquetan la sentencia.
- Que el exclusivo de 80 ms sea construcción de modelos ORM. También podría ser `contact_data`, `image_inventory` o `isoformat` si no tienen span propio.

**Evidencia faltante:**
- Valor de `COPY_REVISION_BATCH_SIZE`.
- Cuerpos de `contact_data`, `image_inventory` y `subject_data`.
- Columnas reales de `Municipality`, `PostalCode` y `Zone`.
- Bytes por fila.

## (2) Una candidata, condicionada

**Función y sentencia:** `source_copy`, en el queryset `records`. Es la sentencia SELECT del server cursor de revisiones con `select_related("municipality", "postal_code", "zone")` y `FOR NO KEY... FOR UPDATE OF self`.

**Cambio:** ampliar el `defer` existente sólo a columnas de los **modelos relacionados**:

```
.defer("search_document", "municipality__<col>", "postal_code__<col>", "zone__<col>", ...)
```

Se conservan `pk` y `code` de cada relacionado. **No** se toca ningún campo de `Revision`, así que no hace falta enumerar los accesos a la revisión.

**Trabajo evitado:** transferencia, adaptación de psycopg y asignación en `from_db` de las columnas relacionadas no consumidas. Se haría en 1500 filas por cada join existente. No cuantifico el ahorro.

**Lo que no cambia:**
- Misma sentencia y mismo número de statements.
- Mismo snapshot y la misma cláusula `OF self`, por lo que los bloqueos de revisiones no cambian. Los catálogos nunca estuvieron bloqueados.
- Server cursor y tamaño de lote intactos, con lo que la memoria sigue acotada o baja.
- No toca frescura, validación ni catálogo memoizado.

**Precondición estática:** si no se cumple, la candidata queda anulada y la decisión es **ninguna**.
1. Esos tres modelos tienen columnas no triviales además de `pk` y `code`, como geometría o textos.
2. `code` es un campo concreto y no una property que lea otros campos.
3. Hay una enumeración transitiva de **todo** acceso a `revision.municipality`, `revision.postal_code` y `revision.zone` en:
   - `contact_data`, `image_inventory` y cualquier función que reciban `revision`;
   - `__str__`/`__repr__` usados en logs o excepciones, y `from_db` o `__init__` personalizados;
   - señales.

   El resultado debe ser que sólo se lee `.code`.

**Contraejemplos:**
- **Frescura y coste (lazy-load):** si `contact_data` lee `revision.municipality.name`, el acceso a un campo diferido dispara `refresh_from_db`. Eso es un SELECT por fila: hasta unas 1500 consultas, fuera del snapshot del lote y sin bloqueo. Daría peor latencia y una lectura semánticamente distinta. Es motivo de rechazo inmediato.
- **Memoria:** ninguno por diseño, porque se transportan menos columnas. Sólo invalidaría el cambio si alguien sustituye `iterator(chunk_size)` o el batch para «compensar». No está permitido.
- **Beneficio nulo:** si las columnas extra son estrechas, el coste sigue y la candidata no aporta nada. La precondición 1 lo filtra sin ejecutar.

**Descartado explícitamente:**
- `only()` en `Revision`: exige enumerar los accesos de funciones que no veo.
- `.only("pk","code")` en `copy_travel_areas`: es una segunda sentencia con el mismo riesgo transitivo; no la mezclo en la misma prueba.
- Client cursor o batch mayor: pierde la cota de memoria.
- Tocar `pipeline_sync` o `validate_assessment`: no hay evidencia de redundancia.

## (3) Experimento mínimo

**Paso 0 (estático, sin ejecución):** inventario de columnas de los tres modelos y la enumeración de accesos del punto 2. Si falla, se cierra con «ninguna candidata» y se aplica lo de abajo.

**Paso 1 (Codex, mismo arnés):**
- PostgreSQL 17 con login runtime separado, HTTP real, mismo fixture 1500/16 MiB, 1 worker sync y 2 warmups.
- Alternado 4 control + 4 candidata, **con recursos frescos por clon**.
- Única adición: etiquetar los spans `driver_execute`/`fetchmany` por sentencia de origen (cursor de revisiones frente a cada spec). No es SQL nuevo; sólo mueve el atributo del span.

**Rechazo si ocurre cualquiera de estas condiciones:**
1. Los recuentos de `source.driver_execute` difieren de 20 o los de `driver_fetchmany` difieren de 25 en alguna muestra. Indicaría lazy-load o un cambio de lote.
2. Alguno de los 1290 hashes difiere, o falla alguno de los 126 PASS más los 4 PASS terminales.
3. Los wall y CPU del fetch etiquetado del cursor de revisiones no quedan, en las 4 muestras, por debajo del mínimo de control de la misma corrida. Se exige no solapamiento, sin umbral inventado.
4. El pico de memoria del worker (tracemalloc o RSS, misma métrica en ambos brazos) es mayor en la candidata.
5. El kernel nativo no se reverifica en esta corrida.

Ni el resultado favorable es PASS ni autoriza nada. No se extrapola a p95 contractual: no hay Caddy, RustFS, cuotas ni topología.

**Si se cierra sin candidata:** la única medición adicional justificada es el mismo paso 1 **sin** el cambio, sólo con el etiquetado por sentencia. Responde una incertidumbre concreta: qué sentencia concentra los 155–185 ms de fetch. Con ese reparto se decide si existe alguna candidata en `batches` o se cierra MOD08 en este frente.

**Decisión finita propuesta:** Paso 0, y después Paso 1 con la candidata o con sólo el etiquetado. Nada más en esta iteración.
````

## 5 · codex · request

UTC: 2026-10-11T15:41:01.261452+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

CONTINUACION MOD08. Usuario acepta mejoras pequeñas, no rebajar frescura/seguridad/SLO. Quiero una candidata fundada en coste nuevo observado, no otra propuesta genérica. Codex ejecuta; revisores sin herramientas.
Estado: mejora privada rutas conservada (20.391→17.589ms etapa, 126PASS). HTTP beneficio inconcluyente. Retiradas: memo autoridad/cadena, precargar cuerpos assessment mutables/purga, inline lector hashes SQL con cola p95 peor. No reutilizar esas vías.
Diagnóstico NUEVO terminal runner20261011-153333-078ab072: 4PASS196.69s, 1290 hashes exactos, recursos propios retirados. PostgreSQL17 login runtime separado owner, HTTP real commit verificado, no SQLite, no proveedor real. Fixture1500revisiones/16MiB, historial548eventos256lecturas; cada clon termina556/260. Un worker sync, dos warmups control, controles y observados alternados4+4. Primer arnés sin ServerCursor incompleto preservado; única corrección incluyó Cursor y ServerCursor overrides. Sin cProfile, sin SQL nuevo, sin cambiar GC; GETresolver y conexión de clon previos, scope/install y close incluidos WSGI. Spans ContextVar por función y driver, exclusivos parent-minus-children. Execute/fetch incluyen servidor/red/adaptación/planificador: NO descomposición causal kernel. Pipeline.sync nativo psycopg PostgreSQL, no Redis. No pg_stat_activity, sin medición real bytes TCP. Fetchmany1500 revisiones confirmado. Kernel nativo validado en proceso pytest, no comprobación de identidad independiente por muestra worker en este nuevo arnés. No Caddy/RustFS/cuotas/topología contractual. Historico3.753s navegación NO comparable a estos requests1.6s.
TCP ms control/observado y CPU WSGI ms:
control TCP=1675.331 CPU=935.141
profiled TCP=1563.075 CPU=857.328
control TCP=1599.547 CPU=885.415
profiled TCP=1591.386 CPU=870.175
control TCP=1626.853 CPU=883.687
profiled TCP=1738.898 CPU=993.994
control TCP=1556.864 CPU=840.957
profiled TCP=1631.956 CPU=921.892


MEDIANAS cuatro instrumentadas (ms), detalle muestras conservado:
source.driver_execute calls=20 wall=54.377 cpu=21.728 exclusive_wall=54.377
source.driver_fetchmany calls=25 wall=169.017 cpu=57.168 exclusive_wall=169.017
source calls=1 wall=308.455 cpu=161.413 exclusive_wall=81.862
runtime_trust calls=4 wall=37.572 cpu=8.287 exclusive_wall=1.787
chain_sources.pipeline_sync calls=4 wall=71.390 cpu=2.309 exclusive_wall=71.390
chain_sources calls=4 wall=78.364 cpu=7.357 exclusive_wall=2.978
validate_chain calls=4 wall=140.549 cpu=26.643 exclusive_wall=3.658
validate_assessment.driver_execute calls=8 wall=7.877 cpu=1.600 exclusive_wall=7.877
validate_assessment.driver_fetchmany calls=16 wall=0.315 cpu=0.316 exclusive_wall=0.315
validate_assessment calls=4 wall=198.739 cpu=49.547 exclusive_wall=12.449

Opinión Codex: existe coste material en fetch source (155–185ms wall,51–63CPU) y pipeline cadena(69–74wall,2–3CPU), pero no demuestra redundancia. Consolidar latest/inspection sólo toca ~8ms SQL explícito de validate_assessment, no toda espera. No memoizar9catálogo ni7tablas ni mover validación fresca. Source servercursor por lotes mantiene memoria ORM acotada; cambiar a clientcursor o subir batch_size puede perder esa garantía. JOINs geográficos traen columnas más allá de code; reducir sólo columnas que jamás consumimos sin cambiar instantánea/punto/bloqueos puede ser candidata pequeña, pero aún sin coste aislado. Catálogo model construction previo ~5ms, no asignar a estos fetch165ms ese coste. Si no hay candidata justificable, pedir UNA medición adicional finita de incertidumbre concreta, no instrumentar todo ni prometer2s.

Código exacto consulta source y consumidores transitorios:
def source_copy(person, listing, case=None):
    if case and case.account_subject_id:
        from .rights_account_copy import source

        return source(case)
    # Same account lock as preference writers; held through snapshot generation.
    if person.subject_id:
        User.objects.select_for_update(no_key=True).get(pk=person.subject_id)
    revisions = []
    if listing:
        # Profile lock prevents a cooperating editor adding another revision mid-copy.
        records = (
            listing.revisions.select_for_update(of=("self",))
            # Generated search vectors can exceed the source text; copies never use them.
            .defer("search_document")
            .select_related("municipality", "postal_code", "zone")
            .order_by("created_at", "pk")
        )
        from .rights_copy_revision_batches import batches

        for revision in batches(records, COPY_REVISION_BATCH_SIZE):
            revisions.append(
                {
                    "revision": str(revision.pk),
                    "status": revision.status,
                    "created_at": revision.created_at.isoformat(),
                    "title": revision.title,
                    "description": revision.description,
                    "description_alternative": revision.description_alternative,
                    "profile_type": revision.profile_type,
                    "content_language": revision.content_language,
                    "categories": [item.slug for item in revision.copy_categories],
                    "services": [item.slug for item in revision.copy_services],
                    "municipality": revision.municipality.code
                    if revision.municipality_id
                    else None,
                    "postal_code": revision.postal_code.code if revision.postal_code_id else None,
                    "zone": revision.zone.code if revision.zone_id else None,
                    "travel_areas": [item.code for item in revision.copy_travel_areas],
                    "spoken_languages": revision.spoken_languages,
                    "days": revision.days,
                    "time_slot": revision.time_slot,
                    "reception": revision.reception,
                    "travel": revision.travel,
                    "contacts": contact_data(person, revision),
                    "images": image_inventory(revision),
                    "rates": [
                        {
                            "concept": rate.concept,
                            "mode": rate.mode,
                            "amount": str(rate.amount) if rate.amount is not None else None,
                            "currency": rate.currency,
                            "duration_minutes": rate.duration_minutes,
                        }
                        for rate in revision.copy_rates
                    ],
                }
            )

"""Exact PostgreSQL UUID batches for locked copy rows and their relations."""

from itertools import islice

from django.db.models import F
from django.db.models.expressions import RawSQL

from apps.catalog.models import Category, Municipality, Service
from apps.listings.models import Rate
from apps.mediafiles.models import Photo


def batches(records, size):
    rows = records.iterator(chunk_size=size)
    while batch := list(islice(rows, size)):
        # IDs originate in the locked revision cursor; no SQL text interpolation.
        ids = RawSQL("SELECT unnest(%s::uuid[])", [[row.pk for row in batch]])
        specs = [
            ("copy_categories", Category.objects.order_by("slug"), "revision__pk"),
            ("copy_services", Service.objects.order_by("slug"), "revision__pk"),
            ("copy_travel_areas", Municipality.objects.order_by("code"), "travel_revisions__pk"),
            ("copy_rates", Rate.objects.order_by("pk"), "revision_id"),
            ("copy_photos", Photo.objects.select_related("blob").order_by("created_at", "pk"), "revision_id"),
        ]
        for attribute, queryset, relation in specs:
            grouped = {row.pk: [] for row in batch}
            for item in queryset.filter(**{relation + "__in": ids}).annotate(copy_parent=F(relation)):
                grouped[item.copy_parent].append(item)
            for row in batch:
                setattr(row, attribute, grouped[row.pk])
        yield from batch

Pipeline completo:
def _source_rows_pipeline(statements, raw):
    from contextlib import ExitStack

    actual = {}
    # Same drain/translation ordering as the validation-seal replay pipeline.
    # Results are fully consumed in table order; no domain checks are advanced.
    with connection.wrap_database_errors, ExitStack() as cursors:
        with raw.pipeline() as pipeline:
            pending = []
            for statement, params in statements:
                cursor = cursors.enter_context(connection.cursor())
                cursor.execute(statement, params)
                pending.append(cursor)
            pipeline.sync()
            for table, cursor in zip(TABLES, pending):
                actual.update({(table, pk): digest for pk, digest in cursor.fetchall()})
    return actual

contact_data usa revision.phone y revision.whatsapp; image_inventory usa copy_photos/blob, no campos adicionales revision. Municipality fields=id,code,name,province_id,source_id,active; PostalCode=id,code,source_id,public_safe; Zone=id,code,name,municipality_id,source_id,active. Sólo code accedido por source.

Responde con UNA candidata segura o ninguna, función/statement exacto, trabajo evitado, contraejemplos de frescura/memoria, experimento mínimo y descarte. No inferir red/locks ni ahorros ms. Si only/defer, accesos transitivos y cero lazy-load extra. Si ninguna, UNA incertidumbre/medición finita útil.

Revisión Claude recibida (opinión no evidencia): propuso sólo defer de columnas geográficas no usadas, condicionado a columnas no triviales y enumeración transitiva; si falla inventario, ninguna candidata y etiquetar cursor revisiones vs consultas batches en un próximo diagnóstico. Correcciones Codex: no existe FOR NO KEY en revisión, sólo select_for_update(of=self). No exigir igualdad de1290hashes de baseline contra candidata que cambia fuente intencionalmente: congelar/verificar cada variante. Su regla de no solapamiento4+4 no reemplaza protocolo estadístico establecido; no repetir126 tests antes de tener beneficio. Fuente responde ahora: tamaño1000, columnas geográficas estrechas(ninguna geometría/texto grande), code concreto, contact_data sólo phone/whatsapp, image_inventorycopy_photos. MÁS IMPORTANTE populate crea1500Revision sin municipality/postal_code/zone: todas las3FKsonNULL. La candidata defer geografía no elimina1500instancias porque no se instancian esas relaciones NULL. No inventar fixture nuevo para perseguir efecto. No implementar esa propuesta bajo evidencia actual.
¿Existe otra candidata con el código suministrado y estos datos o cierras sin candidata? Si propones rows.values/proyección estructural, debe preservar todos campos consumidos, snapshot/bloqueos/batching1000 y firmas/canonical/errores, no materializar16MiB enteros en driver cliente ni cachear autoridad. No basta asumir80ms=ORM: otros procesamientos incluidos. Una medición adicional sólo si responde incertidumbre nueva que cambia decisión.

```

## 6 · notebook · error

UTC: 2026-10-11T15:41:04.987588+00:00

```text
Empty answer; inspect raw artifact
```

## 7 · codex · opinion

UTC: 2026-10-11T15:42:00.951036+00:00

```text
MOD08 continuación. Objetivos2s navegación/5s descargas siguen, usuario acepta beneficios pequeños sin rebajar frescura/seguridad. Tu conocimiento previo del notebook puede estar desactualizado: usa estos hechos de código/medición nuevos; no reutilizar memo autoridad/cadena, precargar assessment mutable/purga ni inline lectorSQL (retirado por cola peor).
Diagnóstico terminal PostgreSQL17 HTTPreal,4PASS196.69s,1290hashes exactos, recursos retirados. Unworker sync,1500revisiones/16MiB,historial548eventos. Cuatro controles alternados4observados,clones equivalentes; commits ownerconfirmados+8eventos/+4lecturas. Sin cProfile ni cambiar GC. Driver Cursor+ServerCursor execute/fetch, Pipeline.sync y salida, funciones ContextVar. WSGIcontrolCPU841–935ms,observado857–994: no beneficio inferible.
Resultados4observadas:
source total286–325ms wall/149–169CPU;20execute53–56wall/21–23CPU;25fetchmany155–185wall/51–63CPU;source exclusivo78–90wall/77–88CPU.
validate_assessment4llamadas suman193–206wall/47–54CPU; SQLdirecto8execute7–9wall y16fetchmany0.3ms; resto require_runtime_chain.
Dentro cadena: runtime_trust4llamadas37–41wall/8–9CPU. chain_sources.pipeline_sync4llamadas69–74wall/2–3CPU. Estos spans solapan sus padres: NO sumarlos. Execute/fetch/sync son cliente+driver+servidor/red/planificador mezclados, no atribuir causa ni locks. No pg_stat_activity/bytesTCP,ni topología contractual;3.753s histórico no comparable.
Código real source_copy: listing.revisions.select_for_update(of=('self',)).defer('search_document').select_related('municipality','postal_code','zone').order_by('created_at','pk'). Se consume batches(records,1000). batches usa records.iterator(chunk_size=1000),islice1000, y5 consultas ORM frescas por lote a Category,Service,Municipality(travel),Rate,Photo.select_related(blob), todas filtradas por ids UUID y agrupadas con copy_parent. No cache.
source construye dict de todos campos exportados status,created_at,title,description,description_alternative,profile_type,content_language,spoken_languages,days,time_slot,reception,travel; sólo code geográfico; contact_data usa phone/whatsapp; image_inventorycopy_photos/blob. Kernelvalidado pytest, sin identidad worker por muestra en este arnés.
Pipelinecadena existente abre raw.pipeline(),encola7SELECT con cursor.execute,sync(),fetchall7,resuelve dict,SALEpipeline. Verifica íntegra cadena y fuentes cada página; no redundancia de seguridad demostrada.
Opinión Claude: defer columnasgeográficas inútiles condicionado a columnasgrandes; de fallar inventario, etiquetarfetch revisiones versus5relaciones. ObjeciónCodex: columnasestrechas y1500revisiones creadas con3FKgeográficas NULL, no1500instanciasgeográficas queahorrar. No aplicarcomo solución. Originalparcial Cursor-onlyfetch<1ms indica interéscursorservidor pero distintosrequests: no restar como medicióncausal. Sourceexclusivo~80ms NO prueba80msORM.
Pide UNA candidata sustentada o ninguna, trabajoevitado, contraejemplofrescura/memoria, experimento mínimo y descarte. Si nohay, una incertidumbrenueva y mediciónque cambiedecisión. No más propuestas generales ni prometerahorrossegundos. Rows.values si se propone exige equivalencia campos/errores/firmas,bloqueos/snapshot/1000batch,evitar lazyloads y mantenerboundedmemory. Codex opina priorizar etiquetadodefetch existente antesdereescribir.

```

## 8 · codex · request

UTC: 2026-10-11T15:42:01.052039+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

MOD08 continuación. Objetivos2s navegación/5s descargas siguen, usuario acepta beneficios pequeños sin rebajar frescura/seguridad. Tu conocimiento previo del notebook puede estar desactualizado: usa estos hechos de código/medición nuevos; no reutilizar memo autoridad/cadena, precargar assessment mutable/purga ni inline lectorSQL (retirado por cola peor).
Diagnóstico terminal PostgreSQL17 HTTPreal,4PASS196.69s,1290hashes exactos, recursos retirados. Unworker sync,1500revisiones/16MiB,historial548eventos. Cuatro controles alternados4observados,clones equivalentes; commits ownerconfirmados+8eventos/+4lecturas. Sin cProfile ni cambiar GC. Driver Cursor+ServerCursor execute/fetch, Pipeline.sync y salida, funciones ContextVar. WSGIcontrolCPU841–935ms,observado857–994: no beneficio inferible.
Resultados4observadas:
source total286–325ms wall/149–169CPU;20execute53–56wall/21–23CPU;25fetchmany155–185wall/51–63CPU;source exclusivo78–90wall/77–88CPU.
validate_assessment4llamadas suman193–206wall/47–54CPU; SQLdirecto8execute7–9wall y16fetchmany0.3ms; resto require_runtime_chain.
Dentro cadena: runtime_trust4llamadas37–41wall/8–9CPU. chain_sources.pipeline_sync4llamadas69–74wall/2–3CPU. Estos spans solapan sus padres: NO sumarlos. Execute/fetch/sync son cliente+driver+servidor/red/planificador mezclados, no atribuir causa ni locks. No pg_stat_activity/bytesTCP,ni topología contractual;3.753s histórico no comparable.
Código real source_copy: listing.revisions.select_for_update(of=('self',)).defer('search_document').select_related('municipality','postal_code','zone').order_by('created_at','pk'). Se consume batches(records,1000). batches usa records.iterator(chunk_size=1000),islice1000, y5 consultas ORM frescas por lote a Category,Service,Municipality(travel),Rate,Photo.select_related(blob), todas filtradas por ids UUID y agrupadas con copy_parent. No cache.
source construye dict de todos campos exportados status,created_at,title,description,description_alternative,profile_type,content_language,spoken_languages,days,time_slot,reception,travel; sólo code geográfico; contact_data usa phone/whatsapp; image_inventorycopy_photos/blob. Kernelvalidado pytest, sin identidad worker por muestra en este arnés.
Pipelinecadena existente abre raw.pipeline(),encola7SELECT con cursor.execute,sync(),fetchall7,resuelve dict,SALEpipeline. Verifica íntegra cadena y fuentes cada página; no redundancia de seguridad demostrada.
Opinión Claude: defer columnasgeográficas inútiles condicionado a columnasgrandes; de fallar inventario, etiquetarfetch revisiones versus5relaciones. ObjeciónCodex: columnasestrechas y1500revisiones creadas con3FKgeográficas NULL, no1500instanciasgeográficas queahorrar. No aplicarcomo solución. Originalparcial Cursor-onlyfetch<1ms indica interéscursorservidor pero distintosrequests: no restar como medicióncausal. Sourceexclusivo~80ms NO prueba80msORM.
Pide UNA candidata sustentada o ninguna, trabajoevitado, contraejemplofrescura/memoria, experimento mínimo y descarte. Si nohay, una incertidumbrenueva y mediciónque cambiedecisión. No más propuestas generales ni prometerahorrossegundos. Rows.values si se propone exige equivalencia campos/errores/firmas,bloqueos/snapshot/1000batch,evitar lazyloads y mantenerboundedmemory. Codex opina priorizar etiquetadodefetch existente antesdereescribir.

```

## 9 · notebook · opinion

UTC: 2026-10-11T15:43:01.072371+00:00

```text
### **1. Distinción de Hechos, Hipótesis y Evidencia Faltante**

* **Hechos Medidos (Observados en el arnés de prueba):**
  * **Desglose de `source`:** Wall total de 286–325 ms (CPU 149–169 ms). Se compone de 20 `execute` (53–56 ms wall / 21–23 ms CPU), 25 `fetchmany` (155–185 ms wall / 51–63 ms CPU) y un tiempo exclusivo de procesamiento/armado de diccionarios de 78–90 ms wall (77–88 ms CPU).
  * **Desglose de `validate_assessment`:** 4 llamadas suman 193–206 ms wall (47–54 ms CPU). El SQL directo consume 8 `execute` (7–9 ms) y 16 `fetchmany` (0.3 ms). La latencia restante proviene de `require_runtime_chain`, donde destacan `runtime_trust` (37–41 ms wall / 8–9 ms CPU) y `pipeline_sync` (69–74 ms wall / 2–3 ms CPU). Estos spans solapan a sus padres y **no deben sumarse**.
  * **Estructura y datos de `source_copy`:** Procesa 1500 revisiones en lotes de 1000 usando `iterator(chunk_size=1000)`. Cada lote ejecuta 5 consultas ORM secundarias a `Category`, `Service`, `Municipality`, `Rate` y `Photo`. Las 1500 revisiones tienen sus 3 FKs geográficas (`municipality`, `postal_code`, `zone`) en `NULL`.
  * **Invalidez de `defer` geográfico:** La propuesta de diferir columnas geográficas no genera ahorro porque las FKs están en `NULL` y las columnas son estrechas.
  * **Impacto en WSGI:** WSGI control muestra CPU de 841–935 ms frente a 857–994 ms observado (delta indeterminado dentro del ruido, sin beneficio inferible).

* **Hipótesis:**
  * Los 155–185 ms de `fetchmany` en `source` se reparten entre la latencia de red/driver al traer las 1500 revisiones con `select_for_update(of=('self',))` y la ejecución repetitiva de las 5 consultas ORM secundarias por lote.
  * El tiempo exclusivo de `source` (~80 ms CPU) corresponde al costo de instanciación de objetos ORM Django y la construcción manual de los diccionarios exportados.

* **Evidencia Faltante (Incertidumbres críticas):**
  * **Atribución fina de `fetchmany`/`execute`:** Falta la telemetría etiquetada que desglose cuántos ms de los 25 `fetchmany` corresponden a la consulta principal de revisiones versus las 5 consultas ORM secundarias por lote.
  * **Métricas de servidor y red:** Sin datos de `pg_stat_activity`, contención de locks en PostgreSQL 17 ni bytes TCP transferidos entre el cliente psycopg3 y la base de datos.

---

### **2. Dictamen Técnico y Decisión Finita**

* **Decisión:** **NINGUNA candidata de reescritura de código, cambio SQL ni modificación de la cadena de validación está sustentada actualmente.**
* **Trabajo Evitado:**
  * Evitar la reescritura prematura de `source_copy` hacia `values()` o SQL directo.
  * Evitar la alteración o simplificación de `require_runtime_chain` / `pipeline_sync`.
  * Descartar definitivamente la modificación de `defer()` en campos geográficos.
* **Contraejemplos (Riesgos de Frescura y Memoria):**
  * **Frescura / Coherencia:** Omitir o precargar en memoria las 5 consultas secundarias de relaciones o reducir las comprobaciones de la cadena de confianza violaría la garantía de frescura y el aislamiento transaccional bajo `select_for_update(of=('self',))`, permitiendo exportar estados mutados sin respaldo de integridad.
  * **Memoria Acotada:** Sustituir la iteración por lotes (`iterator(chunk_size=1000)`) por una evaluación e instanciación masiva de todas las relaciones en una sola consulta rompería la cota de memoria acotada (16 MiB por worker), generando picos descontrolados de asignación en Python.

---

### **3. Experimento Mínimo, Incertidumbre Nueva y Criterio de Descarte**

* **Incertidumbre Nueva:** ¿El tiempo dominante en `fetchmany` (155–185 ms) pertenece al transporte y materialización de la consulta principal de revisiones o a las 5 consultas secundarias agrupadas por lote?
* **Experimento Mínimo Requerido (Sin alterar lógica de negocio):**
  * Etiquetar en el trazador del arnés existente las operaciones de `execute`/`fetchmany` separando explícitamente:
    1. `span.fetch_revisions_main`: Consulta y fetch del QuerySet principal de revisiones.
    2. `span.fetch_relations_batch`: Las 5 consultas ORM de relaciones ejecutadas en cada lote de 1000.
* **Criterio de Descarte / Cambio de Decisión:**
  * **Aprobación de reescritura futura:** Si la medición etiquetada demuestra que **≥70% del tiempo de `fetchmany` (≥125 ms)** es consumido por las 5 consultas secundarias de relaciones por lote, se justificará diseñar una candidata que reemplace esas 5 consultas ORM por un `values_list` agrupado explícitamente por lote.
  * **Descarte definitivo:** Si `span.fetch_revisions_main` representa la casi totalidad del tiempo, o si el cuello de botella se confirma como CPU exclusiva de Python (~80 ms), se descarta cualquier reescritura SQL/ORM y se acepta el perfil actual como el límite estructural de la plataforma.

---

*Nota de control: Esta intervención constituye una opinión técnica de diagnóstico basada estrictamente en los hechos suministrados; no representa autorización de cambios ni aprobación PASS.*
```

## 10 · codex · request

UTC: 2026-10-11T15:50:23.925272+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Última revisión de esta sala. Prueba nueva terminal runner20261011-154421-99415089:4PASS193.91s,1307hashes exactos independientes antes documentar, PostgreSQL/TCP/commit real propios con mismahistoria548eventos/1500revisiones16MiB,4control+4observados. Cursor y ServerCursor ahora separados; Revision.from_db tiene span; kernel worker native-sealed/manifestigual8muestras. Nada productivo nuevo.
4muestras instrumentadas source.server_fetchmany3llamadas[1000,500,0]: wall139.828,148.729,145.815,138.927ms; CPU54.867,58.953,56.775,55.455ms. Source.driver_fetchmany22llamadas wall0.493,0.466,0.650,0.614ms (relaciones/resto). Source.driver_execute19calls wall60.935,49.790,51.636,54.815;server_execute1wall2.496,2.521,3.101,2.701. Source.revision_hydrate1500calls wall25.129,26.052,29.210,27.193/CPU25.229,26.148,29.305,27.279. Wall/CPU fronteras distintas por orden reloj, acumulado1500 explica~0.1msCPU>wall; no esperar negativo ni restaroverhead entrecampañas. Sourceexclusivoresidual58–66ms incluye armado/fueraSQL/overhead del observador, no declarartodoORM.
Notebook recibido tras consulta larga inválida/reformulación breve: ninguna reescritura justificada, etiquetarfetchmain vsrelaciones. Ahora hecho:main domina. Corrijo sus conclusiones falsas: 16MiB es tamaño corpus no cotaRAM; primacía mainfetch NO demuestra límite estructural plataforma ni descarta todaoptimSQL/ORM. Su umbral70%/125ms arbitrario noadoptado. Geografías NULL haceninútil tu candidata de columnasgeográficas para estecoste; models camposestrechos.
Codex considera UNA prueba de etapa original/candidata de bajo riesgo, sin aplicar a producción hasta verresultado: en source_copy ampliar defer('search_document') a campos de Revision jamás consumidos, nogeografía. Mantener todos camposusados, servercursor/tamaño1000/ofself/querytiming/freshauthority/firmas. Noeliminar instancias ni usarvalues/rawSQL. Propuesta omitir source_revision(FK),step,edit_version,telegram,contact_exposure_accepted,publisher_acceptance(FK),updated_at. NO omitir listing_id (ModelIterable known_related_objects podría lazy-load),manager_version ni geofks. No tocar modelos niotroscallers.
Revision concreta: idUUID,listingFK,source_revisionFK,manager_version,status,step,edit_version,title,description,content_language,description_alternative,search_documentgenerated,profile_type,municipalityFK,postal_codeFK,zoneFK,spoken_languagesJSON,daysJSON,time_slot,reception,travel,phone,whatsapp,telegram,contact_exposure_accepted,publisher_acceptanceFK,created_at,updated_at; manytomany categories/services/travelareas no columnasconcretas.
source_copy actualmente: listing.revisions.select_for_update(of=('self',)).defer('search_document').select_related('municipality','postal_code','zone').order_by('created_at','pk'),batches(records,1000). Consume pk,status,created_at,title,description,description_alternative,profile_type,content_language,municipality_id/municipality.code,postal_code_id/postal_code.code,zone_id/zone.code,spoken_languages,days,time_slot,reception,travel; contact_data usa phone/whatsapp; image_inventory usa copy_photos/blob; batches usa pk/copy_parent, asigna copy_categories/services/travelareas/rates/photos. No Model.from_db overrides ni post_init/pre_init receivers encontrados enapps. Consulta relacionada knownlisting requiere listing_id conservado. Todosvalidadoresestado/fingerprintotrosquerys quedan intactos.
Experimento propuesto antes tocarprod: constructor ORMreal sobre1500rowspredecodificadas de PostgreSQL propio,20paresABBAx10/warmup2modos, materializaciónDB/fijacióncampos fuerareloj; originalfrom_db vsnames/valuesfiltrados7campos. Igualdadattrsconsumidos. Criterio predeclarado>=15/20paresfavorableswallCPU y4bloquespositivos; sin mínimoabsolutoms; sin inventar efectoHTTP. Si fallarechazo sinruncompleto; siPASS luego equivalencia source_copy salidas/queries/batches sobrePG yN2 afectada+HTTP propio. Registrar memoria aparte sólosiCPUpositiva. La hidraciónobservada25ms es presupuesto modestoeinstrumentado no ahorrogarantizado.
¿Ves una infracción real de semántica/frescura/lazyloading o este experimento mínimo es razonable? Si no, rechaza con contraejemplo delcódigo. Si sí, señala controles imprescindibles. Noexigir quehashesbaselineycandidataidénticos siarchivo cambiadoa propósito; congelar cada variante.

```

## 11 · claude · opinion

UTC: 2026-10-11T15:51:13.873961+00:00

```text
# Revisión del experimento: `defer` ampliado en `source_copy`

## Dictamen

Con el contexto que aportas no veo una infracción de frescura, bloqueo ni lazy-loading. El experimento mínimo me parece razonable si incluye los controles de abajo. Es una opinión, no un PASS ni una autorización.

Hay dos riesgos semánticos que no puedo descartar con lo que tengo:

- `save()` sobre las instancias fuente.
- Clonación de la instancia fuente.

Si cualquiera de los dos ocurre, la propuesta cambia de comportamiento de forma silenciosa.

## Hechos medidos (de tu informe)

- `server_fetchmany` domina: 139–149 ms wall y 55–59 ms CPU.
- `revision_hydrate` en 1500 llamadas: 25–29 ms wall y CPU.
- Residual exclusivo de Source: 58–66 ms. No es atribuible entero al ORM.
- `source_copy` consume la lista de atributos que enumeras. Los siete candidatos no aparecen en ella.
- `listing_id` se conserva para `known_related_objects`.
- No hay overrides de `from_db` ni receivers `pre_init`/`post_init`.

## Hipótesis y lo que no cubren

- **Ahorro esperado.** 7 de 27 columnas concretas no implica un 26 % de los 25 ms. El coste por campo no es uniforme. En el camino con `DEFERRED`, `Model.__init__` ya itera la ruta posicional con centinela. Lo esperable son pocos ms, quizá cero.
- **Alcance del microbenchmark.** Con filas predecodificadas solo mide `from_db`/`__init__`. No mide el ahorro de transferencia ni la decodificación de `updated_at` (timestamptz) y de los UUID FK en el driver. Ese ahorro, si existe, cae dentro de `server_fetchmany` y no lo verás. Me parece correcto no inventarlo, pero tampoco hay que concluir "no hay ahorro en fetch" si el micro falla.
- **Comparabilidad.** Ambas variantes pasan por la rama "menos valores que `concrete_fields`", porque `search_document` ya está diferido. La comparación es justa en ese sentido.

## Contraejemplos que deben descartarse antes de aceptar

1. **`save()` en una instancia fuente con campos diferidos.** Si la instancia sale de BD con campos diferidos, Django fija `update_fields` a los campos cargados. Entonces:
   - `updated_at` (`auto_now`) deja de actualizarse, sin error.
   - `step` y `edit_version` no se escriben aunque se modifiquen.
   - Si el código hace `rev.status = X; rev.save()` sobre la fuente, el resultado cambia.

   Tu inventario dice qué se lee, no qué se guarda. Hay que verificar que no existe ningún `.save()`, `.full_clean()` ni `refresh_from_db()` parcial sobre las instancias del iterador.
2. **Clonación vía la instancia fuente.** Patrones como `pk=None; save()`, `copy.copy(rev)`, `model_to_dict(rev)`, iterar `_meta.concrete_fields` o un serializador harían una de dos cosas:
   - disparar N lazy-loads (con N+1 bajo `FOR UPDATE`), o
   - copiar `DEFERRED` o valores ausentes.

   Si `copy_parent` construye la copia con kwargs explícitos, no hay problema. Hay que confirmarlo leyendo el código.
3. **Accesos indirectos.** `__str__`/`__repr__` en logs o excepciones, receivers `pre_save`/`post_save` (solo revisaste `init`), `clean()`, fingerprints que reciban la instancia y no un dict, y pickling o caché. Basta uno que toque `step`, `telegram` o `source_revision` para producir una consulta por fila.
4. **Bloqueo.** `of=('self',)` bloquea la fila completa en PostgreSQL sin importar las columnas proyectadas. Un lazy-load posterior leería dentro de la misma transacción con la fila bloqueada. No pierde frescura, pero sí rendimiento. Por eso el control decisivo es el conteo de queries, no la igualdad de valores.

## Controles imprescindibles

**Micro (etapa 1)**

- La variante "original" debe usar exactamente el `init_list` y los valores que produce hoy el queryset real. No uses uno reconstruido a mano. Igual para la candidata, derivándolo del queryset con el nuevo `defer`. Compara `query.get_loaded_field_names()` (o equivalente) contra la lista esperada.
- Comprueba `get_deferred_fields()` en cada instancia. Debe valer `{search_document}` en la original y esa unión con los siete en la candidata.
- Comprueba la igualdad de los atributos consumidos, `listing_id` incluido.
- El span de `Revision.from_db` debe estar activo o inactivo por igual en ambas variantes.
- Añade un control A/A con el mismo esquema ABBA. Si da ≥15/20 "favorables", el criterio está sesgado por orden o calor y el resultado A/B no es interpretable.
- Congela cada variante con su hash propio. Bastan hashes estables por variante; no hace falta que sean idénticos entre variantes.

**Equivalencia (etapa 2, solo si la etapa 1 pasa)**

- Captura las queries de `source_copy` completo en ambas variantes:
  - Mismo número de queries.
  - Mismo SQL salvo la lista de columnas del SELECT principal.
  - Ninguna query adicional por `pk` sobre `revision`.

  Es el detector directo de lazy-loads.
- Prueba un caso que fuerce la ruta de guardado o clonación si existe. Si no existe, deja constancia de la búsqueda (grep de `save(`, `model_to_dict`, `_meta.`, `copy`) como evidencia, no como supuesto.
- Compara las salidas persistidas por fila: copias, relaciones M2M asignadas, `rates`/`photos` y `updated_at` de la fuente antes y después.
- Haz una autoridad fresca por run. No reutilices resultados de 20261011-154421.

**HTTP (etapa 3)**

- Ejecuta N2 afectada más HTTP propio con muestras nuevas. El micro no autoriza ninguna conclusión sobre el p95 contractual.

## Evidencia faltante

- Inventario de escrituras sobre las instancias fuente.
- Implementación de `copy_parent` y de la construcción de copias.
- Receivers `pre_save`/`post_save` de Revision.
- Métodos `__str__` y `clean` del modelo.

## Decisión propuesta (finita)

- **Si** la búsqueda de los contraejemplos 1–3 en el código no encuentra nada, **entonces** se ejecuta la etapa 1 con los controles anteriores.
  - Si falla, o si el A/A no es neutro, se rechaza y se cierra la línea ORM para este coste.
  - Si pasa, se ejecutan la etapa 2 y luego la 3, sin tocar producción hasta el resultado de la 3.
- **Si** aparece cualquier `save()` o clonación sobre la fuente, se rechaza la propuesta tal cual. Como mínimo habría que excluir `updated_at`, `step` y `edit_version` de la lista y repetir la evaluación.
```

## 12 · codex · decision

UTC: 2026-10-11T16:35:57.491739+00:00

```text
Decisión Codex comprobada localmente, no opinión externa ni aceptación MOD08.
# MOD-08 — Diagnóstico de esperas y proyección de revisiones — 2026-10-11

## Decisión local

Conservar la ampliación de `defer()` en `apps/safety/rights_exports.py::source_copy` como beneficio parcial de construcción de modelos. No declarar resuelto el presupuesto HTTP ni sumar este ahorro a mediciones históricas de otro alcance. Mantener la optimización previa de rutas. No cachear autoridad, cadena, catálogos o permisos; no adelantar lecturas mutables ni modificar bloqueos, aislamiento o criptografía.

## Diagnóstico y deliberación

Sala `.ai/rooms/mod08-wait-driver-20261011`: dos revisiones Claude exclusivamente sin herramientas/edición; Notebook recibió el enfoque y los datos de la primera medición. Una consulta extensa falló al validar argumentos; la reformulación breve recibió respuesta. Cuatro turnos externos agotados; opiniones no equivalen a evidencia. El contexto inicial truncaba una función; la revisión final recibió el candidato completo. Se rechazaron la supuesta cuota de memoria de 16 MiB y la inferencia de límite inevitable de plataforma.

La primera captura omitía ServerCursor y quedó como diagnóstico incompleto. La corrección y una segunda descomposición distinguen Cursor, ServerCursor y Revision.from_db. En cuatro observaciones intrusivas del mismo fixture, el fetch principal de revisiones realiza tres llamadas con 1000, 500 y 0 filas: 138,927–148,729 ms wall, 54,867–58,953 ms CPU de hilo. Las otras 22 llamadas fetchmany suman 0,466–0,650 ms. La hidratación de 1500 revisiones ocupa 25,129–29,210 ms wall bajo hooks. La barrera pipeline de la cadena ocupa aproximadamente 63,557–72,747 ms. Estas medidas inclusivas/exclusivas no son ahorros multiplicables ni separan transporte, ejecución de PostgreSQL, adaptación, locks o desplanificación. No se midieron syscalls ni bytes TCP; el residual no es exclusivamente ORM. El exceso wall frente a CPU no demuestra E/S de red.

Fuentes numéricas: [captura corregida](mod08-wait-driver-20261011.json), [descomposición](mod08-wait-split-20261011.json). Ambas verificaciones reales PostgreSQL terminaron con cuatro pruebas PASS, runners `20261011-153333-078ab072` y `20261011-154421-99415089`.

## Cambio y conservación de garantías

Se difieren siete columnas no consumidas por la copia: source_revision, step, edit_version, telegram, contact_exposure_accepted, publisher_acceptance y updated_at, además del search_document ya diferido. Se conservan listing_id, manager_version, claves geográficas y todas las columnas utilizadas. No se modifican el cursor de servidor, su chunk de 1000, el orden, FOR UPDATE OF self, el punto de lectura o los controles de frescura. Las instancias internas no se guardan, clonan ni se entregan al llamador; sale el mismo documento.

Existe un receptor post_init global en rights_validation_seal; se preserva su ejecución. Sus expiraciones expires_at/receipt_expires_at/valid_until no son campos diferidos por este cambio. La equivalencia verifica el documento canónico completo, ausencia de consultas diferidas adicionales, mismos parámetros y número de consultas y el mismo tramo SQL FROM/bloqueo. Sólo cambia la proyección SELECT de revisiones; no se modifica ningún updated_at.

## Medición aislada

Filas reales decodificadas desde PostgreSQL, 1500 revisiones y contenido sintético calibrado de 16 MiB. Se mide exclusivamente construcción mediante Revision.from_db, sin SQL, validación o preparación dentro de los relojes. Veinte pares A/A y veinte A/B alternados ABBA, con calentamiento simétrico y sin cambiar GC.

| Alcance y mediana | Antes | Después | Diferencia | Porcentaje |
| --- | ---: | ---: | ---: | ---: |
| Construcción 1500 revisiones, wall | 19,537191 ms (0,019537 s) | 17,470186 ms (0,017470 s) | 2,067006 ms | 10,58 % |
| Construcción 1500 revisiones, CPU hilo | 19,536036 ms | 17,460796 ms | 2,075240 ms | 10,62 % |

A/B gana 17/20 pares wall y CPU y los cuatro bloques cronológicos; A/A gana 12/20 en ambas métricas y supera el control neutral preregistrado. Esto justifica retener el beneficio de etapa. No se extrapola al servicio, no mide memoria ni adaptación del driver. [Datos](mod08-revision-defer-20261011.json), runner `20261011-155320-446ba755`: 1 PASS.

## HTTP: resultado inconcluso

Veinte pares reales TCP de clones independientes, una instancia Gunicorn sync, kernel nativo sellado verificado por muestra, 1500 revisiones/16 MiB. Cada petición registra cuatro lecturas reales y commits; cabeza/eventos 548→556 y lecturas 256→260. La mejora previa de rutas está presente en ambos brazos. No es la topología completa contractual ni la población histórica de 383 lotes.

| Medida TCP | Antes | Después | Diferencia observada |
| --- | ---: | ---: | ---: |
| Mediana | 1691,390432 ms (1,691390 s) | 1678,775960 ms (1,678776 s) | 12,614472 ms (0,75 %) |
| p95 interpolado, n=20 por brazo | 2079,933066 ms (2,079933 s) | 1815,410986 ms (1,815411 s) | 264,522080 ms (12,72 %) |

Sólo 11/20 pares TCP y CPU favorecen el cambio; hay bloques negativos. No cumple evidencia de beneficio HTTP consistente. Tampoco activa el descarte preregistrado por regresión (15/20 pérdidas y todos los bloques negativos, o mediana y p95 ambos >5 % peores). Ausencia de ese descarte no demuestra no inferioridad. No afirmar mejora causal del p95 ni cumplimiento del objetivo de 2 s. [Datos](mod08-revision-http-20261011.json).

## Verificación y fallos preservados

Equivalencia inicial: runner `20261011-155855-a0872543`, 3 PASS. El primer combinado `20261011-160045-77fc3354` agotó 900 s; no se contabiliza como PASS. El seguimiento `20261011-161740-abbc2d44` confirmó HTTP PASS y dos ERROR de preparación de almacenamiento: faltaba la imagen RustFS fijada por digest. El conjunto de ese runner es ERROR, aunque su caso HTTP tiene JUnit terminal sin error/fallo.

Se descargó únicamente la dependencia RustFS ya fijada en el proyecto, sin modificar fixtures, límites, controles o datos. Se repitieron los 123 casos de corrección del combinado, incluyendo los dos errores, con tres workers pytest y aislamiento por worker. No se cambió el worker Gunicorn de rendimiento ni se ejecutó otro benchmark/modelo a la vez. Runner `20261011-162456-8718be57`: **123 PASS, 0 errores, 0 fallos, 0 skips**, 544,757 s de pytest, además de Ruff, documentación, Django, migraciones y preparación del kernel. Esto verifica seguridad/carreras/sellos/almacenamiento real de la selección; no significa aceptación completa de MOD-08.

Auditoría independiente posterior: los 1316 archivos del manifiesto coinciden, producto rights_exports.py SHA256 `942f355f701ec6c0c88571abaa02f6e9c2e0aa7b7c7df9eebdf7866fc8d7e985`. Resultado y JUnit: `artifacts/local-ci/20261011-162456-8718be57/`. Contenedores propios PostgreSQL/Redis eliminados y sin contenedores de almacenamiento de estas pruebas. Sin commit, push, publicación o contratación.

## Distancia al objetivo y parada de este ciclo

Las últimas mediciones históricas completas siguen siendo navegación p95 3,753392 s frente a 2 s (faltan 1,753392 s), JSON 6,930455 s frente a 5 s (faltan 1,930455 s) y binario 7,317947 s frente a 5 s (faltan 2,317947 s). Descargas n=3/n=8: población insuficiente. Ninguna cifra de esta etapa se resta de esos valores.

Se cierra la sala con el beneficio pequeño verificado y HTTP inconcluso. No repetir el mismo experimento ni iniciar otra candidata sin una hipótesis nueva contrastable: la transferencia/adaptación de las 1500 revisiones merece la siguiente investigación, pero todavía no hay una sustitución de semántica segura y medible. La reducción de consultas secundarias no aborda el coste principal observado.

```
