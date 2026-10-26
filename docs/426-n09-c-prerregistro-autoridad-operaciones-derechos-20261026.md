# N09C — prerregistro de autoridad en operaciones de derechos

Antes del diagnóstico, sin cambiar aplicación. Base28afe57, [425](425-n09-b-inspeccion-autoridad-verificada-20261026.md) y [422](422-n09-a-correccion-verificada-recuperaciones-20261026.md) aceptados localmente sin repetir19ni29casos. N09 sigue abierto139IDs/8de13bloques. Corte vigente:2.047fuentes exactas,SHA256 `92543394dd3ca1164cc5009fa3fe38b56793ea2a84a4d431665f7151898e00ea`.

## Hipótesis acotadas, no defectos runtime aún

En `privacy_holds.hold` y `erasure_inventory.prepare`, el permiso/MFA del usuario recibido se comprueba antes de `locked_case`, sin instancia nueva tras la espera antes de auditar/escribir. En `rights_verification.start` y `receive_event`, `check_actor` recibe el mismo usuario tras el bloqueo y consulta permisos cacheables; el resultado independiente añade `verify_rights_scope` sobre ese objeto. El ámbito/COI y la prueba vigente no sustituyen autoridad actual del operador. Son condiciones de fuente pendientes de reproducción propia.

## Cuatro casos previstos en tres familias

| Caso | Preparación nativa sintética | Permiso retirado durante espera | Resultado requerido |
| --- | --- | --- | --- |
| Medida de privacidad |`test_rights_responses.ready(kind=restriction)` y `test_privacy_publication_holds.values`|execute_rights_request|403;sin hold/acción ni cambio de publicación/solicitud|
| Inventario de borrado |`ready(kind=erase)` y `test_erasure_inventory.values`|execute_rights_request|403;sin inventario/acción ni cambios de fuente|
| Inicio de verificación |`test_rights_verification.prepared` y `payload(operation=start)`|review_rights_request|403;sin proof nuevo ni incremento de versión|
| Resultado independiente |`prepared`, inicio legítimo, refresh/lectura auditada del verificador y `payload(operation=result,outcome=passed)`|verify_rights_scope|403;sin evento/transición de proof/solicitud|

Preparar sesiones y lecturas legítimas antes de bloquear, refrescar instancias tras servicios nativos. Los proof/eventos son del simulador no producción; estos casos prueban autoridad de aplicación, nunca verificación de identidad real ni proveedor. Conservar objetos/auditorías legítimos anteriores y verificar su estado en snapshots antes/después.

Mantener `SELECT FOR UPDATE` del RightsRequest en la conexión principal. Otro hilo realiza un POST HTTP real en la ruta correspondiente. Reutilizar el observador pasivo de419/423para PID efectivo y `pg_stat_activity`/Lock con PID propio bloqueante. Sólo entonces retirar el permiso, confirmar ausencia con Usernuevo y confirmar transacción al liberar el lock. No parchear guards, scope, ORM de negocio, cifrado, proof ni respuestas.

Cada caso exige403, snapshots escalares de solicitud/acciones/auditorías y recursos específicos idénticos, estado mínimo igual, hilo/conexiones cerrados y transacción liberada. Guard propio del nuevo archivo explícito/serial/noPROD/PGpropio, sin reutilizar el guard `__file__` de otro instrumento. Payloads/motivos/datos/credenciales no salen del instrumento: sólo estado, status, huellas/conteos, PIDs propios y tiempo inducido.

## Ejecución y clasificación posterior

Revisión Django Expert/Reviewer, fixtures/guard/instrumento y lint antes del AST/semántica/corte/congelación. Runner oficial con PostgreSQL/Redis propios desechables, parser nativo, aislamiento de broker, observación HTTP y timeout900s, cuatro casos seriales. Avisos Telegram de inicio/terminal, recibos y limpieza verificados. No QA global ni exportación larga.

Conservar FAIL/ERROR/SKIP. Un éxito HTTP200/302con cambios tras espera/revocación confirmadas demuestra un defecto en esa operación; un fallo antes de observarlas puede ser instrumental y no se atribuirá a aplicación. Si deniega correctamente, conservar esa evidencia sin corregir por semejanza. Prerregistrar cambios y regresión sólo para defectos confirmados, sin modificar producto antes del diagnóstico. Tiempos con espera inducida no son latencia normal ni comparación causal. N09/139IDs, otras condiciones de fuente, referencias de purgas/outbox/jobs y N10 siguen pendientes; N02restante al final/N12–N14condicionados/alfa/sinproveedor/sinapertura.
