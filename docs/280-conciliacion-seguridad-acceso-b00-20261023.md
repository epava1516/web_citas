# B00-321 — Seguridad, acceso y autorización posterior a bloqueos

Fecha: 2026-10-23. Conciliación documental y corrección funcional acotada; sin aceptación global de beta.

B00-321: 249 de 295 fuentes únicas conciliadas; quedan 46 de arquitectura. Se incorporan seguridad y derechos históricos 3–4. Corregida la aceptación de una carga privada con autorización caducada tras bloquear recursos: reproducción con un fallo y regresión PostgreSQL de 15 pruebas aprobadas. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura y procedencia

Seis lectores nativos de sólo lectura cubrieron619.164caracteres en seis partes contiguas, mediante56salidas literales de hasta12.000caracteres, sin truncamientos declarados ni reparaciones de lectura. Hubo tres reparaciones de formato del informe: STATUS y el tipo de IMPLEMENTATION_NOTES, sin nuevas lecturas. Son seis lectores y tres seguimientos de serialización; no nuevas invocaciones ClaudeV1. No se estiman tokens nativos y se conserva su consumo histórico.

| Fuente | Caracteres | Particiones contiguas |
| --- | ---: | --- |
| `source:72q3i4ho4b4009aqfmv6`, seguridad3/7 | 309784 | [0,103261), [103261,206522), [206522,309784) |
| `source:c7sgs1jvwzcke3zbj6k5`, seguridad4/7 | 309380 | [0,103126), [103126,206253), [206253,309380) |

Hashes completos respectivos: `a92ab198e6e1b1ee59a21f3ba6a7035888fdeb3d7b778ec5bb8f508e4f9e10f0` y `662b37f16a1febc3a2a897dc8f85e995b01648a7b679fec81c5418647b3364a3`. El principal inspeccionó las fronteras y doce citas con contexto; el verificador efectuó catorce cotejos sobre esos doce intervalos, comprobó uniones y volvió a validar las295capturas. Las partes no se cuentan como fuentes distintas.

Plan, protocolo, propuestas, extractos, contextos, contrastes y auditorías están en `artifacts/beta-promotion-fix-20261020/b00-321-*`. Los informes persistidos son extractos seleccionados y marcados, no transcripciones íntegras de las respuestas. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de247a249disposiciones con reemplazo atómico y permisos conservados; sólo admite la base247 fijada o el resultado idéntico. Su integración requiere además la auditoría positiva de la corrección.

## Interpretación de las capturas

Snapshot11/10/2026/base7e04016, anterior al contrato romántico y con formato alterado. No son bytes canónicos ejecutables ni instrucciones vigentes. No reciben lectura los archivos únicamente importados o referidos. Las fronteras entre partes atraviesan funciones y formularios; la unión cubre cada captura, no el módulo completo.

La captura3 comienza en photo_reintroduction_review y termina en rectification_rates.display. Incluye revisión independiente de candidatos de imágenes, medidas de privacidad y finalidades, calendarios, excepciones y levantamientos, destinatarios, recuperación y rectificación. Una fecha de seguimiento operativa no levanta una restricción, acredita conservación jurídica ni permite republicar. Las candidaturas visuales y los roles históricos no prueban identidad, consentimiento o comunicación efectiva.

La captura4 comienza en rectification_recipients y termina en rights_access_supplement. Incluye carga privada de sustituciones, historia Redis, censos de recursos retenidos, calendarios, acceso, contabilidad de cobertura, decisiones escalares, borradores, revisión y cierre. El conteo de comandos o la reconstrucción de un snapshot RDB no es una copia completa del historial de una persona. Validar hashes y ámbito del censo no acredita la verdad de la declaración del operador. Una decisión sobre un campo y una contabilidad aprobada tampoco acreditan entrega completa. Los ámbitos bloqueados o pendientes deben conservarse; la aceptación local no acredita proveedor externo o producción.

## Contraste actual seleccionado

Se fijaron hashes y24comprobaciones literales en11archivos actuales. Esta selección no es una auditoría global de autoridad, concurrencia o borrado y no recibe crédito de ejecución funcional por sí sola.

