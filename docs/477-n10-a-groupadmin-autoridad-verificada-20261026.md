# N10A — autoridad de GroupAdmin verificada localmente

Aceptación local de la corrección seleccionada, **no cierre de N10**. Continúan9/13bloques aceptados y N10 abierto77IDs. Alpha/noindex. [Original y decisión475](475-n10-a-diagnostico-y-plan-correccion-admin-20261026.md), [selección476](476-n10-a-prerregistro-validacion-groupadmin-20261026.md), base `b2ed399`.

Original `20261026-202925-4860b46d`:1PASS/1FAIL,55,892sJUnitQA/1.788huellas estables. Permiso efectivo change_group retirado durante espera real, aun así302 y cambio de nombre más un CHANGE LogEntry; control nativo válido. Ocho archivos intactos,173modelos auditados, recursos/temporal retirados y TelegramERROR entregado. No se reescribe el fallo ni se acredita escalada: el Group sintético estaba vacío y sin permisos.

Candidata `20261026-211007-c4c78619`: **16PASS, ceroFAIL/ERROR/SKIP,159,971sJUnitQA/1.791huellas estables**. Auditoría propia contrastó cada propiedad con el XML, los nueve bloqueos reales, oráculos, imágenes congeladas antes/observadas durante la ejecución, fuentes adicionales/doc/grafo, limpieza y TelegramPASS entregado. Tres controles válidos de espera, seis denegaciones y siete operaciones legítimas. No se repitieron comandos, restores o campañas anteriores.

## Cambio y preservación

Sólo un nuevo módulo de aplicación, apps/core/admin.py: subclase del GroupAdmin registrado, adquisición del destino antes de un User nuevo y permiso actual, epochs originales de actor/sesión y estado activo/staff/correo/MFA/no borrado. Se conserva el User original; no se bloquean User/grants ni se adoptan epochs actualizados. Guardas en save_model, save_related y borrados; todo delete_selected, incluida auditoría nativa anterior a delete_queryset, queda dentro de una transacción.

Formularios, permisos add/change/delete, widgets, ordenación, URLs, collector, etiqueta y comportamiento nativos permanecen. No hay veto posterior que impida retirar voluntariamente los propios permisos: la autorización precede al efecto intencionado y la próxima petición usa la autoridad nueva. No vendor, modelo, migración, settings, servicio o proveedor modificado.

Los dos diagnósticos originales son byteidénticos al original. En ellos la etiqueta textual histórica UPDATE/defaultGroupAdmin sigue en el instrumento; la candidata mueve esa espera a su SELECT FOR UPDATE explícito antes de la guarda actual. La prueba acredita el mismo destino/PID bloqueado y el método nativo reenviado, no SQL literal inmutable ni una mejora de tiempo causal.

## Antes y después

| Operación / intervención durante espera | Antes | Después | Cuerpo QA antes, s | Cuerpo QA después, s |
| --- | --- | --- | ---: | ---: |
| Cambio autorizado | 302;name+1LogEntry | 302;name+1LogEntry | 7.434 | 7.649 |
| Cambio con change_group retirado | 302;name+1LogEntry | 403;sin cambio ni nuevoLogEntry | 6.217 | 7.040 |
| delete/none | Sin diagnóstico previo equivalente | 302;deleción y auditoría exactas | — | 6.635 |
| delete/permission | Sin diagnóstico previo equivalente | 403;sin efectos adicionales | — | 7.400 |
| bulk/none | Sin diagnóstico previo equivalente | 302;deleción y auditoría exactas | — | 6.554 |
| bulk/permission | Sin diagnóstico previo equivalente | 403;sin efectos adicionales | — | 6.082 |
| change/session | Sin diagnóstico previo equivalente | 403;sin efectos adicionales | — | 6.759 |
| change/mfa | Sin diagnóstico previo equivalente | 403;sin efectos adicionales | — | 7.053 |
| change/staff | Sin diagnóstico previo equivalente | 403;sin efectos adicionales | — | 6.434 |

Los tiempos son cuerpos QA con preparación, espera inducida, snapshots y limpieza, no latencia normal de Admin. El total original de dos casos frente al total candidato de16no es un antes/después homogéneo. La corrección añade lecturas y locks de autoridad; no se presenta como optimización ni se declara porcentaje temporal.

