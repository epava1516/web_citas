# Inventario previo a supresión y conservación

REQ-CR09-ERASURE-INVENTORY-01. Estado: preparación local verificada; no ejecución de supresión ni cierre de derecho. Vincula contratos/10 y docs/25. Adaptador de identidad exclusivamente simulado, inhabilitado en producción.

## Fundamento y alcance

La [AEPD, derecho de supresión](https://www.aepd.es/derechos-y-deberes/conoce-tus-derechos/derecho-de-supresion-al-olvido), consultada el 2026-10-04, explica los supuestos de supresión y sus excepciones, incluida la conservación necesaria para reclamaciones. La existencia de una FK PROTECT es una condición técnica: no acredita obligación legal de conservar todo su contenido ni plazo indefinido. Una solicitud tampoco autoriza a destruir datos de otras personas. Fundamentos, plazos y minimización precisan revisión por finalidad; no se derivan de una tabla o casilla.

El inventario prepara esa revisión: recoge recursos vinculados a Person y a su propia cuenta de sujeto, identifica referencias compartidas y separa publicación, cuenta, autenticación, representación, archivos, copias transitorias y evidencias. Todas las disposiciones son review_required y execution_ready=false. No se ejecuta borrado, revocación, anonimización, retención definitiva, levantamiento o resolución.

## Recursos y dependencias

| Ámbito | Recursos examinados | Condición para ejecución posterior |
| --- | --- | --- |
| Perfil/publicación | Person, Listing, todas sus Revision/Rate y relaciones categorías/servicios/desplazamientos | Retirada de exposición, borrar/redactar campos y relaciones según alcance; revisiones históricas no quedan exentas automáticamente |
| Fotografías | Photo propias y Blob referenciados, coincidencias/restricciones/recursos | Referencia externa impide destruir Blob compartido; conservar o redactar evidencia solo con motivo/plazo revisados |
| Teléfono/representación | Estado HMAC y uso compartido de PhoneClaim, PhoneChallenge, invitaciones, autorizaciones y verificación | Desvincular perfil propio; no eliminar teléfono de agencia usado por otro modelo; revisar contenido y finalidad históricos |
| Cuenta propia | User de Person.subject, tokens, recovery codes, favoritos y aceptaciones propios | Nunca usar cuenta del gestor como sustituta. Responsabilidades de agencia/equipo/staff u otro perfil exigen tratamiento separado |
| Decisiones/expedientes | Decisiones/recursos, denuncias vinculadas, solicitudes de derechos y determinadas dependencias de avisos/copia/auditoría | No exponer ni borrar mensajes/intake de terceros por supresión del modelo; revisar redacción, base y retención de cada dependencia |
| Fuera del inventario inicial | Sesiones/logs/RateWindow/caché/CDN/backups, recursos huérfanos y dependencias no enumeradas | Inventario ampliado, revocación, política y reconciliación/restore-tombstones antes de declarar ejecución integral |

La selección de registros es explícita y documentada en source_manifest. No recorre libremente la agencia ni las FK de actores/revisores para atribuir sus cuentas al sujeto. Fotos compartidas y responsabilidades adicionales se expresan como booleanos, sin identidades ni referencias de otras personas. El inventario no determina quién posee una imagen.

Se generan HMAC de estado de los registros seleccionados y de metadatos de Blob, sin incluir los valores originales en el manifiesto. Cuenta: whitelist sin contraseña, MFA secret, códigos ni tokens. Expedientes: metadatos/versión, sin descifrar intake o razones de terceros. La comprobación del PhoneClaim propio aporta estado HMAC sin publicar el número, incluso cuando su referencia es compartida. Revisiones/fotos propias aportan estado al digest; categorías/servicios/desplazamientos están incluidos. No se inspeccionan bytes físicos de originales/derivados, por lo que cambios físicos sin metadata requieren comprobación adicional.

## Operación privada auditada

ErasureInventory conserva action/proof/person protegidos, digest de origen y manifiesto cifrado. RightsAction registra operación de preparación, clave global UUID, versión y motivo cifrado. Un replay compatible devuelve el inventario original sin volver a registrar ni fingir que está actualizado. Los inventarios son evidencia de preparación, no autorizaciones perpetuas de borrado.

Permisos review_rights_request y execute_rights_request, MFA vigente, COI histórico/actual, responsable asignado, solicitud erase/reviewing, lectura auditada integral de entrada/respuestas y proof aprobado actual del tipo/sujeto/canal/gestor/versión/plazo. Simulación en producción rechazada. Locks del ámbito Agency→Person→Listing→RightsRequest; la preparación no cambia versión, fechas, consentimiento, publicación o estado del expediente.

Las consultas de inventario son un censo local, no un snapshot serializable de todo el sistema. Workers, cuentas y otras fuentes pueden cambiar durante o después de preparar. El futuro ejecutor debe bloquear y revalidar fuentes/dependencias, compartir protocolo con ediciones/cargas/tareas, comparar manifest actual y exigir nueva revisión cuando cambie. No usar solamente un digest antiguo para autorizar eliminación física.

## Contrato de pantalla

GET/POST /{es|en}/moderation/rights/{caseUUID}/erasure-inventory/, nombre erasure_inventory. Formulario key UUID, version entero positivo, purpose20–200; POST CSRF. GET muestra formulario sin manifiesto. POST válido devuelve200 con inventario auditado; datos inválidos400, evidencia/versión/clave/tipo incompatibles409, permiso/COI403, desconocido404. AccountGate puede redirigir302 a MFA cuando la sesión sea obsoleta. Cabeceras/logs privados comunes incluidos errores. El acuse público no muestra inventario, cuenta, motivos o digests.

Recargar por GET no revela automáticamente inventario anterior; para consultar se requiere nueva acción o replay autorizado con su clave. El manifiesto no se descarga ni se entrega al solicitante; una copia de acceso y una respuesta motivada siguen siendo operaciones distintas.

## Pendientes de ejecución completa

Ampliar dependencias e inventario físico, decisión revisada por finalidad con motivo/plazo y alcance, separación de terceros y cuenta con responsabilidades, retirada/revocación, borrado/redacción/anonimización local idempotente, reconciliación de archivos compartidos y tareas antiguas, conservación restringida, purge tras plazo, tombstones/restauración/backups, destinatarios y respuesta/cierre con evidencia real. Las fases CR10/GS01/BF/BB/C siguen pendientes. No reducir la definición de terminado a preparar este inventario.


## Evidencia local

Migration safety0034 aplicada. Inicial1 failed/2 passed30.85s por fixture con revisión inexistente, corregida a borrador existente. Ampliada9 passed64.14s junto a medidas de publicación; final4 passed35.92s del inventario con carrera y M2M adicionales. PostgreSQL/Chromium sin skips, ejecuciones separadas. Detalles en docs/18. No supresión ejecutada ni regresión común CR09.

Ampliación final: estado HMAC de PhoneClaim y regresión de cambios de comprobación;4 passed35.88s sobre código actual, sin skips. La ejecución35.92s era previa; no sumar.


Integración CR09 de dependencias nuevas en inventario: UrgentReportAlert (perfil de anuncio o sujeto histórico), RightsResponseAcknowledgement (respuestas de casos propios) y PrivacyHoldReleaseProposal (cautela de perfil propio) se incorporan como dependent_evidence. Whitelist de metadatos/IDs/fechas/estado, sin leer motivos/textos/huellas de canal, salida solo count/state_digest HMAC. Cambios de reconocimiento o ejecución invalidan fuente de plan anterior; no se añaden operaciones de supresión de estas evidencias ni se presume conservación jurídica completa.
Regresión final25 passed185.51s PostgreSQL/Chromium sin skips (erasure_execution/inventory/plans), exit0. Caso nuevo crea respuesta antes de revisar inventario/plan, reconocimiento POST posterior no cambia case.version/response_version pero cambia HMAC: ejecución rechazada sin borrar token/copias ni crear ErasureExecution; inventario y plan nuevos revisados permiten ejecución scoped y borran token propio. Cobertura existente incluye móvil/permisos/COI/producción/CSRF/versiones/carreras/scopes y aislamiento. Ruff/diff limpios; sin migración nueva ni task/schedule. No suite común/CR09 completos. Docker en actualización; registrar sincronización posterior. Claude3/3 sin nuevas llamadas. Continuar derechos integrales/retención-reconciliación-restauración/respuestas finales, CR09→CR10→GS01→BF/BB→C.


Docker inventario actualizado: app/worker/Beat reconstruidos/recreados; sin migración nueva, safety0041 confirmada/UID10001/backends derechos y avisos disabled/healthCaddy200. SHA256 erasure_inventory.py host/contenedorf1d6965f7610676d360198f2fd8dd7adf0d7e901b94bc900fa63af91471f94b8 coincide. Sin cambios en tareas/schedule ni nuevo ensayo operativo necesario para fuente HTTP.


REQ-CR09-COMPLAINT-CLARIFICATION-01: solicitud prefijada y aportación privada cifrada con idempotencia/versión/CSRF/límite; lectura completa paginada auditada antes de enlace/pregunta/resolución. Corrige colisión messages de contexto con avisos Django. Regresión15 passed101.83s PostgreSQL/Chromium, móvil reforzado1 passed21.05s; evidencia docs/evidencias/aclaraciones-reclamaciones.json. Docker app/worker/Beat reconstruidos/recreados; safety0042 aplicada/UID10001/health200. ComplaintMessage entra como metadatos dependent_evidence, sin nuevas operaciones de supresión. Ruff/check/makemigrations/diff limpios. No resolución final de referencias desconocidas/obsoletas ni avisos externos; CR09 y contrato completo abiertos. Claude3/3 sin llamadas.


REQ-CR09-COPY-PARTS-01: integración final38 passed238.05s, exit0 sin errores/fallos/skips, PostgreSQL/Chromium reales. XML contrastado/hash docs/evidencias/copia-partes-integracion-final.json. Paquetes cifrados<=64MiB reales, snapshots<=10MiB; generación uno a uno sin tope agregado64MiB, manifest/POST privado/proof/versiones/CSRF/auditoría que distingue recurso, acuse móvil ES/EN, purga vencida y supresión transitoria/inventario/parts_cleared. Incluye ensayo real>64MiB sintético y regresión previa de exports/images/retention/inventory/execution. Worker/Beat reales y cleanup aparte docs/evidencias/copia-partes-worker-beat.json. Ruff/check/makemigrations/diff limpios; Docker en resincronización final de contador de supresión. Entrega local acotada, no derecho de acceso/portabilidad integral ni identidad/proveedor/producción/CR09 completos. Pendientes resto de información propia/finalidades/redacción parcial/originales cuando proceda, conservación/reconciliación/restauración/respuestas y CR10→GS01→BF/BB→C. Claude3/3, sin llamadas.
