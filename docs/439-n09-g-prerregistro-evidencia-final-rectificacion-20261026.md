# N09G — prerregistro de evidencia final tras esperas PostgreSQL

Estado: instrumento candidato, sin ejecución runtime ni fallo nuevo confirmado. Base master `28a02db`, [N09F/438](438-n09-f-autoridad-rectificacion-verificada-20261026.md) entregado y sus75PASS conservados sin repetir. N09 completo139IDs abierto,8/13bloques obligatorios aceptados. Alpha/noindex, pruebas y datos sintéticos, ningún proveedor real.

## Corte y condición de fuente

Grafo438preservado:2.072fuentes/20.129nodos/84.176relaciones/971comunidades,SHA86c36c7257207f79d9f485bdc1a0f209bb689cf8c80894c1a9e934655e02e88a. Todas las huellas contrastadas antes de analizar este hito. Consulta focal inicial de cinco módulos:46nodos/496relaciones incidentes; ampliación a siete módulos:65nodos/612relaciones. Relaciones estáticas, no prueba runtime. Cortes/revisión en artifacts/recorridos-n09-g-20261026; se requiere delta AST del instrumento y semántica439/17 antes de congelar.

rectification_final.context comprueba explícitamente User y permisos actuales antes de los bloqueos posteriores; no se lo clasifica como simple comprobación inicial sobre una caché. evidence bloquea RecipientReview y procesa contenidos privados antes del actor final de prepare. draft_context bloquea RightsAction y descifra antes de volver a comprobar al llamador. close bloquea la revisión aprobada y descifra su motivo antes del siguiente context. La fuente de cuenta y contacts.claim añaden esperas internas diferentes. Son condiciones de fuente por verificar, no defectos confirmados por semejanza con F/E.

Hay además una prueba de identidad/ámbito obtenida por context antes de la espera de RecipientReview; prepare no la reconsulta después de evidence. Se incluye una condición acotada de caducidad durante esa espera. Los cambios de prueba legítimos usan locks canónicos: no se simulará una escritura concurrente de expiry saltándose ese protocolo.

## Trece casos propuestos, cuatro operaciones y seis fronteras

| Familia | Servicio nativo | Fila que se sostiene | Observador privado seleccionado |
| --- | --- | --- | --- |
| prepare_review | final.prepare | RecipientReview aceptada | checked_body, exactamente proposal.encrypted_changes |
| inspect_draft | final.inspect | RightsAction del borrador | checked_body, exactamente draft.encrypted_reason |
| review_draft | final.review | RightsAction del borrador | checked_body del mismo borrador |
| close_review | final.close | RightsAction de revisión final aprobada | checked_body, exactamente review.encrypted_reason |
| prepare_account_source | final.prepare, perfil con cambio first_name | User del sujeto | Retorno satisfactorio de account.source |
| prepare_contact_claim | final.prepare, contactos corregidos | PhoneClaim vigente corregida | checked_body, exactamente inventory.encrypted_inventory después de claim |

Seis controles y seis retiradas de safety.respond_rights_request durante la espera. Los llamadores parten de permisos completos review_rights_request/execute_rights_request/review_rectification/respond_rights_request, MFA/epochs vigentes, scope y lecturas legítimos; autor/revisor independientes. Los permisos adicionales de asignación/verificación/revisión de destinatarios se conceden sólo para preparar la saga nativa, no se convierten en requisitos nuevos de la respuesta final.

Decimotercer caso: prepare_review con prueba legítima configurada **antes del snapshot y admisión** con TTL sintético de diez segundos. Tras observar la espera PostgreSQL, exigir que aún esté vigente, mantener el bloqueo hasta que el reloj real alcance su deadline (espera acotada de12s), comprobar expiry/filas/permisos intactos y liberar. No cambiar reloj, estado de prueba ni permisos durante el intervalo. El tiempo pasa realmente, pero el TTL corto es una precondición de fixture: no acredita proveedor de identidad. La denegación esperada es ValidationError, sin descifrado posterior ni efectos. Comparte el control prepare_review válido, sin duplicarlo.

Selección propuesta: archivo completo tests/test_rectification_final_authority_wait.py; matriz explícita de doce pares familia/control-revocación y un par prepare_review/proof_expiry. Son trece escenarios, no trece bugs/operaciones/IDs aceptados. Las cuatro operaciones y variantes corresponden a una ruta del censo, R_rectification_final. Todos los diagnósticos son de servicio nativo: no acreditan HTTP, middleware, navegador ni divulgación de respuesta.

