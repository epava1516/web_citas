# Matriz de ejecución y cierre por derecho — CR09

Corte de código:53b9628, workspace limpio al inicio de esta revisión. Es una matriz técnica para desarrollar los tramos faltantes; no acredita revisión jurídica ni nueva ejecución de pruebas. [Fuentes/funciones/hashes](evidencias/matriz-derechos-fuentes0100.json). Matriz residual global:docs83; ponderación:docs86.

## Recorridos y aceptación

| Derecho | Evidencia de implementación existente | Tramo todavía necesario |
| --- | --- | --- |
| Representación | rights_responses.issue(representation_complete), RightsWithdrawal y prueba/gestor/consentimiento/publicación concordantes | Integrar en regresión final, comunicación/conservación; no convertir retirada de representación en supresión integral |
| Portabilidad | rights_portability_close.close, borrador/revisión independiente/entrega y cobertura aprobadas; descarga privada ligada al cierre | Variantes/rendimiento/comunicación y aceptación integral; conservar diferencias con acceso |
| Acceso | Información/copia preparadas y revisadas; rights_information_export liga información aprobada a exportación privada | **Siguiente desarrollo:** respuesta final y revisión independiente ligadas a información, copia y cobertura vigentes; cierre tipado y descarga posterior bajo esa autoridad |
| Rectificación de perfil | Propuesta/revisión/comunicación previa/acuse/ejecución y respuesta progress; avisos gestores, inventario y evaluación de destinatarios | Respuesta final independiente sobre cambios exactos y pendientes; cierre tras justificar alcance/destinatarios, sin afirmar publicación automática |
| Rectificación de cuenta | Propuesta/revisión/confirmación de destino/acuse/ejecución sin crear perfil | Completar recorrido de destinatarios para cuentas sin perfil y cierre tipado; no reutilizar consultas que exigen person |
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
