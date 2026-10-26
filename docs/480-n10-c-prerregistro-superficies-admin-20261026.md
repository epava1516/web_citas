# N10C — prerregistro de superficies auxiliares Admin

Estado preparado, no ejecutado ni aceptado. Base37ccaaa; [N10B479](479-n10-b-referencias-operativas-verificadas-20261026.md) y [corrección GroupAdmin477](477-n10-a-groupadmin-autoridad-verificada-20261026.md) preservados. N10 abierto77IDs,9/13bloques obligatorios aceptados; alpha/noindex.

El corte previo al análisis N10C tiene2134fuentes,21149nodos,86501relaciones,1030comunidades y SHA228675861febf99adcd83aacac6baa20f30bbc3279dc1285bc775e274ea06290. Todas las identidades del manifiesto se contrastaron antes de analizar. Semántica selectiva, no reconstrucción N15. Django AI Boost confirmó16patrones Admin y health en su perfil dummy: metadatos, no peticiones ni base real.

## Hueco y selección

N10A acredita escrituras nativas de Group, autoretiro y nueve esperas PostgreSQL, no todas las páginas auxiliares. Se seleccionan dos casos ES/EN en tests/test_owned_admin_surface_reference.py. En cada idioma: index/app_index, login de actor admitido, rechazo GETlogout, formulario/cierre password_change, jsi18n, formularios add/change/delete e historial, redirect legado, catch_all inexistente, shortcut sin get_absolute_url, autocomplete autorizado de Group y seis lecturas de changelist. Total28GET por idioma,56peticiones:21legítimas/auxiliares, cuatro denegaciones de view/change retirados, dos cierres staff y uno anónimo. La mayoría de edad/términos/MFA ya forman parte de la fixture nativa; force_login no prueba ceremonia de contraseña/TOTP.

El target es un Group sintético, separado del operador, que no obtiene permisos ni miembros. Es un conjunto fijo con un target, sin generalización de cardinalidad. La retirada intencionada de view/change precede al snapshot de denegaciones; se conservan add/delete para demostrar que esos roles no sustituyen view/change. La retirada de staff precede al último snapshot. No son revocaciones concurrentes nuevas.

Todos los modelos, incluidas tablas intermedias, y archivos/metadata/hash del MEDIA_ROOT de la fixture se comparan en cada fase. No se excluyen modelos; las únicas mutaciones admitidas son las intervenciones de permisos/staff previas a cada baseline. Ninguna petición debe escribir filas, incluidos sesión, usuario y LogEntry. Responses cerradas, status exactos y no-store. Autocomplete debe devolver sólo el target buscado con ID/text exactos; changelist debe contenerlo. No se exportan nombres, IDs, URLs, contenido ni SQL con valores a propiedades.

## Medición, recursos y aceptación

Cada GET registra tiempo instrumentado completo, número/tiempo de ejecuciones SQL y bytes, sin tiempos de preparación/oráculos. Para changelist se separa primera de cinco posteriores; las demás rutas tienen una muestra descriptiva por idioma, no percentiles. No hay candidato de rendimiento ni nuevo presupuesto, porcentaje causal o SLA.

Runner oficial focused, serial, PostgreSQL17/Redis7.4 propios, parser nativo ya disponible y timeout600s. No build ni carga, conexiones MCP o cambios de servicios. Guardas de propiedad real de contenedor/puerto/base/usuario, no producción ni recovery. Fuentes completas, vendor/config/instrumentos/documentos/grafo e IDs de imágenes se congelan antes; vincular contenedores observados al PID/start_ticks exacto del runner. Grafo focal actualizado para este instrumento y documento antes de ejecutar.

Exigir dos PASS sin omisiones/fallos/errores,56status/cuerpos/headers y oráculos por fase, huellas estables, recursos y temporal retirados, recibo Telegram terminal y auditoría original de JUnit. Revisión propia del instrumento Django/seguridad, Ruff y documentación pertinentes. No repetir N10A16/N10B2 ni testigos de los once runbooks sólo por completar este hueco.

Límites: no POSTlogin/password_change/logout; CSRF y sesión/MFA se reutilizan sólo en su alcance probado, sin inventar ceremonia nueva. No navegador, assets descargados por navegador, widget autocomplete, carga, autorización universal tras cualquier última lectura o tiempo operativo de personas reales. View_on_site sobre Group debe404 porque no define get_absolute_url; no se habilitan redirecciones a recursos privados. Los dos IDs de dispatch de rectificación conservan su identidad de inventario, pero referencian el mismo on_commit/process_blob; se concilian por fuente y evidencia vigente, sin contarlos como dos tareas diferentes.

Los once runbooks se investigan en paralelo de sólo lectura mediante agente nativo autorizado, con propiedad exclusiva de reportes en su worktree previo; propuestas no son evidencia ni aceptación. V1nuevo0/histórico8 preservados, consumo nativo desconocido. La investigación no autoriza QA/builds/servicios ni reutilizar imágenes históricas de rollback sin equivalencia actual. N11/N15 y N02residualend siguen pendientes, N12–N14 condicionados.
