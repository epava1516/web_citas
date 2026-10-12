# Validar sin reconstruir la fuente completa

Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

## 1 · user · authorization

UTC: 2026-10-11T19:14:09.865231+00:00

```text
Autorización persistente recibida del usuario: «Sí, excepción solo para deliberar». Claude CLI exclusivamente revisor sin herramientas locales ni edición y con registro real de consumo. La instrucción actual «Adelante» autoriza esta deliberación con Claude y Notebook sobre consumidores paginados; no es delegación escritora ni excepción nueva. No habilitar herramientas en esta sala.

```

## 2 · codex · opinion

UTC: 2026-10-11T19:15:03.396656+00:00

```text
Revisión MOD08/web_citas español, propuestas no son evidencia ni autorización de editar/ejecutar. Notebook tiene arquitectura histórica pero este código/resultados son estado nuevo. No omitir comprobaciones frescas ni prometer SLO por etapas.

MEDIDAS: Prototipo DATOS 1500Revision16MiB, chunkscifrados<=50filas, originalfull199ms→página21ms/prep1.753s. No autoridad/fuente completa. Variante conservadora hash FÍSICO fresco contenido todasfamilias inputs antes/después: full404.347→página352.524ms(51.824ms/12.82%),19/20wall20/20CPU/cuatro bloques favorables; prep1.785s. NO prueba que doblehash sea requisito universal; es estrategiafuerte escogida para cacheentre requests, falta catálogo/permisos/restore/locks. Segunda prueba recuperó30chunks en UNA consulta, descifrómanifiesto1vez/headercifrado separado, reconstruyó dictcompleto y conservó inspection_source HMAC/mutación/bracketderiva original: full411.695→649.771ms(+57.83%),0/20wall, CPU235.511→238.620ms9/20wins/prep1.760s. Lowerbound porque faltan locks/catálogos/callbacksexpiry. GateREJECT integraciónDIRECTA que mantiene dictcompleto; no rechazar universalmente API nueva. 2pytestPASS acreditanexperimentos, no beneficio/N2/endpoint.

CONTEXTO: históriconavegaciónp953.753s383lotes,target2s; JSON6.930/bin7.318target5s peroN3/8 insuficientes. Clones nuevos548EVENT/1500Revision*sin*binariosentregados; no mezclar p95/CPU/etapas ni sumarahorros. Source_copy completo ya1vezporbatch, referencias puras memo intrarequest+summarycache+batch_projection existentes. Canonical Cython nativo. AES/Fernet actual. Todas23authorize/reviewer_case/proof/latest/catalog/fullchain frescas y cadaauditoría cambiacadena. No cacheauthority/triggers, head/counter/Merkle sólono prueba fuente física; cambiosDDL/owner puedenrestaurarhelper y dejardigestGENERATEDantiguo. assessment/selection/coverage susceptiblespurga/expiry. Imagebytesfrescas en S3 y guards despuésesperas.

CODEX HIPÓTESIS NUEVA: separar validación de selección/coverage de emitir valores. record(_audit_only=True) hoy aún construyeproyección enprimermiss aunque devuelveNone; compile_coverage llama project_selected y devuelve projection pero coverage_page final filtra summary sin projection. Primero validate_only sobre FUENTE FRESCA ACTUAL, sin cachepersistente ni nuevostorage: ahorro sólo valores/alloc, no evita source_copy16MiB. Es paso previo explícito y falsable, no promesa177msni2s. Después APIinventario autenticado(dataset,index,row_reference,scalar_paths,metadatafotos)+lectura campospágina podríaevitarmaterialización, pero HMACsource_digest NOsecompone de rowrefs, frescura+origen+caller/permisos/DDL/expiry/restore por demostrar. No contenedores lazydisfrazados ni confiar firmas como reloj; nunca autoridad/revisión almacenada.

CÓDIGO selección COMPLETO actual:
"""Explicit scalar field selection; caller must bind selectors to approved evidence."""

from copy import deepcopy

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

from .fast_canonical import content_reference
from .rights_copy_inspection import SECTIONS
from .rights_portability import DATASETS, checked_assessment


def row_reference(dataset, index, row):
    from .rights_inspection_source import shared_row_reference

    return shared_row_reference(
        dataset, index, row,
        lambda: content_reference({"dataset": dataset, "index": index, "row": row}),
    )


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


@sensitive_variables()
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

compile_coverage ACTUAL (resumen fiel): checked_assessment; rechaza pending; siempre projection=project_selected(source,assessment,selection,field_evidence). checked_images contra source/digestsdeclarados. Porcada DATASET SECTIONS[name](source), lenrows; excluded exigeomisionesvacías. Resto recorre todosindex,row: reference=row_reference, paths=_scalar_paths; missing=paths-selected; omisiones{"all":excluded} o {"fields":decisionesexcluded}; subset/exact segúnallow_partial; contabiliza included/excluded/pending. Rechazaomisionesextra/noexistentes. Fotos=[image["photo"] for row in source["revisions"] for image in row["images"]], rechaza duplicados; cobertura binaria. Resultado schema/datasets/included_images/excluded_images/projection +pending/complete si parcial.

inspection_source ACTUAL: __init__ source_fingerprint antes→source_copycompleto→HMACcanonical_bytes(source). get sólo ContextVaridentidad/connection/atomic/scopecasepersonlistingversion. shared_row_reference memo(dataset,index) sólo si rowidentity pertenecefuentecontextual. ExitHMACsource intacto y fingerprinttotal fresco, si diferencia releefullfuente y comparaHMAC; resetfinally. No cacheentre requests. Callerperson/listing puedecontenerrelacionescached; cachépersistentedebe demostrarvínculoexacto. source_digest(context) sóloHMACcontext, sincontextfreshfull. No suprimir exit mutación/deriva.

inspect_page: reviewer_case/authorize; coverage SELECTFORUPDATE(of=self)+relaciones. inspection_sourcenuevo/reusado. record(_audit_only=True) conauditoría/validate_approved_assessment/selection_evidence frescos. authorized_proof/validate_approved_selection/latest; comparaHMACsource. RightsActioncrea/valida; author=User.objects.getFRESCO; baseline_body, unseal factsselection y assessmentcurrent. summarykey coverage/source/selectiondigests; misscompile_coverage(...allow_partial=True). authorize/proof/digest; coverage_page devuelve fieldsactualespaginados y summary={k:v for k,v in summary.items() if k!='projection'}. RightsPortabilityCoverageRead +guards al salir.

batch_projection ACTUAL: ContextVar/mismaconnection/sourceidentity/actor/session/mfa/case/proof. Key case/versión/proof/expiry/row/ciphertextassessmentselection/payloads/settings/operation, entradasmax4 limpiadasfinally. Keymiss project_selected producevalorescompletos, _audit_only guarda sentinelVALIDATED_ONLY/devuelveNone. Hit audit evitaoperación. Otrosretornos deepcopy. Cadaentrada trasvalidaciónfresh; ahorro nuevo no4x primeraoperaciónporque memo yaexiste. No tocarautoridad.

SOLICITUD (máximo~1200palabras):
1 UNA candidata mínima distinta para primer experimento (o ninguna justificable), archivos/API/pseudocódigo y rutaordinaryintacta. No asumir APIinventarioyaexiste.
2 ¿validate_only evita construirvalores conservando errores/orden de pointer_value RFC6901malformed/listindexnocanónico/containerleaf, granular/duplicados etc? Qué se demuestraN1 yquéposiblecambioobservable se descarta.
3 FuturoinventarioDATOS: binding alHMACoriginal+freshness+permisos/callbacks/DDL/expiry, contraejemploquedescartaría. No vendersignature comoautorizaciónactualni TTLcomopruebavigencia. Enumera qué sigue leyendo cuerpos completos. Ahorro sólohipótesisnoobjetivo2s.
4 Experimento finito N1+benchmarkABBA sobre fuenteactualsinpersistencia, wall/CPU/alloc/bytesproyección, gate ydescarte; N2/HTTP sólo si gana. Alternativaautorizacionesuna vez estáprohibida.

```

## 3 · codex · request

UTC: 2026-10-11T19:15:03.484996+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Revisión MOD08/web_citas español, propuestas no son evidencia ni autorización de editar/ejecutar. Notebook tiene arquitectura histórica pero este código/resultados son estado nuevo. No omitir comprobaciones frescas ni prometer SLO por etapas.

