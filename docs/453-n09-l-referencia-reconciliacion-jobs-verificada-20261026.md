# N09L — referencia local del reconciliador de jobs verificada

Estado: aceptada localmente la referencia finita del reconciliador y la decisión sin cambio de aplicación para estos escenarios. N09 completo139IDs sigue abierto,8/13bloques obligatorios aceptados. Alpha/noindex; base3e6160c y [prerregistro452](452-n09-l-prerregistro-reconciliacion-jobs-20261026.md). Sin generación ni capacidad global acreditadas.

Run:20261026-154343-723972ab,12PASS/0FAIL/ERROR/SKIP,176,355sJUnit/1781huellasestables. Runnerfocused serial/--isolate-test-broker/parsernativo/PostgreSQL17-alpine/Redis7.4-alpine propios. Auditoría independiente propiaPASS:27fasesTask.run/reconcile/dispatch reales,218mensajes IDonly leídos en Redis y212rechazos por caducidad. EAGERFalse comprobado antes/después de cada fase y antes de publicar. Inmutables/pines/dominio/medios/fuentes/colas/contenedores/redes/volúmenes/temporal y recibosTelegram terminal/auditoríaPASS comprobados. No pruebas activas de este lote.

## Referencia temporal y antes/después

| Escenario/elegibles | Fase | Rechazados / publicaciones | Wall tarea, ms | SQL, ms | Dispatch, ms | Apply_async, ms | Sentencias | Después |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| dispatch/0 | first_dispatch | 0 / 0 | 4.458 | 2.057 | 0.000 | 0.000 | 2 | Sin candidata |
| dispatch/0 | queued_immediate_replay | 0 / 0 | 8.709 | 3.420 | 0.000 | 0.000 | 2 | Sin candidata |
| dispatch/1 | first_dispatch | 0 / 1 | 31.941 | 7.333 | 23.439 | 19.793 | 3 | Sin candidata |
| dispatch/1 | queued_immediate_replay | 0 / 0 | 5.399 | 2.848 | 0.000 | 0.000 | 2 | Sin candidata |
| dispatch/10 | first_dispatch | 0 / 10 | 40.334 | 15.892 | 35.359 | 17.434 | 12 | Sin candidata |
| dispatch/10 | queued_immediate_replay | 0 / 0 | 8.900 | 4.032 | 0.000 | 0.000 | 2 | Sin candidata |
| dispatch/100 | first_dispatch | 0 / 100 | 291.054 | 106.314 | 284.768 | 134.112 | 102 | Sin candidata |
| dispatch/100 | queued_immediate_replay | 0 / 0 | 8.390 | 3.550 | 0.000 | 0.000 | 2 | Sin candidata |
| dispatch/101 | first_dispatch | 0 / 100 | 298.830 | 99.434 | 292.375 | 134.640 | 102 | Sin candidata |
| dispatch/101 | dispatch_continuation | 0 / 1 | 8.362 | 3.449 | 2.538 | 1.176 | 3 | Sin candidata |
| dispatch/101 | queued_immediate_replay | 0 / 0 | 5.114 | 2.390 | 0.000 | 0.000 | 2 | Sin candidata |
| expiry/0 | first_expiry | 0 / 0 | 6.007 | 2.595 | 0.000 | 0.000 | 2 | Sin candidata |
| expiry/0 | expiry_replay | 0 / 0 | 8.151 | 4.080 | 0.000 | 0.000 | 2 | Sin candidata |
| expiry/1 | first_expiry | 1 / 0 | 6.114 | 3.387 | 0.000 | 0.000 | 3 | Sin candidata |
| expiry/1 | expiry_replay | 0 / 0 | 6.013 | 2.612 | 0.000 | 0.000 | 2 | Sin candidata |
| expiry/10 | first_expiry | 10 / 0 | 18.988 | 10.858 | 0.000 | 0.000 | 12 | Sin candidata |
| expiry/10 | expiry_replay | 0 / 0 | 5.959 | 3.274 | 0.000 | 0.000 | 2 | Sin candidata |
| expiry/100 | first_expiry | 100 / 0 | 138.745 | 92.341 | 0.000 | 0.000 | 102 | Sin candidata |
| expiry/100 | expiry_replay | 0 / 0 | 7.675 | 3.816 | 0.000 | 0.000 | 2 | Sin candidata |
| expiry/101 | first_expiry | 100 / 0 | 230.960 | 137.368 | 0.000 | 0.000 | 102 | Sin candidata |
| expiry/101 | expiry_continuation | 1 / 0 | 7.916 | 3.983 | 0.000 | 0.000 | 3 | Sin candidata |
| expiry/101 | expiry_replay | 0 / 0 | 6.020 | 2.630 | 0.000 | 0.000 | 2 | Sin candidata |
| mixed/3 | mixed_first | 0 / 3 | 27.358 | 6.951 | 19.009 | 13.176 | 5 | Sin candidata |
| mixed/3 | mixed_running_repeat | 0 / 1 | 13.321 | 4.661 | 4.630 | 2.171 | 3 | Sin candidata |
| failure/2 | broker_failure | 0 / 0 | 8.918 | 3.632 | 0.155 | 0.000 | 2 | Sin candidata |
| failure/2 | first_dispatch | 0 / 2 | 21.910 | 5.717 | 14.746 | 10.382 | 4 | Sin candidata |
| failure/2 | queued_immediate_replay | 0 / 0 | 4.469 | 2.022 | 0.000 | 0.000 | 2 | Sin candidata |

