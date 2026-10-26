# N09F — autoridad de rectificación verificada localmente

Aceptación técnica local de diez fronteras de operación, tras [435](435-n09-f-preparacion-rectificacion-autoridad-20261026.md), [diagnóstico436](436-n09-f-diagnostico-y-plan-correccion-rectificacion-20261026.md) y [prerregistro437](437-n09-f-prerregistro-validacion-autoridad-rectificacion-20261026.md). **N09 completo sigue abierto:139IDs,8/13bloques obligatorios aceptados**. Alpha/noindex, datos sintéticos, sin proveedor real ni apertura.

## Diagnóstico y cambio aceptado

El original `20261026-095759-1cba6827` conserva20casos:10PASS/10FAIL,236,664sJUnit,0ERROR/SKIP. Diez controles legítimos y diez esperas PostgreSQL con PID/Lock/bloqueante y retirada confirmada antes de liberar. Nueve servicios produjeron efectos después de revocar y el GET de foto devolvió200con9.558bytes privados sintéticos. Las1.772huellas, limpieza y avisos Telegram del original quedaron auditados; no se borró ni reinterpretó el FAIL.

Siete fuentes de aplicación: nuevo rectification_authority.py y cambios en rights_rectification, rectification_uploads, rectification_review, rectification_execution, rectification_recipients y rectification_account. Captura de pk/epochs originales antes de los bloqueos y recarga explícita de User activo/no suprimido, MFA, sesión, permisos y ámbito. No se bloquea al operador ni se adoptan epochs nuevos después de la espera.

Base review_rights_request+execute_rights_request; review_rectification adicional para revisión/inventario y respond_rights_request adicional para notify/execute. Los callbacks conservan los permisos completos del llamador a través de current y source_snapshot. Guardas antes de replay y efectos y después de bloqueos canónicos, Proposal/Review/Notification/Upload/Blob.

La captura de cuenta comprueba autoridad después del User objetivo y antes de la proyección privada. Upload/Blob/Rate/Photo separan bloqueo ordenado de identificadores y materialización de metadatos, con comprobación intermedia. Se preservan orden User→Revision→Uploads→Blob→Rate/Photo, representación/digest y semántica de include_uploads/additional_blob_ids. PhoneClaim se prebloquea en el punto original previo a binding; account.apply revalida tras EmailConfirmation y execute tras contacts.claim antes de guardar Person. Los helpers sin callback conservan sus consumidores separados y no reciben aceptación global por esta corrección.

Revisión propia de diferencias, callers, roles, epochs, proyecciones y orden de bloqueos antes de integrar; se retiró un check consecutivo redundante de execute. RuffPASS y recibos comprobados. Los veinte diagnósticos originales siguen byte a byte idénticos,527líneas/SHA2358c9317c343c55378d1dea6596777c612c844a6122443ff581bab032c83a0d. Sin cambios de modelos, migraciones, settings, servicios, plantillas o dependencias; no se ejecutaron escaneos activos por instalar herramientas.

## Validación y auditoría completas

Run `20261026-102707-99847d71`: **75PASS,0FAIL/ERROR/SKIP;1.035,569sJUnit —17min15,569s—**. Selección exacta de30selectores,1.776huellas congeladas antes/durante/después (runner+cuatro documentos manuales). PostgreSQL/Redis propios desechables, parser nativo, serial. Contenedores/redes/volúmenes del run y temporal ausentes al auditar. Telegram terminalPASS y auditoríaPASS enviados y recibos comprobados.

- **Veinte diagnósticos íntegros**:10controles legítimos con los mismos conjuntos de tablas y deltas esperados que el original;10revocaciones con PermissionDenied o HTTP403, dominio/estado mínimo/archivos idénticos, cero retornos privados después de revocar, cero intentos de delay y cero bytes. Veinte esperas reales/PIDs/bloqueantes, hilos/conexiones cerrados. GET de foto403privado, respuesta cerrada; control200con los mismos9.558bytes sintéticos.
- **Once regresiones nuevas**:4preview con instancia original ante sesión/MFA incrementadas, cuenta inactiva o MFA deshabilitado;7replays tras primera operación legítima y revocación, con clave/payload/version originales (propose/upload/discard/review/notify/execute/recipients). Denegación y snapshots de dominio/archivos íntegros, sin retornos privados/callbacks. Son servicios nativos sin nueva espera acreditada y no once defectos baseline adicionales.
- **44originales sin editar**:18fuente/campos/medios,4cuenta/orden de bloqueos,8uploads,10revisión/comunicación/ejecución,2cuenta sin perfil y2inventario de destinatarios de cuenta con/sin email. Conservan digest/drift, edición, proof expiry, fuente auditada, idempotencia/concurrencia, aprobación/rechazo, comunicación/acuse y ámbito. Los relojes/interposiciones de originales no equivalen a las20esperas reales.

