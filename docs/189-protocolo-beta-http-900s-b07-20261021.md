# B07 — Protocolo definitivo beta HTTP900s

Estado: ejecución terminada INVALID por retraso máximo del generador; no acredita capacidad900s. B07 abierto, ocho de dieciocho puntos cerrados.

## Prerrequisitos y versión

Dos cortos acotados [184](184-corto-beta-cuotas-beat-20261021.md) y [186](186-confirmacion-unica-corto-acotado-b07-20261021.md) pasan independientemente; confirmación única agotada, sin promediar percentiles. [187](187-modo-beta-http-contractual-b07-20261021.md) implementa selector exclusivo y33focales en su corte; [188](188-calibracion-quince-subidas-beta-b07-20261021.md) añade24focales actuales y calibración real15subidas/300dinámicas. Los conjuntos se conservan separados, no una única batería57sobre fuentes idénticas.

Antes de lanzar: rehashear artefactos de ambas referencias y calibración, verificar sus auditorías y avisos enviados, confirmar limpieza fresca y ausencia de entorno de capacidad activo. Código runtime actual idéntico a la calibración188; sólo cambios de metadatos .ai/.graphifyignore permitidos en su mapa. Frente a los cortos, declarar los ocho archivos de herramientas/fixtures ampliados en187–188;628fuentes app/config/templates intactas. La imagen inmutable local debe seguir presente, sin pull/build/retag. Archivar copia íntegra de este protocolo y SHA antes de iniciar.

## Recursos y escenario congelados

Misma imagen `sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede`. CPU/RAM por rol: PostgreSQL3CPU/3072MiB, Redis0,2CPU/384MiB, app3,5CPU/3968MiB, RustFS1CPU/512MiB, Caddy0,2CPU/128MiB y controlador0,1CPU/128MiB. Total8CPU/8GiB, swap0, storage≤20GiB; límites kernel verificados antes de carga. Sin reasignaciones ni cambios a servicios normales.

Nueva cohorte sintética propia10000perfiles publicados/2000derechos nativos(667Premium/1333Top), misma agencia/fotografía y municipio; censo completo, no diversidad nacional. Órdenes/eventos firmados sintéticos por servicios reales, misma autoridad fresca y rol runtime. Quince borradores distintos, ocho tablas ANALYZE, refresh y limpieza de mensajes de preparación antes de iniciar runtime. Cuatro Gunicornsync/unhilo/timeout60, Celeryprefork2 y Beat reales en el cgroupapp.

900s a20RPS open-loop:18000dinámicas con IDs únicos,6000listado/6000búsqueda/6000ficha,9000ES/9000EN. Quince uploads adicionales separados: t=0,60,…,840s sobre quince borradores distintos, mismo multipart sintético original; cada uno302 y una Photo+UploadAttemptaccepted/duplicate persistidos, sin aceptar repeat como prueba de nueva ingestión. No computarlos entre las18000dinámicas. Sin calentamiento extra; seis primeras lecturas frías200/no-store y patrocinio. FaseBeat objetivo+5s, GCpreparado antes del reloj, sinfreeze ni cambio de política; registrar desplazamiento real.

## Validez, límites y parada

Demoras generador p95≤10ms/p99≤25ms/máximo≤100ms; cero no emitidas. TimeoutHTTP65s, drain70s, ventana900s y duración total de workload+drenaje≤970s; contabilidad completa por población, pendientes dinámicas ventana≤20 y finales0. Quince subidas emitidas/exitosas302 y contabilidad reconciliada. Percentiles incluyen todas las dinámicas terminadas, no sólo éxitos: p95observable<800ms y erroresinesperados<1%, denominador18000. No sustituir esta fracción por exigir18000éxitos; los fallos siguen visibles.

Mismos observadores declarados del corto/calibración: eventosCelery, GCcliente y VmHWM de procesos propios; sin profilerWSGI/SQL/render ni capturas nuevas durante control. CPUcgroupfinal incluye preparación, no CPU/request ni sólo ventana; memoria es cota conservadora, no pico simultáneo. Exigir≤6GiB según método existente, PIDindividual≤1GiB y storage≤20GiB. No atribuir variación de latencia a mejora causal de producto.

Veredicto BETA_HTTP_CONTRACTUAL_PASS_NOT_GLOBAL sólo con todos los criterios y evidencias completos; FAIL válido BETA_HTTP_CONTRACTUAL_FAIL, generador/contabilidad inválidos INVALID_BETA_HTTP_CONTRACTUAL; setup, timeout o prueba incompleta conservanERROR. Un resultado negativo detiene esta secuencia y se conserva; no repetición automática ni ajuste de criterios. Un PASS permite revisar una eventual confirmación separada conforme16MOD08, no la inicia por este protocolo.

Paso pytest máximo3600s y vida app4200s, lanzador conserva su límite propio. Estimación basada en preparación previa: unos14min de preparación más15min de carga y drenaje, con margen de arranque/limpieza; no prueba prevista de horas. Goal permanece activo. Si se pierde observación, comprobar el mismo handle/proceso y artefactos; no relanzar por timeout de observación.

## Lanzamiento y evidencia

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 beta HTTP contractual900s' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-contractual --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Telegram inicio confirmado antes de ejecutar, terminal después de limpieza. Congelar fuentes, docs, .ai y grafo; sin otras pruebas/builds/refrescos durante ejecución. Sólo lectura y artefactos ignorados de seguimiento. Al terminal: reauditar JUnit, fuentes, protocolo, ledgers, mezcla, cada upload/persistencia, faseBeat/GC/roles, kernel/recursos, procesos/limpieza fresca y recibos. Conservar raw y negativos históricos sin reescritura.

El PASS sólo acreditaría este escenario y fuente dentro de cuotas. Faltan las mezclas territoriales/filtros/páginas/backlog, recursos porventana y PRODUCTION/checked de [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md); no aceptar B07global, B08–B11, B16, N3, proveedor, capacidadInternet ni producción por extrapolación. Scope genérico heredado del controlador no reemplaza evidencia específica. Sin datos reales, publicación, contratación ni servicios externos nuevos.

## Resultado terminal auditado

Corrida `20261021-203352-b43038d6`: **INVALID_BETA_HTTP_CONTRACTUAL**, salida1, un caso fallido de1751,255sJUnit. La [auditoría terminal](evidencias/b07-beta-http-900s-invalid-20261021-audit.json) recalcula los18000IDs y conserva el protocolo original SHA `fa9eb668f332b04e644ab5c1f20b6dacc66c0fb5cd95dd6cabe82d1a62c93cd1`. El máximo de demora del generador143,154ms supera100ms; p953,478ms y p997,002ms cumplen sus límites. No flexibilizar el criterio ni repetir automáticamente esta secuencia.

18000dinámicas exitosas, cero errores/noemitidas/pendientes finales; dos pendientes al cierre. Quince uploads302 sobre quince borradores distintos, persistencia verificada por el caso. p95observable375,277ms es descriptivo de una corrida inválida y no acepta capacidad. Fuentes idénticas al corte congelado, limpieza fresca y recibo Telegram terminal comprobados. B07 sigue abierto y el total permanece8/18.

Durante la espera se guardó relevo y se compactó contexto. Por instrucción posterior del usuario, un disparador persistente reactivó este mismo goal tras el terminal y el aviso confirmado, conservando consumo; no hubo sondeos del modelo durante la pausa. Esto sustituye la previsión inicial de mantenerlo activo, sin alterar el protocolo de carga.