| Materia | Alcance observado |
| --- | --- |
| Fotos y tratamiento | photo_reintroduction_review relee la ejecución después de los bloqueos y separa decisión visual de autorización. processing_final conserva data_deleted=false e identidad simulada; no convierte una restricción en supresión. |
| Evidencia comercial y destinatarios | promotion_order_inventory exige un sujeto exacto y trata pedidos como evidencia dependiente. recipient_candidates conserva roles como candidatos, sin inferir divulgación. |
| Recuperación | recovery_ownership rechaza recursos de otro ámbito y rutas compartidas. recovery_media exige recibos independientes, comprueba ausencia física y sólo registra reintentos OSError. La transacción de base de datos no puede restaurar bytes ya borrados; esta inspección no ejecuta una recuperación nueva ni prueba todos los fallos de storage. |
| Contrato romántico | Los validadores privados de rectificación conservan estructuras históricas. profile_contract y su llamada en submissions siguen rechazando contrato antiguo, servicios y tarifas al validar la publicación romántica. La presencia de esos validadores privados no autoriza a publicar el contenido profesional. |
| Acceso completo | rights_access_close exige paquete revisado, partial=false y pending vacío. El censo físico RDB sigue marcado parcial y con asociación de infraestructura pendiente. No se declara acceso completo desde un inventario o un campo aprobado. |
| Levantamiento de preferencias | purpose_release liga el origen al plan cifrado y a mensajes, exige comprobación vigente y valida original_plan antes de ejecutar. Las diferencias de replay, frescura de permisos y contratos de fallos de storage señaladas por lectores son hipótesis acotadas, no defectos actuales demostrados por esos fragmentos. |

Las hipótesis se conservan en b00-321-reader-hypotheses.json para contraste específico; no se elevan desde texto histórico a fallos confirmados. La hipótesis de vigencia de carga sí se reprodujo y corrigió como se describe a continuación. Seguridad5–7 y el resto del corpus continúan pendientes.

## Defecto de vigencia reproducido y corregido

[rectification_uploads](../apps/safety/rectification_uploads.py) comprobaba la prueba de identidad/ámbito antes de source_snapshot, que toma bloqueos de origen y medios. Si la autorización caducaba durante ese intervalo, podía crear una carga privada con la prueba ya caducada y responder con redirección de éxito. No se ha demostrado publicación ni acceso público desde ese defecto.

La reproducción previa `20261023-230720-abbda4da` falló exactamente por HTTP302 frente409: un fallo, cero errores u omisiones; runner ERROR preservado. PostgreSQL, HTTP, lectura de origen y autorización de dominio fueron reales; sólo se controló el reloj al retornar la lectura bloqueada para modelar el tiempo transcurrido. No se afirma haber esperado24horas ni reproducido una revocación concurrente real.

La corrección repite authorized_proof después del origen y antes de modificar datos tras el último bloqueo de blob o de la carga a descartar. Rechaza un cambio de prueba en ese último punto. No cambia permisos, ámbito, proveedor, caducidades o claves y preserva el código previo del usuario. Los [tests](../tests/test_rectification_uploads.py) cubren caducidad tras origen, tras adquisición del blob y tras bloqueo para descarte. Comprueban rechazo y ausencia de registros/archivos nuevos, o conservación del estado sin descarte, según el caso.

La [auditoría de regresión](evidencias/b00-321-upload-authorization-regression-20261023.json) corresponde a `20261023-231118-5cc92188`:15pruebas aprobadas, cero fallos, errores u omisiones; JUnit114,358s, tres workers y PostgreSQL17/Redis7.4 propios. Selección: test_rectification_uploads.py, test_rectification_photos.py y test_media_snapshot_serializes_blob_mutation de test_rights_rectification.py. Incluye las tres variantes nuevas, flujo privado de fotos, idempotencia y serialización PostgreSQL existente.

Dependencias, Ruff, documentación, Django, migraciones y compilación nativa terminaron con código cero. Las fuentes quedaron congeladas y cotejadas con el prerregistro. El principal confirmó independientemente contenedores y directorio temporal ausentes y aviso Telegram terminal PASS, además del cierre de las unidades de corrección. Un primer refresco AST falló por usar un intérprete sin networkx; se repitió con el intérprete instalado de Graphify y pasó. Ese fallo no se presenta como resultado aprobado.

Todo usa datos sintéticos y verificación de identidad simulada explícita. La regresión no acredita un proveedor real, N3, capacidad ni aceptación global. B07 conserva acta16 y B15 sigue opcional; nueve de18puntos cerrados.

## Continuación y grafo

Quedan46capturas de arquitectura,26.959.806caracteres. El conteo no representa porcentaje de esfuerzo. Se conservan los límites históricos de IVA posterior al166, Código Penal posterior al340quinquies, HTMX, originales judiciales, discordancia de LO10/2022 y corroboración parcial del Reglamento IA.

Grafo370 revalidado al inicio. AST dirigido del test y rectification_uploads y semántica371–372 antes de congelar fuentes. Integración documental mediante semántica dirigida373; sin extracción AST/semántica global ni HTML nuevo exhaustivo. Sin publicación, contratación, gasto o datos reales. Corte anterior: [conciliación279](279-conciliacion-seguridad-derechos-b00-20261023.md).
