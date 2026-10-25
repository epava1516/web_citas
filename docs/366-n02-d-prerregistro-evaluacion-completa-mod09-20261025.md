# N02D — evaluación completa actual de MOD09 tras adoptar el guard

25 de octubre de 2026. Base75f5dcc y [adopción local365](365-n02-c-resultado-contraste-agrupado-guard-20261025.md). N00/N01aceptados2/13,N02/N06abiertos,alfa. El guard está verificado en su etapa;no demuestra objetivos del circuito completo. Grafo previo1961fuentes/18414nodos/80880relaciones verificado antes de estudiar este hito;refresco semántico focal de este protocolo/seguimiento antes de congelar la ejecución. No se modifica aplicación,instrumentos,fixture ni umbrales.

## Decisión de evidencia y motivo

La investigación por fuentes propuso reutilización de descifrado/parseo como hipótesis. Existe [diagnóstico grande anterior](evidencias/mod08-unseal-lote-grande-20261011.md):descriptor223141bytes,parseo repetido31,466msCPU frente a195,651ms de copia;no eran16MiBdescifrados porllamada. No se implementa memoJSON con copia ni se comparte un dict mutable. Este diagnóstico inicial con31lecturas no representa la cadena acumulada del p95;es límite histórico,no perfil causal actual ni descarte eterno de toda optimización. Mantenerlo evita repetir una propuesta ya contradicha sin evidencia nueva.

La única fuente de aplicación distinta respecto a la [medición completa326](326-auditoria-medicion-actual-mod09-b10-20261024.md) es rights_portability_export.py por el guard adoptado. Se evalúa ahora el circuito completo vigente,con estado/recursos/cuerpos reales;no se repite para borrar suFAIL ni se atribuye exclusivamente al código cualquier diferencia entre fechas/entornos. Los tiempos locales instrumentados365no se extrapolan a descarga ni se mezclan con percentiles.

## Secuencia fija autorizada

1. Control actual de preparación: controlador oficial run_capacity_environment --preflight-only --object-delivery --cpu-budget8 --app-image sha256:f50e2f01874ebbd1147261160c6058c64bf2e8d26d50b2446c7549d2692b947b. Un control pequeño de topología/S3/proxy/worker/cuotas/cuerpos/replay,no población de capacidad. Debe terminarREADY_NOT_CAPACITY,exit0,fuentes intactas y limpieza;si falla,no ejecutar carga completa.
2. Una sola evaluación completa,misma fuente congelada: --selection-tcp --selection-concurrent --selection-gunicorn --database-heavy --object-delivery --cpu-budget8 --delivery-complete y la misma imagen soporte inmutable local. Selección original test_owned_complete_target_delivery:un caso con dos sujetos sintéticos independientes concurrentes,1500revisiones/~16MiBJSON y16WebP/~64MiB originales por sujeto. Todas las lecturas/aprobaciones/cuerpos/partes/coordenadas originales;20descargasJSONy20binarias por sujeto y solapamientos originales,sin recortes ni perfil cProfile.

Mantener PostgreSQL17/Redis7.4/RustFS/Caddy/Gunicorn/Celery/Beat propios,roles runtime restringidos y cuotas kernel de la topología original de8CPU. Fuentes/intérprete montados en sólo lectura,imagen soporte exacta,no build/taglatest ni despliegue. Archivos/objetos cifrados y tokens de un uso reales locales;identidad externa simulada explícita de fixture,no proveedor elegido/contratado ni datos reales. No iniciar otra carga propia en paralelo.

Criterios originales intactos:cobertura p95≤2s,entregaJSON/binaria porpaquete p95≤5s y presupuestos originales restantes de generación/acciones/recursos. Comprobar datasets1500,hashes/bytes de16imágenes/ZIP/partes≤8MiB,POST303→GET200/no-store,separación/cuotas/replay/autoridad fresca. No sumar percentiles ni contar20peticiones como20tests. Si el testfalla antes de aserciones finales de solapamiento,recalcular intervalos desde evidencia cruda sin convertirFAILenPASS.

## Espera persistente y mismo objetivo

Referencia de planificación:326tardó2015,181sJUnit (~33min35s),más preparación/control;no ETAgarantizada. Techo original del controlador11500s,errores de recursos invalidan,no justifican reintento automático. Secuencia persistente con stdinDEVNULL/sesiones propias y logs privados ignorados,supervisor terminal separado,Telegram de cada prueba después de limpieza y aviso de resultado/bloqueo.

Antes de pausar:verificar PIDs/start-ticks/sesiones/argv propios,control de preparación válido y controlador completo efectivamente vivo,fuentes/grafo/spec/helpers congelados,estado del mismo goal y reciboTelegramprevio. Guardar relevo completo e informar chat. Pausar explícitamente el goal mediante update_goal(paused),sin detener prueba. La autorización posteriorAGENTS2026-10-21 exige shell de compactación al quedarpaused/idle y reactivación automática del mismo objetivo al terminal;sin sondeos del modelo. No crear goal ni reenviar objetivo/tokenBudget al reactivar;comprobar identidadcreatedAt/objetivo y consumo no decreciente. Otro objetivo/estado terminal/cancelación impide el disparador.

Documentación oficial contrastada:[App Server:gestión de goal](https://learn.chatgpt.com/docs/app-server#manage-a-thread-goal) permite cambiar estado omitiendo objetivo y conservar contabilidad;[compactación](https://learn.chatgpt.com/docs/app-server#trigger-thread-compaction) respondeACKantes de terminar. Exigir nuevo contextCompaction persistido en turno completed,no sóloACK. Si falla compactación/reactivación,registrar y avisar;no afirmar completado. La shell no repite baterías ni acepta resultados.

## Auditoría posterior y contrato pendiente

Conservar ambos resultados originales,JUnit/report/launcher/archiveSHA y límites de logs/almacenamiento,fuentes e imágenes sin cambios,ambos sujetos/cuerpos/concurrencia/cuotas/recursos/OOM,cierre independiente de contenedores/volúmenes/redes propios y Telegram. Estado técnicoPASS/FAIL/ERROR/SKIP separado de disposición contractual. Tabla anterior/actual con tiempos y límites de comparabilidad;ningún porcentaje causal inventado.

LosFAILde326y los objetivos2s/5s y excepción provisional conservan su ámbito. N02requiere además atribución restante y crecimiento/retención/concurrencia pertinentes;esta ejecución no cierra por sí sola bloque ni contrato. Tras auditar elegir siguiente corrección por coste demostrado o descarte fundamentado,sin lanzar automáticamente otro ensayo. N06y todos los demás obligatorios siguen abiertos donde falte evidencia;N12–N14no activados,alfa,sin publicación/proveedores/datos reales.
