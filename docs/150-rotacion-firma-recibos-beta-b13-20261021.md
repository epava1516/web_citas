# B13 — Clasificación de firma: recibos e integridad de entradas

Estado: primer grupo persistente verificado en local; B13 abierto, siete de18puntos cerrados. Continúa el [cierre estático147](147-consumidores-hmac-beta-b13-20261021.md), que contiene383funciones en161archivos consumidores y no equivale a clasificación de campos.

## Campos y respuesta ante rotación

| Campo persistente | Productor/consumidor verificado en fuente | Propósito y respuesta prevista |
|---|---|---|
| Report.receipt_digest | safety.crypto.digest; safety.views.submit/receipt | Autoridad del recibo anónimo. Cambiar SECRET_KEY invalida el enlace anterior; no habilitarlo por conocer sólo un UUID. |
| Report.payload_digest | safety.crypto.digest; safety.views.submit | Binding de replay de entrada. Un replay anterior no debe recalcular y sobrescribir el binding persistido. |
| RightsRequest.receipt_digest | safety.rights.fingerprint; rights.submit/receipt | Autoridad de recibo de derechos. SECRET_KEY_FALLBACKS del framework no implica validación de este HMAC de dominio. |
| RightsRequest.payload_digest | safety.rights.fingerprint; rights.submit | Binding de entrada/replay de derechos. Conservar texto cifrado, estado, fechas y huellas originales, incluso si el replay anterior deja de coincidir. |

Son cuatro campos en dos modelos, no todos los HMAC de la aplicación. La misma raíz alcanza publicación, rectificaciones, pruebas de ámbito, respuestas, planes y exportaciones; esos datos requieren clasificación propia y no se presumen migrados por una prueba de recibos.

## Ensayo preparado

Cuatro casos reales PostgreSQL: denuncia/derechos × framework fallback desactivado/activado. Claves safety/MFA explícitas e independientes desde antes de generar las fixtures; SECRET_KEY inicial y nueva son sintéticas. El cuerpo antiguo debe seguir descifrándose sin cambiar ciphertext. Los recibos ES/EN antes200 y después404, y la consulta no autorizada no crea auditoría de lectura. El replay de la entrada anterior debe409 sin crear otra fila ni reescribir el origen. Una entrada nueva es otro expediente y debe tener recibo válido; no se presenta como reemisión del recibo anterior.

Después de rotar se crea una sesión de revisión/MFA sintética nueva. GET privado no debe revelar el cuerpo ni registrar inspección; POST de propósito válido debe permitir lectura auditada del original y conservar todos sus campos/fechas. Son peticiones Client WSGI, no navegador, TCP o verificación de identidad real. Las fixtures de MFA no se presentan como TOTP humano ejercitado en este caso.

Selección focal prevista22casos:4nuevos,1testigo existente de sesión/HMAC y claves explícitas,6productores directos y11cierre estático. PostgreSQL real para los casos de aplicación; los inventarios AST no reciben por ello crédito de datos históricos. Sin nueva batería de capacidad ni cambios de claves normales. Congelar fuentes y grafo antes de ejecutar, conservar negativos y verificar limpieza y Telegram terminal.

## Procedimiento y pendientes

Antes de una rotación de firma inventariar canales activos, sesiones, OTP, MFA de recuperación y evidencia persistente. No asumir que fallback de Django valida todos los HMAC propios; no rehash de auditoría para hacer desaparecer incompatibilidades. Mantener cifrado independiente, canal administrativo autorizado y revisión de continuidad de los plazos originales.

Si el recibo anterior deja de funcionar, no sustituirlo automáticamente por un caso nuevo ni trasladar los datos por conocer su referencia. Un canal sustitutorio requiere procedimiento de identidad/ámbito y autorización propios. Este ensayo verificará lectura interna del expediente original, no entrega de un enlace de reemplazo al interesado. Esa continuidad del canal y los demás bindings persistentes siguen pendientes; no autoriza una rotación general en producción.

## Resultado terminal

053022-5596f181:22PASS/0FAIL/0ERROR/0SKIP,67.83sJUnit,4workers. [Auditoría terminal](evidencias/b13-signing-receipts-terminal-audit-20261021.json): cuatro casos de dominio, uno de sesión/HMAC existente y diecisiete estáticos. PostgreSQL real para los cinco casos de aplicación; sin skips ni negativo de ejecución. Fuente de producto existente igual al corte041741; fuentes congeladas, contenedores/temporal/PID propios ausentes y TelegramPASS confirmados.

Recibos ES/EN rechazados tras rotación en ambos dominios, con y sin fallback del framework. Replay anterior409 sin rebind ni duplicación; una entrada nueva mantiene su canal propio y no reemplaza el expediente original. Cuerpo cifrado, huellas, fechas, estado y resto de campos originales iguales antes/después. El revisor con sesión nueva accede al original sólo mediante lectura privada auditada, mientras GET no crea esa lectura. Claves explícitas MFA/safety permiten descifrar sin reescribir el cuerpo.

Quedan clasificados y respaldados por prueba cuatro campos de dos modelos; no se extiende a todos los bindings, dominios o ramas dinámicas. La entrega de un canal sustitutorio al interesado no se ensaya ni se autoriza automáticamente: replacement_channel_for_old_case_verified=false. Mantener esa limitación en el procedimiento de rotación y continuidad. B13 sigue abierto7/18 por estos restantes y otros secretos.
