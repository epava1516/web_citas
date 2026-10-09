# Seguimiento de ejecución del contrato

Actualizado: 2026-10-09. Fuente contractual: [contrato16](16-contrato-ejecucion-desarrollo.md). Este documento mantiene el estado y la única cola de ejecución; evidencias y condiciones de cierre se enlazan desde él.

## Estado vigente para reanudar

**Desarrollo contractual bloqueado; saneamiento técnico completado.** La auditoría del 2026-10-09 confirmó durante tres turnos consecutivos que no hay un requisito local independiente ejecutable nuevo demostrado. Faltan los insumos concretos del [acta residual](evidencias/residuales-locales-post-aceptacion0110.json), resumidos en la [matriz única de pendientes](83-auditoria-pendientes-cr09.md). Las reanudaciones y pausas anteriores son antecedentes históricos.

La organización documental actual no reanuda el desarrollo, no autoriza cargas y no reabre componentes aceptados. Se retoma ante un insumo concreto autorizado o un requisito/defecto nuevo demostrado. Codex conserva arquitectura, integración y aceptación.

Mantenimiento autorizado el 2026-10-09: retirar instrumental descartado sin consumidores actuales. Fuentes afectadas: `scripts/benchmark_call_profile.py`, `scripts/benchmark_local_monitor.py` y sus dos archivos de pruebas exclusivos; código de aplicación y esquema fuera del cambio. Verificación N1: referencias/imports, colección de pytest, pruebas de observadores que sí siguen en uso, Ruff, enlaces y diff. Sin PostgreSQL de integración ni cargas: se eliminan herramientas autónomas, no comportamiento persistente. Resultado: cuatro archivos y 337 líneas retirados; cero referencias en código activo, 14 pruebas pertinentes PASS y 2.073 casos recogidos sin errores. Ruff global conserva 280 incidencias idénticas a HEAD, sin incidencias nuevas. [Registro y límites](evidencias/limpieza-instrumental-descartado-20261009.json). Mantenimiento concluido; el bloqueo de desarrollo contractual sigue vigente.

## Saneamiento técnico autorizado — completado

Petición del usuario2026-10-09: resolver deuda detectada. Ruff global PASS:233 incidencias corregidas y47 diagnósticos de variables inyectadas documentados en dos fragmentos históricos conservados byte a byte. Rutas:89 trasladadas a `safety/urls.py`; las156 mantienen orden, argumentos y callbacks. Se corrigió una omisión demostrada: el adaptador de colas no reconocía refresco/barrido MOD05 sin argumentos y bloqueaba respuestas de acceso. Los argumentos o envelopes inesperados siguen rechazados. Preparación nativa reproducible y requisitos CI incorporados.

Verificación terminal: batería inicial120 casos,112 PASS/8 FAIL; cuatro fallos por binarios nativos ausentes y cuatro por la omisión. Correctiva posterior97 PASS, incluidas las ocho variantes fallidas, interfaz ES/EN, Redis físico/orígenes y guards. Worker/Beat reales PASS en la batería inicial. Unitarios16 y26 en runs separados; colección completa2085 casos sin errores. No se suman versiones/entornos como N3 ni se afirma ejecución completa de2085. Primera pasada interrumpida por variable Redis incorrecta, sin acreditar aislamiento ni sumar sus casos. [Fuentes, artefactos, huellas, preparación y límites](evidencias/saneamiento-tecnico-20261009.json).

PostgreSQL/Redis desechables, medios, checkout nativo y binarios propios retirados tras preservar evidencia. Modelos/reglas y servicios normales sin despliegue deliberado; CI externo no ejecutado. Capacidad de expedientes y demás insumos de matriz83 siguen pendientes. Pesos/porcentajes y aceptaciones de fases intactos.

## Entrega aceptada y runtime

