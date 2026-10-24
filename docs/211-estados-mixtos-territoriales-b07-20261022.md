# B07 — equivalencia territorial con estados mixtos

B07-231: preparada equivalencia PostgreSQL de100perfiles en dos ciudades;14inelegibles de siete estados, dos derechos inactivos y20derechos nativos sintéticos. Prueba pendiente, sin carga ni aceptación;8de18,B07 abierto.

El corte229 verificó10000publicados y retirada con cohorte49+1. Roadmap103 y línea base108 requieren distribución de estados: no equiparar ese PASS funcional con cobertura de borradores, pendientes, pausa, caducidad y revocación. Se añade tests/test_mixed_state_territorial_equivalence.py, sin modificar producto ni herramientas de carga.

Protocolo231:100perfiles sintéticos, reparto territorial70/30,20derechos Top/Premium emitidos por servicios reales con eventos de pago sintéticos. Proyección fresca, mezcla pendiente y reparación explícita manual. Siete exclusiones duplicadas en perfil promocionado y orgánico: draft, processing, pending, paused, caducidad temporal manteniendo status published, withdrawn y consentimiento revocado en Person.14excluidos y86visibles tras mutación. Suspender otro derecho y caducar otro conservando ventana válida; ambos perfiles continúan visibles sin patrocinio. No son transiciones de usuario ni ensayo de proveedor.

En cada fase: censo nativo independiente y comparador comercial previo, todas las páginas de dos ciudades con/sin texto en ES/EN; IDs ordenados, recuentos, unicidad y etiquetas. Después de mutación:404ES/EN de los14excluidos; marcas idénticas antes y después de GET, incluyendo generaciones. Firmas pendientes y reparadas iguales; ninguna lectura repara. PostgreSQL real obligatorio. No crédito de worker, TCP, SLO, producción, verificación real o umbral49: éste tiene evidencia215/229 separada.

Ejecutar un único caso focal con runner oficial y watchdog900s, fuentes congeladas, limpieza y Telegram terminal. El fallo inicial Ruff por orden de imports se conserva; corregido el import, nueva comprobación requerida. No batería larga ni900sHTTP automático. Tras resultado, auditar manifiestos y actualizar grafo/documentación antes de decidir escala o integración.


## Resultado231 auditado

B07-231: equivalencia mixta100 auditada PASS/142,990s;60páginas ESEN,14excluidos y86visibles,marcas0→14→0. Derechos suspendido/caducado pierden patrocinio sin ocultar perfil. Reparación manual, sin carga ni worker acreditados;8de18,B07 abierto.

Corrida `20261022-111510-f00a8bb0`:1PASS/0FAIL/0ERROR/0SKIP,142,990sJUnit.20páginas exhaustivas por fase fresca/mezcla pendiente/reparada; IDs ordenados, recuentos, unicidad, etiquetas y404ESEN de14inelegibles verificados. Cada motivo se aplica a un perfil orgánico y otro promocionado: borrador, procesando, pendiente, pausado, plazo caducado manteniendo published, retirado y consentimiento revocado. Las mutaciones preparan estados directamente; no acreditan transiciones de interfaz. Derechos nativos20 antes/después; tarjetas patrocinadas sumadas en las cuatro combinaciones idioma/texto80→44→44. Siete derechos corresponden a perfiles excluidos y otros dos pierden vigencia comercial;11promociones siguen elegibles. Ambos perfiles sin derecho vigente permanecen públicos.

Proyección pendiente y reparada producen firmas idénticas; todas las lecturas mantienen IDs/generaciones de marcas. Reparación explícita manual: no worker ni Beat acreditados por este caso. Perfil100 y dos municipios sintéticos70/30, no diversidad nacional. Sin producción, checked real, TCP ni percentiles de capacidad.

Auditoría antes de editar fuentes/documentación:1690huellas iguales entre prerregistro/runner/árbol, protocolo por bytes/SHA y628fuentes de producto intactas. PostgreSQL17/Redis7.4 reales, compilación nativa, todos los pasos y limpieza Docker/temporal/PID verificados. Telegram CI y auditoría PASS con delivery sent. Evidencias artifacts/beta-promotion-fix-20261020/mixed231-audit.json y audit_mixed231.py. Se conserva Ruff inicial EXIT1 (import desordenado) y lanzamiento EXIT2 rechazado antes de pruebas por faltar native-source; corregidos sin ocultar resultados. Prueba focal ejecutada una sola vez.

