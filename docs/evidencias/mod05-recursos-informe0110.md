# Diagnóstico único MOD05 de recursos — revisión Codex

Autorización expresa: cuatro workers, 10.000 anuncios, 20 RPS durante 30s, 600 dinámicas y un upload. No otro gate ni contractual900s. Preparación oficial MOD05 antes de tráfico y después de crear borradores. Fuente base7ac951c más registro de autorización; hashes exactos en manifiesto congelado. [Revisión independiente](mod05-recursos-revisada0110.json), [recálculo reproducible](mod05-recursos-analisis0110.json), [artefactos originales](mod05-recursos-artefactos0110.json).

## Resultados y poblaciones

Diagnóstico completado:1pytestPASS por obtención de observaciones; filtro de carga VALID/FAIL, nunca capacidad aceptada.600éxitos finales,0errores/noemitidas/timeouts;478durante emisión,122pendientes al cierre; p95cliente7,164s, drain7,617s, upload302. Generador p95/p99/max2,143/3,991/5,974ms. No parada de recursos observada.

600requests dinámicos correlacionados uno a uno con entrada/salida WSGI y PID,200porfamilia. Medias WSGI listado291,223ms/búsqueda331,080ms/ficha95,254ms; medias CPU del thread153,395/158,849/51,071ms. D=Σmedia/3=239,186ms.20D=4,783711worker-s/s. U=servicio upload/60=0,094556worker-s/s, N1 bajo frecuencia contractual1/minuto; W=4,878267worker-s/s. Ocupación durante30s porPID99,483–99,870%,upload incluido. Demora emisión→entrada WSGI media3,937s/mediana4,077s. Cero entradas después del deadline contractual. Cohorte final no mezclada con muestras antiguas ni éxitos del servidor reclasificados.

400requests listado/búsqueda:54state/trusted_state/native_unknown0 y346state/trusted_state/native_unknown1.200fichas handler nativo. Se conserva fallback fresco: no10.000 validaciones inferidas. El upload cambia dependencias; persistencia del candidato desconocido puede relacionarse con ausencia de workerrefresh en arnés, pero el coste específico no está aislado y no se declara causa dominante ni autorización para ignorarlo.

Intervalo interior de emisión observado28,99997s/30muestras: host5,685868CPU; cuatro workers estables1,966209CPU; PostgreSQL compartido estable1,344829CPU; dockerd0,976898CPU. Contadores de procesos presentes en ambos extremos; procesos transitorios omitidos. No coste individual PostgreSQL. Estados pg_stat_activity son conteos de muestras, no duraciones. Recolector5,892539CPU-s en55,32572s, incluido enhost, overhead causal no cuantificado. MemAvailable mínimo10,683GB. Quotas/PSI ausentes se conservan not_measured enoriginales; no garantizan ocho cores permanentes.

## Decisión y límites

La demanda observada supera la ocupación disponible de cuatro workers y coincide con acumulación, conCPUdelthread inferior aWSGIwall. No queda demostrado si el resto es espera deSQL/red, scheduling, conversiones uotrotrabajo; no atribuir total−SQL avalidación. No se justifica otrorefactor ciego ni aumentarworkers automáticamente. Una evaluación futura deconcurrencia necesita comparación controlada conrecursos eidéntica ruta/refresh; seis sigue candidata, noadoptada. Alternativamente aislar coste residual actual con perfilfinito antesdecambiarcódigo. No sumar estos tiempos aahorros históricos ni atribuir diferencias frente60s/portátil a una causa exclusiva.

Limpieza independiente DB/medios y cuatroPIDobservados ausentes,logs originales preservados. Sin cambios permanentes oserviciosajenos, ningún nuevo900s. CR09/GS01 ycontrato abiertos, porcentajes yveredictoshistóricos intactos.
