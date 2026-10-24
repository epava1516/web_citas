# B08 — Conciliación y aceptación técnica local

Decisión del 2026-10-24: B08 aceptado técnicamente en local tras conciliar seis requisitos,16 casos funcionales actuales y evidencia histórica de coste/presupuesto. Once de 18 puntos cerrados: B00–B08 y B12–B13. Pendientes B09–B11 y B14–B17; B15 opcional. No aceptación beta global, producción ni candidata conjunta B16.

El problema inicial era materializar toda la población con promociones. La corrección existente ya usa state_page, con pertenencia completa SQL, orden comercial y guarda nativa de página. No había que reescribirla. Los incrementos341/342 añaden testigos que faltaban y verifican evidencias; no modifican aplicación, autorización, locks o importes.

## Matriz de requisitos

La [matriz literal verificable](evidencias/b08-local-requirement-acceptance-matrix-20261024.json) identifica seis requisitos y huellas de auditoría. Las garantías compartidas siguen en contrato16 y roadmap103; aceptar B08 no cierra toda la etapa3.

| ID | Requisito | Evidencia y alcance |
| --- | --- | --- |
| P01 | Coste con crecimiento y filtros |14 artefactos de diagnóstico1000/10000 y mismo instrumento; tres artefactos de filtros239 y seis fuentes actuales. Medianas seriales descriptivas, sin comparación causal emparejada ni nueva carga. |
| P02 | Selección y ranking paginables | Lectura directa de discovery.results, promotion_paging y publication_state; cuatro fuentes promocionales iguales al contractual296. Se hidrata la página, pero el mapa de derechos conserva coste O(derechos compatibles); no se promete memoria constante. |
| P03 | IDs, orden, rotación y exclusiones |341: 10 PASS; oráculo congelado, derechos solapados Premium/Top/Autosubida, empates, dos días, ES/EN, filtros y32 HTTP dentro de transacciones READ COMMITTED reales. Filtros239 verifica264páginas en fresh/pending/repaired, sin autosubida en ese oráculo adicional. |
| P04 | Sin truncado previo ni caché de autoridad | Mapa efímero sólo en snapshot propio RR; SQL en heredado.341 incluye revocación particular/propietario/editor y revocación comercial confirmada entre solicitudes. Snapshot no equivale a frescura después de cada cambio concurrente dentro de la misma petición. |
| P05 | Fallback íntegro |342: 6 PASS / 36 páginas:12 fallbacks cola1001,12 por 49 desconocidos y4 guarda final;8 páginas posteriores state igualmente equivalentes. Constantes48/1000 sin reducir. Cola huérfana y falta de invalidación explícitamente simuladas; no fallos reales de triggers. |
| P06 | Presupuesto, reversión y límites | Contractual296 ya aceptado B07:18.000 respuestas,15 subidas,p95 415,657 ms y cuotas declaradas. Fallback automático conserva la autoridad nativa. El rollback de versión mantiene procedimiento B13. No aceptar nueva capacidad actual por identidad parcial. |

## Fuentes y evidencia

[Paridad vigente](evidencias/b08-current-parity-regression-20261024.json):run20261024-050815-461b26b4,10PASS/0FAIL/0ERROR/0SKIP,286,126s sumados JUnit, tres workers. [Fallback real](evidencias/b08-natural-fallback-regression-20261024.json):run20261024-051609-ed913bdc,6PASS/0FAIL/0ERROR/0SKIP,124,897s sumados JUnit, un worker.1711/1712 fuentes respectivamente congeladas y contrastadas al terminar;629 archivos producto idénticos entre ambas ejecuciones y actuales al aceptar. Docker, temporal, identidad del proceso y Telegram verificados. Las ediciones posteriores de seguimiento y documentación no alteran esa evidencia original.

[Identidad de reuso](evidencias/b08-reused-evidence-identity-20261024.json) conserva contraste de artefactos y límites: frente a296hay621 archivos producto idénticos, siete archivos safety modificados posteriormente y report_authority.py añadido. No afirmar identidad global ni capacidad contractual de toda la candidata actual. Las cuatro fuentes de paginación promocional sí coinciden; B16 integrará la candidata común. Se mantienen todos los negativos, incluido341interrumpido, y las propuestas descartadas de materialización, SetPager, OFFSET y estadísticas no adoptadas.

Las medianas históricas primeraES1000/10000 pasaron de15758,2/160637,0ms y3426/34026consultas a151,3/361,3ms y33consultas en el diagnóstico de snapshot. Instrumento y estrategia sintética comunes, IDs distintos; no latencia de Internet ni ahorro causal exacto. Las cuotas, mezcla y presupuestos de TCP pertenecen al corte B07 aceptado. No se ha repetido una carga larga para producir otra cifra.

## Reversión y trabajo siguiente

Cuando el estado no es utilizable, la ruta actual cae al listado nativo completo en lugar de ocultar candidatos. Eso cubre las condiciones comprobadas, no una detección universal de errores de orden. Las promociones actuales siguen limitadas a preparación sintética; desactivar PROMOTION_TEST_MODE retira su exposición de prueba sin borrar derechos ni cambiar publicación, y no se presenta como rollback productivo de cobros reales. Una retirada de versión requiere el protocolo B13 y validación conjunta pertinente B16.

B09 debe partir de costes vigentes: SQL/hidratación/render, imágenes y activos, y observación del backlog/fallback. La cola de denuncias en safety.views es una candidata de inspección, no un defecto o ahorro demostrado. B10 mantiene aceptación provisional MOD09; B11 evita reescritura cosmética. Se preserva dirección B15 con cookies propias y preferencias privadas cifradas con cuenta; arquitectura y evaluación jurídica siguen pendientes.
