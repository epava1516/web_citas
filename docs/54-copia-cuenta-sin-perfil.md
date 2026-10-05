# Copia privada de cuenta sin perfil

Estado: implementación parcial en verificación. Complementa docs/51 y el inventario por finalidad de docs/53; no resuelve acceso/portabilidad integral ni acepta CR-09.

## Fuente y revisión

rights_account_copy.source proyecta exclusivamente User vinculado mediante RightsRequest.account_subject, aceptaciones LegalAcceptance de ese User y Favorite propios. Datos de cuenta: username, correo, nombre/apellidos, rol, fechas de alta/último acceso/verificación, estado activo y MFA habilitado. No se proyectan contraseña/hash, secreto MFA, contador, códigos, tokens, permisos internos ni credenciales.

Favoritos contienen referencia del anuncio y fecha, sin recuperar su contenido privado. Aceptaciones contienen documento/versión/idioma/acción/fecha, sin datos de firmantes ajenos. Ser propietario de agencia no introduce miembros, modelos, documentos organizativos completos ni sus imágenes. Perfil, representación y revisiones son null/null/lista vacía en este ámbito.

Esquema subject-account-copy-v1, request_kind conserva access/portability, partial=true y simulation=true. Permanecen pending_review additional_rights_information, purpose_inventory y other_account_records. Un JSON disponible no resuelve portabilidad íntegra ni habilita cierre genérico.

El mismo formulario de exportación sirve GET sin copia/valores y POST preview con propósito/lectura/autoridad vigentes. Preview registra digest de fuente; generate exige la fuente consultada y admite retirar valores de identidad, sin insertar identidad ajena ni cambiar relaciones o metadatos. Nuevos favoritos/aceptaciones cambian digest; escritores cooperativos con User lock mantienen la fuente hasta commit.

## Snapshot y descarga

Migración0063: RightsExport admite exactamente un ámbito Person/User; account_subject explícito, person y manager_version null para cuenta sola. Históricos conservan ámbito Person, sin inferir cuentas desde gestor. Snapshot cifrado, acción idempotente, prueba, canal/versión y caducidad limitados a la prueba existente. Cuenta no genera adjuntos de perfil. Acuse permanece solicitud abierta, nunca resolución automática.

POST download mantiene secreto de canal, CSRF, clave de descarga, expiración, estado/versión, prueba original y última prueba. Cuenta requiere IDs concordantes y HMAC actual del estado bloqueado de User; cambio de identidad/credenciales invalida descarga. Cabeceras privadas/no-store y nombre de archivo rights-account.json. Ámbito perfil mantiene sus comprobaciones históricas.

purge_expired_exports elimina contenido transitorio y conserva auditoría/ámbito, también para cuenta sola. Su ensayo nuevo todavía no acredita worker/Beat con snapshot de cuenta no vacío; ese alcance operativo permanece pendiente. No elimina originales, backups o WAL ni decide conservación definitiva.

## Pruebas y pendientes

79996 terminal0:10 correctas79,74s PostgreSQL (4 nuevas acceso/portabilidad×visitante/propietario de agencia, exportación de perfil anterior y negativos exclusivos de perfil). Redacción no puede insertar correo del actor, CSRF de descarga requerido, snapshot parcial sin imágenes, cambio de nombre invalida descarga y perfiles gestionados permanecen intactos. Identidad/entrega simuladas, no acreditación humana.

Ampliación en curso /tmp/account-only-copy-retention.xml: consulta HTTP, imagen ajena, fuente favorita cambiada, expiración/purga y copia/retención anteriores. Fuente congelada hasta terminal. No sumar baterías como suite común mayor.

Pendientes: inventario completo por finalidad y demás registros propios, información adicional/redacción de expedientes, distinción de portabilidad según finalidades, lotes grandes, móvil ES/EN y concurrencia observada de cuenta, worker/Beat de snapshot propio y Docker0063. Supresión/conservación/limitación/oposición/respuesta final de cuenta y resto CR09→CR10→GS01→BF/BB→C continúan pendientes.


Ampliación19241 terminal1:4 fallidas/9 correctas94,79s. Consulta HTTP válida devolvía400 aunque fuente/formulario ya mostraban la copia: prepare conservaba status inicial POST400. Corregido status200 únicamente tras preview correcto, manteniendo errores/autoridad/validación. Repetición47178 en curso /tmp/account-only-copy-retention-final.xml sobre fuente corregida; no aceptación hasta terminal. Fallo y resultados originales conservados, sin relajar expectativa HTTP.


47178 terminal0:13 correctas89,19s PostgreSQL sin fallos/omisiones; status200 corregido confirmado. Consulta HTTP con fuente auditada, imagen ajena404 sin auditoría de imagen, favoritos cambiados antes de generate denegados, snapshot caducado purgado1/replay0 y copia/retención previas pasan juntas.

56120 terminal0:3 correctas34,94s, PostgreSQL real: pg_blocking_pids confirma espera User de preview/generate/download. Cambio de MFA antes de liberar deniega preview/download; nuevo favorito deniega generate por digest diferente. No auditoría/copia/descarga adicional ni versión mutada por rechazo.

Probe45794 terminal0: worker purga1/repetición0 en13,947s; Beat automático sin despacho manual,2 caducados vacíos y2 vigentes preservados en67,699s. Fuente User/caso/prueba/acciones/descargas/metadata e imágenes de perfil inexistentes conservadas por digest. Prueba pendiente y entorno identity/notice/correo disabled, no identidad aprobada. Base account_copy_probe_e6294c74c5b7 y contenedores eliminados, pg_database/dockers verifican ausencia. [Evidencia](evidencias/copia-cuenta-worker-beat.json).

Docker0063 aplicada, imágenes reconstruidas/recreadas y check/migrate--check/UID10001/health200 verificados. Hashes exports/account_copy/models coinciden host/app/worker/Beat. Etiquetas de cuenta en pantalla/acuse añadidas después de esta reconstrucción; móvil45717 en curso ESEN, fuente congelada y runtime final de plantillas pendiente. Inventario integral/otros derechos de cuenta y CR09/contrato abiertos.


Móvil45717 terminal1:2 fallidas35,46s, GET sin fuente rendía literal JSON null en campo de copia. Añadido ReviewedCopyField.prepare_value: None se presenta vacío; validación JSON/error/copia real conservados. Repetición66710 en curso /tmp/account-copy-mobile-final.xml ESEN; no declarar móvil aprobado hasta terminal. Última fuente de formulario aún no reconstruida en Docker.


66710 terminal0:2 móvilesESEN correctas39,77s Chromium390x844. Login/MFA reales, GET campo vacío sin datos, POST preview auditado→JSON cuenta comprobado→generate→resultado observado→reload sin correo→acuse anónimo→descarga JSON cuenta parcial→reload, sin overflow en panel/acuse y una auditoría por descarga. ReviewedCopyField elimina null visual inicial sin saltar consulta/validación. Fuente funcional final requiere regresión conjunta y Docker de formulario/plantillas antes de entrega.


Regresión final58410 terminal0:27 correctas196,99s PostgreSQL/Chromium, sin fallos/errores/omisiones; copia de cuenta/HTTP/móvil/concurrencia y copia/imágenes/retención anteriores sobre status200/formulario vacío/plantillas finales. [Evidencia](evidencias/copia-cuenta-regresion.json). Docker final recreado/check/migraciones/UID10001/health200/hashes, [runtime](evidencias/copia-cuenta-runtime.json). No sumar baterías anteriores. Inventario completo, otros registros/información adicional, grandes volúmenes y demás derechos por finalidad siguen pendientes; no aceptación CR09.
