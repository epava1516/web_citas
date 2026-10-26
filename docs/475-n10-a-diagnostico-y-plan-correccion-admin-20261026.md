# N10A — diagnóstico confirmado y plan de corrección de GroupAdmin

Estado: defecto finito confirmado, corrección pendiente de validar. N10 sigue abierto, 9/13 bloques aceptados; alpha/noindex. Base `b2ed399`, [prerregistro474](474-n10-a-prerregistro-autoridad-admin-tras-espera-20261026.md).

## Resultado original

Run `20261026-202925-4860b46d`: **1 PASS/1 FAIL, 55,892 s JUnit de QA**, sin ERROR/SKIP de pytest; ERROR terminal del runner por el caso fallido. Las1.788huellas, fuentes adicionales de Django/middleware, documentos y grafo permanecieron intactos. IDs de imágenes congelados antes y comprobados automáticamente en los contenedores vivos del runner identificado por PID/start_ticks. Recursos propios y temporal retirados, Telegram ERROR y auditoría entregados.

Ambos casos llegaron al save_model nativo con permiso permitido y cacheado, sesión/MFA válidos y espera PostgreSQL real sobre Group, con conexiones distintas. En el revocado se retiró únicamente el grant directo auth.change_group y la revocación se confirmó junto con la liberación del holder. Un User nuevo confirmó el permiso efectivo retirado; los demás atributos de actor, membresías y sesión siguieron intactos.

El control devolvió302 y confirmó exactamente name del Group más un LogEntry CHANGE válido. El negativo hizo lo mismo:302, nombre solicitado y una entrada de auditoría. El snapshot completo de173modelos sólo mostró ese efecto nativo; ocho archivos permanecieron iguales. Se demuestra una modificación administrativa después de la retirada efectiva del permiso, **no una escalada de privilegios o alteración de membresías**: el Group objetivo estaba vacío y sin permisos. El original fallido se conserva, junto con el instrumento de294líneas byteidéntico.

| Caso original | Resultado | Efecto | Tiempo del cuerpo QA, s |
| --- | --- | --- | ---: |
| Control autorizado | 302, PASS | Sólo name + un CHANGE LogEntry | 7,434 |
| Permiso retirado durante espera | 302, FAIL | Mismo cambio confirmado pese a permiso efectivo false | 6,217 |

Son tiempos con espera inducida/preparación/snapshots/limpieza, no latencias normales de Admin ni comparación de rendimiento.

## Causa y variantes de fuente

GroupAdmin usa ModelAdmin: has_change_permission consulta la caché legítima de request.user antes del guardado; obj.save espera la fila y luego confirma sin una guarda actual de autoridad después de la espera. La transacción conserva integridad de la operación pero no actualiza por sí misma la autoridad del operador.

El análisis acotado de fuentes identifica también add, permisos M2M, delete y delete_selected; sólo el cambio de nombre tiene aquí reproducción runtime. Change/add y delete individual ya tienen una transacción nativa que incluye auditoría. Delete_selected registra LogEntry antes de llamar a delete_queryset y no tiene una única transacción exterior que abarque todo: una guarda tardía en delete_queryset sin envolver la acción podría dejar auditoría confirmada pese a denegar.

Una guarda incondicional después de los efectos tampoco es una solución compatible: un actor autorizado puede eliminar deliberadamente el permiso de su propio grupo o borrar el grupo que se lo concede. Rechazar porque después carece de ese permiso impediría una operación legítima. Además, los mensajes en memoria no se revierten automáticamente con SQL. No se adopta ese veto posterior ni una excepción amplia para cualquier edición del grupo propio.

## Corrección elegida antes de aplicar

Registrar en `apps/core/admin.py` una subclase del GroupAdmin actual, preservando formularios, selección M2M, permisos/formato nativos, URLs, auditoría y etiqueta/permiso de delete_selected. El proyecto sólo registra el modelo Group en esta superficie; core.User está intercambiado y no hay otros registros propios actualmente. No editar site-packages, desactivar Admin o reducir las operaciones válidas.

- En save_model de un cambio, adquirir primero el Group existente; después consultar un User nuevo con los epochs originales de request.user y de la sesión, estado activo/staff/correo/MFA/no borrado y permiso efectivo de la operación. Delegar el guardado nativo. Para add, comprobar autoridad actual antes del guardado sin inventar una fila existente que bloquear.
- En save_related, volver a comprobar antes de la modificación M2M, conservando add/change y sin veto posterior a una auto-retirada autorizada. No reemplazar el User original por el actualizado ni adoptar sus epochs nuevos.
- En delete_model y delete_queryset, adquirir los Groups objetivo en orden PK antes de la guarda actual; conservar la eliminación y el collector nativos. Un objetivo individual desaparecido no se recrea.
- Envolver delete_selected en una transacción de toda la acción, incluida su auditoría, y delegar al callable nativo con la misma etiqueta y permiso. La guarda después de adquirir objetivos debe preceder a la eliminación; una denegación revierte también el LogEntry previo. No añadir mensajes de éxito fuera del flujo nativo.

Las transacciones y los locks pertenecen sólo al destino configurado del proyecto. No bloquear User/grants del operador, introducir una nueva política de roles, cambiar modelos/migraciones/settings o modificar servicios. La adquisición de Group mueve la espera demostrada antes de la decisión de autoridad. No representa serialización universal de cambios de permisos después de la última comprobación.

Límites expresos: otros locks de filas through/Permission, conflictos de unicidad, FK o auditoría posteriores a la guarda no quedan acreditados por una prueba del Group objetivo. Son candidatos de fuente, no defectos runtime adicionales demostrados. La corrección no se anunciará como garantía de toda intercalación SQL; las variantes medidas y las operaciones legítimas deben quedar identificadas.

## Validación propuesta

Conservar los dos diagnósticos originales sin cambiar sus bytes, datos o expectativas. Añadir, en archivos separados, esperas nativas de borrado individual/masivo —control y permiso retirado por operación— y tres cambios tardíos representativos en el cambio de Group: session_version, mfa_version e is_staff. Deben llegar autorizados a la espera real y después denegar sin efectos adicionales; la mutación intencionada del actor pertenece al snapshot base.

Preservación funcional: add con permisos mínimos de alta, edición de permisos, borrado individual y masivo, más retirada del propio change_group a través de Group.permissions y borrado individual/masivo del único grupo que concede delete_group. Las operaciones propias deben confirmar, retirar el permiso efectivo y no impedir la retirada deliberada; la siguiente operación exige los permisos actuales. Comprobar exactamente Group/through/LogEntry, padres/resto del dominio, sesiones y archivos. No equivaler Group read-only GET permitido a autorización de POST.

Selección prevista: **16casos** —dos originales, siete variantes de espera y siete controles CRUD/semántica propia—, sin repetir comandos, restores, capacidad o campañas N09. Se precisarán los selectores, huellas y condiciones finales antes del lanzamiento, con nuevo corte AST/semántico y congelación. Los resultados originales y cualquier fallo de instrumento se conservarán separados; no se debilitan oráculos. No hay candidata de rendimiento ni un porcentaje de mejora que demostrar.
