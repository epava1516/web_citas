# CR09 — ejecución por alcance y coste

El runner admite `--profile regression --regression-lane functional` y `--regression-lane capacity`. El valor por defecto `all` conserva la batería anterior. Los archivos test_capacity_* forman la segunda partición; los demás, la primera. La unión es completa y disjunta por archivo; se mantienen las exclusiones contractuales anteriores, que requieren gates separados. El reporte registra la partición. Ninguna partición aislada acepta la regresión integral.

Usar functional durante cambios funcionales, focused para reproducción/corrección y capacity cuando cambien mecanismos de capacidad o para la integración que lo requiera. Los prototipos con otros prefijos permanecen en functional: no se asume que todos sean prescindibles. Capacity exige un trabajador y se ejecuta sin otras cargas. Las métricas de una regresión mixta no aceptan rendimiento contractual.

Análisis de la batería 20261018-104857-f945ff5e: pytest 19.999,94 s; suma de fases 19.982,62 s, de los que 3.034,67 s corresponden a test_capacity_*. La partición funcional representa 16.947,96 s históricos: aproximadamente 4 h 42 min de fases frente a 5 h 33 min de batería. Es atribución histórica, no una nueva medición ni ahorro del trabajo integral. Setup335,87 s, call17.279,44 s, teardown2.367,32 s. El principal coste no es la preparación. Datos completos en evidencias/cr09-test-runtime-analysis-20261018.json.

Paralelismo: el runner ya permite --workers con xdist por archivo. Se mantiene serial como valor seguro; el anterior ensayo de tres trabajadores agotó memoria. Antes de habilitar dos trabajadores por defecto hay que demostrar aislamiento y memoria bajo cuotas existentes con grupos representativos. No se ejecutan pruebas de capacidad concurrentemente ni se rebajan datasets/umbrales.

Grafo AST actualizado antes del análisis en artifacts/graphify-testing-reduction-20261018: alcance estructural parcial sobre archivos de runner/fixtures, no actualización semántica completa.

Validación de selección por colección real: all3.631, functional3.333 y capacity298; intersección vacía y unión exacta, con las exclusiones originales aplicadas. Control de dos trabajadores 20261018-165701-2e40c69e:42PASS/0errores/0omisiones, memoria máxima473.772.032bytes, eventosOOM0; fuentes/limpieza verificados. Sólo prueba esos dos módulos, no autoriza generalizar a toda functional. Se validan rechazos de flags fuera de regression y capacity con más de un trabajador.
