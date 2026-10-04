# Historial rectificado en colas generales

Entrega verificada localmente dentro de su alcance. CR-09 y el contrato completo siguen abiertos.

## Comportamiento

La clasificación SQL compartida considera ejecuciones de rectificación de la misma persona, su fuente y revisiones anteriores, excluyendo la revisión corregida de esa ejecución. Una rectificación posterior puede convertir la corrección previa en historial.

Colas y consultas ordinarias de anuncios, coincidencias y reclamaciones excluyen ese historial y las cargas preparadas. Las coincidencias archivadas no bloquean otro perfil. El detector excluye referencias históricas y evita decodificar archivos cuyos únicos candidatos son protegidos. Conserva registros, decisiones y restricciones antiguos; no los elimina ni rehabilita automáticamente.

Las imágenes de moderación adquieren bloqueos de agencia/persona y revisión o anuncio y recargan Photo antes de abrir bytes. resolve y decide revalidan historial tras los bloqueos; decide impide aprobar o rechazar versiones históricas y cargas preparadas incluso con estado pending forzado. Las consultas específicas de derechos mantienen ámbito, acreditación y auditoría independientes. No se revocan bytes ya entregados.

## Evidencia y alcance

Batería anterior a la última guarda de decide:45 pruebas correctas322.529s, cero fallos/errores/omisiones, PostgreSQL y Chromium. Una invocación previa seleccionó un archivo inexistente:0 pruebas/salida4. No sumar baterías solapadas.

Concurrencia final:3 pruebas correctas39.36s. Gestor, moderación de anuncios y coincidencias esperaron bloqueos reales observados mediante pg_blocking_pids. La retirada ejecutada durante la espera hizo que las tres rutas devolvieran404; el otro perfil conservó sus bytes compartidos.

Incidencias de preparación: primera batería2 correctas/1 fallo34.44s por campo kind inexistente; corregido method. Segunda2 correctas/1 fallo36.68s porque añadir Match invalidaba el inventario: el sistema rechazó correctamente el plan obsoleto. La prueba renueva inventario y plan antes de la carrera, sin debilitar la comprobación de huella.

La batería conjunta actual incorpora la guarda de decide y las tres carreras:47 pruebas correctas328.40s, cero fallos/errores/omisiones, sesión46996 terminal0, XML /tmp/rectification-general-queues-locked-final.xml. No atribuirle el resultado de las45 anteriores.

Docker reconstruido y recreación64463 terminal correcta. Hashes de moderation.py/history.py iguales entre host y app, UID10001, check sin incidencias y health200 sobre la última guarda. Sin migración nueva. CI e7d0679 terminó528 correctas1292.39s; no cubre esta entrega sin commit.

## Continuación

Refuerzo con presentación válida:6 pruebas correctas110.68s,5 casos excluidos explícitamente por selección, cero fallos/errores/omisiones en los casos ejecutados. Comprueba aprobación y rechazo sin decisiones nuevas con estado pending y Submission válida. No sumar6+47 como regresión común. Después: recarga manual, recompresión/recortes y rehabilitación independiente, conservación final por finalidad, identidad de cuenta, comunicaciones/cierre y demás derechos. CR10, GS01, BF/BB y entrega final siguen abiertos. Claude3/3; continuación local.

[Evidencia normalizada](evidencias/historial-colas-generales.json).
