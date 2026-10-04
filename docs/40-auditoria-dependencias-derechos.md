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


### Próximo recorrido: retirada física de cargas preparadas

Inspección del código tras 7f00034: `MediaErasure` exige una `ErasureExecution` y supone borrado jurídico con estado terminal `erased`; no debe usarse directamente como caducidad técnica de preparación. La ingestión rechaza `erased`, por lo que reutilizar ese estado impondría una prohibición permanente injustificada a una carga descartada. Se requiere distinguir eliminación de preparación y supresión jurídica, con trabajo durable y reintentos, comprobación de referencias compartidas bajo bloqueo y semántica explícita de una futura carga legítima.

El inventario de supresión incluye Photo y Revision, pero no incorpora aún explícitamente RightsRectificationPhotoUpload. Añadir esa relación y sus dependencias al inventario antes de afirmar cobertura. Casos obligatorios para la próxima entrega: archivo exclusivo descartado/caducado, archivo compartido con anuncio normal o corrección aplicada, carga elegible en otro expediente, fallo parcial de almacenamiento, reintento y carrera con nueva referencia. No eliminar archivos compartidos ni evidencia necesaria por el mero vencimiento técnico del enlace.


### Limpieza de preparación: aceptación local parcial

Implementada limpieza técnica durable con mediafiles0010 y referencias de carga/trabajo incorporadas al inventario seleccionado. 35 pruebas finales correctas en 329.86s; anteriores 20/33 se solapan. Docker/migración/hashes/UID10001/health200 verificados; transporte real de tarea vacía y borrado local en pruebas diferenciados. CI histórica 7f00034:517 correctas1049.74s, no incluye limpieza. Documentación: docs/44-conservacion-cargas-preparadas.md; evidencia: docs/evidencias/conservacion-cargas-preparadas.json. Se mantienen retención final de evidencias/metadatos, acceso histórico/reintroducción, cuenta, comunicaciones/cierre y contrato completo pendientes. Claude3/3; sin invocaciones nuevas.


### Acceso ordinario al historial: aceptación parcial

Centralizada restricción del gestor para versiones anteriores a rectificación y prevención de copia automática; nueva corrección y otros perfiles no bloqueados. Lectura privada revalida referencia tras locks.43 finales correctas286.11s PG/Chromium; 37 anteriores no sumables. Navegación/reclamación agencia8 correctas33.50s separadas; no regresión común. Docker/hashes/check/migraciones/ruff/diff/UID10001/health200 verificados, sin migración nueva. CI fdc3a49 termina527 correctas1073.80s, anterior a este cambio; a36eca3 falla1/516 correctas1487.26s en reload de agencia, evidencia conservada. docs/45 y evidencias/acceso-historico-rectificacion.json. Recarga manual/variaciones/rehabilitación, colas generales/históricos, retención, cuenta/comunicaciones/cierre y resto contrato pendientes. Claude3/3; sin invocaciones nuevas.


### Historial en colas generales: entrega en verificación

Clasificación SQL central compartida; candidatos y colas ordinarias excluyen historial/preparación. decide/resolve revalidan tras locks; lecturas recargan Photo antes de abrir bytes. Concurrencia3 correctas39.36s; batería45 anterior322.529s sin fallos, no cubre última guarda. Batería47 sesión46996 pendiente, Docker reconstruido/recreación64463 pendiente. No acepta CR09 ni retención/reintroducción/rehabilitación. [Detalle](46-historial-colas-generales.md). Claude3/3; sin delegaciones. Contrato íntegro abierto.


### Historial en colas generales: verificación local parcial

47 pruebas conjuntas correctas328.40s PG/Chromium, cero fallos/errores/omisiones. Refuerzo posterior6 correctas110.68s con Submission válida (5 casos excluidos explícitamente por selección); no sumar baterías. Concurrencia3 correctas39.36s solapada con47. Docker reconstruido/recreado, hashes actuales iguales, UID10001/check/health200, ruff/format/makemigrations/diff limpios; sin migración nueva. CI anterior e7d0679:528 correctas1292.39s. Disposiciones de recarga/rehabilitación docs47 todavía diseño, no implementadas. Conservación por finalidad/cuenta/comunicaciones/cierre y contrato entero pendientes. Claude3/3; sin delegaciones.


Registro de disposición verificado localmente:30 correctas318.44s en batería conjunta PG/Chromium; prueba SQL independiente1 correcta19.73s, con ledgers sintéticos (no prueba de aprobación humana). Primera invocación de esa prueba falló por fixture sin revisión aprobada; corregida usando revisión existente. Snapshot conserva selección por Blob y no depende del borrador mutable. Autoridad por archivo/persona y desempate temporal verificados. safety0055 aplicada, Docker/hashes/check/health200 verificados; detector/revisión/rehabilitación/exportación/retención final siguen pendientes. Claude3/3; contrato entero abierto.


Candidatos de recarga verificados localmente en su alcance:13 correctas82.36s PG, sin fallos/errores/omisiones. Anterior8 correctas40.94s corresponde a versión sin uploaded_blob; no sumar. Detector privado registra exactos y candidatos regionales por perfil/archivo retirado, con vínculo protegido a bytes detectados e idempotencia; no declara igualdad visual ni autorización. safety0056 aplicada; Docker reconstruido/recreado, hashes iguales/UID10001/check sin incidencias/health200. Revisión auditada, decisión independiente, bloqueo central de publicación, UI ES/EN, concurrencia y exportación/retención pendientes (docs48). Claude3/3; contrato completo abierto.


### Revisión privada de recargas: verificación local parcial

Consulta auditada, decisión independiente versionada/cifrada, UI móvil ES/EN y bloqueo central de publicación implementados con safety0057.49 conjuntas correctas419,13 s antes del refuerzo de autoridad;7 finales afectadas correctas75,37 s después, no sumar. Carrera nueva reprodujo lectura admitida tras cambio proof durante espera (1 fallida23,63 s); corregida reconsulta después de locks y verificada denegación sin lectura durable. Retirada real local durante lectura y dos decisores sobre una versión también cubiertos. Docker/check/migraciones/UID10001/health200/hashes verificados, normalización de formato sin cambio semántico requiere última reconstrucción. Identidad y autoridad humanas siguen simuladas en pruebas, no proveedores reales. [Detalle](48-revision-privada-recargas.md) y [evidencia](evidencias/revision-privada-recargas.json). Exportación integral, retención/legado, cuenta/comunicaciones/cierre y resto contrato pendientes; CR09 abierto, Claude3/3.
