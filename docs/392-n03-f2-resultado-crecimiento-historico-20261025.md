# N03F2 — crecimiento histórico medido sin cambiar aplicación

Alfa, N03 abierto, 3/13. Protocolo391 cumplido en20261025-202704-5fab8e4c:3PASS/0FAIL/ERROR/SKIP,51,734sJUnit.1746huellas congeladas intactas. Dieciocho llamadas completas, dos archivos/dos Photos actuales y0/10/100históricas con N+1revisiones históricas. No es un contraste de versiones ni otra optimización.

## Tabla de tiempos observados

Milisegundos de aplicación: primera llamada separada; mediana y rango de cinco posteriores por cohorte. Antes/después de selector significa comparación pendiente/completa, no dos versiones de código. Ambas etapas del selector realizan una SQL.

| Fotos históricas | Detector primera (ms) | Detector posteriores mediana (rango ms) | CPU hilo mediana (ms) | SQL detector | Selector pendiente/completo mediana (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 147.885 | 156.429 (128.157–193.612) | 78.456 | 22 | 13.801 / 13.057 |
| 10 | 143.521 | 175.145 (122.208–222.565) | 94.112 | 22 | 11.178 / 16.433 |
| 100 | 214.116 | 202.129 (171.851–240.406) | 99.622 | 22 | 15.618 / 15.580 |

Con cero históricas frente a100, mediana detector156,429→202,129ms yCPU78,456→99,622ms;las poblaciones difieren ylos rangos se solapan parcialmente. SQL permanece22,confirmaciónORB1,Match1. No atribuir aceleración ni causalidad exclusiva a código o extrapolar pendiente/SLA/p95 a80000. Se conserva el coste observado y se avanza conforme a decisión del usuario: tiempos aceptables enalfa, sin nueva optimización marginal.

## Paridad y conservación

Codex verificó las tres propiedades JUnit ycomparó corpus yresultado canónico entre cohortes,además de las seis muestras de cada una. Corpus119478bytes, SHA faffecc707ff0af5e5f5c26743423630efc78a335bab9bcf4e44c44351ed0093. ResultadoSHA636137a93404521ba95dc2a826edddda5543c8a9288ec47b43456a3ae57014f0 en18observaciones; métodoORB yscore exactos. Un candidato elegible/confirmación/Match,ningún histórico comparado ni alterado; revisiones/ledger/Blob/bytes intactos. Firmaorigen2/peer1 por invocación (incluye comprobación de reintroducción). RSS high-water208680/208808/208936KiB,acumulativo del proceso;no RSS completo del servicio.

Selectorpending despacha sólo query ydespués ninguno,enuna consulta nativa cada vez;dispatchcapturado,no prueba detransporte o ejecución. No se incluyen generación de archivos/firmas,preparación deledger ni reseteo deMatch/flag enrelojes; sídetector completo/confirmación/registroySQLexecute numérico. CPU del hilo no es CPU del servidorSQL. OpenCV1hilo/RNG1847diagnóstico,restauración dehilos comprobada porfinally. Mismo producto fa64767,sin cambios deaplicación.

## Verificación y disposición

RunnerPASS ypropiedades completas,fuentesintactas,PostgreSQL/Redispropios yaislamiento decola. RecursosDockeretiquetados ytemporalpropio ausentes traslimpieza,Telegramterminalsent confirmado. Sinworker/Beat/HTTP/capacidad/proveedores/datos reales. Resultado yauditoría conservados; no se repite por documentación.

N03F2 queda aceptado localmente en este ámbito finito. Falta acta final N03: disposición de seis acciones censadas,puentes deidentidad desde testigos previos ytabla consolidada de correcciones/rendimiento,conservando dueñoscompartidos N07/N09/N10. Este resultado no cierra N03 ni cambia3/13.
