# B07 — Colector opcional de recursos de servicios propios

Estado: cinco pruebas focales, seis guardasCLI y calibración TCP pequeña terminal auditadas. B07abierto8/18.

La[matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md) separa ocupación de handlers, CPU y consumo de memoria. Se revisaron ResourceProbe/OwnedCPUObserver/owned_backend: el primero enumera procesos globales y el segundo exige un cgroup de controlador dedicado; no se presentan como medición actual porservicio del arnés beta. El nuevo colector acotado reutiliza lectura de CPU/identidad y contadores conocidos, sin escribir cgroups ni cambiar cuotas.

`scripts/benchmark_owned_services.py` acepta únicamente salida del run exacto, padrepytestdelrunner y tres hijosdirectos web/worker/Beat. Lee descendientes por children del PID conocido, máximo128, sin enumerar /proc global. Comprueba start_ticks y parentesco; un hijo desaparecido queda noobservado, no ceroCPU. Verifica nombres/labels/IDs/PID/cgroup de contenedoresPostgreSQLyRedisdelrun. Muestreo1Hz más extremos, como artefacto separado, sin hooksWSGI/SQL/render/reglas y sin argumentos/env/SQL/filas. Límites de ancestros sólo metadata, sin atribuirles uso compartido.

PorPID: ticksCPUusuario/sistema/RSS. Porhoja de cgroup propia:cpu.stat/memory.current/peak/max/eventos y límites. RSSsumada puede contar páginas compartidas varias veces; muestras no garantizan pico ni captura de procesos transitorios. Memoriapeakdelcgroupes acumulada desde su creación, no sólo ventana. CPUdelservicioincluyetrabajo de fondo; los contadores no dan CPUporpetición ni coste causal de muestreo. CPUdelhilolector documentada por separado; captura inicial/final en hilo principal queda fuera de esa cifra. Cuotas8CPU/8GiBno se infieren de afinidad o RAMhost.

Banderaoficial `--benchmark-service-resources`, defaultapagado y envhijo fijado0cuando no se pide. Sólofocused/1worker/normalrefresh/betapromotions/nodoexactofunctional oshort, sin otros observadores. measuredrechazado. Un shortinstrumentado no habilita900aunque suschecksnuméricospasen. Fuentes de producto intactas.

## Guardas verificadas

Run `20261021-180824-abc353d4`:5PASS/0omisiones. Proceso hijo real/identidadCPU/parentesco y rechazoPIDreutilizado; tres rechazos de contenedor ajeno antes de leer su proceso con doble acotado; salida y ruta de límites fuera de ámbito rechazadas. [Auditoría y CLI](evidencias/b07-service-resources-guards-20261021.json): seis invocaciones rechazadas conexit2y cero runs nuevos: sinnormal, measured, workers2, captura adicional, sinbeta y selecciónajena. Limpieza/fuentes/PIDs/Telegramconciliados. No simulador presentado como aceptaciónTCP.

## Calibración preregistrada

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test 'tests/test_contract_http_load.py::test_contract_arrival_rate_http_with_limited_uploads[functional]' --workers 1 --fixture-snapshots --isolate-test-broker --benchmark-normal-refresh --benchmark-beta-promotions --benchmark-service-resources --timeout 300
```

Sólo10perfiles/2derechos nativos,60dinámicas y1upload, worker/Beat/PostgreSQL/Redis reales propios. Comprobar geografía suma10, cuatro workerssync1hilo, primeraslecturas,0errores/omitidas/finales, subida302persistida. Exigir muestras>=2sinerror y tres árboles conocidos más dos cgroups propios; CPUdeltas no negativas para identidades persistentes, datosparcialesmarcados, salida sin payloads privados. Retirada propia de recursos/temporales/PIDs y Telegramterminal. No carga10000/60s/900sni aceptaciónSLO por esta calibración. Resultado instrumental no es control limpio ni demuestra ahorro de aplicación.

## Resultado terminal de calibración

Run `20261021-181039-62ac893b`:1PASS/0omisiones,87,679sJUnit,60dinámicasexitosas/0errores/omitidas/finales y1upload302persistido. p95observable229,271msdescriptivo, no aceptaciónSLO/capacidad. Geografía completa10y2derechos nativos, cuatro workerssync1hilo, primeraslecturas y patrocinio conservados. [Auditoría corregida](evidencias/b07-service-resources-calibration-20261021-audit.json) concilia35muestras sinerror/33,694sdeintervaloobservado, propiedadesJUnit/manifiesto,628fuentesapp/config/templatesiguales, recursos/temporales/PIDsobservadosretirados y Telegramterminal.

Identidades persistentes:5procesosweb/3worker/1Beat. DeltasCPUdeesosPID:4,47s/1,44s/0,06s respectivamente. SumasRSSmáximasmuestrales558047232/401543168/137269248bytes: páginas compartidas pueden contarse variasveces; no memoria exclusiva ni pico continuo. PGcgroup2,021sCPUyRedis0,281sCPUdelservicioenintervalosaprox33,695s; no CPUporpetición, ni porSQL, ni carga ajena atribuida. Hilolector0,157sCPUno mide overhead causal total; extremos en hilo principal quedan fuera.

Las hojasPG/Redisexponencpu.max=max100000/memory.max=max; el controlador tiene nivelesnot_exposedyancestrocpumaxmax. No se acredita presupuesto kernel8CPU/8GiBni contención bajo20RPS. No series de volumen grande generadas por este corte, ni900s. El import auxiliar del primer auditor usó un nombre incorrecto y falló antes de comprobar datos:ERRORnotificado/versióninicialconservada; corregido a cpu_delta, auditoríaPASSnotificada, sin repetir TCPni cambiar fuentes del ensayo.

El colector queda disponible apagado por defecto. Cualquier shortconesta captura es diagnóstico y conserva bloqueo900aunque cumpla cifras. Los cinco casos unitarios y CLI no ejercen esa rama numérica positiva de un short; la exclusión figura en fuente y measuredCLIrechazado. No afirmar aceptación de carga ni gasto/proveedores por disponibilidad del instrumento.

Corrección posterior195: la captura opcional vuelve a idle_after tras el cliente; calibración nativa60dinámicas/1upload verifica35muestras y transición ordenada. Los artefactos181 conservan sus etiquetas originales; no son CPU exclusiva de la ventana ni aceptación de volumen grande. Véase [frontera195](195-frontera-captura-recursos-b07-20261021.md).
