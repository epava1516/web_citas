# Recarga de imágenes tras rectificación

Continuación de CR-09. Disposición persistente en implementación y pruebas; detección de recarga y rehabilitación todavía pendientes. No acredita bloqueo de recarga o rehabilitación.

## Problema observado

La exclusión de fotos históricas de las coincidencias ordinarias evita revelar evidencia de derechos y bloquear perfiles ajenos, pero también permite que el mismo gestor recargue bytes de una foto retirada. Inferir la selección autorizada de las fotos actuales de corrected_revision sería incorrecto: esa revisión puede editarse después. La disposición debe quedar vinculada a la ejecución revisada e inmutable.

## Disposición persistente

Registrar al ejecutar una rectificación de fotos la selección y exclusiones por persona, ejecución, Photo fuente y Blob, bajo los mismos bloqueos. Debe distinguir conservar, retirar y sustitución, sin convertir la retirada de una persona en una prohibición global del archivo. Referencias y firmas son datos privados; no devolver identificadores del expediente, SHA ni explicaciones ajenas al cargador.

La selección aprobada permanece inmutable aunque se reordene o elimine el borrador corregido. Ejecuciones posteriores invalidan autorizaciones anteriores cuando cambian la disposición. Incluir las nuevas disposiciones y revisiones en erasure_inventory.source_manifest, exportaciones seleccionadas y huellas de lectura: cambios de autoridad invalidan planes anteriores. Versionar y mantener trazabilidad de la decisión; no usar una marca mutable en la revisión como única autoridad.

### Contrato de datos propuesto

Disposición: execution (FK protegida), source_photo (FK protegida), blob (FK protegida), outcome (retained/withdrawn), fecha y unicidad ejecución/foto. La persona deriva de la propuesta ejecutada. Comparar por Blob para no interpretar una sustitución autorizada con los mismos bytes como retirada. Registrar originales activos y fotos preparadas seleccionadas; excluir del bloqueo aquellas explícitamente conservadas.

La autoridad vigente se determina por persona y Blob: una retirada sigue vigente hasta una decisión posterior explícita sobre ese archivo o una rehabilitación revisada. Una corrección posterior de otras fotos, alias o tarifas no borra la retirada anterior. Las ejecuciones antiguas sin disposición normalizada exigen revisión explícita antes de emitir autorización de rehabilitación.

## Detección y publicación

La recarga exacta del mismo perfil se compara con disposiciones retiradas vigentes. Recompresión y recorte usan firmas y confirmación visual existentes para abrir revisión, sin asumir igualdad jurídica. Aceptar la carga para observación y moderación; impedir publicación mientras una coincidencia protegida esté pendiente. No suspender automáticamente la cuenta ni rechazar globalmente bytes compartidos.

Separar estas coincidencias privadas de Match ordinario: la cola general no debe recuperar por este camino fotos históricas ni evidencia del expediente. El aviso al gestor muestra solo que la imagen necesita revisión. La consulta de la evidencia requiere permiso específico, MFA, motivo, ámbito y auditoría antes de bytes. Independencia respecto del gestor/sujeto/agencia y decisor previo cuando corresponda.

## Rehabilitación independiente

Resultados motivados: mantener retirada, falso positivo visual o autorizar uso actual dentro del ámbito revisado. La autorización se liga a persona, foto cargada/Blob, disposición y versión vigente. No resuelve coincidencias de otros perfiles ni aprueba automáticamente el anuncio. Nueva ejecución o cambio de recurso exige revisión actual, sin reutilizar autorizaciones obsoletas.

Idempotencia, bloqueo canónico y comprobación de versiones impiden carreras entre publicación, retirada y rehabilitación. Rechazos y permisos deben verificarse en HTTP y servicio. Los archivos compartidos permanecen disponibles para otros perfiles autorizados.

## Integración y comprobación requerida

Integrar ingestión/procesamiento, validador central de publicación, envío/aprobación, estado del editor ES/EN, cola y consulta auditada, decisión independiente, exportaciones/inventarios y conservación. Diseñar migración sin inferir disposiciones antiguas desde borradores editables: reconstrucción auditada o revisión explícita de casos anteriores.

