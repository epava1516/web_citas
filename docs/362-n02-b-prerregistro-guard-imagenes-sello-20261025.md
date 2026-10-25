# N02B — candidato del guard físico de imágenes con sello válido

25 de octubre de 2026. Base6bffd48, [resultado361](361-n02-a-resultado-metadatos-imagenes-20261025.md) y [revisión de fuentes](evidencias/n02-llamador-investigacion-20261025.json). N00/N01aceptados2/13;N02/N06abiertos,alfa. Grafo previo1955fuentes/18330nodos/80645relaciones,actualizado y verificado antes de preparar este candidato.

## Cambio delimitado y presupuesto previo

Modificar sólo _verify_current_images en apps/safety/rights_portability_export.py: conservar consulta de binding, descifrado de selección y digest por declaración; usar image_contents para obtener metadatos frescos por lote. Mantener orden de declaraciones y cardinalidad estricta,16lecturas/hash cuando hay16imágenes; ningún byte se reutiliza entre invocaciones. No tocar validador completo, sello/replay, autoridad, expiraciones, objetos, snapshots, auditorías, transacción ni entrega. El cambio de versión de reglas por fuente conserva la invalidación normal de sellos anteriores.

Presupuesto de la etapa con n imágenes válidas: anterior1+3nSELECT, candidato1+3si n>0; para dos imágenes7→4,para16imágenes49→4. Ambas variantes conservan exactamente nlecturas completas/orden/SHA; lista vacía sólo consulta binding y descifra. La mejora361pertenece a primitivas existentes; aún no mide este guard integrado ni el flujo completo.

## Comparación y testigos reales

Instrumento nuevo tests/test_held_seal_image_batch.py. Preparar un caso real sintético de portabilidad con dos imágenes distintas mediante servicios nativos de selección/inspección/aprobación/cobertura/generación. Ampliar sólo receta de fixture binaria de una a dos imágenes; no reemplazar validators, holds, replay, fuente, permisos ni archivos por simulaciones. La prueba usa PostgreSQL real propio,almacenamiento local privado,DEBUGFalse. La verificación externa del sujeto sigue siendo el simulador explícito de la fixture histórica; no se acredita proveedor o identidad real.

Comparar guard anterior exacto extraído de AST de6bffd48 con guard candidato en el mismo proceso/caso/exportación/archivos y transacción autorizada, con seis parejas alternando orden y primera pareja separada. Congelar el cuerpo original y comprobar su identidad antes de ejecutarlo; el reemplazo temporal sólo selecciona la implementación del guard bajo prueba, no evita holds ni validación. Medir reloj de guard,CPU/SQL y nlecturas/hash. Cinco parejas posteriores dan mediana/rango; sin p95/p99 ni umbral nuevo. Criterio354: coste determinista no aumenta y tiempo de misma etapa no empeora; señal ambigua permanece inconclusa. No trasladar mejora de dos imágenes al tamaño MOD09 ni a descarga completa.

Antes de cada guard se exige que el camino real haya usado sello válido; ninguna muestra puede venir de fallback de validador completo. Observar desde otra conexión PostgreSQL, con intentoNOWAIT y savepoint, que todos los Blob/Photo declarados ya están bloqueados antes del guard. IDs en orden inverso dePK para evitar una prueba accidentalmente ordenada. No guardar UUID/SQL/parámetros ni datos privados; sólo conteos/tiempos/digests agregados.

Negativo focal: después de una validación con sello válido, alterar físicamente el último archivo conservando metadatos y cabecera WebP; exigir nueva lectura de ambos y rechazo por hash, sin mutación de auditorías/entrega. Restaurar bytes en finally. Revalidar controles originales del sello frente a ocho cambios de evidencia, caducidad/cambio de reglas y pipeline/autoridad fresca. Mantener testigo original de drift entre hijos y rollback; las cuatro primitivas ya verificadas en361 no sustituyen regresión del llamador.

Selección prevista: archivo nuevo con2casos, test_generation_seals_and_later_validations_use_it, test_any_input_change_disables_the_seal_and_matches_full_validation[8], test_seal_expires_at_the_earliest_loaded_expiry_and_on_code_change, test_pipeline_never_bypasses_original_full_fresh_guards y test_physical_bytes_changed_between_children_roll_back_all_batch_audits. Los parametrizados finales se contarán exactamente antes del run. NingúnSKIP cuenta comoPASS. Runner focused --workers1,PG17/Redis7.4propios,librdbv2.4.0,techo900sporcomando;sin carga ni límites dedicados.

## Evidencia y disposición

Antes de ejecutar: fuente original preservada, código/instrumentos revisados, AST actualizado y semántica focal del protocolo,congelación de fuentes/grafo/dependencias/imágenes/selección y commit. Después: JUnit/journal, muestras/coste/bytes/orden, origen de sello y locks reales, negativos originales, hashes intactos hasta auditoría, limpieza y Telegram terminal confirmado. Conservar fallos/reintentos justificados.

Si se adopta, tabla de tiempos anterior/candidato de la misma etapa con muestra/variabilidad/diferencias válidas y alcance; comparación integrada de etapa no es aceptaciónMOD09. N02requiere además atribuir cobertura/entrega completa, crecimiento y concurrencia, conservando objetivos2s/5s,FAILy excepción provisional en ámbito original. Resto del contrato obligatorio sigue abierto;no activarN12–N14ni publicar/proveedores/datos reales.