## Oráculos efectivamente observados

Nueve esperas con conexiones/PIDs distintos, actor permitido/cacheado y epochs de entrada válidos antes de la intervención. Cambios tardíos: change_group/delete_group retirados, session_version, mfa_version o is_staff; cada mutación intencionada pertenece al snapshot base. En stafffalse el permiso efectivo puede seguir true, pero el actor ya no cumple la entrada administrativa. Todas las denegaciones llegaron a la espera real y devolvieron403 sin modificaciones duraderas adicionales.

Delete individual y bulk conservaron controles302 y exactitud de destinos/auditoría. Bulk seleccionó dos Groups y conservó un pin no seleccionado; sus LogEntry no eran visibles al hilo principal antes de liberar el holder y no quedaron confirmados tras denegar. Se comprueban filas duraderas, no reversión de secuencias PostgreSQL.

Siete controles CRUD/semántica: add con sólo add+view, edición de permisos con change+view, delete individual y bulk con delete+view; retirar el propio change_group mediante Group.permissions y borrar individual/masivamente el único Group que concede delete_group. Las tres retiradas propias confirmaron302, perdieron el permiso efectivo y una escritura posterior sobre un objetivo existente devolvió403 sin efectos. El GET de sólo lectura del Group conservado puede seguir200 con view_group: no se confunde lectura permitida con escritura autorizada.

Cada caso comparó173modelos instalados/through, auth y sesiones, permitiendo sólo PK nuevas/eliminadas y campos previstos. Group.permissions/User.groups y LogEntry se vincularon exactamente; actor, contenido, objeto, flag, mensaje e intervalo comprobados localmente. Ocho archivos por caso conservaron tamaño/hash/mtime/modo. No se excluyó una tabla completa. No se publicó contenido privado, nombres/IDs, claves, cookies o SQL en las propiedades.

## Custodia y límites

[Archivo compacto](evidencias/n10-a-groupadmin-autoridad-20261026.tar.gz):26entradas,44929bytes,SHA-256 `ec7b46e28b5106206fc636b0cb5a30fad4c14b362ed86a7000ea33128ff9a418`. Conserva original/candidata, instrumentos/protocolo, auditorías/revisiones y resúmenes de congelación/resultados/imágenes. Excluye logs crudos, credenciales, settings, valores privados, contenido lateral y grafo completo.

Corte antes de validar:2.130fuentes/21.075nodos/86.371relaciones/1.027comunidades,SHA-256 `10478036449c5a108f3954da8844010b0c08db391b6c05d88d8402ad27d2e499`. AST de tres fuentes y semántica475/476/17 selectivos; no reconstrucciónN15 ni semántica exhaustiva. Ruff y gates pertinentes PASS. Lectura propia del módulo y294+237+312líneas de instrumentos; propuestas nativas independientes revisadas, sin pruebas por el escritor. V1nuevo0/histórico8 preservado, consumo nativo desconocido.

La aceptación cubre los destinos/esperas/operaciones declarados. No serializa universalmente cambios posteriores a la última consulta de autoridad ni cada espera through/unique/FK/auditoría. Tampoco es login/TOTP humano, CSRF de navegador, proveedor, despliegue o SLA. Sólo un defecto original de cambio de nombre se reprodujo; las variantes nuevas demuestran la candidata y no son nuevos defectos originales contabilizados.

En paralelo se contrastaron los46comandos con83identidades y133PASSoriginales individuales: [verificación](evidencias/n10-comandos46-verificacion-fuente-20261026.json). Reutiliza18observaciones de collector y cuatro restores con tiempos reales, conservando el run histórico globalERROR y el ámbito de cada modo. No es aceptaciónN10; serialización CLI positiva de operational_snapshot y llamada CLI independiente de configure_rights_evidence_role no se inventan como ejecutadas.

Continuación:N10 completo77IDs y referencias operativas pendientes —arranque actual y límites/propietarios de runbooks/Admin/health/dispatch—; N11/N15 siguen abiertos, N02 residual al final y N12–N14 condicionados. N15 conserva el grafo completo/inventarios/acta y la limpieza final completa de artifacts tras resumen duradero. Mantener15laterales fuera del commit propio, notificaciones yalpha/noindex; objetivo completo no terminado.
