# N09E — fronteras antes del descifrado verificadas

Aceptación técnica **local de tres correcciones de autoridad**, con cuatro variantes adicionales verificadas; no cierre de N09. Diagnóstico [432](432-n09-e-prerregistro-lecturas-privadas-tras-espera-20261026.md), plan anterior al cambio [433](433-n09-e-correccion-prerregistro-fronteras-descifrado-20261026.md), base `a5cd18d` en master. Se mantienen alpha/noindex, datos e identidad sintéticos y ausencia de proveedores reales.

## Requisito y evidencia original

Revalidar autoridad después de esperar una fila privada y antes de descifrar su contenido. El run `20261026-075104-d7159725` conserva **3 PASS/3 FAIL,129,909sJUnit**, cero ERROR/SKIP de pytest,1.770huellas estables, cleanup y Telegram confirmados. El ERROR global del runner refleja los tres FAIL; no tres errores instrumentales.

Auditoría independiente confirmó controles legítimos y revocaciones durante espera PostgreSQL real con PID bloqueante propio: decisión de campo2descifrados nativos satisfactorios, información1y borrador1después de confirmar la retirada de permiso. Los servicios terminaron PermissionDenied y revirtieron sus efectos, pero lo hicieron después de procesar el contenido objetivo. Los observadores reenviaron al callable real sin alterar resultados y conservaron sólo contadores/hash/metadatos. Se demuestra una frontera interna de autoridad incumplida, **sin atribuir devolución de plaintext por HTTP**; el instrumento usa servicios nativos directos.

## Cambio y resultado de la corrección

Run `20261026-082019-bb786d3f`: **38 PASS/1.044,294sJUnit** —17min24,294s—, cero FAIL/ERROR/SKIP. Auditoría raíz completa: selección exacta,1.772huellas estables antes de documentación terminal (1.769runner+3documentos),14esperas reales, limpieza de recursos propios y Telegram de pruebas/auditoría confirmados. PostgreSQL/Redis propios desechables y parser nativo; no conexión dummy presentada como integración.

Sólo siete comprobaciones nuevas en seis funciones de cuatro módulos:

- `rights_access_field_decision.py`: propose tras inventario y última decisión; context tras decisión, compartido por inspección/revisión; consume tras decisión aprobada.
- `rights_information_review.py`: record tras Information, antes de proof/firma/replay/auditoría/unseal, para inspect/review.
- `rights_access_response_review.py`: inspect tras borrador, antes de auditoría/descifrado; record conserva la llamada a inspect.
- `rights_access_field_read.py`: read tras inventario propio, antes de motivo/proyección.

Se reutilizan los autorizadores existentes con el User/epochs originales, sin sustituirlos ni modificar roles, formularios, endpoints, modelos, migraciones, cifrado, configuración o servicios de infraestructura. Las entidades ajenas al cambio permanecen ASTidénticas. Se conservan controles finales, scope/COI, independencia, proof/retención, lecturas auditadas, referencias/versiones, firmas, replays y transacciones. No se bloquea al operador ni se adoptan epochs actuales para eludir una revocación.

La revisión diferencial de fuente e historia y los callers estáticos se conservan en `artifacts/recorridos-n09-e-20261026/DIFFERENTIAL_REVIEW_20261026.md` y `candidate-source-selection-review.json`:3sitios de llamada explícitos a field_read,2context,2propose,2draft.inspect,1consume y1information.record en apps/safety. Es un conteo estático acotado, no un callgraph dinámico exhaustivo. La recomendación previa condicional queda resuelta por esta evidencia de38casos, sin certificar todo el repositorio.

## Selección y oráculos comprobados

**Seis diagnósticos432 íntegros**: tres controles legítimos conservan su resultado/contenido nativo y auditoría esperados; las tres revocaciones originales ahora producen PermissionDenied antes de cualquier llamada al descifrado objetivo y mantienen dominio/estado mínimo intactos. El instrumento432 quedó byte a byte idéntico al que produjo los FAIL originales.

**Ocho regresiones nuevas**: propose reteniendo inventario y observando motivo de lectura; replay de propose reteniendo decisión existente y observando su body; consume reteniendo decisión aprobada independientemente y observando su body; field_read reteniendo inventario y observando su motivo. Cada variante tiene control válido y revocación del permiso respond del autor/operador, distinto del revisor. Controles: propose nuevo añade exactamente Action+Decision, replay no cambia nada y consume/read añaden Action; denegaciones: cero llamadas/retornos de descifrado del objetivo y snapshots completos intactos. No se atribuyen cuatro baseline ni cuatro defectos adicionales confirmados a estas regresiones.

