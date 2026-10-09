# Matriz de ejecución y cierre por derecho — CR09

Referencia histórica inicial:53b9628, workspace limpio al inicio de aquella revisión. Es una matriz técnica para desarrollar los tramos faltantes; no acredita revisión jurídica ni nueva ejecución de pruebas. [Fuentes/funciones/hashes](evidencias/matriz-derechos-fuentes0100.json). Matriz residual global:docs83; ponderación:docs86.

## Estado vigente y componentes cerrados

Revisión documental del 2026-10-09: la tabla siguiente consolida componentes de derechos y sus evidencias, con los cortes de entrega indicados. La reconciliación posterior a la aceptación local de CR09-REND-LECTURA está en el [acta residual](evidencias/residuales-locales-post-aceptacion0110.json). Ese cierre no acepta los derechos integrales ni CR09/GS01/producción. Los insumos faltantes y el bloqueo del goal posterior se consultan en [seguimiento17](17-seguimiento-desarrollo.md); los apartados de método y desarrollo inferiores no constituyen otra cola.

Actualizado el 2026-10-06. Base de las entregas anteriores: `1c69d12` (0107). Actualización vigente hasta `38140e9`: acceso/rectificación locales y respuestas parciales de supresión/limitación/oposición integradas; recursos operativos/aceptación integral pendientes. Runtime y próximo trabajo se mantienen únicamente en [seguimiento17](17-seguimiento-desarrollo.md). Esta tabla consolida el estado actual y prevalece sobre los estados provisionales de las anotaciones históricas inferiores. «Cerrado localmente» significa criterio del componente satisfecho; no aceptación del derecho completo ni de CR09.

| Componente | Estado actual | Alcance cerrado y evidencia | Commit de entrega |
| --- | --- | --- | --- |
| Borrador y revisión de respuesta | Cerrado localmente | Preparación/revisión independiente e interfaz PG + Chromium ES/EN; [evidencia0102](evidencias/acceso-revision-runtime0102.json) | `5401c57` |
| Motor de contabilidad | Cerrado localmente | Validación lógica de referencias, filas, campos y límites; pruebas sin DB, no aceptación web | `71710f8` |
| Referencias de evidencia | Cerrado localmente | Ámbito/huellas comprobados en PostgreSQL; no aprobación de contenido por sí solas | `237ab13` |
| Persistencia cifrada de contabilidad | Cerrado localmente | Preparación auditada/replay/purga PG; [evidencia0103](evidencias/acceso-cobertura-persistencia0103.json) | `49c6d9e` |
| Revisión independiente de contabilidad | Cerrado localmente | Comparación original/copia y decisión privada; [evidencia0104](evidencias/acceso-cobertura-revision0104.json) | `0be7808` |
| Consumo de evidencias y vínculo a respuesta | Cerrado localmente | Cuerpos tipados/aprobación vigente ligados al borrador; [evidencia0105](evidencias/acceso-consumo-respuesta0105.json) | `4428c22` |
| Inventario de registros/campos | Cerrado localmente | Ámbitos recogidos, huellas y cifrado PG; [evidencia](evidencias/acceso-inventario0106.json) | `b5b6c24` |
| Consulta privada del inventario | Cerrado localmente | POST auditado/paginación/GET sin datos PG + Chromium ES/EN; [evidencia](evidencias/acceso-inventario-interfaz0106.json) | `ff0c090` |
| Consulta tipada de valores | Cerrado localmente | Campos soportados User/Revision/Rate, lectura exacta y UI; [evidencia](evidencias/acceso-lectura-campos0106.json) | `1c23253` |
| Decisión y revisión por campo | Cerrado localmente | Inclusión/omisión/redacción, revisión/consumo vigente, purga y UI; [evidencia0107](evidencias/acceso-decision-campos0107.json) | `1c69d12` |
| Copia suplementaria agregada | Cerrado localmente | Materialización de decisiones aprobadas, pendientes explícitos, interfaz PG + Chromium ES/EN; [evidencia](evidencias/acceso-suplemento0107.json) | Esta entrega |
| Cobertura completa, emisión/cierre/descarga de acceso | Recorrido local verificado; censo operativo real pendiente | PG + Chromium ESEN perfil/cuenta, carreras/revocación/descarga; [resultados](evidencias/acceso-integrado0108-resultados.json) y [runtime0108](evidencias/acceso-runtime0108-resultados.json). Origen de censo sintético en pruebas, no acreditar host/proveedor real | `f252ae0` |
| Respuesta/revisión/cierre de rectificación perfil/cuenta | Cerrado localmente en alcance probado | Cuatro casos integrados, carrera y regresiones de acuse; [resultados](evidencias/rectificacion-final0108-resultados.json) y [runtime](evidencias/rectificacion-final-runtime0108.json). Decisiones/evidencias sintéticas, no aceptación operativa real | `187b8e6` |
| Respuestas parciales de supresión/limitación/oposición | Verificadas localmente; aceptación integral pendiente | Motor/acuse compartidos, veinte pruebas conjuntas y Docker; [resultados](evidencias/limitacion-oposicion-final0108-en-desarrollo.json), [runtime](evidencias/limitacion-oposicion-final-runtime0108.json) | `38140e9` |
| Purga de nuevos borradores finales | Verificada localmente en su alcance |0109,26 pruebas integradas y worker/Beat reales; borradores vigentes/emitidos/auditoría preservados. [Operación](evidencias/conservacion-borradores-finales0109-worker-beat.json), [runtime43 archivos](evidencias/conservacion-borradores-finales0109-runtime.json). Conservación integral separada | Núcleo `72ff79a`, runtime `9be0044` |
| Comunicaciones internas de supresión/limitación/oposición | Verificadas localmente en alcance probado | Evaluación/revisión, entrega mínima a destinatarios vigentes, consulta/acuse auditado, concurrencia, reevaluación y respuesta parcial. [Resultados0110](evidencias/comunicaciones-derechos-integradas0110.json), [runtime0110](evidencias/comunicaciones-derechos-runtime0110.json). Destinos históricos/externos y censo integral pendientes | `637e456` |
| Restantes derechos y fases posteriores del contrato | Pendientes de aceptación | Mantener alcance original y matriz residual; no inferir cierre por componentes de acceso | — |

Regla de reapertura: solo defecto reproducible, regresión demostrada o requisito concreto del contrato que este componente todavía deba cumplir. Registrar motivo, alcance afectado y evidencia antes de ampliar una pieza cerrada; repetir únicamente pruebas afectadas. Integrar un componente existente en la siguiente entrega no revoca su cierre local. No ampliar controles por hipótesis ni volver a auditar piezas cerradas para obtener más señales verdes.

## Método de continuación vigente

[Plan de cierre integrado CR09-END-ACCESS](89-plan-cierre-integrado-cr09.md) sustituye la secuencia de nuevas entregas auxiliares. El censo de columnas no equivale a datos personales exigibles ni a aprobación manual obligatoria de cada campo. Integrar un paquete completo con correspondencia comprobable para datos ya proyectados y tratamiento real de omisiones; extender la revisión existente y cerrar/descargar en el mismo recorrido. No ampliar piezas cerradas por hipótesis ni considerar el cambio de método como aceptación.

## Recorridos y aceptación