MEDIDAS: Prototipo DATOS 1500Revision16MiB, chunkscifrados<=50filas, originalfull199ms→página21ms/prep1.753s. No autoridad/fuente completa. Variante conservadora hash FÍSICO fresco contenido todasfamilias inputs antes/después: full404.347→página352.524ms(51.824ms/12.82%),19/20wall20/20CPU/cuatro bloques favorables; prep1.785s. NO prueba que doblehash sea requisito universal; es estrategiafuerte escogida para cacheentre requests, falta catálogo/permisos/restore/locks. Segunda prueba recuperó30chunks en UNA consulta, descifrómanifiesto1vez/headercifrado separado, reconstruyó dictcompleto y conservó inspection_source HMAC/mutación/bracketderiva original: full411.695→649.771ms(+57.83%),0/20wall, CPU235.511→238.620ms9/20wins/prep1.760s. Lowerbound porque faltan locks/catálogos/callbacksexpiry. GateREJECT integraciónDIRECTA que mantiene dictcompleto; no rechazar universalmente API nueva. 2pytestPASS acreditanexperimentos, no beneficio/N2/endpoint.

CONTEXTO: históriconavegaciónp953.753s383lotes,target2s; JSON6.930/bin7.318target5s peroN3/8 insuficientes. Clones nuevos548EVENT/1500Revision*sin*binariosentregados; no mezclar p95/CPU/etapas ni sumarahorros. Source_copy completo ya1vezporbatch, referencias puras memo intrarequest+summarycache+batch_projection existentes. Canonical Cython nativo. AES/Fernet actual. Todas23authorize/reviewer_case/proof/latest/catalog/fullchain frescas y cadaauditoría cambiacadena. No cacheauthority/triggers, head/counter/Merkle sólono prueba fuente física; cambiosDDL/owner puedenrestaurarhelper y dejardigestGENERATEDantiguo. assessment/selection/coverage susceptiblespurga/expiry. Imagebytesfrescas en S3 y guards despuésesperas.

CODEX HIPÓTESIS NUEVA: separar validación de selección/coverage de emitir valores. record(_audit_only=True) hoy aún construyeproyección enprimermiss aunque devuelveNone; compile_coverage llama project_selected y devuelve projection pero coverage_page final filtra summary sin projection. Primero validate_only sobre FUENTE FRESCA ACTUAL, sin cachepersistente ni nuevostorage: ahorro sólo valores/alloc, no evita source_copy16MiB. Es paso previo explícito y falsable, no promesa177msni2s. Después APIinventario autenticado(dataset,index,row_reference,scalar_paths,metadatafotos)+lectura campospágina podríaevitarmaterialización, pero HMACsource_digest NOsecompone de rowrefs, frescura+origen+caller/permisos/DDL/expiry/restore por demostrar. No contenedores lazydisfrazados ni confiar firmas como reloj; nunca autoridad/revisión almacenada.

CÓDIGO selección COMPLETO actual:
"""Explicit scalar field selection; caller must bind selectors to approved evidence."""

from copy import deepcopy

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

from .fast_canonical import content_reference
from .rights_copy_inspection import SECTIONS
from .rights_portability import DATASETS, checked_assessment


def row_reference(dataset, index, row):
    from .rights_inspection_source import shared_row_reference

    return shared_row_reference(
        dataset, index, row,
        lambda: content_reference({"dataset": dataset, "index": index, "row": row}),
    )


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


@sensitive_variables()
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

compile_coverage ACTUAL (resumen fiel): checked_assessment; rechaza pending; siempre projection=project_selected(source,assessment,selection,field_evidence). checked_images contra source/digestsdeclarados. Porcada DATASET SECTIONS[name](source), lenrows; excluded exigeomisionesvacías. Resto recorre todosindex,row: reference=row_reference, paths=_scalar_paths; missing=paths-selected; omisiones{"all":excluded} o {"fields":decisionesexcluded}; subset/exact segúnallow_partial; contabiliza included/excluded/pending. Rechazaomisionesextra/noexistentes. Fotos=[image["photo"] for row in source["revisions"] for image in row["images"]], rechaza duplicados; cobertura binaria. Resultado schema/datasets/included_images/excluded_images/projection +pending/complete si parcial.

inspection_source ACTUAL: __init__ source_fingerprint antes→source_copycompleto→HMACcanonical_bytes(source). get sólo ContextVaridentidad/connection/atomic/scopecasepersonlistingversion. shared_row_reference memo(dataset,index) sólo si rowidentity pertenecefuentecontextual. ExitHMACsource intacto y fingerprinttotal fresco, si diferencia releefullfuente y comparaHMAC; resetfinally. No cacheentre requests. Callerperson/listing puedecontenerrelacionescached; cachépersistentedebe demostrarvínculoexacto. source_digest(context) sóloHMACcontext, sincontextfreshfull. No suprimir exit mutación/deriva.

inspect_page: reviewer_case/authorize; coverage SELECTFORUPDATE(of=self)+relaciones. inspection_sourcenuevo/reusado. record(_audit_only=True) conauditoría/validate_approved_assessment/selection_evidence frescos. authorized_proof/validate_approved_selection/latest; comparaHMACsource. RightsActioncrea/valida; author=User.objects.getFRESCO; baseline_body, unseal factsselection y assessmentcurrent. summarykey coverage/source/selectiondigests; misscompile_coverage(...allow_partial=True). authorize/proof/digest; coverage_page devuelve fieldsactualespaginados y summary={k:v for k,v in summary.items() if k!='projection'}. RightsPortabilityCoverageRead +guards al salir.

batch_projection ACTUAL: ContextVar/mismaconnection/sourceidentity/actor/session/mfa/case/proof. Key case/versión/proof/expiry/row/ciphertextassessmentselection/payloads/settings/operation, entradasmax4 limpiadasfinally. Keymiss project_selected producevalorescompletos, _audit_only guarda sentinelVALIDATED_ONLY/devuelveNone. Hit audit evitaoperación. Otrosretornos deepcopy. Cadaentrada trasvalidaciónfresh; ahorro nuevo no4x primeraoperaciónporque memo yaexiste. No tocarautoridad.

SOLICITUD (máximo~1200palabras):
1 UNA candidata mínima distinta para primer experimento (o ninguna justificable), archivos/API/pseudocódigo y rutaordinaryintacta. No asumir APIinventarioyaexiste.
2 ¿validate_only evita construirvalores conservando errores/orden de pointer_value RFC6901malformed/listindexnocanónico/containerleaf, granular/duplicados etc? Qué se demuestraN1 yquéposiblecambioobservable se descarta.
3 FuturoinventarioDATOS: binding alHMACoriginal+freshness+permisos/callbacks/DDL/expiry, contraejemploquedescartaría. No vendersignature comoautorizaciónactualni TTLcomopruebavigencia. Enumera qué sigue leyendo cuerpos completos. Ahorro sólohipótesisnoobjetivo2s.
4 Experimento finito N1+benchmarkABBA sobre fuenteactualsinpersistencia, wall/CPU/alloc/bytesproyección, gate ydescarte; N2/HTTP sólo si gana. Alternativaautorizacionesuna vez estáprohibida.

```

## 4 · claude · opinion

UTC: 2026-10-11T19:16:07.220917+00:00

````text
# Opinión técnica: MOD08 / web_citas, validación sin construir valores

Esto es una opinión técnica. No es un PASS ni autoriza a editar o ejecutar nada.

## Clasificación de la evidencia

- **Hechos medidos:**
  - Doble hash físico: 404.347→352.524 ms (−12.82%), 19/20 bloques en wall.
  - Integración directa con dict completo: +57.83% en wall, 0/20 bloques en wall y 9/20 en CPU. El gate fue REJECT.
  - Los dos pytest PASS sólo acreditan que los experimentos corren.
- **Hipótesis:** omitir valores en `_audit_only` ahorra asignaciones.
- **Evidencia faltante:**
  - Tipos reales de las hojas.
  - Consumidores de `projection` en `compile_coverage`.
  - Comportamiento del sentinel ante un hit entre operaciones.
  - Cualquier p95 nuevo.

## 1. Candidata mínima única

El alcance se limita al miss de `_audit_only` en `batch_projection`. `compile_coverage` y `coverage_page` no se tocan, porque quitar `projection` del resultado cambiaría su esquema y su consumidor no está inventariado.

**Archivo de selección:**

```python
def _walk_pointer(row, path):   # cuerpo actual de pointer_value SIN deepcopy, mismos raises
    ...
    if isinstance(value, (dict, list)):
        raise ValidationError("Select individual portability fields")
    return value

def pointer_value(row, path):    # ruta ordinaria: semántica idéntica
    return deepcopy(_walk_pointer(row, path))

def _selected_core(source, assessment, selection, field_evidence, leaf):
    # cuerpo actual de project_selected, misma secuencia de checks;
    # sustituye pointer_value por leaf(row, path)
    ...

@sensitive_variables()
def project_selected(source, assessment, selection, *, field_evidence=None):
    return _selected_core(..., leaf=pointer_value)            # salida idéntica

@sensitive_variables()
def validate_selected(source, assessment, selection, *, field_evidence=None):
    _selected_core(..., leaf=_check_leaf)   # sin construir output
    return None