Auditoría reproducible local: `artifacts/recorridos-n09-f-20261026/candidate-audit.json`, con los75casos y comparación de cada control/negativo contra el original. Delay observado reenvía al callback eager real; no es prueba nueva de broker/worker o proveedor. Sólo source_photo de los20diagnósticos acredita HTTP; los otros nueve son servicios nativos. Las regresiones originales conservan sus superficies propias.

## Antes y después, con tiempos observados

Una muestra por caso. Los tiempos son del cuerpo del caso QA, incluyendo preparación, espera inducida, snapshots y limpieza, **no latencia normal ni mejora causal de app**. El totalJUnit incluye además setup/teardown. Los controles permiten comparar el mismo recorrido legítimo, sin convertir una muestra en benchmark.

| Operación | Antes tras revocar | Después tras revocar | QAcontrol antes→después, s | QArevocación antes→después, s |
| --- | --- | --- | ---: | ---: |
| preview | Retorno privado/+SourceRead | Denegado, snapshots intactos |8,408→8,580|7,713→7,053|
| propose | +Proposal/Action/versión | Denegado, snapshots intactos |7,772→8,617|8,128→7,834|
| source_photo | HTTP200/9.558bytes | HTTP403/0bytes, cerrado |8,451→10,261|8,085→9,848|
| upload | +Revision/Photo/Upload/Action/callback | Denegado, snapshots intactos |9,439→10,999|9,513→9,614|
| discard | discarded_at/+Action | Denegado, snapshots intactos |8,922→10,752|9,253→9,790|
| inspect | Retorno privado/+ProposalRead | Denegado, snapshots intactos |8,893→10,828|8,145→9,887|
| review | +Review/Action/versión | Denegado, snapshots intactos |8,575→11,711|9,478→10,754|
| notify | +Notification/Response/Notice/Action/versiones | Denegado, snapshots intactos |10,743→13,319|9,078→13,030|
| execute | Perfil/anuncio corregidos/+Execution/respuesta/callback | Denegado, snapshots intactos |11,728→16,640|10,585→15,482|
| recipients | +Inventario/Action | Denegado, snapshots intactos |11,230→15,716|11,065→14,881|

Hay consultas adicionales para revalidar autoridad y separar bloqueo/proyección. No se atribuye causalmente el incremento observado a una única causa ni se declara mejora de rendimiento.236,664sde20casos frente a1.035,569sde75son selecciones distintas: no se calcula aceleraciónQA entre ellas. La optimización generalQA y N02restante siguen aplazadas según lo acordado.

## Custodia, grafo y límites

Resumen saneado: [autoridad de rectificación](evidencias/n09f-autoridad-rectificacion-20261026.json). [Paquete reproducible acotado](evidencias/n09f-rectificacion-reproduccion-20261026.tar.gz) y su [manifiesto](evidencias/n09f-rectificacion-reproduccion-20261026.manifest.json): originales negativos, auditorías, selección, cortes/huellas y revisiones saneadas; sin logs, Settingsrepr, comandos/credenciales, plaintext/ciphertext, contenidos de instalaciones laterales ni grafo completo.

Corte437previo a congelar:2.071fuentes/20.110nodos/84.138relaciones/970comunidades,SHA3da1a90056df533bc36ba8e2356ab200de9a335086d3b02a2cdfdbfcbae77e7b. Delta AST de ocho fuentes y semántica selectiva436/437/17 validados;438recibe su refresco terminal, sin reconstrucciónN15 ni semántica exhaustiva. La custodia no convierte documentación en evidencia runtime independiente.

La conciliación documental de139IDs enlaza20con testigos locales parciales A–F,15deellos con fuentes directas A–E todavía idénticas; **ningún ID se acepta íntegro por esa anotación**. Son diez fronteras F sobre cinco rutas del censo. Las16correcciones locales A–E y estas10suman26puntos de corrección de operación/frontera, no26causas raíz independientes, IDs o bloques aceptados. N09E38PASS se conservan sin repetir.

Los contadores no demuestran ausencia exhaustiva de toda proyección interna; User/Revision ORM se obtienen al bloquear y la guarda precede a la proyección explícita. El primer wait de upload/discard dentro de source_snapshot no prueba aisladamente sus últimos locks explícitos. No hay serialización universal frente a revocación posterior a la última lectura de autoridad, ni prueba nueva de atomicidad de archivos ante todos los fallos físicos.

Pendientes con disposición propia: rectification_final.evidence y otros consumidores sin callback; ramas tardías de cuenta/email/contactos/catálogos/medios no observadas en las20esperas; purgas/outbox/jobs finitos y conciliación completa139IDs. Las pruebas funcionales de esas ramas no se reclasifican como revocación concurrente. N02restante al final/N10N11N15pendientes/N12–N14condicionados. El objetivo completo sigue activo, alpha/noindex.
