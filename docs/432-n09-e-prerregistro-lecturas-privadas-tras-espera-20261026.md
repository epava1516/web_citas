# N09E — prerregistro de lecturas privadas tras esperar filas de evidencia

Antes de modificar la aplicación o ejecutar diagnósticos. Base `a5cd18d`, master, [N09D/431](431-n09-d-reclamaciones-levantamiento-autoridad-verificada-20261026.md) aceptado localmente y publicado,117PASSretenidos. N09 sigue abierto139IDs/8de13bloques obligatorios. Alpha/noindex, datos y pruebas de identidad sintéticos; ningún proveedor real.

## Corte y pregunta acotada

Corte publicado431:2.060fuentes/19.947nodos/84.128relaciones/961comunidades, SHA256 `454879cac694f401ffc265b601db9f1c178d8a5c4dbd531b533e42b9d48df814`. Revalidado contra todas las huellas actuales antes del prerregistro: ninguna fuente del manifiesto cambiada. Consulta focal de tres módulos:26nodos/359relaciones incidentes; referencias estáticas, no ejecución ni vulnerabilidades confirmadas. Se preserva el grafo y se requiere el delta AST del instrumento y semántica432/17 antes de congelar.

Las revisiones de fuente detectan autorización fresca antes de un SELECT FOR UPDATE de evidencia y otra autorización al final, después del descifrado. Denegación terminal y rollback no prueban por sí solos que no se haya descifrado contenido entre ambas comprobaciones. La tercera condición, respuesta final, se añade al contrastar las dependencias del autorizador compartido; no se la atribuye a los dos informes previos ni se declara un tercer fallo runtime.

| Entrada pública de servicio | Fila que se sostendrá | Permiso retirado | Observador pasivo del contenido objetivo |
| --- | --- | --- | --- |
| rights_access_field_decision.inspect_decision |RightsAccessFieldDecision|safety.respond_rights_request|checked_body de ese módulo, sólo encrypted_body de la decisión|
| rights_information_review.record,operation=inspect |RightsCopyInformation|safety.review_copy_information|unseal de ese módulo, sólo encrypted_information de esa fila|
| rights_access_response_review.inspect |RightsAccessResponseDraft|safety.respond_rights_request|checked_body de ese módulo, sólo encrypted_response del borrador|

Rutas principales del censo: R_rights_access_field_review, R_rights_information_review y R_rights_access_response_review. La selección ejercita servicios públicos nativos directamente; no se simularán respuestas HTTP ni se acreditará transporte/middleware/navegador con esas llamadas. Otros métodos/operaciones y dependencias conservan sus propios requisitos. Se observó la condición de fuente en context/inspect_decision, record y inspect respectivamente, sin editar sus guards, ORM, cifrado o validadores.

## Seis casos previstos, sin candidato de producto

Por cada una de las tres entradas, ejecutar dos casos separados con preparación nativa legítima de perfil, autor y revisor independientes, lectura auditada, prueba y versiones vigentes: control sin revocación y retirada del permiso específico durante una espera real en la fila declarada. No atribuir cobertura de cuenta sin perfil a estos casos de perfil. Preparar el campo incluido y el borrador mediante sus servicios originales, sin fabricar filas cifradas para evitar precondiciones.

Dos conexiones PostgreSQL propias: transacción principal sostiene exclusivamente la fila objetivo; trabajador abre su conexión, llama al servicio real y registra pasivamente el PID efectivo cuando va a ejecutar su FOR UPDATE. Observar pg_stat_activity.wait_event_type=Lock y pg_blocking_pids con el PID del holder antes de retirar permiso. En el caso revocado comprobar pérdida mediante User nuevo y confirmar junto con la liberación del lock. En control, observar la misma espera y liberar sin retirar permiso. No cambiar reloj ni simular la espera.

El observador de descifrado reenvía siempre al callable original y devuelve su resultado intacto. Para el ciphertext objetivo registra sólo contador de llamadas y de retornos nativos satisfactorios, sin cifrado, plaintext, contacto, preferencia, motivo, ruta de archivo ni cuerpo en propiedades/logs/avisos. Instalarlo después de preparar los datos. Los controles deben comprobar descifrado satisfactorio y resultado nativo esperado; en revocación exigir PermissionDenied, **cero llamadas de descifrado al objetivo**, cero descifrados satisfactorios y snapshots íntegros. Una llamada seguida de error no se confundirá con descifrado satisfactorio.

Snapshots escalares del dominio con conteos y hashes antes/después, excluyendo la mutación deliberada del operador/permisos. En controles permitir sólo la auditoría/registro de lectura esperados por cada servicio, conservando expediente/fuentes y versiones; en denegaciones todo intacto. Guard explícito de archivo, serial, noPRODUCTION/RECOVERY_MODE y PostgreSQL propio. Eventos/hilos/timeout/conexiones acotados y liberados incluso en FAIL; cada caso deja metadatos finalmente para separar admisión inválida, ausencia de espera, denegación tardía y contenido realmente procesado.

Total **6 casos nuevos:3controles+3revocaciones**. Instrumento nuevo, sin editar tests originales ni observador419. Reutilizar fixtures/testigos originales de field decision, information review y access response draft con su identidad sintética y límites, no repetir sus baterías sólo por semejanza. El testigo existente de coverage que comprueba autoridad antes de descifrar tras espera se conserva como evidencia original, sin ejecución nueva de esa familia por este prerregistro.

## Decisión y límites

Todavía no hay FAIL de producto confirmado ni corrección autorizada por un resultado inventado. Tras el diagnóstico, auditar cada caso: si se prueba descifrado nativo antes de una denegación por revocación, registrarlo como incumplimiento de la frontera de autoridad, conservando que no se ha observado devolución de plaintext por HTTP. Si falla preparación o no se demuestra espera/revocación, es diagnóstico inválido y no prueba un bug de producto. Conservar controles y FAIL originales; no cambiar oráculos para conseguir PASS.

Runner oficial serial con PostgreSQL/Redis propios desechables y parser nativo; tiempo de pruebas separado de aplicación. Lint, revisión propia y del instrumento, AST/semántica/corte/congelación antes de ejecutar, notificaciones terminales después de cleanup y recibos verificados. No batería larga de exportaciones, no optimización general QA ni nuevos servicios/cargas/escaneos. Las skills Django y seguridad se aplican a autorización también autenticada y a variantes de fallos conocidos. Semgrep ya expone sus tres herramientas permitidas tras la recarga soportada, sin haber ejecutado un escaneo por instalarlo.

El resultado no cerrará automáticamente N09 ni representará todas las ramas de sus139IDs. Rectificación y referencias finitas de purgas/outbox/jobs siguen pendientes de su disposición; N02restante al final, N10/N11/N15 pendientes y N12–N14condicionados. El objetivo completo sigue en curso, sin apertura beta/producción ni proveedor.
