# B07 — Corto beta acotado con fase Beat

Estado: corto grande terminal auditado PASS numérico dentro de cuotas; no contractual ni cierreB07. Ocho de18cerrados.

## Equivalencia antes del volumen

183habilita HTTPpequeño en cuotas. Se añaden modo exclusivo beta-http-short y selectorCAPACITY_BETA_HTTP_SHORT, sólo8CPU/objectdelivery/ownedcontroller; incompatible con funcional, preflight, perfiles, entrega completa y otros escenarios. Sin opción900s. El default del entorno de expedientes y reparto8CPU/8GiB/swap0/storage≤20GiB permanecen: no se reasignan recursos deRustFS/Caddy al app.

Se corrigen dos diferencias del adaptador antes del corto: worker y Beat usan la política de comandos del arnés normalrefresh original, sin without-gossip/mingle ni cola extra; el calendario beta sigue desplegado. ObservadorCeleryexistente con rolesweb/worker/beat registra sólo eventos sintéticos. Se espera publicaciónreal de refresh porBeat y se programa llegada5sdespués, avanzando30ssi se perdió el margen de1s, igual que el control anterior. Se conserva tick/objetivo e inicio real; GCdepreparación puede desplazar el inicio, sin fingir fase exacta. PreparaciónGC/observaciónexistentes, sin congelación ni cambio de umbrales oenabled.

Primer focal `20261021-190110-f949a805`:30PASS/0omisiones parahandoff/exclusividad,fixtureestadísticas y transporte. Después se añadieron sólo asserts de políticaGC/ordenantesdelreloj al adaptador; el ensayo funcional real comprobará ese delta. No se atribuye esa modificación a los30casos anteriores.

Antes de volumen: calibración funcional10perfiles/2derechos/3s20RPS/60dinámicas/1upload con el adaptador actualizado y misma imagen inmutable. Exigir fuentes/roles/DB/broker/cuotas/censo/stats/frías/generador/GC/Beat/ingestión/cleanup/notificación. Un fallo de calibración impide lanzar grande hasta resolverlo. No interpretar su p95comoSLO.

## Protocolo corto prefijado

Sólo tras calibración auditada: un único corto con10000perfiles/2000derechos sintéticos nativos,4Gunicornsync1hilo/timeout60,workerprefork2yBeat,60s20RPS/1200dinámicas por tercios listado/búsqueda/ficha,ESENalternando y1upload separado. Broker/DB/media del entorno acotado propios;roleRuntimeverificado;8tablasANALYZEal terminar preparación, censo completo. No calentamiento extra ni reducción de validaciones.

Conservar generadorp95≤10ms/p99≤25ms/max≤100ms, omitidas0, timeoutHTTP65/drain70, finalespendientes0, ventana≤20, subida302persistida, p95observable<800msyerrorfracción<1%con toda población terminada. El corto admite la fracción de errores contractual; no exige indebidamente1200éxitos si errores<1%yresto válido. GCdelcliente observado sin alterar política; sin profilerWSGI/SQL/render. MuestreoVmHWMdelservidor y contadorescgroupfinales tienen sobrecoste no aislado; CPUtotaldegrupo incluye preparación, no sólo ventanaHTTP. No atribuir todo ese CPUa solicitudes.

Veredictos explícitos: BETA_HTTP_SHORT_FAILparaFAILválido, INVALID_BETA_HTTP_SHORTpara generador/contabilidad inválidos con prueba completa, setupERRORsi falta el escenario. PASSnumérico:BETA_HTTP_SHORT_PASS_NOT_CONTRACTUAL. Se preservan pytest/veredicto/recibos y limpieza también en negativo. No segundo corto ni900sautomáticos, ni cierreB07. Se audita el resultado y decide siguiente trabajo por evidencia.

Tiempo delpasopytest2400s, contenedorappvive3000smáximo; no aumento de cuotas ni criterios de latencia. Preparación estimada minutos/decenas, no horas; goalactivo y sin baterías paralelas. Si no termina en ese límite, conservarERROR/timeout y cleanup; no relanzar por simple expiración de observación.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 corto beta acotado fase Beat' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-short --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

El FAILhistórico177delCIqueda intacto y su perfil no se confunde con el presupuesto nuevo. Falta mezcla territorial/filtros/páginas/backlog y recursos porventana para completarB07. Ningún resultado de este ensayo es verificación real de proveedor/identidad ni aceptación global.

## Calibración de equivalencia terminal

