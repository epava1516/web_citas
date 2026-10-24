# B10-347 — Extremos de exportación y similitud

B09 aceptado por acta19; doce de18puntos cerrados. B10 comienza desde el grafo412 revalidado, sin extracción global nueva. MOD09 conserva la aceptación provisional del escenario c92fe64 y los objetivos originales2s/5s como deuda futura; no reabrir el alfa ni repetir la carga fallida para maquillar resultados.

## Evidencia histórica contrastada

Se verifican el manifiesto y JUnit originales de20261012-150109-89880182: un caso fallido, sin errores/omisiones. La decisión posterior del usuario permanece suficiente provisional/mejorable, no PASS del instrumento. El hash de manifiesto del productor es SHA256 de json.dumps(mapping,sort_keys=True), no del archivo indentado; se corrigió esa suposición inicial del lector sin alterar el archivo. Canonicalización y cargador actual coinciden por bytes con aquel corte, pero rights_exports.py y media.services.py cambiaron: no trasladar tiempos a la candidata actual por identidad parcial.

El contraste de selector20261015-213949-b87873e3,1PASS, conserva10002fotos y cinco blobs totales; ambas consultas devuelven cuatro cuerpos idénticos en tres tandas alternas. La mejora histórica pertenece a JOIN/DISTINCT→EXISTS y ya está en el código, no a FAISS ni al recorrido de muchas imágenes distintas. La [propuesta97](97-propuesta-indice-similitud-fotos-cc05.md) no selecciona tecnología; detect_matches sigue recorriendo blobs admisibles y comparando firmas, con confirmación/guardas posteriores.

## Escenarios seleccionados y presupuesto del diagnóstico

Se añaden dos instrumentos explícitos, sin cambio de aplicación:

1. Detector con10/100blobs de contenidos originales distintos, ficheros PNG/WebP reales y una foto por revisión sintética de otra persona. Corpus determinista v1: recomprensiones40/70, dos recortes, giro90, uniforme y negativos de semillas diferentes. Filas ready/comparison_complete son fixtures, no prueba de subida/revisión ni frecuencia comercial. El conjunto de Match debe corresponder al comparador nativo sobre esa población y el origen debe terminar comparison_complete; no hay índice candidato. Se envuelve cada función delegando siempre a la real para contar llamadas/CPU de stored_signature, compare_signatures, confirm_match y record_match. Se mide además llamada total, SQL, tracemalloc de operación y RSS del proceso. stored_signature no abarca toda la deserialización JSON del driver. Refresco de publicación queda realmente en el Redis propio, sin medir espera/worker; OpenCV1hilo, pytest1worker.
2. Etapa canonical actual con100/1500filas estructuradas y descripciones5400caracteres, dentro del límite normal6000: documento mayor próximo a16MiB. Se compara salida íntegra con JSON ordenado de referencia, Unicode incluido. Una llamada instrumentada, kernel disponible registrado y memoria observada. No mide source_copy, cobertura, cifrado, generación/entrega de paquetes ni solicitud completa.

Topes de seguridad definidos antes del ensayo:128MiB de ficheros del corpus, menos de1GiB RSS del proceso Python y1200s por comando. No se acreditan por ello8CPU/8GiB del sistema completo: son límites del instrumento, sin aislamiento/capacidad ni percentiles. No son nuevos SLO que sustituyan MOD09. Las firmas y la referencia se preparan antes de medir, por lo que no son tiempos fríos.

Selección explícita20casos: detector2, canonical2 y test_image_similarity.py16(5positivos,10negativos y uniforme/pequeña). PostgreSQL/Redis/nativo propios, un worker. Los dos diagnósticos son opt-in por archivo; omitirlos no cuenta como PASS. El resto son testigos funcionales del comparador actual, no cobertura universal de un recuperador aproximado. No se cambia canonicalización, copia, detector, derechos, dependencia ni índice. Primero se inspeccionarán fuente/JUnit/limpieza/Telegram; B10 sigue abierto.

## Corrección del instrumento antes de medir

La primera ejecución20261024-075831-a8a7b146 conserva2FAIL/18PASS: ambos fallos del instrumento al no sobreescribir la opción Django CELERY_TASK_ALWAYS_EAGER; no se llamó al detector. Fuentes intactas, limpieza y Telegram confirmados. Se cambia sólo el diagnóstico para usar settings.CELERY_TASK_ALWAYS_EAGER=False, conservando corpus, tamaños, selección y límites; nueva ejecución pendiente.

## Resultado actual y decisión

Ejecución20261024-080216-d5c5b518:20PASS/0FAIL/0ERROR/0SKIP,109.166sJUnit,1719fuentes congeladas verificadas,637rutas de aplicación/configuración/plantillas/estáticos idénticas al corte B09. PostgreSQL/Redis propios, un worker, limpieza de contenedores/directorio/PID y Telegram confirmados.

[Auditoría actual](evidencias/b10-stage-diagnostic-20261024.json) y [contraste histórico](evidencias/b10-historical-evidence-audit-20261024.json).

| Observación | 10 blobs distintos | 100 blobs distintos |
|---|---:|---:|
| Llamada total instrumentada | 0,880409s | 1,026719s |
| Comparaciones | 10 | 100 |
| CPU de compare_signatures | 0,004544s | 0,057344s |
| CPU de stored_signature | 0,001430s | 0,012952s |
| Confirmaciones / registros | 5 / 5 | 5 / 5 |
| CPU de confirm_match | 0,283060s | 0,257622s |
| CPU de record_match | 0,191656s | 0,168879s |
| Consultas SQL | 74 | 74 |
| Pico Python de operación | 4504929bytes | 5163643bytes |

Las cinco confirmaciones son confirmed; no se interpreta una candidatura regional como identidad. El recorrido y las comparaciones crecen con blobs distintos, mientras las confirmaciones y consultas permanecen constantes en esta selección. La CPU observada de confirmación y registro es mayor que la de comparación a estos tamaños; no prueba el coste dominante para otra densidad de candidatos ni para miles de blobs. Los tiempos no son percentiles, no permiten extrapolar capacidad y no son sumables entre etapas. El RSS es máximo acumulado del proceso; no atribuir su diferencia sólo a detect_matches. No hay algoritmo nuevo ni comparación causal antes/después de rendimiento.

Canonical conserva salida íntegra contra JSON ordenado:100filas/1096235bytes en0,002477s y1500filas/16446835bytes en0,048303s; pico Python del segundo66003931bytes. Kernel validado disponible, sin afirmar por esa disponibilidad que cada comprobación usase el kernel. La llamada aislada no demuestra cuánto pesan canonical, copias o verificaciones en la exportación completa y no reemplaza MOD09.

Decisión: mantener detector, canonical y dependencias actuales. No adoptar FAISS/Hamming, pgvector, BK-tree o LSH a partir de estos datos; tampoco retirar controles de registro por su coste. Sin cambio de aplicación no existe despliegue que revertir; los instrumentos son opt-in y su corrección está aislada. B10 continúa abierto y se mantienen12/18puntos cerrados: queda descomponer el circuito completo de exportación sobre el corte actual, justificar el tamaño/densidad extrema de similitud que corresponda a beta y conciliar la salida de etapa3. No repetir el FAIL histórico ni elevar prioridad sin impacto o incumplimiento aplicable demostrado.
