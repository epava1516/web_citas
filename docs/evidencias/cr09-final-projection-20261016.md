# Corrección del resultado final: copias de publicación reintroducidas

**Defecto reproducido y corregido en9254ce5.** El resumen de supresión comprobaba Listing/Revision pero omitía PublicationState, que contiene texto y fechas copiados. Al reintroducir esa proyección, publication continuaba figurando como completada. No se afirma acceso público ni cierre integral: el flujo mantiene otras limitaciones y decisiones pendientes.

Reproducción `20261016-001455-644b1704`:**1FAIL47,53s**, en la aserción que exigía publication pendiente tras reintroducir la copia. Fuentes congeladas y limpieza verificadas antes de corregir. El fallo permanece.

Corrección: la comprobación de publication exige también que no exista una proyección con elegibilidad, referencia de revisión, texto o fechas residuales. Admite la ausencia de fila y la proyección vacía reconstruida por el refresco. No borra datos durante la revisión final: refleja el estado en completed/pending y permite que los mecanismos existentes invaliden material anterior. No cambia finalidades seleccionadas, autorizaciones ni plazos.

[Resultado terminal](cr09-final-projection-terminal-20261016.json):run `20261016-001657-9f1ed261`,**11PASS160,13s;0FAIL/ERROR/SKIP**. Test nuevo comprueba ausencia inicial, reconstrucción vacía válida, copia restaurada pendiente y retorno a completada al retirar el contenido. Batería existente cubre material, revisión independiente, respuesta HTTP, cuenta, móvil y ausencia física de medios. Este conjunto no constituye N3 común ni aceptación de toda la conservación.

SHA al ejecutaraba6cb4 con cambios incluidos en hashes iniciales; commitposterior9254ce5 conserva fuente comprobada. PostgreSQL/Redis propios, Python3.12.15 y límites existentes. Dependencias/Ruff/docs/Django/migraciones/nativos pasaron. Verificación independiente de fuentes exactas, controlador/hijo ausentes, temporal retirado, contenedores ausentes y unidadexit0/MainPID0/ControlGroupvacío. Sin datos reales ni proveedores. No nuevo p95.

## Actualización del grafo

Corteaba6cb4, anterior a esta segunda corrección:11269nodos/44655aristas/485comunidades,0dangling y131selfloops. AST actualizado; agente nativo existente graph_update_docs_1 extrajo5documentos,21nodos/23aristas con fuente/ubicaciones validadas. No invocaciónClaudeV1 ni proveedor externo; tokens nativos no reportados(null), consumo anterior intacto. No se generó HTML.

Límites:216archivos no clasificados,2SQL sinparser; grafo simple no conserva todas las relaciones paralelas y no acredita cobertura completa. Los documentos posteriores al corte y9254ce5 no quedan incluidos por esta actualización. Recibos e instrumentos permanecen enartifacts/graphify-update-c2114cd/recovery-retention-*. El grafo orientó la revisión de las rutas, mientras la prueba PostgreSQL confirmó el defecto.
