# Acceso histórico tras rectificación

Estado: aceptación local parcial CR-09. No cierra la conservación de evidencias ni el derecho completo.

## Regla de historial

Una ejecución de rectificación restringe las revisiones anteriores de esa persona, incluida su revisión fuente. La revisión nueva creada por esa ejecución permanece utilizable. Una ejecución posterior convierte también esa revisión corregida anterior en historial. La regla se deriva del registro de ejecución y de las fechas persistidas, sin cambiar ni borrar la fuente.

`is_rectification_history` centraliza esa clasificación en revisión de publicación, acceso ordinario del gestor y elección de base para borradores. Su ámbito es la persona: no restringe otra publicación por compartir los mismos bytes.

## Comportamiento del gestor

- La ruta genérica de imágenes privadas devuelve404 para referencias de revisiones históricas rectificadas. Las fotografías de la versión corregida utilizable conservan su acceso privado habitual.
- Estado y editor de versiones históricas devuelven404; no muestran títulos ni contenido de la fuente anterior.
- No se permite publicar una versión histórica, incluso si vuelve a figurar con un estado publicable. El control central de publicación usa la misma clasificación.
- Crear un borrador puede aprovechar una corrección utilizable conforme a las reglas existentes. Si solo queda una base histórica, crea un borrador vacío y muestra una explicación ES/EN. No copia texto, categorías, tarifas ni fotos de la versión anterior.

Los enlaces previamente conocidos no permiten recuperar referencias históricas desde las rutas del gestor. Las filas y archivos quedan conservados para el procedimiento restringido de derechos; no se atribuye a esta entrega borrado físico ni retirada final de evidencia.

## Lecturas concurrentes

La ruta privada bloquea gestor/persona y revisión antes de autorizar y abrir el derivado. Después de esperar esos locks, vuelve a leer Photo y comprueba que no fue retirada ni desvinculada. Esto evita entregar el archivo compartido anterior cuando una supresión autorizada ha cambiado la referencia mientras la petición esperaba.

Se verifica con dos conexiones PostgreSQL, pg_blocking_pids y una ejecución real del servicio de redacción de medios, sobre datos sintéticos y comprobación de identidad simulada explícita. El perfil afectado recibe404; el otro perfil conserva sus archivos y su acceso privado. No se presenta el simulador de identidad como verificación real.

La autorización corresponde al momento de abrir el archivo bajo los locks. No puede recuperar bytes ya entregados ni cancelar retroactivamente una descarga cuyo acceso fue autorizado antes de la operación de derechos.

## Verificación y continuación

La batería final cubre particular/agencia, fotografías fuente y versiones anteriores rechazadas, acceso a la corrección nueva, creación persistida de borrador vacío, mensaje ES/EN, revisión móvil ES/EN, publicación, cargas y medios compartidos. Los resultados y hashes se registran en la evidencia de esta entrega.

La recarga manual de las mismas imágenes, las variaciones por recompresión/recorte y la rehabilitación mediante nueva revisión independiente continúan pendientes. La restricción del historial y la eliminación de copia automática no acreditan por sí solas ese control. También quedan la retención final de referencias/evidencias, identidad de cuenta, destinatarios, respuesta final y demás derechos de CR-09, y todas las fases posteriores del contrato.


Resultados terminales:43 pruebas correctas286.11s, sin fallos/errores/skips. Batería independiente de agencia8 correctas33.50s; no se suma como regresión común. [Evidencia](evidencias/acceso-historico-rectificacion.json). El acceso a referencias históricas desde otras colas generales y su conservación por finalidad siguen pendientes.
