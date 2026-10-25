# N01B — Prerregistro de segmentos sobre una población fija

25 de octubre de2026. Continúa N01/S01 después del [resultado345](345-n01-a-diagnostico-descubrimiento-20261025.md), ya incorporado semánticamente antes de analizar este hito. N00 sigue aceptado1/13; N01 y N04 permanecen en curso. No hay candidato de producto ni mejora atribuida. Alfa.

## Pregunta y selección

N01A observó tiempos/SQL distintos entre10y100perfiles, pero cambió población y orden de ejecución. Este lote mantiene100publicados y registra por escenario la primera petición medida y cinco posteriores. No se fuerza caché de aplicación/OS/PG fría: seed_demo, preparación y escenarios anteriores pueden calentar dependencias. El orden se conserva y publica: ES antes deEN; listado, página2, filtro de perfil, búsqueda vacía y ficha dentro de cada idioma. No atribuir diferencia causal a idioma o calentamiento.

Instrumento nuevo: tests/test_discovery_segment_baseline.py, un único caso transaction=True. Genera100perfiles con los helpers existentes, sin cambiar aplicación, activar promociones, sustituir state_page o mutar guards. Diez segmentos por seis muestras:60peticiones Django HTTP Client, seriales, sinTCP/workerBeat/navegador real/concurrencia. Cada segmento usa la misma población y parámetros en sus seis peticiones. SQL execute_wrapper cuenta y cronometra la llamada original; no captura valores, cuerpos o SQL literal.

Oráculos independientes de resultados para este fixture: IDs y orden esperado obtenidos de la población publicada sintética por published_at descendente/PK ascendente; página1 y2 usan sus tramos, filtro de perfil usa el subconjunto declarado, búsqueda de término sintético ausente devuelve cero y ficha corresponde al ID previsto. Cada muestra debe devolver200/no-store, idioma esperado, sin el email privado centinela de la fixture y exactamente los IDs/conteo previstos. No usar el mismo paginador del producto como referencia. El conjunto sintético pretende ser íntegramente elegible; no acredita todos los estados negativos.

El filtro elige un profile_type declarado distinto del selector especialtrans, fuera del intervalo medido; no infiere atributos. Las fotografías clonadas y geografía limitada conservan los límites de populate. La firma del orden se registra porhash, sin exponer IDs o sujetos reales. La ficha también usa el guard nativo y la transacción de su implementación actual.

## Criterios y medidas anteriores a la ejecución

Un caso y60muestras obligatorias, sin FAIL/ERROR/SKIP ni cambios de fuentes. Gates funcionales de cada respuesta y población final100. Tiempo wall instrumentado, cantidad y wall de execute, ruta/reason de publicación si está disponible, tamaño devuelto yhash orden. Para cinco muestras posteriores se registran mediana/mínimo/máximo; no p95 ni prueba de20RPS. No estimar tiempo Python restando execute ni afirmar tiempo puro de servidor SQL.

Es diagnóstico de referencia: sin techo temporal nuevo para sustituir presupuestos pendientes. El criterio<800ms contractual conserva su escenario y no se evalúa con estas muestras. Antes de adoptar un candidato se fijará comparación equivalente y presupuesto sobre base suficiente. Primera/posteriores no es una tabla antes/después de optimización; cada bloque cerrado tendrá su tabla causal o límite explícito según340.

## Entorno y comando

Mismo runner local oficial, PostgreSQL17/Redis7.4 propios, un worker y librdb2.4.0 fijado, dependencias offline y manifiestos/imagen registrados en congelación. No afirmar cuotas8CPU/8GiB o comparabilidad con la antigua carga contractual. Grafosemántico de este prerregistro y AST del nuevo instrumento antes de congelar. Preservar1507fuentes ejecutables previas; sólo se añade este instrumento, con SHA propio. Sin datos reales, proveedor o pago.

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test tests/test_discovery_segment_baseline.py --workers 1 --timeout 900
```

Timeout por paso, no SLA ni ETA. Previsión acotada, no batería de horas; aplicar protocolo persistente/pausa/compactación/retorno del mismo goal si aparece una espera previsiblemente larga. No editar fuentes/documentos durante ejecución. Auditar JUnit,60muestras, oráculos, fuentes, limpieza y Telegram antes de interpretar. Un fallo de fixture/instrumento se conserva y se corrige con evidencia; no se transforma en mejora o PASS de aplicación.

Pendiente fuera deeste lote: promociones, distribución/retención y tamaños grandes, combinaciones de filtros y profundidad más allá de página2, estados negativos, browser/carga, y otros ocho grupos. No cerrar N01 oN04 por60muestras ni iniciar otra batería contractual por rutina.
