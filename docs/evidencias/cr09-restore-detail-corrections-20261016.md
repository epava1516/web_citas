# Correcciones de pruebas de restauración y detalle

[Recibo con resultados y huellas](cr09-restore-detail-corrections-20261016.json).

| Ejecución | Resultado | Alcance |
|---|---|---|
|210312-31517a3b|2 PASS, 65,84 s|Restauración PostgreSQL base y evidencia comercial|
|210618-e29117b1|1 FAIL, 47,98 s|Clasificador de familias SQL no distingue derechos integrados en hidratación|
|210906-8ef00853|1 PASS, 50,57 s|Guard de detalle preparado, paridad y frescura|

El injerto comercial utiliza un marcador único del hijo de recuperación y conserva las aserciones de digest, ausencia de ranking/bump y duplicados. El test del detalle acepta el contexto preparado antes del guard, desactiva la preparación en el alias real de la vista para comparar el control y observa las subconsultas de derechos aunque la familia principal del SQL sea hidratación. Conserva 14 llamadas, cambios de categoría y blob, firma, no-store, planes genéricos y restauración de cursor/umbral; el uso externo del guard conserva su binding nativo.

Solo cambios de pruebas. Se preservan los fallos originales de la continuación y la correctiva intermedia. Recursos propios sintéticos, PostgreSQL real/native-sealed, un worker y límites anteriores. Terminal, freeze y limpieza comprobados independientemente. No mide capacidad ni acepta N3/CR09. Ocho fallos diagnósticos originales pendientes, además de omisiones, validación integrada, runtime actualizado y carga contractual limpia.
