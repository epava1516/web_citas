# Conservación de objetos huérfanos: prueba física con PostgreSQL y RustFS

**1 PASS en 49,11 s**, run `20261016-000418-429fdc14`, SHA integrado `e5d2956` completo en el [recibo](cr09-orphan-retention-terminal-20261016.json). Test nuevo conservado en `7fa3c61` después de verificar la igualdad de las fuentes con source-hashes inicial. No se modifica código de aplicación ni el intervalo horario.

La tarea `purge_orphan_export_objects` dispone de un día de gracia y excluye claves referenciadas por RightsExportImage/Part. La búsqueda finita no encontró pruebas funcionales directas de esta tarea; el control anterior sólo comprobó su registro. Este test usa PostgreSQL y el fixture RustFS real con imagen fijada, puerto local, credenciales sintéticas y recursos limitados. Se inyecta la instancia real de repositorio y se adelanta explícitamente el reloj dos días; no se simulan respuestas S3 ni datos ORM. No acredita que hayan transcurrido 24 horas reales.

Comprobaciones ejecutadas:

- El huérfano reciente sobrevive al primer barrido.
- Recuperación activa y almacenamiento deshabilitado impiden la purga.
- Con reloj posterior al día de gracia, se elimina exactamente el huérfano: HEAD devuelve404.
- El objeto antiguo ligado a RightsExportPart conserva su referencia, existe y se descifra a los bytes originales.
- Repetir la tarea devuelve0, sin borrar el objeto retenido.

La exportación y su parte se crean en el flujo de dominio con identidades sintéticas; el adaptador de identidad de ese fixture no representa verificación real de personas. La verificación física de PostgreSQL/S3 sí utiliza servicios reales propios. No hay producción ni proveedor externo.

Se conserva intento `000356-ba72c0a9`, detenido por Ruff antes de tests funcionales por importación del fixture; corregido el test, sin aplicación cambiada. Ambas ejecuciones tienen fuentes y limpieza verificadas. Final: controlador/hijo ausentes, temporal del runner eliminado, contenedores PG/Redis ausentes, ningún contenedor con etiqueta del fixture de objetos restante; la propia finalización del fixture también comprueba la retirada exacta de RustFS. Unidad exit0/MainPID0/ControlGroup vacío.

La [conciliación de tareas y reports](cr09-retention-policy-crosswalk-20261016.json) verificó18 cuerpos de tarea iguales por AST a v3,12 con reports crudos PASS y test coincidente en el índice previo,17 con despacho real. No prueba todos los helpers ni la política completa. El índice anterior omite pruebas nuevas de caducidad/huérfanos y cobertura indirecta de limpieza de medios; no interpretar sus seis ausencias como seis tareas sin pruebas.

Pendientes conservados: política por finalidad/excepción/recurso, reconciliación pertinente de backups/restauración y aplicabilidad común, despacho horario si lo exige el criterio. CR09/N3 y rendimiento siguen abiertos; no hay p95 nuevo.