| Derecho | Evidencia de implementación existente | Tramo todavía necesario |
| --- | --- | --- |
| Representación | rights_responses.issue(representation_complete), RightsWithdrawal y prueba/gestor/consentimiento/publicación concordantes | Integrar en regresión final, comunicación/conservación; no convertir retirada de representación en supresión integral |
| Portabilidad | rights_portability_close.close, borrador/revisión independiente/entrega y cobertura aprobadas; descarga privada ligada al cierre | Variantes/rendimiento/comunicación y aceptación integral; conservar diferencias con acceso |
| Acceso | Paquete/revisión/cierre/descarga privados verificados localmente en0108; identidad/aviso y origen del censo sintéticos en pruebas | Contrastar censo operativo real sin declaraciones vacías, integrar aceptación global; conservar revisión y controles existentes |
| Rectificación de perfil | Propuesta/revisión/comunicación previa/acuse/ejecución y respuesta progress; avisos gestores, inventario y evaluación de destinatarios | Respuesta/revisión/cierre locales PG y móvil ESEN verificados en `187b8e6`; contrastar pendientes/evidencias reales, comunicación y conservación; cierre no publica |
| Rectificación de cuenta | Propuesta/revisión/confirmación de destino/acuse/ejecución sin crear perfil | Inventario/evaluación/revisión de destinatarios de cuenta sin perfil verificados localmente y entregados en `02210aa`; respuesta/revisión/cierre local y carrera PG verificados en `187b8e6`; resolver pendientes reales y aceptación integral, sin consultar perfiles por propiedad de agencia |
| Supresión | Inventario/plan/ejecución y recuperación; respuesta parcial integrada con lectura/revisión/emisión/acuse, perfil y cuenta sin Person;10 pruebas conjuntas y2 medios/concurrencia separadas; Docker0108 fuente38140e9 verificado, integrada20 común con limitación/oposición | Cobertura operacional real/conservación/comunicaciones y cierre integral; mantener abierto si quedan finalidades o verificaciones pendientes |
| Limitación | Medidas por finalidad y respuesta parcial exacta con consulta/revisión/emisión/acuse, cuenta/perfil/publicación/calendario, móvil y Docker38140e9; batería común20 correcta | Cobertura operacional real/conservación/comunicaciones y cierre integral; cerrar expediente no libera restricciones |
| Oposición | Plan/revisión/ejecución y respuesta parcial propia object, decisiones cease/continue y pendientes exactos, cuenta/perfil/mezcla/calendario, móvil y Docker38140e9; batería común20 correcta | Cobertura operacional/comunicaciones y cierre integral sobre cada decisión/excepción; no equiparar a limitación ni a denegación genérica |
| No actuación o actuación parcial | Respuestas progress e inventarios de pendientes | Recorrido motivado con evidencia de alcance y comprobaciones proporcionadas; revisión jurídica externa de motivos. No crear botón genérico denegado para ocultar funciones pendientes |

## Especificación conservada del recorrido de acceso

1. Preparación privada sobre expediente access asignado, con lectura auditada completa, identidad/ámbito comprobados, MFA/sesiones/permisos vigentes y ausencia de conflicto.
2. Borrador liga la respuesta exacta a copia entregable e información/cobertura aprobadas, versión del caso/respuestas, pruebas, origen y caducidad. Las exclusiones y pendientes deben ser explícitos; una copia preparada no demuestra cobertura completa.
3. Otro actor consulta los elementos completos de la evidencia y el texto, y registra revisión independiente de esa misma versión. Revocación/cambio de fuente o permiso invalida el recorrido.
4. El cierre consume exactamente esa revisión, crea respuesta privada/outbox cuando proceda, incrementa versiones y resuelve solo access. Atomicidad e idempotencia verificadas; no cerrar con progress ni reutilizar portability_complete.
5. Descargas posteriores requieren el cierre correcto y conservan controles de caducidad, prueba, contenido, permisos y confidencialidad; no hay confirmación automática de recepción.
6. Front y back se prueban juntos: formularios ES/EN, errores/estado pendiente, lectura POST auditada y GET sin descifrar contenidos, móvil, CSRF, conflictos y concurrencia. No declarar el flujo cerrado con solo servicios internos.

## Orden de implementación

Acceso → rectificación (perfil y cuenta) → supresión → limitación/oposición → comunicaciones/escalado/conservación/rendimiento y aceptación integral. Cada recorrido debe aportar ejecución exacta, revisión, respuesta y cierre; los servicios ya existentes se reutilizan preservando su semántica. Si el examen de un recorrido demuestra un bloqueo funcional concreto, corregirlo y verificar su alcance. No ampliar recuperación por hipótesis ni omitir sus requisitos explícitos pendientes.

CR09 no se considera aceptado por esta matriz. CR10→GS01→BF/BB→C permanecen en el contrato. No se recalcula la ponderación solo por crear documentación.

## Revisión de avance con Git — 2026-10-06

HEAD y referencia local origin/master coinciden en `53b9628a21675fc048911ad35e9900cc88293e25`; esta comprobación no consulta de nuevo el servidor remoto. Los cuatro commits posteriores a `83c9d63` cambian 53 archivos, con 3353 inserciones y 47 eliminaciones. Estas cifras describen actividad, no porcentaje de terminación. Incorporan aplicación de efectos de recuperación, restauración PostgreSQL, referencias firmadas para fotografías compartidas, autoridad del checkpoint, aislamiento de colas y limpieza condicionada de sesiones. La evidencia integrada de la última entrega registra 86 pruebas en 313,03 segundos, con límites de alcance explícitos.

Diagnóstico: existe avance funcional comprobable, pero una concentración excesiva en recuperación; CR-09 permanece abierto y CR-10 no se ha iniciado como fase. No aumentar el porcentaje por volumen de código o pruebas. La preparación de respuesta de acceso y migración 0101 presentes en el árbol de trabajo están en desarrollo, sin entrega ni verificación acreditada. Prioridad: completar el recorrido cruzado de acceso con revisión independiente, respuesta y cierre antes de extender nuevamente recuperación, salvo defecto concreto.

## Preparación de respuesta de acceso — migración 0101

`RightsAccessResponseDraft` conserva el texto cifrado, huella del texto, referencia a la información aprobada y sus cinco huellas vinculadas a la exportación, prueba nueva posterior a ella, versiones de expediente/respuestas y épocas de sesión/MFA. La preparación exige actor asignado con permisos actuales, lectura del expediente/respuestas, exportación propia y autoridad vigente. Se registra la operación antes de validar contenido histórico; reintentos con texto o referencias distintos se rechazan. No emite respuesta, no modifica el estado ni demuestra cobertura completa de acceso.

Los inventarios de supresión de perfil/cuenta incluyen el nuevo modelo. La tarea `purge_expired_access_response_drafts` elimina texto cifrado caducado en lotes de hasta 100, con bloqueo y conservación de metadatos; Beat la programa cada 60 segundos. La ejecución real de worker/Beat para esta tarea nueva todavía no está verificada.

Primera ejecución local PostgreSQL: dos casos de perfil/cuenta correctos en 44,66 segundos (`/tmp/access-draft0101.xml`). Cubren autorización posterior a exportación, auditoría antes de validación histórica, cifrado, idempotencia, conflicto de texto, corrupción y cambio de política. La ejecución ampliada PostgreSQL terminó con tres pruebas correctas en 56,51 segundos (`/tmp/access-draft0101-final.xml`): incluye la purga idempotente, conservación de referencias y regresión del censo de dependencias. Ruff y `makemigrations --check --dry-run` terminaron correctamente. No se ha actualizado el runtime Docker ni probado worker/Beat con esta tarea nueva. Faltan interfaz cruzada, validador independiente de evidencia, revisión independiente, cobertura completa y cierre tipado; no aceptar CR-09 ni incrementar avance estimado por este borrador interno.

## Revisión independiente de respuesta de acceso — 0102 en desarrollo

Modelo `RightsAccessResponseReview`, decisión única por borrador, huellas de texto/cifrado, referencias a lectura y decisión y épocas de sesión/MFA. Servicios separados de portabilidad: operaciones `access_draft_read` y `access_draft_review`, comprobación de autor independiente y permisos actuales, firmas de contexto, validación histórica de información/exportación y autorización nueva. La decisión no emite respuesta ni cierra. Inventarios incluyen revisión como evidencia dependiente; censo de cuenta pasa a 69 modelos.

Rutas de preparación y revisión bajo `/moderation/rights/<case>/access/response/`; formularios y plantillas ES/EN, páginas privadas sin descifrado GET y lectura POST auditada. Falta integrar navegación desde el expediente y prueba navegador real, además de cierre/cobertura completa.

