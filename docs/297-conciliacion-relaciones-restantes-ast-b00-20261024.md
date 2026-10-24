# B00-338 — Relaciones históricas completas y resolución de referencias AST

Fecha:2026-10-24. Disposición de cuatro capturas y correcciones dirigidas del grafo actual.

B00-338: 293 de295fuentes únicas conciliadas; quedan dos capturas históricas de nodos. Completada la revisión estructurada de las seis capturas de relaciones y corregidos once destinos de referencias AST del grafo actual, incluidas seis falsas autorrelaciones de herencia. Sin cambios de aplicación ni nueva aceptación funcional. B00 sigue abierto; nueve de18puntos beta cerrados y B15 opcional.

## Cobertura aceptada

Veintiséis lectores nuevos revisaron cuatro capturas de11/10/2026/base7e04016: relaciones1,2,5y6. Son25.230registros y9.494.867caracteres originales. El método contextual aprobado en [corte337](296-conciliacion-relaciones-ambitos-ast-b00-20261024.md) representa todos los atributos mediante constantes, esquemas, diccionarios y filas; los lectores leyeron e interpretaron las26vistas completas,2.432.356caracteres en215intervalos de hasta12.000caracteres, y decodificaron todos los grupos, incluidos casos únicos y transiciones. No se afirma lectura literal completa del formato original ni de los cuerpos de nodos o archivos referenciados.

| Captura | ID | Registros | Partes | JSON original |
| --- | --- | ---: | ---: | --- |
| Relaciones1/6 | `source:xuawvq62yt440dmn8fbo` | 7000 | 5 | Estricto válido |
| Relaciones2/6 | `source:4kdylefbew2cj0asrzsm` | 7000 | 7 | Control sin escapar en1458397 |
| Relaciones5/6 | `source:18xdl1s69ma44vpy12vz` | 7000 | 10 | Control sin escapar en1884423 |
| Relaciones6/6 | `source:g0i02979iw5jxwwamybk` | 4230 | 4 | Estricto válido |

SHA256 de los textos, en ese orden: `778ddb24a18fa9654277901f4e6a99d1b3f8a78da793e92500f722b0da4302e9`, `d6baa8675e069c2f4a5a527d0676b01c89267ffd909b922e71f5494c88c5101f`, `121a6bc6a9f4daa26b6c36e554ee3f153be2a5a9445082bc7c0763d026612d3d` y `d455089622c0d2a2d0222f158778d02630241ab154df25e2009c794b7d20d6fc`.

El principal revalidó las295capturas, reconstruyó cada atributo/tipo/presencia/orden contra cada registro y posición original, rechazó claves duplicadas y constantes no JSON, verificó sobres completos y uniones sin huecos/solapamientos, cotejó52citas originales seleccionadas y reconstruyó la membresía exacta de todos los grupos. Preparar o parsear tablas no recibió crédito semántico automático: se evaluaron los informes de interpretación y su procedencia, conservados como extractos seleccionados, no transcripciones íntegras. Se mantienen original_literal_capture_fully_read=false y rangos de registros separados de rangos literales.

Dos informes inicialmente incompletos sólo omitían la declaración explícita del presupuesto exterior: usaron el valor por defecto documentado10000 y el presupuesto interior explícito10000, sin truncamiento ni pérdida de cobertura. El principal aceptó esa equivalencia y los lectores emitieron suplementos de estado; no releyeron vistas válidas. Se conserva el desvío. Tres lectores declararon salidas auxiliares de grupos mayores de12.000caracteres; uno reemitió su inventario acotado. Las vistas principales fueron completas y esas salidas auxiliares no reciben crédito independiente. Otro probe imprimió por error un mapa ajeno truncado: cero crédito por ese contenido. La inspección inicial de una tarea usó el otro entorno Python, pero las lecturas posteriores usaron la ruta designada y las huellas coinciden. Se conservan también intentos exploratorios de decodificación corregidos, sin reparar datos.

