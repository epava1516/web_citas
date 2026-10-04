# Copia privada de datos e imágenes — CR-09

Estado: ampliación verificada localmente. No respuesta completa de acceso, portabilidad, supresión ni acreditación jurídica.

## Alcance y esquema

Las nuevas copias usan subject-profile-copy-v2. La cuenta se obtiene exclusivamente de Person.subject; nunca se sustituye por titular de agencia, editor, solicitante o gestor. Incluye username/email/nombre/apellidos/fechas de cuenta/rol/estado activo y hecho de MFA habilitado, sin contraseñas, secretos, tokens, códigos, permisos internos ni versiones de sesión. Aceptaciones legales proyectan documento/versión/idioma/acción/fecha del propio sujeto; omiten terceros y referencias internas de agencia. Representación refleja versiones, estado, revocación y comprobaciones del mismo Person y subject, sin motivos ni revisores.

Alias/revisiones/tarifas/geografía conservan la revisión textual anterior. El teléfono solo se proyecta si coincide con un PhoneClaim verificado del propio sujeto, sin agencia; teléfono de agencia/otro titular se oculta. Telegram se oculta mientras no exista comprobación específica de titularidad. La coincidencia de teléfono es una regla de ámbito técnico; en pruebas la verificación sigue siendo sintética. El inventario incluye todas las fotografías retenidas de revisiones propias, con estado/posición/fechas/dimensiones; no devuelve nombres de archivo, blobs, hashes ni coincidencias con otros perfiles.

La fuente actual debe consultarse mediante preview auditado antes de generar. Cambios de cuenta, aceptaciones, perfil, contacto o inventario invalidan el digest anterior. Identidad de cuenta y teléfono pueden mantenerse o vaciarse para redacción; no se permite introducir otra identidad. Estructura, revisiones y fotografías ajenas se rechazan.

## Revisión y selección de imágenes

POST /moderation/rights/{case}/image/{photo}/ requiere responsable asignado, permiso de revisión/ejecución, MFA actual, lectura completa de aclaraciones y proof vigente de access/portability. La imagen debe pertenecer al único Person del caso. Se sirve exclusivamente WebP derivado saneado y listo, sin originales ni metadatos EXIF. El acceso registra actor/caso/versión/foto/digest de bytes/motivo10–200. GET no entrega imagen.

En el JSON revisado, content_included=true y exclusion_code vacío seleccionan una imagen. Solo puede generarse si el mismo revisor consultó esos bytes con la versión actual del caso. Fotografías no seleccionadas conservan awaiting_review o una exclusión declarada third_party/unavailable. Abrir un recurso no demuestra comprensión, titularidad o revisión humana suficiente. Para ocultar una zona de una imagen se necesita un procedimiento de redacción adicional; esta versión permite excluirla íntegramente, sin transformar una fotografía arbitrariamente.

Los bytes seleccionados se congelan en RightsExportImage cifrado, asociado al artefacto y fotografía. El JSON contiene attachment UUID, sin ruta de almacenamiento ni acceso público. Se bloquean blobs compartidos en orden estable y después fotos; contenido individual limitado10MiB, conjunto64MiB. Un exceso rechaza toda la entrega y exige partición, sin truncar silenciosamente. Contenido faltante/no listo/inválido o auditoría de bytes anterior no autoriza release.

## Entrega y caducidad

La descarga del JSON conserva el endpoint existente. Cada imagen tiene POST /safety/rights/{case}/{secret}/export/{export}/image/{image}/ con CSRF y key UUID. Ambos revalidan proof, último proof/canal/caso/sujeto/gestor/versión/caducidad. Compartir UUID o autenticarse como agencia no sustituye el secreto y ámbito vigentes. La clave de auditoría distingue descarga de JSON y de cada imagen; retry exacto no duplica auditoría.

El acuse privado muestra botones para imágenes revisadas. Los archivos se entregan como attachment WebP con nombre fijo, private/no-store/noindex. La generación no cierra el caso: consume la autorización para ese artefacto y mantiene reviewing. Producción/simulador desactivado impiden descargas. La tarea de purga caducada vacía JSON y todos los snapshots cifrados del mismo artefacto bajo lock del export; no destruye datos de origen, WAL, backups ni resuelve supresión.

## Pendientes para cerrar el derecho

Información adicional exigible de acceso y evaluación separada de portabilidad, cuenta sin Person verificable, datos propios fuera de este perfil, contactos compartidos/titularidad, imagen original y metadatos cuando proceda, redacción parcial de imágenes, copias por partes para grandes volúmenes, respuesta motivada/avisos/cierre, supresión y retención definitiva. partial y pending_review permanecen explícitos. Si todas las imágenes se incluyen o se excluyen declaradamente por datos de terceros, se retira image_content de pending_review; esto no vuelve integral el resto de la respuesta.

No proveedor real de identidad o envío contratado; todo proof actual es simulador identificado. Las pruebas locales no acreditan cumplimiento RGPD/LOPDGDD ni entrega real. Evidencias terminales y errores se registran en docs/18 y el próximo paso en docs/17.