```

**Uso en `batch_projection`:** en un miss con `_audit_only`, se llama a `validate_selected` en lugar de `project_selected` y se guarda `VALIDATED_ONLY`. Las claves, la frescura, el límite de 4 entradas y la limpieza en `finally` no cambian.

**Lo que no ahorra:**
- `source_copy` de 16 MiB.
- El HMAC.
- `row_reference` sobre todas las filas, que ya está memoizado.
- La autoridad.

## 2. ¿Conserva errores y orden?

Sí, siempre que `_check_leaf` reproduzca exactamente lo que hoy observa la ruta ordinaria.

**Lo que se conserva por construcción**, al compartir `_walk_pointer` y `_selected_core`:
- Escapes RFC6901 malformados (`~2`, `~` final).
- Índices no canónicos (`01`, `-1`, `+1`, dígitos no ASCII como `١`, índices fuera de rango).
- Hoja que es contenedor.
- Selección distinta de `eligible` y `field_evidence` inexacto.
- Filas duplicadas, rutas vacías, duplicadas o no-str.
- Evidencia granular no `eligible`.
- Filas sobrantes en la evidencia.
- El orden de evaluación: datasets ordenados, luego selectores, luego paths en orden de lista.

**Contraejemplo crítico:** `deepcopy` forma parte de lo observable. Si una hoja no es copiable (objeto propio, lock, generador), hoy se lanza `TypeError` en el path 1. Un validador sin copia seguiría avanzando y lanzaría otra cosa, o nada, en el path 2. Los `datetime` sí se reconstruyen sin error.

Hay dos salidas posibles:
- **(a)** `_check_leaf` hace `deepcopy` y descarta el resultado. Conserva errores y orden, pero sólo ahorra el dict de salida y las listas.
- **(b)** Se demuestra antes, con evidencia, que las hojas tras `canonical_bytes` son sólo `{str, int, float, bool, None}`. Para esos tipos `deepcopy` devuelve el mismo objeto y no puede fallar.

**Recomendación: empezar por (a).** Es la variante segura.

**Qué demuestra N1:** equivalencia diferencial del resultado (tipo de excepción, mensaje y primer fallo, o éxito con `None`) frente a `project_selected` sobre el mismo corpus. Además, que el sentinel nunca se devuelve como valores ante un hit de una operación no-audit.

**Qué descarta N1:** divergencias en errores u orden, y la fuga del sentinel.

**Qué no demuestra N1:** el beneficio, el p95, ni el comportamiento de N2 o del endpoint.

## 3. Futuro inventario de DATOS: sólo hipótesis

**Binding mínimo exigible:**
- El inventario se calcula dentro del mismo `inspection_source` y sobre la misma fuente fresca.
- Su digest lleva HMAC sobre el HMAC completo de la fuente y los bytes canónicos del inventario.
- Al salir se verifica el fingerprint total.
- Caller, permisos, versión de DDL y owner se leen frescos en cada request.

Una firma prueba origen, no vigencia ni autorización actual. Un TTL no es prueba de nada.

**Lo que sigue leyendo cuerpos completos**, de modo que el ahorro no se acerca a 2 s:
- `source_fingerprint` antes y después, y la relectura si hay diferencia.
- `source_copy` y `canonical_bytes`.
- `content_reference` de cada fila, porque `row_reference` depende del contenido.
- `_scalar_paths` sobre todas las filas en coverage.
- Bytes de imágenes en S3 y `checked_images`.
- Las 23 comprobaciones frescas: authorize, reviewer_case, proof, latest, catalog y fullchain.

**Contraejemplos que descartarían el inventario:**
- Un cambio de DDL u owner restaura el helper y deja el digest `GENERATED` antiguo. El inventario coincide con el digest pero no con la fuente física.
- Se purga o expira assessment, selection o coverage entre el inventario y la lectura.
- Se revoca un permiso a mitad de request.
- Un restore deja contenido idéntico y, por tanto, el mismo rowref, pero con otro caller o case.
- Una mutación conserva el head, el counter o el Merkle y altera el físico.
- Un `source_digest(context)` sin fuente fresca completa.

Cualquiera de ellos, si es reproducible, invalida el diseño.

## 4. Experimento finito

**N1, corrección:**
- Corpus explícito con los casos del punto 2.
- Fuzz diferencial con al menos 10⁴ casos, semilla fija y registrada.
- Censo de tipos de hoja sobre el fixture de 1500 revisiones.
- Test de sentinel cruzado audit/no-audit.
- Fuente actual en memoria, sin persistencia ni storage nuevo.
- **Gate:** 0 divergencias. Una sola divergencia es descarte.

**Benchmark ABBA en proceso, sin HTTP:**
- 20 bloques ABBA, con A = `project_selected` y B = `validate_selected` en el miss de `_audit_only`.
- Mismo source, mismo orden y `gc.collect()` entre iteraciones.
- **Métricas:** wall (`perf_counter`), CPU (`process_time`), pico de `tracemalloc` y bloques asignados, y bytes canónicos de la proyección evitada (sólo como contexto).
- **Medidas:** la función aislada y además el `inspect_page` completo en proceso. La primera no se extrapola a la segunda.

**Gate, predeclarado:**
- B gana en CPU y en asignaciones en al menos 16/20 bloques.
- La mediana de mejora está fuera del ruido medido en A/A.
- Ninguna regresión superior al 1% en la ruta ordinaria (`project_selected`).

**Descarte:**
- Cualquier divergencia funcional.
- Victorias por debajo de 16/20.
- Ahorro indistinguible de A/A.
- Necesidad de tocar autoridad o claves.

**Si gana:** sólo entonces N2 y HTTP, con su propio p95 fresco. No se suman ahorros de distintos experimentos ni se mezclan los clones de 548 EVENT con el histórico. La alternativa de autorizar una sola vez sigue prohibida.

## Decisión propuesta

Hay dos opciones:
- **A:** experimento N1 de `validate_selected` en la variante (a), limitado a `batch_projection`.
- **B:** ninguno.

**Opino A**, con una advertencia explícita. Como `deepcopy` de escalares inmutables es casi gratis y `row_reference` ya está memoizado, lo más probable es un ahorro marginal. Un resultado nulo es un desenlace legítimo y debería cerrar esta línea antes de invertir en el inventario.
````

## 5 · codex · opinion

UTC: 2026-10-11T19:16:28.942085+00:00

```text

OBSERVACIÓN CODEX: pointer_value sólo admite hojas escalares. deepcopy de strings no duplica sus bytes. project_selected construye contenedores con referencias, no copia física adicional16MiB. record(_audit_only=True) descarta projection sin canonicalizarla/serializarla. compile_coverage incluye projection pero coverage_page la excluye antes de page_digest. validate_only ahorraría recorrido/resolución/deepcopy escalar/allocs de contenedores, NO16MiBdeRAM/string/SQL. TamañoJSONprojected no equivale a bytesduplicados. No sobreestimar ahorro frente1.753s; ¿merece experimento corto como refactor o priorizarcostefullchain?

