# N01E — resultado de base del diagnóstico operativo

25deoctubrede2026. [Prerregistro352](352-n01-e-consolidacion-escenarios-20261025.md), candidata instrumental568ab46, run20261025-095934-671cae7d. **4PASS,0FAIL/ERROR/SKIP**,18llamadas instrumentadas de servicio. [Auditoría](evidencias/n01-e-snapshot-auditoria-20261025.json), [reportes y reproducción](evidencias/n01-e-snapshot-evidencia-20261025.tar.gz), [congelación](evidencias/n01-e-prerregistro-congelacion-20261025.json). N00aceptado1/13,N01abierto,alfa.

## Coste observado

| Filas PublicationDirty | Primera llamada ms | Mediana5posteriores ms | Rango5posteriores ms | Consultas por llamada |
| --- | ---: | ---: | --- | ---: |
| 0 | 183.843 | 119.093 | 97.073–168.268 |50|
| 10 | 138.306 | 74.147 | 69.455–88.817 |50|
| 100 | 128.480 | 73.149 | 66.514–95.859 |50|

Se mide sólo collect_snapshot; creación de filas, aserciones y lecturas de verificación quedan fuera. La primera llamada no representa frío controlado. Las cohortes se ejecutaron en orden0/10/100, con proceso y conexiones reutilizados; calor/orden/variabilidad impiden interpretar los menores tiempos posteriores como mejora por aumentar filas o por optimizar código. No hubo candidato de aplicación.

El colector conserva cuenta y edad exactas, deja las mismas filas y devuelve autocommit fuera de transacción. Pasó además el test original de transacción PostgreSQL de sólo lectura. Las50consultas incluyen preparación transaccional y agregaciones; no se debe llamarlas50consultas de negocio ni confundir ejecución SQL con toda la latencia. SQLconstante en estas cardinalidades no demuestra coste constante para otras tablas, tamaños o planes.

El comando pytest tardó47,556s con su preparación/QA; no es tiempo de servicio. Sin cuotas de host dedicadas, concurrencia de tráfico, broker o worker medido. Inventario físico y restauración siguen fuera; no hay verificación de proveedor. Fuentes congeladas sin cambios, recursos propios retirados, avisos terminales del runner y auditoría entregados por Telegram.

## Presupuesto técnico anterior a futuros candidatos

Para este escenario concreto, fijar **≤50consultas por llamada** en las tres cardinalidades, manteniendo todos los oráculos y estados. Deriva de las18muestras con50consultas; no es un SLO de latencia ni se extiende a cambios del contenido del diagnóstico. Una futura alteración de alcance debe justificar y prerregistrar su presupuesto antes de medir la candidata.

Pared y ejecución SQL seguirán midiéndose separadamente bajo mismas fuentes de datos, modalidad, orden y recursos. No prometer ahorro temporal por reducir consultas: comprobarlo y declarar inconclusión si la variabilidad no permite atribuirlo. El statement_timeout5s interno sigue siendo protección por sentencia, sin convertirse en límite del servicio. No se calcula p95/p99 con cinco muestras posteriores.

## Antes y después del lote, sin cambio de producto

| Aspecto | Antes | Después | Diferencia/límite |
| --- | --- | --- | --- |
| Base del servicio S09-A | Vacío como propuesta sin nueva observación por operación |18muestras,0/10/100pendientes | Sólo backlog de publicación, no todas las tablas |
| Oráculo actual | Test original pendiente de nueva ejecución |4PASSincluido el original de sólo lectura | No sustituye pruebas de restauración/colas |
| Presupuesto de consultas | Pendiente de base |≤50por llamada en escenario exacto | Fijado antes del candidato; sin mejora causal |
| Aplicación | Base aceptada | Misma aplicación | Sin porcentaje de ahorro |
| Contrato |1/13,N01abierto|1/13,N01abierto| El lote no cierraN01/N10 |

Siguiente: reconciliar semántica del resultado y seguimiento; completar los presupuestos/fichas restantes, con prioridad en autoridad/retención y representación. La matriz352conserva19escenarios y sus huecos. No repetir estas cohortes sin nueva hipótesis o candidato comparable.
