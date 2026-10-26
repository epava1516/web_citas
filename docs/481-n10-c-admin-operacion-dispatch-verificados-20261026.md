# N10C — superficies Admin, runbooks y productor conciliados

Aceptación local de referencias y disposiciones seleccionadas, **sin cerrar N10**. Base37ccaaa; [prerregistro480](480-n10-c-prerregistro-superficies-admin-20261026.md), [N10B479](479-n10-b-referencias-operativas-verificadas-20261026.md) y [GroupAdmin477](477-n10-a-groupadmin-autoridad-verificada-20261026.md). Continúan9/13bloques obligatorios aceptados; alpha/noindex.

## Admin: ejecución actual y límites

Run `20261026-214709-7f404800`: **2PASS,56GET,0FAIL/ERROR/SKIP,60.098sJUnitQA**, 1793huellas estables. ES y EN tienen28observaciones cada uno, incluidos seis changelist por idioma. Se comprobaron16patrones Admin por sus recorridos seleccionados: index/app_index, formularios auxiliares, catálogoJS, autocomplete, shortcutGroup404sinURLabsoluta, redirects y catch_all. Login sólo se observa como GET de actor ya admitido; GETlogout405 no prueba logoutPOST. Las escrituras y esperas de Group conservan477, sin repetición.

En cada idioma, cuatro denegaciones403 tras retirar view/change y tres cierres302 para staffretirado/anónimo. Los operadores mantienen add/delete durante la primera fase negativa: esos roles no sustituyen view/change. Las intervenciones intencionadas preceden al snapshot de cada fase, no se presentan como cambios de las peticiones. Estado completo de173modelos y ocho archivos de la fixture preservado, respuestas cerradas y no-store. Autocomplete devuelve sólo el target buscado; changelist contiene el target. Sin espera concurrente nueva, ceremonia password/TOTP, navegador o carga.

| Referencia | Antes | Actual | SQL actual |
| --- | --- | --- | --- |
| Changelist ES primera | Sin medida comparable | 49.497ms |9|
| Changelist ES cinco posteriores | Sin medida comparable | Mediana 29.618ms |9cadauna|
| Changelist EN primera | Sin medida comparable | 39.126ms |9|
| Changelist EN cinco posteriores | Sin medida comparable | Mediana 40.819ms |9cadauna|

El conjunto tiene un Group target fijo, sin variar cardinalidad global. Relojes instrumentados de Client/SQL, no TCP ni latencia universal. Las otras páginas tienen una muestra por idioma; no se inventan percentiles, speedup o nuevo presupuesto. Preparación/oráculos/QA separados del tiempo de petición.

Fuentes, configuración/vendor/documento/grafo e IDs de imágenes congelados antes de ejecutar; PG17/Redis7.4 observados vinculados al PID/start_ticks del runner, iguales a los cacheados. Contenedores y temporal propios ausentes y TelegramPASS entregado. No build, proveedor o modificación de aplicación. Auditoría reprodujo todas las56propiedades contra el XML original SHA `eaa91a466a3416a3bea1b75f2b18d1d1b06a7c4b7e657d1cd2f3cbbd8d695c33`.

## Once procedimientos operativos

Propuesta de un agente nativo de sólo lectura en worktree aislado, taskN10C-runbooks11-source-evidence con14campos y reporte10campos. Root verificó94identidades de fuentes, ubicaciones/AST de funciones y122nodos originales: **120PASS y2SKIP**, no122PASS. Batería original global conserva ERROR/3697PASS/129SKIP/3FAIL. Se reutiliza la evidencia, no se repite por antigüedad o instalación de herramientas.