En las14esperas se observaron Lock/PID efectivo/bloqueante propio antes de revocar o liberar; en siete negativos se confirmó la pérdida del permiso al liberar. Hilos/conexiones/transacción holder liberados. Comparaciones de contenido legítimo mediante booleanos sin repr privado; observadores sólo forward al original, nunca guardas/ORM/cifrado/proof/reloj simulados.

**24originales sin editar**: field_decision2, scope_inventory2, information_review4, information_review_races8, information_review_mobile2, access_response_draft2 y cuatro casos del recorrido móvil básico de respuesta final (perfil/cuenta y ES/EN). Conservan independencia, lectura/fuente/proof/epochs, replays, CSRF, concurrencia de caso y Chromium móvil. Las esperas nuevas son de perfil; las regresiones funcionales de cuenta no se presentan como esperas adicionales de cuenta.

Los ocho móviles auxiliares de metadatos físicos/logs conservan sus testigos originales y no se declaran PASS nuevo: no cambian parsers, retención ni payloads; la guarda añadida precede a sus ramas y los cuatro básicos ejercitan el mismo entrypoint en ambos ámbitos/idiomas. N09D117y coverage no se repiten por semejanza o por documentar este resultado. No se suman ejecuciones distintas como una batería integrada.

## Tabla antes y después

Una muestra por caso. **Los segundos son del caso completo con preparación nativa, espera, snapshots y cleanup**, no latencia de aplicación. Sin muestra comparable de latencia normal ni porcentajes causales; statement_seconds del instrumento original puede reflejar una consulta posterior coincidente y no se utiliza como cronómetro del primer lock.

| Caso/objetivo | Antes: descifrados satisfactorios/resultado | Después | Caso completo antes → después |
| --- | --- | --- | ---: |
| Campo, permiso revocado |2;PermissionDenied tardío y rollback|0;PermissionDenied antes del objetivo, dominio intacto|21,763 →16,862 s|
| Información, permiso revocado |1;PermissionDenied tardío y rollback|0;PermissionDenied antes del objetivo, dominio intacto|9,217 →8,524 s|
| Borrador, permiso revocado |1;PermissionDenied tardío y rollback|0;PermissionDenied antes del objetivo, dominio intacto|11,329 →10,529 s|
| Campo, control válido |2;éxito nativo|2;éxito nativo/auditoría esperada|24,145 →24,772 s|
| Información, control válido |1;éxito nativo|1;éxito nativo/lectura esperada|8,963 →7,927 s|
| Borrador, control válido |1;éxito nativo|1;éxito nativo/auditoría esperada|11,281 →9,813 s|
| Cuatro variantes nuevas |Sin baseline propio|4controles válidos+4denegaciones antes del objetivo|Sin pareja comparable|
|24originales |Testigos originales retenidos|24PASSdentro de38|Sin pareja comparable|

Las consultas adicionales tienen coste de seguridad. QA129,909sde6diagnósticos frente a1.044,294sde38casos son selecciones distintas, sin mejora causal de tiempo de aplicación o QA atribuida. El criterio de éxito es corregir autoridad conservando comportamiento, no reducir duración.

## Evidencia, límites y continuación

Resumen saneado: [n09e-autoridad-descifrado](evidencias/n09e-autoridad-descifrado-20261026.json). Originales locales: baseline/candidate-audit, freezes, fuentes anteriores, propuestas aisladas y revisiones en `artifacts/recorridos-n09-e-20261026/`; run/XML en `artifacts/local-ci/20261026-082019-bb786d3f/`. Custodia excluye logs, comandos/credenciales, Settingsrepr, contenido privado/ciphertext de sujetos, documentos laterales y grafo completo ajeno al alcance.

Corte433antes de congelar:2.064fuentes/20.010nodos/84.179relaciones/965comunidades,SHA256 `14278d88d386d781b6cc8e54b325dd56490dcc1ea36ca6e1fb152f4b9b4855c2`. AST de cinco fuentes y semántica433/17 verificados;434recibe su delta terminal. Semántica selectiva de raíz documentada como tal, no salida nativa inexistente; tokens nativos desconocidos y V1nuevo0/histórico8conservado. No sustituye N15.

Los contadores cubren exclusivamente el ciphertext declarado, no cualquier contenido del servicio: un replay puede haber procesado contenido legítimo antes de esperar su último lock. No se promete serialización universal tras la última lectura, ni se dan por verificadas todas las proyecciones/locks tardíos de source_snapshot o sus ramas de cuenta. Esos límites conservan su evaluación individual en N09.

N09 acumula **16 defectos locales corregidos** —13A/B/C/D+3E—, no16bloques contractuales. Se mantienen **8/13 bloques obligatorios aceptados**, N09 completo abierto139IDs y pendientes de fuentes/rectificación y referencias finitas de purgas/outbox/jobs. N02restante al final, N10/N11/N15 pendientes y N12–N14condicionados. Objetivo completo no terminado, sin apertura beta/producción ni proveedor.