Pruebas necesarias: bytes idénticos del mismo perfil; recompresión y recorte; imagen diferente; archivo compartido legítimo; edición posterior de la corrección; segunda rectificación; ausencia de autoridad histórica; dos revisores concurrentes; publicación durante revisión; retirada mientras se leen bytes; permisos/MFA/conflictos; caducidad/retención y reintento de worker. PostgreSQL obligatorio, imágenes sintéticas y navegador ES/EN. La similitud visual exige medir falsos positivos y conservar revisión humana.

No modificar el objetivo completo: quedan identidad de cuenta, comunicaciones/cierre, otros derechos, retención y las fases CR10/GS01/BF/BB/C.

## Implementación de disposición en curso

Modelo RightsRectificationPhotoDisposition y migración safety0055. execute registra originales activos y preparados seleccionados en la misma transacción que la ejecución, comparando Blob para retained/withdrawn. No escribe disposiciones si no se rectificaron fotos. No rellena ejecuciones antiguas desde borradores editables. erasure_inventory incluye IDs/estado/fecha como dependent_evidence. No añade consulta pública ni descifra propuesta en ingestión.

Batería75900/XML /tmp/rectification-photo-dispositions.xml en curso, seis variantes reales de ejecución con PostgreSQL. Verifica selección/exclusión, incorporación al inventario y que reordenar el borrador no modifica disposiciones. Modelo y migración todavía no aplicados al runtime Docker. Pendientes: detector protegido, bloqueo central mientras revisión, cola/lectura auditada/rehabilitación independiente, interfaz ES/EN, exportación/retención y pruebas del recorrido completo. No presentar este registro aislado como protección de recarga terminada.

Primera batería75900 terminal0:6 correctas106.70s,5 casos excluidos explícitamente; prueba snapshot/inventario/reordenación, sin detector. Añadida consulta SQL active_withdrawals por persona/Blob, excluyendo decisión posterior del mismo archivo; evita que una corrección ajena borre la retirada. Limpieza técnica conserva blobs referenciados por disposiciones como rectification_evidence (conservación final aún pendiente). Batería ampliada6241/XML /tmp/photo-dispositions-inventory-cleanup.xml en curso; fuente funcional congelada. Build Docker iniciado, migración runtime pendiente. [Evidencia](evidencias/disposicion-fotografias.json).

Runtime actual: build/recreación terminales0, safety0055 aplicada en PostgreSQL local, hashes disposition/execute/cleanup iguales entre host y app, check sin incidencias y health200. Batería30 casos6241 aún en curso; la aceptación funcional ampliada sigue pendiente.

Preparada prueba SQL independiente tests/test_photo_disposition_authority.py con ledgers sintéticos persistidos, no autorización humana: decisiones explícitas posteriores por archivo, otro archivo sin cambios, otro perfil compartiendo bytes y desempate temporal. Ejecutarla después de la batería6241 para evitar ejecuciones simultáneas sobre la base de pruebas. No afirmar verificada todavía.

Batería ampliada6241 terminal0:30 correctas318.44s, cero fallos/errores/omisiones. Prueba SQL de autoridad69038 en ejecución/XML /tmp/photo-disposition-authority.xml; no ejecutarla simultáneamente ni reiniciar por observación expirada. Confirmar resultado y completar contrato/evidencia/commit antes de detector/revisión.


Registro de disposición verificado localmente:30 correctas318.44s en batería conjunta PG/Chromium; prueba SQL independiente1 correcta19.73s, con ledgers sintéticos (no prueba de aprobación humana). Primera invocación de esa prueba falló por fixture sin revisión aprobada; corregida usando revisión existente. Snapshot conserva selección por Blob y no depende del borrador mutable. Autoridad por archivo/persona y desempate temporal verificados. safety0055 aplicada, Docker/hashes/check/health200 verificados; detector/revisión/rehabilitación/exportación/retención final siguen pendientes. Claude3/3; contrato entero abierto.
