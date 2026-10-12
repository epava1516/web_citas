# Resultados de unseal y valoración propia comunicados al notebook

2026-10-11. Conversación99c86acd-9184-4561-8d47-e5c44f4636ab; notebookbb1f4634-45b7-4f41-b807-4b8502614b9d,100fuentes. Sin nuevas fuentes ni borrados.

[Consulta y valoración exactas](mod08-notebook-resultados-unseal-consulta-20261011.txt) / [respuesta completa](mod08-notebook-resultados-unseal-respuesta-20261011.json).

Se enviaron cifras de diagnóstico real, límites del fixture pequeño/sondas escalares, ausencia de Cython histórico/p95, y criterio propio: no introducir memoJSON; medir un lote representativo grande; si el parseo repetido sigue pequeño, investigar execution/fetch/pipeline.sync y trabajo no observado. El notebook coincide y propone baseline diagnóstico.

Contraste local: sí existen diagnostic_baseline.restore/resume y test_owned_target_stage_profiles. Pero resume llama finish del flujo posterior a cobertura aprobada: no equivale a un lote de navegación aislado. El arnés puede rechazar baseline y volver a preparación completa; no ejecutar su comando como supuesto diagnóstico de una sola petición. No se encontraron archivos baseline/clave en artifacts de este checkout en la búsqueda acotada; existencia del mecanismo no acredita disponibilidad de un snapshot válido. PHASE_TARGETS no incluye parse ni pipeline.sync: hay que integrar el nuevo instrumento/desglose explícitamente. Los umbrales5%/20% que propone el notebook no están medidos ni acordados; no son criterios contractuales. Su referencia a orjson no describe crypto.unseal, que usa json.loads. No está demostrado que deepcopy de diccionarios reales necesariamente supere el parseo: debe medirse.

No nuevas pruebas/mediciones/producto en esta consulta. Diagnóstico local anterior terminado; MOD08 completo sigue pausado. Ningún ahorro demostrado adicional ni aceptación2s.
