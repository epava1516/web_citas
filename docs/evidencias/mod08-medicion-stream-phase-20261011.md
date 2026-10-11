# Comparación diagnóstica tras streaming y fases detalladas

Un caso sintético completo. No acredita aceptación de dos casos/N3. Fuentes c893d20 verificadas: 1151 hashes en cada ejecución; contenedores propios ausentes.

| Métrica | Anterior | Actual | Cambio | Objetivo |
| --- | ---: | ---: | ---: | ---: |
| Listado p95, 383 lotes de cuatro páginas | 3,807 s | 3,885 s | empeora 2,06% | 2 s |
| Subconjunto comparable, 123 lotes | 3,205 s | 3,376 s | empeora 5,35% | 2 s |
| Descarga JSON p95, 3 muestras | 7,040 s | 6,908 s | mejora 1,87% | 5 s |
| Descarga binaria p95, 8 muestras | 8,191 s | 7,706 s | mejora 5,92% | 5 s |

Con 3 y 8 muestras el p95 nearest-rank coincide con el máximo; faltan al menos 20 por variante y caso. Descargas incluyen dos autorizaciones HTTP nuevas y EOF. JUnit: 1 prueba, sin fallos, errores ni omisiones. La captura termina con código 1 por su resultado diagnóstico, sin aceptación de capacidad.

## Experimento aislado de SHA-256

Nueve ensayos alternados, buffers sintéticos, digest idéntico comprobado. Incluye construcción y conversión hexadecimal; no mide requests.

| Caso | hashlib mediana wall | cryptography mediana wall |
| --- | ---: | ---: |
| 4 MiB | 0,011246 s | 0,011253 s |
| 16 × 4 MiB | 0,179269 s | 0,179677 s |

Se conserva hashlib: no aparece una ventaja útil al cambiar de backend. Cython ya está integrado en canonicalización; ampliar compilación requiere identificar un recorrido Python con margen suficiente y medir equivalencia y latencia completas. No se altera el contrato de aceptación.
