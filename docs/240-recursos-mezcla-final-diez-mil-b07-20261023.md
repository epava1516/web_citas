# B07 — Recursos por servicio de la mezcla final a diez mil

B07-271 preparado: captura de recursos por servicio a 10.000 perfiles tras corrección259; reutiliza atribución270 y contractual265, sin repetir900s ni aceptar capacidad instrumentada. Ocho de18 cerrados; B07 abierto.

## Incertidumbre y reutilización

257 tuvo PASS funcional pero observador ERROR con cero muestras: sigue no aceptado para recursos.259 reprodujo y corrigió el estado propio created/Pid0 con espera tipada y validación posterior de PID/start_ticks/cgroup. No identifica retrospectivamente la causa257.258 observa sólo100;256 observa1000.262 y265 son corto y contractual limpios PASS y no se repiten.268/269/270 cubren atribución explícita100/1000/10000. Faltan series propias a10000 para esta mezcla después de la corrección.

Comparación actual con prerregistro265: ningún archivo previo eliminado; únicamente añadida la prueba de atribución y modificados .ai/tasks/desarrollo.md y .graphifyignore. Scripts de capacidad y observador idénticos;628archivos de producto intactos. Reutilizar guards44 y comprobación nativa259, integración y preflight pertinentes. Verificación de imagen existente y montajes readonly antes del lanzamiento; no recompilar una imagen sin cambios pertinentes.

## Protocolo271

Una ejecución `scripts/run_vps_capacity.py beta-http-functional --territorial --service-resources --committed-mixed --committed-population 10000 --cpu-budget 8 --app-image sha256:385e6dcd16ea7b6a44b7383028093dbf0047488e960a8c08ced1a01582ca0056`.

Misma fixture sintética7000/3000,2000derechos,14exclusiones,9986visibles y1991patrocinios; cero marcas pendientes. Preparación confirmada y estadísticas fuera de ventana.24páginas antes/después y56detalles excluidos404, IDs/orden/recuentos/patrocinios nativos.42slots/30rutas,60dinámicas en3s a20RPS,20porcategoría30poridioma y1upload302persistido. No usar la latencia de3s como SLO. Contabilidad reconciliada,0noemitidas/finalespendientes; timeout65s/drain70s y generadorp95≤10ms/p99≤25ms/máximo≤100ms vigentes.

Seis servicios propios con identidades exactas, PostgreSQL17/Redis7.4 y cuotas kernel8CPU/8GiB/swap0;4workers1thread. Observador host fuera del presupuesto. Captura limitada600s/600muestras/8MiB después del inicio de fases; espera de preparación10800s y deadlines grandes existentes sin ampliación. Registrar before_arrivals/arrivals_and_drain/idle_after, tres muestras finales. Separar muestras que cruzan fronteras y deltas de contadores sólo entre observaciones compatibles de la misma fase e identidad. No inferir procesos desaparecidos entre muestras, sumar RSS compartido como memoria exclusiva, confundir memory.peak acumulada con pico de ventana, ni atribuir CPU por petición. Ventana breve no demuestra estado estable, percentiles de recursos ni coste causal del observador.

## Presupuesto, aislamiento y auditoría

La preparación10000 anterior257 tardó6059,738sJUnit;270 tardó4810,166s con otras ventanas e instrumento. Son costes de planificación, no predicción lineal ni latencias de peticiones. Se reutilizan límites existentes: preparación10800/pytest18000/app18600/controlador21000. No ampliar por resultado ni ejecutar otras pruebas simultáneas.

Antes de lanzar: comprobar imagen/runtime reutilizados, huellas, protocolo y grafo actualizado. Congelar todas las fuentes del runner, protocolo original y helpers; sin ediciones hasta auditoría completa. Wrapper/watcher/callback/compactador persistentes con PID/start_ticks/sesión/argv; Telegram inicio y prepausa confirmados. Pausar mismo objetivo; shell solicita compactación durante espera y reactivación automática terminal conservando consumo, sin sondeos del modelo.

Tras terminar, auditar igualdad prerregistro/lanzamiento/runner/árbol, protocolo porbytes/SHA, producto628, JUnit y JSON, mezcla/rutas/censos/generador, manifiesto de seis servicios, cuotas kernel, fases y contadores reales, límites de salida y CPU del observador. Comprobar ausencia Docker/PID/temporal y recibos Telegram/compactación/reactivación. Preservar FAIL/INVALID/ERROR antes de corregir; no repetir para obtener verde. PASS sólo acredita captura funcional instrumentada; no reemplaza265 ni cierra B07 automáticamente. Después conciliar matriz214 con requisitos originales antes de decidir aceptación o siguiente intervención.


## Recuperación previa de imagen

B07-271: imagen esperada ausente, negativo preservado; imagen recuperada con 732 archivos históricos verificados y sin red. Preflight nativo pendiente antes de captura10000; B07 abierto, ocho de18.

La comprobación de runtime inicial falló por imagen6936424d ausente; no se ejecutó HTTP. Archivo base SHA0a5e94d8d60aafca23bda3943bd53f6213ce17498f88211a6b6d93190d59497a yconfig261d4b6d verificados; reconstrucción COPY del contexto histórico, sin red ni RUN, con cuotas de construcción. Nueva imagen sha256:385e6dcd16ea7b6a44b7383028093dbf0047488e960a8c08ced1a01582ca0056. Verificación de732archivos históricos, dependencias incluidas, y limpieza del contenedor de extracción. No atribuirlo a aceptación de runtime ni a fuentes actuales embebidas: las fuentes actuales se montan readonly. Causa de desaparición no demostrada. Evidencias resources271-image-negative.json y resources271-recovered-image-proof.json. Preflight nativo necesario con nueva imagen antes del prerregistro largo.


