# CR09: coste aislado de invalidación, 2026-10-16

Ejecución `20261016-022358-07bacd96`, HEAD `a77123c8260b646d70b6f9b07f54cd48288f6531` más diagnóstico explícito incluido en source-hashes. Resultado: **1 PASS, 74,25 s**, 108 llamadas, PostgreSQL propio con 10.000 anuncios sintéticos. Python 3.12.15, PostgreSQL 17.11, kernel native-sealed. Controlador 4 CPU, PostgreSQL 1 CPU; límites habituales conservados.

Tres bloques alternan ambas variantes, sesión nueva por variante. Copias temporales de funciones: la función global instalada se verifica intacta antes/después. No hay filas Match: comprueba coste, no paridad de la corrección con conflictos. La referencia antigua omite invalidaciones necesarias y no es una alternativa válida de producto.

| Fase | Referencia anterior, mediana ms | Actual, mediana ms |
|---|---:|---:|
| empty | 2.734 | 11.882 |
| single | 0.672 | 3.221 |
| bulk | 468.382 | 443.519 |
| single_after_bulk | 0.810 | 0.925 |

El coste individual actual es mayor antes del lote, y próximo a la referencia después. No aparece un coste de segundos por llamada en esta selección. Esto no excluye acumulación de llamadas ni explica causalmente el p95 HTTP: no se ha medido aquí cuántas invalidaciones dispara la subida real. Siguiente diagnóstico: contar y atribuir esas llamadas durante la subida, separadamente de una medición de aceptación, antes de proponer otra optimización.

Sin perfiladores en la última medición clean; este diagnóstico no es otra medida HTTP ni aceptación. Último p95 clean 1,173553838 s FAIL; no repetición ni 900 s. Fuente congelada comprobada contra hashes; runner/hijo, temporal y contenedores propios ausentes; unidad inactive, MainPID=0, ControlGroup vacío. Sin producción, datos reales, proveedores ni nuevas llamadas Claude. CR09/N3 y contrato completo abiertos.

Datos: `artifacts/local-ci/20261016-022358-07bacd96/mark-cost-parsed.json`, JUnit y source-hashes del mismo directorio. CPU del registro es del cliente, no de PostgreSQL; wall incluye planificación, ejecución y transporte.
