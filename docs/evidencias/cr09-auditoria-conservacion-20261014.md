# Auditoría parcial de conservación CR09

Requisitos: docs/83, conservación por finalidad (10%) y purga caducada
previamente cerrada (5%). No se confunden esos alcances.

| Selección inspeccionada | Casos aprobados | Fallos de esos casos |
|---|---:|---:|
| Seguimiento de conservación | 6 | 0 |
| Calendario | 2 | 0 |
| Carreras de seguimiento/autoridad | 2 | 0 |
| Navegador móvil | 2 | 0 |
| Localización | 2 | 0 |
| Conservación de borrador/respuesta | 4 | 0 |
| Caducidad de exportación | 2 | 0 |

[Reports exactos por archivo y ejecución](cr09-conservacion-regresion-20261014.json).
El bloque 3 de origen es globalmente negativo por otro caso; los PASS
seleccionados no convierten esa batería en positiva ni acreditan N3 común.

Inspección de aserciones: el calendario recorre exactamente 1.100 entradas,
con páginas de 50, navegación reversible, filtros, cursor/usuario/ámbito y
caducidad rechazados. No convierte metadatos del calendario en decisiones
jurídicas. Seguimiento agenda cada finalidad retain/review del plan y reconstruye
idempotentemente; lectura privada auditada e independencia preceden a seguimiento.
Las carreras prueban permiso retirado durante espera sin divulgación y misma
clave concurrente con un solo evento. Seguimiento no reactiva planes caducados.

Purga de exportación preserva fuente, prueba y auditoría, rechaza revivir un
artefacto purgado al mover su caducidad y reintenta una copia inicialmente
bloqueada. Purga de borrador conserva respuestas emitidas/legacy y replay;
trabaja en lotes de 100 con continuación y sin borrar registros de evidencia.

Pendiente: contrastar cobertura completa de finalidades, excepciones, backups
y scheduling worker/Beat con esta selección y otras pruebas/evidencias existentes.
No ampliar purga/destrucción real ni asumir política productiva desde fixtures.
