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


## Investigación posterior de candidatas, SHA b5de3bc

Revisión directa de fuentes y negativas existentes después de terminar los runners.
No nuevas medidas HTTP, perfiladores, servicios ni cambios de contrato en esta fase.
Las pruebas citadas aquí se inspeccionaron: no se afirma una nueva ejecución de
integración. La simplificación de rotación conserva su gate unitario anterior.

### Frontera principal: POST y GET de una descarga

La ruta concreta es rights_exports.download → validate_portability →
_sealed_or_full → holds/replay → verify_export_objects + _verify_current_images.
Después se descifra la parte solicitada y stage_delivery conserva sus bytes.
El GET de Caddy vuelve a authorize_token → _fresh → validate_portability; por
último verifica tamaño/SHA del archivo staged y consume el grant de un solo uso.
Referencias: rights_exports.py:817–975; rights_object_delivery.py:141–146,
242–297; rights_portability_export.py:294–327.

La operación medida con redirect atraviesa DOS transacciones: el ContextVar de
one_export_validation se reinicia en cada operación y no evita la segunda
validación. En la ruta de sello válido ambas fases verifican todas las imágenes
exportadas, todas las partes externas y todos los originales declarados; el POST
además descifra el objeto seleccionado para entregar. La descarga JSON también
paga las comprobaciones del conjunto binario. Esto es amplificación estructural
confirmada, no una atribución temporal ni prueba de que eliminarla sea equivalente.
Si el sello no vale, la ruta completa reconstruye proyección/paquetes/transporte.

El GET comprueba hechos que pueden cambiar tras el POST. Las negativas vigentes
cubren recibo/sujeto/expiración/payload/namespace/grant/archivo/restauración:
test_rights_object_delivery.py:77–104. El sello válido también debe rechazar
corrupción exclusivamente externa: test_rights_enforced_validation_seal.py:161–179.
El archivo staged íntegro NO demuestra que originales u otros objetos permanezcan
íntegros. Un token con duración corta NO demuestra ausencia de revocación.

### Alternativas y decisión

| Alternativa | Trabajo que evita | Garantía que conserva o cambia | Decisión |
| --- | --- | --- | --- |
| Reutilizar sólo el head de la cadena o un TTL | hashes frescos de fuentes/historia | pierde detección de fuente alterada con head intacto | rechazada como sustitución equivalente |
| Cambiar a REPEATABLE READ para reutilizar resultados | snapshots posteriores | deja de observar commits posteriores al snapshot; no protege bytes externos | no adoptar como arreglo transparente |
| GET verifica grant, autoridad fresca y archivo staged, sin comprobar todo el origen otra vez | replay histórico y lecturas del conjunto en GET | entrega snapshot validado en POST; ya no exige integridad fresca del origen completo en GET | candidata principal de simplificación arquitectónica; requiere decisión contractual explícita |
| Validar sólo artefacto pedido y sus dependencias | lecturas de imágenes/partes ajenas en ambas fases | daño ajeno puede no impedir entrega; cambia integridad conjunta por integridad del artefacto | candidata, no equivalente al contrato actual |
| Fusionar verificación y lectura de la parte seleccionada en POST | segunda lectura/descifrado de esa parte | precisa conservar orden de errores, tombstones antes/después y cuándo se capturan bytes | investigar como alternativa acotada; ahorro global desconocido |
| Omitir SHA plaintext del codec v1 | pasada SHA de cada frame | modifica construcción criptográfica/formato; redundancia no demostrada | no retirar v1; prioridad inferior al alcance de validación |
| Completar cobertura por manifiesto + revisión de excepciones | clics/lecturas/auditoría acumulada | cambia evidencia humana de páginas servidas por evidencia automática de completitud | mejora de proceso potencial; necesita criterio de revisión aprobado |

La opción de snapshot NO elimina revocación: el GET seguiría verificando recibo,
ámbito/sujeto, prueba/expiraciones, purga, generación de recuperación, grant,
binding, tamaño/digest staged y consumo exclusivo. Habría que enumerar además
exactamente qué hechos SQL invalidan la aprobación y cómo detectarlos. No basta
con quitar _fresh ni confiar en la firma del token. La diferencia explícita es
que alteración de originales/artefactos ajenos posterior al POST no invalidaría
por sí sola los bytes staged aprobados. Su aceptabilidad aún no está decidida.

### Qué prueba falta antes de implementar

1. Enumerar inputs mutables por aprobación y frontera POST/GET; separar autoridad,
   integridad del artefacto y vigencia del conjunto. Escribir criterio exacto de
   éxito/rechazo para cada mutación, incluidas fuentes SQL con head intacto.
2. Para una candidata de garantía equivalente, conservar todas las negativas;
   agregar corrupción de objeto no seleccionado, purga entre fases y cambio
   de original entre POST/GET. Usar PostgreSQL real, LOGIN no propietario,
   RustFS/Caddy propios y datos sintéticos. No usar mocks como aceptación.
3. Para snapshot o comprobación por artefacto, revisar primero el contrato y
   justificar el nuevo resultado protector. No borrar negativas para ocultar la
   diferencia. Comparar cantidad de lecturas y bytes en diagnose separado;
   las muestras antiguas no atribuyen segundos a cada capa.
4. Sólo después de gates funcionales, ejecutar preflight/probe/measure limpio,
   con límites y tabla por caso; repetir únicamente si pasa. El diagnóstico no
   acredita p95. No se ha lanzado un ensayo especulativo en esta investigación.

### Fuentes técnicas primarias y límites

PostgreSQL documenta snapshots por sentencia en READ COMMITTED y snapshot estable
con REPEATABLE READ: la estabilidad cambia qué commits se ven, no equivale a
comprobar frescura posterior ni cubre el almacenamiento externo.
[PostgreSQL 17: Transaction Isolation](https://www.postgresql.org/docs/17/transaction-iso.html).

S3 ofrece lecturas condicionales por ETag/fecha y Object Lock por versión; son
mecanismos del proveedor, no prueba de autenticación AEAD ni del contenido de
un original separado. La compatibilidad de RustFS, ETag/checksums y límites de
bypass/retención tendría que probarse localmente. No se ha desplegado Object Lock
ni se recomienda usarlo para sustituir borrado/purga: retención puede impedirlos.
[Lecturas condicionales S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-reads.html),
[Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html).

Conclusión de investigación: priorizar la semántica de entrega y la amplitud de
validación antes de otra aceleración del intérprete. Está demostrado qué trabajo
se repite; no está medido cuánto del p95 eliminaría cada alternativa. El contrato
vigente sigue siendo el criterio de aceptación y permanece incumplido en tiempos.


Investigación de la fusión de lectura seleccionada: contraejemplo de purga/
corrupción posterior descarta reutilización temprana como equivalente. Alternativa
de lectura final streaming evita staging cifrado; 16 contrastes sintéticos pasan,
pero integración y fallos de scratch pendientes; no adoptada. Véase
[detalle y límites](mod08-lectura-fresca-investigacion-20261012.md).
