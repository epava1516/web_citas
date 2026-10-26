# N09R — conciliación y frontera de inspección de planes

Estado: conciliación139IDs en curso, sin aceptaciónN09 ysin cambios de aplicación.
Base2c9d70c;8/13obligatorios aceptados. [Última corrección465](465-n09-q-autoridad-apelaciones-verificada-20261026.md).

Corte: grafo2113fuentes/20717nodos/85489relaciones,SHA256
4f45abb17d480f6fa64978ecdec212c09b668f7252c2085b4ec956f5d6733540,
manifiesto sin diferencias antes de analizar. La propuesta48asíncronos conserva
21tareas,21declaracionesBeat y6dispatch/cuatroproductores,sin duplicar ejecuciones.
Root contrastará JUnit,fuentes yarchivos originales antes de disponer cadaID.
Comandos/runbooks compartidos conservan N10; sus nombres no acreditan ejecución.

Pregunta concreta: processing_review.current recarga operador tras locked_case,
pero luego espera ProcessingPurposePlan. Record inspect descifra contents antes
su revalidación final. Esta última puede denegar yrevertir la nueva consulta,
pero no deshacer un descifrado ya realizado. El replay exacto retorna contents
antes de esa guarda final. Comprobar ambas ramas antes de aceptar la frontera de
route:R_processing_review; no basta PermissionDenied si hubo acceso privado antes.
No se afirma defecto runtime todavía ni se convierten otras incertidumbres de
fuente en fallos por analogía.

Selección:4casosnativos,new/replay por control/permiso retirado. Fixture existente
test_processing_review.prepared con plan propio de cuenta yrevisor independiente;
permisos actuales,epochs yproof de simulador explícitos,sin proveedor. Oracle de
setup contents obtiene manifest usando current()dentro de transacción ylocks
canónicos; no invocar el helper de cuenta fuera de atomic. En replay crear una
consulta legítima con clave/motivo/versiones exactos antes de los observadores.

Espera: mainretiene ProcessingPurposePlan; workerdistinto llama record(inspect)
yobservador authorize reenvía la implementación real ycaptura permiso cacheado
válido/PIDantes dePlan. Confirmar pg_blocking_pids yworkerbloqueado; sólo entonces
retirar review_processing_plan ycomprobarlo con Userfresh. Commitcon liberación
holder,sin afirmar transición independiente anterior. Contents observado reenvía
la función real yregistra conteos/digests,no plaintext.

Criterios:controlnew retorna bodyexacto ycrea únicamente RightsAction+ProcessingPlanRead
conFK/firmas/proof/plan/source/timestamps/motivo cifrado correctos. Controlreplay
mismoReadPK/body,sin escrituras. Ambos revocados deben PermissionDenied,cero
contentscalls/returns yningún DTOprivado,SQL/medios íntegros. Registrar resultado
real antes de asserts: originalnew podría negar tras descifrar yrollback;
originalreplay podría devolverbodyprivado sin guardafinal. Son hipótesis, no
PASSesperado por un porcentaje oxfail. Conservar cualquierFAIL/ERRORde producto/
fixture yno repetir pruebas válidas de otros consumidores.

Oráculos: todos los modelos instalados/through/sesiones,excluyendo sólo las dos
filas nuevas esperadas en controlnew; snapshots/hash tras la retirada propia y
antes de liberar. Counts de Action/Read,digest/caseversion íntegros,árbol de medios
bytes/mtime/modo estable. Datos nuevos pequeños,IDs/claves/cuerpos sólo en memoria;
evidencia emite bools,conteos,hashes,tipo de resultado yQAelapsed. No HTTP,
broker,worker,proveedor olectura de todo el universo interno acreditados.

Limpieza: workerstatement_timeout10s,future15s,cancelación sólo de su conexión si
timeout,finallycierra conexión/thread/holder con asserts. GuardserialDBpropia/
noPRODUCTION/RECOVERY. Toda prueba/auditoría avisa porTelegram con recibo.
RuffyASTinstrumento+sem466antes de congelar;runnerfocusedserial/parsernativo y
PostgreSQL/Redispropios. Secuencia check=True,no lanzamiento con preflightfallido.

Después:si se confirma,guardafresca antes de privados/replays ytras la espera
seleccionada,conservar transacciones/firmas/efectos/versiones/roles porcaller.
Prerregistrar la regresión afectada antes de aplicar/medir candidata. Si ya es
seguro,aceptar el testigo finito con sus límites. Tabla de estados/conteos ytiempos
QAporpareja,no latencia normal deapp ni mejora causal de rendimiento.

Contexto: la propuesta nativa52de derechos no fue aceptada ciegamente; P/Qya
corrigieron sus fronteras demostradas yesta comprobación nace del contraste de
fuente. Los139IDsno son139tests. N09sigueabierto,N10/N11/N15pendientes,N02restante
al final,N12–N14condicionados,alpha/noindex. Mantener15laterales yla obligación de
limpieza finalartifactsN15,que aún no se ejecuta.
