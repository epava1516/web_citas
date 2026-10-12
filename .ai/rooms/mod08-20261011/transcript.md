# Salón MOD08 — Codex, Claude y NotebookLM

Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

## 1 · user · authorization

UTC: 2026-10-11T13:16:55.636805+00:00

```text
Usuario: «Sí, excepción solo para deliberar». Autoriza CLI Claude instalado como revisor sin herramientas ni edición, con registro de consumo. No modifica contrato/adaptador externo ni autoriza otras delegaciones. 2026-10-11.
```

## 2 · codex · context

UTC: 2026-10-11T13:16:55.687813+00:00

```text
Primera deliberación conjunta MOD08. Codex modera; tu función es revisión independiente sin herramientas.
HEAD 7e04016d8ece6cf52388e283eb06cf0a6040fd2b. Sólo datos sintéticos. No modificar producto ni iniciar capacidad completa.
Último diagnóstico: runner20261011-130102-8286f2c3,5PASS98.47s,1176huellas y limpieza comprobadas. PG17/TCP reales,2workers sync calientes; clones idénticos548eventos/256reads tras64POST;3muestras control/perfilada/control con4CoverageRead+8EVENT por commit.
TCP812.239/1882.635/796.736ms;WSGI811.169/1950.134/795.745;CPU428.554/1563.754/425.883. Gran intrusión cProfile(timer=thread_time), NO p95 ni ahorro; WSGI incluye reporte posterior al yield, TCP puede acabar antes.
Fixture1500revisiones,selección16777172bytes,originales64MiB no seleccionados,cobertura parcial escalar; sinCaddy/RustFS/cuotas/concurrencia de carga. NO comparable al p95 contractual383lotes~3.75s y objetivo2s. Descargas5s siguen pendientes, no medir aquí.
En perfil: source_copy1call425.327wall/362.969CPU; batches_next1501calls378.769/319.893; exclusivobatches incluyeORM/adaptación/agrupación no observada, no CPU pura de ORM. SQLexecute423calls404.473wall107.741CPU NO fetch/pipeline.sync niCPUservidor.
Category/Service/Municipality residualCPU trasSQL observado1.765/1.751/1.889ms(~5.4ms); NO coste exacto ni ahorro, candidata valoresprimitivos cerrada porahora. Model.__init__2010calls21.842ownCPU/72.552incl;from_db1993calls18.858/100.158.
scalar_fields101755entradas/reanudaciones(incl72978recursivas),101.493own/147.259inclmsperfilados NO101755recorridos completos. pointer_value9002calls33.366own78.634incl; project_selected2calls14.623own184.502incl; compile_coverage1call13.334own240.489incl.
CandidataSQLinline anterior rechazada tras20muestras/variante clonesABBA:originalmed797.984/p95819.964ms vsinline789.795/829.377ms. Producto restauradoHEAD. MemoJSON no justificó margen; cachechain/autoridad prohibido por frescura/mutaciónpropia/DDL.
Opinión Codex: medir primero sincProfile los recorridos puros, con conteo estructural independiente y mismo fixture, antesde elegir cambio; no inferir147msahorrables. Posible alternativa menos amplia: compile_coverage sólo consume item['path'], explorar generador especializado de rutas sin construir diccionario de cada hoja, manteniendo orden/validación/error y scalar_fields público. No asumir beneficio ni equivalencia. Otra vía pointer_value separada. Traversaliterativo requiere preservar profundidad/RecursionError/mutación duranteyield/close/throw ademásdeRFC6901; códigoiterativoanteriorNotebook con marco3elementos ytop[3]/top[4] es inválido.
Debatid: (1) ¿qué vía medir primero y por qué? (2) diseño mínimo finito limpio separando preparación,cronometraje y validación; corpus ancho/profundo/representativo; no tiempos mínimos inventados. (3) contraejemplos de rutas especializadas vsiterativo vsdecoderpunteros; qué fuente adicional falta. (4) decisión y criterio de abandono sin porcentajes asumidos. No entregar parche sin evidencia. Identifica límites del contexto y corrige conjeturas de Codex. Devuelve hechos/objeciones/plan/decisión, máx900palabras.
Código exacto actual:

apps/safety/rights_portability_catalog.py :: scalar_fields
def scalar_fields(value, prefix=""):
    """Walk individual leaves with RFC6901 paths; containers are never choices."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValidationError("Invalid portability object key")
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from scalar_fields(child, prefix + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from scalar_fields(child, prefix + "/" + str(index))
    elif prefix:
        yield {"path": prefix, "value": value}
    else:
        raise ValidationError("Portability row requires an object or list")

apps/safety/rights_portability_selection.py :: pointer_value
def pointer_value(row, path):
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        raise ValidationError("Invalid portability field path")
    value = row
    for segment in path[1:].split("/"):
        # RFC6901 escape sequences; reject malformed aliases.
        escaped = segment.replace("~1", "").replace("~0", "")
        if "~" in escaped:
            raise ValidationError("Invalid portability field escape")
        key = segment.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif (
            isinstance(value, list)
            and key.isascii()
            and key.isdecimal()
            and str(int(key)) == key
            and int(key) < len(value)
        ):
            value = value[int(key)]
        else:
            raise ValidationError("Portability field unavailable")
    if isinstance(value, (dict, list)):
        raise ValidationError("Select individual portability fields")
    return deepcopy(value)

apps/safety/rights_portability_selection.py :: project_selected
def project_selected(source, assessment, selection, *, field_evidence=None):
    """Project declared eligible fields; not a standalone authorization or delivery API."""
    checked = checked_assessment(assessment)
    eligible = {
        name for name, item in checked.items() if item["status"] in {"eligible", "granular"}
    }
    if not isinstance(selection, dict) or set(selection) != eligible:
        raise ValidationError("Select each eligible dataset explicitly")
    granular = {
        name for name in eligible if checked[name]["status"] == "granular" and selection[name]
    }
    if field_evidence is None:
        field_evidence = {}
    if not isinstance(field_evidence, dict) or set(field_evidence) != granular:
        raise ValidationError("Provide exact field evidence for mixed dataset selections")
    output = {}
    for dataset in sorted(eligible):
        rows = SECTIONS[dataset](source)
        references = {row_reference(dataset, index, row): row for index, row in enumerate(rows)}
        selectors = selection[dataset]
        if not isinstance(selectors, list):
            raise ValidationError("Invalid portability row selection")
        evidence_rows = field_evidence.get(dataset, {})
        if not isinstance(evidence_rows, dict):
            raise ValidationError("Invalid mixed row evidence")
        seen = set()
        projected = []
        for selector in selectors:
            if not isinstance(selector, dict) or set(selector) != {"row", "fields"}:
                raise ValidationError("Invalid portability row selector")
            reference, paths = selector["row"], selector["fields"]
            if not isinstance(reference, str) or reference not in references or reference in seen:
                raise ValidationError("Portability row unavailable or duplicated")
            if (
                not isinstance(paths, list)
                or not paths
                or any(not isinstance(path, str) for path in paths)
                or len(set(paths)) != len(paths)
            ):
                raise ValidationError("Select unique portability fields")
            if dataset in granular:
                evidence = evidence_rows.get(reference)
                if not isinstance(evidence, dict) or set(evidence) != set(paths):
                    raise ValidationError("Provide exact evidence for each selected mixed field")
                for decision in evidence.values():
                    if not isinstance(decision, dict) or decision.get("status") != "eligible":
                        raise ValidationError("Selected mixed fields require eligible conditions")
                    checked_assessment({name: decision for name in DATASETS})
            seen.add(reference)
            projected.append(
                {"fields": {path: pointer_value(references[reference], path) for path in paths}}
            )
        if dataset in granular and set(evidence_rows) != seen:
            raise ValidationError("Mixed evidence contains unselected rows")
        output[dataset] = projected
    return {"schema": "portability-selected-fields-v1", "datasets": output}

apps/safety/rights_portability_coverage.py :: compile_coverage
def compile_coverage(
    source,
    assessment,
    selection,
    omissions,
    images,
    image_omissions,
    *,
    field_evidence=None,
    allow_partial=False,
):
    if type(allow_partial) is not bool:
        raise ValidationError("Invalid partial coverage mode")
    assessment = checked_assessment(assessment)
    if any(facts["status"] == "pending" for facts in assessment.values()):
        raise ValidationError("Pending datasets prevent final coverage")
    projection = project_selected(source, assessment, selection, field_evidence=field_evidence)
    if not isinstance(omissions, dict) or set(omissions) != set(DATASETS):
        raise ValidationError("Cover every dataset, including empty datasets")
    if not isinstance(images, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("photo"), str)
        or not isinstance(item.get("content_digest"), str)
        for item in images
    ):
        raise ValidationError("Invalid binary coverage declarations")
    checked_images(
        source, assessment, images, {item["photo"]: item["content_digest"] for item in images}
    )
    datasets = {}
    for name in DATASETS:
        rows = SECTIONS[name](source)
        row_decisions = omissions[name]
        if not isinstance(row_decisions, dict):
            raise ValidationError("Invalid coverage row decisions")
        if assessment[name]["status"] == "excluded":
            if row_decisions:
                raise ValidationError("Dataset exclusion already covers its rows")
            datasets[name] = {"status": "excluded", "rows": len(rows)}
            continue
        selectors = {item["row"]: set(item["fields"]) for item in selection[name]}
        missing_rows = set()
        included_count = excluded_count = pending_count = 0
        for index, row in enumerate(rows):
            reference = row_reference(name, index, row)
            paths = {item["path"] for item in scalar_fields(row)}
            selected = selectors.get(reference, set())
            missing = paths - selected
            included_count += len(selected)
            if not missing:
                continue
            missing_rows.add(reference)
            decision = row_decisions.get(reference)
            if reference not in row_decisions and allow_partial:
                pending_count += len(missing)
                continue
            if not isinstance(decision, dict):
                raise ValidationError("Every omitted row or field needs evidence")
            if set(decision) == {"all"}:
                exclusion(decision["all"])
                excluded_count += len(missing)
            elif set(decision) == {"fields"} and isinstance(decision["fields"], dict):
                declared = set(decision["fields"])
                if not declared <= missing or (not allow_partial and declared != missing):
                    raise ValidationError("Cover exactly the omitted scalar fields")
                excluded_count += len(declared)
                pending_count += len(missing - declared)
                for facts in decision["fields"].values():
                    exclusion(facts)
            else:
                raise ValidationError("Invalid omission coverage schema")
        if not set(row_decisions) <= missing_rows or (
            not allow_partial and set(row_decisions) != missing_rows
        ):
            raise ValidationError("Coverage contains unavailable or already included rows")
        datasets[name] = {
            "status": "pending" if pending_count else "covered",
            "rows": len(rows),
            "included_fields": included_count,
            "excluded_fields": excluded_count,
        }
        if allow_partial:
            datasets[name]["pending_fields"] = pending_count


apps/safety/rights_portability_batch_projection.py :: project
    entries = state['entries']
    if key in entries and _audit_only:
        return None
    if key not in entries or entries[key] is _VALIDATED_ONLY:
        value = operation(source, assessment, binding['selection'],
                          field_evidence=binding.get('field_evidence'))
        # At most one entry per individually audited child; never grows across a request.
        if len(entries) >= 4:
            return None if _audit_only else value
        entries[key] = _VALIDATED_ONLY if _audit_only else deepcopy(value)
        return None if _audit_only else value
    return deepcopy(entries[key])

```

## 3 · codex · context

UTC: 2026-10-11T13:17:10.036718+00:00

