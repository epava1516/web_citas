# N09B — autoridad actual verificada antes de inspección privada

Aceptación local acotada de la corrección de [424](424-n09-b-correccion-prerregistro-inspeccion-20261026.md), sobre el diagnóstico de [423](423-n09-b-prerregistro-inspeccion-derechos-20261026.md). **N09 sigue abierto,139IDs y8/13bloques aceptados**. Las dos recuperaciones corregidas en [422](422-n09-a-correccion-verificada-recuperaciones-20261026.md) conservan sus29PASSsin repetición. Alfa, sin proveedores, publicación ni apertura.

## Fallo preservado y cambio verificado

Original050131-3251e781:1FAIL/44,683sQA,0ERROR/0SKIP y fuentes estables. Tras observar la espera PostgreSQL real y revocar el permiso antes de liberar el caso, el POST terminó200y creó una nueva auditoría RightsAccess1→2. Solicitud/acciones/estado mínimo no cambiaron. Se preserva el fallo; no se afirma haber observado bytes descifrados, porque el instrumento no los captura.

Sólo cambian `rights.inspect`, un helper local `current_inspection_actor` y la importación de User. Nueva instancia de usuario al entrar y tras `locked_case`, antes de comprobar el ámbito final, descifrar y auditar. Cuenta existente/activa/no borrada, MFA, permiso actual y versiones originales de usuario/sesión deben coincidir. `request.user` pasa a ser el actor actual para los permisos y la auditoría posteriores; los epochs originales capturados permanecen inmutables.403privado/bilingüe sin efectos al denegar.

Revisión Django Expert/Reviewer y comparación AST: `allowed`, los demás handlers/servicios, decoradores y firmas públicas permanecen iguales. Sin lock nuevo de usuario, esquema, migraciones, settings, plantillas, cifrado ni servicios modificados. La garantía es de autoridad actual en esas fronteras, no serialización universal de revocaciones posteriores a la última lectura.

## Evidencia terminal

Lote051032-93877df9: **19PASS/177,341sJUnit,0FAIL/0ERROR/0SKIP**. Selección prerregistrada completa:1espera real+8negativos directos de vista+10originales. PostgreSQL17yRedis7.4propios desechables, serial, parser nativo y recorrido móvil real. Preparación sintética/eager no acredita worker o proveedor.

La espera confirma Lock y PID propio bloqueante, revocación de permiso y liberación antes del403; estado mínimo, solicitud, acciones y accesos íntegros, RightsAccess1→1. Hilo/conexiones cerrados. Los8negativos mantienen el actor original con cachés legítimas y usan la vista real decorada por RequestFactory; cuenta/permiso/MFA/epochs o contexto de sesión revocados terminan403con headers privados y snapshots intactos. Son pruebas de frontera de vista, sin crédito adicional de middleware/transporte/concurrencia.

Los10originales conservan permisos/MFA, acceso auditado sólo enPOST, privacidad de GET, referencias publicadas/no publicadas, conflicto/transferencia, cambio de gestión, cursores de mensajes/respuestas y móvil. Los historiales sintéticos de52elementos se leen en páginas50y2; no se presentan como52comunicaciones externas. El original de cambio de gestión usa interposición controlada; la espera real se acredita por el diagnóstico independiente.

Las1.763huellas quedaron estables (1.760runner+3documentos aparte). Limpieza de contenedores/redes/volúmenes propios y temporal confirmada; recibos Telegram terminal y auditoría enviados. No se repitió QA exportadora larga ni los29casos N09A.

## Tabla antes y después

| Escenario | Antes | Después | Tiempo observado antes → después |
| --- | --- | --- | --- |
| Inspección con permiso revocado durante espera real |200;RightsAccess1→2|403;RightsAccess1→1,snapshots intactos|218,619→157,107msde petición|
| Actor/request obsoleto,8condiciones de entrada |Sin lote previo equivalente|8denegaciones403sin mutación|Sin pareja temporal comparable|
| Diez recorridos legítimos originales |Testigos originales conservados|10PASSincluidos en19actuales|Sin pareja temporal comparable|

Los tiempos de petición incluyen esperas inducidas distintas y ejecución frente a denegación: no son latencia normal ni una mejora causal de rendimiento. La corrección añade consultas de autoridad por seguridad. Los44,683sdel diagnóstico único y177,341sde19casos son QA de selecciones diferentes; no se calcula aceleración entre ellas.

## Custodia y continuación

Resumen saneado: [n09b-autoridad-inspeccion](evidencias/n09b-autoridad-inspeccion-20261026.json). Originales locales: `artifacts/recorridos-n09-b-20261026/baseline-audit.json`, `artifacts/recorridos-n09-b2-20261026/candidate-audit.json`, cortes/fuentes antes/propuestas y `artifacts/local-ci/20261026-051032-93877df9/result.json`/XML. Evidencias versionadas excluyen logs, comandos con credenciales, trazas Settings y contenidos laterales ajenos.

Grafo prerregistro424:2.046fuentes/19.768nodos/83.854relaciones/950comunidades,SHA256 `01f3c51722cf17303f5be03187f822b932f9deee7df81562a4ea2ff34a91cfd7`; AST/semántica/corte verificados antes de medir. El resultado425recibe refresco semántico propio, sin sustituir el rebuild finalN15.

Pendiente: disposición final de139IDs con52derechos/48async/39compartidos; condiciones de autoridad restantes sólo de fuente en hold/inventario/verificación/rectificación/reclamaciones y referencias finitas de purgas/outbox/jobs. Tres defectos N09 han sido corregidos, sin convertirlos en aceptación de todas las familias. N10 mantiene procedimientos compartidos; N02optimización restante al final; N12–N14condicionados. El objetivo general continúa activo.
