# MOD08: autorización concurrente, herramientas profesionales y candidata finita

Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

## 1 · user · authorization

UTC: 2026-10-11T22:09:07.407571+00:00

```text
Usuario autoriza 2026-10-12 deliberación entre Codex, Claude y Notebook, investigación de herramientas profesionales existentes e implementación local comprobada. Conservamos excepción 2026-10-11: Claude CLI sólo revisor sin herramientas locales ni edición; investigación pública WebSearch/WebFetch autorizada previamente y vigente; consumo registrado. No publicación/proveedores/datos reales.
```

## 2 · codex · context

UTC: 2026-10-11T22:09:07.512190+00:00

```text
Deliberación nueva autorizada por usuario: «delibera cómo hacerlo; herramientas profesionales existentes antes que recrearlas; apruebo implementar mejoras; brainstorming entre las tres; después ejecutar». Codex dirige; Claude sólo revisión/investigación pública, sin lectura local/edición (excepción previa vigente). Notebook conserva sus fuentes.
Hechos nuevos: escenario REAL normal PG17/Django5.2.17/psycopg3.3.6/Gunicorn23, 2 workers sync, Celery2+Beat, RustFS/Caddy; presupuesto total4CPU8GiB, PG1.5CPU3GiB/app1.75CPU3968MiB/objetos.5CPU512MiB/Caddy.1CPU128MiB. Dos casos independientes cada1500revisiones/16MiBJSON/64MiBWEBP. SIN py-spy/cProfile/spans/hooks ni PGstats precargadas. p95 navegación384muestras/caso3.384803/3.389665s (objetivo2); JSON20/caso8.747557/8.961067s, binario20/caso9.033017/8.966103s (objetivo5). Todas las parejas HTTP se solapan; sólo6incumplimientos de tiempo, sin errores de operación, cuerpos/hashes/privacidad comprobados. 1389huellas iguales; cleanup completo. Descargas son partes8MiB, POST303+GET200 con DOS autorizaciones frescas. No compara causalmente con1caso.
Diagnóstico separado1caso py-spy0.4.2+PGstats: diezcapturas sinerrores; p952.483100s/JSONmax4.649687s/binmax5.422434s; sin fases/cProfile ni workerhooks. Cadena:4llamadas links340filas7.53ms temprano vs9844filas203.60ms tardío; sin Lock observado, ClientRead esbackend esperando cliente. StatsSQL anidados/globales solapan: no sumarlas como ahorro. CPU local hashes/canonical/unseal/decoding/distribuida, no único hotspot probado.
Herramientas instaladas fuera depsapp: py-spy0.4.2, Memray1.20.0, Scalene2.3.0. Memray smoke unseal16MiB sintético1559alloc196.7MBtotal89.9MBpeak; no fixture/ni ahorro. Scalene instalado no usado. Preferir API/CLI/reportes oficiales, no reconstruirprofiler. No APIpagada/account/publish. Priorizar UNA pregunta y experimento finito para localizar operación reducible; sólo integración después de equivalencia/PG/security y benchmark sinperfiladores.
Negativos previos: memoautoridad/tickets/catálogo rechazadas por frescura; cadena muta en mismaTx; advisory no bloqueaDDL; precarga assessment.encrypted_assessment oculta purga; crypto válido no frescura. MemoJSON condeepcopy perdió: parse repetido~31msCPU vs~196mscopia; no compartir dictsmutables. InlineSQL cadena HTTP beneficio pequeño/cola peor. Manifiesto paginado al materializar dict completo regresó58%; no reabrir misma candidata. Más workers ya regredió. FuenteNOembebe fotosbase64; bytes64MiB se leen/hash aparte.
Ya existen: nativecanonicalsealed, memoHMAC32MiB exactfreshbytes+currentSECRET_KEY, memoSHA64MiB exactbytes, inspection_source con freshfingerprint antes/después+canonicalmutación yfallbackfullfresh. No proponer instalarlas como nuevas. Sello replay consulta TODAS las filas actuales/expiración/key/config; no autoridad-cache. Fallback al fullbinding; necesitamos comprobar frecuencia/coste de fallo del sello, no asumir éxito.
Mi conjetura Codex: observar/explicar fallback frecuente del replayseal y coste de materialización/copia puede ser mejor que sumar más muestreos generales. PGchains incluyen propia auditoría y avanzan, así que holds puede fallar legítimamente; no excluir esas filas para fabricarhits. MemrayTracker sobre UNA autorización real puede identificar volúmenes, Scalene sobre operaciónCPU separada si necesario. Proponer primero análisis del pyspy existente y una capturaMemray acotada, no otro full30min sin pregunta. Alternativas librerías nativas deben mantenertipos/NaN/Unicode/grandesints/excepciones/formato criptográfico; no reemplazarjson a ciegas.
Solicito: decisión finita para arrancar ahora; herramientaexistente+modo/datos; UNA candidata conservadora sihayfundamento,contraejemplos/gates/abandono; ruta distinta sólo con evidencia nueva. No prometer2/5 ni inventar heurísticos de aceptación. No inferir red de wall-CPU. Puede citar docs oficiales actuales.

Código exacto apps/safety/rights_object_delivery.py
def _fresh(export_id):
    initial = RightsExport.objects.select_related("action").get(pk=export_id)
    case, person, _ = locked_case(initial.action.request_id)
    export = (
        RightsExport.objects.select_for_update(of=("self",))
        .select_related("proof", "action")
        .get(pk=export_id)
    )
    now = timezone.now()
    if case.account_subject_id:
        from .rights_account_copy import scope_matches

        scope = scope_matches(case, export)
    else:
        scope = bool(
            person
            and not export.account_subject_id
            and not export.proof.account_subject_id
            and case.person_id == export.person_id == export.proof.person_id
            and person.manager_version == export.manager_version == case.manager_version
            and export.subject_snapshot == str(person.subject_id or "")
            and export.proof.person_rights_version == person.rights_version
            and export.proof.manager_version == export.manager_version
        )
    if case.kind == "access":
        from .rights_access_close import closure_for_export, validate_closure
    else:
        from .rights_portability_close import closure_for_export, validate_closure
    closure = closure_for_export(case, export)
    if (
        not enabled()
        or not scope
        or case.kind not in {"access", "portability"}
        or case.receipt_expires_at <= now
        or export.expires_at <= now
        or export.purged_at is not None
        or not export.encrypted_payload
        or export.channel_digest != case.receipt_digest
        or export.proof.provider != "simulator"
        or export.proof.procedure != PROCEDURE
        or export.proof.status != "passed"
        or export.proof.scope != case.kind
        or export.proof.subject_id_snapshot != export.subject_snapshot
        or export.proof.channel_digest != export.channel_digest
        or export.proof.expires_at <= now
        or export.proof.case_version + 1 != export.case_version
        or (closure is None and (case.version != export.case_version or case.status != "reviewing"))
        or (
            closure is None
            and case.proofs.order_by("-created_at", "-pk").first().pk != export.proof_id
        )
    ):
        raise Http404
    validation_case = case
    if closure is not None:
        validate_closure(closure, case, person)
        validation_case = copy(case)
        validation_case.version = export.case_version
        validation_case.status = "reviewing"
    from .rights_information_export import validate_export_binding
    from .rights_portability_export import validate_export_binding as validate_portability

    validate_export_binding(validation_case, person, export)
    validate_portability(validation_case, person, export)
    return case, export



Código exacto apps/safety/crypto.py
import base64
import hashlib
import json

from cryptography.fernet import Fernet
from django.conf import settings
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_variables


def cipher():
    key = settings.SAFETY_ENCRYPTION_KEY
    if not key:
        if settings.PRODUCTION:
            raise ValueError("Safety encryption key required")
        key = base64.urlsafe_b64encode(
            hashlib.sha256((settings.SECRET_KEY + ":dev-safety-v1").encode()).digest()
        )
    return Fernet(key)


@sensitive_variables()
def seal(payload):
    return (
        cipher().encrypt(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).decode()
    )


def digest(value):
    return salted_hmac("safety-report-v1", value, algorithm="sha256").hexdigest()


@sensitive_variables()
def unseal(payload):
    return json.loads(cipher().decrypt(payload.encode()).decode())

Resumen código sello: holds sóloTx; filtra RightsExportValidationSeal por export,rule_version y caller_digest actuales,expirytimezone.now; unseal SQLs typedparams; reejecutaordered_selects SHA256 fresh enpipeline8 oserial dentro savepoint; comparadigests yexpiry final; falseporInvalidToken/DatabaseError/type/schema. recording _annotatedSELECT añade SHA row_to_json, fetchall+stripsannotations; unsupported SQL writes/volatile/composable/timefilterwithout expiry declineseal. create sólo supported+statements+expiries. _sealed_or_full siholdstrue verificaobjetos+fotosfrescas, sino fullbinding con source_copy/unseal/evidencechain/audit/signatures/validate_transport ycreate si posible.

```

