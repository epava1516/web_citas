# N01A — Resultado auditado del primer diagnóstico de descubrimiento

25 de octubre de 2026. [Prerregistro344](344-n01-prerregistro-descubrimiento-a-20261025.md) ejecutado en el corteed16134, run20261025-081326-9844f827. Resultado:2PASS,0FAIL/ERROR/SKIP. La [auditoría independiente](evidencias/n01-a-diagnostico-auditoria-20261025.json) comprueba selección exacta, seis fases aprobadas en journal, JUnit, fuentes y limpieza. N01 continúa en curso y N04 no está aceptado por esta muestra. Balance:1/13obligatorios, alfa.

## Referencia observada, sin candidato de optimización

| Población publicada | Peticiones medidas | Tiempo instrumentado de la petición | SQL | Tiempo JUnit del caso con fixture |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 1 | 0,624848s | 52 | 45,534s |
| 100 | 1 | 0,247264s | 29 | 7,605s |

Son dos tamaños distintos ejecutados en ese orden, con posibles efectos de calentamiento y reutilización en el mismo proceso. La segunda fila no es un «después» de optimizar la primera. No hay cambio de producto, diferencia porcentual atribuible, p95, TCP,20RPS o capacidad certificada. Tampoco los tiempos JUnit/55,781s del paso pytest son latencia de aplicación. No se ha demostrado crecimiento lineal de SQL ni su ausencia universal con sólo estos dos puntos.

Ambas peticiones son listado orgánico inicial ES por Django HTTP Client, con PostgreSQL real y oráculos200/población/página/no-store. Promoción, filtros, páginas profundas, EN, ficha, navegador, concurrencia y restantes grupos siguen pendientes de sus fichas. No se modificaron permisos, gates, instrumentos o fixture para aparentar mejora.

## Conservación y entorno

El runner completó dependencias offline, Ruff, documentación, Django, migraciones y compilación nativa. PostgreSQL17 fue preparado antes de la congelación; su digest y el de Redis7.4 constan en la evidencia. No se afirma identidad de entorno con la antigua carga contractual. Los1507SHAejecutables, documentos y grafo congelados permanecieron iguales durante la ejecución y hasta la auditoría.

Contenedores propios ausentes por inspección exacta posterior, temporal eliminado y Telegram terminalsent. El archivo de evidencia conserva metadatos/JUnit/journal, freeze e imágenes; originales y huellas de logs permanecen identificados en la auditoría. No se acepta un simulador como PostgreSQL o integración externa real.

## Próximo lote y regla de comparación

Antes de candidatos, separar primera petición de peticiones posteriores al mismo tamaño, registrar qué estados se calientan y fijar selección/recursos/oráculos antes de repetir. Completar los segmentos pendientes de S01 y fichas de los otros ocho grupos. No iniciar otra batería por rutina ni extrapolar este resultado alinventario completo.

La tabla de antes/después obligatoria se publicará al cerrar cada bloque, con base y candidato comparables o ausencia de base declarada. La deN00está en [343](343-n00-aceptacion-local-20261025.md#antes-y-después-de-n00); esta tabla es sólo una referencia diagnóstica de N01A.
