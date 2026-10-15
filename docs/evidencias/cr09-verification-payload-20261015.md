# Candidato descartado: agrupar los tres campos de última verificación

Run `20261015-234338-54b9df2f`, SHA aplicación `cbdaba36ac8bdf84d7ad006bb2443ebd1725aee5`; test explícito aislado conservado posteriormente en `56ae6f6`, incluido en hashes originales cuando todavía era untracked. Kernel native-sealed, PostgreSQL17.11 propio, límites sin cambios. **1 PASS104,08s**, pero candidato **rechazado por beneficio inconsistente**. [Recibo](cr09-verification-payload-terminal-20261015.json).

Hipótesis finita: tres subconsultas correlacionadas sobre la misma VerificationCheck, con igual orden latest, frente a una Subquery(JSONObject) constatus/manager_version/subject_id y conversión mediante tipoFK nativo. Sin caché de resultados ni cambio persistente de app: monkeypatch únicamente en el test explícito. Compara state_page completo10ksintéticos, limpio/dirty1, listado/búsqueda, tresbloquesAB/BA con tresrepeticiones porbrazo y conexiónnueva porbrazo:72lecturas. Conteo/página/ID yvaloresverificación coinciden enloscasosprobados. Esto no cubre empatecreated_at/históricos/derechos; noafirmar equivalenciaglobal.

| Media state_page ms | Actual | Agrupado |
| --- | ---: | ---: |
| Listado limpio | 202,342 | 196,678 |
| Búsqueda limpia | 184,859 | 226,804 |
| Listado dirty1 | 340,477 | 306,867 |
| Búsqueda dirty1 | 281,438 | 323,526 |
| Total | 252,279 | 263,468 |
| CPU thread total | 119,353 | 127,328 |

Medias por bloque actual/agrupado:252,938/231,263;256,683/269,569;247,216/289,574ms. Agrupadoempeora4,44%wall/6,68%CPU total yambasbúsquedas. No se integra ni ejecuta cargaHTTP de este candidato. No nuevo p95 ni justificación de Cython/índice/precalentamiento.

Fuentecongelada verificada independientemente antesdecommit,controlador/hijo/temporal/contenedorespropiosausentes;unidadMainPID0/ControlGroupvacío. No datosreales ni serviciosnormales. Se conserva resultado completo yfuente.

El fallo de rendimiento no cambia los demás pendientes CR09. Próximo trabajo debe auditar criterios y cobertura aplicable de la versión común, manteniendo el rendimiento abierto; no encadenar cambios pequeños sin evidencia de ROI.