## 3 · codex · request

UTC: 2026-10-11T22:09:07.801383+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sólo WebSearch/WebFetch públicos; sin herramientas locales, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Deliberación nueva autorizada por usuario: «delibera cómo hacerlo; herramientas profesionales existentes antes que recrearlas; apruebo implementar mejoras; brainstorming entre las tres; después ejecutar». Codex dirige; Claude sólo revisión/investigación pública, sin lectura local/edición (excepción previa vigente). Notebook conserva sus fuentes.
Hechos nuevos: escenario REAL normal PG17/Django5.2.17/psycopg3.3.6/Gunicorn23, 2 workers sync, Celery2+Beat, RustFS/Caddy; presupuesto total4CPU8GiB, PG1.5CPU3GiB/app1.75CPU3968MiB/objetos.5CPU512MiB/Caddy.1CPU128MiB. Dos casos independientes cada1500revisiones/16MiBJSON/64MiBWEBP. SIN py-spy/cProfile/spans/hooks ni PGstats precargadas. p95 navegación384muestras/caso3.384803/3.389665s (objetivo2); JSON20/caso8.747557/8.961067s, binario20/caso9.033017/8.966103s (objetivo5). Todas las parejas HTTP se solapan; sólo6incumplimientos de tiempo, sin errores de operación, cuerpos/hashes/privacidad comprobados. 1389huellas iguales; cleanup completo. Descargas son partes8MiB, POST303+GET200 con DOS autorizaciones frescas. No compara causalmente con1caso.
Diagnóstico separado1caso py-spy0.4.2+PGstats: diezcapturas sinerrores; p952.483100s/JSONmax4.649687s/binmax5.422434s; sin fases/cProfile ni workerhooks. Cadena:4llamadas links340filas7.53ms temprano vs9844filas203.60ms tardío; sin Lock observado, ClientRead esbackend esperando cliente. StatsSQL anidados/globales solapan: no sumarlas como ahorro. CPU local hashes/canonical/unseal/decoding/distribuida, no único hotspot probado.
Herramientas instaladas fuera depsapp: py-spy0.4.2, Memray1.20.0, Scalene2.3.0. Memray smoke unseal16MiB sintético1559alloc196.7MBtotal89.9MBpeak; no fixture/ni ahorro. Scalene instalado no usado. Preferir API/CLI/reportes oficiales, no reconstruirprofiler. No APIpagada/account/publish. Priorizar UNA pregunta y experimento finito para localizar operación reducible; sólo integración después de equivalencia/PG/security y benchmark sinperfiladores.
Negativos previos: memoautoridad/tickets/catálogo rechazadas por frescura; cadena muta en mismaTx; advisory no bloqueaDDL; precarga assessment.encrypted_assessment oculta purga; crypto válido no frescura. MemoJSON condeepcopy perdió: parse repetido~31msCPU vs~196mscopia; no compartir dictsmutables. InlineSQL cadena HTTP beneficio pequeño/cola peor. Manifiesto paginado al materializar dict completo regresó58%; no reabrir misma candidata. Más workers ya regredió. FuenteNOembebe fotosbase64; bytes64MiB se leen/hash aparte.
Ya existen: nativecanonicalsealed, memoHMAC32MiB exactfreshbytes+currentSECRET_KEY, memoSHA64MiB exactbytes, inspection_source con freshfingerprint antes/después+canonicalmutación yfallbackfullfresh. No proponer instalarlas como nuevas. Sello replay consulta TODAS las filas actuales/expiración/key/config; no autoridad-cache. Fallback al fullbinding; necesitamos comprobar frecuencia/coste de fallo del sello, no asumir éxito.
Mi conjetura Codex: observar/explicar fallback frecuente del replayseal y coste de materialización/copia puede ser mejor que sumar más muestreos generales. PGchains incluyen propia auditoría y avanzan, así que holds puede fallar legítimamente; no excluir esas filas para fabricarhits. MemrayTracker sobre UNA autorización real puede identificar volúmenes, Scalene sobre operaciónCPU separada si necesario. Proponer primero análisis del pyspy existente y una capturaMemray acotada, no otro full30min sin pregunta. Alternativas librerías nativas deben mantenertipos/NaN/Unicode/grandesints/excepciones/formato criptográfico; no reemplazarjson a ciegas.
Solicito: decisión finita para arrancar ahora; herramientaexistente+modo/datos; UNA candidata conservadora sihayfundamento,contraejemplos/gates/abandono; ruta distinta sólo con evidencia nueva. No prometer2/5 ni inventar heurísticos de aceptación. No inferir red de wall-CPU. Puede citar docs oficiales actuales.

