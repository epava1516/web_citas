# Regresión funcional correctiva y espera persistente

Fecha:2026-10-20. Estado: regresión finalizada negativa y auditada; correctiva126 pendiente, sin aceptación beta. El runtime se registrará en artifacts/beta-promotion-fix-20261020/wide-corrected-persistent-launch.json. Un PID o una colección no acreditan PASS.

## Necesidad y alcance

El negativo155011 conserva38FAIL/56ERROR/122SKIP y3238PASSúnicos+4subreportes. Las correctivas119–123 y el común124 han revalidado los94negativos con363PASS en cada brazo2/4,622fuentes de producto idénticas y todas las fuentes iguales entre los dos. Esto no prueba los restantes miles de consumidores sobre la candidata que incorpora el defecto real de catálogo corregido. La adaptación compartida, el fallo anterior y su corrección justifican esta regresión; no se inicia por la orden de notificación.

Selección prevista:3460nodeids únicos,3454del carril funcional anterior más6unitarias nuevas del preflight. Excluir56archivos del carril de capacidad y conservar las cuatro exclusiones largas oficiales: short/measured de test_contract_http_load, test_rights_portability_large_history.py y test_publication_state_tcp.py. Los diagnósticos beta_* no entran en colección ordinaria: el mutante manual ya tiene prueba explícita en124. La colección debe coincidir exactamente con los nodeids registrados; un total igual no basta.

Los122SKIP históricos son omisiones, no PASS; revisar razones y cambios al terminar. Exigir PASS de los94negativos originales y los362casos ordinarios del común124, además de conciliar todos los resultados de la selección. No declarar beta global, capacidad o los excluidos como verificados. El cortoTCP20RPS sigueFAIL,900s bloqueado y B00residual/B07–B17 pendientes; seis cierres locales conservan sus cortes.

## Configuración congelada

Runner oficial: --profile regression --regression-lane functional --workers 4 --fixture-snapshots --isolate-test-broker --native-source /tmp/web-modelos-librdb-v2.4.0 --duration-order-from artifacts/beta-promotion-fix-20261020/wide-corrected-duration-history.json --timeout 21600.

Cuatro trabajadores explícitos por el43,95%menos observado en la selección124; un par2→4 no garantiza esa reducción en toda la suite. Default general6y productoGunicorn4sync intactos; capacidad serial separada. No cambiar cuotas, criterios, selección ni autoridad para acelerar. PostgreSQL/Redis propios, Chromium y RustFS fijado reales donde corresponda; adaptadores externos simulados identificados, datos sintéticos. Sin proveedores/pagos/publicación/datos reales.

Historial único fusionado de155011 y común actual193902, reemplazando duraciones de casos afectados antes bloqueados. Ordenar archivos completos, preservar orden interno y comprobar igualdad de colección en los cuatro trabajadores. No es resultado ni latencia de producto. La predicción de1–2horas usa el funcional anterior8210s y la comparación focal, con incertidumbre por mezcla, cachés y host compartido; no es una promesa ni una extrapolación de capacidad.

Antes de congelar: actualizar AST dirigido de fuentes afectadas y semántica real de decisiones/documentos, con alcance honesto; comprobar colección exacta y conservar huellas/historial. Desde la congelación no editar fuentes, docs, ledger ni grafo. Conservar el negativo y cada resultado anterior. No ejecutar otro gate o carga propia simultáneamente.

## Lanzamiento, aviso y pausa autorizada

Lanzar el runner persistente con stdin DEVNULL, stdout/stderr a archivo propio, start_new_session=True y close_fds=True. Verificar PID/start_ticks, sesión/grupo propios, archivo de salida, runner.json y source-hashes.json iguales a la congelación. Confirmar el hijo real de pytest y el conjunto recogido; si hay rechazo/error, registrar y corregir, nunca afirmar que sigue ejecutándose.

Con la prueba confirmada viva, enviar al Telegram de OpenClaw un aviso que nombre esta regresión funcional, indique la espera larga y la pausa del goal y explique que el runner notificará su resultado terminal después de limpiar. Comprobar delivery:sent y comunicarlo en el chat. Sólo después llamar update_goal(status=paused), según la autorización de AGENTS del2026-10-18 para estas esperas. La prueba debe continuar viva; no sondear ni reactivar automáticamente un goal pausado. El usuario reactivará tras el aviso terminal.

Si no se confirma persistencia o aviso previo, resolverlo o informar del fallo antes de declarar preparado el relevo. Registrar identificación y recibos reales únicamente en artefactos ignorados durante el freeze; conciliar esta documentación al retomar.

## Auditoría al reanudar

Inspeccionar estado real antes de repetir nada. Si terminal, conciliar XML/journal/nodeids y subreportes, selección/exclusiones/SKIP,94negativos y362comunes, fuentes actuales/congeladas, herramientas nativas, contenedores/objetos/temporales/PID y recibo terminal de Telegram. Un envío fallido no convierte pruebas en PASS. Si sigue vivo, verificar el mismo proceso, sin relanzar por timeout de observación.

Un FAIL exige descomponer y corregir su causa antes de repetir; conservar negativos. Un PASS sólo acepta esta regresión funcional con sus omisiones explícitas. Sigue pendiente el trabajo real de optimización/capacidad y el roadmap completo hacia beta, no un cambio de nombre de los tests.


## Colección previa verificada

Colección3460nodeids únicos coincide exactamente con el prerregistro, incluidos94negativos originales y362comunes ordinarios;0casos ejecutados. Se mantienen56archivos de capacidad excluidos y las cuatro exclusiones oficiales. El colector informa3460/3462por las dos deselecciones short/measured; los otros archivos se excluyen antes de recoger. Evidencia beta-wide-corrected-collection-20261020.json. No PASS funcional ni de capacidad; al lanzar deben coincidir también los cuatro workers reales.


## Terminal negativo auditado

195459-bacfc549 terminóERROR:3460nodeids únicos,3331PASS+4subreportes/7FAIL/0ERRORdepreparación/122SKIP, JUnit4168,465s. Fuentes actuales idénticas al freeze y622fuentes de producto idénticas al común124, todos94negativos originales y362comunes ordinarios pasan; los122nodeids omitidos coinciden con el corte anterior. Cuatro trabajadores recogieron exactamente lo registrado, sin cambios de orden interno. Auditoría beta-wide-corrected-negative-terminal-audit-20261020.json comprueba también recursos/objetos/temporales/procesos retirados y recibo1792530303194202708-2655792 sent. Auditoría notificada1792530403689210285-3186182 sent.

Los siete fallos pertenecen a rectification_review, todos por regex de validate_submission sobre la revisión original rectificada: esperaba el error de contrato romántico y recibió el bloqueo histórico específico. El producto conserva ese bloqueo previo, como requiere120. Reanálisis y correctiva126; no volver a lanzar por seguir viendo artefactos de un proceso terminal. La pausa anterior fue sólo espera autorizada y ya consta objetivo activo al retomar. No aceptación beta ni de capacidad. Los69min28s observados de este carril no son una comparación causal con155011 porque sus fuentes/resultados difieren; la comparación aislada del arnés sigue siendo124.
