# Auditoría parcial de urgencias CR09

Requisito de docs/83: rol, suplencia/revocación, canal local, plazo sintético,
cronología y resultado terminal. La prueba ES/EN en
`tests/test_urgent_report_drill.py` verifica que reconocer no resuelve;
asignación primaria, revocación con GET/POST denegados, suplente sin permiso
de reasignación denegado, concesión explícita de reasignación, lectura auditada
antes de decidir, resolución terminal y replay sin duplicar acciones. Mantiene
el acuse previo y retira el caso resuelto del seguimiento. Avisos quedan queued;
no demuestra entrega externa ni cobertura humana.

El mismo archivo tiene 12 controles de revocación permiso/sesión/MFA/actividad
tras bloqueos, en llamada nueva/replay/retorno. Los 14 casos pasaron en el
bloque 2 de 9b0353f. No es aceptación de versión común N3.

| Recorrido sintético | Resolución observada | Plazo del fixture |
|---|---:|---:|
| es | 0.894869 s | 300 s |
| en | 1.051245 s | 300 s |

[Propiedades y cronología JUnit](cr09-urgencias-regresion-cronologia-20261014.json).
Pendiente reconciliación de cobertura/versión común; no repetir este simulacro
sin defecto o criterio concreto pendiente.
