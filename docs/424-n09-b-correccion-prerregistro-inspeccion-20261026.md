# N09B — corrección prerregistrada de autoridad antes de inspección

Antes de aplicar el candidato. [423](423-n09-b-prerregistro-inspeccion-derechos-20261026.md) se ejecutó sin cambiar la aplicación09028b5. N09 abierto139IDs/8de13bloques aceptados; [422](422-n09-a-correccion-verificada-recuperaciones-20261026.md) sigue aceptado sin repetir su QA29.

## Diagnóstico confirmado y preservado

Lote050131-3251e781: **1FAIL/44,683sJUnit**,0ERROR/0SKIP,1.761huellas estables (1.759runner+2documentos), limpieza y Telegram terminal confirmados. Auditoría independiente confirma `pg_stat_activity`/Lock y PID propio bloqueante, permiso retirado y confirmado por una nueva instancia User antes de liberar; después POST200en vez de403y `RightsAccess` pasó1→2. Solicitud, acciones y estado mínimo permanecieron iguales; hilo y conexiones cerrados. Es un tercer defecto confirmado de autoridad obsoleta de N09 en una ruta distinta. No se observan ni registran bytes descifrados:200y auditoría nueva prueban la inspección indebidamente autorizada, sin ampliar esa evidencia.

Petición218,619msincluye espera inducida; no latencia normal ni resultado de rendimiento. El fallo original queda intacto, sin xfail ni cambio del oráculo.

## Candidato acotado y límites

Sólo `apps/safety/rights.py`: importación de User, helper local de actor actual para inspección y llamadas en `inspect`. No modificar `allowed`, colas, otros servicios, modelos, migraciones, settings, formularios, rutas, plantillas ni funciones de cifrado.

Capturar versiones de sesión/MFA del usuario de entrada una vez. Consultar una nueva instancia User al entrar en la vista y tras `locked_case`, antes del scope final/descifrado/auditoría. Exigir cuenta existente/activa/no borrada, MFA habilitado, permiso `review_rights_request`, igualdad de las versiones originales con las actuales y de las versiones `account_version`/`mfa_version` de la sesión con las actuales. La compatibilidad inicial de account_version0la gestiona el middleware vigente, no se autoenlaza aquí una sesión revocada.

Actualizar `request.user` con el actor fresco para los permisos, ámbito y auditoría posteriores; conservar las versiones originales capturadas aunque se sustituya la instancia. Denegación403privada y comportamiento bilingüe nativo, sin nuevos efectos. Mantener orden de locks/lecturas, propósito/cursor/paginación, payload/mensajes/respuestas sólo después de acceso autorizado y comportamiento GET sin datos privados. No añadir lockUser ni prometer serialización universal después de la última lectura de autoridad. Nuevas consultas justificadas por seguridad, no optimización marginal.

## Verificación prevista:19casos

Reejecutar el único diagnóstico real de423sin cambiar su oráculo y añadir8negativos de entrada a la vista con un request/actor legítimo obsoleto: retirar permiso, desactivar cuenta, marcar borrado, deshabilitar MFA, incrementar epochMFA, incrementar epochsesión, contexto de sesiónMFAincorrecto y contexto de sesióncuentaincorrecto. Usar RequestFactory y la vista real decorada para conservar un objeto de usuario cacheado tras mutación ORM externa; son negativos de frontera de vista, no prueba adicional de middleware o transporte. Todos403y snapshots de negocio intactos. No parches de guards, cifrado, ORM o respuesta.

Diez originales sin editar, seleccionados por sus garantías actuales:

- `test_rights_intake`: `test_rights_permission_is_separate_mfa_required_and_inspection_audited`, `test_rights_only_permission_still_requires_current_mfa`.
- `test_rights_linking`: `test_link_is_audited_and_preserves_unverified_scope_dates_and_payload`, `test_scope_can_reference_unpublished_data_without_verification`, `test_original_agency_editor_cannot_inspect_after_transfer_or_revoke`, `test_management_version_change_between_snapshot_and_lock_prevents_read`, `test_mobile_link_stays_unverified_and_get_hides_request_data`.
- `test_rights_messages`: `test_reviewer_only_reads_clarifications_after_audited_post`, `test_older_clarifications_are_accessible_with_audited_cursor`.
- `test_rights_responses`: `test_all_outgoing_pages_are_required_and_receipt_has_complete_history`.

Total1espera+8negativos+10originales=19. Los originales cubren auditabilidad/permisos/MFA, datos en GET/POST, referencias publicadas/no publicadas, conflicto/transferencia, cambio de gestión, mensajes/respuestas de52elementos con páginas50y2y un recorrido móvil real. Pruebas que usan interposición controlada se identificarán como tales; no sustituyen la espera PostgreSQL real. PostgreSQL/Redis desechables, serial, runner nativo oficial con timeout900s; no exportación larga ni QA de otros bloques por solapamiento.

Propuestas aisladas, revisión Django Expert/Reviewer, lint antes de AST/semántica/corte/congelación; notificaciones terminales y limpieza con recibos. Conservar FAIL/ERROR/SKIP y corregir el alcance afectado sin recortar selección para ocultarlos. Aceptar sólo con19PASSy oráculos/snapshots válidos. Tabla antes/después incluirá tiempos observados con sus límites, sin porcentajes causales entre espera+ejecución y espera+denegación. N09 seguirá abierto hasta conciliar139IDs; otras condiciones sólo de fuente requieren evaluación propia. N02al final, N10compartido/N12–N14condicionados, alfa/sinproveedor/sinapertura.
