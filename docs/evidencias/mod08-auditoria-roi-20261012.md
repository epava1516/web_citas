# Auditoría de proporcionalidad técnica / ROI, MOD-08, 2026-10-12

Solicitud posterior del usuario: limitar mecanismos a lo obligatorio y/o beneficioso;
identificar sobreingeniería real sin confundir decisiones técnicas con exigencias legales.
Revisión en lectura de SHA388c991 durante medida congelada. Sin cambios ni cargas nuevas.
Tres agentes nativos de lectura acotada (roi_chain, roi_crypto, roi_traceability), no ClaudeV1;
Codex conserva dirección y verifica las propuestas contra código/pruebas/fuentes primarias.
Sus reportes no acreditan pruebas ejecutadas ni aceptación: crypto/trace tienen campos de
formato incompletos/no normativos; sólo se usan hallazgos que Codex verificó en fuentes.

## Resultado

Hay trabajo evitable confirmado en rotación de claves y amplificación de comprobaciones
confirmada en los caminos caros. La amplificación no demuestra por sí sola inutilidad:
varias repeticiones sostienen garantías contractuales más fuertes que el mínimo legal.
No existe ROI monetario ni probabilidad de incidentes medida; desconocido no equivale a cero.
El coste marginal de cada control en p95 HTTP tampoco está aislado todavía.

La metodología es riesgo concreto → resultado protector → prueba negativa → beneficio
marginal de repetir/ampliar → alternativa equivalente o garantía que cambiaría → coste
medido → decisión. Seguridad, privacidad y trazabilidad también cuentan como beneficios,
no sólo milisegundos. La disponibilidad y la carga humana son parte del coste.

## Marco legal acotado