Primera prueba detectó nombres de operación superiores al límite de 20 caracteres; se corrigieron sin ampliar el campo. Batería corregida PostgreSQL: tres pruebas correctas en 59,61 segundos (`/tmp/access-review0102-final.xml`), incluye revisión independiente, obligación de lectura exacta, idempotencia y rechazo de firma alterada. `manage.py check` y coherencia de migraciones correctos. Batería HTTP/CSRF terminal: tres pruebas correctas en 61,86 segundos (`/tmp/access-review-ui0102.xml`). Comprueba lectura POST, GET sin contenido, decisión sin exposición, CSRF y aislamiento del autor. Sin commit/entrega de 0102 ni actualización de Docker.

Navegación añadida desde expediente: preparación para actor asignado y listado paginado de borradores ajenos para revisor autorizado, sin texto en GET. Regresión PostgreSQL terminal: tres pruebas correctas en 65,02 segundos (`/tmp/access-review-navigation0102.xml`), incluidos enlaces separados por actor.

Chromium real con live_server y PostgreSQL: cuatro variantes móviles ES/EN × perfil/cuenta correctas en 82,43 segundos (`/tmp/access-review-mobile0102.xml`). Preparación con formulario, navegación al borrador ajeno, lectura auditada y aprobación; comprueba que el texto no reaparece tras aprobar ni en GET, sin desbordamiento horizontal a 390 × 844. El expediente conserva estado y versiones: este recorrido todavía no incluye cierre.

Docker local actualizado a migraciones 0101/0102, app/worker/Beat reconstruidos; 12 archivos de código/configuración/plantillas coinciden por SHA-256 con host en los tres procesos. Django check y migrate check correctos, salud HTTP200, app UID10001; tarea de purga registrada en worker. No afirmar purga de contenido caducado real mediante Beat: la ejecución con contenido se verificó directamente en PostgreSQL de pruebas, no en el runtime normal. Evidencia acceso-revision-runtime0102.json.

Próximo desarrollo: cobertura de acceso con decisiones expresas sobre todos los ámbitos pendientes de la copia de perfil (`image_content`, `shared_contacts`, cuenta no vinculada) o cuenta (`purpose_inventory`, `other_account_records`), exclusiones motivadas y copia/información exactas verificadas independientemente. No convertir el marcador `partial` en completo ni reutilizar cobertura de portabilidad como evidencia de acceso. Después: emisión/cierre tipados, descarga privada tras cierre, idempotencia/concurrencia y recorrido navegador completo.

## Contabilidad de cobertura de acceso — motor interno en desarrollo

`rights_access_coverage.compile_coverage` contrasta huellas exactas del origen y entrega, todas las secciones de la proyección (incluidas vacías), referencias de todas las filas de origen y asignación única de cada fila entregada. Cada campo omitido/modificado exige decisión `omitted`/`redacted` con motivo y evidencia declarada; rechaza datos/campos/contenedores adicionales sin origen y deja intactos los marcadores `partial`. Usa únicamente utilidades estructurales de campos y referencias del código de portabilidad, sin adoptar sus criterios de elegibilidad o aprobación.

Los ámbitos pendientes de ambas proyecciones y los límites no proyectados `purpose_inventory` y `other_subject_records` se conservan obligatoriamente en el manifiesto. Se exige documentación `excluded`/`supplemented` con motivo y evidencia declarados; una cadena de texto no verifica esa evidencia ni acredita una exclusión procedente. Este motor no autoriza acceso, no aprueba una denegación, no certifica completitud del derecho y todavía no se consume en el cierre. El servicio siguiente debe vincular registros comprobables/huellas a cada decisión, permitir su lectura independiente y rechazar referencias inexistentes/obsoletas antes de aprobarlas. No usar `other_subject_records` como exclusión genérica para eludir el inventario de datos.

Pruebas lógicas sin base de datos: 14 correctas en 0,58 segundos (`/tmp/access-coverage-accounting0102-final.xml`), incluídos campos/ámbitos pendientes, filas ajenas, referencia/digest alterados, índice booleano, secciones ausentes, contenedor vacío ajeno y redacción con tipo de decisión correcto. Ruff correcto. Esto no constituye prueba de integración PostgreSQL ni recorrido web. Próximo: persistencia cifrada/auditada ligada a exportación e información aprobadas, inventarios/purga, revisión independiente del origen/copia/evidencias y consumo por cierre. No aumentar porcentaje por este motor aislado.

## Referencias comprobables de evidencia — desarrollo pendiente de integración

`rights_access_evidence_refs.bind_references` enlaza IDs y huellas de acciones `copy_page_save`/`copy_info_review` al mismo expediente y versión exacta de preparación de la exportación, con bloqueo transaccional. La huella cubre actor, operación, versión, payload y razón cifrada; no descifra ni expone contenido. Rechaza versiones/operaciones ajenas, ID booleano y alteraciones. No concede permisos ni aprueba la decisión: el consumidor debe sostener los bloqueos y autorización canónicos y validar además las pruebas históricas, épocas y cuerpos de las filas concretas.

Pruebas PostgreSQL con información/exportaciones aprobadas sintéticas de perfil/cuenta: dos correctas en 44,91 segundos (`/tmp/access-evidence-refs0102.xml`). Ruff y check correctos. Sin commit ni integración web del adaptador; persistencia de cobertura, lectura independiente de cuerpos y cierre permanecen pendientes.

## Persistencia de cobertura — 0103

`RightsAccessCoverage` guarda cifrados copia/declaraciones/referencias/contabilidad y liga expediente, actor, exportación, información aprobada, prueba nueva, versiones y épocas. `rights_access_coverage_store.save` exige actor asignado, permisos actuales, lectura del expediente/respuestas y comprobación posterior a exportación; registra auditoría antes de validar/descifrar evidencia histórica. Valida transporte exacto de copia (incluido manifiesto fragmentado), huella de origen de la información aprobada, referencias por cada decisión y manifiesto de contabilidad. Reintento debe conservar razón, todas las referencias, huellas, contenido y vigencia. No aprueba exclusiones por contener una razón ni cierra el derecho.

Inventarios perfil/cuenta incluyen el modelo; censo de cuenta 70. Tarea de purga cifrada por lotes/skip_locked preserva metadatos y está programada cada 60 segundos. PostgreSQL: 3 pruebas correctas en 56,70 segundos (`/tmp/access-coverage-store0103.xml`), perfil/cuenta sintéticos más censo, auditoría antes de transporte, idempotencia, vínculo alterado, versiones/estado conservados y purga idempotente. Ruff/coherencia de migraciones/check/diffcheck correctos. Docker y worker/Beat de 0103 no actualizados ni verificados; no afirmar esa ejecución.

### Criterio de salida y siguiente entrega

El usuario exige evitar concentración innecesaria en un solo punto (2026-10-06). Persistencia/contabilidad interna alcanzan su criterio local con estas pruebas; no ampliar este bloque salvo defecto reproducible o requisito de aceptación concreto. Siguiente: revisión independiente con lectura auditada de copia, decisiones y registros referenciados; aprobación vinculada a cuerpos/autoridad exactos, respuesta final y cierre/descarga. Los ámbitos no proyectados no admiten aprobación por texto genérico: deben vincularse a inventario real del sujeto y decisiones sobre su alcance. Después completar cierres de rectificación, supresión y limitación/oposición conforme a matriz. La aceptación de cada recorrido requiere prueba cruzada; no reabrir piezas verificadas para controles hipotéticos. CR09 y todas las fases posteriores siguen pendientes según contrato original.

## Revisión independiente de contabilidad de acceso — 0104

`RightsAccessCoverageReview` conserva lectura/decisión, huellas de contabilidad/cifrado y épocas de sesión/MFA, con decisión única aprobada/rechazada. `rights_access_coverage_review.inspect/record` exige actor distinto del autor, permisos/lecturas actuales, expediente/prueba/versiones vigentes; registra `access_cover_read` antes de descifrar y reproduce la preparación exacta con las épocas originales del autor. Revisión vincula esa lectura exacta y decisión; rechaza reintentos alterados, lectura ausente, autor y una segunda decisión con otra clave. Inventarios incluyen revisión; censo cuenta 71.

