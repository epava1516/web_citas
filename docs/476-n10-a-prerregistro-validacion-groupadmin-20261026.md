# N10A — prerregistro de validación de GroupAdmin

Estado: candidata preparada y revisada estáticamente, sin aceptación runtime. Base `b2ed399`, [original y decisión475](475-n10-a-diagnostico-y-plan-correccion-admin-20261026.md). N10 abierto,9/13 bloques aceptados, alpha/noindex. El original `20261026-202925-4860b46d` conserva1PASS/1FAIL/55,892sJUnit y sus efectos reales; no se cambia aPASS.

## Candidata e identidad

Sólo cambia producto en el nuevo `apps/core/admin.py`: GroupAdmin propio con guardas actuales después de adquirir Group, guarda antes de save_related, y transacción de toda delete_selected incluyendo auditoría. User fresco en el alias de escritura, epochs originales de request.user/sesión, activo/staff/correo verificado/MFA/no borrado y permiso específico add/change/delete. No reemplazar al actor original, bloquear User/grants, editar vendor, migraciones/settings o servicios. Se conservan formularios, widgets, URLs, collector, etiquetas, permisos y operaciones nativos.

SHA de candidata revisada: `9dcd3bab3fc18ca2264ebcdeaf299a6f7a99d1f4ebeea89e0fe15c4e0060adec`. Los diagnósticos originales mantienen SHA `b53c6008dfe755d326161cdfe9e1342ae78d493d723b5ee4890f07f0b21196a2`. Nuevos instrumentos: wait_variants `33968def93392f1f078ecc9285deecd22117521451682244665739ea45b8680a`; crud `cf544d69aad1e01fddf6ca789219d404264facc389a27f9dfd20bb49479b337e`. No se cambia el archivo original para adaptar sus expectativas.

El observador original conserva la etiqueta textual de su contexto anterior, “default GroupAdmin/UPDATE”. En la candidata sigue observando el método registrado y reenviándolo; la espera se mueve al SELECT FOR UPDATE explícito antes de la guarda actual. Se acreditan las mismas filas objetivo bloqueadas y PIDs distintos, no que el SQL literal de espera permanezca UPDATE. El cambio de esa frontera es precisamente la corrección; sus tiempos no se compararán como aceleración.

## Selección exacta

Runner focused serial sobre estos tres archivos y ningún otro:

| Archivo | Casos | Propósito |
| --- | ---: | --- |
| tests/test_admin_group_authority_wait.py | 2 | Control y auth.change_group retirado durante espera real, originales byteidénticos |
| tests/test_admin_group_wait_variants.py | 7 | Delete individual y bulk, cada uno control/revocado; change con session_version, mfa_version o is_staff cambiados durante la espera |
| tests/test_admin_group_crud.py | 7 | Add, cambio de permisos, delete individual y bulk con permisos mínimos; retirar el propio change_group y borrar individual/masivamente el único grupo que concede delete_group |

Total16: nueve esperas reales —tres controles y seis denegaciones— y siete operaciones legítimas. Las variantes nuevas no tienen diagnóstico previo equivalente y no se presentan como defectos adicionales reproducidos. No repetir comandos, restores, capacidad o campañas N09.

## Datos, permisos y oráculos

Directory/photo_environment nativos, actores sintéticos activos no superuser con correo/MFA vigentes, is_staff deliberado y sesiones nativas force_login con account_version/mfa_version correctos. Es un supuesto de autenticación del instrumento, no login/TOTP humano, CSRF de navegador o proveedor. Cada control CRUD sólo recibe view_group y el permiso de su operación. En auto-retirada el único grant de change_group/delete_group viene del Group objetivo; no hay otro grant o grupo que lo enmascare.

Las esperas usan conexiones propias distintas, holder Group y pg_blocking_pids real. El callback sobre el método Admin registrado sólo observa/cachea la autoridad inicial y PID antes de reenviar a save_model/delete_model/delete_queryset; no sustituye permiso, respuesta ni escritura. La intervención se realiza después de confirmar la espera y se confirma con la liberación del holder. Snapshot base posterior a esa intervención incluye el grant retirado o el cambio intencionado del actor. Estado de staff false puede conservar has_perm true: no confundir permiso efectivo con todas las condiciones de entrada.

