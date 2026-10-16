# Retirada correctiva de 0021

Migración 0022 restaura exactamente MARK0020 y los tres triggers originales0015, y elimina helpers0021. Se conserva historial reversible. No toca modelos, reglas nativas, SLO, filtros ni datos reales. Las invalidaciones conservadoras de borradores vuelven a la ruta normal.

Run `20261016-051506-ee981916`, HEAD cf86cd0 más corrección registrada en source-hashes: **10 PASS en 123,23 s**, cero fallos/skips. SQL prosrc verificado, ida/vuelta0021/0022, private Revision/Photo vuelven a Dirty; escritores prebloqueados completan; publicación concurrente espera al escritor y conserva estado nativo; cuatro controles MatchPhoto y dos de refresco frente a referencias bloqueadas. Fuentes congeladas y limpieza de procesos/temporal/contenedores propios verificadas independientemente, unidad inactive/MainPID0/cgroup vacío.

| Caso acotado | 0021 rechazada | 0022 restaurada |
|---|---|---|
| Dos escritores con Listing propio prebloqueado | FAIL: deadlock | PASS: ambos completan y estado exacto |
| Publicación concurrente con Blob no confirmado | PASS anterior | PASS actual, espera PG observada |

No hay nuevo p95. No aplicar el ROI secuencial del prototipo al producto restaurado. Tests funcionales de la función retirada conservados en `tests/rejected_private_draft_migration.py`, fuera de colección automática, no evidencia vigente; experimentos owned explícitos siguen disponibles y conservan el FAIL. Se añade control normal de Listing prebloqueado a MatchEdges para la regresión permanente. Pendientes su ejecución y proyección/lifecycle/condicional, imagen actualizada y rendimiento. No aceptación CR09/N3/global.