Ruta `rights_access_coverage_review` y lista paginada de borradores ajenos desde expediente; GET privado sin contenidos, POST auditado para comparación de origen autorizado/copia exacta y decisiones. Plantilla ES/EN y CSRF. La decisión es de contabilidad; no acredita por sí sola los registros no proyectados, no emite respuesta ni resuelve acceso. Sigue pendiente validar/consultar los cuerpos de los registros referenciados y el inventario completo de alcance al consumir la aprobación. No usar aprobación contable como sustituto de esas comprobaciones.

Pruebas PostgreSQL de servicios/HTTP/inventario: tres correctas en 65,29 segundos (`/tmp/access-coverage-review-ui0104.xml`), antes de añadir la comparación original/copia. Con comparación y navegación: dos casos actuales perfil/cuenta con HTTP y Chromium móvil ES, correctos en 58,20 segundos (`/tmp/access-coverage-review-csp0104.xml`). Confirman consulta privada, no exposición GET/después de decisión, CSRF/aislamiento del autor, firmas/reintentos, comparación y ausencia de desbordamiento a 390 × 844. No sumar como una única batería ni acreditar Chromium EN con estos casos.

Fallos corregidos: nombre de campo de cifrado incorrecto en migración aún no entregada; test navegaba en inglés buscando botón español; estilos inline bloqueados por CSP, corregidos con clases de CSS servido sin relajar política. La comprobación móvil mide desbordamiento y aporta diagnóstico de elementos si falla. Ruff/check/migraciones/diffcheck correctos.

Runtime Docker local actualizado 0103/0104, app/worker/Beat reconstruidos; 13 archivos coinciden por SHA-256 con host en los tres y CSS servido por Caddy coincide con host tras collectstatic. Salud200, app UID10001, Django check/migratecheck correctos; ambas tareas de purga de acceso registradas. No acreditar destrucción con contenido caducado vía Beat: los casos de purga con contenido se probaron directamente en PostgreSQL. Evidencia acceso-cobertura-revision0104.json.

Criterio de salida de esta entrega satisfecho: revisión de contabilidad e interfaz local verificadas. Continuar con consumo de evidencia/alcance y respuesta/cierre, sin añadir controles hipotéticos a esta pantalla. CR09 y el contrato íntegro permanecen abiertos.

## Consumo de contabilidad y vínculo de respuesta — 0105

`rights_access_reference_bodies.validated_bodies` recupera información exactamente aprobada o páginas revisadas del mismo expediente/exportación. En páginas valida prueba/origen/actor históricos, lectura y firma, ámbito de página, limpieza permitida y firma de cuerpo; en información exige la revisión vinculada y validación histórica realizada por preparación/consumo. La pantalla de cobertura muestra estos cuerpos solo tras consulta auditada. Modificar una página después de aprobar la contabilidad impide consumirla.

`rights_access_coverage_use.consume/validate_approval` registra `access_cover_use` antes de recuperar contenido y revalida firma de preparación, cifrado/transporte/cobertura, referencias/cuerpos, lectura y decisión independientes, pruebas/épocas/permisos actuales y firmas. El validador acepta una instantánea reviewing exacta bajo bloqueos/autorización/auditoría del consumidor; no es endpoint ni autorización de alcance completo.

Migración 0105 añade `RightsAccessResponseDraft.coverage_review` (nullable para borradores parciales anteriores). Preparación y formulario permiten seleccionar contabilidad aprobada; consumo exige misma copia/prueba y liga ID/huellas de decisión/contabilidad a firma del borrador, limitando caducidad. Validador de respuesta revalida ese vínculo; inventarios incluyen el FK. Sin enlace el borrador sigue siendo parcial; esta entrega no introduce emisión/cierre completo de acceso.

PostgreSQL: seis pruebas correctas en 132,16s (`/tmp/access-response-accounting0105.xml`), cuatro combinaciones perfil/cuenta × referencia información/página más dos borradores anteriores; incluyen HTTP de preparación vinculada y Chromium móvil ES de consulta/evidencias en cuatro casos, corrupción de página y reintentos. Regresión adicional de autoridad común: una correcta/3 no seleccionadas en 51,71s (`/tmp/access-accounting-authority0105.xml`), revocación de sesión del revisor y huella de decisión alterada bloquean consumo. No sumar como única batería. Ruff/migraciones/diffcheck correctos.

Docker0105 aplicado, app/worker/Beat reconstruidos: 12 archivos coinciden por SHA-256 con host, check/migratecheck correctos, salud200, UID10001. Evidencia acceso-consumo-respuesta0105.json. No hay nueva aceptación externa/proveedores ni destrucción real con contenido vía Beat.

Criterio de salida de este vínculo alcanzado localmente. Próximo desarrollo: inventario concreto de alcance no proyectado y sus decisiones, consumo de esa validación en emisión/cierre y descarga posterior. No considerar los textos de límites ni la aprobación contable como prueba de entrega de todos los datos. Continuar después con rectificación/supresión/limitación/oposición según matriz y contrato íntegro.

## Inventario de registros y campos de acceso — 0106, componente interno

`rights_access_scope_inventory.source` reutiliza los ámbitos de perfil/cuenta de los inventarios mediante captura opcional, deduplica registros y bloquea filas en PostgreSQL. Cataloga todos los campos concretos, grupos/permisos del titular y blobs del perfil: referencias y huellas por registro/campo, sin valores en el resultado. Normaliza UUID, decimales, fechas y binarios antes de calcular huellas. Los inventarios de supresión mantienen su comportamiento predeterminado. El expediente actual se excluye explícitamente mediante relaciones FK hacia él, para evitar que auditoría/persistencia propias invaliden el origen; esa exclusión queda pendiente de tratamiento en acceso, no se aprueba como omisión.

`rights_access_scope_store.inspect` exige asignación, versiones, permisos/MFA vigentes, lecturas y comprobación de identidad; audita antes de consultar el origen. Migración 0106 conserva inventario cifrado ligado a actor/prueba/épocas y huella; reintento exige contenido y metadatos exactos. Purga por lotes conserva metadatos. Inventarios incorporan el modelo; censo de dependencias 72.

PostgreSQL: 7 pruebas correctas en 91,79 segundos (`/tmp/access-scope-inventory0106.xml`), perfil/cuenta, consulta auditada, reintento estable, huella cambiada por identidad, bloqueo por prueba o inventario alterados, sesión revocada, conservación del estado del expediente, purga idempotente y regresiones de inventario de supresión/censo. Ruff, coherencia de migraciones y diffcheck correctos. Se corrigió serialización UUID detectada por la prueba; los intentos fallidos no cuentan como verificación. Evidencia `acceso-inventario0106.json`.

Criterio interno alcanzado; no ampliar este inventario por hipótesis. Pendientes concretos: interfaz privada, decisiones/entrega por registro/campo, datos del procedimiento actual y recursos fuera de estos ámbitos (sesiones/logs/cachés/colas/backups y registros externos/no enlazados); consumo por respuesta, cierre y descarga de acceso. No hay verificación Docker0106 ni navegador de este componente: runtime permanece0105. No constituye cobertura completa, aceptación CR09 ni aumento porcentual. Tras cerrar el recorrido de acceso, continuar rectificación, supresión y limitación/oposición según contrato.

### Interfaz y runtime del inventario — 0106

Ruta privada `rights_access_scope`, enlazada desde expediente para el actor asignado. GET verifica autoridad/estado y no recupera contenido ni genera auditoría. POST con CSRF, motivo, clave y versiones consulta el servicio auditado; muestra solo huellas/tipos/referencias y pendientes. Paginación de 25 registros (incluye ámbitos vacíos), anterior/siguiente mediante POST conservando clave y motivo: revalida origen/autoridad en cada página sin duplicar auditoría/inventario. No hay valores personales ni aprobación/cierre; GET posterior vuelve a formulario sin inventario. Plantilla ES/EN, no-store y clases compatibles con CSP.

HTTP PostgreSQL: 2 pruebas correctas60,52s (`/tmp/access-scope-ui0106.xml`); batería ampliada, 2 correctas73,51s (`/tmp/access-scope-browser0106.xml`) con Chromium real390×844, ES/EN, perfil/cuenta, formulario, siguiente página, ausencia de desbordamiento, recarga sin contenido, CSRF/navegación y regresiones del servicio. Baterías separadas, no sumarlas como una sola. Docker local0106 aplicado, check/migratecheck correctos, salud200, UID10001 y 12 hashes iguales host/app/worker/Beat. Programación de purga incluida; destrucción con contenido por Beat no acreditada. Evidencia `acceso-inventario-interfaz0106.json`.