```

## 6 · codex · request

UTC: 2026-10-11T19:16:46.934425+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Revisión MOD08/web_citas español, propuestas no son evidencia ni autorización de editar/ejecutar. Notebook tiene arquitectura histórica pero este código/resultados son estado nuevo. No omitir comprobaciones frescas ni prometer SLO por etapas.

MEDIDAS: Prototipo DATOS 1500Revision16MiB, chunkscifrados<=50filas, originalfull199ms→página21ms/prep1.753s. No autoridad/fuente completa. Variante conservadora hash FÍSICO fresco contenido todasfamilias inputs antes/después: full404.347→página352.524ms(51.824ms/12.82%),19/20wall20/20CPU/cuatro bloques favorables; prep1.785s. NO prueba que doblehash sea requisito universal; es estrategiafuerte escogida para cacheentre requests, falta catálogo/permisos/restore/locks. Segunda prueba recuperó30chunks en UNA consulta, descifrómanifiesto1vez/headercifrado separado, reconstruyó dictcompleto y conservó inspection_source HMAC/mutación/bracketderiva original: full411.695→649.771ms(+57.83%),0/20wall, CPU235.511→238.620ms9/20wins/prep1.760s. Lowerbound porque faltan locks/catálogos/callbacksexpiry. GateREJECT integraciónDIRECTA que mantiene dictcompleto; no rechazar universalmente API nueva. 2pytestPASS acreditanexperimentos, no beneficio/N2/endpoint.

CONTEXTO: históriconavegaciónp953.753s383lotes,target2s; JSON6.930/bin7.318target5s peroN3/8 insuficientes. Clones nuevos548EVENT/1500Revision*sin*binariosentregados; no mezclar p95/CPU/etapas ni sumarahorros. Source_copy completo ya1vezporbatch, referencias puras memo intrarequest+summarycache+batch_projection existentes. Canonical Cython nativo. AES/Fernet actual. Todas23authorize/reviewer_case/proof/latest/catalog/fullchain frescas y cadaauditoría cambiacadena. No cacheauthority/triggers, head/counter/Merkle sólono prueba fuente física; cambiosDDL/owner puedenrestaurarhelper y dejardigestGENERATEDantiguo. assessment/selection/coverage susceptiblespurga/expiry. Imagebytesfrescas en S3 y guards despuésesperas.

CODEX HIPÓTESIS NUEVA: separar validación de selección/coverage de emitir valores. record(_audit_only=True) hoy aún construyeproyección enprimermiss aunque devuelveNone; compile_coverage llama project_selected y devuelve projection pero coverage_page final filtra summary sin projection. Primero validate_only sobre FUENTE FRESCA ACTUAL, sin cachepersistente ni nuevostorage: ahorro sólo valores/alloc, no evita source_copy16MiB. Es paso previo explícito y falsable, no promesa177msni2s. Después APIinventario autenticado(dataset,index,row_reference,scalar_paths,metadatafotos)+lectura campospágina podríaevitarmaterialización, pero HMACsource_digest NOsecompone de rowrefs, frescura+origen+caller/permisos/DDL/expiry/restore por demostrar. No contenedores lazydisfrazados ni confiar firmas como reloj; nunca autoridad/revisión almacenada.

CÓDIGO selección COMPLETO actual:
"""Explicit scalar field selection; caller must bind selectors to approved evidence."""
from copy import deepcopy
from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables
from .fast_canonical import content_reference
from .rights_copy_inspection import SECTIONS
from .rights_portability import DATASETS, checked_assessment

def row_reference(dataset, index, row):
    from .rights_inspection_source import shared_row_reference
    return shared_row_reference(dataset, index, row, lambda: content_reference({'dataset': dataset, 'index': index, 'row': row}))

def pointer_value(row, path):
    if not isinstance(path, str) or not path.startswith('/') or len(path) > 500:
        raise ValidationError('Invalid portability field path')
    value = row
    for segment in path[1:].split('/'):
        escaped = segment.replace('~1', '').replace('~0', '')
        if '~' in escaped:
            raise ValidationError('Invalid portability field escape')
        key = segment.replace('~1', '/').replace('~0', '~')
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and key.isascii() and key.isdecimal() and (str(int(key)) == key) and (int(key) < len(value)):
            value = value[int(key)]
        else:
            raise ValidationError('Portability field unavailable')
    if isinstance(value, (dict, list)):
        raise ValidationError('Select individual portability fields')
    return deepcopy(value)

@sensitive_variables()
def project_selected(source, assessment, selection, *, field_evidence=None):
    """Project declared eligible fields; not a standalone authorization or delivery API."""
    checked = checked_assessment(assessment)
    eligible = {name for name, item in checked.items() if item['status'] in {'eligible', 'granular'}}
    if not isinstance(selection, dict) or set(selection) != eligible:
        raise ValidationError('Select each eligible dataset explicitly')
    granular = {name for name in eligible if checked[name]['status'] == 'granular' and selection[name]}
    if field_evidence is None:
        field_evidence = {}
    if not isinstance(field_evidence, dict) or set(field_evidence) != granular:
        raise ValidationError('Provide exact field evidence for mixed dataset selections')
    output = {}
    for dataset in sorted(eligible):
        rows = SECTIONS[dataset](source)
        references = {row_reference(dataset, index, row): row for index, row in enumerate(rows)}
        selectors = selection[dataset]
        if not isinstance(selectors, list):
            raise ValidationError('Invalid portability row selection')
        evidence_rows = field_evidence.get(dataset, {})
        if not isinstance(evidence_rows, dict):
            raise ValidationError('Invalid mixed row evidence')
        seen = set()
        projected = []
        for selector in selectors:
            if not isinstance(selector, dict) or set(selector) != {'row', 'fields'}:
                raise ValidationError('Invalid portability row selector')
            reference, paths = (selector['row'], selector['fields'])
            if not isinstance(reference, str) or reference not in references or reference in seen:
                raise ValidationError('Portability row unavailable or duplicated')
            if not isinstance(paths, list) or not paths or any((not isinstance(path, str) for path in paths)) or (len(set(paths)) != len(paths)):
                raise ValidationError('Select unique portability fields')
            if dataset in granular:
                evidence = evidence_rows.get(reference)
                if not isinstance(evidence, dict) or set(evidence) != set(paths):
                    raise ValidationError('Provide exact evidence for each selected mixed field')
                for decision in evidence.values():
                    if not isinstance(decision, dict) or decision.get('status') != 'eligible':
                        raise ValidationError('Selected mixed fields require eligible conditions')
                    checked_assessment({name: decision for name in DATASETS})
            seen.add(reference)
            projected.append({'fields': {path: pointer_value(references[reference], path) for path in paths}})
        if dataset in granular and set(evidence_rows) != seen:
            raise ValidationError('Mixed evidence contains unselected rows')
        output[dataset] = projected
    return {'schema': 'portability-selected-fields-v1', 'datasets': output}

compile_coverage ACTUAL (resumen fiel): checked_assessment; rechaza pending; siempre projection=project_selected(source,assessment,selection,field_evidence). checked_images contra source/digestsdeclarados. Porcada DATASET SECTIONS[name](source), lenrows; excluded exigeomisionesvacías. Resto recorre todosindex,row: reference=row_reference, paths=_scalar_paths; missing=paths-selected; omisiones{"all":excluded} o {"fields":decisionesexcluded}; subset/exact segúnallow_partial; contabiliza included/excluded/pending. Rechazaomisionesextra/noexistentes. Fotos=[image["photo"] for row in source["revisions"] for image in row["images"]], rechaza duplicados; cobertura binaria. Resultado schema/datasets/included_images/excluded_images/projection +pending/complete si parcial.

inspection_source ACTUAL: __init__ source_fingerprint antes→source_copycompleto→HMACcanonical_bytes(source). get sólo ContextVaridentidad/connection/atomic/scopecasepersonlistingversion. shared_row_reference memo(dataset,index) sólo si rowidentity pertenecefuentecontextual. ExitHMACsource intacto y fingerprinttotal fresco, si diferencia releefullfuente y comparaHMAC; resetfinally. No cacheentre requests. Callerperson/listing puedecontenerrelacionescached; cachépersistentedebe demostrarvínculoexacto. source_digest(context) sóloHMACcontext, sincontextfreshfull. No suprimir exit mutación/deriva.

inspect_page: reviewer_case/authorize; coverage SELECTFORUPDATE(of=self)+relaciones. inspection_sourcenuevo/reusado. record(_audit_only=True) conauditoría/validate_approved_assessment/selection_evidence frescos. authorized_proof/validate_approved_selection/latest; comparaHMACsource. RightsActioncrea/valida; author=User.objects.getFRESCO; baseline_body, unseal factsselection y assessmentcurrent. summarykey coverage/source/selectiondigests; misscompile_coverage(...allow_partial=True). authorize/proof/digest; coverage_page devuelve fieldsactualespaginados y summary={k:v for k,v in summary.items() if k!='projection'}. RightsPortabilityCoverageRead +guards al salir.

batch_projection ACTUAL: ContextVar/mismaconnection/sourceidentity/actor/session/mfa/case/proof. Key case/versión/proof/expiry/row/ciphertextassessmentselection/payloads/settings/operation, entradasmax4 limpiadasfinally. Keymiss project_selected producevalorescompletos, _audit_only guarda sentinelVALIDATED_ONLY/devuelveNone. Hit audit evitaoperación. Otrosretornos deepcopy. Cadaentrada trasvalidaciónfresh; ahorro nuevo no4x primeraoperaciónporque memo yaexiste. No tocarautoridad.

SOLICITUD (máximo~1200palabras):
1 UNA candidata mínima distinta para primer experimento (o ninguna justificable), archivos/API/pseudocódigo y rutaordinaryintacta. No asumir APIinventarioyaexiste.
2 ¿validate_only evita construirvalores conservando errores/orden de pointer_value RFC6901malformed/listindexnocanónico/containerleaf, granular/duplicados etc? Qué se demuestraN1 yquéposiblecambioobservable se descarta.
3 FuturoinventarioDATOS: binding alHMACoriginal+freshness+permisos/callbacks/DDL/expiry, contraejemploquedescartaría. No vendersignature comoautorizaciónactualni TTLcomopruebavigencia. Enumera qué sigue leyendo cuerpos completos. Ahorro sólohipótesisnoobjetivo2s.
4 Experimento finito N1+benchmarkABBA sobre fuenteactualsinpersistencia, wall/CPU/alloc/bytesproyección, gate ydescarte; N2/HTTP sólo si gana. Alternativaautorizacionesuna vez estáprohibida.

OBSERVACIÓN CODEX: pointer_value sólo admite hojas escalares. deepcopy de strings no duplica sus bytes. project_selected construye contenedores con referencias, no copia física adicional16MiB. record(_audit_only=True) descarta projection sin canonicalizarla/serializarla. compile_coverage incluye projection pero coverage_page la excluye antes de page_digest. validate_only ahorraría recorrido/resolución/deepcopy escalar/allocs de contenedores, NO16MiBdeRAM/string/SQL. TamañoJSONprojected no equivale a bytesduplicados. No sobreestimar ahorro frente1.753s; ¿merece experimento corto como refactor o priorizarcostefullchain?

```

