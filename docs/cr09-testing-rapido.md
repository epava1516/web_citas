# CR09 — ejecución por alcance y coste

El runner admite `--profile regression --regression-lane functional` y `--regression-lane capacity`. El valor por defecto `all` conserva la batería anterior. Los archivos test_capacity_* forman la segunda partición; los demás, la primera. La unión es completa y disjunta por archivo; se mantienen las exclusiones contractuales anteriores, que requieren gates separados. El reporte registra la partición. Ninguna partición aislada acepta la regresión integral.

Usar functional durante cambios funcionales, focused para reproducción/corrección y capacity cuando cambien mecanismos de capacidad o para la integración que lo requiera. Los prototipos con otros prefijos permanecen en functional: no se asume que todos sean prescindibles. Capacity exige un trabajador y se ejecuta sin otras cargas. Las métricas de una regresión mixta no aceptan rendimiento contractual.

Análisis de la batería 20261018-104857-f945ff5e: pytest 19.999,94 s; suma de fases 19.982,62 s, de los que 3.034,67 s corresponden a test_capacity_*. La partición funcional representa 16.947,96 s históricos: aproximadamente 4 h 42 min de fases frente a 5 h 33 min de batería. Es atribución histórica, no una nueva medición ni ahorro del trabajo integral. Setup335,87 s, call17.279,44 s, teardown2.367,32 s. El principal coste no es la preparación. Datos completos en evidencias/cr09-test-runtime-analysis-20261018.json.

Paralelismo: usar explícitamente --workers 2 para la partición funcional y --workers 1 para capacidad; no cambiar ni depender del valor por defecto del parser. El usuario decidió mantener dos y no ampliar trabajadores. La batería funcional completa 20261018-173221-2870ec78 pasó con3214PASS,4subpruebasPASS,122SKIP y cero fallos/errores;3336nodeids,3340 entradas JUnit al incluir subpruebas. Duración de pytest10156,86s (2h49min17s). Pico del controller3624529920bytes (3,375607GiB),96,45% de3584MiB; OOM0. Es evidencia de esa selección/configuración, no autorización para tres trabajadores ni para paralelizar capacidad. El anterior ensayo de tres agotó memoria. No se rebajan datasets/umbrales. [Recibo terminal](evidencias/cr09-functional-parallel-terminal-20261018.json).

Grafo AST actualizado antes del análisis en artifacts/graphify-testing-reduction-20261018: alcance estructural parcial sobre archivos de runner/fixtures, no actualización semántica completa.

Validación de selección por colección real: all3.631, functional3.333 y capacity298; intersección vacía y unión exacta, con las exclusiones originales aplicadas. Control de dos trabajadores 20261018-165701-2e40c69e:42PASS/0errores/0omisiones, memoria máxima473.772.032bytes, eventosOOM0; fuentes/limpieza verificados. Sólo prueba esos dos módulos, no autoriza generalizar a toda functional. Se validan rechazos de flags fuera de regression y capacity con más de un trabajador.


Comparación de alcance y duración:

| Ejecución | Selección | PASS | Subpruebas PASS | SKIP | Fallos/errores | Pared pytest |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 20261018-104857-f945ff5e | Completa ordinaria, serial | 3501 | 4 | 130 | 0 | 19999,94s |
| 20261018-173221-2870ec78 | Funcional, dos trabajadores | 3214 | 4 | 122 | 0 | 10156,86s |

Las selecciones son distintas: no atribuir toda la diferencia al paralelismo ni a velocidad de requests. Conciliación real por nodeid: la funcional anterior contiene3333; la nueva3336, sin retiradas y con tres tests adicionales de notificaciones. La capacidad conserva298 casos esperados sobre fuentes técnicas sin cambios. Esos298 y las exclusiones contractuales requieren evidencia propia; la suma de particiones no elimina omisiones ni acepta CR09/N3 automáticamente.