| Alcance | Estado y fuente |
| --- | --- |
| BASE y CR01–08 | Verificados localmente; 9 de 15 hitos. [Actas](README.md#verificar-una-entrega) y [componentes reutilizables](88-matriz-cierre-derechos.md). |
| CR09-REND-LECTURA | Aceptado expresamente por el usuario el 2026-10-09 en `1a10ecf86a808daf9ae4dd2f72fbe414d5fc3c91`, con datos y proveedor sintéticos; integrado en master por fast-forward en `7691642`. |
| Servicios normales | Código desplegado `73d28f6`, migración Docker de derechos `0110`; núcleo de purga `72ff79a`. La integración de lectura aceptada no se desplegó en esos servicios. La versión de esquema de `listings` se distingue de `safety 0110`. |
| CR09 integral y fases posteriores | Abiertos; las preparaciones CR10/UI/ESEN/accesibilidad/SEO se reutilizan, sin aceptación de CR10, GS01, BF/BB o C. |
| Producción | Pendiente de gates y evidencia externa; sin publicación, contratación o datos reales. Cobros reales fuera de v1. |

## Evidencia y límites de la lectura aceptada

La revisión de Codex reutilizó artefactos originales y comprobó huellas y recálculos, sin nuevas cargas. [Informe de gates](evidencias/mod05-gates-normal-informe0110.md), [comparación 4/6](evidencias/mod05-capacidad-4-vs-6-refresco-informe0110.md) y originales [60 s](evidencias/mod05-gate-normal-short-artefactos0110.tar.gz), [900 s intento 2](evidencias/mod05-contractual-normal-intento2-artefactos0110.tar.gz) y [4/6](evidencias/mod05-capacidad-4-vs-6-refresco-artefactos0110.tar.gz).

| Escenario | Resultado conservado |
| --- | --- |
| Gate normal, 60 s | PASS: 1.200 éxitos, cero errores, p95 621,608 ms; pendientes de ventana 5 y finales 0, upload 1/1, drain 0,133 s. |
| Contractual normal, 900 s, intento 2 | PASS: 18.000 éxitos, cero errores, p95 392,360 ms; pendientes de ventana 7 y finales 0, uploads 15/15, drain 5,087 s. |
| Contractual normal, intento 1 | INVALID por demora del generador; no se sustituye por el resultado posterior. |
| Comparación 4/6 | Beneficio de seis FAIL en ambos pares; cuatro workers siguen como referencia, seis no adoptados. |

La [cobertura positiva](evidencias/mod05-cobertura-positiva0110.json) de [la prueba](../tests/test_publication_positive_coverage.py) conserva equivalencia byte a byte con la vía nativa y ruta `state`, ES/EN: normal 25 sin filtro/contact/agency y 10 con `checked` age; PRODUCTION 10 en todos los filtros. No acredita verificación externa real. La prueba positiva conserva código y resumen, sin JUnit original, y no fue repetida por Codex.

Los gates no archivan logs originales de Gunicorn ni eventos WSGI individuales. Host compartido, fixture y topología `normal_worker_beat` delimitan el PASS. No se acredita capacidad con grandes poblaciones positivas PRODUCTION/`checked`. Página 3 y promociones sintéticas conservan las limitaciones del informe; promociones usan fallback nativo medido. No se separan causalmente el efecto de la topología y el de la corrección de la marca sin señal, ni se atribuye la corrección GC del generador al backend. Todos los FAIL/INVALID/PASS anteriores conservan sus escenarios.

## Próximo trabajo y criterio de salida

CI propio autorizado2026-10-09 y entregado: el usuario indica que no hay presupuesto para CI alojado y solicita gestionarlo nosotros. `scripts/run_local_ci.py` sustituye la dependencia operativa de GitHub con recursos desechables y evidencia local; GitHub queda solo manual. Perfil `smoke`:70 PASS/0 skips en357,03s, broker/publicación/Redis físico con PostgreSQL17 y Redis7.4 propios. Comprobaciones finales PASS; control negativo con checkout nativo inexistente devuelve ERROR/salida1 y limpia sus recursos. Las tres ejecuciones conservan huellas iguales y seis contenedores retirados. [Resultado y límites](evidencias/ci-local-20261009.json), [artefactos](evidencias/ci-local-20261009-artefactos.tar.gz) y [procedimiento](ci-local.md). Dos ajustes posteriores del postprocesamiento del ejecutor se verificaron con checks/control negativo, sin repetir ni sumar la batería funcional como N3. Sin cargas de capacidad, publicación, ejecución alojada o gasto. Facturación GitHub deja de ser prerrequisito; N3 y demás insumos continúan según su alcance.

Petición posterior2026-10-09: encargarse de los pendientes del saneamiento; el usuario eligió preparar una propuesta de capacidad. [Propuesta concreta](propuesta-cierre-pendientes-locales.md): tamaños, concurrencia, recursos y límites por etapa para revisión, sin aprobarlos ni ejecutar cargas nuevas. CI leído realmente: ejecución37874402205 bloqueada antes de iniciar pasos por facturación/límite de gasto de GitHub, acción del titular. Workflow local conserva JUnit y manifest nativo ante fallos; sin publicación ni ejecución externa. Esta preparación no acepta N3 o CR09 ni cambia porcentajes.

1. Consultar el [bloque pendiente](83-auditoria-pendientes-cr09.md) y su insumo requerido; no repetir otra ronda de auditoría sin nueva información.
2. Cuando exista insumo autorizado o defecto demostrado, registrar aquí requisito, fuente, resultado observable y condición de salida. Reutilizar los [alcances cerrados](88-matriz-cierre-derechos.md) y ejecutar solo el trabajo pertinente.
3. Aplicar N1/N2/N3 según contrato16. N3 común sigue siendo responsabilidad de Codex cuando se satisfagan sus prerrequisitos; no se traslada al usuario ni se compone sumando versiones distintas.
4. Tras satisfacer CR09 y sus condiciones contractuales, continuar CR10 → GS01 → BF/BB → C. Las preparaciones independientes no adelantan la aceptación formal de fases.

## Avance ponderado vigente

Revisión v10: **CR09 72,50%** y **contrato 65,375%** (65,38% mostrado). [Método y tablas](86-medicion-avance-contrato.md), [cálculo original](evidencias/avance-ponderado-v10.json). Estimaciones de ingeniería por alcance; no horas, número de pruebas ni aceptación de fases. Esta organización y el cierre local de lectura no cambian pesos, denominador ni porcentajes.

## Reglas de continuación

Una cola, entregas completas y PostgreSQL en integración. Datos y medios sintéticos, recursos propios y limpieza. Reutilizar evidencia válida y mantener sus fuentes, versiones y límites; congelar fuentes durante ejecuciones vivas. Una hipótesis finita y una condición de salida antes de diagnosticar; sin pruebas o cargas por rutina. No publicar, contratar proveedores, usar datos reales ni modificar servicios ajenos.

Claude propone; Codex aplica y verifica. No hay máximo numérico desde MOD-03. Antes de delegar leer completo el contrato externo AI_ENGINEERING 1.0.1 y usar su `scripts/claude-task`, sin copiar ni alterar el adaptador. Consumo e invocaciones conservados en `.ai/tasks/desarrollo.md`; no sustituirlos por resúmenes de grafo.

## Historial y organización documental

[Copia íntegra anterior](17-historial/2026-10-09-17-seguimiento-desarrollo-antes-organizacion.md): conserva exactamente las 751 líneas previas, incluidas decisiones, verificaciones, fallos y antiguos próximos pasos. [Historial anterior](17-historial-desarrollo.md), [inventario de copias y huellas](historial-documentacion.json) y [registro de esta organización](evidencias/organizacion-documental-20261009.json). Las copias son consulta de evidencia, no una segunda cola; sus enlaces relativos conservan la base registrada en el inventario. [Comprobación de documentación](README.md#mantener-la-documentación).
