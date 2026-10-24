# B07 — Frontera posterior de captura de recursos

Estado: corrección del instrumento y calibración pequeña verificadas; B07 abierto,8/18.

La revisión tras193/194 detecta que `tests/test_contract_http_load.py` asignaba `arrivals_and_drain` al colector opcional de recursos antes del cliente pero nunca lo devolvía a `idle_after`. La muestra final podía atribuir verificaciones y cierre a la fase de carga. Se añade esa transición inmediatamente después del cliente y su informe GC, antes de contadores/verificaciones posteriores. Las etiquetas son aproximadas a1Hz; la ventana precisa sigue siendo el origen y elapsed del ledger, sin CPU exclusiva por petición ni pico continuo. No se reclasifican artefactos históricos.193/194 tenían el colector apagado.

## Protocolo previo

Cinco guardas existentes pasan; no ejercen la nueva transición integrada. Ejecutar una sola calibración funcional nativa con el mismo comando181,10perfiles/2derechos,60dinámicas/1upload, PostgreSQL/Redis/Gunicorn/Celery/Beat reales propios. Exigir caso PASS sin omisiones, muestras>=2 sin error, presencia ordenada de before_arrivals/arrivals_and_drain/idle_after y muestra final idle_after; cotejar ledger monotónico sin afirmar frontera exacta por etiquetas. Exigir0errores/omitidas/finales, upload302persistido, fuentes congeladas,628fuentes de producto intactas, limpieza propia y Telegram terminal. FAIL/ERROR detiene secuencia y se conserva. No carga grande ni aceptaciónSLO, sin900automático.

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test 'tests/test_contract_http_load.py::test_contract_arrival_rate_http_with_limited_uploads[functional]' --workers 1 --fixture-snapshots --isolate-test-broker --benchmark-normal-refresh --benchmark-beta-promotions --benchmark-service-resources --timeout 300
```

Congelar fuentes y documentación durante la ejecución. El artefacto previo guarda SHA del protocolo y mapa de fuentes. Esta calibración sólo verifica la frontera del instrumento; distribución territorial, filtros, estados y capacidad de matriz180 siguen pendientes. El colector está limitado al runner local y no se adapta por elusión de sus controles a contenedores capacity.

## Resultado terminal

Run `20261021-220724-a0bf8808`:un caso PASS/0FAIL/0ERROR/0SKIP,86,327sJUnit;60dinámicas exitosas/0errores/omitidas/finales y1upload persistido. [Auditoría terminal](evidencias/b07-service-resources-phase195-20261021-audit.json):35muestras/33,576s, etiquetas before_arrivals→arrivals_and_drain→idle_after ordenadas, final idle_after; todas las muestras idle_after posteriores al origen+elapsed del cliente. Nueve procesos persistentes propios,628fuentes de producto intactas; protocolo/mapa de fuentes, contenedores, temporales, PIDs y Telegram comprobados. Cinco guardas separadas PASS; no se suman como seis casos de una misma ejecución integrada.

Primer intento de auditoría falló en la guarda de salida del runner: se inició mientras el proceso aún enviaba el aviso terminal. Se conserva EXIT1; no fue fallo de la prueba ni se repitió TCP. Tras confirmar salida real y recibo delivery=sent se ejecutó de nuevo el mismo auditor, PASS. No atribuir ese primer intento a aceptación de limpieza.

CPU/RSS son del intervalo completo muestreado, no exclusivos de carga. La [captura181](181-colector-recursos-servicios-beta-b07-20261021.md) histórica permanece intacta, incluidas sus limitaciones. La [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md) conserva pendiente volumen/territorio/filtros/estados/colas/recursos bajo presupuesto kernel. No aceptación B07 ni900automático.
