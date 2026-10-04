# Auditoría de dependencias pendientes de derechos

Revisión técnica 2026-10-04 sobre f5c636c. Fuente: metadatos Django de core/catalog/listings/mediafiles/safety y AST de erasure_inventory.source_manifest. No consulta datos personales. Esta revisión identifica trabajo pendiente; no acepta inventario integral ni supresión completa.

El inventario actual es seleccionado. Sus entradas y huellas cubren recursos operativos concretos y metadatos de evidencias, no todos los campos ni todas las relaciones de la aplicación. La lista de modelos sin etiqueta literal en el AST requiere interpretación: Blob ya se inspecciona en la sección media; catálogos/geografía y LegalDocument son fuentes generales, no quedan automáticamente pendientes de borrar por la solicitud de una persona.

| Dependencia | Cobertura actual | Continuación necesaria |
| --- | --- | --- |
| RightsAccess/Action/Message/ProofEvent | Lecturas/acciones/mensajes y comprobación versionadas; parte de sus efectos entra mediante RightsRequest/proof | Inventario independiente de contenido, metadatos y autores; conservación restringida/redacción por alcance, preservar hechos de autorización sin entregar texto ajeno |
| ComplaintAccess/Resolution/Notice y sus entregas simuladas | Complaint y ComplaintAction referidas incluidas; resolución y outbox implementadas | Cubrir referencias Report y ModerationDecision, motivos/derivados/evidencias y destinatarios sin identificar al denunciante frente a gestores |
| NoticeRecovery/entregas simuladas de denuncias y derechos | Intentos/estado/versiones de outbox incluidos; recuperación auditada | Inventariar historial operativo y conservación restringida, sin borrar acuses o auditorías de terceros por dependencia global |
| RightsExportPreview/Extension | Export/copia descargable/purga y ampliación implementadas | Incluir contenido de vistas previas, fechas/motivos y avisos; diferenciar material transitorio de evidencia preservada |
| ErasureInventory/Plan/Execution | Metadatos y contenidos cifrados creados por el propio procedimiento; sin expurgo general | Política por finalidad y archivo restringido; evitar que crear inventario/plan invalide su propia fuente por incluir recursivamente su registro recién generado |
| MatchResolution | Match/PhotoRestriction/Appeal y huellas seleccionadas | Auditar motivo y revisión independiente asociados a coincidencias propias/compartidas, no extender titularidad a otra persona |
| Agency/Member/Invitation/Review/Appeal | Bandera account_has_other_responsibilities impide borrar cuenta con otras responsabilidades | Revisar ámbito de la persona frente al de una organización y otros modelos; baja/transferencia/responsabilidades/evidencias propias requieren operaciones explícitas |
| RateWindow/sesiones/cache/logs | Cuenta y tokens versionados, logs privados filtrados | Inventario y retención real por almacenamiento; no tratar expiración de enlace o filtro de log como borrado de dato histórico |
| Almacenamiento externo/WAL/backups/réplicas/CDN | Borrado local físico específico verificado; adaptadores externos pendientes | Tombstones duraderos independientes de backup, restauración/conciliación y plazos versionados; ensayos reales separados de simuladores |

No ampliar `source_manifest` sin revisar causalidad y locks: si incluye su propio nuevo ErasureInventory/Plan, la fuente cambia al prepararla y hace imposible ejecutar un plan válido. Separar fuente operativa mutable, expediente de conservación y auditoría del procedimiento; registrar límites explícitos y comprobar cambios intercalados relevantes. El HMAC seleccionado no acredita serialización de todas las relaciones o almacenes.

## Trabajo por derecho que continúa pendiente

