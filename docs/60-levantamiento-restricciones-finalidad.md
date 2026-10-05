# Levantamiento comunicado de restricciones por finalidad

Estado: diseño de continuación, no implementado. Depende de docs58–59; no acepta derechos ni CR09. La regresión de ejecución0069 sigue activa; no cambiar fuentes funcionales hasta terminal.

## Requisitos del recorrido

El ledger activo no debe desactivarse por fecha de revisión, cierre de caso, una nueva copia o modificación directa desde interfaz ordinaria. Evaluar una medida concreta por cuenta/finalidad y su modo restrict/cease, conservando las demás medidas activas. Una medida cease por oposición no se equipara automáticamente a una limitación temporal resuelta; exigir una solicitud nueva/retomada comprobada y fundamento revisado antes de permitir otra vez el tratamiento.

Se mantiene referencia al expediente original, comprobación, ejecución, autor y decisión revisada. Revisor independiente del ejecutor original, con permiso dedicado, revisión/ejecución/respuesta de derechos y MFA/sesión vigentes/COI. Reasignación canónica del caso cuando corresponda; no crear permisos implícitos por ser propietario de agencia.

Recorrido íntegro: consulta auditada de medida/decisiones actuales → propuesta motivada independiente → respuesta privada minimizada vinculada a propuesta → comunicación/recepción por canal registrado → nueva comprobación de identidad/ámbito después de propuesta y recepción → lectura completa actual de expediente/respuestas → ejecución de levantamiento de esa medida. El usuario debe conocer qué finalidad se propone reactivar; no incluir motivos internos, identificadores de moderadores, contactos de terceros o evidencia ajena.

Una confirmación simulada de desarrollo mantiene ese carácter. El acuse técnico no acredita comprensión humana, identidad real ni entrega del proveedor; no activar este procedimiento con adaptadores de prueba en producción.

## Modelo y causalidad previstos

Proposal enlaza Restriction, acción, prueba inicial, respuesta, HMAC de fuente y motivo cifrado; ejecución de release enlaza acción/prueba fresca/fecha. Mantener originales inmutables y registro de liberación separado. Unicidad de liberación efectiva por medida; propuestas reemplazadas no se ejecutan. Clave exacta idempotente, otra firma rechazada.

Fuente contempla cuenta/ámbito vigente, ledger activo/revisión/versión, decisión y ejecución originales, mensajes del solicitante y otros cambios pertinentes. No incluir la propia propuesta/aviso de forma que su creación invalide el HMAC. Comprobar por separado versión de respuestas/canal, última propuesta y recepción, prueba posterior y vigencia de lecturas. Cambiar fuente/ámbito/revocación/propuesta/aviso debe impedir ejecución sin levantar restricciones.

Locks canónicos de caso/ámbito → ejecución/medida → propuesta; adquirir User de preferencias según jerarquía existente. Revalidar permiso/COI/sesión/prueba/fuente después de esperas y antes de confirmar efectos, siguiendo corrección0069. No retener joins opcionales accidentalmente. Las operaciones de favoritos bajo User deben observar de forma atómica el estado anterior o el nuevo estado de la medida.

## Pantallas y pruebas exigidas

Cola privada por estado/vencimiento/finalidad con datos minimizados; pantalla de consulta/propuesta/ejecución ESEN, GET sin motivos/decisiones, POST auditado. En acuse privado, respuesta propia y recepción sin fundamentos internos. Resultado de levantamiento conserva solicitud abierta y no otorga excepciones para otra finalidad.

Probar medida válida, autor original/otro ámbito/no permiso/MFA revocados, falta de consulta/recepción/comprobación posterior, propuesta antigua, prueba revocada durante waits, claves repetidas/concurrentes, dos medidas activas para misma finalidad (levantar una no desbloquea la otra), preferencias preservadas, otros usuarios y canal de derechos accesibles, móvil ESEN/recarga, PostgreSQL/Docker y regresión conjunta.

Calendario operativo de medidas y registro/ejecución de excepciones acotadas siguen entregas necesarias; levantar una medida no es una excepción puntual ni decide conservación histórica. Fuente jurídica y revisión primaria de artículos18/19/21: docs58. Revisión jurídica externa permanece gate de producción.
