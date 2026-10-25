# N06A — atribución auditada del SQL al iniciar revisiones

25 de octubre de 2026. [Protocolo356](356-n06-a-prerregistro-atribucion-revisiones-20261025.md), candidata instrumental69bc463, run20261025-103234-0e1e2151. **2PASS,0FAIL/ERROR/SKIP**,3inicios POST302 con oráculos originales de revisión/rechazo sin cambios. [Auditoría](evidencias/n06-a-atribucion-auditoria-20261025.json), [reportes originales y reproducción](evidencias/n06-a-atribucion-evidencia-20261025.tar.gz), [congelación](evidencias/n06-a-prerregistro-congelacion-20261025.json). N00/N01aceptados2/13;N06 abierto,alfa. No hay candidato de aplicación ni optimización demostrada.

## Atribución observada

| Estado/original | Ordinal de inicio | Total SQL | create_draft | Autoridad gestor | Tarea foto eager | Tarea state eager | Resto petición |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| approved | 1 | 116 | 11 | 2 | 55 | 34 | 14 |
| rejected_correction | 1 | 116 | 11 | 2 | 55 | 34 | 14 |
| rejected_correction | 2 | 124 | 11 | 2 | 63 | 34 | 14 |

En los dos primeros inicios,89/116consultas (76,7%)pertenecen a tareas eager; en la corrección,97/124(78,2%). Son porcentajes de **consultas**, no de latencia, CPU o coste total de aplicación. Cada consulta está en una única etapa; las ocurrencias de tablas con joins no son sumables como consultas adicionales. Se verificaron campos permitidos, números finitos y partición exacta por etapa y verbo, sin SQL, parámetros o identificadores de sujetos persistidos.

Las tareas sí ejecutan código real de aplicación sobre PostgreSQL y archivos locales; el modo eager coloca ese trabajo dentro de la petición de esta prueba. No son tareas de un worker/broker medidas y no se declara falso que su coste exista en la aplicación. Cambia dónde se observa, según la configuración. Tampoco se demuestra que el77–78%del tiempo del panel sea trabajo de fondo.

El código directo create_draft consume11consultas en las tres observaciones. Autoridad consume2y el resto14. La señal116/124no basta para afirmar N+1 de clonación: el aumento observado de8consultas pertenece al procesado de foto eager. Las consultas fuente de copia de campos/filas no crecen entre estos tres estados; no se extrapola a otros tamaños de galería, actores o historiales.

No se obtiene un presupuesto del camino encolado restando89/97del total. El despacho y la concurrencia con un worker real pueden cambiar condiciones, consultas, estados y tiempos; requieren su propia ficha y base antes del candidato.

## Tiempos y condiciones

| Estado | Ordinal | Pared instrumentada ms | Ejecución SQL ms |
| --- | ---: | ---: | ---: |
| approved | 1 | 456.182 | 202.946 |
| rejected_correction | 1 | 496.601 | 256.990 |
| rejected_correction | 2 | 556.703 | 285.061 |

La pared incluye el observador de stack y trabajo no SQL; ejecución SQL excluye el coste del clasificador. No son tiempos equivalentes al observador más simple N01D y no hay comparación causal de latencia. Una muestra por estado no acredita p95/p99 ni capacidad. El paso pytest tardó51.294s con preparación/QA; no es latencia de una acción. Sin cuotas dedicadas o frío controlado.

PostgreSQL17/Redis7.4 propios, mismas fixtures eager y cuerpos originales. Fuentes congeladas sin cambios durante la ejecución/auditoría; contenedores propios y temporal ausentes. Telegram terminal del runner y auditoría correctiva entregados. Se conserva el primer error de lint F811 del instrumento y su corrección, y el primer error auxiliar de importación de auditoría con su recibo. No fueron FAIL de aplicación; las dos pruebas válidas no se repitieron para corregir la ruta del auditor.

## Antes y después del diagnóstico

| Aspecto | Antes N06A | Después N06A | Diferencia/límite |
| --- | --- | --- | --- |
| SQL de listing_start |116/124sin atribución de etapa en N01D |11copia+2autoridad+14resto, más89/97tareas eager | Mismo conteo total observado; mayor atribución, no reducción |
| Hipótesis de clonación | El total podría interpretarse como coste directo | El grueso del conteo está en tareas eager; copia11en tres estados | No N+1demostrado ni capacidad de otros tamaños |
| Petición con cola normal | Sin base actual comparable | Sigue sin base; motivo y etapa siguiente concretados | No inferir resultado restando consultas |
| Código de aplicación | Base aceptada | Misma base, sólo instrumento | Sin porcentaje de mejora de producto |
| Contrato |2/13,N06iniciado|2/13,N06en curso| Este lote no cierraN06 |

Siguiente: refrescar semántica del resultado/seguimiento y estudiar los helpers locales de worker/broker para un prerregistro normal encolado, con permisos/instantánea/bytes/paridad y condiciones de reintento/revocación preservadas. No cambiar la fixture para rebautizar una reducción de QA como optimización de aplicación. Después elegir candidato sólo sobre coste demostrado en su etapa, y completar los otros escenarios N06 de cuenta y representación.
