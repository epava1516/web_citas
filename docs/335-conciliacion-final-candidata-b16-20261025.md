# B16-373 — Conciliación final de candidata, en revisión

La [matriz de candidata](evidencias/b16-final-candidate-reconciliation-20261025.json) fija 1507 fuentes ejecutables, pruebas y dependencias desde el prerregistro de la ejecución contractual370, commit 8f68fc8. Documentación posterior no cambia ese producto. Las 45 funciones testigo de AD01–AD11 conservan sus SHA actuales frente a la [revisión semántica329](329-revision-semantica-testigos-b16-20261024.md); se conserva el puente explícito de la guarda de registros históricos posterior a353. Esto no es una repetición completa sobre la versión final.

## Resultados que se conservan separados

La regresión funcional original conserva 3697 PASS, 3 FAIL y 129 SKIP; la correctiva de23casos permite conciliar3700PASS/129SKIP, sin reescribir el ERROR original ni sumar grupos solapados. El carril ordinario de capacidad conserva297PASS/9SKIP. Los ocho recorridos funcionales omitidos tienen testigos suplementarios; los121diagnósticos/prototipos no ganan crédito PASS.

Las [once exclusiones](evidencias/b16-exclusions-final-disposition-20261025.json) tienen disposición de alcance: siete casos exactos actuales aprobados, dos territoriales reutilizados con puente de fuentes/helper, y dos HTTP antiguos sustituidos para el requisito aplicable por los controles actuales368/370. Estos dos últimos no son ejecuciones aprobadas de aquellos nodeids antiguos. El FAIL corto histórico permanece. Véanse [330](330-conciliacion-exclusiones-b16-20261024.md) y [334](334-auditoria-http-contractual-b16-20261025.md).

## Nueve instrumentos opt-in de capacidad

Su SKIP original permanece, incluso cuando hay testigo explícito posterior. HTTP beta tiene ahora368/370. Preflight de proxy/purga tiene361. Entrega completa tiene362: FAIL de tiempo, integridad y aislamiento verificados; se conserva bajo la aceptación provisional MOD09 y la disposición individual B10, sin convertirlo en PASS ni cerrar su deuda de rendimiento.

Los perfiles de etapas, atribución de fuentes y herramientas profesionales son diagnósticos de coste/instrumentación, no una puerta de producto que exija activar todas las herramientas para aceptar una candidata. La reconexión nativa inspecciona también instrumentación del diagnóstico y no se acredita por los otros PASS. Las selecciones TCP individual y concurrente siguen omitidas en ese carril;362 ejercita entrega y dos sujetos concurrentes, pero no se adjudican automáticamente esas selecciones exactas ni sus presupuestos desde dicha evidencia. Su aplicabilidad restante debe quedar resuelta antes del acta B16. No se lanza una batería sólo para eliminar SKIP.

## Pendientes concretos de aceptación

Falta completar la disposición por requisito de esos instrumentos, enlazar recuperación y requisitos operativos con sus actas/evidencias y fijar la aceptación individual de deuda no crítica. La [auditoría334](334-auditoria-http-contractual-b16-20261025.md) ya resuelve la medida contractual actual, recursos, conservación y retirada. B14/B15/B17 mantienen sus alcances externos/opcionales y la entrega sigue en alfa; no se consideran técnicamente completados por trasladarlos a deuda.

La reconstrucción completa desde cero del grafo y el diferencial del inventario original siguen siendo obligaciones finales, antes del acta final del contrato. El refresco dirigido de334y seguimiento incorpora diez citas literales comprobadas, conserva AST y comunidades y no satisface esa reconstrucción. B16 permanece abierto y el balance es14/18.
