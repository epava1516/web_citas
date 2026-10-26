# N09D — autoridad verificada en reclamaciones y levantamiento

Aceptación técnica **local de seis correcciones**, sobre cinco rutas del censo; no cierre de N09. Diagnóstico [429](429-n09-d-prerregistro-reclamaciones-levantamiento-20261026.md), plan anterior al cambio [430](430-n09-d-correccion-prerregistro-reclamaciones-levantamiento-20261026.md), base `f65a530` en master. Se mantienen alpha/noindex, datos sintéticos y ausencia de proveedores reales.

## Requisito, cambio y evidencia

Permisos, estado de cuenta, sesión y MFA vigentes antes de acceder a contenido privado o producir efectos, también después de esperar locks PostgreSQL. El run original `20261026-062847-a8dd3f53` conserva **6 FAIL/87,487 s JUnit**, sin ERROR/SKIP, 1.767 huellas estables, limpieza y Telegram confirmados. Auditoría separada confirmó cada espera, PID bloqueante propio, revocación confirmada antes de liberar y efecto contrario al403esperado. No se atribuyó un fallo instrumental al producto.

El candidato `20261026-065607-548db09c` terminó **117 PASS/1.052,177 s JUnit** —17min32,177s—, cero FAIL/ERROR/SKIP. Auditoría independiente completa: 1.770 huellas verificadas antes de la documentación terminal (1.767runner+3documentos), selección exacta, cleanup y Telegram terminal/resultado de auditoría confirmados. Runner oficial serial con PostgreSQL/Redis propios desechables y parser nativo; no MCP de base dummy ni simulación de base como prueba real.

Cinco archivos de aplicación: nuevo `complaint_authority.py`, y cambios en `complaints.py`, `complaint_actions.py`, `complaint_resolutions.py`, `privacy_release.py`. Captura inmutable de epochs originales y nueva instancia User en admisión y después de locks, antes de replay, auditoría, descifrado, apertura de archivo o escritura. Exige cuenta activa/no borrada, MFA, epochs originales y permisos de operación actuales. Las dos vistas afectadas comprueban además account_version/mfa_version de sesión y usan request.user fresco para privilegios de fuente.

Act mantiene review_complaint, manage_complaint_assignment para unassign y resolve_complaint para reassess, además de scope/source_permission existentes. Resolve exige review_complaint+resolve_complaint y conserva independencia, ámbito, fuente/versiones, lectura completa de imágenes y redacción. Propose/execute exigen los cuatro permisos review_rights_request/execute_rights_request/review_privacy_hold/respond_rights_request después del último Hold o Proposal/Hold, manteniendo independencia, ACK y nueva prueba posterior, bindings y publicación pausada.

No se cambian modelos, migraciones, formularios, decoradores, settings, servicios ni otras funciones de esos módulos. AST de entidades ajenas al cambio idéntico, con imports/helpers nuevos explícitos. Los instrumentos429, observador419 y los nueve módulos originales permanecieron byte a byte intactos. Revisión propia Django/seguridad/diferencial documentada localmente en `artifacts/recorridos-n09-d-20261026/DIFFERENTIAL_REVIEW_20261026.md`; su recomendación previa condicional se resuelve con esta evidencia runtime, sin certificar seguridad global.

## Selección y oráculos comprobados

- **Seis esperas HTTP reales**, cinco POST y un GET: inspección no enlazada, foto de revisión rechazada, claim, resolución de listing rechazado, propuesta y ejecución de levantamiento de restriction. En todas, bloqueo PostgreSQL observado antes de retirar permiso, confirmación de revocación antes de liberar,403y tablas/estado mínimo intactos; hilos y conexiones cerrados. El GET denegado no es streaming, entrega cero bytes de imagen y cierra respuesta. El baseline200entregó10.314bytes locales sintéticos, sólo longitud/hash preservados.
- **44 negativos de entrada**: inspect6, photo7, claim6, resolve7, propose9, execute9. Actor/caché legítimos previos y mutaciones ORM externas de permisos/cuenta/MFA/epochs; respuestas403en vistas o PermissionDenied en servicios, snapshots intactos. RequestFactory de vistas no acredita middleware, transporte ni concurrencia adicionales; esos ámbitos se separan de las seis esperas reales.
- **Cuatro replays revocados** de claim, resolve, propose y execute. Primero efecto legítimo comprobado y conservado como referencia; después revocación y repetición de clave/payload originales, PermissionDenied y snapshots idénticos a esa referencia. No basta que el replay no escriba.
- **63 regresiones originales**: intake13, assignment5, linking5, listing_linking6, resolutions10, messages13, localization2, resolution_localization2, privacy_release7. Conservan recorridos legítimos, CSRF, COI/historial/transferencia, foto ajena, lecturas auditadas y versiones, replays y concurrencia, ES/EN y móvil. No se suman a ejecuciones anteriores como si fueran una batería integrada distinta.