## 7 · notebook · error

UTC: 2026-10-11T19:16:59.268865+00:00

```text
Empty answer; inspect raw artifact
```

## 8 · codex · request

UTC: 2026-10-11T19:17:49.922516+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

MOD08/web_citas, revisión nueva sobre código real. Opiniones no son PASS. La consulta anterior fue rechazada como argumentos inválidos; esta versión reduce el contexto, no repetir automáticamente.

RESULTADOS propios nuevos PostgreSQL17/nativo/1500Revision16MiB/20paresABBA:
A) Sólo página50, con hash FÍSICO fresco de contenidos de TODASfamilias antes/después: baseline404.347→352.524ms,19/20wall20/20CPU, prep1.785s.
B) Recoger30chunks en UNAconsulta, manifiesto descifrado1vez+header, dictcompleto para inspection_source original con HMAC/mutación/deriva intactos: baseline411.695→649.771ms,+57.83%,0/20wall,CPU235.511→238.620ms. Prep1.760s. Lowerbound: aún faltan locks/catálogo/callbacksexpiry del proveedor. REJECT integraciónDIRECTA que mantiene fuentecompleta; no descartar universalmenteAPI nueva. 2pytestPASS=experimentos, no aceptación. HTTP histórico383lotes3.753s,target2s; clones548EVENT difieren, no sumar ni prometer2s.

CÓDIGO/CONSUMIDORES actuales:
project_selected(source,assessment,selection,field_evidence): checked_assessment; exacteligiblekeys; evidencekeys=granularselected; datasetssorted; references={row_reference(dataset,index,row):row for index,row in enumerate(SECTIONS[dataset](source))}; exige selectorslist,selector exactkeys{row,fields},referenceexistente/no repetido, pathslistnonempty/unique/str. Granular requiere evidenceexactpaths/eligible y checked_assessment decisiones. Porselector hace projected.append({"fields":{path:pointer_value(references[ref],path) for path in paths}}). Rechaza evidenciasobrante. Devuelve dictschema/datasets.
pointer_value: pathstrstartswith'/'/len<=500; porsegment rechaza escape~malformed, decodifica~1/~0. Recorre dictkeyexistente o listindexascii/decimal/str(int(key))==key/inrange; si finaldict/list rechaza containerleaf; return deepcopy(value). Deepcopy strings NOduplica bytes; construirprojection sólocontendores/referencias, NOotros16MiBdetexto. No serializaciónposterior deprojection enaudit_only.
record(_audit_only=True) SIEMPRE validacionesfresh; batch_projection ContextVaratomic/sourceidentity/scopeactor/proof, key ciphertextassessmentselection/versions/expiry/config frescas. Miss llama project_selected ydescartavalores; almacena sentinelVALIDATED_ONLY,max4; hit audit no ejecuta. Non-audit debe reconstruir si sentinel. Cache sólopureintrarequest, limpiafinally.
compile_coverage siempre project_selected; despuésrecorretodasfilas _scalar_paths y refs para countselected/missing/omissions; checked_imagesmetadata yphotosduplicados; resultado incluyeprojection. inspect_page lo guardaensummarycacheintrarequest y coverage_page excluyeprojection delsummary entregado. Imagenfísica se revalidaS3aparte.
inspection_source original una fullsource_copyporbatch, HMACoriginalsourcecompleta, salidaHMACmutación yfingerprinttotal(xmin/ctid)fresh, si deriva releefull. No cacheentre requests. Canonical Cythonnativo. Mantener23authorize,case/proof/latest/catalog/fullchain frescos y auditorías; head/counter/Merkle ni firmas no pruebanvigencia, purgaexpirycontinúan.

CODEX candidata mínima: validate_selected sobre sourceactual, compartiendo MISMO recorrido y erroresincluido deepcopydescalar, pero no construirdicts/listasoutput; sólo miss _audit_only. Sinstorage/cache/authority ni source_copyahorro. Es probablebeneficiomarginal y podría cerrarse si no gana. APIinventario autenticadoindex/ref/path para evitarfullsource seríaotrahipótesisconHMACbinding/caller/DDL/permisos/retención pendientes.

Elige1candidata, archivos/pseudocódigo, contraejemplo y N1diferencial (RFC6901,listindex,containerleaf,granular,duplicados,ordenprimererror,sentinelnoaudit) + benchmarkABBA sinGC/profiler, threadCPU; memoriaenpasadaseparada. Si no haybeneficio mayor, dilo. ¿Invertirvalidate_onlycomo experimento corto o cambiar foco a fullchain? No omitirautoridad ni garantizareducción2s. Máximo900palabras.
```

## 9 · notebook · opinion

UTC: 2026-10-11T19:19:16.209461+00:00

````text
### Distinción de hechos medidos, hipótesis y evidencia faltante

**Hechos medidos:**
- **Resultados de las pruebas de rendimiento (PG17 nativo):** En el Experimento A (página 50 con hash físico fresco de todas las familias), el baseline mejoró de 404.347 ms a 352.524 ms (-12.8%), logrando 19/20 victorias en wall time y 20/20 en CPU [1, 2]. En el Experimento B (recolectar 30 chunks en una sola consulta), el wall time se degradó un +57.83% (411.695 ms → 649.771 ms, 0/20 victorias en wall time) y el tiempo de CPU se incrementó ligeramente (235.511 ms → 238.620 ms) [1, 2]. Los 2 `pytest` en PASS corresponden a experimentos locales y no equivalen a aceptación ni autorización en producción [3, 4]. El rendimiento histórico HTTP muestra 383 lotes en 3.753 s, distante del objetivo contractual de 2 s [4, 5].
- **Comportamiento del código y consumidores vigentes:**
  - `project_selected` valida `checked_assessment`, requiere coincidencia exacta de claves elegibles y evidencia granular, e invoca `pointer_value` por cada campo en `references[ref]` [6].
  - `pointer_value` exige prefijo `/`, valida decodificación RFC 6901 (`~1`/`~0`), verifica que los índices de lista cumplan `str(int(key)) == key` en rango y rechaza contenedores hoja (`containerleaf`) [6]. En CPython, el uso de `deepcopy` sobre escalares `str` no duplica los buffers de bytes subyacentes [6, 7].
  - `record(_audit_only=True)` y `batch_projection` verifican contexto atómico y autoridad vigentes [1, 7, 8]. Retornan `None` y almacenan el centinela `_VALIDATED_ONLY` (máximo 4 entradas por contexto) [1]. En ejecuciones `non-audit`, la presencia del centinela fuerza la ejecución real de `project_selected` [1].
  - `compile_coverage` ejecuta `project_selected` y contabiliza omisiones [2]. `inspect_page` almacena el resumen en `_summary_cache` intra-petición y `coverage_page` remueve `projection` antes de entregar la respuesta [2, 9].

**Hipótesis:**
- Una variante `validate_selected` que ejecute el mismo recorrido de validación que `project_selected` sin instanciar diccionarios/listas de proyección podría ofrecer una reducción marginal en consumo de CPU y allocs de memoria en la fase `_audit_only`.
- Una API de inventario autenticado index/ref/path evitaría procesar el `fullsource` completo de 16 MiB, pero requiere definir previamente la gestión de permisos DDL, retención y bindings HMAC.

**Evidencia faltante:**
- Ausencia de mediciones p95 bajo concurrencia real con múltiples workers que demuestren si evitar la construcción de diccionarios de proyección altera la latencia percibida [4, 10].
- Falta de pruebas que garanticen la ausencia de deriva semántica de validación entre `validate_selected` y `project_selected` [6].

---

### Decisión finita propuesta

**Decisión:** **Cambiar el foco hacia la optimización de `fullchain` (cadena de autoridad, candados y refresco de fuente) y NO invertir recursos en `validate_only` como experimento.**

**Justificación:**
El costo computacional de instanciar los diccionarios de proyección en `project_selected` es despreciable en comparación con las comprobaciones repetidas de autoridad y lecturas de la fuente [1, 2, 6]. Experimentos anteriores orientados a parches de micro-optimización local (como el enfoque de cuatro lectores) no redujeron el tiempo HTTP p95 y provocaron regresiones en cargas JSON (+11.7%) y binarias (+18.1%) [4]. La brecha hasta la meta contractual de 2 s no se cerrará mediante ahorros de allocs en proyecciones escalares [4, 5].

---

### Candidata mínima, Pseudocódigo, Contraejemplo y N1 Diferencial

#### Pseudocódigo de `validate_selected`:
```python
@sensitive_variables()
def validate_selected(source, assessment, selection, *, field_evidence=None):
    checked = checked_assessment(assessment)
    eligible = {name for name, item in checked.items() if item["status"] in {"eligible", "granular"}}
    if not isinstance(selection, dict) or set(selection) != eligible:
        raise ValidationError("Select each eligible dataset explicitly")
    granular = {name for name in eligible if checked[name]["status"] == "granular" and selection[name]}
    if field_evidence is None:
        field_evidence = {}
    if not isinstance(field_evidence, dict) or set(field_evidence) != granular:
        raise ValidationError("Provide exact field evidence for mixed dataset selections")

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
        for selector in selectors:
            if not isinstance(selector, dict) or set(selector) != {"row", "fields"}:
                raise ValidationError("Invalid portability row selector")
            reference, paths = selector["row"], selector["fields"]
            if not isinstance(reference, str) or reference not in references or reference in seen:
                raise ValidationError("Portability row unavailable or duplicated")
            if not isinstance(paths, list) or not paths or any(not isinstance(p, str) for p in paths) or len(set(paths)) != len(paths):
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
            for path in paths:
                val = pointer_value(references[reference], path)
                deepcopy(val)
        if dataset in granular and set(evidence_rows) != seen:
            raise ValidationError("Mixed evidence contains unselected rows")