- Acceso/portabilidad: inventario completo del alcance comprobado, información adicional conforme a procedimiento, distinción de datos entregables por tipo, originales/metadatos/redacción parcial y paquetes por partes para volúmenes grandes; respuesta final ligada a la entrega real. La copia actual sigue marcada parcial.
- Rectificación: propuesta de corrección por campos/finalidades, revisión y ejecución versionadas, conflicto con datos compartidos y evidencias históricas, aviso minimizado y respuesta final; no sustituir por una cautela de publicación.
- Limitación/oposición: evaluar finalidades y bases por alcance, tratamientos que continúan o se bloquean, conservación/otras operaciones, duración/revisión y respuesta final. Cautela/levantamiento de publicación son componentes verificados, no ejecución integral del derecho.
- Supresión: decisiones por dependencias completas, ejecución/redacción/conservación restringida motivada, conciliación tras restaurar y aviso a destinatarios pertinentes, respuesta final verificable. Cuenta/tokens/copias/contactos/representación/media/contenido ya ejecutados tienen el alcance declarado en docs26–35.
- Reclamaciones: triage de fuentes obsoletas/desconocidas y avisos a personas afectadas; no perder restricciones vigentes al reabrir una revisión.

Mantener CR09 abierto hasta completar sus recorridos y regresión/acta. CR10→GS01→B-F/B-B→C y los gates de producción siguen íntegros. Plazos/bases definitivos y procedimientos/proveedores reales son dependencias externas; mecanismos locales y simuladores no acreditan cumplimiento jurídico completo. Claude3/3; continuar desarrollo local sin nueva delegación.


Acceso/copia — actividad propia de favoritos (en verificación): rights_copy_data.subject_data incorpora account_activity.favorites del User comprobado de person.subject_id, con listing_reference/created_at y sin contenido/contactos/gestor del anuncio ni actividad de agencia u otros usuarios. Sujeto ausente produce lista vacía. Fuente canónica/revisión/digest existentes incluyen este campo, por lo que cambios de favoritos entre preview/generate invalidan revisión; no se permite editar la actividad estructurada. Copia sigue parcial/simulada conforme a alcance actual. Regresión test_rights_copy_scope en curso; no aceptar aún/actualizar Docker ni commit. CR09 y contrato completo abiertos, Claude3/3 sin nuevas llamadas.


Copia de favoritos propios: regresión terminal test_rights_copy_scope5 passed35.88s, exit0. Cubre proyección sujeto/ausencia de sustitución por gestor, contacto compartido, deriva de cuenta/imágenes, nueva deriva de favorito y descarga privada de copia revisada. No suite común completa ni aceptación integral acceso/portabilidad. Ruff/check/makemigrations/diff limpios. Docker app/worker/Beat reconstruidos/recreados sin migración nueva; health200/hash rights_copy_data.py host/contenedor15ad800229539c133ca49ca9d4a68a2cbaa8a3dbc0075647e2997469626e025f coincide. Copia sigue parcial/simulada, sin terceros ni verificación externa real. Claude3/3; CR09 y resto del contrato pendientes.


### Referencias históricas después de rectificar fotografías

La selección de fotografías se puede corregir en una revisión pendiente, con fuente histórica preservada. Esto no equivale a supresión ni determina por sí solo qué actores deben poder consultar referencias históricas. Verificar la ruta genérica `private_photo` del gestor, previsualizaciones de moderación y cada derivado/copia/exportación que conserve una referencia anterior. Establecer disposición motivada por ámbito y finalidad, sin afectar otro perfil que comparta bytes. Incluir futuras cargas de los mismos bytes y conciliación/restauración. El caso permanece abierto mientras estas disposiciones y comunicaciones no estén resueltas.


### Sustitución de fotografías: evidencia parcial

Cargas privadas y descarte lógico implementados con safety0054. Baterías finales separadas: 33 y 8 pruebas pasan con PostgreSQL/Chromium, con solapamiento; no son 41 pruebas de regresión común. Docker y hashes verificados. Registro de dependencias adicional: RightsRectificationPhotoUpload, RightsAction, RightsProof, revisión rights-stage, Photo, Blob, derivados y coincidencias. Caducidad/descarte no borran archivos ni cierran el derecho. Retención física, referencias históricas, reintroducción, comunicaciones y respuesta final pendientes. Claude 3/3; sin delegaciones nuevas. Evidencia: docs/evidencias/rectificacion-cargas-sustitucion.json.
