# B07 — Calibración funcional HTTP dentro del entorno acotado

Estado: focales48+2PASS y calibración real corregida terminal auditada en cortes separados; no capacidad. B07abierto8/18.

Continúa182: modo nuevo beta-http-functional, exclusivo owned8CPU/objectdelivery, sin preflight/delivery/profilers/otrosescenarios mezclados. Default y reparto del entorno de entrega se conservan:PG3CPU/3072MiB,Redis0,2/384,app3,5/3968,objetos1/512,Caddy0,2/128,controlador0,1/128;8CPU/8192MiB/swap0/storage≤20GiB. No CI anidado ni servicios adicionales. Imagen local por digest sin retag/pull.

Reutiliza fixture promocional y generador existentes. Base test_promotion_gate_capacity_ci en el PGpropio permite el guard del generador; la frontera capacidad exige modo/controladorverificado,8CPU,hostpg/puerto5432/migradorci,brokerredisDB0exacto y lectura kernel del cgroupapp350000/100000,3968MiB,swap0. El finalizador mantiene guardas originales por defecto; sólo el modo acotado verificado usa la frontera propia sin Docker dentro de app. Las mismas ocho tablas/estado limpio/censo se validan antes de ANALYZE.

Servidor existente con variante explícita: cuatro workerssync1hilo/timeout60s sólo en beta, resto modos conserva2workers/90s. Workerprefork2/Beat reales comparten appcgroup y rol runtimepropio; calendario beta conserva el desplegado, sin extras de preflight de expedientes. Se observan cuatro hijosGunicorn y cgroupidéntico, y retirada de procesos. La calibración no demuestra cada tarea periódica ni coste de colas de carga grande.

Focal183615:48PASS en handoff/preflight/fixturestats; rol183756:2PASS reales PostgreSQL/credencialesprivadas/cleanup. Sin skips acreditados. Actualtest opt-in sólo por flag oficial; su skip en colección ordinaria no es PASS ni aceptación.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 calibración HTTP beta acotada ocho CPU' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-functional --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Exigir un caso nativo sinomisiones,10perfiles/2derechos/censocompleto/8tablas finalizadas, seis frías200no-store con patrocinio en listado, cuatro workers reales,60dinámicas/3s20RPSsegún generador existente y una subida302persistida. Broker propio vaciado sólo tras refresco explícito/preparación y tras retirada de procesos. Conservar contabilidad completa y propiedades sin cookies/CSRF/credenciales. Controlador verifica kernel y presupuesto antes de fixture, y al terminar memoria/storage/cleanup/fuentes.

Salida esperada BETA_HTTP_FUNCTIONAL_NOT_CAPACITY: ni siquiera un PASSautoriza corto/900s o aceptaB07. Una falla se conserva y corrige en su alcance, sin ampliar población ni relajar garantías. Fuente congelada y Telegramterminal obligatorio. No proveedores, personas reales o publicación.

## Resultado terminal y corrección del protocolo de salida

Primera corrida `20261021-184031-3a91bb1a`: caso funcionalPASS/0omisiones y controles íntegros, pero exit1delcontrolador porque su lista de veredictos terminales no incluíaBETA_HTTP_FUNCTIONAL_NOT_CAPACITY. Launcher successfalseconservado. El pytest interno intentó notificar desde la red aislada y falló; el wrapper externo notificóEXIT1conreciboenviado. No se reescribe ese resultado como gatePASS.

Corrección acotada posterior en dos scripts: aceptar el nuevo veredicto funcional en la salida, sin confundirlo con capacidad; propagar LOCAL_CI_TELEGRAM_OWNER=runner desde el wrapper al controlador y al pytest interno únicamente cuando ya está delegado. Sin wrapper, conserva comportamiento anterior. Criterios/dataset/cuotas/servidor/fixture/generador intactos; el delta de fuentes se declara en auditoría, no se atribuyen48+2casos a los dos cambios posteriores.

Verificación corregida `20261021-184446-568e3791`, entornoVPS `20261021-184446-1f5d4d76`:BETA_HTTP_FUNCTIONAL_NOT_CAPACITY/exit0/launchersuccesstrue. Un caso nativoPASS/0omisiones,56,474sJUnit. [Auditoría](evidencias/b07-bounded-beta-http-functional-20261021-audit.json) concilia60IDsúnicos/60éxitos/ceroerrores/omitidas/finales,1upload302persistido, seis frías200con patrocinio,10perfiles/2derechos/censocompleto/estadísticas8tablas.

Gunicornreal4sync1hilo/timeout60s, nuevePIDsmuestreados entre master/workers/prefork2/Beat, raíces terminadasexit0y ausencia observada dentro del namespace. Rolruntimeprovisionado y verificado por el contexto existente; dos pruebas del rol separadas. Cuotas kernel agregadas8CPU/8GiB/swap0; cota conservadora de memoria1327951872bytes<6GiB y techo almacenamiento4865392640bytes<20GiB. No pico sincronizado ni prueba de memoria bajo10000perfiles.

p95observable313,658msdescriptivo para3s/60dinámicas; transportePASSnoesaceptaciónSLOde900sni comparación causal frente al CI anterior. Se conservan diferencias de cuota, permisos de DB, dataset y arranque al comparar cortes.628fuentesapp/config/templatesiguales; fuente actual calibrada salvo documentación/seguimiento posteriores, delta de salida/notificación probado por el recorrido real. Seis contenedores/volumen/red ausentes, fuentes y reciboTelegramexterno conciliados; logpytestcorregido sin fallo de aviso interno.

La adaptación queda disponible sólo para esta calibración pequeña; no parámetro para escalar silenciosamente. Falta diseñar el escenario grande con mezcla/filtros/estados y recursos por ventana dentro de cuotas, antes de un corto nuevo. FAILhistórico de177preservado y900bloqueado. Sin cambio de producto ni cierreB07;8de18cerrados.

## Extensión posterior184

El modo separado beta-http-shorty la equivalencia de comandos/faseBeat/GC se preparan y calibran en[184](184-corto-beta-cuotas-beat-20261021.md). No cambia el alcance de los resultados de este documento ni convierte su calibración3sen capacidad. Volumen y contención grandes permanecen pendientes de un ensayo nuevo.
