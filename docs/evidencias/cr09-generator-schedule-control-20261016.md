# Sonda aislada del generador: controles conocidos

[Recibo](cr09-generator-schedule-control-20261016.json). TrescontrolesPASS0,50s; ningún Django/PG/HTTP/carga real. No explica todavía el retraso113,55ms del contractualINVALID.

Sonda tests-only del bucle SelectorEventLoop de Python3.12.15, con relojes de pared/CPUdelhilo y `/proc/self/task/TID/schedstat`. Separa intervalos del selector y ejecución posterior de callbacks; conserva hasta256intervalos significativos≥20ms, sinrepresentacionesdecallbacks/URI/headers/cuerpos. El timer ordinario no se atribuye como CPU; callback40msCPU se detecta con≥35msCPU; sleep40msbloqueante con≥35mswall/<20msCPU. Las deltas son inclusivas y solapadas; no sumarni imputar toda diferencia a runqueue. No manipulaGC/afinidad/prioridad/permisos/emisor/límites.

[Linux define](https://docs.kernel.org/6.13/scheduler/sched-stats.html) runtime y espera runnable en nanosegundos; [Python3.12 permite](https://docs.python.org/3.12/library/asyncio-runner.html) loop_factory para ensayos aislados. La implementación usa hookprivado `_run_once`, acotado a diagnóstico y no producción. Sobrecoste no medido; jamásaceptar p95 desde esta sonda. Se preserva warning de pytest al intentar caché bajo /dev por configaislada; tests completos, sin efectos DB.

Siguiente paso: integrar la sonda únicamente en un modo diagnóstico explícito de generador, conservando el emisor/criterios originales. Una ejecución diagnóstica finita con recursos propios necesitará prerregistro y limpieza; no es repetición de aceptación. Si no reproduce retraso, no inventar causa ni encadenar ensayos.