```

#### Contraejemplo:
Un payload que contenga un puntero dirigido a un contenedor intermedio (`containerleaf`) o evidencias sobrantes en `evidence_rows` debe fallar con `ValidationError` [6]. Si `validate_selected` omitiera llamar a `pointer_value` o alterara el orden de las comprobaciones, la llamada `_audit_only` marcaría el centinela `_VALIDATED_ONLY` como válido, pero la re-ejecución posterior en modo no-audit dentro del mismo bloque atómico fallaría inesperadamente con `project_selected` [1, 6].

#### N1 Diferencial:
1. **RFC 6901 y listindex:** `pointer_value` exige `/` inicial, decodifica `~1`/`~0` y valida los índices con `str(int(key)) == key` [6].
2. **containerleaf:** Si el elemento final es un `dict` o `list`, se rechaza explícitamente [6]. `validate_selected` debe evaluar `pointer_value` para cada ruta sin excepción.
3. **Granularidad y Duplicados:** Las referencias duplicadas o las evidencias no seleccionadas lanzan un error al finalizar la iteración del dataset [6]. El orden de detección de errores debe mantenerse idéntico.
4. **Sentinela No-Audit:** La llamada con `_audit_only=True` debe retornar `None` y almacenar `_VALIDATED_ONLY` en el contexto atómico actual [1].

#### Protocolo de Benchmark ABBA (Sin GC / Thread CPU time / Memoria separada):
```python
import gc, time, tracemalloc

def abba_benchmark(source, assessment, selection, evidence, iterations=20):
    gc.disable()
    times_A, times_B = [], []
    try:
        for _ in range(iterations):
            t0 = time.thread_time_ns()
            project_selected(source, assessment, selection, field_evidence=evidence)
            times_A.append(time.thread_time_ns() - t0)

            t1 = time.thread_time_ns()
            validate_selected(source, assessment, selection, field_evidence=evidence)
            times_B.append(time.thread_time_ns() - t1)
    finally:
        gc.enable()
    return times_A, times_B

def abba_memory_pass(source, assessment, selection, evidence):
    tracemalloc.start()
    project_selected(source, assessment, selection, field_evidence=evidence)
    _, peak_A = tracemalloc.get_traced_memory()
    tracemalloc.reset_peak()
    validate_selected(source, assessment, selection, field_evidence=evidence)
    _, peak_B = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak_A, peak_B
```

🔍 ¿Quieres que analicemos los cuellos de botella específicos de la cadena de autoridad (`fullchain`) para identificar qué verificaciones de firmas o candados DB pueden reestructurarse?
````

## 10 · codex · opinion

UTC: 2026-10-11T19:19:36.656834+00:00

```text
Codex revisión local tras primera opinión de Claude:
1. 19/20 son pares, no 19/20 bloques; hay cuatro bloques cronológicos. Pruebas no acreditan beneficio global.
2. source_fingerprint lee id/xmin/ctid de todo el conjunto, NO cuerpos. Una relectura por deriva sí lee source_copy; no convertir siempre en full-body lectura. _scalar_paths visita estructura y no serializa textos. checked_images sólo metadata; audited_images sí lee bytes S3. content_reference hashes bytes de fila, pero memo dentro de contexto existente evita repetir porrow/index.
3. deepcopy de strings mantiene referencias; no evitar16MiB de bytescopiados. Canonicalchecker sólo type exact str/bool/int/finitefloat/None/dict/list/tuple; datetime/custom se rechazan. Sinembargo pointer_value admite finaltuple (no dict/list), porloque validador podría necesitar deepcopy de tupla; mantener deepcopy igual para primera candidata protege interfaz pública inclusoextensiónnoJSON.
4. Primera candidata estrecha puede limitarse a validar sinemitir en miss audit dentro batch_projection. Clave/pure scope/sentinel/ruta ordinaria/no-audit intactos; fuera batch mantenerrutaordinary inicialmente. No llamadasautoridad nuevas omitidas. Esto no evita source_copy ni HMAC ni rowref ni JSONdecrypt.
5. Rechazar protocolo GCcollect nuevo y tracemalloc en reloj principal; conservar GC sin cambios, thread_time_ns, medir memoria aparte. Cero divergenciasN1 es puerta absoluta; muestras de rendimiento A/A y A/B suficientes sólo descriptivas, 1% noinferioridad formal no demostrable automáticamente con20pares. No mínimo arbitrario10^4fuzz si corpusdirigido ya alcanza errores; generación acotada semilla fija sí.
6. No decidirgranrediseño/storepaginado desde beneficiosoloalloc. Si microcarecebeneficio consistente cerrarvalidate-only. Si sólo reduce marginalmente, no prometer2s ni dedicar bucle de reescrituras. Source404/412ms actualnoequiv3.753s histórico; históriconoalcanzaconensayocuatroclones.
7. Optimizaciónfullchain sólo siguientehipótesis independiente: consultar serverhashescompactos manteniendo TODOS hashes físicos, cada SELECTy snapshotorden, errores y catálogo. NO funcionesvariables suplantables, NO combinar7snapshotsenuno, NO head/ticketcomo autoridad. No candidatoimplementable aprobado aún.

```

## 11 · codex · request

UTC: 2026-10-11T19:20:36.244646+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Cierre correctivo de sala. Tu intervención anterior proponía validate_only audit como experimento marginal. No recibes memoria de otras llamadas: aquí comparto resultados y objeciones explícitos. No código, benchmark ni producto nuevos durante sala.

Notebook respondió: recomienda cambiar a fullchain y NO experimentar validate_only porque cree despreciable emitir contenedores, pero no midió ese coste. Citó regresión de cambiar2→4readers (histórico JSON+11.7%/binario+18.1%), que NO prueba resultado validate-only ni explica su coste. Aun así dio pseudocódigo validate_selected donde llama val=pointer_value(...) y deepcopy(val) OTRA VEZ (pointer_value ya deepcopies), innecesario/error; protocolo llamadoABBA sólo alternaA/B, desactivaGC, contra instrucciones. Coincide mantenererror/orden/granular/sentinel; no aporta implementación concreta fullchain ni evidenciaahorro. Su proposicióndepaginado sigue hipótesisconHMAC/DDL/permisos/retención pendiente. No presentar consenso.

Tus frases originales a corregir: source_fingerprint no lee cuerpos (id/xmin/ctid), _scalar_paths no serializa bytesstring, checked_images no leeS3 (audited_images sí),19/20eranparesno bloques. Tú proponíasGCcollectentreiteraciones y tracerjuntoCPU; corregirprotocolo mismoGCsin cambios, thread_time_ns y memoriaenpasadaseparada. No mínimo arbitrario10^4fuzz o1%noinferioridadformal con20muestras. Distinguecontraejemplos de datosvsautoridad y scope actual vsrestorecachépersistente.

CODIGO adicional contrastado: fast_canonical.reference_check acepta EXACT type str,bool,int,finitefloat,None,dict,list,tuple; rechaza datetime/custom. No asumir que todosleafinmutablesporque tuple puedecontenercontenedores y pointer_value final sólo rechaza dict/list, no tuple. Conservar llamada pointer_value+deepcopyigual,descartar resultado (sin segunda deepcopy) primera candidata. Deepcopystr no duplica bytes16MiB; actualrecordauditnoconvierteprojectionaJSON. No nuevocacheautoridad. La rutaordinaryactual no necesita refactoringgeneral para ensayar una funciónprivada (core compartido despuésdegate si útil).

CODEX juicio de decisión: no está probado coste alloc pero tampoco mejora útil. Un experimento muy acotado sobre sourceactual/refmemo caliente y fría puede resolverincertidumbre; máximo una candidata semántica + una corrección porinstrumento siERROR, nada de bucle interminable. N1deduplicados,invalidpaths/escapes,listindex ASCII/canónicos/outofrange,container/tuple,granular,evidenciaextra,primererrororden,sentinelhit audit→nonaudit yfallbacksincontext. Cero divergencias. A/A20paresbaselinecaliente yAB20paresinterleaved sinotrobenchmark, wall/threadCPU, memoriaotra pasada sinclaimSLO. No nuevosservicios/persistencia. Caso importante row_reference memo yaactivo(en1500rows): si missmemo domina, la comparacióncorefría miente impacto real; medir ambas, noescogermejorposterior. N2 sólo si ahorro medibleconsistenteynoalterarordinary. Si≥15/20paresfavorableswallCPUycuatrobloquespositivos superiorruidoA/A: mantenercandidataparacorrectitud/HTTP; si no, cerrarroute. ¿Adecuado siquiera como prueba? Si no, dar alternativafullchain REAL que preserveALLhashesfresh/7SELECTsnapshots/order/errors/DDLattestation y explique target medido, noheadticketcache ni SQLmultiqueryúnico snapshot.

Si es pequeño (<deltaestablevisible), no vender como camino de1.753s; se acepta sólo beneficio parcialtrasN2/HTTP. FutureAPIinventario no seaprueba por esto ni heredadigestHMACsinprueba. No tocarcompile_coverage de inicio, salvoopcióninternalexplícita separada luego si useful + inventario callers previo. Después si nopista, declarar falta candidato sólido en vez inventar.

Responde máximo700palabras: 1decisión finita entre experimento pequeño/foco alternativo, pseudocódigomínimo seguro, contraejemplo, gate/descarte, qué debe investigarseresidual y qué NO sabemos. No repetirla propuestaoriginalsin incorporarlas críticas. Añade si el propio criterio15/20 necesitaríaseñaldeclocksdadosahyposses.

```

