# N02C — contraste agrupado y adopción local del guard

25 de octubre de 2026. [Protocolo364](364-n02-c-prerregistro-contraste-agrupado-guard-20261025.md),instrumento754c393,run20261025-134320-fefba16c. **1PASS/0FAIL/ERROR/SKIP**,120guards reales/12grupos/10llamadas porgrupo. [Auditoría](evidencias/n02-c-agrupado-auditoria-20261025.json), [reproducción/evidencias](evidencias/n02-c-agrupado-evidencia-20261025.tar.gz), [congelación](evidencias/n02-c-prerregistro-congelacion-20261025.json). Aplicación e instrumentos anteriores byteidénticos;1516fuentes runtime/dependencias/oráculos contrastadas con el run correcto de N02B. No se repitieron los14controles originales ni el negativo ya válido. N00/N01aceptados2/13,N02/N06abiertos,alfa.

## Tabla anterior y guard adoptado

Mismo caso/exportación/archivos/proceso,transacción y holds/replay nativos nuevos en cada llamada. Guard anterior literal575bytes/SHAexacto de6bffd48 frente al guard en lote4a83fe6;ninguna aplicación se modifica para este contraste. Dos imágenes sintéticas pequeñas,10554bytes;DEBUGFalse establecido sólo antes de generar. Cada una de las cinco parejas posteriores tiene10guards porvariante;unidad de comparación es la **media por llamada de cada grupo**,no una llamada individual ni p95.

| Medida | Anterior | Guard en lote | Diferencia observada |
| --- | ---: | ---: | ---: |
| Media del primer grupo10 | 54.393ms | 22.629ms | 31.764msmenos |
| Mediana de5medias de grupo10 | 39.513ms | 28.857ms | 10.656msmenos (26.967%) |
| Rango de5medias posteriores | 30.645–43.069ms | 26.480–30.454ms | Cinco parejas favorables |
| Mediana de mediasCPUdelhilo | 29.546ms | 20.611ms | 8.935msmenos |
| Mediana de mediasSQLexecute | 12.097ms | 9.099ms | 2.998msmenos |
| SELECTporguard | 7 | 4 | 3menos (42,857%) |
| Lecturas/hash/bytes porguard | 2/10554 | 2/10554 | 0 |

El helper check conserva su perfilador Python original de conteos activo en ambas variantes: el reloj de guard incluye ese sobrecoste; no es latencia limpia sin instrumentación. No sumar CPUySQLexecute: sus relojes se solapan. La primera pareja de grupos queda separada por decisión previa, no por su resultado. Se conservan también todas las120muestras individuales: rangos completos22,522–208,690ms anterior/14,500–42,983ms candidato. No se retiran outliers ni se mezclan estas medias con las medianas individuales de363.

| Pareja posterior | Media anterior porguard(ms) | Media candidato porguard(ms) | Reducción(ms) |
| --- | ---: | ---: | ---: |
| 1 | 43.069 | 28.857 | 14.211 |
| 2 | 42.400 | 28.121 | 14.279 |
| 3 | 39.373 | 29.082 | 10.291 |
| 4 | 30.645 | 30.454 | 0.190 |
| 5 | 39.513 | 26.480 | 13.033 |

**Cumple el criterio local fijado antes de medir:** las5/5parejas posteriores y la mediana de sus medias mejoran; coste7→4,contenido/orden/bytes/efectos sin diferencias. Se adopta localmente el guard en lote, con corrección acreditada en363y presente contraste temporal. La pareja4sólo difiere0,190ms: no es prueba de significación, garantía estadística,ganancia estable universal ni aceptación de latencia bajo carga. La reducción26,967%pertenece a esta etapa agrupada con dos archivos pequeños;no al sitio ni a una descarga completa.

## Integridad, reutilización y límites

Cada una de las120invocaciones recorre el helper check con nueva transacción y sello válido real;el guard se alcanza exactamente una vez y no hay fallback completo. En cada guard,otro backend PostgreSQL observa55P03al intentarNOWAITen2Blob/2Photo previamente bloqueados:480testigos de fila,fuera del reloj. Dos lecturas completas/hash y orden se conservan siempre:240lecturas porinterfaz de almacenamiento,con cachéSO posible,no disco frío forzado. No se cachean bytes/metadatos entre invocaciones.

La auditoría recalcula las12medias y sumas desde120muestras finitas,comprueba orden alterno/repeticiones/pares completos,7/4consultas,2lecturas/10554bytes/digest/4locks,baselineSHAycontadores sin nuevos efectos. Reutiliza los16casos distintos de363como testigos funcionales/coste con aplicación,dependencias,cuerpos y versiones nativas sin cambios;no incorpora sus tiempos como observaciones de este contraste. El [resultado363](363-n02-b-resultado-guard-imagenes-sello-20261025.md) conserva su corte inconcluso y losFAILinstrumentales anteriores siguen visibles.

PostgreSQL17/Redis7.4propios,librdbv2.4.0,archivos privados locales y objetos desactivados;sin cuotas dedicadas,carga ni concurrencia de sujetos. La verificación externa de identidad sigue siendo el simulador explícito de la fixture,no proveedor real. No prueba HTTP/proxy/Gunicorn/worker de exportación,p95/p99,n16/~64MiB ni todoMOD09. CPUySQLregistrados,no memoria máxima o capacidad de producción.

Fuentes congeladas intactas hasta auditoría,un caso exacto/tres eventosPASS;recursos propios y temporal retirados,Telegram terminalsent. Pytest92,15s/comando94.378s,preparación/QA separados del reloj de guard. No se amplió el lote ni se repitió por conveniencia.

## Siguiente trabajo contractual

Adopción de un guard,no cierre deN02. Atribuir cobertura/selección/serialización/cifrado/paquetes/cola/entrega en el escenario original,crecimiento y concurrencia;evaluar costes restantes y volver a comprobar el flujo completo. Objetivos2s/5s,FAILy excepción provisional conservan su ámbito original;este resultado no prueba su cumplimiento. Cuenta/representación/crecimiento deN06 y demás bloques siguen obligatorios;N12–N14condicionados no activados,alfa,sin publicación/proveedores/datos reales.