## Preparación y oráculos

Saga nativa: propuesta/ejecución recibida y prueba nueva, inventario/lectura/evaluación de destinatarios, reasignación y aceptación independiente, nueva prueba y lecturas, borrador/inspección/revisión final según el escenario. Reutiliza helpers inmutables de F para alias y prepara cuenta/contactos mediante independent_case y servicios originales. Ninguna fila cifrada de dominio se fabrica para saltar precondiciones. En las variantes de cuenta el expediente es de perfil (account_subject_idNULL), sujeto distinto del operador; no se lo presenta como cuenta sin perfil.

Guard explícito de archivo, serial, PostgreSQL de pruebas propio, noPRODUCTION/RECOVERY_MODE/xdist. Dos conexiones propias; PID efectivo, pg_stat_activity.wait_event_type=Lock y holder dentro de pg_blocking_pids antes de retirar permiso o vencer la prueba. Cambio de permiso confirmado al liberar; para expiry se conserva toda la tabla de permisos en los snapshots. Espera de observación15s, statement_timeout35s, future45s y cancelación acotada. Hilos/conexiones/lock y metadatos de finally incluso ante fallo.

Los wrappers reenvían los callables originales sin sustituir guardas/ORM/cifrado/proof/reloj. Sólo comparan ciphertext objetivo en memoria y registran contadores/booleans/hashes, nunca valores privados. Para account.source una entrada anterior al wait puede ser legítima: se exigen cero retornos privados satisfactorios después de revocar, sin exigir cero entradas. Que el callback seaNone se observa como metadato, no se impone como requisito a una futura corrección correcta. Cuenta/contacto deben esperar dentro del helper declarado, con evidencia del primer FORUPDATE coincidente, no por una etiqueta asumida.

Controles: resultado semántico correcto y sólo RightsAction nueva en prepare/inspect/review; close además RightsResponse/RightsNotice/RightsRequest, versiones+1/resolved/unverified y perfil/anuncio íntegros. Snapshots completos escalares de core/listings/mediafiles/safety y tablas intermedias, hashes/recuento de archivos. Negativos: PermissionDenied o ValidationError según condición, cero procesamiento privado posterior al evento y todos los snapshots intactos (en permiso se excluye sólo su concesión retirada). La caducidad no modifica datos durante la espera ni necesita máscaras de snapshot.

Cada control debe ser válido antes de atribuir el negativo al producto. Ausencia de espera, proof inválida antes de admisión, target incorrecto o error de fixture se clasifican como diagnóstico inválido. Una denegación final con rollback y procesamiento privado anterior no se reclasifica como segura por acabar denegada. Los contadores cubren la frontera privada seleccionada, no toda materialización interna/filas ORM; no promesa de serialización universal posterior.

## Revisión y ejecución pendientes

Escritor nativo aislado `/root/n09g_final_diagnostics`, worktree `/tmp/web-modelos-n09g-final-20261026`, base28a02db; sólo el test nuevo y su informe ignorado, sin runtime/aplicación/root/docs/grafo/Git. Root revisó el archivo completo, dependencias idénticas y contrato JSON. Antes de congelar se corrigieron notas de informe a string, un acoplamiento del oráculo a callbackNone y controles positivos exactos. Root corrigió únicamente imports tras RuffI001; el AST ajeno a imports se conserva respecto a la entrega, y el primer negativo de lint queda preservado con su recibo. No se acepta complete del escritor como QA.

Antes del diagnóstico: Ruff corregido, revisión propia, delta AST/semántica43917/manifiesto y congelación. Runner oficial focused, workers1, timeout1800, parser nativo `/tmp/web-modelos-librdb-v2.4.0`, PostgreSQL/Redis propios y notificaciones/cleanup verificados. Conservar original siFAIL y auditar cada condición/control antes de cambiar aplicación. Los tiempos serán cuerpo de caso con preparación/espera/snapshots/limpieza, no latencia normal ni mejora causal.

No se repiten F75/E38 ni baterías válidas por esta preparación. Servicios de evaluación/revisión de destinatarios se usan como fixtures, sin aceptar por ello sus fronteras propias. Otras ramas tardías, purgas/outbox/jobs y conciliación139IDs retienen su disposición. N02restante al final/N10N11N15pendientes/N12–N14condicionados; objetivo completo activo.