Código exacto apps/safety/rights_object_delivery.py
def _fresh(export_id):
    initial = RightsExport.objects.select_related("action").get(pk=export_id)
    case, person, _ = locked_case(initial.action.request_id)
    export = (
        RightsExport.objects.select_for_update(of=("self",))
        .select_related("proof", "action")
        .get(pk=export_id)
    )
    now = timezone.now()
    if case.account_subject_id:
        from .rights_account_copy import scope_matches

        scope = scope_matches(case, export)
    else:
        scope = bool(
            person
            and not export.account_subject_id
            and not export.proof.account_subject_id
            and case.person_id == export.person_id == export.proof.person_id
            and person.manager_version == export.manager_version == case.manager_version
            and export.subject_snapshot == str(person.subject_id or "")
            and export.proof.person_rights_version == person.rights_version
            and export.proof.manager_version == export.manager_version
        )
    if case.kind == "access":
        from .rights_access_close import closure_for_export, validate_closure
    else:
        from .rights_portability_close import closure_for_export, validate_closure
    closure = closure_for_export(case, export)
    if (
        not enabled()
        or not scope
        or case.kind not in {"access", "portability"}
        or case.receipt_expires_at <= now
        or export.expires_at <= now
        or export.purged_at is not None
        or not export.encrypted_payload
        or export.channel_digest != case.receipt_digest
        or export.proof.provider != "simulator"
        or export.proof.procedure != PROCEDURE
        or export.proof.status != "passed"
        or export.proof.scope != case.kind
        or export.proof.subject_id_snapshot != export.subject_snapshot
        or export.proof.channel_digest != export.channel_digest
        or export.proof.expires_at <= now
        or export.proof.case_version + 1 != export.case_version
        or (closure is None and (case.version != export.case_version or case.status != "reviewing"))
        or (
            closure is None
            and case.proofs.order_by("-created_at", "-pk").first().pk != export.proof_id
        )
    ):
        raise Http404
    validation_case = case
    if closure is not None:
        validate_closure(closure, case, person)
        validation_case = copy(case)
        validation_case.version = export.case_version
        validation_case.status = "reviewing"
    from .rights_information_export import validate_export_binding
    from .rights_portability_export import validate_export_binding as validate_portability

    validate_export_binding(validation_case, person, export)
    validate_portability(validation_case, person, export)
    return case, export



Código exacto apps/safety/crypto.py
import base64
import hashlib
import json

from cryptography.fernet import Fernet
from django.conf import settings
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_variables


def cipher():
    key = settings.SAFETY_ENCRYPTION_KEY
    if not key:
        if settings.PRODUCTION:
            raise ValueError("Safety encryption key required")
        key = base64.urlsafe_b64encode(
            hashlib.sha256((settings.SECRET_KEY + ":dev-safety-v1").encode()).digest()
        )
    return Fernet(key)


@sensitive_variables()
def seal(payload):
    return (
        cipher().encrypt(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).decode()
    )


def digest(value):
    return salted_hmac("safety-report-v1", value, algorithm="sha256").hexdigest()


@sensitive_variables()
def unseal(payload):
    return json.loads(cipher().decrypt(payload.encode()).decode())

Resumen código sello: holds sóloTx; filtra RightsExportValidationSeal por export,rule_version y caller_digest actuales,expirytimezone.now; unseal SQLs typedparams; reejecutaordered_selects SHA256 fresh enpipeline8 oserial dentro savepoint; comparadigests yexpiry final; falseporInvalidToken/DatabaseError/type/schema. recording _annotatedSELECT añade SHA row_to_json, fetchall+stripsannotations; unsupported SQL writes/volatile/composable/timefilterwithout expiry declineseal. create sólo supported+statements+expiries. _sealed_or_full siholdstrue verificaobjetos+fotosfrescas, sino fullbinding con source_copy/unseal/evidencechain/audit/signatures/validate_transport ycreate si posible.

```

## 4 · claude · opinion

UTC: 2026-10-11T22:10:10.673644+00:00

```text
# Opinión de Claude para la sala técnica. No es un PASS ni una autorización.

**Decisión:** empezar ahora con dos pasos sin tocar código ni usar instrumentación nueva. Primero, reanalizar las capturas py-spy que ya tenéis. Segundo, sacar conteos de PG ya disponibles para responder una sola pregunta: **¿cuántas veces se recorre la ruta completa (`fullbinding`) por cada autorización, y cuántas veces se descifra y parsea ese mismo payload dentro de una misma llamada a `_fresh`?** Una sola captura Memray, acotada, sólo si después hace falta. Nada de otra ejecución completa de 30 minutos.

## Lo que se lee en el código que habéis pasado (hechos)
- `_fresh` llama a **los dos validadores**, `validate_export_binding` y `validate_portability`, sin mirar `case.kind`. Las dos importaciones son incondicionales. Cada autorización (POST 303 y GET 200, o sea dos por descarga) pasa por los dos.
- `unseal` hace todo cada vez sobre el token completo: Fernet verifica el HMAC, descifra con AES-CBC, decodifica y luego `json.loads`. Para 16 MiB de JSON, el smoke de Memray ya midió 196,7 MB asignados en total y 89,9 MB de pico, aunque con datos sintéticos.
- La fila del export está bloqueada con `select_for_update(of=("self",))` dentro de la transacción. Pero sabemos que la cadena cambia dentro de esa misma transacción.

## Hipótesis (sin verificar)
H1: cada validador, o cada uno de sus fallbacks a `fullbinding`, llama a `source_copy`/`unseal` por su cuenta. Si es así, el mismo token se descifra y parsea entre 2 y 4 veces por descarga. No sabemos si los validadores salen pronto cuando el `kind` no les toca, ni con qué frecuencia el sello `holds` da false. **No está demostrado.**

## Paso 1: lo que ya existe (sin perfiladores nuevos)
1. **py-spy 0.4.2, capturas existentes.** Si tenéis la salida en `raw` o `speedscope`, agrupad por pila y mirad lo inclusivo bajo `_fresh` → `validate_export_binding` / `validate_portability` → `_sealed_or_full`. Separad la rama `holds` de la rama full. Contad los **llamadores distintos** de `crypto.unseal` y de `Fernet.decrypt`. Si sólo tenéis flamegraph SVG, no se pueden sacar conteos fiables: hacedlo constar como evidencia que falta y no lo reconstruyáis a mano. Limitación: py-spy muestrea. Da proporciones de tiempo, no número de llamadas ni causas, y viene de un solo caso.
2. **Frecuencia del fallback con datos de PG, no con hooks.** `create` sólo se ejecuta tras un fallback que se puede sellar. Por tanto, el número de filas `RightsExportValidationSeal` creadas en la ventana de la ejecución (por `rule_version` y `caller_digest`), comparado con el número de autorizaciones, da una **cota inferior** del fallback. Los fallbacks que no se pudieron sellar (SQL no soportado, volátil, etc.) no dejan fila. Si existen los snapshots de PGstats del caso de diagnóstico, comparad cuántas veces se ejecutó el SELECT del sello con cuántas veces se ejecutaron las consultas propias de la ruta full. Recordad que esas estadísticas están anidadas y se solapan: sirven para contar, no para sumar ahorros.