Las particiones se redujeron antes de delegar para mantener cada vista definitiva por debajo de120.000caracteres. El plan preliminar sólo fue preparación. Hay26lectores y dos suplementos, cero nuevas invocaciones ClaudeV1; se preservan las ocho históricas y su consumo, sin estimar tokens nativos. El revisor de método anterior no se cuenta como nueva revisión de estas fuentes.

## Qué contienen los registros

Relaciones1 conserva7.000calls con contexto call y clasificación EXTRACTED. Cruza aplicación, herramientas, pruebas, evidencia y JS vendorizado; las llamadas a preparación, autorización, revisión, consumo, generación o limpieza no acreditan sus resultados. Los grupos de archivo pueden reaparecer en tramos no contiguos, por lo que un intervalo mínimo/máximo no sustituye su membresía completa. Los nombres minificados de HTMX y ubicaciones L1 no localizan de forma fiable un comportamiento del producto.

Relaciones2 conserva1.803calls,155contains,1.497references de decoradores, una re_exports y3.544imports. contains/context=call se interpreta como contención léxica capturada, no ejecución. Múltiples decoradores, parametrización, fixtures, skips y referencias a transacciones describen estructura; no son pruebas ejecutadas ni mecanismos efectivos demostrados.

Relaciones5 conserva4.427contains,75inherits,334method,826rationale_for,167references,769indirect_call y402calls. Los5.829primeros registros EXTRACTED carecen de context; ausencia no se transforma en null explícito. Después aparecen1.171INFERRED con context de argumento, asignación o llamada. Rationale_for identifica dónde se adjunta una explicación, sin suministrar su cuerpo. Los títulos de contratos, actas, instrucciones y seguimiento históricos no se adoptan como reglas actuales ni acreditan estados o aceptaciones.

Relaciones6 conserva4.230INFERRED:129calls,34indirect_call,156references y3.911uses. Las inferencias de usos tienen score0.95/peso0.8; otras familias usan score0.85/peso1. Un score alto no verifica flujo de datos, permisos o ejecución. Los contextos collection/getattr/return y referencias documentales con términos genéricos conservan su significado limitado. En las cuatro fuentes revisadas suman5.401INFERRED; el origen ast no los convierte en resultados de ejecución o revisión humana aceptada.

Se preservan exactamente los dos campos con controles sin escapar: rutas de config/init y object_storage/init. El decoder permite esos controles sólo bajo guardas y tras conservar el fallo del parser estricto; no normaliza a __init__.py ni acredita los bytes del productor. El grafo antiguo no se restaura o importa al actual. Con el corte337, las seis capturas de relaciones —39.230registros— tienen disposición estructurada; los9.171nodos y sus atributos todavía requieren las dos capturas restantes.

## Decoradores: cuatro destinos ajenos corregidos

Las capturas señalaron referencias de decoradores hacia funciones de pruebas ajenas. Se contrastaron y reprodujeron esas asociaciones en el grafo actual. El [observador Celery](../scripts/benchmark_celery_observer.py) importa before_task_publish,task_prerun ytask_postrun de celery.signals y utiliza sus expresiones .connect; sus tres handlers apuntaban al método HTTP CONNECT de un helper de pruebas. El [probe de recuperación](../scripts/probe_recovery_task_gate.py) usa app importado de config.celery y @app.task; apuntaba a una función de prueba de caducidad.

Se sustituyeron esos cuatro destinos por referencias sintácticas cualificadas según los imports y el AST actual: celery.signals.before_task_publish.connect,celery.signals.task_prerun.connect,celery.signals.task_postrun.connect yconfig.celery.app.task. No se importaron los observadores/probes, registraron hooks o inicializó Django. La cualificación demuestra la expresión del código fuente, no la identidad del objeto en ejecución.

## Herencia: distinguir Str de str

