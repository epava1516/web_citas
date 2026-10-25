# N07A — corrección verificada de reordenación concurrente

25 de octubre de2026. Alfa. Se acepta localmente esta corrección funcional, **no todo N07**. El contrato conserva6/13bloques obligatorios aceptados. [Prerregistro400](400-n07-a-prerregistro-medios-publicacion-20261025.md), [reproducción/candidato401](401-n07-a-carrera-reordenacion-retirada-20261025.md), [original auditado](evidencias/n07-a-original-auditoria-20261025.json), [alcance de código](evidencias/n07-a-alcance-correccion-20261025.json) y [contraste correctivo](evidencias/n07-a-candidato-auditoria-20261025.json).

## Resultado y autoridad

Original20261025-222614-c4dfdaad:2FAIL por500/StopIteration en ambos idiomas. Correctivo20261025-223112-9764c87c: **4PASS/0FAIL/ERROR/SKIP**,57,786sJUnit. Los dos casos de carrera usan bloqueos reales PostgreSQL y retirada confirmada entre consulta y continuación de reorder. Ahora devuelven404, mantienen retirada/compañera/posiciones y sólo el incremento de edit_version de remove. Los dos casos existentes de localización ES/EN usan Chromium156real y conservan400dirección inválida,409revisión no editable,404titular ajeno,302reordenación válida y retirada/versión/orden esperados. No se editaron esos casos existentes.

Codex revisó el único cambio de producto en reorder, las1751huellas de la congelación, los resultados/JUnit/propiedades originales, las guardas y los cuerpos AST de las demás funciones. Los dos documentos nuevos aún no rastreados por Git se verificaron aparte del manifiesto del runner; no se afirma que estuvieran registrados por éste. El ejecutable Chromium/launcher coincide antes/después. Recursos propios y temporal ausentes, Telegram terminal sent y auditoría independiente PASS. Una envoltura de observación pasa por el guard real y sólo registra PID; no sustituye permiso, HTTP, reloj o retirada. Preparación eager explícita, no evidencia de broker.

## Antes y después

| Acción/medida | Antes | Después | Diferencia y alcance |
| --- | --- | --- | --- |
| Reorder espera mientras se retira la foto, ES/EN |500por StopIteration,2FAIL |404controlado,2PASSdentro de correctivo | Corrección funcional demostrada con PostgreSQL real |
| Retirada, compañera, posiciones y edit_version | Efectos previos conservados antes del error | Conservados; reorder denegado no añade edición | Sin reintroducir foto ni alterar orden |
| Reordenación normal y denegaciones existentes | Oráculos originales del producto |2PASSnavegador ES/EN |400/409/404/302y efectos conservados |
| Consultas y guardas | Misma lista activa bajo bloqueo | Ninguna consulta añadida; guardas intactas | Inspección del cambio, no porcentaje de velocidad |
| Latencia de aplicación | Sin medida aislada comparable | Sin medida aislada comparable | No evaluable como mejora temporal; no se inventa porcentaje |
| Duración de QA |44,212sJUnit,2casos fallidos |57,786sJUnit,4casos aprobados | Selección distinta; no representa antes/después de rendimiento de la app |

El original fallido permanece como tal. También se conservan el rechazo inicial de argumentos, el ERROR Ruff anterior a pytest y los errores corregidos de los auditores (vista parcial y documento fuera del manifiesto), con sus avisos terminales. Ninguno se convierte en PASS retroactivo ni se atribuye al producto.

## Trabajo restante

N07 conserva39IDs por conciliar: lifecycle/publicación, revisión/apelaciones, gestión de medios, señales/tareas/Beat y autoridades/retención compartidas. La revisión nativa aporta agrupación y fuentes, no39PASSindividuales. Se preparó en worktree aislado el diagnóstico N07B de publicación con prefork/rol restringido, backlog y bulk/rawSQL, cadencias nativas30/60s y sweep manual separado; aún no ejecutado. N03/N04/N05/N06 y N09/N10 conservan sus propietarios y límites. No se fuerza optimización marginal, no se abre beta y MOD09 restante sigue diferido al final por decisión del usuario.
