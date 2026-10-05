# Derechos de una cuenta sin perfil

Estado: implementación iniciada; vínculo de ámbito comprobado localmente, consumidores pendientes. Complementa docs/40, docs/49 y docs/50; no acepta CR-09. No constituye una nueva función comercial: evita que una cuenta registrada necesite crear un perfil publicable para tramitar sus datos.

## Hueco comprobado

El vínculo nuevo de docs/50 admite una Person sin Listing. Todavía exige Person. RightsProof, RightsRectificationProposal, ErasureInventory y ErasureExecution mantienen referencia obligatoria a Person. Por tanto, el recorrido verificado no demuestra acceso, rectificación, limitación/oposición o supresión de una cuenta de visitante o propietario de agencia que no sea sujeto de un perfil.

No fabricar un Person, anuncio, representación o consentimiento para satisfacer esa dependencia. Tampoco usar al propietario de agencia como sustituto del sujeto de un modelo. La solicitud pública y su canal pueden recibirse antes de identificar la cuenta; una referencia técnica no demuestra identidad.

## Requisitos del recorrido

1. Vinculación privada auditada a User existente con asignación, versión, motivo, clave idempotente, permisos/MFA y conflictos de interés. Mantener las referencias históricas; distinguir expresamente ámbito de cuenta y ámbito de perfil, sin migrar casos antiguos por inferencia.
2. Comprobación proporcionada de identidad y ámbito ligada a caso, cuenta y canal, con revisión independiente, caducidad y versión. No tratar sesión, ID, correo propuesto o enlace de acuse como acreditación suficiente por sí solos. Preservar separación entre comprobación de identidad y posesión de nuevo buzón.
3. Fuente autorizada bajo lock de User y caso, con estampa de credenciales, sin proyectar contraseña/MFA/tokens. Adaptar contratos/modelos de prueba y propuestas para representar cuenta sola; ninguna operación debe conceder autoridad sobre personas/agencias relacionadas por mera dependencia.
4. Rectificación de nombre/apellidos/correo con aprobación, comunicación/recepción y ejecución atómica. Unicidad de correo, confirmación del destino, invalidación de sesiones/enlaces y conservación de MFA mantienen las garantías de docs/49. Cuenta sola nunca crea ni cambia contenido editorial.
5. Inventario por finalidad de datos propios: cuenta, aceptaciones documentales, favoritos, evidencias/canales y recursos operativos pertinentes. Separar datos ajenos y secretos; conservar la historia de destinatarios y motivos minimizados. Acceso/portabilidad, retención/supresión, limitación/oposición y respuesta final requieren ejecución propia, no un estado marcado manualmente.
6. SSR ES/EN y móvil para cada operación, CSRF, consultas auditadas y GET inocuo. Ensayos PostgreSQL de cambios de cuenta durante espera, independencia, claves concurrentes, colisiones, reintentos y rollback; worker/Beat y Docker reales cuando corresponda. Identidad/entrega simuladas se documentan como simuladas.

## Condición de aceptación

Partir de cuenta registrada sin Person ni Listing y completar cada derecho aplicable con sus pruebas y evidencias. Probar también cuenta de propietario de agencia sin mezclar modelos gestionados y cuenta propia. La aceptación se añade a la matriz de CR-09 únicamente tras recorrer estados reales y verificar sus consumidores; no basta admitir un nuevo campo de vínculo.

Operación, conservación definitiva, proveedores y revisión jurídica siguen sujetos a sus gates existentes. Este documento conserva un pendiente técnico; no declara integración o cumplimiento completos.

## Avance de ámbito explícito

RightsRequest.account_subject distingue una cuenta propia del perfil; migración0059 añade constraint que impide combinar cuenta con Person o Revision. Acción link admite link_account_id, exige responsable/consulta auditada/MFA/motivo/versión/clave, bloquea caso y User y rechaza cuenta suprimida o representación sin perfil. Conflicto de interés incluye cuenta referenciada; no se crea perfil ni prueba. Reintento exacto conserva la acción única y el canal/historia original. Formulario SSR expone referencia de cuenta sin datos personales.

Batería PostgreSQL /tmp/rights-account-linking.xml:10 correctas69,07s,7 excluidas. Incluye nuevas2 y enlaces anteriores de anuncio/perfil, CSRF, conflicto, referencias mixtas, representación y cuenta suprimida. Check/makemigrations/ruff/diff limpios. No acredita carreras del nuevo vínculo, móvil de cuenta, identidad, derechos ejecutados ni runtime0059. No cierre de requisito completo ni CR09. Próximo: autoridad versionada de cuenta, fuente y propuestas, consumidores/inventario/ejecución, navegador/concurrencia y Docker.

## Autoridad de cuenta

RightsProof admite exactamente un ámbito: Person o account_subject, constraint en migración0060. Conserva ámbito de perfiles existente, no migra por inferencia. Comprobación de cuenta guarda HMAC del estado bloqueado de User (nombre, apellidos, correo/verificación, activación, credenciales y versiones de sesión/MFA), ID del sujeto y canal/version/expiración del expediente. Resultado exige segundo revisor con permiso, lectura auditada actual y estado fuente idéntico. Consumidor reconsulta User bajo lock y rechaza comprobación obsoleta. Adaptador sigue simulado y prohibido en producción.