Criterio de consulta privada alcanzado. Próximo: decisiones y entrega de datos por registro/campo y tratamiento de ámbitos pendientes; después consumo por emisión/cierre/descarga de acceso. No reabrir esta interfaz salvo defecto reproducible. CR09/contrato completo siguen abiertos.

### Consulta de valores inventariados — lectura tipada

`rights_access_field_read.read` consulta exclusivamente campos explícitos de `core.User`, `listings.Revision` y `listings.Rate`. Mantiene los bloqueos/autorización canónicos, asignación, lecturas, versiones, prueba y épocas; registra `access_field_read` antes de recuperar el inventario original o valores. Reproduce la consulta original firmada, exige referencia única en el ámbito, origen completo inalterado y huella exacta del valor. La clave queda ligada a inventario/modelo/referencia/campo/motivo/autoridad. La captura interna de origen entrega solo el valor solicitado; el manifiesto habitual sigue sin valores. No hay recuperación genérica de ciphertext, credenciales, FK o JSON arbitrario.

La pantalla ofrece botones solo para campos con adaptador, muestra valor tras POST privado y auditado y lo oculta en GET posterior. La consulta no aprueba entrega al solicitante, ni guarda copia del valor ni cierra el derecho. Otros modelos y campos siguen necesitando sus adaptadores/decisiones según naturaleza de datos; no se pueden declarar cubiertos por este lector parcial.

PostgreSQL/HTTP/Chromium: batería final 2 pruebas correctas125,88s (`/tmp/access-field-browser0106.xml`), perfil/cuenta ESEN móvil390×844, navegación/paginación hasta campo email, lectura real por formulario, valor correcto, recarga sin datos y sin desbordamiento; incluye replay, clave usada para otro campo, password rechazado y referencia ajena. Batería anterior 2 correctas90,83s sin lectura de valor por Chromium, separada. Primer intento navegador falló por selector ambiguo entre dos aside; selector específico corregido y recorrido repetido. Ruff/check/migratecheck/diffcheck correctos. Docker appworkerBeat actualizado (sin migración nueva), salud200, 4 hashes igualeshost. No aceptación de cobertura completa/CR09.

Criterio de consulta tipada de estos campos satisfecho. Siguiente: persistir decisiones de inclusión/redacción/omisión vinculadas a lectura/origen, revisión y materialización de suplemento de copia; cubrir ámbitos pendientes y consumir en emisión/cierre. No ampliar lector sin requisito de campo concreto necesario para esa entrega.

## Decisiones de entrega por campo — 0107

`RightsAccessFieldDecision` conserva propuesta cifrada, inventario/lectura auditada originales, acción de preparación, caducidad/purga y revisión independiente con acción/lectura/épocas del revisor. `rights_access_field_decision.propose` reproduce la lectura exacta bajo autorización actual, firma decisión/origen/campo/valor redactado/motivo/versiones/épocas; inclusión usa el valor original, omisión entrega null y redacción textual permite únicamente fragmentos del original más `[redacted]`, eliminando contenido. No permite datos inventados ni redacción que conserva el texto completo. Reintentos deben reproducir todo el cuerpo y las referencias.

Consulta y revisión independientes auditan antes de recuperar contenido, muestran original/copia/motivo y reconstruyen la preparación con épocas originales del autor. Rechazan autor, lectura ajena/ausente, segunda decisión distinta y evidencia/origen alterados o vencidos. `consume` exige actor asignado, aprobación y autoridad vigentes; audita y reproduce revisión/lectura/preparación antes de materializar un campo para una futura copia. No convierte esta aprobación individual en prueba de cobertura completa. GET de revisión no recupera valores.

Frontend/backend conectados: formulario de propuesta desde campo consultado; vista privada de resultado; lista paginada de propuestas ajenas en expediente y revisión privada ES/EN con comparación y decisión. Modelo incluido en inventarios perfil/cuenta (censo73); purga cifrada por lotes conserva metadatos y referencias; Beat programado60s.

Verificación final PostgreSQL: siete pruebas correctas249,69s (`/tmp/access-field-decision0107-final.xml`): perfil/cuenta, tres decisiones, preparación HTTP/replay/lista, consulta/revisión Chromium ESEN390×844, valores original/redactado, recarga sin valor y sin desbordamiento, autor bloqueado/segunda revisión distinta, redacción ajena/sin eliminación rechazadas, consumo de aprobaciones, revocación de sesión del revisor bloquea consumo, purga idempotente y regresiones inventario de supresión/censo. Batería preliminar de tres correctas188,87s no se suma a la final. Ruff/migraciones/diffcheck correctos. Docker0107 aplicado appworkerBeat, check/migratecheck/salud200/UID10001 y 15 hashes iguales host. Evidencia `acceso-decision-campos0107.json`; no acreditar purga con contenido por Beat a partir de programación/hash.

Criterio de propuesta/revisión/consumo individual satisfecho. Pendientes concretos: materializar suplemento agregado y comprobar decisiones de todos los campos/registros requeridos, adaptadores de datos aún no entregados y ámbitos pendientes del inventario (procedimiento actual/recursos externos/no enlazados), vincular esa cobertura completa a emisión/cierre y descarga. No hay cierre de acceso, aceptación CR09 ni cierre del contrato; continuar ese recorrido y después restantes derechos/fases. No ampliar este bloque salvo fallo reproducible o campo requerido por la copia.


## Copia suplementaria materializada — 0107

`rights_access_supplement.prepare` materializa decisiones aprobadas de un único inventario actual. Audita antes de consultar cuerpos, reproduce el inventario original y consume cada aprobación vigente con claves derivadas estables. Exige IDs positivos únicos, misma fuente/referencia/huella de campo y una única decisión por campo; rechaza decisiones contradictorias en vez de elegir silenciosamente una. Devuelve inclusión/redacción con valor aprobado, omisión sin valor, referencias de preparación/revisión/consumo, huella agregada y caducidad mínima. Enumera campos y ámbitos pendientes y conserva `partial` cuando existen; no certifica entrega completa.

Ruta privada para actor asignado, enlazada desde inventario consultado. GET no recupera valores; lista paginada solo IDs aprobados. POST con motivo/versiones/CSRF prepara vista previa ES/EN. No persiste ni entrega este suplemento al solicitante, no emite respuesta ni cierra acceso: esos requisitos quedan dentro del recorrido pendiente. No usar esta vista como descarga final.

PostgreSQL/HTTP/Chromium: dos pruebas correctas291,91s (`/tmp/access-supplement0107.xml`), perfil/cuenta, copia exacta/replay, conflicto de decisiones y booleano rechazados, consulta ajena403, preparación móvil ESEN390×844, GET/recarga sin valores y sin desbordamiento; incluyen flujo previo de tres decisiones/revisión/consumo/revocación/purga. No atribuir esta prueba de un campo agregado a volumen masivo ni cobertura de campos aún sin adaptador. Ruff/check/migratecheck/diffcheck correctos. Docker actualizado en0107 appworkerBeat, salud200 y cinco hashes igualeshost. Evidencia `acceso-suplemento0107.json`.

Corrección de ritmo solicitada por el usuario: hay avance verificable, pero las entregas han sido demasiado fragmentadas y el recorrido de acceso sigue abierto. Priorizar la cobertura exigible y emisión/cierre/descarga de extremo a extremo; no ampliar módulos ya cerrados con controles hipotéticos. La tabla de estado vigente al inicio de este documento prevalece sobre notas históricas provisionales, con alcance y evidencias explícitos para impedir reaperturas innecesarias. CR09 y el contrato completo no están aceptados.

## Cambio de prioridad y preparación independiente —2026-10-08

