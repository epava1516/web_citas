# B08-342 — Fallback promocional con umbrales reales

Grafo399 revalidado antes de este hito:14.015nodos/60.235relaciones,1748fuentes y cero hashes obsoletos. Consulta orientativa BFS truncada y contraste directo posterior de discovery.results, publication_state._state_page, modelo PublicationDirty y pruebas previas; no extracción semántica global.

## Prerregistro

Se añade tests/test_promotion_natural_fallback.py:seis casos PostgreSQL, tres escenarios por ES/EN. Cada caso prepara60perfiles sintéticos y siete derechos Top mediante pedidos/eventos sintéticos, conserva los límites reales48/1000 y compara listado y búsqueda photography con autoridad nativa y ranking congelado. Recorre todas las páginas: IDs, orden, recuento, unicidad y etiquetas; exige motivo de fallback y conservación de marcas cuando corresponde.

- dirty_1001:1001marcas huérfanas sintéticas persistidas fuerzan el techo global real. No demuestra1001escrituras de dominio ni sus triggers.
- unknown_49:49candidatos reales marcados mediante el servicio, con petición en transacción READ COMMITTED heredada; no se sustituye state_page ni el umbral.
- stale_guard:se invalida el teléfono de un perfil promocionado y se elimina deliberadamente su marca para simular divergencia del estado derivado. La primera página debe caer a la guarda nativa, excluirlo y volver a marcarlo. Las páginas posteriores pueden usar state_page; deben conservar el resultado nativo completo. No es prueba de una invalidación defectuosa real.

Un único selector de archivo, un worker y timeout1200s por comando; PostgreSQL/Redis/nativo propios mediante run_local_ci. Los seis casos pertenecen al mismo archivo y el runner distribuye por archivo; aumentar workers no paralelizaría esta selección. No se repiten los diez casos de341: sus fuentes y las de aplicación siguen intactas. Se verificarán fuentes congeladas, JUnit, limpieza real y recibo Telegram antes de aceptar resultado.

## Criterios de B08 pendientes

Conciliar esta ejecución con la paridad completa341, el coste histórico auditado1000/10000 y el contractual B07 vigente, distinguiendo hashes idénticos de cobertura funcional. El mapa de promociones sigue proporcional a los derechos compatibles y no conserva resultados entre peticiones. Sin límites arbitrarios de candidatos, cambios de aplicación, prueba de proveedor real o nueva carga contractual en este corte. B08 sigue abierto y el balance permanece diez de18puntos.

## Resultado y decisión posterior

Ejecución20261024-051609-ed913bdc:6PASS/0FAIL/0ERROR/0SKIP,124,897s sumados JUnit.36páginas, con12fallbacks dirty1001,12unknown49,4guarda final y8páginas posteriores state.1712fuentes congeladas, contenedores/temporal/proceso terminados y Telegram verificados. La [matriz303](303-matriz-cierre-promocional-b08-20261024.md) concilia el resultado; el [acta18](actas/18-beta-b08-aceptacion-local-20261024.md) acepta B08localmente. El prerregistro anterior conserva su estado previo a la ejecución.
