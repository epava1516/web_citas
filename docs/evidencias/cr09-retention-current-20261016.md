# Conservación: revalidación de calendario, finalidad y autoridad

Run `20261016-005352-06e9c88e`, SHA `7934622`: **8 PASS en 96,69 s**, cero fallos, errores u omisiones. PostgreSQL y Redis propios, datos sintéticos, controlador limitado a cuatro CPU/3584 MiB y recursos del adaptador conservados. No cambios de aplicación ni nueva carga HTTP.

Se revalidan `test_retention_reviews.py` y `test_retention_review_races.py` porque sus fixtures ejecutan supresión de cuenta/publicación, modificada después de la regresión común. [Recibo con los ocho casos](cr09-retention-current-terminal-20261016.json).

Las aserciones comprueban: calendario de todas las finalidades retain/review, reconciliación idempotente y reparación parcial sin sobrescribir seguimiento; inspección privada y auditada, revisión independiente, CSRF y versiones; conservación de datos/plazo original tras seguimiento y cuenta suprimida; rechazo de plan alterado; lectura de todas las páginas históricas y replay del snapshot original; revocación de permiso durante espera PostgreSQL observada que impide divulgación; concurrencia de la misma clave con una única actualización/evento.

No se prueba autorización jurídica real de conservación, purga poblada de cada tarea, todas las excepciones, despacho horario ni N3 integrado. Un calendario de seguimiento no amplía el plazo ni autoriza tratamiento. Los resultados anteriores se conservan; esto acredita aplicabilidad de esta selección a la versión actual.

Verificación independiente previa a documentar: hashes exactos, controlador/hijo ausentes, temporal retirado y contenedores propios inexistentes; unidad terminal MainPID0/ControlGroup vacío. Dependencias congeladas, Ruff, documentación, Django, migraciones y herramientas nativas pasaron dentro del run. CR09 y el resto del contrato siguen abiertos.