CR09-REND-LECTURA aplazado hasta petición expresa, sin cierre ni cambios de requisitos/porcentajes/veredictos. Preparación independiente de shell/cuenta ESEN (teclado, acceso, reset, MFA, aceptación actualizada y registro/mensajes) integrada localmentef87951f con comprobaciones PG/Chromium por componente; [seguimiento y evidencia](17-seguimiento-desarrollo.md). No reabren derechos entregados ni aceptan BF/GS01/CR10. Las dependencias y la cola se mantienen exclusivamente en seguimiento17; esta referencia no crea otro roadmap.

Preparación de entrada pública ES/EN integrada localmente4e4e081: reclamación, denuncia y solicitud de derechos, con4 casos PG/Chromium por componente; privacidad/replay/IDs/payload/cifrado/autoridad/plazos conservados. [Cola/evidencias](17-seguimiento-desarrollo.md). No cierre integral de derechos/BF/GS01 ni aumento de porcentajes.

Aclaraciones de recibos privados ES/EN integradas8dddbb1,6 casos PG/Chromium; mínimos distintos, cifrado, versiones, replay, capacidad/caducidad y plazos preservados. [Cola/evidencia](17-seguimiento-desarrollo.md). Preparación de presentación, no aceptación de derechos/BF/GS01 ni nuevos porcentajes.

Consulta auditada ES/EN integrada5a8cb5b con9 casos PG/Chromium y regresiones por cola: GET no descifra, POST motivado audita, recarga oculta datos y revocación bloquea. Sesión sintética real, no ensayo TOTP nuevo. [Seguimiento/evidencia](17-seguimiento-desarrollo.md). Preparación independiente; derechos/fases/porcentajes y rendimiento aplazado conservados.

Preparación independiente adicional0110: acciones triage ES/EN `8b1604f`, [14 casos únicos PG/Chromium y regresiones](evidencias/triage-localizacion-consolidada0110.json); etiquetas/opciones localizadas, motor/autoridad/privacidad/fechas intactos. Casos repartidos entre dos ejecuciones, no N3 común. No aceptación integral, cambios de porcentaje ni cierre GS01/CR09; rendimiento aplazado. Cola única en17.

Preparación independiente0110 de resolución de reclamación ES/EN `643a6b3`: [5PG correctos,2Chromium ES/EN](evidencias/resolucion-reclamacion-localizacion-revisada0110.json), redacción/respuesta mínima/fuente/replay y privacidad conservados. Solo presentación del motor existente, sin aceptación integral/GS01/CR09, runtime normal ni avance porcentual. Cola única17, rendimiento aplazado.

Preparación independiente0110 publicación/moderación ES/EN `e007275`: [6PG correctos,4Chromium ES/EN](evidencias/acciones-anuncios-localizacion-revisada0110.json); etiquetas/opciones, motores y autoridad/lecturas/restricciones intactos. No aceptación integral/GS01/CR09 ni avance porcentual/runtime/performance. Cola única17.

Preparación independiente0110 recursos/revisión ES/EN `c86171c`: [10 únicos correctos PG,2Chromium](evidencias/recursos-localizacion-consolidada0110.json); consumidores foto/agencia y etiqueta de privacidad específica conservados,3ejecuciones/noN3 común. No aceptación integral/GS01/CR09 ni porcentajes/runtime/performance nuevos. Cola única17.

Preparación independiente0110 organización/gestor ES/EN `f4c2dc5`: [7PG correctos,4Chromium](evidencias/revision-organizacion-gestor-localizacion-revisada0110.json), simulación explícita/referencias sintéticas y bloqueos PRODUCTION/autoridad/readiness preservados. No verificación real ni aceptación integral/GS01/CR09, porcentajes/runtime/performance. Cola única17.

Preparación independiente0110 revisión de coincidencias ES/EN `bdeda6e`: [4PG correctos,2Chromium](evidencias/coincidencias-localizacion-revisada0110.json); pares/fotos privadas/permisos/restricciones y motor preservados. No aceptación integral/GS01/CR09, porcentajes/runtime/performance nuevos. Cola única17.

Preparación independiente0110 teléfono ES/EN `31e1fc8`: [4PG correctos,2Chromium](evidencias/telefono-localizacion-revisada0110.json); etiquetas solamente, digest/consumo/autoridad/guards intactos. SMS locmem simulado, no proveedor/entrega real ni aceptación integral/GS01/CR09, porcentajes/runtime/performance. Cola única17.

Preparación independiente0110 autorización/cambio gestor ES/EN `90072c0`: [6PG correctos,4Chromium](evidencias/autorizacion-gestor-localizacion-revisada0110.json); labels solamente, documentos/versiones/autoridad/consumo/replay/retirada preservados. Locmem/sintético, no jurídico/entrega real ni aceptación integral/GS01/CR09, porcentajes/runtime/performance. Cola única17.

Preparación independiente0110 simulador de edad ES/EN `8c9724e`: [3PG correctos,2Chromium](evidencias/simulador-edad-localizacion-revisada0110.json); etiquetas/opciones, simulación explícita y firmas/guards/autoridad/readiness preservados. No edad/identidad real ni aceptación integral/GS01/CR09, porcentajes/runtime/performance. Cola única17.

Preparación independiente0110 alta agencia/editor/persona ES/EN `0bba6a7`: [6PG correctos,4Chromium](evidencias/alta-agencia-persona-localizacion-revisada0110.json); labels, consumidores y roles/MFA/quotas/invitación/revocación preservados. Aviso de sesión propia teardown/retirada independiente revisados. Locmem no proveedor real ni aceptación integral/GS01/CR09, porcentajes/runtime/performance. Cola única17.

Nota local2026-10-08: promoción simulada ES/EN entregada `029ba44`,4PG incluidos2Chromium; [evidencia revisada](evidencias/promocion-simulada-localizacion-revisada0110.json). Preparación UI exclusivamente, sin aceptación CR10/GS01/fases/derechos ni modificación de pesos, dependencias o veredictos. Recursos propios retirados; siguiente requisito concreto y única cola en docs17.

Nota local2026-10-08: administración de catálogo ES/EN `2bede85`,7PG incluidos2Chromium; [revisión](evidencias/catalogo-promocion-localizacion-revisada0110.json). Preparación UI sin aceptación CR10/GS01/fases/derechos, ventas reales ni modificación de pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: conflictos de promoción ES/EN `6937e46`,3PG incluidos2Chromium; [revisión](evidencias/conflictos-promocion-localizacion-revisada0110.json). Intercalado catálogo controlado no prueba de carrera real; preparación UI sin aceptación CR10/GS01/fases/derechos ni modificación de pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: confirmación destino cuenta ES/EN `8843a47`,3PG incluidos2Chromium; [revisión](evidencias/destino-cuenta-localizacion-revisada0110.json). Simulator cifrado no transporte real; preparación UI sin aceptación integral derechos/GS01/fases ni modificación de pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: rechazos upload ES/EN `0883927`,3PG incluidos2Chromium; [revisión](evidencias/upload-localizacion-revisada0110.json). Contador30→31 sin efectos, ingest privado conservado; eager de fixture no worker real. Preparación UI sin aceptación integral ni modificación de pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: edición fotografías rechazos ES/EN `84f662e`,2PG Chromium; [revisión](evidencias/edicion-foto-localizacion-revisada0110.json). Fixtures queued no ingest/worker;400/409/foreign404 sin efectos, operaciones válidas conservadas. Preparación UI sin aceptación integral ni modificación de pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: revisión conservación ES/EN `131d50b`,3PG incluidos2Chromium; [revisión](evidencias/revision-conservacion-localizacion-revisada0110.json). Fecha operativa no extensión/autoridad de borrado; plan/plazo/cuenta intactos. Preparación UI sin aceptación integral ni modificación de pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: seguimiento medidas por finalidad ES/EN `afae3a3`,4PG incluidos2Chromium/login/TOTP local; [revisión](evidencias/seguimiento-finalidad-localizacion-revisada0110.json). Seguimiento no levanta medida/plazo ni autoriza publicación. Preparación UI sin aceptación integral ni modificación de pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: filtros calendario finalidad ES/EN `f93141d`,3PG incluidos2Chromium; [revisión](evidencias/filtros-finalidad-localizacion-revisada0110.json). Sin cambio medidas/plazos/cursor; volumen previo reutilizado. Preparación UI sin aceptación integral ni modificación de pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: rechazos calendarios privados ES/EN `d17d867`,4PG Chromium; [revisión](evidencias/rechazos-calendario-localizacion-revisada0110.json). Sin efectos/privacidad/guards intactos, no repetición volumen/races. Preparación UI sin aceptación integral ni modificación pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: levantamiento comunicado presentación ES/EN `5a15375`,12casos10PGChrome2formsinDB; [revisión](evidencias/levantamiento-localizacion-revisada0110.json). Identidad scoped simulator/recibo local no proveedor/transportereal; wrapper rollback controlado no carrera real. Preparación UI sin aceptación integral ni modificación pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: filtros restricciones expediente ES/EN `509ada0`,3PG incluidos2Chromium; [revisión](evidencias/filtros-expediente-localizacion-revisada0110.json). Default activo/autoridad/COI/orden25/paginación intactos, sin levantar medidas. Preparación UI sin aceptación integral ni modificación pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: excepción finalidad presentación ES/EN `c81a1b2`,6PG incluidos4Chromium; [revisión](evidencias/excepcion-finalidad-localizacion-revisada0110.json). Ámbitos de cuenta/no consumo/medida activa; scopedproof simulator no identidad/decisión jurídica real. Preparación UI sin aceptación integral ni modificación pesos/dependencias/veredictos. Única cola docs17.