| Procedimiento | Antes | Disposición actual y límite |
| --- | --- | --- |
| Arranque | Testigos históricos y dos diagnósticos omitidos por guarda | Referencia actual479 de cuatro workers/health; SKIP históricos siguen SKIP. Sin build/stackCompose/medio poblado o nuevo rolruntime. |
| Worker/broker | Dos caídas propias con recuperación de outbox | Primitivas/consumidores pertinentes conservados; no crashmidtask, reboot o HA. |
| Cifrado | Activa/fallback, lectura antigua y escritura nueva | Fuentes equivalentes en alcance; no retiro exhaustivo/recifrado de orígenes externos. |
| Firma Django | Sesiones/recibos/HMAC con cambio de clave | Cuatro funciones rights.py ASTidénticas al original ligado a manifiesto; inspección actual tiene aceptación425 separada. |
| Credencial PostgreSQL | Rotación TCP y reconexión DatabaseWrapper | Fuentes actuales verificadas; no recarga coordinada de flota desplegada. |
| Credencial Redis | ACL/Kombu y recuperación de cola propia | Primitivas verificadas; no hotreload de entorno de Celery desplegado. |
| Secreto proxy | Dos transportes Caddy y clave anterior cerrada/reload real | Mismo contenedor/grant y bytes comprobados en originales; no hotreload backend ni cero interrupciones. |
| Restauración | Cuatro perfiles PGdump/restore/medios con relojes y otro testigo de publicación | Evidencia vigente conciliada en command46; no offsite/PITR ni servir clon por HTTP/worker. |
| Retorno | Ciclo real histórico de tres etapas con726fuentes | Sólo mecanismo histórico. ae33175/37ccaaa tienen753rutas Git no docs/tests/.ai idénticas; no imágenes preparadas/switchactual. |
| Incidente dominio | Revocación de canales con evidencia conservada | AST pertinentes y originales contrastados; no recuperación sin clave, rolloverledger o revalidación transparente general. |
| Retirada urgente | Drills y cierre de superficies públicas | Puente actual de publicación405 con worker/Beat real verificado; no personal/proveedor/SLAreal. |

La tabla distingue primitivas reales, escenario y modos no observados; QA de cada original no es tiempo de operación normal. El arranque y restauración conservan relojes específicos ya registrados en479 y en la verificación de46comandos; no hay antes/después comparable de operación normal para los demás ni mejora atribuida.

**Retorno restringido al corte**: las antiguas imágenes del ciclo5a0751c1→66c6d381→5a0751c1 no se autorizan como retorno de la candidata actual, porque preceden guardas posteriores. La igualdad753incluye mode/type/blob de todas las rutas seleccionadas, no sólo nombres elegidos; el worktree sólo difiere en AGENTS.md entre esas rutas, por instrucciones laterales. DockerCOPYtambién incorpora fuentes docs/tests, así que ni siquiera se infiere digest de imagen idéntico. Una modificación futura de aplicación obliga a reexaminar esta equivalencia; no se concede rollback universal ni se habilita despliegue.

## Dos IDs de dispatch, un productor

Los IDs históricos dispatch8/9 con líneas326/327 se preservan; el AST actual sitúa un único on_commit en337 que captura blob_id y llama process_blob.delay con robustTrue. Root verificó21archivos directos/depruebas idénticos al corteF y once casos originalesPASS. capture_authority añade sólo keywordrecipient_review=False y su rama; tras retirarlos el AST completo coincide con el blob antiguo ligado al manifiesto. Los dos llamadores de execution no pasan ese nuevo flag.

El control original de execute tras espera PostgreSQL produce un callback; al retirar permiso hay PermissionDenied, cero callbacks y estado/archivos sin efecto adicional. Ocho ramas funcionales y el replay completan los once casos reutilizados. Callback reenviado eager no acredita broker/worker nuevo, proveedor o latencia normal de dispatch. No son dos tareas nuevas ni dos créditos de ejecución por los dos IDs.

## Pregunta pendiente antes del cierre N10

La revisión posterior de la entrada nativa Admin identifica una incertidumbre no cubierta por force_login: el LoginView del framework no asigna account_version, mientras AccountGate sólo enlaza automáticamente la versión inicial0. El signin propio sí asigna la versión admitida. **Todavía es una pregunta de fuente, no un fallo runtime confirmado**. Hay que diagnosticar el POST nativo de contraseña con sesiónversion0/1 y comprobar que conduce a MFA conservando la sesión. No cambiar ni debilitar AccountGate por esta observación. Por ello no se acepta el login nativo completo mediante los GET de este lote y N10 sigue abierto.

Evidencia compacta: [archivoN10C](evidencias/n10-c-admin-runbooks-dispatch-20261026.tar.gz), 19miembros/181073bytes, SHA `fe3fa313e33574d897768aba6e96b413bd2a85f1848178ec669d2206def27ff6`. Incluye instrumento, prerregistro, congelaciones, XML/recibo, auditorías root y propuesta nativa marcada como tal, sin logs ni secretos. El primer verificador de propuesta requirió adaptar campos opcionales Caddy, parsingGit conNUL y la estructura anidada del ciclo histórico; se preservan los intentos y recibos locales, sin repetir QA del producto ni alterar evidencia original.

Siguiente: diagnóstico de login nativo; después completar disposiciones77 y salida N10. N11/N15 pendientes; N02residualend por usuario y N12–N14 condicionados. Contrato/objetivo activos.