Siguiente incremento: integrar esta mezcla en el escenario de observación nativa con preparación fuera del slot, sin repetir la cohorte49 ya verificada. Antes de escalar hay que medir el coste de oráculos en el caso pequeño y congelar nuevo protocolo. PRODUCTION/checked requiere un escenario separado: capacity_beta_http.verify_owned_fixture rechaza PRODUCTION y promotion_exposure.enabled deshabilita promociones sintéticas allí. La metadata sintética de las pruebas checked no prueba proveedor real. Mantener umbral48, límite1000, no READ_REPAIR, presupuestos del generador y SLO originales. B07 abierto; sin900HTTP automático.


## Protocolo232 — reparación nativa

B07-232: preparado control mixto100 con worker y Beat reales propios; comprobación pendiente completa antes del arranque, reparación observada y limpieza exigidas. Integración pendiente;8de18,B07 abierto.

Se reutiliza el caso231 y se parametriza manual/native. La variante manual conserva sus comprobaciones; native requiere opt-in normal_worker_beat sin xdist. Ejecutar sólo el selector[native], con runner oficial, --benchmark-normal-refresh, --isolate-test-broker, --workers1 y dependencia librdb fijada. No repetir manual ni10000. Watchdog900s; no ensayoHTTP900s.

La variante nativa ejecuta antes del arranque todas las páginas frescas y pendientes y404ESEN, preservando marcas. Después verifica identidad efectiva de PostgreSQL y contenedor/puerto/etiqueta de Redis propio vacío; arranca worker Celery concurrencia2 y Beat con sus comandos habituales y generación aislada. Mantiene calendario nativo y no invoca refresh_all para reparar. Desde readiness exige≤45s hasta dirty0 y evento SUCCESS no eager correlacionado por UUID con publicación Beat, cleared≥14 y sin snapshot_error. Es reparación posterior a las lecturas, no escenario concurrente ni slot Beat+5s.

Detener primero Beat y después worker; comprobar PID/start_ticks, raíces terminadas y Redis vacío. Configuración temporal de media/delivery propia; ningún servicio normal ni proveedor. Guardar mixed-worker-repair.json, ledger y propiedad JUnit. Luego repetir el mismo oráculo nativo y todas las páginas reparadas, iguales a pendientes. La lista inicial sigue100/70–30/20derechos/14excluidos/86visibles; sin cambio de producto628. Las comprobaciones de cargas229 y de umbral49 se conservan separadas. Un PASS no acepta B07 ni capacidad.


## Adaptador de lanzamiento232

B07-232: selector nativo100 autorizado de forma exacta en runner serial con broker aislado; seis guardas CLI y Ruff pendientes de recibo. Primera solicitud rechazada antes de pruebas; integración real pendiente.8de18,B07 abierto.

El runner rechazó el primer selector porque normal_refresh sólo admitía contratoHTTP; no arrancó contenedores ni pruebas. Se conserva mixed232-rejected-preregister.json y su protocolo original. scripts/run_local_ci.py admite ahora exclusivamente el selector mixto[native] bajo focused/workers1 y --isolate-test-broker; selector manual o múltiple conserva rechazo, y el contratoHTTP anterior conserva compatibilidad. Se comprueban seis fronteras CLI sin contenedores. La primera ejecución del comprobador olvidó workers1 y falló; se corrige sólo su invocación, sin aflojar runner. Congelar de nuevo fuentes/protocolo tras grafo242 y recibos.


## Negativo232 y protocolo233

B07-233: preparación de broker aislada por generación; negativo232 auditado antes del arranque del worker. Se conservan claves previas y se exige reparación Beat/worker de14marcas. Integración233 pendiente;8de18,B07 abierto.

Corrida232 `20261022-112631-585f9c23`:1FAIL/0ERROR/0SKIP,116,261s de caso; CI ERROR y Telegram sent. La guarda broker.dbsize()==0 falló antes de arrancar procesos worker/Beat. No se archivó inventario de claves en ese corte y no se atribuye su tipo. Auditoría negativa verifica1691fuentes, protocolo congelado, limpieza real y recibo antes de editar. Evidencia mixed232-negative-audit.json; no reparación nativa acreditada.