Controles con espera:302 y exactamente el cambio/deleción solicitados más auditoría nativa vinculada. Bulk selecciona dos Groups y conserva un pin; el snapshot del hilo principal no debe ver sus LogEntry aún no confirmados antes de liberar. Negativos:403 y ninguna modificación adicional de filas o archivos; los LogEntry previos de bulk deben revertirse. Se distinguen efectos físicos transaccionales y secuencias de los cambios duraderos de filas que se comprueban; no se promete revertir secuencias PostgreSQL.

Controles CRUD:302 con altas, cambios o cascadas exactos, sin cambiar otros grupos, permisos o datos. En auto-retirada la operación autorizada debe confirmar y el User nuevo debe perder el permiso. La siguiente escritura sobre un objetivo existente debe devolver403 y no producir efectos. Con view_group puede seguir siendo legítimo un GET200 de sólo lectura; no se exige403 a un objetivo ya borrado que el Admin nativo pueda redirigir.

Comparar todos los modelos instalados/through, auth y sesiones mediante transición esperada explícita: sólo PK nuevas/eliminadas y campos concretos, nunca excluir una tabla completa. Validar LogEntry actor/content_type/object/action_flag/mensaje/intervalo; Group.permissions y User.groups con sus FK exactos. Archivos por tamaño, hash, mtime y modo. Métricas y hashes sólo; sin nombres, IDs, cookies, valores privados, SQL/parámetros o cuerpo de formularios en propiedades JUnit.

Propiedades estrictas: `owned_admin_group_authority_wait`, `owned_admin_group_wait_variant` y `owned_admin_group_crud`, JSON finito y estado incompleto hasta pasar oráculos. Conservar resultados observados antes de las aserciones y cualquier FAIL/ERROR/SKIP. Las conexiones, respuestas, hilo y holder se cierran en todas las ramas con tiempos acotados y cancelación exclusiva del backend propio identificado.

## Ejecución, presupuesto y aceptación

Antes de lanzar: Ruff, revisión propia de aplicación e instrumentos, documentos/AST/semántica475/476/seguimiento, verificación de identidades y congelación de todas las fuentes, dependencias, vendor pertinente, documentos, grafo e IDs de imágenes. Un monitor local ligado al PID/start_ticks del runner comprobará que los contenedores reales corresponden a esas imágenes. No elegir un proceso ajeno por ser el más reciente ni reejecutar si se pierde su observación.

Runner oficial focused, --workers1, parser nativo local fijo limpio en `bc5f295c98b40c2c33099d9d72ab30ce9e595dc7`, PostgreSQL17-alpine/Redis7.4-alpine desechables propios, timeout900s. Límites por sentencia/hilo/cola ya fijados; se prevé un lote de minutos y se aplica el protocolo persistente de pruebas largas si la evidencia lo hace necesario. Nada se ejecuta en bases o servicios existentes, y MCP PostgreSQL sigue sin destino/rol automático.

Criterio:16PASS sinFAIL/ERROR/SKIP; nueve esperas/readiness comprobadas, negativos403/sin efectos, controles nativos exactos y auto-retiradas válidas, fuentes estables, limpieza real y Telegram terminal/auditoría enviados con recibo. No hay candidata de rendimiento ni umbral nuevo: tiempo de cuerpo/JUnit incluye espera y QA, no latencia normal ni mejora causal. Se conservan el presupuesto de corrección y las garantías, no se elimina autorización para ahorrar consultas.

La aceptación será local y acotada a esas operaciones/esperas. No serializa todos los cambios posteriores a la última comprobación ni acredita todos los locks through/FK/unique/auditoría. Fuentes y límites adicionales permanecen explícitos, sin declarar vulnerabilidades o seguridad universal por analogía. Después se documentará la tabla antes/después y se continuará N10 completo77IDs, N11 y N15; N02 residual al final y N12–N14 condicionados. Mantener los15cambios laterales fuera de la entrega propia.