## 12 · claude · opinion

UTC: 2026-10-11T19:21:25.658891+00:00

````text
# Cierre correctivo: decisión sobre `validate_only` audit

## Correcciones a mi intervención anterior

- `source_fingerprint` no lee cuerpos. Usa id, xmin y ctid.
- `_scalar_paths` no serializa bytes ni str.
- `checked_images` no lee S3. Quien lo hace es `audited_images`.
- "19/20" eran pares, no bloques.
- Retiro `gc.collect` entre iteraciones. Debe usarse la misma configuración de GC sin cambios.
- Retiro el tracer junto a la medida de CPU. Se medirá `thread_time_ns`, y la memoria irá en una pasada separada.
- Retiro el mínimo de 10⁴ casos de fuzz y la no-inferioridad del 1 %. Con 20 muestras eran umbrales arbitrarios.

## Decisión finita

**Hacer el experimento pequeño, sin bucle.** Se prueba una sola candidata semántica y, como máximo, una corrección por error del instrumento. Si no supera el gate, se cierra la ruta.

Es adecuado sólo como prueba de hipótesis acotada, y la hipótesis es estrecha. La candidata conserva `pointer_value` y su deepcopy. Por tanto, el único ahorro posible es no emitir ni ensamblar contenedores aguas abajo. Si el coste lo domina el deepcopy o el miss de memo, lo esperable es un resultado nulo, y eso también es una respuesta válida.

No propongo ahora una alternativa fullchain. Ni la del notebook ni la mía tienen hoy un objetivo medido que preserve los hashes frescos, los 7 SELECT, los snapshots, el orden, los errores y la attestation DDL.

## Pseudocódigo mínimo

```
def _validate_selected_audit(doc, paths, ctx):
    if ctx is None:
        return ORDINARY(doc, paths, ctx)       # fallback idéntico, la candidata no participa
    for p in ordered_dedup(paths):              # la MISMA función/orden que ordinary
        tokens = parse_pointer(p)               # mismos escapes ~0/~1, índice ASCII canónico, out-of-range
        _ = pointer_value(doc, tokens)          # misma llamada; su deepcopy interno se conserva
                                                # resultado descartado; SIN segundo deepcopy
        # excepciones propagan sin capturar: mismo tipo/mensaje/primer error
    # memo: escribir exactamente lo que escribe ordinary o nada; nunca una entrada "validada sin contenedores"
    return AUDIT_RESULT_SAME_SHAPE_AS_ORDINARY_WITHOUT_CONTAINERS
```

Restricciones:

- Es una función privada, sin refactorizar la ruta ordinaria.
- No hay caché de autoridad nueva, ni persistencia, ni servicios.
- No se toca `compile_coverage`.

## Contraejemplos que N1 debe incluir

**Datos:**
- Una tupla que contiene un dict. `pointer_value` sólo rechaza dict y list finales, no tuple. La candidata no puede rechazar ni aceptar distinto.
- No asumir hojas inmutables.
- `datetime` o tipos custom, que `reference_check` rechaza. Hay que comprobar su orden frente a un error de puntero.
- Índices `01`, `-`, dígitos no ASCII y fuera de rango.
- `~2` y escapes inválidos.
- Paths duplicados cuyo primer error depende de la deduplicación.
- Evidencia extra y caso granular.

**Autoridad:**
- Sentinel hit audit→nonaudit: una entrada de memo poblada por audit no debe servir a nonaudit con forma distinta.
- Fallback sin contexto.

**Alcance:**
- Sólo el memo `row_reference` actual en proceso. El resultado no dice nada sobre una caché persistente restaurada, que queda fuera de alcance.

## Gate y descarte

1. **N1:** cero divergencias en resultado, tipo y mensaje de excepción, primer error, orden y estado del memo después de la llamada. Una sola divergencia descarta la candidata. Si la causa es el instrumento, se permite una única corrección.
2. **Medida:** A/A con 20 pares de baseline caliente, y A/B con 20 pares intercalados en un orden contrabalanceado declarado de antemano. El "ABBA" del notebook era sólo alternancia A/B.
   - Se mide wall y `thread_time_ns`, con el GC como está.
   - La memoria va en otra pasada.
   - No se lanza ningún otro benchmark en paralelo.
3. **Regímenes:** memo caliente y memo frío (miss), ambos predeclarados. Ambos deben pasar, o se reportan los dos y se cierra. No se elige el favorable a posteriori.
4. **Criterio de paso:** en cada régimen, ≥15/20 pares favorables tanto en wall como en CPU, y además 4 bloques predefinidos de 5 pares con delta positivo por encima de la dispersión A/A.
5. **Después del gate:** N2 sólo si se pasa y la ruta ordinaria no se altera. Después, prueba de correctitud por HTTP.
6. **Alcance del beneficio:** aunque pase, es un beneficio parcial. No es el camino hacia 1,753 s y no permite reclamar SLO ni p95.

## ¿El 15/20 necesita supuestos explícitos sobre los relojes?

Sí.

- **Independencia:** 15/20 equivale a p≈0,021 en un test de signos unilateral, pero sólo si los pares son independientes y no hay empates.
- **Resolución de `thread_time_ns`:** puede ser gruesa según kernel y clocksource. Hay que declarar los empates como desfavorables y reportar la tasa de empates.
- **A/A de control:** el A/A debe dar unos 10/20. Si da 15/20 o más, el instrumento tiene sesgo de orden o deriva (frecuencia, térmica) y el A/B no vale.
- **Wall y CPU correlacionados:** exigir ambos no son dos pruebas independientes.
- **Magnitud:** 15/20 no mide cuánto se gana. La magnitud se decide sólo frente al ruido A/A.

## Hechos, hipótesis y evidencia faltante

**Hechos aportados:**
- `reference_check` acepta tipos exactos.
- `pointer_value` hace deepcopy y no rechaza tuple.
- Hacer deepcopy de un str no duplica los 16 MiB.
- El record de audit no convierte la proyección a JSON.

**Hipótesis no medidas:**
- Que emitir contenedores cueste algo apreciable (el notebook la niega sin medirla; yo no la afirmo).
- Que el ahorro sobreviva al miss de memo.

**Evidencia faltante:**
- Reparto del coste entre deepcopy, ensamblaje y miss de memo.
- Tasa real de acierto del memo en producción.
- Granularidad del reloj de CPU en esta máquina.

La regresión de 2→4 readers (+11,7 % en JSON, +18,1 % en binario) no informa sobre validate-only.

## Investigación residual y lo que no sabemos

- Si se descarta, la siguiente pregunta es de atribución, no de candidata: qué fracción de los 1,753 s corresponde a cada etapa de la cadena.
- Sin esa medición, no hay un fullchain real que proponer. Hay que declarar que falta un candidato sólido.
- La paginación, el inventario de API futura y el digest HMAC siguen siendo hipótesis pendientes:
  - HMAC: falta probarlo y no se hereda.
  - DDL, permisos y retención: sin resolver.