Corrección limitada a tests/mixed_state_worker.py: comprobar vacía únicamente una generación aleatoria nueva, registrar número/huellas de claves de preparación y conservarlas. Worker/Beat usan esa generación; al terminar sólo se borran sus claves. Exigir generación propia vacía, claves previas aún vivas con igual valor y ninguna clave nueva fuera de la generación. Las expiraciones previas se registran separadas; no se exige conservar TTL ni borrar preparación. No se conoce el contenido del broker negativo232 ni se convierte ese fallo en éxito.

233 repite únicamente el selector native100 afectado por esta corrección, mismo reparto70/30,20derechos,14excluidos,86visibles y60páginas previstas. Mismos comandos worker/Beat, espera≤45s desde readiness, UUIDpublicaciónBeat→ejecuciónSUCCESS, ausencia eager/snapshot_error y dirty0. Sin reparación manual en variante nativa. Mismos controles de procesos/propiedad, fuentes congeladas y Telegram. No se repite229 ni manual231, no hay carga HTTP ni SLO/capacidad acreditados. Congelar tras grafo243 y comprobar Ruff/documentación.


## Resultado233 auditado — reparación nativa de estados mixtos

B07-233: equivalencia mixta100 con Beat/worker reales auditada PASS/174,917s;60páginas,14excluidos,86visibles y reparación14→0.28,892571s desde readiness; dos claves previas preservadas. Fuentes/limpieza/Telegram verificados;8de18,B07 abierto.

Corrida `20261022-113144-9e6fe9ca`: un caso PASS, sin fallos, errores ni omisiones; 174,917 segundos JUnit. Inventario sintético de 100 perfiles, dos municipios 70/30 y 20 derechos comerciales emitidos por los servicios existentes con eventos sintéticos. Los siete motivos de exclusión se verifican tanto en perfil orgánico como promocionado: 14 excluidos y 86 visibles. Un derecho suspendido y otro caducado pierden patrocinio, conservando sus perfiles públicos. Las tarjetas patrocinadas suman 80/44/44 en las cuatro combinaciones idioma/texto.

Veinte páginas exhaustivas en cada fase fresca/pendiente/reparada, 60 en total. IDs ordenados, recuentos, unicidad, etiquetas y 404 ES/EN comprobados. Las lecturas pendientes mantienen las generaciones de las 14 marcas; firmas pendientes y reparadas idénticas. Worker y Beat se arrancan después de completar esas lecturas. No son peticiones concurrentes con la reparación ni carga TCP.

Beat publica UUID bbcaa2be-cfcf-4936-aa71-6a251bd42b2d; el worker registra SUCCESS no eager, limpia exactamente 14 marcas hasta cero y no registra error de snapshot. Publicación→inicio 6,715392ms, ejecución 258,458766ms. Reparación observada a 28,892571s desde readiness; ciclo de arranque y espera 31,947237s. Las cotas marca→limpieza son 60,905944–61,023096s porque incluyen las lecturas pendientes previas al arranque. No afirmar reparación en 45s desde mutación: este protocolo acota desde readiness y no sustituye el slot original ni la cota del caso229. Ledger: un UUID correlacionado, cero ambiguos y cero publicaciones/ejecuciones no correlacionadas en el tramo capturado; sin afirmación sobre otros tramos.

Redis propio: dos claves de preparación preservadas sin cambio de valor, cero expiradas y cero claves nuevas fuera de la generación; generación del worker vacía tras su limpieza. Dos raíces y dos hijos observados retirados. PostgreSQL y Redis efectivos verificados; sin cuotas de carga ni proveedor real acreditados. Auditoría antes de editar: 1691 fuentes iguales en prerregistro/runner/árbol, protocolo por bytes/SHA y 628 fuentes de producto intactas. Limpieza real de contenedores, temporal y procesos y Telegram terminal confirmados. Evidencias mixed233-audit.json y audit_mixed233.py en artifacts/beta-promotion-fix-20261020. Negativo232 y rechazos previos conservados.

Siguiente: perfilar en una cohorte pequeña el coste del oráculo antes de ampliar esta mezcla al HTTP acotado. Cualquier optimización debe conservar lecturas nativas frescas, pertenencia, orden, etiquetas y separación de la proyección; no adoptar PublicationContext sólo por existir en producto. La hipótesis está registrada sin cambio de oráculo. No repetir229 ni lanzar900s automáticamente. B07, producción/checked y aceptación beta global siguen pendientes.