Nota local2026-10-08: denegación privada de medidas ES/EN `2a22c8e`,6PG/Chromium únicos entre tres ejecuciones; [consolidación](evidencias/denegacion-medidas-localizacion-consolidada0110.json). Solo guard inicial publicación; cola POST405 preservada. Recursos propios retirados; preparación sin aceptación integral ni cambio pesos/dependencias/veredictos; única cola docs17.

Nota local2026-10-08: presentación planes tratamiento ES/EN `bb6b8b8`,12casos6PGChrome/6forms; [revisión](evidencias/planes-tratamiento-localizacion-revisada0110.json). Finalidades/confirmación/independencia intactas; no nueva prueba carrera/publicación real ni aceptación integral; recursos propios retirados. Pesos/dependencias/veredictos intactos, única cola docs17.

Nota local2026-10-08: mensajes privados planes ES/EN `3656ce2`,2PGChrome403/409 iniciales sin efectos, [revisión](evidencias/rechazos-planes-localizacion-revisada0110.json). Flujos completos válidos reutilizados. Recursos propios retirados; sin aceptación integral/cambio pesos/dependencias/veredictos; única cola docs17.

Nota local2026-10-08: respuestas parciales presentación ES/EN `c2ce621`,8casos4PGChrome/4forms; [revisión](evidencias/respuesta-parcial-localizacion-revisada0110.json). Tipos de ejecución/required/lectura/revisión/emisión/acuse preservados; no aceptación integral de derechos/cambio pesos/dependencias/veredictos. Recursos propios retirados; única cola docs17.

Nota local2026-10-08: denegación privada respuestas parciales ES/EN `8fb3b87`,4PGChrome inicial403 sin efectos; [revisión](evidencias/denegacion-respuesta-parcial-localizacion-revisada0110.json). Flujos completos válidos reutilizados; recursos propios retirados; sin aceptación integral/cambio pesos/dependencias/veredictos, única cola docs17.

Nota local2026-10-08: respuesta/cierre rectificación presentación ES/EN `cabd785`,6casos4PG2Chrome/2forms; [revisión](evidencias/respuesta-rectificacion-localizacion-revisada0110.json). Cierre/perfil no publicado y cuenta sin Person propios preservados; simulador no identidad/transporte real. Recursos propios retirados; sin aceptación integral/cambio pesos/dependencias/veredictos, única cola docs17.

Nota local2026-10-08: denegación respuesta final rectificación ES/EN `7f17802`,2PGChrome inicial403 sin efectos; [revisión](evidencias/denegacion-rectificacion-final-localizacion-revisada0110.json). Flujos completos válidos reutilizados; recursos propios retirados; sin aceptación integral/cambio pesos/dependencias/veredictos, única cola docs17.

Nota local2026-10-08: consulta/propuesta rectificación presentación ES/EN `7fcb7f8`,5PG3Chrome; [revisión](evidencias/propuesta-rectificacion-localizacion-revisada0110.json). Payload/selección/orden/validadores propios intactos, ingest eager no worker real; recursos propios retirados; sin aceptación integral/cambio pesos/dependencias/veredictos, única cola docs17.

Nota local2026-10-08: revisión/comunicación rectificación presentación ES/EN `0f79c10`,6PG únicos4Chrome entre tres versiones de prueba/app igual; [consolidación](evidencias/revision-rectificacion-localizacion-consolidada0110.json). GET vs POSTreload/sourceaudit propios conservados; simuladores no identidad/transportereal/worker. Recursos propios retirados; sin aceptación integral/cambio pesos/dependencias/veredictos, única cola docs17.

Nota local2026-10-08: destinatarios rectificación presentación ESEN `3cb4e96`,4PG únicos2Chrome nativos; [consolidación](evidencias/destinatarios-rectificacion-localizacion-consolidada0110.json). Tokens/formset/raw/independencia/autoridad conservados y legacy compartido; erroresfixture302 preservados. No nueva aceptación BF/GS01/canales reales/porcentajes, recursos propios retirados; única cola docs17.

Nota local2026-10-08: comunicaciones revisadas/inbox presentación ESEN `59be14b`,6PG1Chrome ambas lenguas; [revisión](evidencias/comunicaciones-destinatarios-localizacion-revisada0110.json). Operaciones/targets/raw/GETprivado/autoridad/acuse preservados; avisos internos no entrega externa real. Sin aceptación BF/GS01/cambio pesos/dependencias/veredictos, recursos propios retirados y única cola docs17.

Nota local2026-10-08: inventario acceso/decisión por campo presentación ESEN `b51ed59`,6PG4Chrome ambas lenguas; [revisión](evidencias/inventario-acceso-localizacion-revisada0110.json). Targets/reference64/rawredacted/GETprivado/autoridad/auditoría preservados; sin nueva política jurídica. Sin aceptación BF/GS01/cambio pesos/dependencias/veredictos, recursos propios retirados y única cola docs17.

Nota local2026-10-08: revisión contable acceso presentación ESEN `26f0040`,4PG4Chrome ambas lenguas; [revisión](evidencias/revision-contabilidad-acceso-localizacion-revisada0110.json). Independencia/read_id/cifrado/GETprivado/autoridad/auditoría preservados; aprobación contable no cierre. Sin aceptación BF/GS01/cambio pesos/dependencias/veredictos, recursos propios retirados y única cola docs17.

Nota local2026-10-08: POST400 decisión por campo presentación ESEN `0eb2b19`:defecto BoundField reproducido y4PG4Chrome de regresión, [revisión](evidencias/decision-campo-post400-localizacion-revisada0110.json). Validadores/autoridad/cifrado/GETprivado intactos y no effects; evidencia46 válida reutilizada sin reinterpretar400. Sin aceptación BF/GS01/cambio pesos/veredictos; recursos propios retirados y única cola docs17.

Nota local2026-10-08: copia suplementaria acceso presentación ESEN `e17df87`,6PG4Chrome con parseo/IDs/selecciónaprobada/autoridad/auditoría/GETprivado preservados; [revisión](evidencias/copia-suplementaria-localizacion-revisada0110.json). Preview parcial no emisión/cierre/cobertura completa; recursos propios retirados, sin aceptación BF/GS01/pesos/porcentajes/veredictos, única cola docs17.

Nota local2026-10-08: respuesta final acceso preparación/revisión presentación ESEN `f2fbd2d`,6PG4Chrome; [revisión](evidencias/respuesta-final-acceso-localizacion-revisada0110.json). Modelqueries/IDs/defaults/autoridad/independencia/GETprivado preservados; no emisión/cierre/cobertura integral/aceptación BF/GS01/capacidad. Recursos propios retirados; sin cambio pesos/porcentajes/veredictos, única cola docs17.

