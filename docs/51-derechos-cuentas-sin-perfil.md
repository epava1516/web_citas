# Derechos de una cuenta sin perfil

Estado: pendiente de implementación. Complementa docs/40, docs/49 y docs/50; no acepta CR-09. No constituye una nueva función comercial: evita que una cuenta registrada necesite crear un perfil publicable para tramitar sus datos.

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
