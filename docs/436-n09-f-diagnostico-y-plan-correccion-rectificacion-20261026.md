# N09F — diagnóstico confirmado y plan de corrección de rectificación

[Prerregistro435](435-n09-f-preparacion-rectificacion-autoridad-20261026.md), base `6d4c288`, sin cambios de aplicación durante el diagnóstico. N09 abierto139IDs, ocho de trece bloques obligatorios aceptados; alpha/noindex y datos sintéticos.

## Resultado original preservado

Run `20261026-095759-1cba6827`: **20 casos, 10 PASS y 10 FAIL**, cero errores u omisiones, **236,664s JUnit**. El runner termina ERROR porque existen fallos de prueba; no hubo error de preparación en estos veinte casos. Las 1.772 huellas congeladas coinciden antes, durante y después. PostgreSQL/Redis propios y parser nativo, sin proveedor real. Recursos Docker y temporal del runner eliminados; Telegram terminal confirmado con delivery=sent.

Auditoría independiente: `artifacts/recorridos-n09-f-20261026/baseline-audit.json`. Los diez controles son válidos y producen sus efectos nativos esperados. En cada negativo se observó realmente el PID del trabajador esperando Lock y el holder dentro de pg_blocking_pids antes de retirar permiso, comprobar la pérdida con User nuevo, confirmar la transacción y liberar el lock. Los diez negativos terminaron con éxito nativo a pesar de la revocación. No se han debilitado oráculos ni reinterpretado fallos de fixtures como producto.

| Operación | Efecto observado después de revocar | Tiempo del caso revocado, s | Corrección verificada |
| --- | --- | --- | --- |
| preview | Retorno privado y nueva auditoría SourceRead | 7,713 | Pendiente |
| propose | Action, Proposal y cambio del expediente | 8,128 | Pendiente |
| source_photo | GET200 y 9.558 bytes privados sintéticos entregados | 8,085 | Pendiente |
| upload | Nueva Revision/Photo, Action, Upload y callback eager | 9,513 | Pendiente |
| discard | discarded_at modificado y nueva Action | 9,253 | Pendiente |
| inspect | Retorno privado y nueva ProposalRead | 8,145 | Pendiente |
| review | Nueva Review/Action y cambio del expediente | 9,478 | Pendiente |
| notify | Notification, Response, Notice, Action y versiones | 9,078 | Pendiente |
| execute | Corrección de perfil/anuncio, Execution, respuesta y callback eager | 10,585 | Pendiente |
| recipients | Nuevo inventario cifrado y Action | 11,065 | Pendiente |

Los tiempos son duración del cuerpo del caso, incluyendo preparación, espera inducida, snapshots y limpieza; no latencia normal de app. JUnit incluye además setup/teardown. No hay todavía tiempos de candidata ni mejora de rendimiento. Todos los agregados físicos de archivos permanecieron idénticos: el instrumento reutiliza un Blob listo. Esto no elimina el efecto de nuevas referencias o callbacks después de revocar. Delay observado reenvía al procesamiento eager original; no se atribuye ejecución de worker ni entrega externa.

Sólo source_photo ejercita HTTP y demuestra bytes entregados después de la revocación en este entorno sintético. Las otras nueve entradas son servicios nativos: prueban efectos o procesamiento privado, sin atribuirles transporte HTTP. Los contadores de retorno de helpers no demuestran ausencia exhaustiva de toda materialización interna. Se preservan los límites de primer bloqueo de upload/discard dentro de source_snapshot; no acreditan sus últimos bloqueos explícitos.

## Corrección autorizada dentro del bloque

Revalidar User activo, MFA, epochs originales, permisos y ámbito vigente después de esperas, antes de replay, procesamiento privado y efectos. Capturar los epochs del operador al entrar; no adoptar una versión nueva después del bloqueo ni bloquear su fila User. Mantener todos los checks actuales de proof, asignación, versiones, independencia, motivo, auditoría e idempotencia.

Permisos base: review_rights_request y execute_rights_request. Revisión independiente e inventario añaden review_rectification. Notify/execute añaden además respond_rights_request. La captura de fuente debe recibir explícitamente la autoridad completa del llamador; una comprobación base no sustituye sus permisos adicionales.

Propagar un callback de autoridad por source_snapshot y la fuente de cuenta, comprobando después de los bloqueos internos y antes de proyecciones privadas. Para metadatos de filas bloqueadas, considerar una fase ordenada de bloqueo sólo de identificadores, comprobar autoridad y materializar después las filas ya bloqueadas. Preservar User→Revision→Uploads→Blob→Rate/Photo, el contenido/orden del snapshot y su digest. Una comprobación sólo al retornar source_snapshot sería tardía para el requisito declarado.

Revisar también las fronteras explícitas Proposal/Review/Notification/Upload/Blob y el replay de cada servicio. Si se extiende el callback a account.apply, comprobar tras la espera de EmailConfirmation antes de escribir; esa protección de fuente no convierte el diagnóstico de alias en cobertura runtime de la rama de email.

Escritor nativo en `/tmp/web-modelos-n09f-rectification-20261026`, propiedad exclusiva de seis módulos de rectificación existentes, un posible helper rectification_authority.py e informe ignorado. Los veinte diagnósticos originales quedan intactos. Sin permisos para ejecutar pruebas, editar root/docs/grafo, dependencias, migraciones, servicios o commits. Root revisará diferencias, propagación de roles, orden de bloqueos y callers antes de integrar. Después fijará selección de validación, delta AST/semántica y congelación previos al runner.

## Pendientes sin aceptación anticipada

Hay diez operaciones con defecto reproducido, **todavía no diez correcciones aceptadas**. Se conservan las dieciséis correcciones locales A–E y los38PASS de N09E; no son dieciséis bloques del contrato ni se repiten ahora. N09 completo no se cierra con este lote.

Cuenta sin perfil, cambios de email, replays, catálogos/contactos/ubicación/tarifas, cargas expiradas, inserción concurrente de Blob, revocación de sesión/MFA y rectification_final.evidence requieren disposición propia. Las ramas que se protejan por código conservan sus límites de cobertura hasta validarlas. Purgas/outbox/jobs finitos y la conciliación de139IDs siguen pendientes. N02restante al final; N10/N11/N15pendientes, N12–N14condicionados. El objetivo completo permanece activo.
