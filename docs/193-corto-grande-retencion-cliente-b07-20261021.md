# B07 — Corto grande tras corregir retención de tareas cliente

Estado: ensayo terminal auditado PASS numérico acotado; B07 sigue abierto, ocho de18 puntos cerrados.

## Justificación y límite

[191](191-retencion-tareas-generador-b07-20261021.md) reproduce y corrige retención de tareas terminadas;11PASScliente. [192](192-calibracion-nativa-retencion-cliente-b07-20261021.md) calibra el runtime real:300dinámicas y15uploads persistidos con generador válido. Sólo cambian cliente y sus pruebas respecto a189, además de documentación/metadatos.628fuentesproducto intactas. Este cambio justifica una nueva secuencia finita; no es un tercer corto idéntico a184/186 ni una repetición del900inválido189. No alterar GC para evitar pausas ni atribuir causalidad a coincidencias.

## Escenario congelado

Un único beta-http-short,60s20RPS/1200dinámicas,400listado/400búsqueda/400ficha,600ES/600EN y una subida adicional302persistida.10000perfiles sintéticos nativos/2000derechos(667Premium1333Top), misma agencia/foto/municipio, censo completo de publicaciones; no diversidad nacional. Preparación nativa/rolruntime restringido/PostgreSQL17/Redis/ocho tablas ANALYZE,4Gunicornsync1hilo/timeout60, Celeryprefork2 y Beat reales, faseobjetivo+5s y lecturasfrías200/no-store/patrocinio. No calentamiento adicional.

Misma imagen5a075 inmutable local y cuotas184/192 exactas:PG3CPU3072MiB/Redis0,2CPU384MiB/app3,5CPU3968MiB/objects1CPU512MiB/Caddy0,2CPU128MiB/controlador0,1CPU128MiB, agregado8CPU8GiBswap0/storage≤20GiB. Kernelverificado antes de carga. Memoriaconservadora≤6GiB/PID≤1GiB, CPUfinalincluye preparación y no es CPUrequest. ObservadoresGC/Celery/VmHWMexistentes sinperfiladorWSGI/SQL/render y sinmutarGC.

Demorageneradorp95≤10ms/p99≤25ms/max≤100ms, ceroomitidas, timeout65/drain70/elapsed≤130s. Pendientesventana≤20/final0 y contabilidad reconciliada. p95observable de toda población terminada<800ms, fracciónerror<1%denominador1200; no exigir1200éxitos si fracciónválida. Una subida302persistida y contabilidad completa. El criterio conserva errores visibles.

BETA_HTTP_SHORT_PASS_NOT_CONTRACTUAL sólo si todo cumple; BETA_HTTP_SHORT_FAIL/INVALID_BETA_HTTP_SHORT/ERROR se preservan y detienen secuencia. Sin repetición automática ni900s por este protocolo. Un PASS permite estudiar confirmación separada conforme16MOD08, sin aceptación global. Límitepytest2400s/app3000s; estimación15–20min con preparación.

## Lanzamiento y espera

Antes de iniciar comprobar artefactos/calibración192/fuentescliente11PASS/628producto/limpieza fresca/recibos e imagen local, grafo dirigido actualizado y protocolo archivadoSHA. Congelar fuentes/docs/.ai/grafo hasta terminal; ninguna otra prueba/build.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 corto grande correctiva tareas193' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-short --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Lanzamiento persistente con stdinDEVNULL/logdurable y handles propios. Por instrucción posterior: avisoTelegram previo confirmado identifica prueba/motivo; pausar explícitamente el mismo goal, guardar relevo y solicitar compactación. Vigilante independiente confirma terminal/limpieza/recibo y dispara reactivación automática del mismo goal preservando consumo, sin sondeos del modelo. Un fallo de callback se notifica y no acepta el ensayo. No apagar la prueba al pausar.

Al terminal auditar fuentes/protocolo original/JUnit/ledgers/mezcla/GC/Beat/roles/kernel/recursos y cleanupfresco/recibos antes de editar. Mantener todos los negativos. La matriz180 sigue pendiente de mezclas territoriales/filtros/páginas/backlog/PRODUCTIONchecked y recursos por ventana. No proveedor real/N3/producción ni cierreB07 por este corto.

## Resultado terminal auditado

Run `20261021-212403-207eeaa4`: `BETA_HTTP_SHORT_PASS_NOT_CONTRACTUAL`, salida0, un caso PASS/0FAIL/0ERROR/0SKIP,914,775sJUnit incluida preparación. La [auditoría independiente](evidencias/b07-corrected-client-short-20261021-audit.json) recalcula1200éxitos/0errores/0omitidas,400peticiones por ruta y600por idioma; dos pendientes al cierre de ventana y cero finales. p95 observable515,045ms; demora del generador p95/p99/máxima3,479/6,397/16,209ms. Una subida302persistida.

10000publicaciones/2000derechos nativos en un municipio; cuatro workers/nueve procesos observados, tres publicaciones Beat y siete ejecuciones worker reales, sin confundir ejecuciones con ticks. Inicio observado tick+5,107s; GC intacto y sin congelar. Cuotas8CPU/8GiB/swap0 verificadas, memoria conservadora1673637888bytes y almacenamiento4865392640bytes;628fuentes de producto intactas. Protocolo original conservado con SHA `d446a2f42fd70110d71b98a033660acfbe0f0d0a21914c6ac0161eceaf6e882c`; fuentes, ledger, JUnit, limpieza fresca y recibos Telegram comprobados antes de editar.

La espera persistente, pausa explícita, compactación y reactivación del mismo objetivo funcionaron; callback `RESUMED_AFTER_TERMINAL`, consumo conservado y avisos terminal/reactivación enviados. No demuestra mejora causal de aplicación ni eliminación de pausas GC a900s. Se preserva el INVALID189. Sin repetición ni900automáticos: una confirmación requiere protocolo separado y criterios contractuales. B07 y matriz180 permanecen abiertos.
