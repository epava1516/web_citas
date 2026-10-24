# Acta14 — Aceptación técnica local B12, 2026-10-21

B12 queda aceptado técnicamente en local conforme al [roadmap103](../103-roadmap-beta-clasificados-20261020.md). La [matriz de doce requisitos](../evidencias/b12-local-requirement-acceptance-matrix-20261021.json) contrasta cada obligación con fuentes, pruebas y límites. No aceptación global de beta ni apertura.

## Candidata y contabilidad

Worktree web_modelos_mod08_vps, baseGit920ea36b6f4d0e8c0a60d030730de5aed1cf1781 y cambios locales identificados por source-hashes.json de los runners. HEAD solo no identifica la candidata. No commit de aceptación creado.

022632-91e875b1:60PASS/0FAIL/0ERROR/0SKIP,4workers,157,414sJUnit; PostgreSQL/Redis y RustFS reales locales. 023008-a83a296a:1PASS serial del diagnóstico de coste, mismas fuentes. Reutilización estricta de41casos del corte232949-2d2b26df:5eventos+7transporte+27logging+2gates de recuperación. Fuentes de testigos, fixtures y emisores idénticas; único producto existente cambiado desde ese corte: operational_snapshot.py, sin dependencia de esos testigos.102casos únicos conciliados entre cortes, no una ejecución única102PASS.

Se confirmaron fuentes frescas al aceptar, ausencia de contenedores/temporales y procesos propios, huellas de evidencias originales y Telegram terminal. Los cambios documentales y del ledger posteriores no se presentan como fuentes probadas de producto. [Detalle140](../140-conciliacion-purgas-beta-b12-20261021.md).

## Requisitos aceptados

- Errores HTTP públicos observados y resultados de tareas con vocabulario fijo; el cuerpo succeeded no equivale a entrega realizada.
- Edad exigible de colas, backlog de publicación, fallback observado y tareas fallidas. Ventanas acotadas conservan coberturaunverified y healthunknown, incluido después de recuperación.
- Dieciséis purgas/limpiezas configuradas conciliadas: temporales, confirmación de cuenta, caché privada y medios. Vencimiento lógico, retención protegida y borrado físico se distinguen.
- Fallos inyectados y recuperación: outbox con prefork y backoff60s natural, publicación reparada por worker, fallo parcial de medios y purga RustFS. Simulación de entrega y hooks eager de almacenamiento identificados; no se confunden con proveedor o consumo externo.
- Umbrales de atención según cadencias y presupuesto del muestreador:48SELECT, p95local149,731ms vacío/224,161ms con50kfilas frente1s, intervalo propuesto60s. No plazo garantizado de detección ni SLO HTTP.
- Ingeniería responsable de respuesta local, con códigos/runbooks de inspección y recuperación por servicios existentes. Sin replay, cambios de autoridad ni borrados automáticos por alertas.
- Privacidad de métricas/eventos y transporte acotado: sin identidades, contactos, payloads, filtros o preferencias; pipe/fork/errores verificados. Microbenchmark303eventos recibidos y rotación propia50001/50001 preservados con sus huellas.

## Límites que conserva la aceptación

El monitor es administrativo y manual. No instala guardia, colector desplegado ni envío automático de alertas. El backend opcional de objetos produce aviso de inventario no medido cuando está habilitado; el snapshot SQL no inventaría almacenamiento ni acredita ausencia universal. Deshabilitarlo tampoco prueba ausencia de objetos anteriores. Hay pruebas físicas locales delimitadas con API/archivos reales, no inventario de producción ni proveedores externos.

Coste medido en orden fijo y PostgreSQL local caliente, sin garantía de todas las cardinalidades o CPU de servidor. Eventos best effort y pérdidas/rotación explícitas; no contabilidad durable ni cobertura universal. Runbooks de continuidad completos, responsables reales, custodia, canales y guardia quedan en B13/B17; adaptadores reales en B14. Estas limitaciones no se convierten en verificación real por aceptar B12 localmente.

B01–B06 y B12 suman siete de18puntos cerrados. B00 residual, B07–B11 y B13–B17 pendientes. B07 mantiene el cortoFAIL de p952703,689ms; ensayo largo bloqueado. Siguiente frente: B13 continuidad y moderación, comenzando por auditar runbooks y evidencia de recuperación existentes antes de nuevas pruebas. No publicación, proveedor, contratación ni datos reales autorizados por esta acta.
