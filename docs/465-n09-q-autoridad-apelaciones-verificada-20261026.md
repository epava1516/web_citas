# N09Q — autoridad de resolución de apelaciones verificada

Estado: dos correcciones de frontera aceptadas localmente; N09abierto139y8/13
bloques obligatorios aceptados. Alpha/noindex. [Prerregistro463](463-n09-q-prerregistro-autoridad-apelaciones-20261026.md)
y[diagnóstico/candidata464](464-n09-q-diagnostico-y-candidata-apelaciones-20261026.md).

Original:20261026-181503-cf56b27f,2PASS/2FAILsinERROR/SKIP,67,801sJUnitQA,
1.784huellas intactas. Tras retirar permiso efectivo durante esperaPGúltima fila,
ambosPOSTupheldresolvían con302ycinco campos modificados; controles legítimos302.
Se conserva elERRORdel runner yelFAILde seguridad. Auditoría confirma mutación
nativa indebida,restantesmodelos/medios iguales ycleanup/TelegramERRORsent.

Candidata:20261026-182417-7be2c8ea,19PASS/0FAIL/ERROR/SKIP,152,685sJUnitQA,
1.785huellas estables. Auditoría independiente propiaPASS: nueve esperasPGreales
ydiez originales funcionales. PostgreSQL17/Redis7.4propios yparsernativo fijado,
runnerfocusedserial. Contenedores exactos ytemporal retirados; recibosTelegram
terminalPASSydeauditoría delivery=sent. No quedan pruebas activas de este lote.

Cambio: appeal_authority recarga Useractual para los dos módulos de apelación,
exige activa/no borrada/MFAhabilitado,permiso efectivo yepochs de sesión/MFA de
actororiginalysu sesión. Mantiene compatibilidad inicial account_versionausente
sólo si versión0,igual al middleware. No refresca request.user borrando sus
valores de admisión. Cada review vuelve a comprobar tras el último Appeal/
PhotoAppealantes de resolver. La alias reviewer_allowedtambién da admisión fresca
aambas colas; el helperglobal de moderation ymatch_review no cambia.

## Antes y después

| Caso | HTTP / campos alterados antes | HTTP / campos alterados después | Cuerpo QA antes → después |
|---|---:|---:|---:|
| Publicación control | 302 / 5 | 302 / 5 | 5.298 → 6.452 s |
| Fotografía control | 302 / 5 | 302 / 5 | 6.679 → 7.363 s |
| Publicación revocada | 302 / 5 | 403 / 0 | 5.227 → 4.273 s |
| Fotografía revocada | 302 / 5 | 403 / 0 | 6.846 → 6.683 s |

Los cinco campos son status,result,reason,reviewer_id,resolved_at; los negativos
conservan fila objetivo ytodos los restantes modelos/medios por hashes. Las
marcas legítimas se comprueban dentro del intervalo. El snapshot anterior incluye
la retirada propia del permiso,commiteada al liberar el holder; no revocación
confirmada en una tercera conexión antes del desbloqueo.

Tiempos de cuerpoQAincluyen preparación/espera/snapshots,caché no controlada yN1;
no latencia normal de app,tiempo humano,p95 oaceleración causal. No comparar por
cociente67,801sde4casos con152,685sde19. Se acepta coste de consultas frescas por
seguridad,sin mejora atribuible de rendimiento ni un presupuesto nuevo inventado.

Cobertura: cuatro esperas originales publicación/foto por control/revocación de
permiso,ycinco nuevas esperas de publicación cambiando sesión,MFAversion,activa,
MFAhabilitado oborrado. PIDdistinto,bloqueo real observado,Userrequestconpermiso
cacheado,intervención efectiva tras bloqueo,403sin efecto en siete negativos,
302con resoluciónexacta en dos controles. Respuestas/conexiones/hilos/holders
cerrados. Las cinco variantes no acreditan otros cinco fallos baseline ni cinco
esperas por fotografía; comparten helper con colocación observada en ambasrutas.

Originales:5test_appealsy5test_photo_appeals, incluyendo cuotas,decisión posterior,
independencia/COI,gestor obsoleto,replay409,resoluciónconcurrente única ypares
recíprocos sin publicación automática. No nuevas pruebas de navegador otransporte
externo. Las funciones de submit/queue/formularios conservan AST; cada review
queda idéntico al original al quitar su única guarda nueva dentro de la transacción.
El cambio de bindingdel helper de admisión es explícito,no se afirma equivalencia
de política sólo por AST. No nuevos locks,writes,esquemas,servicios oCI.

Revisión: escritor nativo aislado sparse propietario sólo del instrumento; root
revisó/fortaleció hashes de otros modelos yflags de resolución para preservar la
causa delFAILoriginal. Revisor independiente yroot verifican lockorder/COI/actor/
epochs/compatibilidad. Dos Ruffprevios fallaron sólo por orden deimports; se
conservaron ycorrigieron antes de congelar,RufffinalPASS. ClaudeV1nuevo0,historial
anterior conservado; consumo nativo desconocido. Propuestas no fueron evidencia
hasta cotejar fuentes,resultados,archivos yrecursos porroot.

Grafo: candidata464con2.112fuentes/20.701nodos/85.472relaciones,SHA
ee6f6b4dddb856f813e0264338d507b6088d46c5d07acbb4b6393ac16e604cf6.
AST de4fuentesysemántica464/17antes de congelar. Refresco terminal465/17selectivo,
sin repetir runtime ni reconstruirN15;111preservado. La base histórica se conserva,
no semántica exhaustiva ni garantía de todos los puntos temporales posibles.

Custodia: [paquete saneado](evidencias/n09-q-autoridad-apelaciones-20261026.tar.gz),
SHA256 `4af37517dad9d2ee0fa2e6008b8fe7ed4205f67472190f73b8de00d7970533ce`,25miembros con manifiesto comprobado;
fuentes originales/candidata,auditorías,revisiones,cortes resumidos yrecibos.
Sin logscrudos,settings,entorno,credenciales,valores privados,grafo completo o
contenidos laterales. Detalle local enartifacts/recorridos-n09-q-20261026/.

Límites: estos dos handlers ysus nueve intercalados; upheld de referencia y
reconsideración en regresiones funcionales,no nueva espera por cada result.
Sin serialización universal frente arevocación posterior ala última comprobación.
moderation.decide/match_review.resolve quedan como incertidumbres de fuente
nombradas para conciliación pertinenteN11; no se les atribuye estePASSni defectos
runtime por inspección. Tampoco se reabre N07global por rutina.

Continuación: terminar139disposiciones ypuentes actualesN09, despuésN10/N11/N15;
N02restante al final,N12–N14condicionados. Se mantienen alpha/noindexycambios
laterales fuera de entrega propia. N15debe resumir fuera deartifactsypurgarla
completamente como última acción obligatoria, aún pendiente.