`20261021-190444-4a69803b`, entornoVPS190443:1PASS/0omisiones/91,514sJUnit,veredictoBETA_HTTP_FUNCTIONAL_NOT_CAPACITY/exit0. [Auditoría](evidencias/b07-bounded-beta-beat-calibration-20261021-audit.json) concilia30focales previos y declara único delta posterior en test_capacity_beta_http: assertsGC/orden verificados por el recorrido real.60dinámicasexitosas/0errores/omitidas/finales,1upload302persistido,10perfiles/2derechos/censocompleto,4workers/9PIDobservados.

PublicaciónBeat de refresh unida porIDa ejecución real workerSUCCESS/noeager; cinco ejecucionesrefreshobservadas en total, no cinco ticksBeat. Objetivo tick+5s, inicio real tick+5,151968s tras preparaciónGC; no fase perfecta. PolíticaGCsin cambios/unfrozen,18eventosCelerysintéticos. p95239,966msdescriptivo, no ganancia causal frente a183ni SLOgrande.

Cuotas8CPU/8GiB/swap0 verificadas, cotamemoriaconservadora1337208832bytes<6GiB;628app/config/templatesiguales,fuentesledger/recursos/temporales/namespacesretirados y Telegramterminalauditados. La calibración satisface el prerrequisito; no se amplía su aceptación. Se permite preparar el único corto descrito arriba con fuentes congeladas, sin otras pruebas/build/refrescos de grafo durante ejecución. El ID/resultado grande se incorporará sólo tras terminal y auditoría, sin modificar este protocolo para ajustarlo a sus cifras.

## Corto grande terminal auditado

Run `20261021-191608-f5f21f49`, entornoVPS `20261021-191607-1fef5cbf`:BETA_HTTP_SHORT_PASS_NOT_CONTRACTUAL/exit0/launchersuccesstrue. Un casoPASS/0omisiones,870,767sdelcasoJUnit. [Auditoría independiente](evidencias/b07-bounded-short-pass-20261021-audit.json) recalcula muestras, criterios y contabilidad sin modificar fuentes del ensayo.

1200IDsúnicos/1200éxitos,0errores/omitidas/finalespendientes;400listado/400búsqueda/400ficha,600ES/600EN. p95observable432,620ms<800ms; demorasgeneradorp953,281ms/p996,314ms/máximo16,443ms, bajo10/25/100ms. Tres pendientes al cierre observado60,001353s, verificados contra ended_atcrudos; finales0. Una subida302persistida; primeraslecturasfrías200y patrocinio conservados. Todos los criterios numéricos originales pasan, con capturaGCnormal y observadorCelerydeclarados, sin profiler de petición.

10000publicaciones y2000derechos sintéticos por servicios nativos(667Premium/1333Top); censo geography={'2':10000}, completo pero un solo municipio, no representación nacional.4Gunicornsync1hilo/timeout60,9PIDruntimeobservados/raícesexit0;3publicacionesBeatrefreshy7ejecucionesrealesworkerSUCCESSnoeager, sin equiparar ambas cuentas. Inicio real tick+5,151960s, GCpreparadoantesdelreloj/sinfreeze/políticaigual.

Controles kernel exactos por seis roles:8CPU/8GiB/swap0; cota conservadora de memoria1628270592bytes<6GiB y storageceiling4865392640bytes<20GiB. Memoria agregada de picos/caches/tmpfs más cota del controlador, no pico simultáneo. CPUcgroupfinalincluye preparación y no se atribuye entero a HTTP.628app/config/templatesiguales a la imagen5a075: no se acredita una mejora causal de aplicación frente a otros cortes. Perfil, rolSQL, cohortes, cachés/host y arnés difieren respecto a referencias históricas sin aislamiento causal.

Texto genérico scope del controlador conserva una etiqueta heredada de readiness; no se reescribe el artefacto. Esta conclusión usa el veredicto específico beta_http_short, ledger y controles auditados, sin convertirlo en aceptación global ni en prueba de todos los escenarios. Unidades30ycalibraciónprevias mantienen sus ámbitos, no regresión única niN3.

Fuente/protocolo congelados confirmados, seis contenedores/volumen/red ausentes comprobados de nuevo y Telegramterminalenviado. No segundo corto ni900sejecutados por este corte. El primer PASSpermite estudiar una confirmación finita conforme16MOD08enotro protocolo; no la inicia automáticamente ni modifica éste. B07todavía requiere confirmación/escenarios/presupuestos pendientes de la matriz180;8de18cerrados. LosFAILanteriores siguen intactos.
