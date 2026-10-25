# N03E — reintentos y recuperación real con worker y Beat

25/10/2026. Alfa,N03abierto,3/13bloques obligatorios aceptados. Referencia real de386 aceptada localmente; no hay cambio de aplicación ni optimización temporal afirmada.

## Resultado y transporte demostrado

Run20261025-192053-4c827d97:1PASS/0FAIL/ERROR/SKIP,116,573sJUnit.1744huellas intactas,selección exacta serial,PostgreSQL17/Redis7.4 propios,prefork2 yBeat conrolSQLrestringido comprobado en cada ejecución.101eventos observados y38ejecuciones:9MEDIA,28REFRESH y1RECOVER; todas sin eager. Los fallos de tareas descritos abajo son entradas negativas deliberadas y esperadas por el caso, no fallos de pytest. SinHTTP/carga/proveedor ni aprobación pública/humana.

A. Original sintético físicamente ausente: mismoID con cuatro ejecuciones retries0/1/2/3 y estadosRETRY/RETRY/RETRY/FAILURE. Tres señalesretry reales conFileNotFoundError; fallo final del mismo tipo. Backoff conjitter registrado1/2/3segundos,permitido por rangos0..1/0..2/0..4. Esperas publicación→inicio siguiente1,002/2,002/3,001s, posteriores alETArestante observado. DBfailed/attempt4/errorcode; original restaurado quedó como controlagotado excluido porBeat. Prueba límite de ese mensaje, no máximo global entre mensajes.

B. Otro original canónico temporalmente sustituido porGIFsintético válido: ValidationError real por formato no admitido, una ejecuciónFAILURE/retries0 yningúnretry. DBfailed/attempt1. JPEGcanónico restaurado ySHAverificado antes deBeat; recuperación real posterior lo dejóready/attempt2. No parche de tareas, almacenamiento, RNG, reloj, retry o despacho.

C/D. Beat real con sólo entrada nativa recover-private-media a60,0s y scheduleprivado nuevo. Primerapublicación desdePIDBeat,RECOVERSUCCESSen hijo worker,cuatro publicacionesMEDIA distintas emitidas porworker ycuatro ejecucionesSUCCESS. Cohorte:queued→ready/attempt1,stale→ready/attempt2,failedB→ready/attempt2,readyconPhotopendiente→comparacióncompleta/attempt1/noaprobada. Controlesfreshprocessing,exhausted4,erasing/erased/purging/purged idénticos antes/después;freshlease<180s. Los cuatro Blob positivos distintos y sus transiciones independientes, junto a cuatro tareas y fuente process limitada a su Blob, vinculan la cohorte sin leer argumentos en el observador; no se afirma un mapeo directo de argumentos que no se capturó.

## Tabla antes y después — tiempos reales

Antes no había testigo equivalente de estas fases: los llamados directos/capturas385 no son una referencia temporal del broker. Una muestra por transición,intentos deA separados,cuatro tareas recuperadas en paralelo,prefork2. El reloj de tarea incluyeSELECTde rol ybookkeeping del observador. Ready es observación del arnés, no instante exacto. No sumar etapas solapadas ni inferirp95/SLA.

| Etapa | Antes comparable | Después observado |
| --- | --- | ---: |
| A: ejecución por intento0/1/2/3 | No medido con este protocolo | 113,108/162,662/129,905/72,094 ms |
| A: countdown retry0/1/2 | No medido | 1/2/3 s |
| B: ejecución fallida ValidationError | No medido | 130,025 ms |
| InicioBeat→primerpublish | No medido | 61,504 s |
| PublishBeat→inicioRECOVER | No medido | 7,588 ms |
| EjecuciónRECOVER | No medido | 113,305 ms |
| PublishBeat→readyobservado cohorte | No medido | 1,150 s |
| Cuatro ejecucionesMEDIA recuperadas | No medido | 190,325/606,946/673,120/341,824 ms |

La cadencia configurada permanece60s; un primer tick observado a61,504s no acredita distribución de intervalos ni SLA de usuario. QA116,573s incluye preparación/espera/limpieza y no es latencia de aplicación. Los28refrescos se conservan como coste observado, sin abrir una hipótesis marginal de optimización ahora.

## Auditoría, procedencia y límites

Borrador nativo n03b_prepared_writer en worktree aislado553253c,ownershipdosinstrumentos+informe,sin pruebas/imports/lint/Git/red por escritor. Rootleyó los487líneas iniciales,integró sólo dos archivos y añadió snapshots reales de positivos/controles,roles/raíces/publicaciones/manifiestoSHA,seguimiento inicial dePID y rechazo deSIGKILL. LintPASS y prerregistro/semántica386+ASTambos instrumentos verificados antes de congelación. Tokens nativos desconocidos,noV1nuevo. La aplicación y sus dependencias de553253c permanecen idénticas; fixtures canónicas diezSHA distintos ydimensiones/bytes registrados, sin datos reales.

Auditorindependiente verificaJUnit/propiedad=informe,101eventos,sin errores de observador,publicaciones↔ejecuciones porID/retrynúmero sin colapsar reintentos,rolrealSQL/PID/noeager,retries/fallos tipados/ETA,estados/negativos y límites. Worker/Beatexit0,cuatroPID/startticks ausentes,rolSQL ycredenciales privadas retirados,directorioprivado eliminado,clavesajenas preservadas y0nuevas fuera delnamespace. Inventario independiente sin contenedores/volúmenes/redes/temp de ese run;Telegramterminalsent. Logs privados permanecen ignorados y archivo de evidencia excluye stdout/stderr.

No demuestra kill/redelivery de worker, intervalo de todos los ticks,límite global de intentos entre mensajes,carga,80kcapacidad,HTTP o proveedor. No se sustituyen esas ausencias por una declaración amplia. N03Eaceptado localmente; N03/N07 siguen abiertos hasta conciliar todas las acciones,criterios y límites del contrato con testigos actuales. MOD09restante diferido al final del desarrollo porusuario; tiempos actuales aceptables enalfa y sin nueva optimización marginal del detector. Sin apertura de beta/producción.
