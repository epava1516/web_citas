# B16-356 — Separar señales históricas de las tareas del esquema activo

La revisión positiva actual de contenido descubrió una diferencia real respecto del corte histórico: Redis ya contenía dos registros antes de la siembra del escenario. No se borraron ni se clasificaron por el nombre de sus claves. La revisión independiente y el operador conservaron sin resolver la fuente Redis y las23conclusiones de no entrada histórica; la aplicación rechazó el cierre completo. Este negativo demuestra el rechazo ante cobertura incompleta, no un fallo de aislamiento de datos demostrado en producción.

## Negativos preservados

- `20261024-142803-1795b37f`: perfil ES,1FAIL/0ERROR/0SKIP,267,434sJUnit.29fuentes inspeccionadas, fuenteRedis pendiente de lector tipado y23orígenes históricos sin decisión no_link. Propuesta independiente y decisión de rechazo del operador se conservan privadas con originales cifrados. Fuentes iguales, limpieza y Telegram verificados.
- `20261024-143903-ef02f2b1`: reproducción de la causa,1FAIL/1PASS. La función real de catálogo de la migración0023, ejecutada con modelos históricos de MigrationExecutor, persiste la categoría y programa una tarea del esquema activo después del commit. La escritura normal de Category mantiene su control positivo. No es un replay completo de cambio de esquema ni demuestra por sí solo que una tarea llegara a fallar por columnas incompatibles.

## Cambio acotado y garantías

El receptor global schedule_refresh escuchaba cualquier modelo cuya tabla fuese una dependencia, incluidos modelos de registros históricos de Django. Se añade una guarda de identidad del registro: el modelo efectivo —incluido through para relaciones— debe pertenecer al registro global de modelos activos antes de programar esta optimización de latencia.

No se cambian triggers de invalidación, elegibilidad nativa, Beat, autoridad, locks, versiones ni lectores de Redis/RDB. Los modelos históricos y de registros aislados conservan la invalidación de base de datos; su lectura pública sigue protegida aunque no se programe el refresco inmediato. El manejo preexistente de alias de conexión queda fuera de este cambio. No se descartan tareas del broker para conseguir un resultado positivo.

`20261024-144205-543aec10`:9PASS/0FAIL/0ERROR/0SKIP,58,637sJUnit; migración sin tarea activa, escritura normal, rama through, invalidación real y rechazo nativo/404 al desactivar categoría histórica, rollback/deduplicación y conservación del contenido legado en migración. El revisor señaló que la primera prueba through llamaba al helper directamente. Se sustituyó por remove/add real sobre categorías de una revisión publicada: `20261024-144428-6598f5bf`,1PASS, diferido hasta commit y una sola tarea. No se presenta el primer helper como prueba de registro real de señal. Producto idéntico entre ambos cortes; el segundo mejora sólo esa prueba. Fuentes, limpieza y avisos terminales de ambos comprobados.

## Revisión externa de contenido posterior a la corrección

Cada variante usa un runner propio, siembra nueva sin snapshots y29fuentes observadas. Se mantienen operador root y revisor nativo independiente b16_356_content_review; la aplicación conserva su autor y revisor distintos. El operador comprueba originales, digests, asociaciones y consulta de solo lectura antes de publicar cada respuesta cifrada. No se heredan aprobaciones entre escenarios ni se equipara un nombre sintético con procedencia segura.

| Variante | Ejecución | Estado |
| --- | --- | --- |
| Perfil ES |20261024-144542-a6eb827a|1PASS,318,928sJUnit; fuentes1723, limpieza yTelegram verificados.|
| Cuenta ES |20261024-145152-95525323|1PASS,251,213sJUnit; fuentes, limpieza yTelegram verificados.|
| Perfil EN |20261024-145645-013a5c10|1PASS,204,014sJUnit; fuentes, limpieza yTelegram verificados.|
| Cuenta EN |20261024-150052-406f7c6e|1PASS,235,095sJUnit; fuentes, limpieza yTelegram verificados.|

En perfil ES, las cinco fuentes de almacenamiento del baseline y sus archivos están realmente vacíos; la captura actual comprueba16bases Redis sin registros. Dos archivos del sujeto y la proyección de correo de su cuenta tienen asociaciones explícitas; se omiten expresamente sus tres campos de contenido. Sesiones e imágenes de terceros se excluyen mediante relaciones comprobadas. Los23orígenes históricos sólo reciben conclusión de no entrada/importación/restauración a este escenario finito: no se descifran ni clasifican semánticamente los ciphertexts históricos y no se acredita independencia de sujetos por sus nombres.

La duración de estas pruebas incluye revisión del operador y del agente; no es latencia de una acción de usuario. No se acredita entrega cruda de fotografías ni desaparición universal de otros recursos. B16 sigue abierto, igual que capacidad y conciliación de rutas. El proyecto permanece en alfa, y la reconstrucción completa del grafo y el diferencial final del inventario siguen pendientes por contrato.


El [resumen de evidencia y límites](evidencias/b16-356-migration-signal-owned-review-20261024.json) conserva ambos negativos. Sólo publication_signals.py cambia dentro del producto respecto del testigo355. La reparación nativa posterior `20261024-145646-7c8733cc` pasa1caso en177,652sJUnit:100perfiles,60páginas y14→0marcas porBeat/worker,28,895s desde readiness. Se verifican fuentes, limpieza yTelegram. Se ejecutó junto al escenario perfilEN, en PG/Redis/temporales propios; no se atribuye rendimiento ni capacidad a esos tiempos concurrentes.


Las cuatro variantes actuales quedan verificadas por separado, con fuentes, cleanup y recibos propios. Perfil incluye tres proyecciones asociadas con decisiones explícitas de omisión; cuenta no selecciona registros de terceros. No se suman sus tiempos como rendimiento ni se sustituye con ellas la cobertura de capacidad o de todo B16. La revisión nativa es una única tarea de solo lectura con seguimientos; ocho invocaciones ClaudeV1 históricas preservadas, cero nuevas y consumo nativo no estimado.
