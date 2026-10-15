# Diagnóstico de arranque con ocho procesos y kernel nativo

Run `20261015-232822-f60cfe0d`, SHA `3a881187bc5510096e106851a5e84d9ddbf0f960`. Diagnóstico separado tras el fallo limpio; sin cambio de aplicación. Kernel `native-sealed` obligatorio antes de recursos y registrado en resultado. Mismos límites propios; ocho sync dentro de cuatro CPU. WSGI/SQL/GC e identificación de peticiones más contadores de CPU de cgroups propios a1Hz. [Recibo terminal](cr09-eight-native-ingress-terminal-20261015.json).

1200 identificadores emparejados cliente/WSGI/Gunicorn, cero errores de parseo, 1200 respuestas200, cero errores/timeouts/omisiones/pendientes finales y subida302. Generador válido. Test **FAIL /185,85s**; no acredita capacidad.

| Métrica | Último limpio nativo8sync | Diagnóstico nativo8sync |
| --- | ---: | ---: |
| p95 HTTP s | 1,792941386 | 1,152858585 |
| Errores / completadas | 0 /1200 | 0 /1200 |

Contextos distintos: no interpretar diferencia como mejora/regresión de código o evidencia de reproducibilidad.

| Media de las mismas peticiones | 0–5s,100 | 15–60s,900 |
| --- | ---: | ---: |
| HTTP ms | 1184,935 | 217,212 |
| Antes de WSGI ms | 747,214 | 1,120 |
| WSGI ms | 437,891 | 216,352 |
| CPU del thread ms | 124,023 | 103,293 |
| SQL wall ms,inclusivo | 272,176 | 90,364 |
| GC wall ms,inclusivo | 13,366 | 8,207 |
| Consultas SQL | 42,64 | 38,00 |

86 lentas>=0,8s:80 emitidas0–5s y6 entre5–10s, ninguna después. Los ocho workers recibieron antes de0,303s; no hay worker ausente durante todo el arranque. Antes de WSGI incluye cliente/transporte/admisión/parseo/scheduling, no cola pura. WSGI/SQL/GC son inclusivos, no sumar. Residuo posterior puede ser negativo por cierre WSGI después de recepción.

PG ejecutó0,863cores medios iniciales frente0,483estables, cero periodos con throttling en ambos intervalos. Controller completo2,435 frente2,119cores, incluye pytest/generador/Celery/observador. No se midió presión del hipervisor; PSI no está expuesto en el host. No prueba suficiencia de hardware ni causa por sí solo.

Caller dominante `public_validation.py:263` es **list(query)**: agrupa hidratación y múltiples prefetch, no una consulta única. Suma SQL media atribuida a ese caller87,234ms inicial/22,743ms estable,7,8/6,667ejecuciones. Count/selección de población `publication_state.py:447` aporta37,639/5,815ms. Rama dirty general388/446 aparece al principio. No elegir índice/compilador o cachear autoridad a partir de un caller agregado. Siguiente investigación acotada: separar consulta principal de prefetch y planificación de ejecución con datos sintéticos; conservar semántica y guardia final.

[EXPLAIN PostgreSQL17](https://www.postgresql.org/docs/17/using-explain.html) permite distinguir planificación/ejecución y buffers; ANALYZE añade sobrecoste y se ejecutaría fuera de la medición HTTP. Éste es el instrumento siguiente para una hipótesis SQL concreta, no un resultado aún obtenido. No otro ensayo limpio ni barrido de workers.

Limpieza comprobada independientemente: fuentes sin cambios, controlador/hijo/ocho workers/Celery ausentes, temporal y contenedores propios retirados, unidad terminalMainPID0/ControlGroupvacío. Fuentes exactas de instrumentos en `instrumentos-cr09-eight-native-ingress-20261015`, hashes en recibo. JSON original conserva texto heredado pg_server_shared, incorrecto para el adaptador: servicios reales propios y limitados. CR09/N3 abiertos.