## Tabla antes y después

Muestra temporal de una petición por escenario, cada una con espera inducida; base frente a ejecución denegada, no latencia normal ni mejora causal. Se consignan los tiempos disponibles sin porcentajes atribuibles.

| Acción tras revocación | Antes | Después | Petición antes → después |
| --- | --- | --- | ---: |
| Inspección de reclamación |200; acceso auditado nuevo|403; dominio intacto|223,083 →223,981 ms|
| Foto enlazada, GET |200;10.314bytes y acceso nuevo|403;0bytes de imagen, respuesta cerrada|121,502 →232,599 ms|
| Claim |302; acción y expediente modificados|403; dominio intacto|111,182 →207,517 ms|
| Resolución de listing rechazado |302; resolución/aviso/fuente modificados|403; dominio intacto|646,690 →207,150 ms|
| Propuesta de levantamiento |302; propuesta/respuesta/aviso creados|403; dominio intacto|471,644 →254,140 ms|
| Ejecución de levantamiento |302; medida desactivada/publicación modificada|403; dominio intacto|446,458 →191,542 ms|
|44negativos y4replays |Sin lote equivalente anterior|48denegaciones,snapshots intactos|Sin pareja comparable|
|63originales legítimos |Testigos conservados|63PASSdentro de117|Sin pareja comparable|

Las consultas adicionales son coste de seguridad. QA87,487sde6diagnósticos frente a1.052,177sde117casos son selecciones distintas; no acreditan aceleración ni regresión causal de tiempo de aplicación o QA.

## Límites y continuación

No se bloquea el operador ni se promete serialización universal frente a una revocación posterior a la última lectura de autoridad. Intake sin privilegio de fuente conserva su acceso legítimo al intake, sin imágenes ni evidencia de fuente. El diagnóstico de resolución sólo ejercita listing; la regresión funcional de report no se presenta como otro caso de revocación concurrente. La rama report conserva su servicio y locks propios.

Los levantamientos nuevos ejercitan realmente restriction y pruebas del simulador, sin identidad ni proveedor reales. El fixture original `prepared(kind)` fija restriction aunque tres etiquetas paramétricas indiquen restriction/object/rectify; se conserva sin editar y no se acredita cobertura de tres tipos por esas etiquetas. La imagen fue servida localmente, no se acredita proxy/objeto externo con ese caso.

Resumen saneado: [n09d-autoridad-reclamaciones](evidencias/n09d-autoridad-reclamaciones-20261026.json). Originales locales: baseline/candidate-audit, candidate-freeze, revisión de fuentes, correspondencia de cinco IDs/seis operaciones y run/XML en `artifacts/recorridos-n09-d-20261026/` y `artifacts/local-ci/20261026-065607-548db09c/`. Custodia excluye logs, comandos/credenciales, Settingsrepr, contenidos de instalaciones laterales y grafo completo con documentos ajenos.

Corte previo430:2.059fuentes/19.928nodos/84.091relaciones/960comunidades,SHA256 `ea84d7685cc462371b132e7f2eb5d633f8f3528e30c3f5c6d918cad626391c6e`; AST de seis fuentes y semántica430/17 revisados antes de congelar117. Resultado431recibe su conciliación semántica propia; no sustituye N15.

N09 acumula **13 defectos locales corregidos**: siete A/B/C más seis D. No equivalen a13bloques contractuales ni a aceptación de las139acciones de N09. Se mantienen **8/13 bloques obligatorios aceptados**, N09 abierto, pendientes de autoridad/fuentes restantes de rectificación y lecturas previas a descifrado y revisión finita de purgas/outbox/jobs. N02restante al final, N10/N11/N15 pendientes y N12–N14condicionados; el objetivo completo no está terminado.

Las capacidades laterales están incorporadas con sus límites y sin repetir QA por instalarlas. Las16skills están anunciadas; Django AI Boost/PostgreSQL/Context7/Playwright/Chrome DevTools expuestos no equivalen a conexión real. Recarga MCP soportada aceptada sin reinicio, objetivo/consumo/estado preservados; Semgrep anuncia tres herramientas en App Server pero no en el catálogo de este turno. PostgreSQL sigue sin destino/rol de lectura, GSC/PSI no instalados/conectados y kits aislados no sustituyen runtime/runner. Archivos laterales permanecen fuera de esta entrega.