## Paso 2: una captura Memray, sólo si el paso 1 deja dudas
Usar `memray.Tracker(file_name, native_traces=False, trace_python_allocators=False, file_format=ALL_ALLOCATIONS)`. No usar `AGGREGATED`, porque pierde las asignaciones temporales y deja sin el reporter `stats` ([docs API](https://bloomberg.github.io/memray/api.html)). Envolver **una sola** llamada real a `_fresh` dentro de su transacción, en un proceso aparte de diagnóstico con la fixture real, no en el benchmark. Luego `memray stats` y `memray flamegraph`. El objetivo es contar cuántas veces se asignan los ~16 MiB del texto descifrado y del dict, y desde qué pila. El Tracker sigue también a otros hilos y sólo puede haber uno activo a la vez. Scalene se queda sin usar salvo que el paso 1 señale una operación de CPU concreta y aislable.

## Candidata conservadora (sólo si se confirma H1)
**Descifrar una sola vez por llamada a `_fresh` y compartir sólo `bytes` inmutables. Cada consumidor hace su propio `json.loads`.** Esto respeta los negativos previos: no se comparte ningún dict mutable y no hay deepcopy. El parse repetido (~31 ms) se conserva, y lo que se quita es el descifrado y la decodificación repetidos. El alcance es una llamada a `_fresh`, nunca entre peticiones ni entre las dos autorizaciones, así que ninguna caché ejerce de autoridad.

**Contraejemplos y condiciones:**
- Si algún validador vuelve a leer `encrypted_payload` a propósito para detectar mutaciones dentro de la misma transacción, compartir los bytes rompe esa garantía. Condición: el `encrypted_payload` que se usa en cada consumidor tiene que ser idéntico byte a byte al recién leído, y si no, se recorre la ruta full como ahora.
- `InvalidToken` debe saltar en el mismo punto y con el mismo tipo que hoy. El cambio de `SECRET_KEY` o `SAFETY_ENCRYPTION_KEY` debe seguir invalidando.
- No se toca la lógica del sello, ni `holds`, ni las filas de auditoría de la cadena. Si `holds` falla de forma legítima, eso no se corrige.
- Orden de comprobaciones: equivalencia (tipos, NaN, Unicode, enteros grandes, excepciones), suite de PG y seguridad, y sólo entonces el benchmark de los dos casos **sin perfiladores**. Las cifras de py-spy y Memray no se trasladan al p95 contractual.

**Criterios de abandono, fijados antes de medir:**
- py-spy y Memray muestran un solo descifrado por llamada, o el descifrado pesa poco frente al recorrido de la cadena.
- La frecuencia del fallback es baja.
- La equivalencia exige leer el payload otra vez.
- El benchmark sin perfiladores no se distingue del baseline. Las parejas HTTP ya se solapan, así que eso no prueba nada.

## Ruta alternativa (sólo con evidencia nueva)
Si el paso 1 muestra que el fallback es frecuente y que la causa es la cadena (filas de links de 340 → 9844, de 7,53 → 203,60 ms), el problema está en el **crecimiento de esa cadena** y no en la criptografía. En ese caso la siguiente pregunta es por qué cambian los digests del sello (su propia auditoría avanza), y para eso conviene `auto_explain`/`EXPLAIN (ANALYZE, BUFFERS)` de esa consulta. No hay que excluir filas para fabricar aciertos.

## Lo que no se puede afirmar
- Que nada de esto vaya a alcanzar 2 s o 5 s. Con un solo caso de diagnóstico no hay causalidad.
- Que `ClientRead` signifique red. Es el backend de PG esperando a su cliente, que es Django.
- Que cambiar de biblioteca JSON sea seguro. No se propone.

Fuentes:
- [Memray API docs](https://bloomberg.github.io/memray/api.html)
- [py-spy README](https://github.com/benfred/py-spy)
```

## 5 · codex · request

UTC: 2026-10-11T22:11:09.102842+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Deliberación nueva autorizada por usuario: «delibera cómo hacerlo; herramientas profesionales existentes antes que recrearlas; apruebo implementar mejoras; brainstorming entre las tres; después ejecutar». Codex dirige; Claude sólo revisión/investigación pública, sin lectura local/edición (excepción previa vigente). Notebook conserva sus fuentes.
Hechos nuevos: escenario REAL normal PG17/Django5.2.17/psycopg3.3.6/Gunicorn23, 2 workers sync, Celery2+Beat, RustFS/Caddy; presupuesto total4CPU8GiB, PG1.5CPU3GiB/app1.75CPU3968MiB/objetos.5CPU512MiB/Caddy.1CPU128MiB. Dos casos independientes cada1500revisiones/16MiBJSON/64MiBWEBP. SIN py-spy/cProfile/spans/hooks ni PGstats precargadas. p95 navegación384muestras/caso3.384803/3.389665s (objetivo2); JSON20/caso8.747557/8.961067s, binario20/caso9.033017/8.966103s (objetivo5). Todas las parejas HTTP se solapan; sólo6incumplimientos de tiempo, sin errores de operación, cuerpos/hashes/privacidad comprobados. 1389huellas iguales; cleanup completo. Descargas son partes8MiB, POST303+GET200 con DOS autorizaciones frescas. No compara causalmente con1caso.
Diagnóstico separado1caso py-spy0.4.2+PGstats: diezcapturas sinerrores; p952.483100s/JSONmax4.649687s/binmax5.422434s; sin fases/cProfile ni workerhooks. Cadena:4llamadas links340filas7.53ms temprano vs9844filas203.60ms tardío; sin Lock observado, ClientRead esbackend esperando cliente. StatsSQL anidados/globales solapan: no sumarlas como ahorro. CPU local hashes/canonical/unseal/decoding/distribuida, no único hotspot probado.
Herramientas instaladas fuera depsapp: py-spy0.4.2, Memray1.20.0, Scalene2.3.0. Memray smoke unseal16MiB sintético1559alloc196.7MBtotal89.9MBpeak; no fixture/ni ahorro. Scalene instalado no usado. Preferir API/CLI/reportes oficiales, no reconstruirprofiler. No APIpagada/account/publish. Priorizar UNA pregunta y experimento finito para localizar operación reducible; sólo integración después de equivalencia/PG/security y benchmark sinperfiladores.
Negativos previos: memoautoridad/tickets/catálogo rechazadas por frescura; cadena muta en mismaTx; advisory no bloqueaDDL; precarga assessment.encrypted_assessment oculta purga; crypto válido no frescura. MemoJSON condeepcopy perdió: parse repetido~31msCPU vs~196mscopia; no compartir dictsmutables. InlineSQL cadena HTTP beneficio pequeño/cola peor. Manifiesto paginado al materializar dict completo regresó58%; no reabrir misma candidata. Más workers ya regredió. FuenteNOembebe fotosbase64; bytes64MiB se leen/hash aparte.
Ya existen: nativecanonicalsealed, memoHMAC32MiB exactfreshbytes+currentSECRET_KEY, memoSHA64MiB exactbytes, inspection_source con freshfingerprint antes/después+canonicalmutación yfallbackfullfresh. No proponer instalarlas como nuevas. Sello replay consulta TODAS las filas actuales/expiración/key/config; no autoridad-cache. Fallback al fullbinding; necesitamos comprobar frecuencia/coste de fallo del sello, no asumir éxito.
Mi conjetura Codex: observar/explicar fallback frecuente del replayseal y coste de materialización/copia puede ser mejor que sumar más muestreos generales. PGchains incluyen propia auditoría y avanzan, así que holds puede fallar legítimamente; no excluir esas filas para fabricarhits. MemrayTracker sobre UNA autorización real puede identificar volúmenes, Scalene sobre operaciónCPU separada si necesario. Proponer primero análisis del pyspy existente y una capturaMemray acotada, no otro full30min sin pregunta. Alternativas librerías nativas deben mantenertipos/NaN/Unicode/grandesints/excepciones/formato criptográfico; no reemplazarjson a ciegas.
Solicito: decisión finita para arrancar ahora; herramientaexistente+modo/datos; UNA candidata conservadora sihayfundamento,contraejemplos/gates/abandono; ruta distinta sólo con evidencia nueva. No prometer2/5 ni inventar heurísticos de aceptación. No inferir red de wall-CPU. Puede citar docs oficiales actuales.


Corrección nueva de Codex tras inspeccionar pilas completas: en las CUATRO capturas de descarga marcadas SÍ se ve el fastpath del sello: _verify_current_images y verify_export_objects bajo _sealed_or_full; no hay _validate_export_binding en esos segmentos. NO prueba frecuencia de llamadas/cobertura global, pero contradice empezar optimizando fallbacks sin evidencia. Muestreo inclusivo mainThread: holds/_replay_pipeline~0.96-1.25s, verify_export_objects~1.52-2.87s, _verify_current_images~0.29-1.13s; se solapan, no sumar. factory._new_s3_client aparece~0.32-0.53s en POST, ya compite por CPU.
Claude ha respondido (opinión no verificación): analizar pyspy existente antes de nuevo perfilado; MemrayTracker sólo una _fresh real si dudas; no otro full30min sin candidata. Si H1descifrado repetido confirmado compartirbytesinmutables trasfreshciphertextequality/currentkey, no dicts; abandonar siunsealpequeño olecturasfrescas sealteran. No confirmó H1 ni hizo WebSearch/WebFetch (contador0). Yo descarto porahora hipótesis fallback dominante y candidataJSON/decrypt porfalta de evidencia.
Nueva ruta propuesta Codex: transporte SDK Boto3. Ya se reutiliza hasta4clientes por operación/thread (read_clients ContextVar) pero se CIERRAN al salir; cada verify_export_objects crea ThreadPoolExecutor2trabajadores, cadauno nueva boto3.session.Session().client(...), y part_bytes fuera scope creaotrocliente. SDK lowlevelclients documentados thread-safe, NO process-safe; sesionesNOthreadsafe. https://docs.aws.amazon.com/boto3/latest/guide/clients.html https://docs.aws.amazon.com/boto3/latest/guide/session.html. Posible reuse transporte entre operaciones por proceso/configexacta, SIN respuestas, autoridad, ciphertexts, tombstonescached; factory vuelve a construircrypto yreadtombstones+bodyfresh cadaobjeto. Requiere leases/refcount/close/fork/keychange, o vía existente SDK más sencilla. Pregunta ¿vale medir construccióncold vsreuse-clientreal y lecturafresca con Memray oficial/ABBA sininstrumentos, antes de cambiar producto? Considera ahorros insuficientes para2/5 y no inventarPASS. UNA ruta prioritaria, pruebas adversarias y parada.

```

## 6 · notebook · opinion

UTC: 2026-10-11T22:12:00.739944+00:00

```text
### **Dictamen de Sala Técnica Local**

**Carácter de la intervención:** Opinión técnica de evaluación y deliberación. *No constituye autorización de despliegue, cambio en producción ni certificación PASS de SLA contractual.*

---

### 1. Clasificación de Evidencia

#### **Hechos Medidos (Verificados en trazas e inspección de pilas):**
1. **SLA no alcanzado en escenario REAL (2 casos):**
   * Navegación p95: ~3.38s (objetivo ≤ 2s).
   * JSON 16 MiB p95: ~8.85s (objetivo ≤ 5s).
   * Binario 64 MiB p95: ~9.00s (objetivo ≤ 5s).
2. **Descarte del fallback dominante:** La inspección directa de pilas en las capturas de descarga confirma la ejecución por la ruta rápida (`_verify_current_images` y `verify_export_objects` bajo `_sealed_or_full`). No hay presencia de `_validate_export_binding` en dichos segmentos.
3. **Sobrecarga en Boto3:** `factory._new_s3_client` consume entre 0.32s y 0.53s en peticiones POST. `verify_export_objects` instancia un `ThreadPoolExecutor` (2 workers) donde cada hilo vuelve a invocar `boto3.session.Session().client(...)`.
4. **Especificación de SDK AWS Boto3:** La documentación oficial establece que los clientes de bajo nivel (*low-level clients*) son *thread-safe* (no *process-safe*), mientras que las instancias de `boto3.session.Session` **no** son *thread-safe*.

#### **Hipótesis:**
* Reutilizar un cliente Boto3 *low-level* (*thread-safe*) a nivel de proceso/worker (o por combinación exacta de configuración de transporte), manteniendo la reconstrucción fresca de contexto criptográfico, lectura de tombstones y cuerpo de objeto, eliminará la sobrecarga repetida de instanciación/handshake (~0.32–0.53s) sin degradar la concurrencia ni comprometer la frescura.

#### **Evidencia Faltante:**
* No se ha medido el impacto neto en p95 (navegación y descargas) que produce la reutilización del cliente Boto3 bajo la contención real del contenedor `app` (2 workers sync con 1.75 vCPU limitados).
* Se desconoce si la latencia de `_new_s3_client` se solapa con I/O o si satura ciclos de CPU requeridos por la serialización y verificación local de hashes.

---

### 2. Decisión Finita y Ruta Prioritaria

**Decisión:** **SÍ, procede medir** la diferencia entre la construcción *cold* vs. *reuse-client* en un experimento acotado antes de aplicar cambios en producto.

**Ruta Prioritaria Única:**
Evaluar la reutilización de clientes Boto3 de bajo nivel (*thread-safe*) por worker de Gunicorn, restringiendo la modificación exclusivamente a la capa de transporte S3.

**Invariantes de arquitectura obligatorias:**
1. Queda prohibido compartir instancias de `boto3.session.Session` entre hilos.
2. Queda prohibido almacenar en caché respuestas S3, autorizaciones, claves, ciphertexts, tombstones o descriptores de seguridad.
3. Cada objeto debe continuar ejecutando su validación fresca de tombstones, lectura de cuerpo y verificación criptográfica.

---

### 3. Diseño del Experimento y Métricas

1. **Herramienta y Modos:**
   * Muestreo acotado con **Memray** sobre la ejecución de UNA autorización real para auditar volúmenes de asignación de memoria en la creación del cliente.
   * Benchmark de carga **A/B/B/A sin perfilador activo** sobre el escenario de 2 casos (384 muestras de navegación, 20 descargas JSON/WEBP) para registrar el p95 real de pared.
2. **Métrica Objetivo:** Medir la reducción de tiempo en `factory._new_s3_client` y verificar su traslado directo al p95 global de navegación y descargas.

---

### 4. Contraejemplos, Gates de Seguridad y Criterio de Abandono

* **Gate 1 (Violación de Thread-Safety):** Si la implementación intenta compartir instancias de `Session` o clientes entre procesos/forks distintos, la propuesta queda **RECHAZADA de inmediato**.
* **Gate 2 (Violación de Frescura/Seguridad):** Si la reutilización del cliente causa retención de credenciales expiradas, sockets corruptos tras reconexión o altera la lectura fresca de tombstones/objetos, el cambio se **REVIERTE inmediatamente**.
* **Criterio de Abandono (Insuficiencia de Ahorro):**
  * Si la reducción medida en p95 global es **inferior a 150 ms**, o si genera contención en los workers sync de Gunicorn, la ruta se **ABANDONA**.
  * **Advertencia de alcance:** Un ahorro de ~0.3s–0.5s en la inicialización del cliente S3 es insuficiente por sí solo para cubrir la brecha de ~3.8s hacia el objetivo contractual de 5s en payloads de 16/64 MiB (donde el trabajo pesado de hashes y unseal en CPU sigue siendo determinante). Por lo tanto, **no se extrapolará esta optimización puntual como un PASS contractual.**
```

## 7 · codex · request

UTC: 2026-10-11T22:12:49.278001+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Revisión correctiva, no opinión genérica. Tu H1/fallback dominante no se sostiene en las cuatro capturas marcadas: bajo _sealed_or_full aparecen _verify_current_images yverify_export_objects fastpath, NO _validate_export_binding. Clientconstruct .32-.53s inclusivos, verifyexportobjects1.52-2.87s inclusivo, holds/_replay .96-1.25s. Intervalos solapan ysamplingnocontador; descartaroptimizarfallbacksin evidencia. No sustituirunseal ni compartirdicts (negativo31msparse/196msdeepcopy).
Nueva candidata: reutilizar lowlevelBoto3client (SDKexistingpoolHTTP) ENTREoperaciones dentromismoPID/configexacta, exclusivamente transporte, NUNCArespuesta/bytes/tombstone/autoridad. Actualmente factory usa nueva boto3.session.Session().client cada scope; read_clients ContextVar hasta4 por operación, cierratodos al salir; verifyObjects crea2threads porllamada, cadauno recreaclient. Repositorioconstruye Keyring/cipher freshcadavez yreadtombstone→GETbodydrainAEAD/hash→tombstone. Reporeadpara part_bytesfueraScope recreaotroclient. Versionboto3/botocore1.43.108. SDKclients generallythreadsafe NOprocesssafe; SessionNOthreadsafe. https://docs.aws.amazon.com/boto3/latest/guide/clients.html /guide/session.html.
Antesintegrar: experimento1 construcciónrealSDKABBA20pares frío vsreuse (límiteinferior/teórico, noHTTP), MemrayTrackeroficial enconstrucciónporseparado ystats/flamegraph; experimento2 realRustFS lecturasfrescas mismoobject4-8MiB cold/reuse +purga/corrupt/settings/key/fork/close/error. PGgateexistente parafactory/integración. Noaprobarpor microbench; si positivo cerrar cicloHTTPnormal2cases trascandidata.
¿Qué diseño mínimo recomendáis paratransport lifecycle sin poolcasero grande? Boto3client porPID/config con cap4guardimmutablefreshsettings everyhit; construcciónserialbajoLockSessionlocal, refcountleases para no cerrarclienteactivo enconfigchanges, atexitclose/fork-reset sin compartir sockets, fallingbacknative ensettings unsupported/overflow. Scopeexisting puede borrow wrapper sinclose clientehasta poolshutdown; KEEP callerlifeclose semantics tests quizácambio explícito tradeoff. ¿Mejor session/model-loaderreusepreservaTTLoperation ycacheexistingSDKcapas sinunsafeSession sharing? Esto último evita socketsfork pero talvezprivadoAPI/mutablemodelload. Propon ruta MÁS simple con contraejemplos. No inventargatepositivo ni ahorro2/5. Descarta si seguridad requiere retirarfreshchecks. DespuésdeNotebook cruzarérespuestas.

```

## 8 · claude · opinion

UTC: 2026-10-11T22:13:44.528456+00:00

```text
# Revisión correctiva: ciclo de vida del transporte S3

## 0. Corrección de mi H1

Retiro la H1 del fallback dominante. En las cuatro capturas marcadas, `_validate_export_binding` no aparece bajo `_sealed_or_full`. Lo que aparece es `_verify_current_images` y `verify_export_objects` por fastpath. Por tanto, optimizar el fallback queda descartado mientras no haya evidencia nueva. También mantengo descartadas la sustitución de unseal y el compartir dicts.

## 1. Qué está medido y qué no

**Medido** (muestreo inclusivo, no contador):
- Construcción de client: 0.32–0.53 s.
- `verify_export_objects`: 1.52–2.87 s.
- holds/`_replay`: 0.96–1.25 s.

**No se puede afirmar:**
- Que la construcción sea la parte dominante. Los tiempos inclusivos se solapan y el muestreo no da conteos exactos.
- Cuánta latencia se debe a crear el pool HTTP frente a cargar los modelos del SDK.
- Si reutilizar conexiones TCP contra RustFS local aporta algo medible.

**Hipótesis (H2):** la mayor parte del coste de construcción viene de crear un `Session` nuevo en cada scope. Eso obliga a recargar loader, modelos JSON y endpoints, y a registrar eventos. Las conexiones cuentan menos. No está verificado.

## 2. Opciones, de más simple a más compleja

**B. Una Session por PID, con `.client()` serializado bajo Lock.**
- El client sigue siendo nuevo en cada scope y se cierra igual que ahora.
- No se comparten sockets, porque el pool pertenece al client.
- Sólo usa API pública (`boto3.session.Session`, `.client()`). No toca el loader directamente.
- Ataca H2 sin cambiar el ciclo de vida.

**C. Un client por operación y config exacta, compartido entre los ≤4 `read_clients` y los 2 threads de verify.**
- Lo crea el scope y se cierra al salir de la operación.
- Los clients son thread-safe, así que los dos threads de verify pueden compartirlo.
- No hay estado entre operaciones: no hacen falta leases, atexit ni gestión de fork.
- Elimina hasta ~5 construcciones por operación. Ese número viene de la descripción del código, no es un ahorro medido.

**A. Client por PID y config con cap 4, leases/refcount, atexit y reset en fork.**
- Es lo que mencionas como candidata.
- Es la única opción que reutiliza conexiones entre operaciones.
- Trae la mayor superficie de riesgo: cambia la semántica de cierre del caller, necesita refcount ante cambios de config, y añade atexit, fork, conexiones obsoletas y DNS.

**Recomendación: B+C como ruta mínima. A queda congelada** salvo que el experimento 2 demuestre que la reutilización HTTP entre operaciones importa.

## 3. Diseño mínimo B+C

1. **Holder por PID** con `pid`, `Lock`, `Session` y la `config_key` que la creó.
   - En cada acceso se leen los settings frescos y se recalcula la `config_key`. La clave incluye endpoint, región, addressing style, timeouts, retries, verify/TLS, proxy e identidad de credenciales.
   - Si `pid` o la clave cambian, se crea una Session nueva bajo Lock. No se comparte nada con el padre.
2. **Construcción de clients:** `.client()` siempre bajo el Lock, porque Session no es thread-safe. El client resultante se usa fuera del Lock.
3. **Scope de operación:** como mucho un client por `config_key`, compartido por `read_clients` y los threads de verify. Al salir se cierran todos, igual que hoy.
4. **`part_bytes` fuera del scope:** sigue creando su propio client, que ahora se beneficia de B.
5. **Fallback nativo** a `Session()` nueva por scope, que es el comportamiento actual, en tres casos:
   - settings no soportados,
   - credenciales con proveedor no fingerprintable,
   - cualquier excepción del holder.
6. **No se cachea nada más:** ni respuestas, ni bytes, ni tombstones, ni Keyring/cipher. La secuencia readtombstone→GET→drain→AEAD/hash→tombstone queda igual. **Si algún paso exigiera retirar una comprobación fresca, la candidata se descarta.**

## 4. Contraejemplos

| Caso | Riesgo | Mitigación / estado |
|---|---|---|
| Rotación de credenciales | La Session guarda credenciales; reutilizarla puede firmar con credenciales caducadas. | La identidad de credenciales va en la clave. Si no se puede comparar sin persistir el secreto, fallback nativo. |
| Fork con Lock tomado | El hijo hereda un Lock bloqueado. | La comprobación de `pid` crea Lock y Session nuevos. Opcionalmente, `os.register_at_fork(after_in_child=...)` para resetear. |
| Contención en verify | Dos threads serializados en `.client()` podrían sumar latencia. | C lo elimina, porque se construye una sola vez por operación. |
| Config distinta dentro de una operación | — | Cubierto por la `config_key`; cap implícito de 4. |
| Client con error de transporte | En C, urllib3 gestiona el pool y la operación termina. | En A el estado persistiría entre operaciones: otro motivo para no elegirla todavía. |
| Mutación de la Session | Un `register` de eventos sobre la Session compartida filtraría a otros clients. | Hay que auditar si el código registra handlers en la Session o sólo en el client. **Evidencia faltante.** |
| Tests de cierre | — | B+C conserva el cierre al final del scope. Sólo cambia cuántos clients se cierran, y los tests que cuentan cierres deben cambiar explícitamente. |
| Memoria | Los modelos cacheados por PID pesan algo. | Medirlo con Memray, no suponerlo. |

## 5. Experimentos ajustados

**Exp 1 (sólo construcción, sin HTTP)**
- Tres brazos rotados (ABC/CBA, 20 ciclos): Session+client fría, Session reutilizada con client nuevo, y client reutilizado.
- Memray Tracker se ejecuta por separado del cronometraje, con stats y flamegraph.
- Fijar *antes* de medir el umbral que justifica seguir.
- Es un límite teórico: no permite deducir el p95.

**Exp 2 (RustFS real)**
- Lecturas frescas del mismo objeto de 4–8 MiB, en frío y con reutilización.
- Incluir purga, corrupción (el AEAD debe fallar igual), cambio de settings y de clave, fork, close durante uso y errores.
- Comparar C frente a A en este experimento. Sólo si A gana por conexiones se reabre A.

**Gates**
- Gate PG existente para factory/integración.
- Después, 2 casos HTTP normales de extremo a extremo con la candidata.
- Sin gate positivo, no hay integración. Esto es una opinión, no un PASS.

## 6. Decisión finita

- **D1:** si el brazo de Session reutilizada en Exp 1 captura la mayor parte de la diferencia frente al brazo frío, se implementa B+C, se pasan el gate PG y Exp 2, y se cierra.
- **D2:** si la construcción es marginal frente a `verify_export_objects`, no se cambia nada en transporte y se vuelve a perfilar `_verify_current_images` con contadores.
- **D3:** sólo si Exp 2 muestra una ganancia HTTP entre operaciones que C no captura, se evalúa A, con un cambio explícito y testeado de la semántica de cierre.
```

## 9 · codex · request

UTC: 2026-10-11T22:15:20.466012+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Cierrecorrectivoantes ejecutar. Claude retiraH1fallbackdominante. ProponeB reutilizarSession+clientnuevo cadaoperación yC clientcompartido sólooperación entre2threads; A clientpersistente/refcounts/forkqueda congelada. Yo Codex prefiero probarB comoSessionPERTHREAD/PID conAPIpública .client(**kwargsfresh), NO Sessionglobal compartida: evita lockfork ycontraejemploSessionthreadsafe. FuturoCtransportecompartido sólooperación con cierre despuésjoin ykwargs/settingsexactos; no extendercacheautoridad. No cambiar JSON ni compartir dicts.
Ejecutaré experimentooficialpyperf2.10.0 (aislado, gratis) para creaciónSession+client fría versus Session caliente con client NUEVO/cerrado; datosprofesionales reutilizables JSON/stats, no runnerbenchmark casero. Memray1.20.0 Tracker por separado sinpyperf para asignaciones yflamegraph oficial. SDKactual1.43.108. Ni métricas deHTTP ni fuente real aquí, primer gateinfra necesario antescandidate. Si creaciónamortizada mejoraestable yAPIconstante compatible, probarrealRustFSfreshREAD4MiB/purga/corrupt/key/settings/fork/thread/lifecycle yPGtests antesproductintegration. Sinpositivo/protocoloequivalente, no integrar ni repetir30min. Efecto microsóloalcanceCPUconstructor; noinferir2/5 ni pocoaplica38msa4s.
Correccionesatutexto: unrequesttransfierePARTE~8MiB, NO JSON16/WEBP64porpetición. Son totalesfixture. Tiempos pyspy .32-.53 soninclusivos estimadosNO conteocausalsobrecarga/handshakegarantizado; lowlevelclientcreaciónNOestablececonexión sinGET, loader/modelosposible. Umbral150mspropuesto no provienecontrato niusuario; lo rechazo comogatearbitrario. Conservo2s/5s y decisiónmicrotécnica porbeneficioestablereproducible/seguridad; losmodelosnoPASS. ¿Objeción específica BperthreadSessionconcurrentes/frameworkfork/configambiente? Respuesta breve decisión,gatesyalternativaexistingtoolsi falla.

```

## 10 · notebook · opinion

UTC: 2026-10-11T22:16:17.097447+00:00

```text
Esta intervención constituye exclusivamente una **opinión técnica** para debate y **nunca representa un PASS ni autorización** para despliegue en producción. No se cachea autoridad, se requiere comprobación fresca en cada puerta de control y se prohíbe extrapolar microbenchmarks de CPU al p95 contractual.

---

### 1. Clasificación del Estado Técnico

#### Hechos Medidos y Confirmados (Contexto Suministrado)
* **Transferencia por Petición**: Un request transfiere únicamente una PARTE de ~8 MiB (los valores de 16 MiB JSON y 64 MiB WEBP corresponden a totales acumulados del fixture, no por petición).
* **Naturaleza de Métricas py-spy (.32s–.53s)**: Corresponden a tiempos inclusivos estimados por el profiler; no constituyen un conteo causal de sobrecarga ni garantizan latencias de handshake de red.
* **Comportamiento del Low-Level Client (botocore/boto3)**: La creación del cliente de bajo nivel instancia cargadores de modelos e infraestructura en CPU, pero **no** establece conexiones de red HTTP/TCP hasta ejecutar una llamada I/O (e.g. GET).
* **Límites Contractuales Válidos**: Los umbrales de control reales conservados son 2s / 5s. El umbral arbitrario de 150 ms queda rechazado por no provenir del contrato ni del usuario.
* **Entorno de Pruebas**: Microbenchmark aislado con `pyperf 2.10.0` y análisis de asignación de memoria con `memray 1.20.0` (flamegraph oficial), sobre SDK 1.43.108.

#### Hipótesis
* La amortización de la `Session` mediante patrón per-thread/per-PID reducirá el overhead de CPU en el constructor del cliente sin afectar la estabilidad de la API pública.
* Reutilizar una `Session` caliente y crear un `.client(**kwargs fresh)` cerrado por operación evita contención de locks sin alterar la firma pública.

#### Evidencia Faltante
* Medición real con `pyperf` y `memray` que confirme la mejora cuantitativa entre creación fría vs. `Session` caliente con `client` nuevo/cerrado.
* Métricas de latencia de red e integración con almacenamiento real (RustFS fresh READ 4MiB, purga, corrupción, llaves, settings, fork/thread lifecycle) y suite de pruebas de PostgreSQL.

---

### 2. Objeciones Específicas a la Opción B (`Session` PERTHREAD/PID)

1. **Incompatibilidad con Framework Forking (Gunicorn/Celery `os.fork`)**:
   Si la `Session` per-thread se instancia antes del `fork()` del proceso trabajador (por ejemplo, durante el módulo de carga inicial de WSGI/ASGI), los locks internos del sistema de eventos de botocore (`session.events`) o descriptores SSL pueden quedar en un estado corrupto o bloqueado en el proceso hijo.
2. **Acumulación y Fuga de Configuración en Thread Pools**:
   Si el framework reutiliza hilos entre peticiones HTTP distintas, la `Session` persistida en el hilo puede acumular o cachear event listeners y metadatos de resolución de credenciales. Si los `kwargs` varían dinámicamente entre peticiones, la `Session` subyacente puede aplicar comportamientos no deseados.
3. **Inmunidad de Estado Mutado**:
   Crear `.client(**kwargs fresh)` sobre la misma `Session` compartida en el hilo no aísla las mutaciones que el cliente pueda registrar en la `Session` compartida (event hooks globales de botocore).

---

### 3. Decisión Finita y Contraejemplos

* **Decisión Finita (Opinión Técnica, NO PASS)**:
  Probar la **Opción B bajo el patrón Strict Lazy Post-Fork (`(os.getpid(), threading.get_ident())`)**:
  * La `Session` debe crearse de forma estrictamente diferida (*lazy*) **después** del fork del proceso.
  * Se invoca `.client(**kwargs fresh)` por operación, asegurando el cierre y liberación explícita del cliente al terminar la tarea.
  * Queda prohibido compartir diccionarios de configuración o mutar `session.events` dinámicamente.

* **Contraejemplos a Evitar**:
  1. *Contraejemplo A (Pre-fork Session)*: Instanciar la `Session` a nivel de módulo antes de que Gunicorn cree los workers. Provoca interbloqueos aleatorios (*deadlocks*) en los event emitters de botocore post-fork.
  2. *Contraejemplo B (Session Global Compartida entre Hilos)*: Compartir una única `boto3.Session()` entre múltiples hilos concurrentes que registren listeners dinámicos. Produce condiciones de carrera en la resolución de configuración.

---

### 4. Gates de Control Obligatorios

1. **Gate 0 (Infraestructura / Microbenchmark de CPU)**:
   Verificación con `pyperf 2.10.0` y `memray 1.20.0` de que la amortización de `Session` reduce el uso de CPU de forma reproducible y sin fugas de memoria en el flamegraph.
2. **Gate 1 (Aislamiento Post-Fork y Concurrencia)**:
   Prueba sintética multihilo tras `os.fork()` confirmando ausencia de deadlocks en locks de botocore/urllib3.
3. **Gate 2 (Integración Real con RustFS y PG)**:
   Pruebas reales contra RustFS (READ 4MiB, purga, corrupción, llaves) y PostgreSQL. Sin resultado positivo equivalente, **no integrar ni repetir ciclos de 30 min**.
4. **Gate 3 (Garantía SLA)**:
   Validación estricta frente a los límites contractuales de 2s / 5s.

---

### 5. Alternativa con Herramienta Existente si Falla la Opción B

Si la Opción B falla en los gates de fork o concurrencia:
* **Cliente Único Estático por Proceso Worker (`boto3.client` Post-Fork)**:
  Instanciar un único `boto3.client` estándar en el hook `post_fork` del worker (e.g. `gunicorn.post_fork`), reutilizando la concurrencia *thread-safe* nativa del cliente de `botocore` para llamadas I/O y manteniendo el pool de conexiones subyacente de `urllib3` activo durante el ciclo de vida del proceso trabajador, eliminando por completo la creación de clientes por petición.

---

¿Deseas que preparemos el guión del experimento aislado con `pyperf` y `memray` para validar el Gate 0?
```

## 11 · codex · decision

UTC: 2026-10-11T22:18:33.916210+00:00

```text
Codex decide arrancar por reutilización de CLIENT de Boto3 dentro de UNA operación (C de Claude), no Session persistente ni client entre requests. Los riesgos de B (config SDK implícita/cache/event/fork) requieren más inventario: no se integra B ahora. A persistenttransport/refcount también queda fuera. API SDK lowlevelclients oficialmente thread-safe; Session se crea aislada al crear primerclient, sin uso concurrente. Se amplía scope existente read_clients para préstamos explícitos entre los dos workers, construcción protegida por Lock, PID/configexacta, cierre único despuésjoin,crypto freshcadafactory+GET/tombstone/AEAD/hash unchanged. Sin nuevo poolHTTP/allocator/autoridad-cache.
Profesionales usados: py-spy previo corregido (fastpath sí); pyperf2.10.0 constructor20valores/proceso4 total20samples: cold114±56ms/warmnewclient4.24±.68ms. Avisos de inestabilidad PRESERVADOS, no PASS/gateHTTP ni ahorrogarantizado. MemrayTracker separado3constructores: cold204032346bytes/18487alloc vswarm1420939bytes/1330alloc; es constructorSDK, no _fresh completo, warmedSessionmemory fuera captura, native debug symbols incompletos. ModeloSDKallocationredundant demostrado en esta prueba; no kernel/network inference. Reportsstats/flamegraphofficialguardnoCDN/nosourcecode. Se conserva raw.
Puertas: tests lease/foreignscope/PID/config/key/close/error/thread, realRustFS cadaGETfresh/tombstone/AEAD/corrupt y ordenlifecycle; PGintegration obligatoria. Medición acotada freshverify existenteindividual2clients vsoperation shared1client en ABBA20pares (profesionalpyperfparaSDKconstructor, existing realpytestfixtureparaIO notprofilerhomemade). No instrumentacionencronómetro. Si mediana regrede/inconsistente osecurityfail, no integrate. Sólo positivo permite productproof+HTTPnormalfinal, nunca extrapolar2/5. Si mejora pequeña se acredita incremental ycapacidad siguependiente. UmbralNotebook150ms no adoptado, partes8MiBcorregidas, modelopinionnoPASS.

```