```text
Primera deliberación conjunta MOD08. Codex modera; tu función es revisión independiente sin herramientas.
HEAD 7e04016d8ece6cf52388e283eb06cf0a6040fd2b. Sólo datos sintéticos. No modificar producto ni iniciar capacidad completa.
Último diagnóstico: runner20261011-130102-8286f2c3,5PASS98.47s,1176huellas y limpieza comprobadas. PG17/TCP reales,2workers sync calientes; clones idénticos548eventos/256reads tras64POST;3muestras control/perfilada/control con4CoverageRead+8EVENT por commit.
TCP812.239/1882.635/796.736ms;WSGI811.169/1950.134/795.745;CPU428.554/1563.754/425.883. Gran intrusión cProfile(timer=thread_time), NO p95 ni ahorro; WSGI incluye reporte posterior al yield, TCP puede acabar antes.
Fixture1500revisiones,selección16777172bytes,originales64MiB no seleccionados,cobertura parcial escalar; sinCaddy/RustFS/cuotas/concurrencia de carga. NO comparable al p95 contractual383lotes~3.75s y objetivo2s. Descargas5s siguen pendientes, no medir aquí.
En perfil: source_copy1call425.327wall/362.969CPU; batches_next1501calls378.769/319.893; exclusivobatches incluyeORM/adaptación/agrupación no observada, no CPU pura de ORM. SQLexecute423calls404.473wall107.741CPU NO fetch/pipeline.sync niCPUservidor.
Category/Service/Municipality residualCPU trasSQL observado1.765/1.751/1.889ms(~5.4ms); NO coste exacto ni ahorro, candidata valoresprimitivos cerrada porahora. Model.__init__2010calls21.842ownCPU/72.552incl;from_db1993calls18.858/100.158.
scalar_fields101755entradas/reanudaciones(incl72978recursivas),101.493own/147.259inclmsperfilados NO101755recorridos completos. pointer_value9002calls33.366own78.634incl; project_selected2calls14.623own184.502incl; compile_coverage1call13.334own240.489incl.
CandidataSQLinline anterior rechazada tras20muestras/variante clonesABBA:originalmed797.984/p95819.964ms vsinline789.795/829.377ms. Producto restauradoHEAD. MemoJSON no justificó margen; cachechain/autoridad prohibido por frescura/mutaciónpropia/DDL.
Opinión Codex: medir primero sincProfile los recorridos puros, con conteo estructural independiente y mismo fixture, antesde elegir cambio; no inferir147msahorrables. Posible alternativa menos amplia: compile_coverage sólo consume item['path'], explorar generador especializado de rutas sin construir diccionario de cada hoja, manteniendo orden/validación/error y scalar_fields público. No asumir beneficio ni equivalencia. Otra vía pointer_value separada. Traversaliterativo requiere preservar profundidad/RecursionError/mutación duranteyield/close/throw ademásdeRFC6901; códigoiterativoanteriorNotebook con marco3elementos ytop[3]/top[4] es inválido.
Debatid: (1) ¿qué vía medir primero y por qué? (2) diseño mínimo finito limpio separando preparación,cronometraje y validación; corpus ancho/profundo/representativo; no tiempos mínimos inventados. (3) contraejemplos de rutas especializadas vsiterativo vsdecoderpunteros; qué fuente adicional falta. (4) decisión y criterio de abandono sin porcentajes asumidos. No entregar parche sin evidencia. Identifica límites del contexto y corrige conjeturas de Codex. Devuelve hechos/objeciones/plan/decisión, máx900palabras.
Código exacto actual:

apps/safety/rights_portability_catalog.py :: scalar_fields
def scalar_fields(value, prefix=""):
    """Walk individual leaves with RFC6901 paths; containers are never choices."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValidationError("Invalid portability object key")
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from scalar_fields(child, prefix + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from scalar_fields(child, prefix + "/" + str(index))
    elif prefix:
        yield {"path": prefix, "value": value}
    else:
        raise ValidationError("Portability row requires an object or list")

apps/safety/rights_portability_selection.py :: pointer_value
def pointer_value(row, path):
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        raise ValidationError("Invalid portability field path")
    value = row
    for segment in path[1:].split("/"):
        # RFC6901 escape sequences; reject malformed aliases.
        escaped = segment.replace("~1", "").replace("~0", "")
        if "~" in escaped:
            raise ValidationError("Invalid portability field escape")
        key = segment.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif (
            isinstance(value, list)
            and key.isascii()
            and key.isdecimal()
            and str(int(key)) == key
            and int(key) < len(value)
        ):
            value = value[int(key)]
        else:
            raise ValidationError("Portability field unavailable")
    if isinstance(value, (dict, list)):
        raise ValidationError("Select individual portability fields")
    return deepcopy(value)

apps/safety/rights_portability_selection.py :: project_selected
def project_selected(source, assessment, selection, *, field_evidence=None):
    """Project declared eligible fields; not a standalone authorization or delivery API."""
    checked = checked_assessment(assessment)
    eligible = {
        name for name, item in checked.items() if item["status"] in {"eligible", "granular"}
    }
    if not isinstance(selection, dict) or set(selection) != eligible:
        raise ValidationError("Select each eligible dataset explicitly")
    granular = {
        name for name in eligible if checked[name]["status"] == "granular" and selection[name]
    }
    if field_evidence is None:
        field_evidence = {}
    if not isinstance(field_evidence, dict) or set(field_evidence) != granular:
        raise ValidationError("Provide exact field evidence for mixed dataset selections")
    output = {}
    for dataset in sorted(eligible):
        rows = SECTIONS[dataset](source)
        references = {row_reference(dataset, index, row): row for index, row in enumerate(rows)}
        selectors = selection[dataset]
        if not isinstance(selectors, list):
            raise ValidationError("Invalid portability row selection")
        # [Fragmento omitido aquí: valida tipos/selectores únicos/evidencia granular;
        # no se propone omitirlo en producto.]
        for selector in selectors:
            reference, paths = selector['row'], selector['fields']
            seen.add(reference)
            projected.append(
                {"fields": {path: pointer_value(references[reference], path) for path in paths}}
            )
        if dataset in granular and set(evidence_rows) != seen:
            raise ValidationError("Mixed evidence contains unselected rows")
        output[dataset] = projected
    return {"schema": "portability-selected-fields-v1", "datasets": output}

apps/safety/rights_portability_coverage.py :: compile_coverage
def compile_coverage(
    source,
    assessment,
    selection,
    omissions,
    images,
    image_omissions,
    *,
    field_evidence=None,
    allow_partial=False,
):
    if type(allow_partial) is not bool:
        raise ValidationError("Invalid partial coverage mode")
    assessment = checked_assessment(assessment)
    if any(facts["status"] == "pending" for facts in assessment.values()):
        raise ValidationError("Pending datasets prevent final coverage")
    projection = project_selected(source, assessment, selection, field_evidence=field_evidence)
    if not isinstance(omissions, dict) or set(omissions) != set(DATASETS):
        raise ValidationError("Cover every dataset, including empty datasets")
    if not isinstance(images, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("photo"), str)
        or not isinstance(item.get("content_digest"), str)
        for item in images
    ):
        raise ValidationError("Invalid binary coverage declarations")
    checked_images(
        source, assessment, images, {item["photo"]: item["content_digest"] for item in images}
    )
    datasets = {}
    for name in DATASETS:
        rows = SECTIONS[name](source)
        row_decisions = omissions[name]
        if not isinstance(row_decisions, dict):
            raise ValidationError("Invalid coverage row decisions")
        if assessment[name]["status"] == "excluded":
            if row_decisions:
                raise ValidationError("Dataset exclusion already covers its rows")
            datasets[name] = {"status": "excluded", "rows": len(rows)}
            continue
        selectors = {item["row"]: set(item["fields"]) for item in selection[name]}
        missing_rows = set()
        included_count = excluded_count = pending_count = 0
        for index, row in enumerate(rows):
            reference = row_reference(name, index, row)
            paths = {item["path"] for item in scalar_fields(row)}
            selected = selectors.get(reference, set())
            missing = paths - selected
            included_count += len(selected)
            if not missing:
                continue
            missing_rows.add(reference)
            decision = row_decisions.get(reference)
            if reference not in row_decisions and allow_partial:
                pending_count += len(missing)
                continue
            if not isinstance(decision, dict):
                raise ValidationError("Every omitted row or field needs evidence")
            if set(decision) == {"all"}:
                exclusion(decision["all"])
                excluded_count += len(missing)
            elif set(decision) == {"fields"} and isinstance(decision["fields"], dict):
                declared = set(decision["fields"])
                if not declared <= missing or (not allow_partial and declared != missing):
                    raise ValidationError("Cover exactly the omitted scalar fields")
                excluded_count += len(declared)
                pending_count += len(missing - declared)
                for facts in decision["fields"].values():
                    exclusion(facts)
            else:
                raise ValidationError("Invalid omission coverage schema")
        if not set(row_decisions) <= missing_rows or (
            not allow_partial and set(row_decisions) != missing_rows
        ):
            raise ValidationError("Coverage contains unavailable or already included rows")
        datasets[name] = {
            "status": "pending" if pending_count else "covered",
            "rows": len(rows),
            "included_fields": included_count,
            "excluded_fields": excluded_count,
        }
        if allow_partial:
            datasets[name]["pending_fields"] = pending_count


batch_projection.project (resumen de flujo, no código completo): caller ha validado/descifrado frescamente; cache operation-local max4 entradas. Primera proyección _audit_only valida y descarta output almacenando sentinel_VALIDATED_ONLY; si luego se necesita output se vuelve a ejecutar operación. No hay demostración de que eliminar una llamada preserve validaciones actuales.

```

## 4 · codex · request

UTC: 2026-10-11T13:17:10.087184+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Primera deliberación conjunta MOD08. Codex modera; tu función es revisión independiente sin herramientas.
HEAD 7e04016d8ece6cf52388e283eb06cf0a6040fd2b. Sólo datos sintéticos. No modificar producto ni iniciar capacidad completa.
Último diagnóstico: runner20261011-130102-8286f2c3,5PASS98.47s,1176huellas y limpieza comprobadas. PG17/TCP reales,2workers sync calientes; clones idénticos548eventos/256reads tras64POST;3muestras control/perfilada/control con4CoverageRead+8EVENT por commit.
TCP812.239/1882.635/796.736ms;WSGI811.169/1950.134/795.745;CPU428.554/1563.754/425.883. Gran intrusión cProfile(timer=thread_time), NO p95 ni ahorro; WSGI incluye reporte posterior al yield, TCP puede acabar antes.
Fixture1500revisiones,selección16777172bytes,originales64MiB no seleccionados,cobertura parcial escalar; sinCaddy/RustFS/cuotas/concurrencia de carga. NO comparable al p95 contractual383lotes~3.75s y objetivo2s. Descargas5s siguen pendientes, no medir aquí.
En perfil: source_copy1call425.327wall/362.969CPU; batches_next1501calls378.769/319.893; exclusivobatches incluyeORM/adaptación/agrupación no observada, no CPU pura de ORM. SQLexecute423calls404.473wall107.741CPU NO fetch/pipeline.sync niCPUservidor.
Category/Service/Municipality residualCPU trasSQL observado1.765/1.751/1.889ms(~5.4ms); NO coste exacto ni ahorro, candidata valoresprimitivos cerrada porahora. Model.__init__2010calls21.842ownCPU/72.552incl;from_db1993calls18.858/100.158.
scalar_fields101755entradas/reanudaciones(incl72978recursivas),101.493own/147.259inclmsperfilados NO101755recorridos completos. pointer_value9002calls33.366own78.634incl; project_selected2calls14.623own184.502incl; compile_coverage1call13.334own240.489incl.
CandidataSQLinline anterior rechazada tras20muestras/variante clonesABBA:originalmed797.984/p95819.964ms vsinline789.795/829.377ms. Producto restauradoHEAD. MemoJSON no justificó margen; cachechain/autoridad prohibido por frescura/mutaciónpropia/DDL.
Opinión Codex: medir primero sincProfile los recorridos puros, con conteo estructural independiente y mismo fixture, antesde elegir cambio; no inferir147msahorrables. Posible alternativa menos amplia: compile_coverage sólo consume item['path'], explorar generador especializado de rutas sin construir diccionario de cada hoja, manteniendo orden/validación/error y scalar_fields público. No asumir beneficio ni equivalencia. Otra vía pointer_value separada. Traversaliterativo requiere preservar profundidad/RecursionError/mutación duranteyield/close/throw ademásdeRFC6901; códigoiterativoanteriorNotebook con marco3elementos ytop[3]/top[4] es inválido.
Debatid: (1) ¿qué vía medir primero y por qué? (2) diseño mínimo finito limpio separando preparación,cronometraje y validación; corpus ancho/profundo/representativo; no tiempos mínimos inventados. (3) contraejemplos de rutas especializadas vsiterativo vsdecoderpunteros; qué fuente adicional falta. (4) decisión y criterio de abandono sin porcentajes asumidos. No entregar parche sin evidencia. Identifica límites del contexto y corrige conjeturas de Codex. Devuelve hechos/objeciones/plan/decisión, máx900palabras.
Código exacto actual:

