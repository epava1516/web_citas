# N09R — acceso privado tardío confirmado y candidata de procesamiento

Estado: defecto finito confirmado,candidata pendiente. Conciliación139IDs con
126verificadosconlímites en borrador,12compartidosN10y1pendiente de corrección;
ninguna aceptaciónN09por el simple censo.8/13obligatorios,alpha/noindex.
[Prerregistro466](466-n09-r-prerregistro-frontera-plan-procesamiento-20261026.md).

Original:20261026-190208-b39509bf,2PASS/2FAILsinERROR/SKIP,77,902sJUnitQA,
1.786huellas intactas. Las cuatro operaciones esperan realmente Plan conPIDs
separados yoperador autorizado/cacheado inicialmente. Tras retirar permiso al
liberar el holder,contents real se invoca yretorna una vez en ambos negativos:
new termina PermissionDeniedconrollback,pero ya descifró;replay devuelve el
Readexistente ybodyprivado. Todos los hashes SQL/medios permanecen iguales en
los negativos,por lo que su integridad no demuestra confidencialidad. Controles
new/replay correctos;recursos/temporal retirados yTelegramERROR/auditoría enviados.

Causa: current()comprueba actor después del alcance canónico,antes del lockPlan.
La guarda final de record no precede contents yla rama de replay retorna antes
de esa guarda. Una PermissionDeniedtardía no revierte el acceso privado ya hecho.
El diagnóstico invoca servicios nativos ycontentsreenviado; no prueba HTTP.

Candidata: dos líneas en processing_review.py. Tras adquirir Plan válido,current()
repite authorize con useroriginal,caseyel mismo review_permission. Antes de
contents en la rama nueva,record repite authorize; su guarda final se conserva.
No cambiar authorize/contents,epochs originales,rolesFalse de ejecución,claves/
firmas,FKoestados,transacciones yorden de locks. Denegar antes de privados yno
sólo antes de commit; sin nuevos locks,writes,modelos,vistas,servicios oCI.
Revisión independiente yroot sin bloqueantes en el diff,propuesta no runtime.

Selección candidata:10casos. Cuatro diagnósticos originalesbyteidénticos,new/replay
por control/revocado,mismos oráculos. Tres originales de test_processing_review
(inspección/revisión/replayHTTP,drift/cifrado,pendingrechazable) ytres de
 test_processing_execution (ejecutor con review_permissionFalse,preservar
favoritos,bloquear uso ordinario,fines no soportados yborrado restringido). Son
regresión por las funciones modificadas; processing_final usa contentsintacto
por política independiente yno hereda estePASSni necesita una campaña adicional
por este diff. No repetir I–O ni otros consumidores ya válidos.

Criterio:10PASSsinFAIL/ERROR/SKIP. Dos negativos con PermissionDeniedantes de
contents,cero calls/returns/DTOprivado ySQL/medios/case intactos. Controlnewcrea
sóloAction+ReadconFK/firmas/timestamps correctos;controlreplaymismaPK/body,sin
escrituras. Fuentes congeladas,oráculos,conexiones/hilos/holder cerrados,contenedores
ytemporal ausentes,recibosTelegramconfirmados. No garantía universal después de
la última comprobación,ni exhaustividad de toda proyección privada interna.

Medidas: cuerpoQAincluye saga nativa,espera,snapshots/cleanup; mostrar por pareja
antes/después con unidad,muestra1ysin aceleración causal deapp. No comparar
77,902sde4casos con totalfuturo10como mejoraQA. Consultas adicionales se aceptan
por seguridad,no como optimización temporal. Las métricas normales de estas rutas
siguen sin nueva referencia comparable; no inventar un antes/después de latencia.

Preparación: root corrigió oracle de cuenta para usar current()dentro de
transacción canónica antes de ejecutar el original; no hubo unERRORde fixture
aceptado como defecto. RuffPASS,AST del módulo de aplicación ysemántica467/17
antes de congelar,codigo del diagnóstico intacto. Runnerfocusedserial/parser
nativo/PostgreSQLRedispropios,check=True. Auditoría terminal específica antes de
aceptación. Preservar el original2FAIL,sinxfail ni nuevos umbrales.

Conciliación: root contrastó52derechos,48async/JUnit/archivos/funciones y39compartidos.
Nueve purgas simples no reciben latencia prestada de CopyInformation; Beat es
declaración,no ejecución de cadencia. El caso Plan impidió aceptar ciegamente la
propuesta52. Después de corregir se terminarán los139estados con límites/propietarios,
sin cambiar aPASS los12comandos/runbooks que pertenecen operativamente aN10.

Continuación:N09abierto,N10/N11/N15pendientes,N02restante al final,N12–N14condicionados.
Preservar15laterales,alpha/noindexylimpiarartifactscompletamente sólo como última
acción obligatoriaN15tras resumen duradero,procesos ydependencias resueltos.
