# Dependencias y causalidad del inventario propio de cuenta

Estado: implementación y runtime verificados localmente en baterías10 y4 separadas; prueba adicional de legado correcta por separado. Complementa docs/53 y docs/55; no acepta conservación/supresión integral ni CR09.

## Ámbito y proyección

account-erasure-inventory-v2 amplía el censo seleccionado de14 a31 modelos. Cada recurso conserva modelo/finalidad/recuento/HMAC/disposición review_required. El HMAC usa campos expresamente seleccionados de estado y referencias, sin proyectar filas, identidades ajenas, cuerpos de mensajes/respuestas, motivos privados, secretos o enlaces. Una intervención del usuario no concede propiedad de todo el expediente.

| Recursos incorporados | Ámbito seleccionado | Finalidad |
| --- | --- | --- |
| AgencyInvitation | Agencia de la que la cuenta es propietaria; sin correos ni digest de invitación | organization_responsibilities |
| RightsAccess/Action | Expedientes vinculados a cuenta o solicitados por ella, o intervención como actor; excepción de procedimiento actual | dependent_evidence |
| RightsMessage/Response | Expediente vinculado/solicitado o intervención propia; sin contenido ni razón | third_party_evidence |
| RightsProofEvent | Prueba de cuenta o intervención como verificador; sin razones | dependent_evidence |
| RightsResponseAcknowledgement/Notice/SimulatedRightsNoticeDelivery | Respuesta de expediente vinculado/solicitado; estado de entrega no equivale a entrega real | dependent_evidence |
| RightsExtension/ExportPreview | Expediente propio y, para preview, intervención propia | dependent_evidence |
| RightsExportDownload | Copia de cuenta o actor de descarga; sin token/canal ni contenido | dependent_evidence |
| Complaint/ComplaintMessage | Solicitante/autor explícito; no atribuir anónimos por coincidencias | third_party_evidence |
| ErasureInventory/Plan/Execution anteriores | Referencia propia de cuenta y expediente diferente al actual | dependent_evidence |

Estas categorías son un inventario interno. No se incorporan automáticamente a la copia descargable ni autorizan borrar registros de terceros. Las finalidades se mantienen dentro del catálogo ya existente, sin crear operaciones ejecutables nuevas.

## Causalidad y versiones

RightsAction del expediente actual excluye únicamente erasure_inventory/erasure_plan/erasure_execute. ErasureInventory/Plan/Execution de ese mismo expediente se excluyen de la fuente mutable. Preparar o registrar plan debe conservar su digest; los artefactos excluidos requieren conservación auditada propia y figuran en pending como current_procedure_audit_excluded. Acciones no procedimentales, lecturas, mensajes o respuestas pertinentes sí cambian el estado seleccionado y exigen preparar/revisar de nuevo.

Los snapshots anteriores v1 permanecen cifrados e inmutables. Compararlos con una fuente v2 produce Resources changed; no migrar ni reescribir su digest silenciosamente. Preparar un inventario nuevo con otra clave y revisar sus finalidades. El replay exacto de una ejecución ya realizada conserva el resultado original conforme a su contrato.

## Límites y verificación

Siguen pendientes otras relaciones organizativas/editoriales y de reclamación, contenidos/evidencias protegidos, sesiones/registros/cache/backups y tombstones/restauración. No identificar usuarios a partir de correos o textos coincidentes. Cuenta ya suprimida no adquiere nueva autoridad viva por conservar su FK de expediente.

Batería58613 en curso10 pruebas de inventario/ejecución/carreras propias sobre v2, XML /tmp/account-inventory-dependencies.xml. Prueba nueva de causalidad/redacción de metadatos preparada en tests/test_account_inventory_dependencies.py, todavía no ejecutada. Docker normal sigue entrega5d9110f/v1; reconstrucción y verificación pendientes. No aceptar antes del resultado terminal y actualización de runtime.

58613 terminal0:10 propias correctas80,04s, cero fallos/errores/omisiones PostgreSQL, XML /tmp/account-inventory-dependencies.xml. Incluye inventario/ejecución/carreras de cuenta sobre v2 sin invalidación circular.97846 activa4 de causalidad/dependencias, móvil ESEN e aislamiento de copia ajena, /tmp/account-inventory-v2-boundaries.xml; fuente congelada. Build31431 en curso; no runtimev2 aceptado.

97846 terminal0:4 correctas58,91s, cero fallos/errores/omisiones PostgreSQL/Chromium. Causalidad/dependencias, ESEN móvil e aislamiento de copia ajena pasan sobre v2. No sumar con10 anteriores como suite14; evidencia inventario-cuenta-v2-regresion.json. Build31431/recreate20891/runtime59616 terminal0:14 hashes iguales host/app/worker/Beat,31 modelos únicos, UID10001/health200/CSS servido/check/migrate--check y backends disabled. Sin migración nueva; evidencia inventario-cuenta-v2-runtime.json.3973 activa prueba dirigida de legado: snapshotv1 sintético permanece cifrado/inmutable y plan exige inventario/revisión nuevos, /tmp/account-inventory-v2-legacy.xml.

3973 terminal0:1 legado correcto25,97s PostgreSQL, cero fallos/errores/omisiones. Fixture de snapshotv1 conserva ciphertext/digest tras denegación de plan con fuentev2; preparación nueva con clave nueva permite revisión y no modifica cuenta. Evidencia añadida como batería separada, no sumar como suite15. Sin pytest activo; calidad/runtime verificados. Conservación integral y demás CR09/contrato siguen pendientes.
