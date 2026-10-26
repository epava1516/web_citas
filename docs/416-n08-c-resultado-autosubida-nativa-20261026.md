# N08C — autosubida con worker real y Beat nativo

Aceptación local de la referencia finita de [N08C/414](414-n08-c-prerregistro-autosubida-nativa-20261026.md), tras la corrección mínima del instrumento descrita en [415](415-n08-b-resultado-y-c-correctivo-20261026.md). No hay cambio de aplicación ni candidato de optimización en B/C. N08 sigue abierto hasta conciliar sus 17 identificadores; contador global7/13.

## Ejecución y contraste con el primer fallo

`20261026-031404-bfa5f7d6`: **1 PASS, cero fallos, errores o skips**, 175,906 segundos JUnit. Se verificaron las 1.760 huellas congeladas (1.756 del runner y413/414/415/seguimiento aparte), fuentes estables durante la ejecución, PostgreSQL y Redis desechables reales, limpieza y notificación terminal Telegram `delivery: sent`. La auditoría posterior también terminó correctamente y confirmó su propio recibo.

Sólo se repitió el caso C. Los tres casos B válidos de `20261026-030555-20d5ac97` se conservaron sin repetir; aquel lote mantiene su resultado **3 PASS y1 FAIL**, no se convierte en una batería verde. El primer C falló antes de la fixture y del arranque del worker, por comprobar eager antes de que `setup` solicitase `directory/photo_environment`. Se movió la misma aserción después de `setup`; original, parche mínimo, huellas y fallo siguen preservados. No se atribuye ese fallo a la aplicación.

## Qué se observó

Dos compras exclusivamente sintéticas se prepararon mediante los servicios nativos y eventos firmados locales: una del titular individual y otra del gestor de agencia. La preparación eager queda fuera de las mediciones de tarea y no acredita el worker. Ventana diaria y cupo uno, periodos ajustados manteniendo duración, sin sustituir el reloj ni las guardas de aplicación.

El worker real usó pool prefork con dos hijos y rol SQL restringido del arnés desechable. Hubo **cinco ejecuciones únicas, no eager, SUCCESS**, cada una con prueba independiente de `current_user` y PID: cuatro de autosubida y un refresco de publicación generado por la revocación. Se crearon dos hijos, pero las cinco ejecuciones se observaron en **un único hijo**; no se afirma reparto entre ambos.

La tarea preencolada produjo una subida para el primer derecho elegible y ninguna para el segundo, todavía futuro. El reintento con worker listo produjo cero nuevas subidas y respetó ventana/cupo. Se preservó el oráculo para un eventual cambio de día UTC, sin presentarlo como repetición de la misma ventana.

Después se suspendió explícitamente el primer derecho. El segundo se hizo temporalmente vigente y se revocó su consentimiento mediante `consent_revoked_at` y `save` nativos antes de iniciar Beat. Se observó el refresco derivado y se drenó por separado. Beat seleccionó la entrada fuente `synthetic-promotion-bumps`, sin modificar sus **60 segundos**, y produjo dos despachos separados por **59,971952 segundos**. En ambos, el segundo derecho avanzó `last_checked_at` y conservó cero `PromotionBumpExecution`. La exclusión del primero se atribuye a suspensión; la del segundo a revalidación de elegibilidad. Fechas editoriales, estado, versión del ciclo, revisión aprobada y número de revisiones permanecieron iguales.

## Tabla de tiempos por etapa

Milisegundos observados, una ejecución por fila; no son mediana, p95, carga ni SLA. Pared/CPU corresponden al cuerpo de tarea observado; la prueba adicional de rol y snapshot en postrun queda fuera de ese intervalo. CPU del hilo excluye PostgreSQL. La espera de la primera fila incluye arranque de worker; las demás usan worker listo.

| Etapa | Espera cola (ms) | Pared tarea (ms) | CPU hilo (ms) | Resultado | Después de otro candidato |
| --- | ---: | ---: | ---: | ---: | --- |
| Autosubida preencolada con arranque | 2860,428 | 397,838 | 188,752 | 1 subida | No medido |
| Reintento con worker listo | 9,226 | 288,758 | 105,043 | 0 nuevas | No medido |
| Primer tick Beat nativo60s | 17,444 | 233,881 | 85,356 | 0 nuevas | No medido |
| Segundo tick Beat nativo60s | 8,009 | 191,542 | 60,555 | 0 nuevas | No medido |

El trabajo útil y estado difieren entre filas; no comparar sus tiempos como ganancia de código ni sumar refresco, cola y preparación a una supuesta latencia comercial única. Sin candidato nuevo, mejora atribuible no evaluable. Las pruebas históricas conservadas de ventanas/cupo, siete carreras y avance del lote100 aportan su evidencia funcional original; no son nuevas mediciones de latencia para100 derechos ni una prueba de capacidad de producción.

## Limpieza y límites

Se comprobó la desaparición de las cuatro identidades PID/tiempo de inicio (worker, dos hijos y Beat), salida normal del worker, terminación de Beat, eliminación de rol temporal, credenciales y módulo privado. Las claves Redis ajenas conservaron su contenido; cero claves nuevas fuera del namespace propio. La limpieza terminal del runner eliminó sus recursos y directorio temporal. El caso C no hizo llamadas Client; no añade peticiones HTTP a las436 de B.

Fuente corregida SHA256 `bb877043e727dcbd69aa5179dafcb137e1ef2b6b2d257fd6f21804eb4350b1d7`; original `7fa91f6739870714d8085d8c428121b08e0122262c3a3a2468979b95d2a252b6`. Auditoría local: `artifacts/recorridos-n08-c-20261026/reference-c-audit.json`. Su archivo versionado se conciliará con el cierre N08; no se afirma todavía un paquete final. Sin proveedor, pago real, apertura beta, migraciones ni cambios de servicios existentes. El siguiente paso es la revisión conjunta de las 17 acciones y los criterios del contrato.
