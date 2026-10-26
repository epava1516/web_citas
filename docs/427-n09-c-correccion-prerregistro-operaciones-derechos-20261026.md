# N09C — corrección prerregistrada de cuatro operaciones de derechos

Antes de cambiar la aplicación. Base28afe57; [426](426-n09-c-prerregistro-autoridad-operaciones-derechos-20261026.md) diagnosticado y preservado. N09 abierto139IDs/8de13bloques; [425](425-n09-b-inspeccion-autoridad-verificada-20261026.md)19PASSy [422](422-n09-a-correccion-verificada-recuperaciones-20261026.md)29PASSno se repiten por notas.

## Cuatro defectos confirmados, originales intactos

Lote053006-990a74d8: **4FAIL/73,493sJUnit**,0ERROR/0SKIP,1.763huellas estables (1.761runner+2documentos), limpieza y Telegram confirmados. Auditoría independiente de cada caso confirma Lock/PID propio bloqueante antes de retirar el permiso, revocación comprobada mediante Usernuevo, confirmación al liberar, hilo/conexiones cerrados. Cada POST terminó200/302con efectos en vez de403sin cambios; no se atribuye un fallo instrumental a aplicación.

| Operación | Resultado original tras revocación | Tiempo de petición inducido |
| --- | --- | ---: |
| Medida de privacidad |302;+hold/+acción;solicitud y publicación modificadas|449,082ms|
| Inventario |200;+inventario/+acción;fuentes y solicitud intactas|851,242ms|
| Inicio de verificación |302;+proof y versión de solicitud incrementada|320,166ms|
| Resultado independiente |302;+evento,proof y solicitud modificados;scope simulated_passed|346,407ms|

Los proof/eventos son sintéticos del simulador: autoridad de aplicación, sin identidad real ni proveedor. No se registran payloads ni motivos. Conservar las4FAILsin xfail ni reducción de oráculos. Los tiempos incluyen bloqueo inducido; no latencia normal, capacidad ni mejora causal.

## Cambio de producto propuesto, con propiedad acotada

Sólo tres módulos: `apps/safety/privacy_holds.py`, `apps/safety/erasure_inventory.py`, `apps/safety/rights_verification.py`. Helpers locales de actor actual/importUser y llamadas en `hold`, `prepare`, `start`, `receive_event`; no modificar otros handlers, formularios, modelos, cifrado, migraciones, settings, servicios ni contrato externo. `check_actor` de verificación y sus reglas de ámbito se conservan; no refactor general.

Capturar una vez session_version/mfa_version del usuario recibido. Consultar una nueva instancia User para admitir el servicio y tras los locks relevantes, antes de replay o escritura. Exigir existencia, cuenta activa/no borrada, MFA habilitado, epochs iguales a los originales y permisos actuales: review_rights_request+execute_rights_request para hold/inventory; review_rights_request para iniciar; review_rights_request+verify_rights_scope para resultado independiente. Usar el actor fresco en ámbito y auditoría. PermissionDenied conserva el403de las vistas nativas.

En hold/prepare/start, repetir autoridad después de los locks canónicos. En receive_event, después del caso y de su último lock de proof; revalidar el ámbito y separación del verificador sobre el proof bloqueado antes del replay/evento. Conservar enabled/producción, validación y firma del payload, bindings/versiones, lectura auditada, motivos/cifrado, claves y semántica de replay legítimo. No añadir locks del operador ni cambiar el orden de locks de dominio; no prometer serialización universal después de la última lectura de autoridad. Consultas adicionales justificadas por seguridad, sin candidato de rendimiento.

## Verificación prevista:58casos finitos (revisión antes de integrar/congelar)

Reejecutar los4diagnósticos reales de426sin cambiar oráculos. Añadir una quinta espera real de resultado independiente sosteniendo el último RightsProof, después de adquirir los locks canónicos: comprueba la nueva frontera posterior al proof, que la espera del caso no ejercita. Es regresión nueva, sin baseline previo ni quinto defecto confirmado atribuido. El plan previo57y su semántica quedan conservados localmente como versión anterior; esta revisión58se fija antes de integrar el candidato y de ejecutar/congelar. No se repite ninguna prueba válida por este ajuste. Añadir31negativos públicos de servicio con actor/cache legítimos obsoletos y mutaciones ORM externas:

- 27 entradas frescas: hold7+inventory7+start6+result7. En cada operación: retirar permiso principal, cuenta inactiva/borrada, MFA deshabilitado, epochMFAincrementado y epochsesiónincrementado; además retirar review_rights_request en hold/inventory/result (start ya tiene ese permiso como principal).
- 4 replays: una ejecución legítima previa de cada operación, conservar sus efectos como referencia, retirar el permiso principal y llamar al mismo servicio con la clave/payload originales. Exigir PermissionDenied y snapshots intactos; no basta un retorno de objeto anterior sin mutación.

Estos31casos son de servicio, sin afirmar middleware/transporte/concurrencia adicionales; las5esperasPOSTprevistas acreditarán la espera real. Ningún patch de guards, ORM de negocio, cifrado o proof; sólo adaptación nativa de fixtures durante preparación. Guard propio explícito/serial/noPROD/PGpropio. Snapshots escalares de caso/acciones/accesos/persona/listing/revisiones/hold/inventory/proof/event excluyen la mutación deliberada del operador.

Regresión original completa y sin editar: `test_privacy_publication_holds.py`6casos, `test_erasure_inventory.py`4, `test_rights_verification.py`8y `test_rights_account_verification.py`4: **22originales**. Incluyen grounds/proofs/COI/transferencias, CSRF, replay/versión, concurrencia, móvil, simulador rechazado enPROD, revisión independiente y separación del estado de cuenta/perfil. Los casos de interposición controlada se distinguirán de los4bloqueos reales. Los4de cuenta se incluyen porque comparten los servicios de verificación modificados, sin reabrir N06.

Total5esperas+31negativos+22originales=58. Runner oficial serial con PostgreSQL/Redis propios desechables, parser nativo/aislamiento de broker/observación HTTP y timeout900s. Sin QA global/exportación larga ni repetir19/29aceptados. Propuestas aisladas, revisión Django Expert/Reviewer, lint antes de AST/semántica/corte/congelación; resultado terminal, limpieza y recibos Telegram comprobados.

Aceptar sólo con selección completa58PASSy pruebas de autoridad/snapshots válidas. Si falla, conservar originales, separar producto/instrumento y corregir el alcance afectado sin recortar selección. Tabla antes/después con tiempos disponibles y límites, sin aceleración causal entre ejecuciones/denegaciones o seleccionesQA distintas. N09 sigue pendiente hasta disposición de139IDs; otras condiciones de fuente y referencias finitas purgas/outbox/jobs requieren su evaluación. N02al final/N10compartido/N12–N14condicionados/alfa/sinproveedor/sinapertura.