## Evidencia local

Migración safety0030 aplicada;34 pruebas afectadas pasan88.48s con PostgreSQL y Chromium sin skips, incluidos recorrido móvil completo, privacidad/logs CSRF y purga de snapshots mediante tarea local. Los errores de fixtures y su corrección están en docs/18. Esta batería no es regresión comúnCR09 ni entrega real. El ensayo operativo posterior de purga de imágenes con worker/Beat se registra a continuación y por separado en docs/18.


## Ensayo operativo de caducidad de adjuntos

Procedimiento actual en [operación](12-operacion-seguridad.md): launcher con base/cola/worker/Beat aislados. Comprueba tarea real de purga del contenido JSON y WebP cifrado de copias caducadas, repetición sin efectos, copia vigente y filas de origen/auditoría intactas. Fixture sintético: no originales físicos, identidad comprobada ni decisión de derechos. Resultado terminal: worker1/0 en13.208s; Beat automático67.59s, cuatro adjuntos caducados vacíos y cuatro vigentes conservados. Detalles, IDs y cleanup en docs/18; no inferir borrado de origen/backups ni cumplimiento legal.


Integración de copia con favoritos: batería terminal exports/export_retention/copy_scope12 passed79.49s, exit0 PostgreSQL/Chromium; XML /tmp/rights-copy-favorites-integration.xml. Después se detectó carrera de preferencias: Favorite.add bloqueaba User, remove no; source_copy tampoco coordinaba snapshot con escritores. Cambio en verificación: source_copy bloquea sujeto User(no_key=True) dentro de transacción tras locks de perfil/caso y antes de revisiones; remove bloquea User y revalida sesión/activo antes de eliminar solo favorito propio. Regresión nueva exports/copy_scope/favorites en curso; resultado terminal/Docker/commit pendientes. No afirmar resolución de carreras de todos los campos/dependencias. CR09/contrato abiertos, Claude3/3 sin llamadas.


Coordinación de copia/favoritos aceptada localmente en su alcance: batería posterior a corrección13 passed83.21s (exports/copy_scope/favorites), exit0 PostgreSQL/Chromium. Prueba adicional de concurrencia1 passed17.56s: dos conexiones reales; source_copy en transacción mantiene bloqueo User, pg_blocking_pids identifica conexión de snapshot bloqueando POST remove; favorito permanece hasta commit, después remove302 y fila eliminada. No sumar ambas como batería común. Batería anterior12 passed79.49s previa al cambio de locks documentada separada en docs/evidencias/copia-favoritos-integracion.json. Ruff/check/makemigrations/diff limpios. Docker app/worker/Beat reconstruidos/recreados, health200, hashes host/contenedor favorites.py3b9bd76cc41b3e81d964252f5956952a20ed9fd166d477531904cfd44c2fdfaa y rights_exports.pydc57277b2f28a6b3d24e84cd4e51fe3de0b49aa8e1a99480a47488e04a72fda9 coinciden. Sin nueva migración/tasks/schedule. No acredita coherencia de todos los escritores/dependencias ni acceso integral; CR09 y contrato completo pendientes. Claude3/3.


Copia de historial propio de representación (en verificación): representation.history proyecta RepresentationAction únicamente del Person enlazado y su subject_id comprobado, orden fecha/PK, acción/manager_version/tipos de gestor/fecha/documento legal slug-versión-idioma. No entrega IDs de gestores/subject, motivos internos, invitaciones o secretos. Historial de otra persona o de otro sujeto excluido. Cambios propios invalidan preview mediante fuente canónica vigente; campos estructurados inmutables en reviewed_copy. Procedimientos de representación existentes bloquean Person; copia mantiene locks perfil/cuenta. Regresión test_rights_copy_scope en curso, XML /tmp/rights-representation-history.xml. Copia sigue parcial/simulada, antiguos sujetos u otros perfiles requieren evaluación propia; no declarar acceso integral. CR09 y contrato abiertos; Claude3/3.


Historial de representación: batería terminal7 passed46.47s, exit0 PostgreSQL real sin skips. Datos sintéticos de otra persona/mismo sujeto y mismo perfil/otro sujeto quedan excluidos; IDs privados de gestor ausentes; nueva acción propia después de preview rechaza generate; preview fresco genera y descarga JSON con proyección exacta. Incluye pruebas previas de favoritos, cuenta, contacto e imagen y bloqueo concurrente. Evidencia/XML/hash en docs/evidencias/copia-historial-representacion.json. Ruff/diff/check limpios, Docker en actualización. No acepta acceso integral/casos de antiguos sujetos. CR09/resto contrato abiertos; Claude3/3.

Docker historial: app/worker/Beat reconstruidos/recreados, sin migración nueva; health200 y SHA256 rights_copy_data.py host/contenedor c978c7a21d1015f6dd1f6fc89609949eb6bada6ccec46bfa0596cf86fd4e9ca0 coincide. Sin cambio funcional de tasks/schedule.
