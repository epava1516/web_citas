# B07 — Control limpio tras el diagnóstico sync

Estado: primer control limpio terminal auditado FAIL válido; secuencia detenida. Ocho de18cerrados;900s todavía bloqueado.

176obtiene unPASSinstrumental con aplicación idéntica a las corridas negativas: p95548msfrente a1234/1360msanteriores, sin demostrar efecto causal del observador. La ocupación sintética supera99%en cuatrohandlers y el margen observado varía. Esto justifica comprobar el comportamiento sin instrumentación antes de seleccionar una corrección o avanzar, no atribuir una mejora inexistente ni borrar negativos.

## Protocolo y decisión antes de ejecutar

Dos controles limpios secuenciales condicionados: lanzar el primero; sólo si tienePASSválido auditado, repetir una vez sin cambiar fuentes/selección/recursos. La segunda corrida responde a la incertidumbre explícita entre ejecuciones, no a perseguirPASS. Si el primero o el segundo esFAIL/INVALID, conservarlo, no900s ni más repeticiones automáticas. DosPASSno acreditan causalidad ni todo el contrato: permiten preparar el900scon criterios íntegros.

Mismo short169/173/176:10000perfiles/2000derechos por servicios sintéticos reales, cuatroGunicornsync1hilo,20RPS60s/1200dinámicasESENpor tercios/1subida, worker/Beat y PostgreSQL17/Redis propios, estadísticas finales8tablas. Cada control usa recursos/dataset sintéticos nuevos del runner oficial; UUIDs y tiempos relativos varían conforme al generador declarado. Host/cachés compartidos no se consideran aislados. No es un A/B causal del observador.

Comando169sobre el arnés actual, sin ambas capturas:

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test 'tests/test_contract_http_load.py::test_contract_arrival_rate_http_with_limited_uploads[short]' --workers 1 --fixture-snapshots --isolate-test-broker --benchmark-normal-refresh --benchmark-beta-promotions --timeout 2400
```

Ambas banderas de captura deben constarFalse, sin archivo de límitesservidor ni payloadsclient_phases. Conservar población, primeraslecturas frías, política de errores y timeout. No añadir calentamiento del servidor.


Exigir en cada control p95observable<800ms/errores<1%,generadorp95≤10ms/p99≤25ms/máximo≤100ms,ceroomitidas/finalespendientes,ventana≤20,timeout65/drain70,subida302persistida. Conservar primeraslecturas frías y patrocinio. Reconciliar1200IDscliente/servicio, runtimetopología, fuente de datos y finalizaciónstats; registrar latencias, errores y pendientes sin descartar muestras.

Los controles registran manifiesto de recursos/host, no prueban cuotas kernel8CPU/8GiB por inferirlas de afinidad o RAM total. Tampoco acreditan otros escenariosPRODUCTION/checked/CDN. No aumentar workers/PG/caché para pasar ni reinterpretar el resultado176como control limpio.

Congelar fuentes/docs/.ai/grafo para ambos controles; sólo artefactos/evidencia excluida durante la espera. Entre corridas: terminal real, reciboTelegram, limpieza y auditoría fresca antes de decidir la continuación; un timeout de observación no autoriza relanzar. Estimación conjunta en minutos/decenasdeminutos, no horas previstas; goal activo. No otras baterías/build/refrescos de grafo concurrentes, proveedores, datos reales o apertura.

## Resultado terminal del primer control

Corrida `20261021-170829-cac4e830`: un caso FAIL, cero errores de pytest y cero omisiones;957,517sJUnit. El runner denominaERRORal gate por salida1depytest; el benchmark esFAILválido, noINVALID. [Auditoría de muestras](evidencias/b07-clean-short-control-20261021-170829-cac4e830-audit.json) recalcula p95observable1241,749ms, superior al límite estricto800ms.1200dinámicas exitosas, cero errores inesperados/omitidas/pendientes finales;20pendientes al cierre, dentro del máximo20. Generador, drenaje, subida302persistida y restantes criterios pasan.

Manifiesto confirma10000perfiles/2000derechos, cuatro workers sync de un hilo, normal worker/Beat y ambas capturas más observador desactivados. Sinpayloadclient_phases ni archivos de límites servidor. Estadísticas finales8tablas en218,304ms; primeraslecturas frías y patrocinio conservados. Huellas congeladas,628fuentesapp/config/templatesiguales,724de726del mapa de imagen iguales;2herramientas modificadas y módulo diagnóstico nuevo declarado. Recursos propios/temporales/procesos retirados y Telegram terminal confirmado, con auditoría posterior notificada.

El FAILdetiene esta secuencia: no segundo control, no900s y no repetición automática. El PASSinstrumental176no se convierte en aceptación ni demuestra que instrumentar acelere la aplicación. La variación entre corridas sigue sin atribución causal; los negativos anteriores permanecen. B07abierto y8de18cerrados. Siguiente trabajo: atribución acotada de coste y preparación antes de proponer una corrección distinta; no aumentar recursos, reducir cobertura o relajar criterios para pasar.
