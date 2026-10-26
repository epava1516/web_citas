# N09Q — resolución indebida confirmada y candidata de apelaciones

Estado: dos fronteras reproducidas, candidata pendiente de aceptación. N09abierto
139y8/13obligatorios aceptados. [Prerregistro463](463-n09-q-prerregistro-autoridad-apelaciones-20261026.md).

Original: run20261026-181503-cf56b27f,2PASS/2FAILsinERROR/SKIP,67,801sJUnit;
runnerERRORpreservado y1.784huellas estables. Ambos controles legítimos302resuelven
sólo cinco campos de la apelación. Ambos revocados también302,con statusresolved,
resultupheld,revisor/motivo exactos ycinco campos alterados frente al403exigido.
Se acredita espera realPGúltima fila, permiso de Userrequestcacheado yretirada
efectiva de Userfresh,commiteada con liberación del holder. Todas las restantes
filas/modelos ymedios invariantes; auditoría distingue mutación indebida deERROR
de fixture. Contenedores/temporal ausentes yTelegramERROR/deauditoría enviados.

Causa: la guarda de admisión sobre request.user no se recargaba tras locks de
alcance yAppeal/PhotoAppeal. COI/estado no sustituyen permiso vigente. El resultado
upheld usado no reabre Match/Revision ni publica; el defecto demostrado es resolver
la apelación sin permiso actual, no una publicación indebida ya observada.

Candidata: nuevo módulo appeal_authority con guardafresca compartida sólo por
appeals/photo_appeals. Recarga User, exige activa/no borrada/MFAhabilitado, permiso
efectivo yversiones de sesión/MFA coincidentes con actor original ysesión. Conserva
compatibilidad de sesión inicial sin account_version cuando la versión es0,
igual al middleware. No mutar request.user ocopiarle versiones nuevas, que borraría
la referencia de admisión. Cada handler vuelve a llamarla tras su último lock
Appeal/PhotoAppeal yantes de comprobar estado/escribir. La alias reviewer_allowed
se conserva para observación reenviada; las dos colas reciben también admisión
fresca por el import compartido. El helperglobal de moderation no se modifica.

Preservación: actor/FK,COI/independencia,orden Agency/Person/Listing/Revision/Match/
Appeal,cuotas,versión ysuperseded,state/replays,reason yredirects originales. Sin
nuevos locks,writes,esquemas,servicios oCI. Consultas adicionales por seguridad;
no prometer latencia menor oserialización universal después de la última lectura.
Revisor nativo independiente confirma AST de ambos handlers equivalente al de
812b2b7al retirar únicamente la guarda añadida; root verifica antes de aceptar.

Selección candidata:19casos previstos. Cuatro diagnósticos originales de espera
(publicación/foto por control/permiso retirado),cinco variantes adicionales de
publicación cambiando sesión,MFAversion,activa,MFAhabilitado oborrado durante la
misma espera real,y10originales funcionales de test_appeals/test_photo_appeals.
Las cinco variantes no son otros cinco defectos baseline acreditados; el helper
es compartido ysu colocación en fotografía se observa con la retirada de permiso.
No afirmar cinco nuevas esperas por fotografía ni nueva prueba de navegador.

Oráculos: los nueve diagnósticos mantienen fullSQL/medios yúltima fila; controles
sólo cinco campos302,negativos403sin efectos. PIDdistinto,cachecalentada,
intervención confirmada antes de liberar,conexión/hilo/response/holder cerrados.
Los diez originales conservan idempotencia,independencia,cuotas,decisión posterior,
pares recíprocos,sin publicación automática yconcurrencia. Criterio19PASSsin
ERROR/FAIL/SKIP,fuentes intactas,limpieza independiente yrecibosTelegram.

Medidas: comparar estados/deltas yQA de los cuatro pares,una muestra/caso con
preparación/espera/oráculos; sin latencia normal de app,tiempo humano,p95 oaceleración
causal. No dividir67,801sde4casos entre el total futuro19. Conservar fallos
originales. No repetir pruebas ajenas a estas guardas por pertenecer a N07/N09.

Gates: Ruffacotado,AST de tres fuentes de app ydel instrumento mássemántica464/17;
congelación estricta check=True,runnerfocusedserial/parsernativo/PostgreSQLRedis
propios. Auditoría por caso/campos/hash/limpieza/Telegram antes de aceptación.
El caso heredado de sesión inicial0 permanece; valores no0sin credencial vigente
no obtienen compatibilidad. Toda modificación posterior obliga a reconciliar
fuentes antes de una medición nueva, sin reconstrucciónN15innecesaria.

Límites: dos handlers ysu helper,fivecamposupheld/control yvariantes nombradas;
no cobertura universal de moderation.decide/match_review.resolve ni revocación
posterior a la guarda. Esas dos fuentes quedan como incertidumbres nombradas
para conciliación pertinente N11, no defectos runtime oejecuciones autorizadas
por este documento. No reabrir N07global por rutina.

Continuación:139disposiciones,N10/N11/N15;N02restante al final,N12–N14condicionados.
Alpha/noindex,sin proveedor oapertura. Limpieza completaartifactscomo última acción
obligatoriaN15 aún pendiente;15laterales preservados fuera de la entrega propia.
