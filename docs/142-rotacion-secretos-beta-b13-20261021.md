# B13 — Rotación de secretos, fase de transición, 2026-10-21

Estado: transición de cifrado verificada en alcance local; rotación general y B13 siguen abiertos. [Matriz141](141-continuidad-moderacion-beta-b13-20261021.md); siete de18puntos cerrados por el corte anterior. No credenciales reales modificadas.

## Inventario de clases y límites

| Clase | Uso actual | Procedimiento y evidencia pendiente |
| --- | --- | --- |
| DJANGO_SECRET_KEY | Sesiones, salted_hmac de varios dominios, reglas de publicación y huellas persistentes | La rotación revoca sesiones y cambia HMAC; no es transparente para enlaces, pruebas, códigos MFA o aprobaciones anteriores. Ensayo sintético preparado; inventario de efectos y revalidación aún necesario |
| SAFETY_ENCRYPTION_KEY | Cuerpos JSON, binarios legacy, referencias/tombstones del repositorio de objetos | Transición preparada con nueva clave activa y anteriores sólo de lectura; no reescribir auditoría ni retirar claves implícitamente |
| MFA_ENCRYPTION_KEY | Semillas TOTP cifradas | Misma transición independiente; recovery_digest depende de SECRET_KEY, no de esta clave de cifrado |
| RIGHTS_OBJECT_KEYS/ACTIVE_KEY | Datos de objetos AES por key ID | Keyring y rotación existentes con RustFS; conservar referencias/tombstones/retenciones y comprobar testigo actual |
| RIGHTS_DELIVERY_PROXY_SECRET | Autorización del proxy privado | Requiere coordinación del proxy y aplicación; no ensayado por la transición Fernet |
| Credenciales PostgreSQL/Redis/S3 | Conexión de servicios | Rotar en el servicio y clientes, comprobar rechazo anterior y recuperación; ensayo pendiente y proveedores reales separados |
| Ledger y backup | RECOVERY_ENCRYPTION_KEY, RECOVERY_SIGNING_KEY y claves de copia | No reemplazar claves de archivos retenidos ni autoridad independiente; transición/custodia distintas, pendientes de contraste |

En desarrollo, cifrado MFA/safety sin claves explícitas deriva de SECRET_KEY. Cambiar sólo SECRET_KEY en ese estado cambia también el cifrado efectivo y rompe lectura anterior. No usar esa derivación como estrategia de rotación ni en producción. Cambiar una clave de firma no equivale a migrar huellas persistentes. No se añaden fallbacks de firma ni se mantienen sesiones antiguas como efecto de esta implementación.

## Transición Fernet preparada

apps/core/encryption.py construye una clave activa y hasta tres anteriores con MultiFernet. Cifra sólo con la activa y descifra intentando las anteriores. Sin lista anterior devuelve Fernet como antes. Configuración inválida, duplicada, más de tres anteriores o tipos incorrectos se rechaza con diagnóstico fijo sin valores. Las anteriores se configuran como cadena de claves separadas por comas; vacía es el estado por defecto.

Variables nuevas MFA_ENCRYPTION_KEY_FALLBACKS y SAFETY_ENCRYPTION_KEY_FALLBACKS. Requieren clave activa explícita; no se mezclan con derivación implícita de desarrollo. settings valida claves explícitas al arrancar y cipher vuelve a validar su configuración al usarla. No se descifra ni reescribe automáticamente una fila, archivo o evidencia al activar una clave nueva. La huella del cliente de almacenamiento y la de proyección de portabilidad incorporan la configuración de lectura para impedir reutilización de cómputo/transporte con otra configuración.

El ejemplo de producción transmite las listas opcionales a app, worker y Beat mediante su configuración común; no se despliega. .env.example contiene campos vacíos. No registros de claves, nuevos proveedores, migraciones de datos ni comandos que pongan secretos en argumentos de proceso.

## Runbook local de transición autorizada

1. Ingeniería inventaría datos/campos/archivos cifrados, referencias, tombstones, auditoría, copias y política de retención. Conservar claves previas bajo custodia separada; no imprimirlas ni copiarlas a evidencias o Telegram. Una exposición de clave exige tratar el incidente y su alcance, no se resuelve por conservarla como fallback.
2. Verificar primero con datos sintéticos en aislamiento. Preparar la clave activa nueva y la anterior como lectura, sin cambiar SECRET_KEY ni la clave de otra familia. Mantener autoridad, fechas y estados existentes. La prueba local no autoriza tocar credenciales reales.
3. En el entorno autorizado, coordinar consumidores y productores: los lectores deben conocer la clave nueva antes de recibir nuevas escrituras, y conservar las anteriores necesarias. Mantenimiento con ingreso/tareas detenidos o despliegue coordinado; no una mezcla de procesos que desconozcan claves ya usadas. Este ensayo no acredita despliegue mixto en vivo.
4. Tras reiniciar de forma coherente, comprobar lectura antigua, escritura nueva exclusivamente con activa, MFA y lectura de objetos; comprobar integridad/auditoría sin reescritura. Los fallbacks no conceden autoridad a solicitudes caducadas, sesiones revocadas ni referencias purgadas.
5. Para rollback de configuración, todos los lectores deben conservar también la clave que cifró las escrituras nuevas; volver a la clave antigua como única lectora pierde acceso a lo recién escrito. No usar esa reversión unilateral.
6. No retirar una clave anterior por tiempo ni porque las escrituras nuevas funcionen. Requiere censo completo y evidencia de que ya no es necesaria, incluyendo copias retenidas y tombstones, o un procedimiento de recifrado compatible con auditoría y custodia. Este incremento no implementa ese censo ni recifrado general. Si se alcanza el límite de tres anteriores, no descartar otra para pasar el arranque: resolver retención/migración primero.

