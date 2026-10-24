# B10-364 — Crecimiento y densidad del detector de similitud

Tras el grafo dirigido437 y la revisión de detector/corpus, se conservan las decisiones de [308](308-descomposicion-extremos-exportacion-similitud-b10-20261024.md): ninguna tecnología seleccionada. El ensayo histórico de10002Photo/cincoBlob representa reutilización de bytes; el actual de100Blob distintos/cinco candidatos perceptuales no representa densidad elevada.

El contrato funcional propone10000anuncios sintéticos y hasta ocho fotos aprobadas por anuncio:80000fotos vigentes es una referencia de dimensionado, no censo deBlob ni máximo del historial retenido. No se puede justificar que100Blob representen ese extremo. Tampoco se extrapolarán percentiles ni capacidad desde una sola llamada instrumentada.

Se prerregistran dos pasos de diagnóstico necesarios para localizar el siguiente límite:1000Blob distintos con los mismos cinco positivos y negativos deterministas del corpusv1, y100Blob de originales distintos casi iguales visualmente. En el segundo se modifica un píxel de cada original real y el comparador nativo debe recuperar al menos90% como candidatos; no se fuerza su respuesta ni se omite confirmación visual. Se comprueba unicidad SHA del corpus. Ambos conservan archivos PNG/WebP reales, referencia exhaustiva, igualdad exacta deMatch, exclusión de la propia persona y estado final. Los dos casos originales10/100siguen disponibles sin cambiar sus nodeids.

Instrumentación: mismos contadores reales de firma/comparación/confirmación/registro, SQL, CPU de hilo, memoria Python y RSS; OpenCV un hilo y pytest un worker. Topes anteriores128MiB de corpus y1GiB RSS del proceso,1200s por comando. PostgreSQL/Redis propios y código nativo actual mediante run_local_ci; su aviso terminal se comprueba después de limpieza. No son SLO ni límites del entorno completo. Selección: test_current_scan_growth_and_density, dos casos. No modificar fuentes durante ejecución.

Criterio funcional: conjunto deMatch igual a referencia, número de comparaciones igual al deBlob y confirmaciones/registros igual al número de candidatos; conservar negativos. Resultado temporal descriptivo, sin nuevo umbral inventado. Si aparece coste relevante se descompone antes de decidir una optimización; si no aparece, todavía debe resolverse la representatividad del extremo de80000y de retención. Estos pasos no cierran B10 ni constituyen el contrato futuro de optimización de QA. No se aplican cambios de producto en este paso.

Estado: prerregistro, resultado pendiente.

## Resultado y disposición del ensayo

Ejecución20261024-213414-574e4266:2PASS/0FAIL/0ERROR/0SKIP,582,988sJUnit. [Auditoría de fuentes y resultados](evidencias/b10-similarity-growth-density-audit-20261024.json): fuentes actuales intactas, inventario Docker propio vacío, temporal retirado y Telegram terminal sent. El prerregistro original permanece separado en artifacts.

| Observación instrumentada |1000distintos/5coincidencias|100densos/100coincidencias|
|---|---:|---:|
| Llamada detector |3,199770s|14,392127s|
| CPU comparación de firmas |0,479006s|0,067510s|
| CPU confirmación visual |0,293125s|6,368067s|
| CPU registro protegido |0,234059s|3,709945s|
| SQL |74|1214|
| Pico Python operación |12320031bytes|6561230bytes|

El caso denso conserva100SHA originales distintos,100candidatos/confirmaciones/registros y100veredictos confirmed; el disperso1000comparaciones y cinco confirmaciones/registros. Ambos conservan paridad exacta con referencia. Las duraciones call depytest483,451s/60,034s incluyen construcción del corpus; no equivalen a los3,20s/14,39s del detector.

A esta densidad destacan confirmación y registro; un índice de recuperación no evita confirmar candidatos que ya son verdaderos positivos ni autoriza eliminar guardas. Se mantiene el comparador y las dependencias, sin adoptar índice ni introducir límites que oculten candidatos. Estos dos tamaños demuestran sensibilidad a crecimiento y densidad, pero no capacidad para80000fotos, historial ilimitado o colas concurrentes. Queda conciliar la disposición del extremo aplicable con el criterio B10 y registrar el riesgo residual; no declarar una garantía comercial ni cerrar B10 por estos dosPASS.