El [test de equivalencia canónica](../tests/test_rights_native_canonical_equivalence.py) declara Str(str),Int(int),Float(float),Dict(dict),List(list),Tuple(tuple) yNumber(IntEnum). La normalización había confundido los seis nombres de clase con las bases builtin, generando seis autorrelaciones de herencia. La séptima base permanecía como intenum sin cualificar.

Se comprobaron las declaraciones, los imports y la ausencia de redefiniciones de esos nombres builtin en el módulo. Se dirigieron las siete referencias a builtins.str/int/float/dict/list/tuple yenum.IntEnum. Se conservan los nodos de las clases originales y sus demás relaciones. No se ejecutaron pruebas nativas, evaluó MRO en runtime ni cambió el codificador por esta corrección.

Las dos reparaciones añaden11nodos de referencia y cambian11destinos, sin añadir relaciones. La verificación independiente contrastó el AST y comprobó que todos los otros nodos y aristas permanecían idénticos antes del refresco documental. Las autorrelaciones bajan de136a130 por las seis falsas herencias; las restantes no se clasifican automáticamente como defectos o recursión. El sello registra estas reparaciones y detecta su pérdida o una fuente cambiada. Se conservan además las48Meta cualificadas del corte337. No es una corrección global de graphifyy; una extracción futura requiere revalidar estas resoluciones.

## Inferencias y contraste actual

Persisten asociaciones INFERRED con nombres genéricos —render,copy,client,check,key ocallbacks— que pueden apuntar a namespaces ajenos por heurística. No se presentan como dependencias actuales verificadas. Sólo se corrigen aquí los once destinos cuya sintaxis se contrastó directamente; no se borra toda inferencia dudosa ni se convierte una etiqueta EXTRACTED en garantía global.

El contraste seleccionado abarca10archivos y21literales. [Visibilidad](../apps/listings/moderation.py) y [política del perfil](../apps/listings/profile_contract.py) mantienen validación romántica. Los auxiliares de [geografía](../static/geography.js) y [búsqueda](../static/search-geography.js) manipulan controles, sin que la similitud de nombres minificados pruebe relaciones de dominio. [RecoveryAwareTask](../config/celery.py) declara su guarda; no se infiere la operación de workers desde el grafo.

En [revisión de cobertura](../apps/safety/rights_access_coverage_review.py) y [autoridad de revisión](../apps/safety/rights_access_response_review.py) se localizaron comprobaciones actuales de permisos, sesión y MFA y reautorización al final. Esta lectura no verifica frescura en cada punto de espera o descifrado. Las hipótesis de revocación requieren reproducción PostgreSQL propia antes de declararlas defectos; no se atribuye una filtración por ver una secuencia de llamadas. No se modificó aplicación/pruebas ni se ejecutó otra batería funcional en este corte.

## Estado y continuación

[Ledger](evidencias/b00-current-source-review-ledger-20261023.json):289a293disposiciones, seis a dos pendientes, base289SHA3abd1e935e23c7035e30c38d933968e2d1b72e3fa2fc9ee5ebc78fe1c845df78fijada, reemplazo atómico y permisos conservados. Artefactos `artifacts/beta-promotion-fix-20261020/b00-338-*`; verificadores fijados a su corte, sin sobrescribir un ledger posterior. Grafo391 revalidado al iniciar, reparaciones AST dirigidas e integración semántica392 con citas al código actual. Sin AST global, detección global de comunidades, semántica exhaustiva o HTML global.

Quedan las dos capturas de nodos,3.738.548caracteres: `source:gbdn3ox1asszgxe8nytq` y`source:a3xmiqi2izexc6m6pgni`. Continuar con todos sus atributos, explicaciones preservadas y límites, después consolidar requisitos y pendientes de B00. La conciliación de fuentes no cierra por sí sola B00, beta, capacidad, seguridad global o producción. Nueve de18puntos beta cerrados; B15 opcional con diseño de cookies/preferencias privadas aún pendiente de implementación. Sin proveedores, publicación, gasto o datos reales. Corte previo: [conciliación296](296-conciliacion-relaciones-ambitos-ast-b00-20261024.md).