## Preflight272 negativo preservado

B07-272 auditado INVALID antes de pytest: imagen fijada de objetos ausente, fuentes/protocolo y limpieza verificados. Recuperación por digest exacto en curso; preflight correctivo273 pendiente, captura10000 no iniciada.

Corrida20261023-052314-d73270f3: fallo image-rustfs_rustfs_sha256 por imagen rustfs/rustfs@sha256:1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c ausente. Sin JUnit ni pytest; no fallo de producto ni aceptación de runtime. Auditoría resources272-negative-audit.json confirma fuentes1702 completas/prerregistro/CI/árbol/protocolo original y ausencia Docker/PID; TelegramINVALID enviado. Causa de desaparición no demostrada. Recuperar únicamente digest fijado, comprobar todas las imágenes requeridas y repetir sólo preflight afectado; conservar este negativo. Sin nueva carga larga ni cambio de producto. Turno anterior PROGRESO: recuperación de imagenapp y732archivos comprobados. Ocho ClaudeV1 históricos/consumo intactos, ninguno nuevo.


## Preflight273 correctivo auditado

B07-273 auditado: preflight nativo PASS con imagen recuperada y objetos restaurados por digest; fuentes1.702/producto628, limpieza y Telegram confirmados. Captura de recursos10000 pendiente; B07 abierto, ocho de18.

Corrida20261023-052602-fab1d4e9:1PASS72,196sJUnit (72,68spytest). Imagenapp385e6dcd yRustFS1803faef fijadas; cinco imágenes disponibles antes del lanzamiento. PostgreSQL/S3/AEAD/proxy/generación ypurga por worker/Beat nativos verificados, dos workersGunicorn propios del preflight, sin crédito de capacidad4workers ni carga10000. Fuentes1702 idénticas prerregistro/CI/árbol, protocolo original intacto,628producto intacto, seis cuotas8CPU/8GiB/swap0 yausencia Docker/PID verificadas antes de esta edición. Auditoría resources273-preflight-audit.json. Negativo272 porimagenobjetos ausente preservado, causa de desaparición no demostrada.

El aviso pytest dentro del contenedor falló; auditoría inicial detectó ausencia de recibo. Se conserva audit_resources273_preflight-initial.py ysu EXIT1. Reenvío terminal explícito desdehost confirmado en resources273-terminal-host-receipt.json, sin repetir prueba. Auditor corregido exige ese recibo, no inventa el aviso original. Para próxima carga envolver run_vps_capacity con run_notified/LOCAL_CI_TELEGRAM_OWNER=runner ycomprobar terminalhost después de limpieza; no depender de accesoTelegram dentrodelcontenedor.

Siguiente: preparar launcher y auditor de recursos271, validar sushelpers yprerregistroconimagen385e6dcd ypreflight273, lanzar persistente captura funcional3s/60dinámicas/1upload a10000 con6servicios yobservadorcorregido259. Pausa/compactación/autoresume del mismo objetivo sólo tras cuatroPIDs yavisos confirmados. No repetir corto262/contractual265 niatribución268269270. OchoClaudeV1históricos yconsumo preservados,ninguno nuevo. Turno PROGRESO: negativo auditado, dependenciaexactarecuperada ypreflightcorrectivoPASS auditado; fullgoalactivo.


## Captura271 auditada

B07-271 auditado: captura funcional a 10.000 perfiles PASS, 22 muestras de seis servicios, fuentes1.702/producto628 y limpieza verificadas. Compactación solicitada y reactivación automática del mismo objetivo confirmadas; B07 abierto, ocho de18.

Corrida20261023-053440-560f458d: 1PASS6121,010sJUnit. Sesenta respuestas dinámicas correctas, un upload302 persistido; 9986perfiles visibles y1991patrocinios tras14exclusiones.24páginas antes y24después equivalentes al censo nativo y56detalles excluidos404. Generador válido: p95 2,441ms y máximo3,438ms. Ventana funcional3s; p95HTTP703,284ms descriptivo, sin crédito contractual.

Auditoría resources271-audit.json verifica prerregistro/lanzamiento/CI/árbol1702, protocolo original porbytes,628archivos de producto, PostgreSQL17/Redis7.4, cuotas kernel8CPU8GiBswap0, cuatro workers, seis identidadesPID/start_ticks/cgroup, ausencia Docker/PID y recibos Telegram.22muestras puras:12antes,7durante llegadas/drenaje y3después. Preparación excluida4493,959s; observador4504,856s de duración y18,630sCPU. Deltas compatibles durante llegadas: app2,147núcleos medios y PostgreSQL1,642 en aproximadamente3,072s; no CPU por petición, extrapolación ni causalidad. memory.peak es acumulada y RSS puede compartir páginas; conservar esas limitaciones.

Telegram terminal del host después de limpieza y del wrapper confirmado; solicitud de compactación REQUEST_ACKNOWLEDGED y callback RESUMED_AFTER_TERMINAL conservan objetivo/consumo, sin goal nuevo. Primera auditoría no leyó resultados por ruta incorrecta (vps-measurements); EXIT1 y aviso conservados. Se corrigió el argumento a capacity-environment y la auditoría pasó sin repetir carga ni editar fuentes congeladas.

257 permanece ERROR de observador con cero muestras, sin causa retrospectiva demostrada.271 cubre la serie funcional grande posterior a259. No repetir corto262, contractual265 ni atribución268/269/270. Siguiente: conciliar requisitos originales de B07 y sus límites; esta captura no concede aceptación beta global. Ocho invocacionesClaudeV1 y consumo histórico preservados, ninguna nueva.
