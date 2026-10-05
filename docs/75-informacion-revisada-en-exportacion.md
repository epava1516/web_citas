# Información revisada en exportación privada

Estado: diseño pendiente de implementación. Continúa docs73–74 y el contrato CR09 completo.

## Selección y ámbito

Añadir una operación guiada de generación que seleccione explícitamente una decisión independiente approved de información de acceso. No modificar silenciosamente la generación parcial existente ni suponer que cualquier borrador guardado está aprobado. El cliente envía referencias, versión, clave y motivo; nunca un cuerpo que pueda sustituir información validada.

La decisión debe corresponder al expediente, sujeto, tipo access, fuente vigente y última versión aplicable del borrador; exigir prueba vigente y misma política. Verificar la firma del guardado, lectura del revisor y decisión, incluidos actores independientes, versión del expediente, huellas y relación de consulta. Revalidar permisos actuales del responsable que genera y ausencia de conflicto. Una aprobación registrada no es autorización permanente del generador.

El formato incorpora additional_information con los diez apartados revisados y referencia de política por versión/idioma/huella; referencias internas de actor, motivo, lecturas y decisiones permanecen en evidencia privada. Copia parcial y simulation permanecen verdaderos mientras falten otros conjuntos o comprobaciones reales. Retirar additional_rights_information de pending_review solo después de incluir el documento completo validado; no retirar shared_contacts u otros pendientes por ese motivo. Portabilidad mantiene recorrido separado hasta implementar elegibilidad por conjuntos.

## Persistencia y consumo de prueba

Vincular RightsExport a la decisión exacta, fuente y huellas mediante evidencia persistente PROTECT. No incorporar las nuevas referencias a una exportación anterior por rellenado retrospectivo. Reintento exacto devuelve solo esa exportación aún vigente, sin consumir prueba ni duplicar archivos. Conflictos o cambios revierten generación, paquetes y consumo de prueba conjuntamente.

La generación existente incrementa case.version y deja scope_status unverified. Validar las firmas de información con la versión original del expediente que consta en export.action.expected_version; no reescribir esa evidencia para coincidir con la versión incrementada. La descarga usa el vínculo comprobado de exportación/prueba/versiones original y resultante, sin volver a autorizar una operación de generación con prueba consumida. Una excepción de versión interna para este consumo necesita prueba específica y nunca un parámetro público libre.

## Descarga y caducidad

Además de las comprobaciones existentes de canal/sujeto/prueba/caso, comprobar que la decisión/consulta/borrador/política siguen íntegros y no purgados/caducados. Un cambio o retirada de política impide descarga y exige nueva revisión; no regenerar contenidos sobre la marcha. Toda respuesta fallida revierte la auditoría de descarga y no entrega bytes.

La caducidad de exportación no supera borrador, consulta efectiva ni prueba. Los cuerpos completos y ZIP/fragmentos mayores deben conservar la misma vinculación; el manifiesto debe explicar los pendientes sin simular que contiene el JSON original completo. La purga de borrador invalida la exportación vinculada aunque su ciphertext siga presente; la política de retención posterior de metadatos continúa pendiente de aprobación operativa.

## Recorrido y verificación

Formulario guiado desde preparación de copia, información aprobada visible solo tras consulta auditada y guardado de generación devuelve metadatos. Probar perfil/cuenta, idiomas/móvil, redacciones e imágenes/paquetes, autor y gestor excluidos, decisiones y referencias ajenas, último borrador pendiente, firmas o vínculos alterados, política cambiada, prueba consumida/revocada, replay tras incremento del caso y descarga anónima por canal privado.

Pruebas PostgreSQL con espera observada en generación y descarga para cambios de fuente/prueba/política/decisión/caducidad. Verificar rollback sin archivos o acciones parciales. Ejecutar regresión común con generación por páginas y exportación existente sobre el mismo código. Ninguna de estas pruebas sustituye acceso integral, respuesta final, comunicaciones, conservación/restauración o aceptación completa de CR09.


## Contrato de transporte previsto

Modelo de vínculo de exportación: OneToOne PROTECT a RightsExport, FK PROTECT a decisión de información, fuente y huellas de borrador/política/lectura/decisión. Su finalidad es revalidar entrega; no incluye motivos ni cuerpo duplicado. Añadirlo al inventario de perfil y cuenta, probar dependencias presentes y exclusión del procedimiento actual. Las exportaciones anteriores carecen de vínculo y permanecen parciales.

Operación propuesta generate_pages_with_information: reason10–2000, key UUID, version del expediente e information_review_id positivo. Reutiliza compilación de páginas revisadas y generación de redacciones/imágenes; selección de información solo por referencia validada en servidor. Introducirla mediante mini flujo cruzado con contrato de formulario, estados y prueba navegador; no convertirla en un argumento libre copy ni rebajar la revisión de páginas para facilitar el test.

Los paquetes mayores de8MiB se reconstruyen por fragmentos conforme a rights-data-manifest-v1. El manifiesto transporta referencias públicas de política únicamente si forman parte del documento autorizado; no arrastra IDs internos de auditoría. Tanto JSON principal como descargas de imágenes/partes deben pasar la misma revalidación del vínculo. No afirmar memoria acotada del recorrido completo: la fuente y copia compilada todavía se materializan completas.