apps/safety/rights_portability_catalog.py :: scalar_fields
def scalar_fields(value, prefix=""):
    """Walk individual leaves with RFC6901 paths; containers are never choices."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValidationError("Invalid portability object key")
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from scalar_fields(child, prefix + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from scalar_fields(child, prefix + "/" + str(index))
    elif prefix:
        yield {"path": prefix, "value": value}
    else:
        raise ValidationError("Portability row requires an object or list")

apps/safety/rights_portability_selection.py :: pointer_value
def pointer_value(row, path):
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        raise ValidationError("Invalid portability field path")
    value = row
    for segment in path[1:].split("/"):
        # RFC6901 escape sequences; reject malformed aliases.
        escaped = segment.replace("~1", "").replace("~0", "")
        if "~" in escaped:
            raise ValidationError("Invalid portability field escape")
        key = segment.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif (
            isinstance(value, list)
            and key.isascii()
            and key.isdecimal()
            and str(int(key)) == key
            and int(key) < len(value)
        ):
            value = value[int(key)]
        else:
            raise ValidationError("Portability field unavailable")
    if isinstance(value, (dict, list)):
        raise ValidationError("Select individual portability fields")
    return deepcopy(value)

apps/safety/rights_portability_selection.py :: project_selected
def project_selected(source, assessment, selection, *, field_evidence=None):
    """Project declared eligible fields; not a standalone authorization or delivery API."""
    checked = checked_assessment(assessment)
    eligible = {
        name for name, item in checked.items() if item["status"] in {"eligible", "granular"}
    }
    if not isinstance(selection, dict) or set(selection) != eligible:
        raise ValidationError("Select each eligible dataset explicitly")
    granular = {
        name for name in eligible if checked[name]["status"] == "granular" and selection[name]
    }
    if field_evidence is None:
        field_evidence = {}
    if not isinstance(field_evidence, dict) or set(field_evidence) != granular:
        raise ValidationError("Provide exact field evidence for mixed dataset selections")
    output = {}
    for dataset in sorted(eligible):
        rows = SECTIONS[dataset](source)
        references = {row_reference(dataset, index, row): row for index, row in enumerate(rows)}
        selectors = selection[dataset]
        if not isinstance(selectors, list):
            raise ValidationError("Invalid portability row selection")
        # [Fragmento omitido aquí: valida tipos/selectores únicos/evidencia granular;
        # no se propone omitirlo en producto.]
        for selector in selectors:
            reference, paths = selector['row'], selector['fields']
            seen.add(reference)
            projected.append(
                {"fields": {path: pointer_value(references[reference], path) for path in paths}}
            )
        if dataset in granular and set(evidence_rows) != seen:
            raise ValidationError("Mixed evidence contains unselected rows")
        output[dataset] = projected
    return {"schema": "portability-selected-fields-v1", "datasets": output}

apps/safety/rights_portability_coverage.py :: compile_coverage
def compile_coverage(
    source,
    assessment,
    selection,
    omissions,
    images,
    image_omissions,
    *,
    field_evidence=None,
    allow_partial=False,
):
    if type(allow_partial) is not bool:
        raise ValidationError("Invalid partial coverage mode")
    assessment = checked_assessment(assessment)
    if any(facts["status"] == "pending" for facts in assessment.values()):
        raise ValidationError("Pending datasets prevent final coverage")
    projection = project_selected(source, assessment, selection, field_evidence=field_evidence)
    if not isinstance(omissions, dict) or set(omissions) != set(DATASETS):
        raise ValidationError("Cover every dataset, including empty datasets")
    if not isinstance(images, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("photo"), str)
        or not isinstance(item.get("content_digest"), str)
        for item in images
    ):
        raise ValidationError("Invalid binary coverage declarations")
    checked_images(
        source, assessment, images, {item["photo"]: item["content_digest"] for item in images}
    )
    datasets = {}
    for name in DATASETS:
        rows = SECTIONS[name](source)
        row_decisions = omissions[name]
        if not isinstance(row_decisions, dict):
            raise ValidationError("Invalid coverage row decisions")
        if assessment[name]["status"] == "excluded":
            if row_decisions:
                raise ValidationError("Dataset exclusion already covers its rows")
            datasets[name] = {"status": "excluded", "rows": len(rows)}
            continue
        selectors = {item["row"]: set(item["fields"]) for item in selection[name]}
        missing_rows = set()
        included_count = excluded_count = pending_count = 0
        for index, row in enumerate(rows):
            reference = row_reference(name, index, row)
            paths = {item["path"] for item in scalar_fields(row)}
            selected = selectors.get(reference, set())
            missing = paths - selected
            included_count += len(selected)
            if not missing:
                continue
            missing_rows.add(reference)
            decision = row_decisions.get(reference)
            if reference not in row_decisions and allow_partial:
                pending_count += len(missing)
                continue
            if not isinstance(decision, dict):
                raise ValidationError("Every omitted row or field needs evidence")
            if set(decision) == {"all"}:
                exclusion(decision["all"])
                excluded_count += len(missing)
            elif set(decision) == {"fields"} and isinstance(decision["fields"], dict):
                declared = set(decision["fields"])
                if not declared <= missing or (not allow_partial and declared != missing):
                    raise ValidationError("Cover exactly the omitted scalar fields")
                excluded_count += len(declared)
                pending_count += len(missing - declared)
                for facts in decision["fields"].values():
                    exclusion(facts)
            else:
                raise ValidationError("Invalid omission coverage schema")
        if not set(row_decisions) <= missing_rows or (
            not allow_partial and set(row_decisions) != missing_rows
        ):
            raise ValidationError("Coverage contains unavailable or already included rows")
        datasets[name] = {
            "status": "pending" if pending_count else "covered",
            "rows": len(rows),
            "included_fields": included_count,
            "excluded_fields": excluded_count,
        }
        if allow_partial:
            datasets[name]["pending_fields"] = pending_count


batch_projection.project (resumen de flujo, no código completo): caller ha validado/descifrado frescamente; cache operation-local max4 entradas. Primera proyección _audit_only valida y descarta output almacenando sentinel_VALIDATED_ONLY; si luego se necesita output se vuelve a ejecutar operación. No hay demostración de que eliminar una llamada preserve validaciones actuales.

```

## 5 · claude · opinion

UTC: 2026-10-11T13:18:24.557703+00:00

```text
# Revisión independiente MOD08: recorridos de `scalar_fields` y `pointer_value`

**Alcance.** Esta revisión sólo usa el contexto suministrado. No ejecuté nada y no hay PASS ni autorización.

## Hechos (medidos o leídos del código)

- La carga es TCP 812/1883/797 ms (control/perfilada/control). La intrusión de cProfile es grande. Ninguna cifra es p95 ni ahorro.
- `compile_coverage`: 1 llamada, 13.3 ms propios y 240.5 ms inclusivos.
- `project_selected`: 2 llamadas, 184.5 ms inclusivos.
- `scalar_fields`: 101 755 entradas/reanudaciones, de ellas 72 978 recursivas. Tiene 147.3 ms inclusivos.
- `pointer_value`: 9002 llamadas, 33.4 ms propios y 78.6 ms inclusivos.
- En el código mostrado, `compile_coverage` sólo usa `item["path"]` y lo consume entero en una comprensión de conjunto. Por tanto, el orden no importa para el resultado, sólo para qué error aparece primero.
- El escape RFC 6901 es inyectivo: distintas claves hermanas no pueden colisionar en la misma ruta.
- `pointer_value` rechaza rutas de más de 500 caracteres. `scalar_fields` no tiene límite de longitud.

## Objeciones y correcciones a Codex

1. **La atribución es inconsistente.** `compile_coverage` suma 240.5 ms inclusivos y contiene una llamada a `project_selected`. Si esa llamada aporta una parte sustancial de los 184.5 ms, no caben 147 ms de `scalar_fields` en el resto. Además, con generadores y `yield from`, cProfile acumula por reanudación y los inclusivos no se pueden sumar.
   - **Hipótesis:** `scalar_fields` tiene otros llamadores, quizá el fragmento omitido de evidencia granular, el catálogo o `_audit_only`.
   - **Falta:** el desglose por llamador (`print_callers`) del perfil de este HEAD y un grep de usos de `scalar_fields`.
   - La frase "compile_coverage sólo consume path" es cierta localmente, no globalmente.
2. **101 755 no es el número de hojas.** Con `yield from`, cada hoja reanuda tantos marcos como niveles de profundidad tenga. El coste depende de Σ profundidad por hoja, no sólo de las hojas. Hace falta un conteo estructural independiente:
   - filas, hojas, contenedores y contenedores vacíos;
   - profundidad máxima y Σ profundidad;
   - claves con `~` o `/`;
   - longitud total de rutas.
3. **Las exigencias close/throw/mutación sólo aplican si se sustituye el `scalar_fields` público.** Una función privada y ansiosa que devuelva un conjunto de rutas, usada sólo en `compile_coverage`, no expone el protocolo de generador. Sí debe conservar:
   - el error de raíz escalar;
   - el error de clave no-str con el mismo mensaje;
   - el recorrido DFS en preorden, para que el primer error sea el mismo;
   - la aceptación de subclases (`isinstance`, no `type() is`);
   - el comportamiento ante profundidad extrema.
4. **Una versión iterativa cambia la semántica de `RecursionError`.** La actual falla a cierta profundidad y la iterativa aceptaría estructuras más profundas. No sabemos si hay un límite de profundidad aguas arriba (decodificador JSON).
   - **Falta:** esa fuente.
   - Además, con rutas de más de 500 caracteres no hay campo seleccionable para `pointer_value`. Si las exclusiones por campo validan longitud, eso no se ve en el código mostrado.
5. **En `pointer_value`, los 45 ms no propios probablemente son `deepcopy` más métodos de `str`, que cProfile instrumenta y por eso inflan más este código.** Es hipótesis, no está medido. Cachear segmentos decodificados por ruta sería sólo un memo de parseo (operación-local, función pura del string), no autoridad. Aun así, debe re-lanzar el error en cada llamada.
   - **Contraejemplo para atajar `deepcopy`:** hojas no JSON, como objetos mutables o tipos de dominio. Falta saber qué tipos producen `SECTIONS`.

## Contraejemplos para el corpus de validación

- Claves `"~"`, `"/"`, `"~01"`, `"~1"` y `""`.
- Clave `"0"` en dict frente a índice 0 en lista.
- Raíz `{}` o `[]` (cero rutas, sin error) frente a raíz escalar (error).
- Contenedores vacíos anidados.
- Clave no-str en la raíz y a profundidad, combinada con un error previo en DFS.
- Subclases de dict, list y str.
- Profundidad cercana y superior al límite de recursión.
- Para `pointer_value`: `"01"`, `"-"`, índice fuera de rango, `"~2"` y `"~"` final, segmento vacío y ruta de exactamente 500 caracteres.

## Plan mínimo y finito

**Paso 0, atribución (sin medición nueva):**
- callers de `scalar_fields` y `pointer_value` en el perfil existente de `7e04016d`;
- grep de usos;
- tipos de hoja reales;
- límite de profundidad del decodificador.

Si la mayor parte de `scalar_fields` no viene de `compile_coverage`, se reorienta el plan.

**Paso 1, preparación (sin cronometrar):**
- Materializar en un clon sintético las filas exactas que recibe `compile_coverage` y congelarlas.
- Calcular el conteo estructural del punto 2.
- Generar corpus anchos, profundos y con escapes por parámetros declarados, sin inventar tiempos.

**Paso 2, validación (sin cronometrar, antes y después del tiempo):**
- La variante privada debe producir el mismo conjunto de rutas por fila.
- Debe dar el mismo tipo y mensaje de excepción en todos los contraejemplos.
- Cualquier diferencia descarta la variante.

**Paso 3, cronometraje sin cProfile:**
- Original frente a variante, intercalados en ABBA.
- `perf_counter_ns` y `thread_time_ns`.
- Mismo estado de GC en ambas.
- Número fijo de rondas de calentamiento descartadas.
- Incluir una sesión A/A para medir el ruido propio.

**Paso 4, sólo si el paso 3 separa más allá del A/A:**
- Prueba extremo a extremo con el arnés anterior (clones ABBA, 20 muestras por variante).
- Esto sigue sin ser p95 contractual: no hay Caddy, RustFS, cuotas ni concurrencia.

## Decisión propuesta (finita)

| Vía | Decisión |
|---|---|
| A. Ruta privada ansiosa para `compile_coverage` | Medir primero, tras el paso 0 |
| B. Decodificador o memo de `pointer_value` | Diferida hasta conocer tipos de hoja y atribución |
| C. `scalar_fields` iterativo público | Rechazada por ahora: mayor superficie semántica sin evidencia |
| D. Abandonar | Ver criterios |

**Criterios de abandono (sin porcentajes asumidos):**
- El paso 0 muestra que `compile_coverage` no es el llamador dominante.
- Cualquier divergencia en el paso 2.
- El paso 3 no separa la variante del ruido A/A medido en la misma sesión.
- El paso 4 no mejora mediana y p95 de muestra por encima de la dispersión de control frente a control.

No se entrega parche. Lo de 147 ms ahorrables sigue siendo una conjetura no respaldada.
```

## 6 · codex · opinion

UTC: 2026-10-11T13:19:45.790342+00:00

```text
Codex tras comprobar código: rg encuentra scalar_fields además en coverage_read_gate(countsum),coverage_pages(candidates y conteo),coverage_page(islice),catalog(islice),accesscoverage(values). Por tanto mi hipótesis compile-only noestá demostrada; atribución en perfil existenteNOconservada (top100stats sincallergraph), no fingir quepodemos sacar print_callers. source_copy transforma fechas/IDs/importes enstr pero days/spoken_languages contienenJSON; SECTIONS son accesores listasdictsource. fast_canonical.reference_check impone profundidad>200=>ValueError, tiposJSON admitidos, ocurre sólo alcanonicalizar; no prueba universal de dominio en cada llamada a scalar_fields. Conservar APIpúblico y errores. Corregir Claude: costes inclusivos nose suman pero147 y240 no son necesariamente inconsistentes: project_selected tiene2calls globales, distribución interna desconocida. No prometer quehay incoherenciademedición porcuentasglobales.
Pregunta a Notebook: actúa como segundo participante, contrasta Codex/Claude con fuentes actuales prioritarias sobrehistorial y devuelve objeciones y una decisión finita. ¿Medir primero llamadas externascompletas porcaller con dosrelojes bajosoverhead en unrequestinstrumentado ycontroles, o microbenchcorpus primero? ¿Qué candidate scope más seguro evitar dicts de hojas en consumidoresdepaths/count sin tocar público? No inventar equivalencia ni ahorro. Indica qué aceptar/rechazar delplanClaude y qué informaciónfaltaría. Máx800palabras,no parche.

```

## 7 · codex · request

UTC: 2026-10-11T13:19:45.841137+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Primera deliberación conjunta MOD08. Codex modera; tu función es revisión independiente sin herramientas.
HEAD 7e04016d8ece6cf52388e283eb06cf0a6040fd2b. Sólo datos sintéticos. No modificar producto ni iniciar capacidad completa.
Último diagnóstico: runner20261011-130102-8286f2c3,5PASS98.47s,1176huellas y limpieza comprobadas. PG17/TCP reales,2workers sync calientes; clones idénticos548eventos/256reads tras64POST;3muestras control/perfilada/control con4CoverageRead+8EVENT por commit.
TCP812.239/1882.635/796.736ms;WSGI811.169/1950.134/795.745;CPU428.554/1563.754/425.883. Gran intrusión cProfile(timer=thread_time), NO p95 ni ahorro; WSGI incluye reporte posterior al yield, TCP puede acabar antes.
Fixture1500revisiones,selección16777172bytes,originales64MiB no seleccionados,cobertura parcial escalar; sinCaddy/RustFS/cuotas/concurrencia de carga. NO comparable al p95 contractual383lotes~3.75s y objetivo2s. Descargas5s siguen pendientes, no medir aquí.
En perfil: source_copy1call425.327wall/362.969CPU; batches_next1501calls378.769/319.893; exclusivobatches incluyeORM/adaptación/agrupación no observada, no CPU pura de ORM. SQLexecute423calls404.473wall107.741CPU NO fetch/pipeline.sync niCPUservidor.
Category/Service/Municipality residualCPU trasSQL observado1.765/1.751/1.889ms(~5.4ms); NO coste exacto ni ahorro, candidata valoresprimitivos cerrada porahora. Model.__init__2010calls21.842ownCPU/72.552incl;from_db1993calls18.858/100.158.
scalar_fields101755entradas/reanudaciones(incl72978recursivas),101.493own/147.259inclmsperfilados NO101755recorridos completos. pointer_value9002calls33.366own78.634incl; project_selected2calls14.623own184.502incl; compile_coverage1call13.334own240.489incl.
CandidataSQLinline anterior rechazada tras20muestras/variante clonesABBA:originalmed797.984/p95819.964ms vsinline789.795/829.377ms. Producto restauradoHEAD. MemoJSON no justificó margen; cachechain/autoridad prohibido por frescura/mutaciónpropia/DDL.
Opinión Codex: medir primero sincProfile los recorridos puros, con conteo estructural independiente y mismo fixture, antesde elegir cambio; no inferir147msahorrables. Posible alternativa menos amplia: compile_coverage sólo consume item['path'], explorar generador especializado de rutas sin construir diccionario de cada hoja, manteniendo orden/validación/error y scalar_fields público. No asumir beneficio ni equivalencia. Otra vía pointer_value separada. Traversaliterativo requiere preservar profundidad/RecursionError/mutación duranteyield/close/throw ademásdeRFC6901; códigoiterativoanteriorNotebook con marco3elementos ytop[3]/top[4] es inválido.
Debatid: (1) ¿qué vía medir primero y por qué? (2) diseño mínimo finito limpio separando preparación,cronometraje y validación; corpus ancho/profundo/representativo; no tiempos mínimos inventados. (3) contraejemplos de rutas especializadas vsiterativo vsdecoderpunteros; qué fuente adicional falta. (4) decisión y criterio de abandono sin porcentajes asumidos. No entregar parche sin evidencia. Identifica límites del contexto y corrige conjeturas de Codex. Devuelve hechos/objeciones/plan/decisión, máx900palabras.

Claude (respuesta completa preservada localmente): recomienda atribución por llamador antes de especializar compile_coverage; corpus con hojas/contenedores/vacíos/profundidad/suma profundidades/escapes/longitud rutas; candidato privado ansioso sólo conjuntos rutas, no cambiar generador público; ABBA y A/A sinprofiler, validar antes/después; luegoHTTP20/variante sólo sihay señal sobreA/A. Objeta que147ms scalar_fields pueden proceder de otros callers y queproyección ocupa partecompile240ms; apunta suma inclusivos generadores noaditiva. Pide tiposhoja y límite profundidad; no atajar deepcopy porque posibles hojasmutables noJSON. Sugiere diferir memo de decoderpunteros yrechazariterativopúblico ahora. Criterioabandono: discrepanciaerrores/resultados, sinseñalA/A oHTTPsinmejora.
Codex tras comprobar código: rg encuentra scalar_fields además en coverage_read_gate(countsum),coverage_pages(candidates y conteo),coverage_page(islice),catalog(islice),accesscoverage(values). Por tanto mi hipótesis compile-only noestá demostrada; atribución en perfil existenteNOconservada (top100stats sincallergraph), no fingir quepodemos sacar print_callers. source_copy transforma fechas/IDs/importes enstr pero days/spoken_languages contienenJSON; SECTIONS son accesores listasdictsource. fast_canonical.reference_check impone profundidad>200=>ValueError, tiposJSON admitidos, ocurre sólo alcanonicalizar; no prueba universal de dominio en cada llamada a scalar_fields. Conservar APIpúblico y errores. Corregir Claude: costes inclusivos nose suman pero147 y240 no son necesariamente inconsistentes: project_selected tiene2calls globales, distribución interna desconocida. No prometer quehay incoherenciademedición porcuentasglobales.
Pregunta a Notebook: actúa como segundo participante, contrasta Codex/Claude con fuentes actuales prioritarias sobrehistorial y devuelve objeciones y una decisión finita. ¿Medir primero llamadas externascompletas porcaller con dosrelojes bajosoverhead en unrequestinstrumentado ycontroles, o microbenchcorpus primero? ¿Qué candidate scope más seguro evitar dicts de hojas en consumidoresdepaths/count sin tocar público? No inventar equivalencia ni ahorro. Indica qué aceptar/rechazar delplanClaude y qué informaciónfaltaría. Máx800palabras,no parche.

apps/safety/rights_portability_catalog.py
def scalar_fields(value, prefix=""):
    """Walk individual leaves with RFC6901 paths; containers are never choices."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValidationError("Invalid portability object key")
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from scalar_fields(child, prefix + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from scalar_fields(child, prefix + "/" + str(index))
    elif prefix:
        yield {"path": prefix, "value": value}
    else:
        raise ValidationError("Portability row requires an object or list")
apps/safety/rights_portability_selection.py
def pointer_value(row, path):
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        raise ValidationError("Invalid portability field path")
    value = row
    for segment in path[1:].split("/"):
        # RFC6901 escape sequences; reject malformed aliases.
        escaped = segment.replace("~1", "").replace("~0", "")
        if "~" in escaped:
            raise ValidationError("Invalid portability field escape")
        key = segment.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif (
            isinstance(value, list)
            and key.isascii()
            and key.isdecimal()
            and str(int(key)) == key
            and int(key) < len(value)
        ):
            value = value[int(key)]
        else:
            raise ValidationError("Portability field unavailable")
    if isinstance(value, (dict, list)):
        raise ValidationError("Select individual portability fields")
    return deepcopy(value)
```

## 8 · notebook · opinion

UTC: 2026-10-11T13:20:31.688428+00:00

```text
### 1. Distinción de estado: Hechos, Hipótesis y Evidencia Faltante

* **Hechos medidos:** 
  1. El perfil actual con `cProfile(timer=thread_time)` registra 101.755 invocaciones/reanudaciones en `scalar_fields` (101,5 ms own / 147,3 ms incl. CPU), pero con alta intrusión del profiler.
  2. `scalar_fields` no es exclusivo de `compile_coverage`: el rastreo con `rg` confirma uso en `coverage_read_gate`, `coverage_pages`, `coverage_page`, `catalog` y `accesscoverage`.
  3. La variante anterior de SQL inline fue rechazada tras control A/B/B/A de 20 muestras por degradar el p95 (829,37 ms vs. 819,96 ms) y el producto se encuentra restaurado en HEAD (`7e04016d8e`).
  4. La función `pointer_value` ejecuta `deepcopy` en cada extracción válida y aplica validación estricta RFC6901 (`~1`, `~0`).

* **Hipótesis no demostradas:**
  1. Que los 147 ms atribuibles a `scalar_fields` procedan predominantemente de `compile_coverage`.
  2. Que eliminar la construcción del diccionario `{"path": ..., "value": ...}` impacte de forma medible en el p95 contractual del request (2 s objetivo / 3,75 s actual).

* **Evidencia faltante:**
  1. Desglose real de tiempo por llamador (*call site attribution*) sin la sobrecarga de `cProfile`.
  2. Mediciones A/A y A/B en la pila completa (WSGI/TCP) comparando el impacto global.

---

### 2. ¿Qué medir primero y por qué?

**Acepto medir primero las llamadas completas por call site en un request instrumentado con bajo overhead, rechazando empezar por un microbenchmark aislado.**

Un microbenchmark sobre corpus sintético puede mostrar una reducción relativa de microsegundos al omitir asignaciones de diccionarios, pero es incapaz de revelar si dicho tiempo representa el 5% o el 90% del costo real en la petición WSGI/TCP. Medir en la petición real con temporizadores de baja sobrecarga (`time.perf_counter_ns()` envolviendo las llamadas de cada sitio identificado) proporciona la distribución exacta del costo entre `compile_coverage`, `coverage_read_gate` y el resto de los consumidores.

---

### 3. Evaluación de Claude/Codex, candidato de alcance y contraejemplos

#### Aceptaciones y correcciones a los planteamientos previos:
* **De Claude:** Acepto exigir atribución por *call site* previa a cualquier refactorización y conservar intactos el contrato público y las excepciones `ValidationError`. Rechazo priorizar el microbenchmark de corpus antes de la instrumentación e2e.
* **De Codex:** Confirmo su hallazgo con `rg` que invalida la hipótesis de un único llamador. Aclaro que no debe interpretarse incoherencia entre los 240 ms de `compile_coverage` y los 147 ms de `scalar_fields`, dado que la agregación plana de `cProfile` no preserva la jerarquía de invocaciones.

#### Ámbito de candidato más seguro (sin alterar la API pública):
Si la instrumentación demuestra que el consumidor principal de `scalar_fields` solo necesita el conjunto de rutas y no los valores, el candidato más seguro es un generador privado especializado interno (ej. `_iter_scalar_paths(value, prefix="")`) que retorne directamente las cadenas de texto con la ruta escapada RFC6901. Esto evita instanciar y desechar 101.755 diccionarios intermedios, manteniendo `scalar_fields` y `pointer_value` sin modificaciones.

#### Contraejemplos técnicos a considerar:
1. **Rutas especializadas vs. Re-evaluación con `pointer_value`:** Si un consumidor obtiene únicamente las rutas mediante un generador de cadenas y posteriormente invoca `pointer_value` para cada ruta sobre la estructura original, se pasa de un recorrido único \\(O(N)\\) a un costo \\(O(N \cdot D)\\) por el re-parseo iterativo de segmentos y el `deepcopy` final en cada hoja.
2. **Recorrido iterativo manual vs. Generador recursivo:** Sustituir la recursión por un bucle con pila explícita en Python puede alterar el orden de evaluación si se usa LIFO en lugar de FIFO, o fallar al gestionar la propagación de excepciones (`ValidationError` ante claves no-string) y métodos del generador (`throw`, `close`).
3. **Caché o memorización en el decodificador de punteros:** Memorizar el parseo de rutas en `pointer_value` falla si las estructuras o los valores de la fila se mutan entre invocaciones dentro de la misma sesión o request.

---

### 4. Decisión finita y criterio de abandono

#### Decisión finita (Plan de acción):
1. **Fase 1 (Instrumentación):** Insertar un wrapper de cronometraje de bajo overhead (`time.perf_counter_ns()`) únicamente en los 5 sitios de llamada identificados por `rg` para `scalar_fields`, registrando tiempo acumulado y conteo en 10 ejecuciones del fixture de 1500 revisiones.
2. **Fase 2 (Evaluación de candidato):** Si y solo si uno de los consumidores concentra >70% del tiempo gastado en recorridos y únicamente requiere las rutas, implementar la función privada `_iter_scalar_paths`.
3. **Fase 3 (Verificación A/B):** Ejecutar comparación A/A y A/B en el runner real midiendo el tiempo de respuesta WSGI/TCP.

#### Criterio de abandono inmediato:
* Abandono automático si la diferencia de p95 en la petición completa entre la variante A y B se encuentra dentro del margen de ruido de las pruebas A/A, o si existe cualquier discrepancia en la validación de tipos, errores `ValidationError` u orden de las rutas RFC6901.

---

¿Avanzamos con la toma de tiempos instrumentada por call site en la suite de pruebas?
```

## 9 · codex · opinion

UTC: 2026-10-11T13:21:39.456886+00:00

```text
Intervención Codex de revisión crítica, ronda2:
- Se suministra abajo respuesta íntegra deNotebookLM de esta sala; segundaopinión, nohechos adicionales. El perfilguardado no incluye callergraph, sólo100mayores getstats; no fingir print_callers recuperable.
- Notebook vuelve a convertir101755reanudaciones en101755diccionarios: falso; sólocada yieldhoja produce dict. Hojasreales requierenconteoindependiente fuera cronometraje.
- Wrapper alrededor scalar_fields(row) cronometraCREACIÓN delgenerador, NOejecución. Wrapper de cada next aumentaeventos ydistorsión; timerexterno a yieldfrom coninicio/final incluyeprocesamiento delconsumidor entreyield. No proporciona distribución exacta. Preferencia Codex: medir consumidorescompletos compile_coverage/coverage_page/required_pages conpocos timerswall+CPU; atribución ampliaexplícita inclproyección/refs, no aislarpurotraversal porresta. Complementar luego corpus materializado ymicrobenchpuro, sinpresentar coste realrequest inferido. Si quieres otro diseño explicaperímetro yoverhead.
- Umbral70% y10instrumentadas inventados, noseadoptan porpredicciónmodel. Sondecisiones de diseño no datoscientíficos. Control/instrumentada/control puedeacotar intrusión, no distribuciónexacta.
- Parsear segmentosmemoSólo delstring puroNO queda invalidado por mutación de fila; cachear valorresuelto sí. Esta vía diferida, no está prohibida por falsa razón. Conservarexcepciones en puntoactual yrevalidación/traversalfrescos.
- LIFO puede preservarDFS siiteradores/ordenhijos correctos; FIFO daríaBFS. Notebook confunde criterioestructura conordenreal. No elegiriterativo ahora.
- rg muestra6archivos consumidores y8sitios externos:catalog1,coverage1,read_gate1,coverage_pages2,access_coverage2,coverage_page1; además2llamadas recursivas internas. No todos están activos en inspect_batch. No tocar módulosque noejecuta elescenario sólo porqueaparecen enrg.
- fast_canonical.reference_check depth>200=>ValueError, exacttypesJSON(null,str,bool,int,floatfinito,dictstr,list,tuple). source_copy convierteids/fechas/importesstr yconserva algunosJSONField days/languages. canonicalguard no prueba dominio universal de scalar_fields/decoder. Público seguiría sin cambios.
- Varianteprivada sólo paths en compile_coverage: podría evitar diccionario, pero duplicar recursión altera presupuestoRecursionError porframes. Prueba equivalenciatipos/mensajes/ordenprimererror ycallstackboundary; no afirmar ansioso elimina semántica deerror/sideeffects de subclases. Candidato NOimplementado ni medido.
- Rechazo alternativa globalcache/pointerresult/authoritychain/nativecode ahora. Mantener comparativasA/A/ABBA, mismoGCpreparaciónfuera, erroresantesydespués. Si aparececandidataconseñal, HTTPclones20/variante equivalentes antesadopción; noaceptacióncontractual ni umbralmsarbitrario.
Solicitud Claude: revisa estas objeciones, identifica cualquiererror nuestro y entrega la versión mínima verificable delplan siguiente con condición de salida ycriterioabandono. ¿Merece diagnóstico de consumidores+corpus antescandidato? No entreguescódigo,noejecutesnada,máx700palabras. No afirmes queelcontexto suple medición faltante.

```

## 10 · codex · request

UTC: 2026-10-11T13:21:47.465994+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Primera deliberación conjunta MOD08. Codex modera; tu función es revisión independiente sin herramientas.
HEAD 7e04016d8ece6cf52388e283eb06cf0a6040fd2b. Sólo datos sintéticos. No modificar producto ni iniciar capacidad completa.
Último diagnóstico: runner20261011-130102-8286f2c3,5PASS98.47s,1176huellas y limpieza comprobadas. PG17/TCP reales,2workers sync calientes; clones idénticos548eventos/256reads tras64POST;3muestras control/perfilada/control con4CoverageRead+8EVENT por commit.
TCP812.239/1882.635/796.736ms;WSGI811.169/1950.134/795.745;CPU428.554/1563.754/425.883. Gran intrusión cProfile(timer=thread_time), NO p95 ni ahorro; WSGI incluye reporte posterior al yield, TCP puede acabar antes.
Fixture1500revisiones,selección16777172bytes,originales64MiB no seleccionados,cobertura parcial escalar; sinCaddy/RustFS/cuotas/concurrencia de carga. NO comparable al p95 contractual383lotes~3.75s y objetivo2s. Descargas5s siguen pendientes, no medir aquí.
Category/Service/Municipality residualCPU trasSQL observado1.765/1.751/1.889ms(~5.4ms); NO coste exacto ni ahorro, candidata valoresprimitivos cerrada porahora. Model.__init__2010calls21.842ownCPU/72.552incl;from_db1993calls18.858/100.158.
scalar_fields101755entradas/reanudaciones(incl72978recursivas),101.493own/147.259inclmsperfilados NO101755recorridos completos. pointer_value9002calls33.366own78.634incl; project_selected2calls14.623own184.502incl; compile_coverage1call13.334own240.489incl.
CandidataSQLinline anterior rechazada tras20muestras/variante clonesABBA:originalmed797.984/p95819.964ms vsinline789.795/829.377ms. Producto restauradoHEAD. MemoJSON no justificó margen; cachechain/autoridad prohibido por frescura/mutaciónpropia/DDL.
Opinión Codex: medir primero sincProfile los recorridos puros, con conteo estructural independiente y mismo fixture, antesde elegir cambio; no inferir147msahorrables. Posible alternativa menos amplia: compile_coverage sólo consume item['path'], explorar generador especializado de rutas sin construir diccionario de cada hoja, manteniendo orden/validación/error y scalar_fields público. No asumir beneficio ni equivalencia. Otra vía pointer_value separada. Traversaliterativo requiere preservar profundidad/RecursionError/mutación duranteyield/close/throw ademásdeRFC6901; códigoiterativoanteriorNotebook con marco3elementos ytop[3]/top[4] es inválido.
Debatid: (1) ¿qué vía medir primero y por qué? (2) diseño mínimo finito limpio separando preparación,cronometraje y validación; corpus ancho/profundo/representativo; no tiempos mínimos inventados. (3) contraejemplos de rutas especializadas vsiterativo vsdecoderpunteros; qué fuente adicional falta. (4) decisión y criterio de abandono sin porcentajes asumidos. No entregar parche sin evidencia. Identifica límites del contexto y corrige conjeturas de Codex. Devuelve hechos/objeciones/plan/decisión, máx900palabras.

Intervención Codex de revisión crítica, ronda2:
- Se suministra abajo respuesta íntegra deNotebookLM de esta sala; segundaopinión, nohechos adicionales. El perfilguardado no incluye callergraph, sólo100mayores getstats; no fingir print_callers recuperable.
- Notebook vuelve a convertir101755reanudaciones en101755diccionarios: falso; sólocada yieldhoja produce dict. Hojasreales requierenconteoindependiente fuera cronometraje.
- Wrapper alrededor scalar_fields(row) cronometraCREACIÓN delgenerador, NOejecución. Wrapper de cada next aumentaeventos ydistorsión; timerexterno a yieldfrom coninicio/final incluyeprocesamiento delconsumidor entreyield. No proporciona distribución exacta. Preferencia Codex: medir consumidorescompletos compile_coverage/coverage_page/required_pages conpocos timerswall+CPU; atribución ampliaexplícita inclproyección/refs, no aislarpurotraversal porresta. Complementar luego corpus materializado ymicrobenchpuro, sinpresentar coste realrequest inferido. Si quieres otro diseño explicaperímetro yoverhead.
- Umbral70% y10instrumentadas inventados, noseadoptan porpredicciónmodel. Sondecisiones de diseño no datoscientíficos. Control/instrumentada/control puedeacotar intrusión, no distribuciónexacta.
- Parsear segmentosmemoSólo delstring puroNO queda invalidado por mutación de fila; cachear valorresuelto sí. Esta vía diferida, no está prohibida por falsa razón. Conservarexcepciones en puntoactual yrevalidación/traversalfrescos.
- LIFO puede preservarDFS siiteradores/ordenhijos correctos; FIFO daríaBFS. Notebook confunde criterioestructura conordenreal. No elegiriterativo ahora.
- rg muestra6archivos consumidores y8sitios externos:catalog1,coverage1,read_gate1,coverage_pages2,access_coverage2,coverage_page1; además2llamadas recursivas internas. No todos están activos en inspect_batch. No tocar módulosque noejecuta elescenario sólo porqueaparecen enrg.
- fast_canonical.reference_check depth>200=>ValueError, exacttypesJSON(null,str,bool,int,floatfinito,dictstr,list,tuple). source_copy convierteids/fechas/importesstr yconserva algunosJSONField days/languages. canonicalguard no prueba dominio universal de scalar_fields/decoder. Público seguiría sin cambios.
- Varianteprivada sólo paths en compile_coverage: podría evitar diccionario, pero duplicar recursión altera presupuestoRecursionError porframes. Prueba equivalenciatipos/mensajes/ordenprimererror ycallstackboundary; no afirmar ansioso elimina semántica deerror/sideeffects de subclases. Candidato NOimplementado ni medido.
- Rechazo alternativa globalcache/pointerresult/authoritychain/nativecode ahora. Mantener comparativasA/A/ABBA, mismoGCpreparaciónfuera, erroresantesydespués. Si aparececandidataconseñal, HTTPclones20/variante equivalentes antesadopción; noaceptacióncontractual ni umbralmsarbitrario.
Solicitud Claude: revisa estas objeciones, identifica cualquiererror nuestro y entrega la versión mínima verificable delplan siguiente con condición de salida ycriterioabandono. ¿Merece diagnóstico de consumidores+corpus antescandidato? No entreguescódigo,noejecutesnada,máx700palabras. No afirmes queelcontexto suple medición faltante.

Respuesta NotebookLM completa:
### 1. Distinción de estado: Hechos, Hipótesis y Evidencia Faltante

* **Hechos medidos:** 
  1. El perfil actual con `cProfile(timer=thread_time)` registra 101.755 invocaciones/reanudaciones en `scalar_fields` (101,5 ms own / 147,3 ms incl. CPU), pero con alta intrusión del profiler.
  2. `scalar_fields` no es exclusivo de `compile_coverage`: el rastreo con `rg` confirma uso en `coverage_read_gate`, `coverage_pages`, `coverage_page`, `catalog` y `accesscoverage`.
  3. La variante anterior de SQL inline fue rechazada tras control A/B/B/A de 20 muestras por degradar el p95 (829,37 ms vs. 819,96 ms) y el producto se encuentra restaurado en HEAD (`7e04016d8e`).
  4. La función `pointer_value` ejecuta `deepcopy` en cada extracción válida y aplica validación estricta RFC6901 (`~1`, `~0`).

* **Hipótesis no demostradas:**
  1. Que los 147 ms atribuibles a `scalar_fields` procedan predominantemente de `compile_coverage`.
  2. Que eliminar la construcción del diccionario `{"path": ..., "value": ...}` impacte de forma medible en el p95 contractual del request (2 s objetivo / 3,75 s actual).

* **Evidencia faltante:**
  1. Desglose real de tiempo por llamador (*call site attribution*) sin la sobrecarga de `cProfile`.
  2. Mediciones A/A y A/B en la pila completa (WSGI/TCP) comparando el impacto global.

---

### 2. ¿Qué medir primero y por qué?

**Acepto medir primero las llamadas completas por call site en un request instrumentado con bajo overhead, rechazando empezar por un microbenchmark aislado.**

Un microbenchmark sobre corpus sintético puede mostrar una reducción relativa de microsegundos al omitir asignaciones de diccionarios, pero es incapaz de revelar si dicho tiempo representa el 5% o el 90% del costo real en la petición WSGI/TCP. Medir en la petición real con temporizadores de baja sobrecarga (`time.perf_counter_ns()` envolviendo las llamadas de cada sitio identificado) proporciona la distribución exacta del costo entre `compile_coverage`, `coverage_read_gate` y el resto de los consumidores.

---

### 3. Evaluación de Claude/Codex, candidato de alcance y contraejemplos

#### Aceptaciones y correcciones a los planteamientos previos:
* **De Claude:** Acepto exigir atribución por *call site* previa a cualquier refactorización y conservar intactos el contrato público y las excepciones `ValidationError`. Rechazo priorizar el microbenchmark de corpus antes de la instrumentación e2e.
* **De Codex:** Confirmo su hallazgo con `rg` que invalida la hipótesis de un único llamador. Aclaro que no debe interpretarse incoherencia entre los 240 ms de `compile_coverage` y los 147 ms de `scalar_fields`, dado que la agregación plana de `cProfile` no preserva la jerarquía de invocaciones.

#### Ámbito de candidato más seguro (sin alterar la API pública):
Si la instrumentación demuestra que el consumidor principal de `scalar_fields` solo necesita el conjunto de rutas y no los valores, el candidato más seguro es un generador privado especializado interno (ej. `_iter_scalar_paths(value, prefix="")`) que retorne directamente las cadenas de texto con la ruta escapada RFC6901. Esto evita instanciar y desechar 101.755 diccionarios intermedios, manteniendo `scalar_fields` y `pointer_value` sin modificaciones.

#### Contraejemplos técnicos a considerar:
1. **Rutas especializadas vs. Re-evaluación con `pointer_value`:** Si un consumidor obtiene únicamente las rutas mediante un generador de cadenas y posteriormente invoca `pointer_value` para cada ruta sobre la estructura original, se pasa de un recorrido único \\(O(N)\\) a un costo \\(O(N \cdot D)\\) por el re-parseo iterativo de segmentos y el `deepcopy` final en cada hoja.
2. **Recorrido iterativo manual vs. Generador recursivo:** Sustituir la recursión por un bucle con pila explícita en Python puede alterar el orden de evaluación si se usa LIFO en lugar de FIFO, o fallar al gestionar la propagación de excepciones (`ValidationError` ante claves no-string) y métodos del generador (`throw`, `close`).
3. **Caché o memorización en el decodificador de punteros:** Memorizar el parseo de rutas en `pointer_value` falla si las estructuras o los valores de la fila se mutan entre invocaciones dentro de la misma sesión o request.

---

### 4. Decisión finita y criterio de abandono

#### Decisión finita (Plan de acción):
1. **Fase 1 (Instrumentación):** Insertar un wrapper de cronometraje de bajo overhead (`time.perf_counter_ns()`) únicamente en los 5 sitios de llamada identificados por `rg` para `scalar_fields`, registrando tiempo acumulado y conteo en 10 ejecuciones del fixture de 1500 revisiones.
2. **Fase 2 (Evaluación de candidato):** Si y solo si uno de los consumidores concentra >70% del tiempo gastado en recorridos y únicamente requiere las rutas, implementar la función privada `_iter_scalar_paths`.
3. **Fase 3 (Verificación A/B):** Ejecutar comparación A/A y A/B en el runner real midiendo el tiempo de respuesta WSGI/TCP.

#### Criterio de abandono inmediato:
* Abandono automático si la diferencia de p95 en la petición completa entre la variante A y B se encuentra dentro del margen de ruido de las pruebas A/A, o si existe cualquier discrepancia en la validación de tipos, errores `ValidationError` u orden de las rutas RFC6901.

---

¿Avanzamos con la toma de tiempos instrumentada por call site en la suite de pruebas?
```

## 11 · claude · opinion

UTC: 2026-10-11T13:22:34.063254+00:00

```text
# Revisión ronda 2 MOD08 (opinión, no PASS)

## Hechos que acepto tal como se suministran
- Perfil guardado: sólo los 100 mayores `getstats`, sin callergraph. No hay atribución por llamador recuperable.
- `scalar_fields`: 101755 entradas o reanudaciones (72978 recursivas). cProfile cuenta cada reanudación del generador. **No se puede derivar de ahí el número de hojas ni de diccionarios.** Tampoco vale la resta 101755−72978: no da hojas.
- Intrusión del perfil: control unos 800 ms frente a perfilada unos 1880 ms. Los 240 ms de `compile_coverage` y los 147 ms de `scalar_fields` son cifras perfiladas. **No se pueden escalar a coste real.**

## Errores de NotebookLM (coincido con Codex)
1. Dice que se crean "101755 diccionarios". Es falso por la razón anterior.
2. Dice que un wrapper con `perf_counter_ns` da una "distribución exacta". Es falso: envolver la llamada mide la creación del generador, y envolver cada `next` añade distorsión.
3. Dice que "`pointer_value` ejecuta `deepcopy` en cada extracción". **No aparece en el contexto suministrado.** Es una afirmación no verificada y no debe circular como hecho.
4. Habla de "5 sitios". Codex reporta 6 archivos, 8 sitios externos y 2 llamadas internas. Además, aparecer en `rg` no implica estar activo en inspect_batch.
5. Confunde LIFO/FIFO con el orden real del recorrido. Además, sus "70%" y "10 ejecuciones" son inventados.
6. Matiz sobre el rechazo de inline: un p95 calculado sobre 20 muestras es casi un máximo y es frágil. El rechazo sigue siendo válido porque las medianas tampoco daban margen claro, pero no conviene citar "degradó p95" como hecho robusto.

## Matices a Codex
- **Timers por consumidor.** Los perímetros deben ser **no solapados**, o hay que contabilizar la exclusividad. Si un consumidor llama a otro instrumentado, se cuenta dos veces. También hay que fijar qué reloj CPU se usa (`thread_time` por worker sync) y mantenerlo igual en todas las variantes.
- **GC.** Dejar de crear diccionarios por hoja cambia la presión de gen0. Conviene registrar los conteos de colecciones antes y después de cada muestra, fuera del cronometraje, como covariable. Si no, un efecto GC se atribuirá al recorrido.
- **Memo de segmentos.** Codex tiene razón: no lo invalida la mutación de fila. Pero tiene objeciones propias: crecimiento sin cota, y no cachear excepciones o, si se cachean, reemitir el mismo tipo, mensaje y orden. Sigue diferida, por esa razón y no por frescura.
- **Generador privado de rutas.** Puede tener exactamente la misma profundidad de frames si replica la estructura de la recursión. Que la cambie es una hipótesis que hay que verificar, no un hecho. `reference_check` (profundidad >200) no acota el dominio de `scalar_fields`.

## Respuesta: ¿diagnóstico de consumidores y corpus antes de candidato?
Sí, pero en **una sola campaña finita**. Hoy no sabemos si `compile_coverage` es el consumidor dominante sin perfilador, ni si el recorrido supera el ruido A/A del request.

## Plan mínimo verificable

**Fase 0. Preparación (sin cronometrar)**
- Mismo HEAD, clones idénticos, fixture verificado y workers calientes.
- Una pasada **sólo de conteo**: invocaciones por sitio activo, hojas producidas y profundidad máxima por consumidor. Esa pasada se descarta para tiempos.
- Materializar en ese momento las entradas reales de cada consumidor activo y serializarlas.

**Fase 1. Atribución por consumidor**
- Build diagnóstico, nunca producto.
- Pocos timers de wall y CPU en perímetros no solapados de los consumidores activos, más el total del request.
- Intercalar control/instrumentada en ABBA para acotar la intrusión.
- El número de muestras se fija antes de empezar y se declara como decisión de diseño. Repetir 20 por variante facilita comparar con la campaña de inline.
- Incluir conteos GC y errores antes y después.

**Fase 2. Corpus y microbenchmark (complemento, no inferencia del request)**
- Corpus materializado más corpus de bordes:
  - estructuras vacías;
  - claves no str;
  - claves con `~` y `/`;
  - bool frente a int y floats no finitos;
  - tuplas;
  - subclases de dict y str;
  - profundidad cerca del límite de recursión;
  - mutación durante el yield, `close` y `throw`;
  - un ancho y un profundo.
- Medir el **coste base** de `scalar_fields` consumido sólo por rutas sobre el corpus materializado, para comprobar su orden frente al timer del consumidor de la Fase 1.

## Condición de salida
La campaña termina cuando hay una tabla con:
- cuota por consumidor, con la cota de intrusión;
- conteos estructurales;
- ruido A/A del request de la misma campaña;
- coste base en el corpus.

Sin parche.

## Decisión y criterio de abandono
- Sólo se abre un candidato (ruta privada en el consumidor dominante) si se cumplen las dos condiciones:
  - el coste de ese consumidor, descontada la cota de intrusión, es **distinguible del ruido A/A medido** en esta campaña;
  - ese consumidor no usa `value` en ninguna parte, verificado en el código.
- **Se abandona la línea de recorrido** si:
  - la intrusión acotada es comparable al coste medido;
  - o el consumidor no es distinguible del A/A;
  - o los conteos muestran que el escenario apenas ejecuta ese sitio.
- `pointer_value` se evalúa sólo con su propia fila en la misma tabla.
- El iterativo, la caché global y el código nativo quedan fuera.
- Cualquier candidato posterior exige:
  - equivalencia de tipos, mensajes y orden del primer error en todo el corpus;
  - HTTP en clones ABBA con 20 por variante.

Aun así, no constituye aceptación contractual: el p95 de 383 lotes y las descargas de 5 s siguen sin medir.

## Límites
No he visto el código de `pointer_value`, `compile_coverage` ni los sitios activos. Nada de esto sustituye a la medición.
```

## 12 · codex · opinion

UTC: 2026-10-11T13:24:19.992993+00:00

```text
Cierre de la sala, Codex modera. Abajo respuesta íntegraClaude2 y códigoexactopointer_value actual. Contrástalos y rectifica tuserrores anteriores; NO iniciar pruebas ni generarpatch. Máx650palabras.
Correcciones propias:
1. Claude2 dice pointer_value.deepcopy noverificado porfalta códigoenesta ronda. Round1 recibió códigoexacto, Round2 es invocaciónindependiente sinhistorialpropio yteníaelresumen. Codex síverificó código: return deepcopy(value), serepiteabajo. No confundir falta decontextodeunturno confalta defuente.
2. Coincido que cProfile147ms y101755 no proporcionahojas/dicts ni ahorro. Tu último generadorpaths NOevitaría101755dicts probados. Corrigeesaafirmación, elumbral70%,5sitios(Losrg6archivos8externos),LIFO/FIFO y parse-memo-frescura: decoderpuroruta noreutilizavalor ydebeestarcotado/erroresenpuntoactual; diferidoporcosteno medido, nomutaciónfila.
3. No haycota rigurosa quepueda restarse alcosteconsumidor: controles sóloobservan cambio/rangosdeintrusión, no overheadcausal porfase. No descontar diferencia controlinstrumentada, ni presentarcuota exactadeCPUtraversal. Usartimerswall+threadCPU pocos yperímetrosclaros condescuento hijosobservados si anidados; noenvolver creación generadoro cada next para prétender precisión. Comenzar consumidoresactivoscompile_coverage,coverage_page/required_pages si realmenteejecutan, registrar ceros. Nada de cambiar8call sites sinrastreoprevio.
4. Guardar corpusvíaJSON alteratuplas/subclases/hojas; fixturefuenteJSONpuededumpconcomprobacióntipoequivalente, casosAPIbordes construir/reconstruirenmemoria fuera tiempo, no normalizarlos paraeliminarcontraejemplos.
5. No comparar valorabsolutoconsumidor frente ruidoTCPpara atribuirahorro; baselinepurecorpus mide coste base, luego una variante necesita diferencial A/A vsA/B comparable, noigualdad simple dep95frágilN20. Observaciones8msinline ruidosas,sinestimar savingsesperadas; p95nearest-rank20 esdato experimentalfrágil,no afirmación robustacolacontractual.
Plan Codexpropuesto para siguiente tarea (noejecutadoporcrear sala): una campaña diagnóstica finita condescripciónfuente/perímetros; conteo estructuralpasada separada yúnico control-instrumentada-control en clonesmismohistorial con2workerswarm, pocosspansporconsumidor, GCfuera timer; corpus representativocongelado másbordes; microbench baselinepuro A/A alternado número fijo prefijado para caracterizar costeyruido (sin varianteproductiva). Sólo preparar candidate privada rutas si patrón de coste repetible yconsumidorpaths-only verificado. Iterativopúblico/cacheautoridad/rewriteORM/deepcopyeliminación quedanfuera. Ningún corte70%,msinventados. Abandono diagnóstico: instrumentaciónnointerpretable frentecontroles oausenciadecosterelevante enfixture; conclusiónno concluyente tambiénválida. Siaparecesignal desarrollar equivalencia completa+microABBA+HTTP20/varianteclonesconcontroles antesadopción en tarea posterior; no reanudar89min/contractual.
Pregunta final: ¿Aceptas esteplan corregido? Señala contraejemplos restantes y diferencias de opinión deClaude2; devuelve decisión condicionada, sin asegurarrendimiento. El cierre lo verificaCodex, consenso noesPASS.

```

## 13 · codex · request

UTC: 2026-10-11T13:24:20.046568+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Cierre de la sala, Codex modera. Abajo respuesta íntegraClaude2 y códigoexactopointer_value actual. Contrástalos y rectifica tuserrores anteriores; NO iniciar pruebas ni generarpatch. Máx650palabras.
Correcciones propias:
1. Claude2 dice pointer_value.deepcopy noverificado porfalta códigoenesta ronda. Round1 recibió códigoexacto, Round2 es invocaciónindependiente sinhistorialpropio yteníaelresumen. Codex síverificó código: return deepcopy(value), serepiteabajo. No confundir falta decontextodeunturno confalta defuente.
2. Coincido que cProfile147ms y101755 no proporcionahojas/dicts ni ahorro. Tu último generadorpaths NOevitaría101755dicts probados. Corrigeesaafirmación, elumbral70%,5sitios(Losrg6archivos8externos),LIFO/FIFO y parse-memo-frescura: decoderpuroruta noreutilizavalor ydebeestarcotado/erroresenpuntoactual; diferidoporcosteno medido, nomutaciónfila.
3. No haycota rigurosa quepueda restarse alcosteconsumidor: controles sóloobservan cambio/rangosdeintrusión, no overheadcausal porfase. No descontar diferencia controlinstrumentada, ni presentarcuota exactadeCPUtraversal. Usartimerswall+threadCPU pocos yperímetrosclaros condescuento hijosobservados si anidados; noenvolver creación generadoro cada next para prétender precisión. Comenzar consumidoresactivoscompile_coverage,coverage_page/required_pages si realmenteejecutan, registrar ceros. Nada de cambiar8call sites sinrastreoprevio.
4. Guardar corpusvíaJSON alteratuplas/subclases/hojas; fixturefuenteJSONpuededumpconcomprobacióntipoequivalente, casosAPIbordes construir/reconstruirenmemoria fuera tiempo, no normalizarlos paraeliminarcontraejemplos.
5. No comparar valorabsolutoconsumidor frente ruidoTCPpara atribuirahorro; baselinepurecorpus mide coste base, luego una variante necesita diferencial A/A vsA/B comparable, noigualdad simple dep95frágilN20. Observaciones8msinline ruidosas,sinestimar savingsesperadas; p95nearest-rank20 esdato experimentalfrágil,no afirmación robustacolacontractual.
Plan Codexpropuesto para siguiente tarea (noejecutadoporcrear sala): una campaña diagnóstica finita condescripciónfuente/perímetros; conteo estructuralpasada separada yúnico control-instrumentada-control en clonesmismohistorial con2workerswarm, pocosspansporconsumidor, GCfuera timer; corpus representativocongelado másbordes; microbench baselinepuro A/A alternado número fijo prefijado para caracterizar costeyruido (sin varianteproductiva). Sólo preparar candidate privada rutas si patrón de coste repetible yconsumidorpaths-only verificado. Iterativopúblico/cacheautoridad/rewriteORM/deepcopyeliminación quedanfuera. Ningún corte70%,msinventados. Abandono diagnóstico: instrumentaciónnointerpretable frentecontroles oausenciadecosterelevante enfixture; conclusiónno concluyente tambiénválida. Siaparecesignal desarrollar equivalencia completa+microABBA+HTTP20/varianteclonesconcontroles antesadopción en tarea posterior; no reanudar89min/contractual.
Pregunta final: ¿Aceptas esteplan corregido? Señala contraejemplos restantes y diferencias de opinión deClaude2; devuelve decisión condicionada, sin asegurarrendimiento. El cierre lo verificaCodex, consenso noesPASS.

Código verificado:
def pointer_value(row, path):
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 500:
        raise ValidationError("Invalid portability field path")
    value = row
    for segment in path[1:].split("/"):
        # RFC6901 escape sequences; reject malformed aliases.
        escaped = segment.replace("~1", "").replace("~0", "")
        if "~" in escaped:
            raise ValidationError("Invalid portability field escape")
        key = segment.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif (
            isinstance(value, list)
            and key.isascii()
            and key.isdecimal()
            and str(int(key)) == key
            and int(key) < len(value)
        ):
            value = value[int(key)]
        else:
            raise ValidationError("Portability field unavailable")
    if isinstance(value, (dict, list)):
        raise ValidationError("Select individual portability fields")
    return deepcopy(value)
Claude ronda2 completa:
# Revisión ronda 2 MOD08 (opinión, no PASS)

## Hechos que acepto tal como se suministran
- Perfil guardado: sólo los 100 mayores `getstats`, sin callergraph. No hay atribución por llamador recuperable.
- `scalar_fields`: 101755 entradas o reanudaciones (72978 recursivas). cProfile cuenta cada reanudación del generador. **No se puede derivar de ahí el número de hojas ni de diccionarios.** Tampoco vale la resta 101755−72978: no da hojas.
- Intrusión del perfil: control unos 800 ms frente a perfilada unos 1880 ms. Los 240 ms de `compile_coverage` y los 147 ms de `scalar_fields` son cifras perfiladas. **No se pueden escalar a coste real.**

## Errores de NotebookLM (coincido con Codex)
1. Dice que se crean "101755 diccionarios". Es falso por la razón anterior.
2. Dice que un wrapper con `perf_counter_ns` da una "distribución exacta". Es falso: envolver la llamada mide la creación del generador, y envolver cada `next` añade distorsión.
3. Dice que "`pointer_value` ejecuta `deepcopy` en cada extracción". **No aparece en el contexto suministrado.** Es una afirmación no verificada y no debe circular como hecho.
4. Habla de "5 sitios". Codex reporta 6 archivos, 8 sitios externos y 2 llamadas internas. Además, aparecer en `rg` no implica estar activo en inspect_batch.
5. Confunde LIFO/FIFO con el orden real del recorrido. Además, sus "70%" y "10 ejecuciones" son inventados.
6. Matiz sobre el rechazo de inline: un p95 calculado sobre 20 muestras es casi un máximo y es frágil. El rechazo sigue siendo válido porque las medianas tampoco daban margen claro, pero no conviene citar "degradó p95" como hecho robusto.

## Matices a Codex
- **Timers por consumidor.** Los perímetros deben ser **no solapados**, o hay que contabilizar la exclusividad. Si un consumidor llama a otro instrumentado, se cuenta dos veces. También hay que fijar qué reloj CPU se usa (`thread_time` por worker sync) y mantenerlo igual en todas las variantes.
- **GC.** Dejar de crear diccionarios por hoja cambia la presión de gen0. Conviene registrar los conteos de colecciones antes y después de cada muestra, fuera del cronometraje, como covariable. Si no, un efecto GC se atribuirá al recorrido.
- **Memo de segmentos.** Codex tiene razón: no lo invalida la mutación de fila. Pero tiene objeciones propias: crecimiento sin cota, y no cachear excepciones o, si se cachean, reemitir el mismo tipo, mensaje y orden. Sigue diferida, por esa razón y no por frescura.
- **Generador privado de rutas.** Puede tener exactamente la misma profundidad de frames si replica la estructura de la recursión. Que la cambie es una hipótesis que hay que verificar, no un hecho. `reference_check` (profundidad >200) no acota el dominio de `scalar_fields`.

## Respuesta: ¿diagnóstico de consumidores y corpus antes de candidato?
Sí, pero en **una sola campaña finita**. Hoy no sabemos si `compile_coverage` es el consumidor dominante sin perfilador, ni si el recorrido supera el ruido A/A del request.

## Plan mínimo verificable

**Fase 0. Preparación (sin cronometrar)**
- Mismo HEAD, clones idénticos, fixture verificado y workers calientes.
- Una pasada **sólo de conteo**: invocaciones por sitio activo, hojas producidas y profundidad máxima por consumidor. Esa pasada se descarta para tiempos.
- Materializar en ese momento las entradas reales de cada consumidor activo y serializarlas.

**Fase 1. Atribución por consumidor**
- Build diagnóstico, nunca producto.
- Pocos timers de wall y CPU en perímetros no solapados de los consumidores activos, más el total del request.
- Intercalar control/instrumentada en ABBA para acotar la intrusión.
- El número de muestras se fija antes de empezar y se declara como decisión de diseño. Repetir 20 por variante facilita comparar con la campaña de inline.
- Incluir conteos GC y errores antes y después.

**Fase 2. Corpus y microbenchmark (complemento, no inferencia del request)**
- Corpus materializado más corpus de bordes:
  - estructuras vacías;
  - claves no str;
  - claves con `~` y `/`;
  - bool frente a int y floats no finitos;
  - tuplas;
  - subclases de dict y str;
  - profundidad cerca del límite de recursión;
  - mutación durante el yield, `close` y `throw`;
  - un ancho y un profundo.
- Medir el **coste base** de `scalar_fields` consumido sólo por rutas sobre el corpus materializado, para comprobar su orden frente al timer del consumidor de la Fase 1.

## Condición de salida
La campaña termina cuando hay una tabla con:
- cuota por consumidor, con la cota de intrusión;
- conteos estructurales;
- ruido A/A del request de la misma campaña;
- coste base en el corpus.

Sin parche.

## Decisión y criterio de abandono
- Sólo se abre un candidato (ruta privada en el consumidor dominante) si se cumplen las dos condiciones:
  - el coste de ese consumidor, descontada la cota de intrusión, es **distinguible del ruido A/A medido** en esta campaña;
  - ese consumidor no usa `value` en ninguna parte, verificado en el código.
- **Se abandona la línea de recorrido** si:
  - la intrusión acotada es comparable al coste medido;
  - o el consumidor no es distinguible del A/A;
  - o los conteos muestran que el escenario apenas ejecuta ese sitio.
- `pointer_value` se evalúa sólo con su propia fila en la misma tabla.
- El iterativo, la caché global y el código nativo quedan fuera.
- Cualquier candidato posterior exige:
  - equivalencia de tipos, mensajes y orden del primer error en todo el corpus;
  - HTTP en clones ABBA con 20 por variante.

Aun así, no constituye aceptación contractual: el p95 de 383 lotes y las descargas de 5 s siguen sin medir.

## Límites
No he visto el código de `pointer_value`, `compile_coverage` ni los sitios activos. Nada de esto sustituye a la medición.
```

## 14 · notebook · error

UTC: 2026-10-11T13:24:22.994156+00:00

```text
Empty answer; inspect raw artifact
```

## 15 · codex · decision

UTC: 2026-10-11T13:26:33.760887+00:00

```text
Cierre de Codex: deliberación terminada con dos opiniones de Claude, una de NotebookLM y contraste local de código. Cuarto turno (cierre NotebookLM) rechazado query request invalid; preservado sin retry. No hay consenso final confirmado por NotebookLM.
Decisión: diagnosticar consumidores completos y coste base puro antes de crear candidata. Conteos estructurales fuera del tiempo; control/instrumentada/control de clones idénticos, timerswall+CPU por pocosconsumidores activos conperímetro declarado, sincProfile ni descuento causal de overhead; corpus representativo/bordes ybaselineA/A sinnormalizarcontraejemplosJSON. No ejecutar campaña enesta entrega de sala.
Candidata sólo condicional: rutas privadas en consumidorpaths-only si coste interpretable/repetible; equivalenciaerrores/tipos/orden/profundidad ymicroA/A-A/B+HTTPcomparables antesadopción. Abandonarante divergencia o señal no distinguible delruido comparable. No cortes70%/msinventados, no101755dicts ni147msahorrables; no cacheautoridad, omitirvalidación ni tocar generadorpúblico ahora.
Fuentes productivas intactas. Nueve controles unitarios de sala PASS; tres respuestas reales verificanCLI, no rendimiento. Acta: docs/evidencias/mod08-salon-deliberacion-20261011.md. MOD08general/capacidad siguenpausados; objetivos2s/5spendientes.
```

## 16 · codex · context

UTC: 2026-10-11T13:52:30.583785+00:00

```text
# MOD08 — Consumidores y coste base de campos/punteros — 2026-10-11

Campaña autorizada por «Procede pues con lo que se propone», tras
[la sala de deliberación](mod08-salon-deliberacion-20261011.md).
Runner final `20261011-134116-08cc3941`: **10 PASS/0 fallos/errores/skips**, 112.021s JUnit.
1208 entradas del mapa de fuentes verificadas exactamente antes de documentar; PostgreSQL,
Redis, runner y Gunicorn propios ausentes comprobados independientemente. HEAD `7e04016d`.
Código productivo intacto. [Datos, muestras y negativa previa](mod08-scalar-consumers-20261011.json).

## Resultado y decisión

La pista del profiler queda acotada: hay **27163 hojas**, no 101755 diccionarios. El
recorrido que construye conjuntos de rutas cuesta unos **23.059ms** de mediana en el
corpus representativo, y resolver sus **4501 punteros seleccionados**, **6.305ms**.
Son costes del código original consumido de esas formas; **no son ahorros ni una
descomposición exacta del request**.

No se prepara ni aplica una candidata productiva en esta campaña. El coste base observado
es modesto para justificar una reescritura orientada a resolver el déficit de segundos del
escenario contractual. No se demuestra que toda optimización local sea inútil: podría
existir una mejora pequeña, pero no se ha comparado una variante. El acuerdo entre modelos
no sustituye esa evidencia. Se cierra este diagnóstico, conservando el instrumento y
dejando la API pública, autoridad, consultas frescas y auditoría intactas.

`compile_coverage` es el consumidor que enumera todas las hojas en este request, y sólo
usa sus rutas. Las cuatro páginas apenas añaden 108 hojas. La construcción de la fuente
es un perímetro mayor, pero incluye materialización, consultas y trabajo no separado;
no se atribuye su residual a ORM puro ni se reabre la precarga de relaciones ya descartada.

## Método y perímetros

Cuatro archivos nuevos sólo en tests: `capacity_scalar_diagnostic.py`,
`capacity_scalar_wsgi.py`, `test_capacity_scalar_diagnostic.py` y
`test_capacity_scalar_consumers_http.py`. Se reutilizan los helpers existentes de
servidor, roles y clones, sin modificarlos. No cProfile ni hooks SQL/fetch/pipeline/next.

Fixture sintético: 1500 revisiones, selección de 16777214 bytes, originales retenidos
de aproximadamente 64MiB no seleccionados y cobertura parcial escalar. Aprobación con
31 lecturas paginadas reales; historial mediante 64 POST reales: 548 eventos y 256
lecturas de cobertura. Rol LOGIN runtime separado, PostgreSQL17/Redis propios y dos
workers Gunicorn sync calientes mediante POST comprobados.

Cada petición medida usa un clon idéntico con nueva conexión y commit normal. Inspección
independiente después del commit comprueba cuatro lecturas y ocho eventos añadidos.
Preparación y warmups fuera de cifras. Sin Caddy/RustFS, cuotas contractuales ni carga
concurrente. Tres tiempos HTTP no forman un p95 ni aceptan 2s/5s o dos casos.

La cuarta petición usa otro clon y se dedica a contar, con sus tiempos descartados.
Se envuelven aliases de `scalar_fields` en consumidores; la definición recursiva original
no se parchea. El conteo estructural separado calcula filas, hojas, contenedores,
profundidad y rutas sin conservar valores. Censo y SHA de la fuente recibida en el
worker coinciden con el corpus materializado del padre.

## Tres peticiones control/spans/control

| Muestra | TCP completo | WSGI | CPU de hilo | PID | Colecciones GC 0/1/2 |
| --- | ---: | ---: | ---: | ---: | --- |
| Control anterior | 1645.055ms | 1643.470ms | 911.186ms | 200149 | 68/6/1 |
| Spans | 1664.316ms | 1672.298ms | 938.915ms | 200148 | 71/6/1 |
| Control posterior | 1620.490ms | 1619.004ms | 882.591ms | 200148 | 67/6/0 |

Dos workers calientes, pero distintos PIDs medidos. Las colecciones GC también difieren.
El scope y su restauración se incluyen en WSGI; preparar/escribir el reporte y capturar
estadísticas GC quedan fuera de ese reloj. El cuerpo TCP puede terminar antes del cierre
WSGI. No restar diferencias como overhead causal ni como ganancia ajustada.

La primera tanda fallida, con el mismo método HTTP, tuvo controles 801/769ms. La variación
entre tandas es grande y afecta también a CPU; no se ha identificado su causa. No atribuir
la diferencia al cambio de nombre del arnés ni a una optimización: no hubo variante.

## Consumidores completos, sólo petición instrumentada

| Función | Calls | Wall inclusivo | CPU inclusiva | Wall exclusivo | CPU exclusiva |
| --- | ---: | ---: | ---: | ---: | ---: |
| source_copy | 1 | 405.580ms | 251.397ms | 405.580ms | 251.397ms |
| compile_coverage | 1 | 42.851ms | 42.837ms | 31.289ms | 31.275ms |
| project_selected | 2 | 64.789ms | 64.789ms | 64.789ms | 64.789ms |
| coverage_page | 4 | 0.414ms | 0.407ms | 0.414ms | 0.407ms |

`required_pages`, `inspect_catalog`, `prepare_page` y `access_compile_coverage` no se
observaron. Eso no prueba coste cero de esas funciones en otros recorridos. Exclusivo
descuenta sólo hijos observados: una llamada a `project_selected` está dentro de
`compile_coverage`, la otra fuera. No sumar inclusivos ni interpretar los 31ms como
tiempo puro de `scalar_fields`; incluyen referencias, conjuntos, decisiones y otra lógica.

## Conteo independiente

| Sitio observado | Invocaciones externas | Hojas producidas |
| --- | ---: | ---: |
| compile_coverage, línea 66 | 1502 | 27163 |
| coverage_page, línea 43 | 4 | 108 |

Los 1502 objetos son 1500 revisiones, un perfil y una cuenta sujeto. Censo total de ese
corpus: 40682 nodos, 13519 contenedores, 10484 vacíos; profundidad máxima 3, suma de
profundidades de hojas 33458 y 336156 caracteres de rutas (máximo 27). No hay claves con
escapes en este fixture; se cubren en el corpus adicional. Las hojas son str/None/bool/int.
No equivale a un censo exhaustivo de los dominios permitidos por las API públicas.

## Baseline puro original A/A

Se ejecuta en el padre después de terminar Gunicorn, sin lecturas DB dentro del tiempo.
Preparación, validación de resultados y estadísticas GC fuera del cronometraje; estado GC
conservado. Dos warmups descartados por operación, luego `ABBA × 5`: 20 muestras,
10 por etiqueta. **A y B ejecutan exactamente el mismo código original.**

| Operación, corpus representativo | Resultados por muestra | Mediana wall | Mediana CPU | Rango wall | Desv. poblacional wall |
| --- | ---: | ---: | ---: | --- | ---: |
| Conjuntos de rutas por fila | 27163 | 23.059ms | 23.056ms | 21.599–27.745ms | 1.433ms |
| Conteo de hojas | 27163 | 21.001ms | 20.957ms | 20.289–31.571ms | 2.647ms |
| Punteros seleccionados | 4501 | 6.305ms | 6.280ms | 5.610–7.948ms | 0.558ms |

Medianas wall A/B: rutas 23.013/23.059ms, conteo 20.829/21.246ms y punteros
6.343/6.237ms. Cero colecciones GC durante estos intervalos. Ese A/A caracteriza esta
medición pura, no el ruido TCP ni un supuesto ahorro. Rutas incluye formar conjuntos;
conteo incluye consumir el generador; punteros incluye descartar el valor devuelto. No
se atribuye toda la proyección a `pointer_value` ni se elimina su `deepcopy`.

Corpus adicional de cuatro filas: objeto ancho de 256 hojas, rama de profundidad 64,
escapes RFC6901 y un contenedor vacío. 259 hojas, profundidad máxima 65, ruta máxima
389 caracteres. Conjuntos 0.184ms, conteo 0.167ms y tres punteros 0.023ms de mediana;
no son cifras del request. Resultados y censo idénticos antes/después, sin normalizar
mediante JSON. Tests separados cubren subclases/tuplas/bool/float no finito, raíz escalar,
clave inválida, escapes y límites de rutas, mutación entre yields, close/throw y RecursionError.

## Incidente y verificación

Primera tanda `20261011-133814-09f90cce`: 8 PASS/1 FAIL/0 errores/skips, 94.805s JUnit,
fuentes congeladas y retirada propia comprobada. Falló después de HTTP/conteo, al
preparar el corpus de punteros: el dict `body` quedó oculto por la función `body()` que
creaba el POST. Se renombró `request_body` después del terminal y se completó el corpus
ancho/profundo/escapes. No se declara aquella tanda PASS ni se suman sus tests a la final.

La tanda corregida tiene nueve casos unitarios y una integración PG/TCP real, todos PASS.
Checks de Ruff, Django, migraciones y documentación incluidos en el runner; la documentación
final se verifica aparte. El mapa completo de fuentes coincide exactamente y la ausencia
de contenedores de ambas tandas y procesos propios se comprobó por inventario independiente.
No queda un benchmark de esta campaña ejecutándose. MOD08 general sigue pausado y sus
objetivos contractuales permanecen pendientes.

```
