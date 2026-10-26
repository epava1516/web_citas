# N09J — referencia local del outbox verificada

Estado: aceptada localmente la referencia finita del consumidor y la decisión sin cambio de aplicación para los escenarios observados. N09 completo139IDs sigue abierto,8/13bloques obligatorios aceptados. Alpha/noindex; baseb54ee2a y [prerregistro448](448-n09-j-prerregistro-perfil-outbox-20261026.md). No entrega externa ni capacidad global acreditadas.

Run:20261026-142236-c8c798d7,7PASS/0FAIL/ERROR/SKIP,111,027sJUnit/1779huellasestables. Runnerfocused serial/parsernativo/PostgreSQL17-alpine/Redis7.4-alpine propios. Auditoría independiente propiaPASS: siete escenarios y dieciséis fases Task.run reales con adaptador local reenviado sin sustituir. Dominio/archivos/fuentes/limpieza de contenedores/redes/volúmenes/temporal y recibosTelegram terminalPASS/auditoríaPASS comprobados. No pruebas activas de este lote.

## Referencia temporal y antes/después

| Escenario/elegibles | Fase / procesados | Wall tarea, ms | SQL, ms | Adaptador, ms | Sentencias | Después |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| volume/0 | first_batch / 0 | 9.760 | 4.479 | 0.000 | 3 | Sin candidata |
| volume/1 | first_batch / 1 | 40.165 | 21.312 | 10.760 | 15 | Sin candidata |
| volume/10 | first_batch / 10 | 176.404 | 88.626 | 55.783 | 87 | Sin candidata |
| volume/100 | first_batch / 100 | 1402.331 | 762.438 | 468.445 | 802 | Sin candidata |
| volume/101 | first_batch / 100 | 1095.473 | 580.253 | 365.039 | 802 | Sin candidata |
| skip_locked/3 | skip_locked / 2 | 31.964 | 17.570 | 5.428 | 18 | Sin candidata |
| skip_locked/3 | after_unlock / 1 | 19.193 | 8.895 | 3.591 | 15 | Sin candidata |
| skip_locked/3 | replay / 0 | 5.949 | 2.329 | 0.000 | 3 | Sin candidata |
| failure/2 | adapter_failure / 2 | 34.381 | 17.366 | 0.436 | 16 | Sin candidata |
| failure/2 | immediate_followup / 0 | 13.458 | 5.535 | 0.000 | 3 | Sin candidata |

Decisión: conservar la aplicación. No defecto funcional ni incumplimiento de un presupuesto de outbox demostrado; no se justifica cambiar las transacciones/savepoints por estos datos.100avisos simulados en1402,331ms/802sentencias; el primer lote100del caso101en1095,473ms/802. Son estados/datasets distintos,N1porfase, no comparación entre dos versiones ni repeticiónA/A. No hay segunda candidata ni después medido: mejora causal no evaluable. No trasladar el umbral de rutas públicas al worker ni convertir schedule60s de fuente en SLA o pruebaBeat.

Medidas: wall alrededor de task.run incluye su transacción; SQL suma tiempo observado por execute_wrapper, conSELECT/UPDATE/INSERT/SAVEPOINT/RELEASE ycontroles que se expongan. El tiempoSQL puede estar dentro del adaptador, así que SQL+adapter no es tiempo total. Preparación/snapshots/asserts quedan fuera; cuerpoQA/tiempo no medido se conservan por caso.111,027sJUnit es QA, no latencia de100avisos. Instrumentación con coste no cuantificado,caché no vaciada y calentada por seeds/drenado/snapshots; sinp95/carga limpia o capacidad histórica. Hardware previo observadoHaswell8CPUx86_64,MemTotal23760928kB; no carga ni quotas durante muestra.

Oráculos: tres productores nativos generan seeds, drenados con el consumidor real antes de medir. Clones con claves/parent/FK/secuencias compatibles aportan volumen sintético, no admisión de nuevas historias. Cinco volúmenes0/1/10/100/101con pines retryfuturo/failed5 y seeds simulados. Ordenexactoporcreated_at/PKdentro de clase e intercaladoReport/Complaint/Rights;100/1/0para101 yN/0enlosdemás. Cada éxito incrementa una vez attempts,limpiaerror/próximointento,marca simulated y añade un único recibo correspondiente. Inmutables/pines/resto de modelos instalados/through/auth/sesiones/padres/Actions/archivos conservados por hashes.

Bloqueo: un ReportNotice retenido, PIDdiferente termina consumiendoComplaint/Rightsmientras sigue el holder; liberar consumeReport y replay0. PIDs reales guardados, conexiones/thread/holder cerrados. No afirmar esperaLock, caída de worker ni reintento porCelery a partir de esta prueba skip_locked.

Fallo: dos envelopes deliberadamente inválidos de fixture,seal/unseal/validate_emailreales,attempts0y4. Resultado processed2/retry1/failed1/simulated0; intentos1y5,error_codeadapter_failure,próximointento60s/None y cero recibos nuevos. Followupinmediato0conpinesintactos. Son datos de faultinjection,no productorválido ni bug; no modificar timestamps ni esperar60s en esta medición. Un retorno normal del cuerpo con retry/failed no significa entrega exitosa, ni taskCeleryfailed: el testigo histórico distingue esos estados.

Reutilización: seis funcionales de test_notice_delivery y un caso realprefork de test_notice_worker_recoveryPASS67,703sQA del run20261024-094540-3a6ec8ac; el run completo mantieneERROR por otros casos.19fuentes pertinentes idénticas de consumidor/crypto/config/Celery/observadores/test/deps, más agregado con natural60seconds/unrecibosimulado/noallclear. Sólo tramooutbox: cuatro despachos manuales reales, fallo único, reintento prematuro0, espera natural y recuperación única. No fase actual de publicación, entrega externa oBeat. El candidatohistórico20261021concrypto/settingsdistintos no se seleccionó. Estos siete originales se conservan sin repetir ni contarlos como nuevas ejecuciones del lote7.

Revisión: propia Django/Celery/seguridad acotada al instrumento, fuente del consumidor y testigos reutilizados; sin cambios de aplicación/esquema/settings/servicios/CI. Root refina asserts para impedir introspección de ciphertext y hace monótono el drenado de seeds. Antes de congelar añadió PIDs a evidencia; primera huella6171y grafo04b0352preservados, huella finalabdbd09771361a36921d9408b103c308d447f64d374d0a125f81680c1fb03f47/RuffPASS/deltaactualsinruntimeanteriorrepetido. No análisis o escaneo global supuesto.

Grafo: corte4472085fuentesSHA1fd121a721384a408260818c2d8f0e0053e1e18aa53611fcbd62885ef995a735; antes de medir4482087fuentes20335nodos84660relaciones986comunidadesSHA5288d30d524c23a35e7b1dbe7d08f16b9230c1f6124f092438881c8d17e972ea. Cierre semántico449/17selectivo root, sin nuevoAST/runtime, no reconstrucciónN15 ni semántica exhaustiva;111 preservado.

Límites: nuevoTask.run+simuladorlocal no es worker/broker/Beat nuevo ni proveedor. Referencia de volumen pequeño con transacciones por aviso, sin throughput/carga/retardo de cola real ni coste sobre histórico masivo. AliasBeat no es una segunda ejecución. Objetos/jobs/reconciliación/otrasramas/139IDs y N10/N11/N15 pendientes; N02restante al final/N12–N14condicionados.15laterales preservados fuera de la entrega propia; no cerrar N09 por sumar perfiles o testigos.
