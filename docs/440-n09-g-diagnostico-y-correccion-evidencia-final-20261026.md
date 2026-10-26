# N09G — diagnóstico y corrección propuesta de evidencia final

Antes de integrar la candidata y validar cambios de aplicación. Base master28a02db; [prerregistro439](439-n09-g-prerregistro-evidencia-final-rectificacion-20261026.md). F75/E38 conservados sin repetir; N09 completo139IDs abierto,8/13bloques obligatorios aceptados, alpha/noindex y datos sintéticos.

## Original confirmado

Run `20261026-120035-1594b022`: **13casos,6PASS/7FAIL,0ERROR/SKIP;282,230sJUnit**.1.775huellas idénticas antes/durante/después, limpieza de contenedores/redes/volúmenes y temporal comprobada; Telegram terminalERROR y auditoríaPASS enviados, recibos verificados. Se conserva el original completo; no se convierten sus fallos enPASS.

Auditoría independiente en artifacts/recorridos-n09-g-20261026/baseline-audit.json: seis controles nativos válidos, todos con espera PostgreSQL/PID/Lock/holder, procesamiento del target y efectos exactos previstos. Los seis retiros de respond se comprobaron con User nuevo y se confirmaron al liberar el bloqueo.

| Escenario negativo | Resultado nativo observado | Target privado después del evento | Caso QA, s |
| --- | --- | --- | ---: |
| prepare_review | PermissionDenied tardío, dominio intacto |1retorno de checked_body/propuesta|17,898|
| inspect_draft | Éxito, material devuelto y nueva Action de lectura |1retorno de checked_body/borrador|17,257|
| review_draft | PermissionDenied tardío, dominio intacto |1retorno de checked_body/borrador|17,332|
| close_review | PermissionDenied tardío, dominio intacto |1retorno de checked_body/revisión aprobada|17,090|
| prepare_account_source | PermissionDenied tardío, dominio intacto |1retorno privado de account.source|17,112|
| prepare_contact_claim | PermissionDenied tardío, dominio intacto |1retorno de checked_body/inventario|18,284|
| prepare_review/proof_expiry | Éxito y borrador creado con prueba caducada |1retorno de checked_body/propuesta|27,172|

En la caducidad, TTL corto de10s configurado antes del snapshot/admisión; la prueba seguía vigente al confirmar la espera, después venció por reloj real mientras el holder mantuvo la fila. Todos sus campos y concesiones de permisos permanecieron idénticos durante el intervalo, con los siete permisos de preparación conservados. No se modificó reloj ni datos durante la espera. El incremento tras liberar fue una Action de borrador, no una mutación artificial ocultada por el snapshot.

Los tiempos son cuerpo de caso con preparación nativa, espera inducida, snapshots y limpieza, no latencia normal ni mejora de rendimiento. Todos los casos son servicios nativos: no hay nueva evidencia HTTP ni de proveedor/worker. Contadores de frontera seleccionada, no inventario exhaustivo de toda materialización interna. Hay siete condiciones negativas reproducidas en cuatro operaciones/seis fronteras de una ruta; no siete causas raíz, operaciones o bloques nuevos.

## Candidata acotada antes de validación

Sólo rectification_final.py. Capturar identidad/epochs originales y cuatro permisos del llamador al entrar en prepare/inspect/review/close, usando capture_authority existente de F. Guardar permisos, cuenta activa/MFA/scope y asignación cuando corresponda después de los bloqueos y antes de privados/efectos. No sustituir el llamador por el autor del borrador ni adoptar nuevos epochs después de esperar.

Callback explícito de operación activa: autoridad original, asignación aplicable, versiones de expediente/respuesta y prueba vigente vinculada al PK original. Reconsultar authorized_proof después de esperar, incluyendo su caducidad. Propagar por evidence/draft_context y APIs existentes execution_scope_matches/snapshot/account.source; comprobar después de RecipientReview/Draft/Review y después de contacts.claim antes del inventario privado. La fuente de cuenta comprueba después de User antes de devolver su proyección. No editar esos helpers de F ni añadir lock de operador.

Preservar revisión independiente, latest/digests, proof/bindings/versiones, auditorías, TTL del borrador, motivos y pending. Cierre nuevo comprueba antes de descifrar aprobación y mantiene callbacks hasta antes de su transición final. **Replay de cierre resuelto conserva autoridad actual e integridad/epochs históricos, sin exigir una nueva prueba activa sobre un caso resolved/unverified.** Tampoco ejecutar un callback de prueba activa después de resolver y revertir un cierre legítimo.

Root revisará el diff de una sola fuente y sus callers antes de integrar. actor() usado por GET de la vista y las firmas públicas permanecen intactos. Los parámetros de autoridad de helpers internos se ajustan en todos sus callers conocidos; la búsqueda de consumidores no encontró llamadas externas de context/evidence/record/draft_context. No cambian vistas/templates/URL, modelos, migraciones, settings, servicios o proveedor. El complete del escritor aislado no acredita corrección runtime.

## Selección de validación propuesta:18casos

1. Los13diagnósticos originales íntegros, incluidos seis controles y siete negativos. Se exigen PermissionDenied o ValidationError según condición, cero procesamiento del target después del evento, snapshots y archivos intactos, esperas/clock/roles/PIDs/cleanup demostrados.
2. test_account_final_rectification_review_and_atomic_close, pendingTrue/False:2casos originales, incluidos caminos legítimos, rechazo por pendientes, replay y bindings propios.
3. test_account_final_rectification_concurrent_close:1caso original, dos cierres serializados y respuesta única; replay resuelto no debe pedir prueba activa nueva.
4. test_rectification_recipient_review_and_close_requirements:2casos originales ES/EN de contrato de formulario/localización, sin atribuirles concurrencia o navegador.

Total13+2+1+2=18previstos; conteo definitivo por runner, no una colección ya ejecutada. No repetir F75/E38 ni recorridos móviles completos sin una dependencia modificada que lo justifique. Los originales de cuenta y los controles de perfil cubren superficies distintas, sin afirmar equivalencia universal de ramas.

Antes de ejecutar: Ruff de candidata/instrumento, revisión propia, delta AST de la fuente y semántica440/17, manifiesto y congelación. Runner focused serial, parser nativo, PostgreSQL/Redis propios, timeout1800. Auditar los18casos, fuentes, negativos/controles, replay y limpieza/Telegram antes de aceptar. Una mejora temporal no es requisito de esta corrección de seguridad y vigencia; los tiempos anteriores/posteriores se documentarán separados de la latencia de app.

Evaluación/revisión de destinatarios usadas como fixture mantienen sus fronteras propias pendientes. Otros consumidores/ramas no observadas, purgas/outbox/jobs y conciliación139IDs siguen pendientes. N02restante al final/N10N11N15pendientes/N12–N14condicionados; objetivo completo activo.