El RGPD regula resultados y responsabilidad, seguridad proporcionada al riesgo y derechos
como acceso/portabilidad; no prescribe esta cadena SQL ni un POST por cada página.
Minimización y retención también limitan cuánto se conserva. [RGPD, arts5/15/20/25/32](https://www.boe.es/buscar/doc.php?id=DOUE-L-2016-80807).
El CEPD exige eficacia demostrable, no una tecnología concreta, y permite alternativas
eficaces que consuman menos tiempo/recursos; el coste no excusa incumplir la protección.
[Guía4/2019 v2, §§13–16 y23–25](https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_201904_dataprotection_by_design_and_by_default_v2.0_en.pdf).
Esta revisión no acredita toda obligación sectorial española ni cumplimiento global;
la ausencia de una tecnología prescrita en esos artículos no vuelve opcional su finalidad.

## Inventario y decisión de auditoría

| Control | Beneficio probado/objetivo | Evidencia de coste o exceso | Decisión |
| --- | --- | --- | --- |
| Autorización fresca, ámbito, sesión/MFA y expiración | negativas de otra persona, revocación y prueba caducada | no atribución aislada de coste; checks antes/después de esperas tienen momentos diferentes | conservar la garantía; no eliminar por similitud textual |
| Separación de roles, restricciones/guards append-only | impide al runtime reescribir evidencia y mover ámbito de acción | complementa hashes, no duplicado equivalente | conservar |
| Cadena completa y hashes frescos repetidos | detecta cambios de filas/enlaces con head intacto | trabajo crece con toda la historia; llamada forzada sin ticket y captura genérica de los mismos resultados | candidata a simplificar sólo con dependencia/invalidación completa; head solo rechazado |
| Replay genérico sobre filas que ya contienen hashes | detecta cambios en resultados consumidos y su orden | hash de fila sobre hashes previos, agregado y replay posterior | beneficio incremental/coste sin aislar; no quitar capa por llamarla duplicada |
| Verificar todos los objetos/imágenes al entregar una parte | bloquea entrega si falla cualquier artefacto del conjunto aprobado | bucles sobre todas las partes e imágenes y lectura adicional de originales | revisar semántica: íntegro conjunto versus íntegra parte/snapshot; no equivalencia automática |
| Abrir cada página para aprobar cobertura | prueba qué contenido sirvió el sistema a qué actor/version | el gate exige todas las páginas, incluso conjuntos vacíos; no prueba comprensión humana | reconsiderar workflow; completitud automática + revisión independiente de excepciones requeriría cambiar contrato |
| Auditoría/acciones por helper interno | procedencia e intención antes del descifrado | varias etapas internas dentro de una exportación atómica | posible consolidación manteniendo intención y referencias; no eliminar accesos independientes |
| Hash del texto claro dentro de EOF ya autenticado por AEAD | compromiso final v1 de todos los bytes | superposición criptográfica plausible; no prueba formal de dispensabilidad | investigar formato versionado con prueba criptográfica; no modificar v1 ni confundir con hashes externos/contexto |
| Rotación rewrap con decrypt a sink temporal descartado | autenticar antes de reenvolver DEK | API verify ya autentica sin texto claro ni salida; sink de decrypt se escribe y se vuelve a leer | simplificación aplicada y verificada; mantenimiento, no cuello HTTP demostrado |
| Hash de todo apps/config y todas settings para seal | invalidación conservadora fail-closed | cambios ajenos pueden invalidar; código hash una vez por proceso, settings live | conservar hasta inventario pertinente completo; frecuencia/coste no medidos |
| Celery/idempotencia/recuperación/proxy privado | evita duplicados y trabajo pesado en request, mantiene entrega revocable | arquitectura operativa con pruebas pertinentes | útil; no mecanismo impuesto literalmente por ley |

## Evidencia reproducible en código

- Cadena: apps/safety/evidence_chain.py:260–294 y322–331; require_runtime_chain
  fuerza validación sin ticket; apps/safety/rights_portability_review.py:238–240 lo
  llama desde aprobación. Guards/privilegios: evidence_chain.py:22–77 y
  evidence_chain_sql_v1.py:40–73. Hash no keyed y excepción owner significan que
  la cadena no acredita resistencia a un DBA malicioso que reescriba coherentemente
  fuentes/enlaces/head. Prueba consistencia dentro de la frontera actual.
- Registro/replay: rights_validation_seal.py:160–190 y258–270. La captura de SELECT
  recibe digests de cadena y añade su propio hash de fila/orden. No se infiere
  redundancia eliminable sin inventariar exactamente lo que cubre cada capa.
- Contraejemplo al shortcut de head: tests/test_rights_enforced_validation_seal.py:
  137–157 cambia page_digest vía admin con el head intacto y exige rechazo desde
  LOGIN real. tests/test_rights_evidence_chain_pipeline.py:132–192 demuestra cambios
  comprometidos entre snapshots. Sólo lock del head + role confiable no cubre esos
  cambios físicos de fuentes. Reutilización exigiría otro mecanismo acreditado.
- Externo: rights_portability_export.py:295–327 llama verify_export_objects y
  vuelve a leer todas las imágenes originales aun con sello válido;
  rights_object_content.py:148–178 recorre RightsExportImage y RightsExportPart.
  tests/test_rights_portability_image_storage.py:248–262 modifica sólo bytes,
  sin cambios DB, y exige rechazar imagen/parte/generación. SQL/head no sustituye
  esa garantía. Una copia inmutable versionada/snapshot podría cambiar el diseño,
  pero el almacenamiento mutable actual no acredita esa equivalencia.
- Páginas: rights_portability_coverage_read_gate.py:12–26 y41–68; mapa completo y
  actor/proof/version/session exactos. Revisión independiente es útil; ligar su
  resultado a un manifiesto completo y revisar excepciones podría ser más simple,
  pero no equivale hoy al gate de todas las lecturas originales.
- Replay de aprobación/selección/recompilación: rights_portability_coverage_use.py:
  108–135. one_export_validation en rights_portability_export.py:248–290 ya evita
  duplicación histórica en una operación delimitada; no autoriza reutilización
  entre transacciones ni omitir controles mutables de otros caminos.
- Codec: object_storage/codec.py:144–173 y177–208 liga AEAD a contexto, índice,
  clase/tamaño de frame y final autenticado; SHA plaintext aparece dentro de EOF.
  Sólo formalizar un formato nuevo podría evaluar si elimina una garantía redundante;
  no eliminar hashes de referencia/ciphertext o contexto que cumplen otro propósito.
- Rotación: codec.py:231–246 autentica copiando ciphertext, decrypt(copy,sink),
  y descartando plaintext. verify(copy,...) en224–228 usa la misma máquina de
  autenticación sin tempfile plaintext. Mantener copia cifrada evita reread de
  un origen cambiante. repository.py:199–202 llama esta rotación; no es beneficio
  de request HTTP medido. Tests relevantes: test_rights_object_verify_only.py:60–106
  y test_rights_object_codec.py. Tras la auditoría se aplicó verify en rewrap y se
  ejecutaron 97 pruebas unitarias: PASS. Se añadieron seis rechazos sin salida
  (corrupción, truncamiento, bytes extra, contexto, clave y techo) y una prueba
  de que el almacenamiento temporal sólo recibe ciphertext. No se cambió el formato.

## Propuesta concreta por orden de riesgo

1. Mantener el núcleo demostrado de acceso/integridad/idempotencia/frescura y cerrar
   la métrica actual. No atribuir al código cambios energéticos del portátil.
2. Simplificación de mantenimiento aplicada y verificada: rewrap usa verify sobre la
   copia cifrada antes de cambiar envoltura, sin sink claro. Sin promesa de p95.
3. Inventariar fronteras de validación repetidas: qué protege cada llamada y si sus
   entradas realmente pueden cambiar entre ellas. Preferir adaptar mecanismos ya
   existentes frente a crear caches paralelas; no guardar autoridad ni saltar
   detección de mutaciones con head intacto.
4. Decisión de producto para mayor impacto potencial: semántica de copia fechada/
   manifiesto y verificación por artefacto, versus validez fresca de todo el conjunto
   en cada descarga. Si se elige cambiar garantía, actualizar contrato y negativas
   pertinentes con justificación, no borrar tests para hacer pasar un atajo.
5. Separar aprobación independiente de clics exhaustivos: automatizar completitud,
   conservar revisión de ámbito/excepciones y evidencia del manifiesto exacto.
   Requiere revisar el criterio técnico aprobado, no asumir obligación legal.
6. Sólo si coste y prueba formal justifican: formato codec v2 sin SHA plaintext
   redundante, conservando autenticación/contexto/orden/EOF y lectores v1. Riesgo
   criptográfico mayor; revisión independiente y pruebas negativas antes de adoptar.

No se ha eliminado ningún control ni modificado el contrato durante esta revisión.
No se afirma ROI numérico por mecanismo ni aceptación global/N3. Alcance principal:
los caminos MOD08 de revisión/exportación/entrega que motivan la latencia; no es una
certificación de todos los módulos del proyecto ni de textos/proveedores reales.
