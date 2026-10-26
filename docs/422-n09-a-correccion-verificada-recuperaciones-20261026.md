# N09A — autoridad fresca verificada en recuperaciones

Aceptación local acotada de la corrección de [421](421-n09-a-correccion-autoridad-prerregistro-20261026.md), no cierre de N09. Se mantienen **8/13bloques aceptados** y los139IDs del inventario de [418](418-n09-inventario-descomposicion-20261026.md). Continúa alfa, sin proveedores, despliegue ni apertura.

## Fallos preservados y cambio de aplicación

El original041859-126a93a0 conserva2FAIL/57,843sQA: aviso con revocación durante espera PostgreSQL real devolvió302y reinició aviso/creó recuperación; medios falló antes de la espera por una instancia de fixture obsoleta. La única corrección instrumental fue refrescar ese trabajo. La repetición exclusiva042943-80ced3cc conserva1FAIL/48,210sQA y confirma medios302con reinicio del trabajo/+MediaErasureRecovery/+RightsAction. No se borra ni convierte ningún fallo anterior enPASS.

Cambian sólo `notice_operations.requeue` y `media_operations.requeue`, sus importaciones y un helper local en cada módulo. Capturan versiones de sesión/MFA una vez; consultan una nueva instancia User al entrar y tras los locks de dominio/aviso/trabajo, antes del replay o escritura. Comprueban existencia, cuenta activa/no borrada, MFA/versiones y permisos nativos; ámbito y actor de auditoría usan el usuario fresco. Se preservan firmas públicas, orden de locks, claves, cifrado y reintentos legítimos. Los demás handlers/formularios mantienen su AST.

No hay nuevo lock de User, esquema, migración, settings, servicio ni transporte cambiado. La garantía corresponde a esas fronteras de lectura de autoridad; no acredita una serialización universal de cualquier cambio posterior de permisos.

## Verificación real y límites

Lote044639-dff64b4a: **29PASS,0FAIL,0ERROR,0SKIP;296,139sJUnit**. Selección completa prerregistrada:2esperas HTTP reales+14negativos de servicio+13regresiones originales. PostgreSQL17yRedis7.4desechables propios, serial, instrumentos revisados, parser nativo real y dos recorridos móviles originales. Preparación sintética/eager no se presenta como worker ni proveedor.

Las dos esperas observaron `pg_stat_activity`/Lock y el PID propio bloqueante antes de revocar; tras liberar, ambas terminaron403con snapshots de dominio y estado mínimo idénticos. Hilos/conexiones cerrados y transacción liberada. Los14negativos (2servicios×7revocaciones) prepararon cachés legítimas y un actor obsoleto con mutaciones ORM externas: permiso principal, permiso de revisión, cuenta inactiva/borrada, MFA deshabilitado y versiones MFA/sesión incrementadas. Todos denegaron sin cambios de negocio.

Las13regresiones originales verifican recuperación autorizada, replay que no reinicia un ciclo posterior, dos conexiones, ámbito/conflicto, CSRF, cifrado, guard producción/simulador y navegación móvil. No se repitieron QA de exportación larga ni otros bloques cerrados. Las1.763huellas permanecieron estables (1.758runner+5documentos aparte); contenedores/redes/volúmenes propios y temporal ausentes al auditar. Telegram terminal y auditoría enviados, recibos comprobados.

## Antes y después, incluidos tiempos observados

| Caso | Antes de corregir | Después de corregir | Petición antes → después |
| --- | --- | --- | --- |
| Aviso report, permiso revocado durante espera |302;failed5/V0→queued0/V1;+1recuperación|403;estado y todos los snapshots intactos|169,280→203,045ms|
| Medios, permiso revocado durante espera |302;failed5/V1→queued0/V2;+1recuperación/+1acción|403;estado y todos los snapshots intactos|213,874→306,112ms|
| Actor obsoleto,14negativos de servicio |Condiciones previstas en421;sin lote previo equivalente|14denegaciones/snapshots intactos|Sin pareja temporal comparable|
| Regresión legítima |13testigos originales vigentes|13PASS en la selección actual|Sin pareja temporal comparable|

Los tiempos de petición incluyen **esperas inducidas distintas y denegación frente a ejecución**; no son latencia normal ni comparación causal de rendimiento. Las consultas adicionales de usuario/permisos corrigen autorización. Los57,843s/48,210sde diagnóstico y296,139sde29casos corresponden a selecciones diferentes: no se calcula aceleraciónQA entre ellos.

## Evidencia y continuación

Resumen saneado: [n09a-autoridad-recuperacion](evidencias/n09a-autoridad-recuperacion-20261026.json). Locales reproducibles: `artifacts/recorridos-n09-a-20261026/baseline-audit.json`, `artifacts/recorridos-n09-a2-20261026/baseline-audit.json`, `artifacts/recorridos-n09-a3-20261026/candidate-audit.json`, cortes, fuentes antes y propuestas aisladas; terminal oficial `artifacts/local-ci/20261026-044639-dff64b4a/result.json` y XML original. No se versionan logs o trazas con settings.

Grafo prerregistro421:2.041fuentes/19.721nodos/83.831relaciones/945comunidades,SHA256 `fced367a4ced08ff7ee602dfc3f5733cb638fa5e069ad3b393dc45007c306414`; AST de los dos servicios e instrumento y semántica de421/seguimiento verificados antes del corte. La documentación terminal requiere su propio refresco semántico; no equivale al rebuild finalN15.

Pendiente N09: conciliar139IDs con evidencias reutilizables y referencias acotadas, analizar condiciones de autoridad detectadas sólo por fuente en otras familias y medir purgas/outbox/lecturas de acuerdo con el inventario. No se acepta una familia por semejanza con esta corrección. N10 mantiene sus procedimientos compartidos; N02optimización restante al final por instrucción del usuario; N12–N14condicionados. Objetivo general activo.