Responsable técnico local: Ingeniería. Custodia, sustitutos, acceso de emergencia, incidente real y operación productiva siguen en B17. La rotación general de secretos no queda aceptada por esta fase.

## Verificación preparada

Cohorte prevista150casos con4workers:60de observabilidad/retención y recorridos comunes actuales,16nuevos de rotación,9de perfil de despliegue,16de proyección de portabilidad,24de clientes de objetos,11de cuentas,5de MFA/agencias y9de almacenamiento. PostgreSQL/Redis/RustFS reales locales donde corresponda; dobles de lifecycle de clientes identificados como mocks, sin crédito de proveedor. Fuentes y grafo congelados antes de ejecutar. No batería de capacidad ni aceptación B13 por esta selección.

Casos nuevos: configuración inválida y diagnóstico sin eco; validación al arrancar; tres anteriores; ausencia de activa explícita; filas PostgreSQL antiguas intactas y TOTP válido bajo transición; nuevas escrituras no legibles por clave antigua; retirada prematura falla sin borrar datos; rotación de firma invalida sesión y cambia HMAC sin modificar cifrado explícito; referencia de objeto antiguo y bytes RustFS permanecen intactos y nuevo descriptor usa activa. Caché de proyección se recalcula al cambiar fallbacks y conserva cuatro lecturas auditadas; configuración opcional llega a los tres servicios del ejemplo.

## Primer corte y correctiva focal

030427-5c12b873:149PASS/1FAIL/0ERROR/0SKIP,206,738sJUnit,4workers. El único fallo ocurrió antes de rotar firmas: la cuenta sintética carecía de correo verificado y AccountGate cerró correctamente su sesión. [Auditoría negativa](evidencias/b13-encryption-transition-first-negative-audit-20261021.json): fuentes, limpieza y TelegramERROR confirmados; fuente exacta del test preservada porSHA.

Se corrige únicamente esa fixture con correo sintético y email_verified_at, conservando el rechazo de cuentas no verificadas. Producto intacto desde el corte150. Repetición focal del caso de firma; los otros149casos sólo se reutilizarán tras comparar fuentes de producto, AST del módulo y aserciones del caso modificado. No afirmar una ejecución única150PASS si se concilian dos cortes.

El primer intento de extracción estructural de configuración no encontró PyYAML en el entorno del grafo; no modificó fuentes ni grafo. Se sustituyó por render de Compose local con valores sintéticos y --no-env-resolution, comprobando dos variables y los alias de tres servicios. La plantilla real .env no se leyó. Además se corrigió el generador de sidecars del grafo que aún marcaba B12 pendiente pese al acta14; el estado ahora refleja siete cerrados y B13 abierto.

## Resultado vigente: transición local verificada

031135-ec7bc9c2:1PASS/0FAIL/0ERROR/0SKIP focal,38,983sJUnit. Cuenta sintética verificada establece sesión antes de cambiar SECRET_KEY y pierde autenticación después; cifrado independiente permanece legible y las huellas HMAC/reglas cambian. La corrección no desactiva AccountGate.

[Conciliación estricta](evidencias/b13-encryption-transition-scoped-reuse-audit-20261021.json):149PASS del030427 más1PASS focal son150casos únicos entre dos cortes, no una ejecución única150PASS. Producto y configuración idénticos entre ambos; módulo de test sólo cambia los argumentos email y email_verified_at del caso de firma, con AST normalizado igual tras retirarlos. Aserciones, imports, decoradores y helpers compartidos intactos. Fuentes actuales, limpieza y Telegram terminal de ambos cortes confirmados.

Los16casos de rotación quedan cubiertos, incluyendo PostgreSQL, TOTP y RustFS reales locales. Las nuevas escrituras usan activa, las anteriores se leen durante transición, las filas antiguas/bytes de objeto permanecen intactos. Retirar antes de tiempo impide lectura antigua sin borrar datos; ello no habilita retirar una clave en un entorno real. Otros134casos cubren recorridos afectados: avisos/retención, cuentas/MFA, configuración, auditorías de portabilidad y almacenamiento. Mocks de lifecycle no se presentan como integración real.

Quedan añadidos SAFETY_ENCRYPTION_KEY_FALLBACKS y MFA_ENCRYPTION_KEY_FALLBACKS vacíos por defecto, validación temprana con diagnóstico fijo, coherencia de cachés de lectura/proyección y configuración opcional del ejemplo de producción. El helper no contiene ORM ni recifrado; el único cambio de datos del test MFA es el consumo TOTP normal. No migración de datos ni despliegue efectuados.

## Pendiente para completar B13

Censo de huellas persistentes afectadas por SECRET_KEY y procedimiento de revocación/revalidación; inventario completo para retirar claves antiguas (incluyendo copias y tombstones) y tratamiento de claves comprometidas; coordinación y ensayos de credenciales de servicios, proxy y ledger; contraste de restauración, retirada urgente y compatibilidad de rollback/migraciones del contrato beta. No cerrar B13 por esta fase ni asumir rotación transparente de HMAC. B07 mantiene su FAIL y no hay nueva medición de capacidad/rendimiento.

Continuación posterior: [143](143-inventario-claves-hmac-beta-b13-20261021.md) verifica un censo acotado de54columnas y ocho productores HMAC directos con36PASS. No equivale al inventario transitivo/externo completo ni autoriza retirar claves.
