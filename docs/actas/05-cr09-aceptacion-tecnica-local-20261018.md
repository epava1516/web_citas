# CR09 — aceptación técnica local, 2026-10-18

Se acepta CR09 en el alcance técnico local del contrato vigente. Revisor: Codex principal. Corte de fuentes probado: `657f727` y producto idéntico a la regresión integrada; **1.373 archivos técnicos**, incluidos código, pruebas e instrumentos, coinciden con los de ambas particiones comunes. Los cambios entre commits de documentación no se presentan como versiones funcionales distintas.

La decisión se basa en la [matriz de los nueve criterios originales](../evidencias/cr09-local-acceptance-matrix-20261018.json), con requisito literal, evidencia, versión, decisión y límites. No se deduce de contar etapas verdes.

| Criterio local | Decisión y fundamento |
| --- | --- |
| Portabilidad y respuesta privada | Aceptado: revisión de cuatro escenarios perfil/cuenta ES/EN y dos negativos, originales sintéticos asociados al escenario, cierre/replay/descarga y JSON/binarios reales. [Revisión](../evidencias/cr09-owned-content-review-20261018.md), [TCP/JSON](../evidencias/cr09-excluded-functional-terminal-20261018.json). |
| Derechos, finalidad, verificación y autoridad | Aceptado: flujos por derecho y permisos/autoridad/revocación, con aserciones y ejecución actuales. [Correspondencia](../evidencias/cr09-current-requirement-report-crosswalk-20261018.json), [seguridad](../evidencias/cr09-local-security-review-20261018.json). No acredita identidad real. |
| Conservación y destrucción por finalidad | Aceptado para configuración y recursos propios ensayados: excepciones, vencimiento, reintentos, referencias compartidas y tareas. [Pruebas actuales](../evidencias/cr09-retention-recovery-current-reports-20261018.json). Registro/cadencia y despacho tienen alcance separado de contenido y custodia productivos. |
| Restauración PostgreSQL y medios | Aceptado: restauración real, aplicación de supresión, bloqueo de publicación/credenciales obsoletas, pares preservados e idempotencia. [Trece casos actuales](../evidencias/cr09-retention-recovery-current-reports-20261018.json). No extrapolar RPO/RTO fuera del fixture. |
| Recursos y fuentes finitas | Aceptado para fuentes necesarias del escenario: censo, procedencia y decisión de divulgación revisada; archivo privado desconocido bloquea cierre. [Cuatro revisiones y límites históricos](../evidencias/cr09-owned-content-review-20261018.md). No clasifica semánticamente todos los archivos históricos ni exige recursos ajenos al escenario. |
| Comunicaciones y destinatarios | Aceptado localmente: buzón y adaptadores identificados, lectura/acuse/revocación/roles/concurrencia y cierre. [Mecanismos actuales](../evidencias/cr09-current-mechanisms-docker-binding-20261018.json), [seguridad](../evidencias/cr09-local-security-review-20261018.json). Sin afirmar recepción externa real. |
| Urgencia y escalado | Aceptado: simulacro técnico con suplencia, autoridad, decisión y negativos, presente en versión común. [Catorce casos actuales](../evidencias/cr09-current-mechanisms-docker-binding-20261018.json). No acredita disponibilidad de personas reales. |
| Rendimiento de expedientes grandes | Aceptación provisional MOD09 conservada. Los FAIL históricos y deuda mejorable permanecen; no se redefinen los umbrales ni se reabre esta optimización como bloqueo de la continuación. |
| Integración y revisión CR09 | Aceptado en esta fase: regresión conjunta sobre fuentes técnicas iguales, exclusiones necesarias con evidencia específica, recuperación, Docker, revisión técnica y carga limpia reproducible. [Matriz completa](../evidencias/cr09-local-acceptance-matrix-20261018.json). |

## Evidencia integrada y rendimiento

Regresión funcional: 3.214 PASS más cuatro subpruebas, 122 SKIP. Capacidad serial: 290 PASS, ocho SKIP. Selecciones disjuntas, 3.634 casos distintos; tres incorporaciones de avisos respecto a la batería histórica. Los 130 SKIP se conservan como tales: diagnóstico/prototipo explícito no se convierte en entrega. Las obligaciones de contenido, runtime, rutas y exclusiones funcionales tienen evidencia específica vinculada en la matriz; no se suman como casos únicos ni se borra el historial.

[Control positivo actual](../evidencias/cr09-dirty-refresh-current-terminal-20261018.json): Beat publica, worker ejecuta no-eager, una marca eliminada en29,14s≤45s, IDs emparejados y limpieza independiente. Resuelve el hueco de los refrescos con cero marcas del contractual.

| Medición HTTP limpia | p95 observable | Dinámicas correctas | Subidas correctas | Veredicto |
| --- | ---: | ---: | ---: | --- |
| Corto60s | 0,723973s | 1.200 | 1 | PASS válido |
| Contractual900s | 0,334852s | 18.000 | 15 | PASS válido |
| Repetición900s | 0,332467s | 18.000 | 15 | PASS válido |

[Corto](../evidencias/cr09-current-short-terminal-20261018.json), [contractual](../evidencias/cr09-current-contractual-terminal-20261018.json), [repetición](../evidencias/cr09-contractual-repro-terminal-20261018.json). Cero errores y generador válido en cada uno; sin perfiladores, cuatro sync, worker/Beat normal, fuentes congeladas, recursos propios y limpieza independiente. Los ensayos no demuestran mejora causal del código ni permiten atribuir al código diferencias del portátil con perfil energético variable. Docker v10 es equivalente al producto actual y conserva su alcance funcional, sin capacidad Docker presumida.

## Continuación y producción

Esta aceptación satisface la revisión N3 de CR09 dentro del alcance local declarado, con MOD09 provisional. **No acepta la aplicación completa, GS01 ni producción.** El objetivo íntegro continúa por CR10→GS01→B-F/B-B→C. La fase C exigirá la verificación final de su versión integrada; cambios funcionales posteriores requieren pruebas por impacto.

Quedan separados los requisitos de producción: operador, identidad/proveedores reales, revisión jurídica/textos definitivos, política/custodia externas, geografía nacional real verificada, destinatarios y disponibilidad humana y revisión externa de seguridad. No se publica ni contrata nada. La auditoría previa [04](04-cr09-auditoria-pendiente.md) se conserva como historial, sustituida en estado actual por esta acta.
