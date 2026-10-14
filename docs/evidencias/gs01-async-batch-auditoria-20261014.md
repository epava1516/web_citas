# GS-S02: evidencia de generación asíncrona y lote

Requisitos de docs97: estados visuales asíncronos, fallback sin JS, ES/EN,
autoridad vigente y lote múltiple sin perder lecturas/decisión independiente.

| Selección | PASS | Fallos de la selección |
|---|---:|---:|
| Navegador asíncrono ES/EN | 6 | 0 |
| Jobs de dominio | 26 | 0 |
| Lotes HTTP/navegador/dominio | 12 | 0 |
| Validación de lote grande | 1 | 0 |

[Reports y hashes exactos](gs01-async-batch-regresion-20261014.json).
No sumar versiones como N3: los resultados pertenecen a las particiones
identificadas y el bloque 3 conserva un fallo ajeno a esta selección.

El navegador comprueba queued/running/succeeded, rejected/failed, suspensión
final del polling, ausencia de respuesta final ante error, fallback sin JS,
privacidad/403 tras revocación y ancho móvil ES/EN. Los cambios del job se
ejecutan explícitamente desde el fixture: no prueba worker Celery real.
Los tests de dominio cubren replay, conflicto, reintento con rollback, lease,
concurrencia, caducidad, identidad/proof/fuentes y broker tipado.

El lote verifica auditoría por página e idempotencia, rollback total si una
página posterior falla, límite de cantidad, POST privado, render de cada página,
browser con cuatro páginas ES/EN, autoridad al retorno y límite de imágenes.
No elimina la decisión independiente ni atribuye tiempos de UI a p95 HTTP.

Esta evidencia permite reutilizar los casos y descarta falta total de cobertura
visual del lote. GS-S01 versión común y GS-S03 cobertura CR09/CR10 siguen
pendientes. La aceptación GS01/BF/BB/C no se deduce de estos 45 casos.
