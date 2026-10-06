# Matriz de ejecución y cierre por derecho — CR09

Referencia histórica inicial:53b9628, workspace limpio al inicio de aquella revisión. Es una matriz técnica para desarrollar los tramos faltantes; no acredita revisión jurídica ni nueva ejecución de pruebas. [Fuentes/funciones/hashes](evidencias/matriz-derechos-fuentes0100.json). Matriz residual global:docs83; ponderación:docs86.

## Estado vigente y componentes cerrados

Actualizado el 2026-10-06. Base de las entregas anteriores: `1c69d12` (0107). Actualización vigente hasta `187b8e6`: acceso y rectificación con recorridos locales; recursos operativos/aceptación integral pendientes. Esta tabla consolida el estado actual y prevalece sobre los estados provisionales de las anotaciones históricas inferiores. «Cerrado localmente» significa criterio del componente satisfecho; no aceptación del derecho completo ni de CR09.

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
| Supresión | Inventario/plan/ejecución por finalidad, medios exclusivos/compartidos y recuperación registrados | Revisión de ejecución y efectos físicos/pendientes/retenciones; respuesta final precisa y cierre por alcance, no cierre total si quedan finalidades sin resolver |
| Limitación | processing_execution y purpose_restrictions: medidas por finalidad, revisión/caducidad y liberación | Respuesta/revisión/cierre tipados para la medida vigente; el cierre del expediente no debe liberar restricciones |
| Oposición | Plan/revisión/ejecución/excepciones motivadas por finalidad | Respuesta/revisión/cierre sobre cada decisión, efecto/excepción y pendientes; no equiparar a limitación ni a una denegación genérica |
| No actuación o actuación parcial | Respuestas progress e inventarios de pendientes | Recorrido motivado con evidencia de alcance y comprobaciones proporcionadas; revisión jurídica externa de motivos. No crear botón genérico denegado para ocultar funciones pendientes |

## Contrato del siguiente flujo: cierre de acceso

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
