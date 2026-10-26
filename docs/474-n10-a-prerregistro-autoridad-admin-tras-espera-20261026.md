# N10A — prerregistro de autoridad Admin tras espera PostgreSQL

Estado: hipótesis de fuente pendiente de diagnóstico; no defecto confirmado ni candidata de producto. Base `b2ed399`, [inventario473](473-n10-inventario-descomposicion-operativa-20261026.md), N10 abierto y 9/13 bloques aceptados. Alpha/noindex. Riesgo de autorización seleccionado antes que el coste de arranque; no se ha implementado ni lanzado ese perfil de arranque.

## Pregunta y selección

Determinar si retirar el permiso efectivo auth.change_group durante una espera SQL de GroupAdmin impide confirmar el cambio de grupo. La fuente instalada de Django5.2.17 comprueba has_change_permission antes de save_model; el guardado nativo puede esperar un Group bloqueado. El middleware del proyecto exige cuenta, documentos y MFA al entrar. Esa lectura de fuente no demuestra el resultado concurrente, por lo que se exigen control legítimo y revocación efectiva durante una espera observada.

ID del censo: `admin_pattern:A_admin:auth_group_change`. Dos casos explícitos, control y revocado, en `tests/test_admin_group_authority_wait.py`; no se agregan todavía altas, borrados o acción bulk. No tocar la aplicación ni Django para obtener el diagnóstico. Las variantes posteriores, si procede, partirán de un defecto probado y se registrarán por separado.

## Datos, actores y operación real

Usar directory y photo_environment nativos con datos sintéticos en PostgreSQL propio. Actor activo no superuser, correo verificado, MFA habilitado; is_staff y permisos auth.view_group/auth.change_group se preparan deliberadamente como datos del caso. Client fuerza una sesión autenticada igual que los testigos nativos, con account_version y mfa_version correctos. No es una prueba de login/TOTP humano, CSRF real, proveedor o navegador.

Un nuevo Group sintético único, sin miembros ni permisos, es el único objetivo. GET nativo del formulario debe devolver200 antes de empezar. POST a `/en/admin/auth/group/<pk>/change/` cambia exclusivamente name; permissions permanece vacío. Deben ejecutarse AdminSite, ModelAdmin, ModelForm, obj.save y auditoría reales, sin sustituir sus permisos, resultados o efectos.

Un observador sobre el método bound save_model del Admin registrado sólo captura actor, caché y PID inmediatamente antes de reenviar al callable nativo. No determina la autorización ni simula la escritura. Confirmar permiso permitido en la petición original, caché calentada y epochs vigentes; no admitir como prueba un403 temprano que nunca llegue al bloqueo.

## Espera, intervención y oráculos

El hilo principal retiene la fila Group con select_for_update. La petición corre en otra conexión propia. Observe_blocked/pg_blocking_pids deben acreditar la espera efectiva y los PIDs distintos. En el negativo se retira sólo el grant directo auth.change_group; un User nuevo debe comprobar que el permiso efectivo ya no existe. La revocación se confirma junto con la liberación del holder, manteniendo sesión/MFA/otros roles. El control no cambia autoridad.

Tomar snapshot completo después de la intervención intencionada y mientras el guardado sigue bloqueado. Así la retirada deliberada pertenece al estado base, no se omite una tabla de permisos para esconder cambios. Comparar todos los modelos instalados/through, auth y sesiones; archivos por contenido, tamaño, mtime y modo. No excluir tablas enteras.

- Control:302, sólo name del Group objetivo y exactamente un AdminLogEntry CHANGE vinculado al actor/Group y dentro del intervalo. Grupo sin miembros/permisos y todo el resto SQL/archivos intacto.
- Revocado:403, Group sin cambiar, ningún nuevo AdminLogEntry ni modificación adicional de SQL/archivos. Una302 con escritura no se interpreta como denegación posterior suficiente.

Antes de la aserción negativa final se conservarán resultado HTTP real, booleano de cambio del nombre, número/validez de entradas de auditoría y forma del delta de snapshot. Si el original falla, el perfil debe permitir distinguir efecto real, problema del instrumento o ausencia de espera, sin convertir el FAIL enPASS.

## Identidad, ejecución y límites

Propiedad JUnit `owned_admin_group_authority_wait`, JSON finito, con contadores, booleanos, hashes y tiempos; sin IDs de sujetos/grants, nombres de grupo, claves, cookies, contenidos de formularios, SQL/parámetros o logs. Las identidades de fuentes e instrumento se fijarán antes de lanzar. El AST del instrumento y la semántica473/474/seguimiento se incorporarán al grafo con corte y alcance explícitos, sin reconstrucción global N15.

Runner oficial focused serial, sólo el archivo de dos casos, PostgreSQL/Redis desechables propios y parser nativo fijo limpio. Capturar antes los IDs de imágenes cacheadas que se usarán con --pull=never. No usar una conexión MCP ni destinos ajenos; no hacer cambios de servicio o migraciones persistentes. Statement timeout y colas/future acotados; liberar holder y cerrar hilo/conexiones en todas las ramas, cancelando únicamente el backend propio identificado si es necesario. No dejar un executor esperando indefinidamente.

Criterio diagnóstico: control válido y revocación observada, fuentes intactas, oráculos y limpieza verificados, FAIL/ERROR/SKIP separados y aviso Telegram terminal con recibo. Un FAIL negativo con control y espera válidos puede confirmar la hipótesis; no se exige que el original salga verde ni se debilita el oráculo para lograrlo. Si se confirma, la corrección y su selección pertinente se prerregistrarán después, preservando los dos diagnósticos originales.

Medidas: tiempo de la petición/cuerpo de caso puede incluir espera inducida, preparación, snapshots o limpieza según el campo declarado. No es latencia normal de Admin ni porcentaje causal de mejora. No hay candidata de rendimiento ni SLO nuevo. El timeout del runner se fija en300s; el caso tiene límites propios mucho menores y se prevé una ejecución de minutos. Notificaciones de pruebas y protocolo de pruebas largas vigentes; no relanzar por perder la observación.

La evidencia de restauración y collector ya localizada conserva su ámbito y no se repite por esta prueba. N10 completo77IDs permanece abierto hasta conciliar el resto y sus acciones operativas; N11/N15 y N02 residual/condiciones mantienen su estado.
