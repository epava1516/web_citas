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