Decisión: conservar la aplicación.100publicaciones en291,054ms/102sentencias, primer lote100del caso101en298,830ms/102;100rechazos por caducidad en138,745ms/102, primer100del caso101en230,960ms/102. Datasets/estados distintos,N1porfase: no son A/A ni comparación de versiones. No defecto funcional ni incumplimiento demostrado que justifique candidata marginal. Sin después medido, mejora causal no evaluable; no trasladar un presupuestoHTTP o MOD09 al reconciliador.

Medidas: wall sólo Task.run; wrapper externo retornaNone y reconciler interno retorna cantidad de dispatchTrue, no rechazos ni generación completada. SQLexecute sin texto/params; dispatch contiene apply_async y UPDATE de queued, apply_async reenvía al productor real con cola propia/retryFalse. Relojes anidados/solapados, no sumables. Brokerfailure cuenta llamadasdispatch2 y fallosinyectados2, apply_asyncreal0. Preparación/snapshots/asserts/cleanup/QA aparte;176,355sJUnit es tiempoQA. N1/instrumentación/caché calentada/sinp95/after/throughput/SLA. ContextoHaswell8CPUx86_64/MemTotal23760928kB/FSregistrado durante el run, no baseline previo ni carga/cuotas por fase.

Oráculos: seed prepared/enqueue actual y clones FKválidos con timestampscreated_at únicos son volumen sintético, no nuevas selecciones aprobadas. Pines de expiración/disponibilidad/proof/reciente extendidos siete días sólo enfixture. Volúmenesdispatch0/1/10/100/101yexpiry0/1/10/100/101,100/1/0para101yN/0resto. Expiración alterna queued/running con available/lease futuros para aislar primer selector, no backlog mixto. Sólo dispatched_at cambia en queued enviadas; expiradas cambian state/reason/lease/finished con límites temporales. Resto de columnas/pines5/todos modelos instalados/through/auth/sesiones/auditorías/exportaciones/medios intactos. Cada caso tieneN+5filas o3+5en mixto. Mensajes reales decodificados y multiconjunto exacto de IDs comparado privadamente, sin emitir IDs/razón/ciphertext/rutas/claves/env/logs. Sólo claves de cola/prioridades propias retiradas, contextosbroker/Redis cerrados sin app.closeglobal; Redisownedretirado al terminar.

Matriz: queued disponible sin dispatched, queued disponible con dispatched antiguo y running leasevencido producen3envíos; inmediata segunda fase sólo1del mismo running. Dosqueued recién enviadas no repiten; running conserva token/attempts/lease/estado y todas las columnas. Guardasfutureavailable/recentdispatch/activelease/failed/rejected intactas. Es al menos una vez en broker, no doble exportación ni promesaexactlyonce; no se ejecuta generación. Separar primer100expirados y segundo100dispatch; el segundo filtro no excluye caducados pendientes del backlog, que claim rechaza después, fuera del perfil aislado de expiración.

