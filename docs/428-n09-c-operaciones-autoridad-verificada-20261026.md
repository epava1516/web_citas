# N09C — autoridad actual verificada en cuatro operaciones

Aceptación local acotada de [427](427-n09-c-correccion-prerregistro-operaciones-derechos-20261026.md), tras [426](426-n09-c-prerregistro-autoridad-operaciones-derechos-20261026.md). **N09 sigue abierto:139IDs y8/13bloques aceptados**. Los19PASSde [425](425-n09-b-inspeccion-autoridad-verificada-20261026.md) y29PASSde [422](422-n09-a-correccion-verificada-recuperaciones-20261026.md) se conservan sin repetición por esta documentación. Alfa, sin proveedores, despliegue ni apertura.

## Fallos conservados y corrección

Original053006-990a74d8:4FAIL/73,493sJUnit,0ERROR/0SKIP,1.763huellas estables y limpieza/Telegram confirmados. Cada caso observó espera PostgreSQL/Lock/PID propio bloqueante antes de retirar el permiso, confirmó su revocación con Usernuevo y confirmó transacción al liberar. Pese a ello, medida/inventario/inicio/resultado terminaron302/200/302/302con los efectos específicos documentados. Son cuatro defectos confirmados; no se borran ni convierten esos FAILenPASS.

Sólo cambian `privacy_holds.hold`, `erasure_inventory.prepare`, `rights_verification.start` y `receive_event`, sus importsUser y tres helpers locales de actor actual. Capturan una vez epochs originales y consultan Usernuevo en admisión y después de los locks canónicos. Resultado independiente vuelve a consultar después del último lock de Proof y revalida ámbito/independencia antes de replay o escritura. Cuenta existente/activa/no borrada, MFA, epochs y permisos nativos actuales son obligatorios. Scope y auditoría usan el actor fresco; PermissionDenied produce el403privado nativo.

Revisión Django Expert/Reviewer y comparación AST confirman firmas/decoradores y demás funciones/clases intactos, incluido check_actor. Se conservan enabled/producción, firma/validación del payload, pruebas/bindings/versiones, lectura auditada, cifrado/motivos, claves y replays autorizados. Sin lock nuevo del operador, cambio de orden de locks, modelo, migración, settings, plantilla ni servicio. La autoridad se verifica en esas fronteras; no se promete serialización universal posterior a la última lectura.

## Resultado terminal completo

Lote054641-e95e52a7: **58PASS/529,725sJUnit (8min49,725s),0FAIL/0ERROR/0SKIP**. Selección íntegra prerregistrada:5esperas reales+31negativos de servicio+22originales. PostgreSQL17/Redis7.4propios desechables, serial, parser nativo y tres recorridos móviles originales. Preparación sintética/eager y proof/eventos del simulador no acreditan worker, identidad real ni proveedor.

Las cinco esperas reales —cuatro sobre solicitud y una sobre el último Proof— terminan403con los10conjuntos de snapshots escalares y estado mínimo intactos; revocación/PIDs propios/Lock/liberación/hilos/conexiones comprobados. Los31negativos incluyen27entradas de cuatro operaciones (hold7/inventory7/start6/result7) y4replaysrevocados. Cada replay conserva primero un efecto legítimo y usa la misma clave/payload original después de revocar: exige PermissionDenied aunque devolver el objeto anterior no produjera una nueva escritura. Todos conservan snapshots y autoridad inicial/cachés naturales demostradas. Estos31son de servicio, sin crédito extra de middleware/transporte/concurrencia.

Los22originales permanecen sin editar:6hold+4inventario+8verificación de perfil+4verificación de cuenta. Verifican grounds/proofs, ámbito/COI/transferencia, CSRF, replay/versiones, dos conexiones, móvil, rechazo de simulador enPROD, revisión independiente y cambios de estado del sujeto. Las interposiciones controladas de originales se distinguen de las cinco esperas reales. Los cuatro de cuenta se ejecutaron por dependencia del mismo servicio modificado, sin reabrir N06.

La versión prevista57se conservó antes de revisión a58, integración y congelación. Se añadió una sola espera de Proof para ejercitar la nueva frontera que un bloqueo del caso no cubre. Esa quinta espera tiene evidencia actual, sin baseline previo ni quinto defecto confirmado. No hubo ejecución de57ni repetición de QA por el ajuste.

Las1.766huellas permanecieron estables (1.763runner+3documentos aparte). Auditoría independiente confirmó58casos,5oráculos de espera,31combinaciones únicas de negativos,22originales, limpieza de contenedores/redes/volúmenes propios y temporal, y recibos Telegram terminal y auditoría enviados. No se repitió QA global ni exportación larga.

## Tabla antes y después con tiempos observados

| Operación y espera inducida | Antes de corregir | Después de corregir | Petición antes → después |
| --- | --- | --- | --- |
| Medida,permiso execute revocado en caso |302;+hold/+acción;caso/publicación cambiados|403;todo el dominio intacto|449,082→278,266ms|
| Inventario,execute revocado en caso |200;+inventario/+acción|403;todo el dominio intacto|851,242→232,217ms|
| Inicio,review revocado en caso |302;+proof y versión|403;todo el dominio intacto|320,166→203,572ms|
| Resultado,verify revocado en caso |302;+evento;proof/caso cambiados|403;todo el dominio intacto|346,407→237,671ms|
| Resultado,verify revocado en último Proof |Sin baseline previo|403;todo el dominio intacto|Sin pareja →229,596ms|
|27entradas obsoletas y4replaysrevocados |Sin lote temporal equivalente|31PermissionDenied,snapshots intactos|Sin pareja comparable|
|22recorridos originales legítimos |Testigos vigentes conservados|22PASSdentro de58|Sin pareja comparable|

Son ejecuciones frente a denegaciones con esperas inducidas distintas: no latencia normal ni porcentajes causales de rendimiento. Las consultas adicionales corrigen autorización.73,493sde4diagnósticos y529,725sde58casos son seleccionesQA distintas, no aceleración ni regresión causal de tiempo por sí mismas.

## Evidencia y continuación

Resumen saneado: [n09c-autoridad-operaciones](evidencias/n09c-autoridad-operaciones-20261026.json). Originales locales: `artifacts/recorridos-n09-c-20261026/baseline-audit.json`, `artifacts/recorridos-n09-c2-20261026/candidate-audit.json`, cortes/fuentes/propuestas y `artifacts/local-ci/20261026-054641-e95e52a7/result.json`/XML. Custodia versionada excluye logs, comandos/credenciales, trazas Settings, contenidos laterales ajenos y grafo completo con otros documentos.

Corte previo427:2.052fuentes/19.836nodos/83.955relaciones/955comunidades,SHA256 `293e8ea2be65fcadad7855979fb50d67074db981d4fa8af08e4726aaa9f69e91`; AST/semántica verificados antes de congelar. El resultado428recibe su semántica propia; no sustituye N15.

N09 acumula siete defectos locales corregidos en A/B/C, sin equivaler a siete bloques contractuales ni a aceptación de todas las familias. Sigue pendiente disposición de139IDs, condiciones de fuente restantes de rectificación/reclamaciones/privacidad/lecturas previas a descifrado y referencias finitas purgas/outbox/jobs. Las revisiones paralelas durante esta batería fueron sólo fuente/informes; no nueva evidencia runtime. N10compartido/N02restante al final/N12–N14condicionados; objetivo general activo.