No hay consenso con el notebook en la recomendación ni en el pseudocódigo. Sí coincidimos en mantener el error, el orden, el caso granular y el sentinel.

Esto es una opinión, no un PASS ni una autorización.
````

## 13 · codex · decision

UTC: 2026-10-11T19:23:43.910437+00:00

```text
# MOD-08 — Deliberación tras descartar la fuente completa cifrada — 2026-10-11

## Decisión de Codex

No hay una nueva solución demostrada para alcanzar los2s. Se cierra la sala con **una hipótesis pequeña y falsable**: validar la selección de una inspección audit-only sin ensamblar el resultado que se descarta. Debe ensayarse primero sólo en tests, con fuente fresca actual, misma resolución de campos/deepcopy y todas las validaciones; sin persistencia ni API paginada nueva. Su probable beneficio es marginal. No repetir la integración de30chunks→dict completo que regresó57,83%.

No se adopta aún código, se modifica autoridad ni se declara aceptación. La investigación de una API de inventario auténticamente paginado y de la cadena permanece pendiente: esta deliberación no proporciona una implementación equivalente ni un ahorro acreditado para esas rutas.

## Intervenciones y discrepancias

Sala [.ai/rooms/mod08-consumidores-20261011](../../.ai/rooms/mod08-consumidores-20261011/transcript.md), cuatro solicitudes externas acotadas, cerrada. Contexto: código completo de project_selected/pointer_value, resumen verificado de inspection_source, compile_coverage, coverage_page, record y batch_projection; resultados de las dos puertas recientes y limitaciones del escenario. Código local y mediciones nuevos tienen prioridad sobre documentación histórica del notebook.

- Claude inicial (63,731s; CLI reporta claude-opus-5-5) propone ensayo privado en primer miss audit-only, sin tocar compile_coverage. Conserva deepcopy para no introducir diferencias de tipo/error. Admite ahorro probablemente marginal y que no evita source_copy/HMAC/row_reference.
- Notebook: primera consulta fue rechazada por argumentos inválidos. Se conserva ERROR; no hay prueba de que la causa fuera una longitud límite publicada. Se redujo manualmente el contexto y la siguiente solicitud (86,275s) respondió. Modelo no identificable por CLI. Recomienda NO invertir en validate_only y pasar a fullchain, pero no aporta candidata concreta de cadena ni medida del coste de contenedores.
- Claude correctivo (49,402s; modelos/consumo exactos en registro) recibe la respuesta del notebook y objeciones Codex. Mantiene el experimento único acotado, rectifica errores de medición/lecturas y declara que hoy tampoco tiene una alternativa fullchain concreta que conserve todas las barreras. **No hay consenso** en prioridad; Codex elige resolver la incertidumbre con un ensayo pequeño, no invertir primero en persistencia/rediseño grande.

Todas las opiniones son verified=false, no evidencia de aceptación. Consumo real de ambas invocaciones Claude añadido a .ai/tasks/desarrollo.md, anterior preservado. No herramientas locales, edición ni herramientas web de Claude en esta sala; excepción persistente sólo deliberación. El notebook conserva100fuentes, mismosIDs; ninguna añadida/eliminada.

## Correcciones que impiden adoptar las respuestas literalmente

1. deepcopy de str conserva sus bytes. La proyección crea contenedores con referencias; no duplica otros16MiB de textos ni se serializa en la ruta audit-only. El ahorro potencial de no emitir valores es recorrido/deepcopy/ensamblaje, no transferencia de source ni16MiB de RAM adicionales. Tamaño JSON no equivale a memoria duplicada.
2. source_fingerprint consulta id/xmin/ctid, no cuerpos. _scalar_paths recorre estructura sin serializar textos. checked_images comprueba metadata, audited_images sí recupera bytes físicos. Rowrefs ya se reutilizan en el contexto; no multiplicar cuatro veces el coste de un miss.
3. Notebook recomienda fullchain sin coste medido; su argumento de la regresión histórica2→4readers no demuestra nada sobre validate-only. Su pseudocódigo hace una segunda deepcopy después de pointer_value, innecesaria; su benchmark etiquetadoABBA esAB y desactivaGC. No se utiliza.
4. Claude inicial proponía GCcollect y traza junto al reloj; la revisión retira ambos, así como mínimos arbitrarios10^4fuzz y noinferioridad1% con20muestras. Memoria en pasada independiente y CPU del hilo, GC intacto.
5. El pseudocódigo correctivo de Claude tampoco se implementa literalmente: ordered_dedup cambiaría el rechazo de paths duplicados; pointer_value recibe pathstr, no tokens; su forma de retorno placeholder/memo es ambigua. La ruta audit debe devolverNone y marcar el sentinel existente sólo después de terminar cada comprobación. Hits nonaudit deben volver a proyectar; no servir sentinel como valores.
6. Canonical admite tipos exactos JSON y también tuple; pointer_value sólo rechaza dict/list finales. No asumir hojas siempre primitivas ni eliminar deepcopy sin demostrar alcance. Además, quitar dict comprehensions puede omitir evaluaciones de hash de claves str-subclass en interfaces genéricas. Un algoritmo que sólo conserva el resultado para JSON común no basta para cambiar la API pública: preservar ordinary, scope de candidata explícito y N1 de tipos/efectos/errores antes de cualquier integración.
7. >=15/20 pares es sólo cribado descriptivo; autocorrelación/deriva y wall/CPU correlacionados impiden venderlo como prueba estadística formal. Empates cuentan sin beneficio. A/A sesgado hace la tanda inconclusa; no exigir retrospectivamente exactamente10/20.

## Próximo experimento finito

1. **Una candidata privada sólo tests** que conserve cada validación y su orden de project_selected. No tocar el servicio público, compile_coverage, catálogos, autoridad, cache key/scope/expiry, source_copy ni snapshots. Mantener pointer_value con deepcopy una vez. Eliminar únicamente ensamblaje de output descartado que N1 demuestre inobservable; si exige cambiar validación de inputs, descartar esa variante.
2. **N1 diferencial** frente al oracle actual: eligible/granular, evidencia exacta/sobrante, duplicados, selección vacía/forma incorrecta, RFC6901 inválido y válido, índices ASCII/no canónicos/out-of-range, containerleaf/tuple/subclases, dos errores simultáneos para verificar primero, estado de memo y resultados independientes. Gate cero diferencias observables; test sentinel audit→nonaudit y fallback/contexto inválido. Fuentes completas y hojas actuales; no fake aprobación.
3. **Cribado PostgreSQL/kernel nativo**, fuente1500revisiones16MiB y selección reales equivalentes; preparación fuera registrada. A/A20pares y A/B20pares contrabalanceados, warmups fijos, clocks perf_counter_ns/thread_time_ns, GC intacto, sin profiler/tracemalloc dentro de tiempos ni modelos simultáneos. Regímenes rowref memo frío y caliente declarados antes, resultados de ambos; no escoger después el favorable. Cuatro bloques cronológicos de cinco pares, magnitud y dispersión A/A.
4. **Puerta:** cero divergenciasN1 y beneficio consistente >=15/20wall+CPU y bloques positivos que excedan ruido de controles. Si reloj/controles no permiten discernir efecto, resultado inconcluso, no positivo. Si no gana, cerrar la ruta de ensamblaje; no una cadena de nuevos microparches. Una única corrección si el instrumento tiene ERROR; conservar fallo y repetir afectados, no muestras selectivas. Aceptación funcional/rendimiento son puertas distintas.
5. Sólo si gana de forma útil, candidata productiva estrecha y N2 PostgreSQL/runtime/RustFS propio, guardas tardías/rollback/auditorías/móvil, después HTTP emparejado. Si no hay mejora HTTP consistente, conservar como máximo beneficio parcial justificado o retirarla según riesgo; nunca declarar2s/5s ni restar delta del p95 histórico.

Si no supera la puerta no existe todavía una siguiente candidata sólida de cadena: primero atribuir su coste actual con barreras/snapshots y crecimiento histórico. Propuesta de resultados compactos sólo investigable si mantiene hashes físicos frescos de TODASfilas, siete sentencias/snapshots/orden, errores y atestación. No autoridad memo ni head/counter/Merkle sustitutos. El inventario paginado sigue necesitando una prueba distinta de vínculo HMAC/frescura/caller/DDL/permisos/retención y consumidores sin cuerpos completos.

## Cierre y estado

Durante esta sala no se ejecutaron benchmarks ni nuevas pruebas de producto. Dos respuestas Claude y una Notebook reales, un ERROR Notebook preservado; rechazos locales de contexto demasiado largo ocurrieron antes de solicitud externa y no son invocaciones a modelos. Fuentes de código/mediciones suministradas verificadas sin diferencias mediante su manifiesto. Ningún modelo ejecutándose tras cierre. No commit, push, publicación, proveedores o datos reales. Sala limitada terminada, hipótesis y criterios listos; no goal nuevo ni aceptaciónMOD08.

```