Fallo: ConnectionError sintético antes de publicar, capturado por dispatch nativo comoFalse. Dosqueued siguen duraderos sin ningún cambio/marca de envío, razón privada conservada, cero mensajes y entero0. Publicación real restituida→2/envíos2yreplay0. No caída real del broker/proceso ni fallo de generación; tareasSUCCESS y resultado de generación no se equiparan. ColaRedisreal con mensajes no es prueba de worker/Beat/proveedor.

Intento:20261026-153459-2516cd3f conserva1callPASS/3callFAILparciales en journal, sinJUnitcompleto,0perfilesaceptados. photo_environment reactivaEAGERTrue después del guard inicial; los mensajes no aparecen en Redis. Root detiene medianteSIGTERMdelrunner/caminosoportadodelimpieza, runnerERROR/señal15,1781fuentesintactas/recursosytemporalretirados/TelegramERRORsent. Ningún tiempo inicial se usa en la tabla ni se convierte en fallo de producto. Instrumento/freeze/protocolo/journal/fallos preservados; corrección sólo EAGERFalsepostfixture y guardasrealespre/postfase/prepublish. NuevaRuff/ASTsem/congelación antes de repetir los doce perfiles inválidos, sin repetir pruebas válidasI/J/K ni originales.

Reutilización: siete testigos originalesPASS seleccionados de20261024-094540-3a6ec8ac,21fuentes directas pertinentes idénticas: expiración, contrato tipado de mensaje, límitesworker, proyección histórica pura, prefijooutage/dispatchrecuperado y dos denegaciones tras esperaPostgreSQL observada por permiso/proof. En outage se conserva sólo el prefijo consumidor0→1, no éxito de generación posterior; en denegaciones no se alcanza generate. Seed antiguo no acredita admisiónactual; fuentes directas no son cierretransitivoglobal. Wholeoldrun conservaERROR y otros19casos mantienen sólo su historia, no26PASSactuales. Dos dependencias difieren: rights/fingerprint y guardimágenes; el guard actual coincide byteexacto con el aceptadoN02C365/run20261025-134320-fefba16c, sólo alcance de etapa. No repetir worker/paquetes ni reabrirN02.

Revisión: propia Django/Celery/seguridad acotada al instrumento y consumidor, sin cambios de aplicación/esquema/settingsdelproducto/servicios/CI. Root revisa366líneas de propuesta aislada, compara privacidad mediante bool/hash, añade cantidades reales de filas cambiadas y distingue wrapperNone/entero/publish/dispatch. La revisión inicial no detectó el override tardío de fixture; runtime lo mostró y se corrigió antes de aceptar. Instrumento finalSHA40256baf4d574c8eca18624d28d08d8e865fa43f1a4cf44251be41fdd0014fa6/RuffPASS. Reporte canónico diez campos, complete delegado nunca fuePASSruntime.15laterales preservados fuera de entrega propia, sin escánerglobal ni herramientas nuevas usadas como QA.

Grafo: corte4512091fuentesSHA70e7a24ee553db02a9ca2ba6cee2a9a537159b7a6d210c12640453aeb3f213df; primerprerregistro4522093fuentes20437nodos84960relaciones992comunidadesSHA3f7b8b789eb87e0ca5d89ec6c73782cb02a2e9467eaf428f095790b13d527385 conservado. Tras corrección y antes de congelar, ASTactual+sem452/17selectiva root2093fuentes20438nodos84962relaciones993comunidadesSHA4b15ea0c96053735bfe4cbf8eb02a0e8dad2fabb2eecb1a15ce095bd33cb9a2c. Cierre sem453/17sin nuevoAST/runtime; no reconstrucciónN15 ni semánticaexhaustiva;111preservado.

Límites: Task.run/PG/Redispropios no es worker/generación/Beat/proveedor ni un nuevoSLOMOD09. TTLs de selección/proof no acreditados por clones;27fases finitas no capacidad de histórico masivo, reintentos de generación, fallo abrupto o proveedor. Otros reconciliadores/consumidores/139IDs yN10N11N15pendientes;N02restante al final/N12–N14condicionados. No cerrarN09 por sumar mensajes, perfiles o aliasBeat.