Batería92650 terminal0:14 correctas102,15s, sin exclusiones, PostgreSQL; nuevas4 de cuenta, comprobaciones anteriores de perfil y2 vínculos de cuenta. Inicio/resultado/replay/independencia y cambio de correo/sesión/MFA antes del resultado o nombre después de aprobación denegados sin aprobación nueva. Check/makemigrations/ruff/diff limpios. Error inicial de check por reverse accessor corregido con related_name explícito antes de crear0060 y ejecutar pruebas.

Pendientes: carreras observadas de cuenta, navegador móvil, propuestas/ejecución/inventario y todos los derechos aplicables; Docker aún0058. Las14 no constituyen suite común CR09 ni aceptación del recorrido integral.

## Propuestas de rectificación de cuenta

Migración0061 permite un único ámbito Person/User en RightsRectificationProposal; cuenta no admite source_revision. Fuente bloqueada solo de User/canal, consulta auditada sin secretos y cambios limitados al bloque account. Servidor rechaza alias/título/fotos y demás contenido editorial; propuestas cifradas, replay exacto, fuente anterior invalidada y GET sin valores. Revisión independiente filtra además por account_subject del expediente. Endpoint de fotos rechaza ausencia de Person. Ejecución y confirmación de destino de cuenta sola todavía pendientes.

Primera batería37949 terminal1:2 fallidas/4 correctas51,15s; preparación de nuevas pruebas carecía de execute_rights_request, rechazo correcto PermissionDenied. Corregida preparación y caché de permisos, sin relajar servidor. Repetición54693 terminal0:6 correctas50,10s,2 móviles excluidas, PostgreSQL; fuente/propuesta nuevas y cuenta de perfiles anterior. Ampliación HTTP69850 terminal0:2 correctas29s: GET sin email/valores, POST consulta auditada y campos visibles, cifrado/replay/sin mutación. Ruta de foto inicial errónea solo probaba404 del router; corregida a /rectification/photos/ y prueba89082 terminal0:1 correcta22,72s (1 excluida), verifica rechazo real del endpoint con cuenta sin perfil. No sumar estas baterías como suite común.

Check/ruff/makemigrations/diff limpios. Runtime sigue0058, consumidores de ejecución/copia/supresión/conservación, navegador/concurrencia y aceptación común siguen pendientes.

## Ejecución y destino de cuenta sola

Consumidores account_email_confirmation y rectification_account resuelven User desde ámbito explícito del expediente; no sustituyen al sujeto por gestor. Ejecución conserva revisión independiente, comunicación/acuse del canal, nueva prueba y consultas auditadas, sin clonar editorial ni incrementar rights_version inexistente: resulting_rights_version nullable en0062 para cuenta sola. Caso/version/scope invalidan autoridad tras ejecución. Confirmación de destino mantiene caducidad/cifrado/origen/CSRF y consumo; correo cambia session_version y conserva contraseña/MFA.

73412 terminal0:1 correcta24,80s, PostgreSQL, recorrido completo nombres y replay sin Person. Ampliación64639 terminal0:4 correctas48,89s: nombres/correo×cuenta visitante/propietario de agencia. Revisión independiente→comunicación→acuse HTTP real→prueba fresca→ejecución; correo usa entrega local explícitamente simulada, GET no confirma y POST sin CSRF403; POST válido confirma, ejecución consume y borra entrega. Comparación de todas las filas Person preserva modelos gestionados, sin perfil nuevo. No verifica todavía origen/navegador móvil de cuenta sola, carreras nuevas, copia/supresión/retención ni proveedor real.

Regresión conjunta anterior de confirmación/cuenta/carreras/revisión con nuevos recorridos pendiente; runtime0059–0062 todavía pendiente. CR09 permanece abierto.

## Regresión y límites de ámbito

Regresión conjunta60099 terminal0:38 correctas420,96s PG/Chromium antes de guardas de consumidores exclusivos de perfil. locked_profile_case centraliza rechazo de ámbito cuenta en publicación/recursos media/destinatarios/inventario y ejecución de supresión de perfil; copia antigua rechaza cuenta hasta incorporar proyección propia. No ejecutar un derecho de cuenta mediante operación de perfil.

Batería41927 terminal1:1 fallida/15 correctas134,21s; negativos de cuenta carecían de permiso review_rectification y obtenían PermissionDenied antes de la comprobación de ámbito. Corregida preparación con permiso y recarga de User; repetición95107 terminal0:1 correcta22,31s. Verifica cinco consumidores (publicación, inventario de supresión de perfil, destinatarios, descarte media y copia de perfil) rechazados sin acciones/cambio de cuenta/version/ámbito. Las15 positivas anteriores siguen probando la misma fuente funcional, no sumar como nueva suite16.

Docker reconstruido y recreado después de guardas, sin nueva migración tras0062. Verificación de18 fuentes host/app/worker/Beat y check/migrate--check/UID10001/health200 en evidencia runtime. Aún pendientes: copia/inventario/limitación/oposición/supresión/retención/respuesta final de cuenta sola, carreras y móvil nuevos y aceptación común CR09.