Nota local2026-10-08: pantalla cierre acceso ESEN `0089110`,6PG4Chrome:entrada corta400/parcial409/cobertura completa sigue requerida/autoridad403 sin efectos; [revisión](evidencias/cierre-acceso-localizacion-revisada0110.json). Cierre nativo completo histórico reutilizado, no nueva aceptación integral/BF/GS01/capacidad; recursos propios retirados, sin pesos/porcentajes/veredictos nuevos yúnica cola17.

Nota local2026-10-08: respuesta genérica progreso/representación retirada presentación ESEN `45385ae`,6PG4Chrome; [revisión](evidencias/respuesta-derechos-localizacion-revisada0110.json). Kinds/withdrawal/proof/autoridad/cifrado/plazos/GETprivado preservados, issue/funciones ajenas AST idéntico. Autoridad/transporte sintéticos no reales, sin aceptación BF/GS01/porcentajes/veredictos nuevos; recursos propios retirados yúnica cola17.

Nota local2026-10-08: información copia presentación ESEN `485fde9`,8PG6Chrome; [revisión](evidencias/informacion-copia-localizacion-revisada0110.json). Diezapartados/raw/parcialidad/binding/autoridad/privacidad intactos; política sintética no aceptación real, recursos propios retirados, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: evaluación/revisión portabilidad presentación ESEN `c0939a4`,6PG4Chrome; [revisión](evidencias/evaluacion-portabilidad-localizacion-revisada0110.json). Nueve datasets/typedunknowns/raw/defaults/autoridad/privacidad intactos; bases jurídicas sintéticas no aceptación real, recursos propios retirados, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: selección escalar portabilidad presentación ESEN `3680393`,6PG4Chrome; [revisión](evidencias/seleccion-escalar-portabilidad-localizacion-revisada0110.json). Lazy/defaults compartidos/path/token/typedfacts/autoridad/privacidad intactos; selección ydescarga parciales sintéticas no cobertura real, recursos propios retirados, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: revisión selección eimagen auditada presentación ESEN `bf8251f`,6PG4Chrome; [revisión](evidencias/revision-seleccion-portabilidad-localizacion-revisada0110.json). Max200/IDs/defaults/raw/autoridad/privacidad intactos; imagen/selección/descarga sintéticas no transporte real, recursos propios retirados, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: preparación selección imagen portabilidad presentación ESEN `327ebfb`,6PG4Chrome; [revisión](evidencias/preparacion-imagen-portabilidad-localizacion-revisada0110.json). Condiciones/token/bytes/defaults/selección previa/autoridad/privacidad intactos; imagen/selección/descarga sintéticas no transporte real, recursos propios retirados, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: exportación aprobada portabilidad presentación ESEN `cd838c6`,6PG4Chrome; [revisión](evidencias/exportacion-portabilidad-localizacion-revisada0110.json). Partial/cobertura/bindings/lazy/defaults/raw/autoridad/privacidad intactos; cobertura sintética no censo operativo real, recursos propios retirados, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: declaraciones cobertura portabilidad presentación ESEN `607d9c6`,8PG6Chrome; [revisión](evidencias/declaraciones-cobertura-portabilidad-localizacion-revisada0110.json). Exclusiones/allowpartial/path/token/defaults/raw/autoridad/privacidad intactos; declaración sintética parcial no censo operativo real, recursos propios retirados, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: revisión cobertura portabilidad presentación ESEN `6d8162f`,6PG4Chrome; [revisión](evidencias/revision-cobertura-portabilidad-localizacion-revisada0110.json). Requiredpages/gate409/condicionesraw/IDs/defaults/autoridad/privacidad intactos; cobertura sintética no censo operativo real, recursos propios retirados, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: respuesta final portabilidad preparación/revisión presentación ESEN `e635d8a`,6PG4Chrome; [revisión](evidencias/respuesta-final-portabilidad-localizacion-revisada0110.json). Raw/cobertura/IDs/defaultCloseNone/closeAST/autoridad/privacidad intactos; verificaciones ycanales sintéticos no reales, recursos propios retirados pese awarningpytestconservado, sin BF/GS01/porcentajes nuevos; única cola17.

Nota local2026-10-08: cierre portabilidad presentación ESEN `a6ae7d4`,6PG4Chrome; [revisión](evidencias/cierre-portabilidad-localizacion-revisada0110.json). Cierre/replay/autoridad/cifrado/plazos conservados, recursos propios retirados; no aceptación jurídica/canal real/fase ni porcentajes nuevos. Única cola17, rendimiento aplazado.

Nota local2026-10-08: preparación copia acceso auditada ESEN `286081b`,6PG4Chrome; [revisión](evidencias/preparacion-copia-acceso-localizacion-revisada0110.json). JSON/auditoría/revisión/permisos/privacidad/version/plazo conservados; recursos propios retirados. Sin motores/ensayos grandes nuevos ni aceptación jurídica/fase/porcentajes; única cola17.

Nota local2026-10-08: consulta auditada imagen copia acceso ESEN `f26ca4a`,2PG2Chrome; [revisión](evidencias/imagen-copia-acceso-localizacion-revisada0110.json). BytesWebP/auditoría/privacidad/scope/autoridad conservados yrecursos propios retirados; no canal/identidad real/aceptaciónfase ni porcentajes. Única cola17, rendimiento aplazado.

Nota local2026-10-08: errores versión/cobertura compilación copia auditada ESEN `4dbc827`,6PG4Chrome ybaseline reproducido; [revisión](evidencias/errores-operaciones-copia-acceso-localizacion-revisada0110.json). Guard409/cobertura/raw/params/desconocidos preservados, recursos propios retirados; no localización global/fase/porcentajes nuevos. Única cola17.

Nota local2026-10-08: errores consulta paginada/decisiones guardadas copia auditada ESEN `f809e06`,6PG4Chrome/baseline; [revisión](evidencias/errores-paginas-copia-acceso-localizacion-revisada0110.json). Catálogo estático finito/motoresSHA/409/cursor/contabilidad/raw/params/unknown preservados; recursos propios retirados. Sin localización global/aceptaciónfase/porcentajes; única cola17.

Nota local2026-10-08: errores copia revisada entrega ESEN `ece2433`,6PG4Chrome/baseline; [revisión](evidencias/errores-copia-revisada-localizacion-revisada0110.json). Redacción/esquema/identidad/partialidad/409/contabilidad/raw/params/unknown preservados; recursos propios retirados. Sin localización global/fase/porcentajes; única cola17.

Nota local2026-10-08: recuperación foco rechazo ESEN `489d63b`,6PGChromium/12rechazos+8GET ybaseline; [revisión](evidencias/foco-errores-formulario-revisada0110.json). Foco/contorno/tab/ARIA/password/privacidad/version preservados, backend sin cambio yrecursos retirados. No lectorpantalla humano/WCAGlegal/fase/porcentajes; una cola17.

Nota local2026-10-08: asociación etiquetas revisión página `b57d9bc`,6PG4Chrome ybaseline; [revisión](evidencias/etiquetas-revision-pagina-copia-revisada0110.json). Auto_id soloHTML/POSTnames/ARIA/tab/privacidad/cifrado/guardar-replay únicos conservados; recursos propios retirados. Sin fase/WCAGlegal/porcentajes; una cola17.

Nota local2026-10-08: contraste computado shell/formularios `99ddfce`,5PG4Chrome/317pares conformes/39ausencias; [recálculo](evidencias/contraste-shell-formularios-analisis0110.json). Sin cambio producto yrecursos propios retirados; no WCAGglobal/legal/fase/porcentajes ni capacidad. Única cola17.

Nota local2026-10-08: reflujo320/1280CSS y foco fragmento `4ea542b`,10PGChromium/20estados; [revisión](evidencias/reflujo-shell-formularios-revisada0110.json). Sin aceptación integral, porcentajes o capacidad; única cola17.

Nota local2026-10-08: metadatos idioma plantillas `a63ba11`:4PG/1Chromium PASS, sin cambio producto; [revisión](evidencias/metadatos-idioma-plantillas-revisada0110.json). Dominio sintético, no aceptación fase/producción ni porcentajes nuevos; única cola17.
