# B10-363 — Auditoría terminal de medición actual MOD-09

La ejecución `20261024-205341-42fa3118`, prerregistrada en [325](325-medicion-actual-mod09-b10-20261024.md), terminó con **1 FAIL, 0 ERROR, 0 SKIP**. JUnit: 2015,181 s (33 min 35 s). Se conserva el resultado `FAIL_DELIVERY_STAGE_LIMITS`; no se cambian los objetivos de 2 s/5 s ni se declara B10 cerrado.

| p95 | Sujeto A | Sujeto B | Objetivo |
| --- | ---: | ---: | ---: |
| Lectura de cobertura | 3,377 s | 3,368 s | 2 s |
| Descarga JSON por paquete | 6,600 s | 6,529 s | 5 s |
| Descarga binaria por paquete | 6,645 s | 6,770 s | 5 s |

La generación asíncrona actual tardó 40,744/40,667 s. Los resultados permanecen próximos al histórico provisional; esta comparación entre entornos no demuestra una mejora causal del código. La aceptación provisional MOD-09 acordada permanece y seguimos en alfa.

La [evidencia de auditoría](evidencias/b10-current-mod09-terminal-audit-20261024.json) verifica 1723 huellas sin diferencias, archivo legible y su SHA, memoria propia conservadora de 4279021568 bytes, techo de almacenamiento de 5939134464 bytes y ningún OOM de servicios. La consulta independiente de etiquetas Docker devolvió cero contenedores, volúmenes y redes propios restantes. Telegram terminal confirmado.

Ambos sujetos terminaron el flujo sin excepciones: el código comprueba cuerpos, SHA, igualdad de datasets y originales recuperados antes de asignar success según las infracciones temporales. Son sujetos sintéticos, sin acreditación de proveedores reales. El FAIL de success precede a las aserciones finales de solapamiento; por eso la auditoría recalculó directamente todos los intervalos originales: 20 guardados binarios, 31 lecturas de selección, 20 inspecciones, 20 guardados de cobertura, 384 lecturas de cobertura y 20 descargas de cada tipo, por sujeto, con solapamiento de todos los pares.

Compactación confirmada mediante nuevo elemento persistido; retorno conservó el objetivo y su consumo, sin crear otro. Queda conciliar el resultado con B10, justificar el escenario extremo de similitud y completar la cobertura semántica de B16. No se repite automáticamente esta carga ni se abre ahora el contrato pospuesto de optimización de QA.
