# B13 — Separación opcional entre firma Django y HMAC de dominio

Estado: implementación verificada localmente por evidencia combinada; B13 abierto7/18. La limitación verificada en [150](150-rotacion-firma-recibos-beta-b13-20261021.md) es el punto de partida: en modo heredado, rotar SECRET_KEY revoca recibos y altera bindings persistentes.

## Comportamiento implementado

SAFETY_HMAC_KEY es opcional. Vacía conserva exactamente el secreto heredado de Django; explícita gobierna sólo crypto.digest y rights.fingerprint. Se mantienen salts y SHA256, sin normalización de bytes, formato nuevo de digest, recifrado ni actualización de filas. La validación admite vacío o string explícito de al menos50caracteres, no sólo espacios; un error no imprime el valor. No se acredita entropía por longitud.

Para datos existentes, fijar exactamente el valor anterior de DJANGO_SECRET_KEY antes de rotar la firma Django conserva los HMAC existentes. No generar una clave de dominio diferente sobre filas ya firmadas esperando una migración automática. En una instalación nueva sin vínculos previos se puede provisionar una clave independiente por canal privado. El ejemplo de entorno queda vacío y Compose propaga el campo opcional por el ancla común de app/worker/Beat; no se modifica ninguna configuración real.

La separación permite ensayar continuidad del mismo recibo y replay al cambiar la firma de sesiones. No reemite un secreto ni autoriza acceso por UUID. La rotación/compromiso de la propia clave de dominio sigue siendo otro procedimiento: puede invalidar pruebas, decisiones y canales antiguos, no se corrige rehash de evidencia inmutable ni se promete recuperación del canal comprometido.

## Dependencias incluidas

El memo de rights_operation_fingerprints toma la clave efectiva en cada llamada y la revalida tras el productor nativo; un cambio de clave no reutiliza un resultado anterior. La versión de publicación incorpora la clave efectiva y la fuente del proveedor, manteniendo también el cambio conservador por SECRET_KEY. Las cachés de objetos y proyección de selección de portabilidad incluyen la configuración HMAC. Se debe ensayar la deriva para no conservar autorización previa tras cambiar la clave de dominio.

El inventario de productores conserva ocho sitios y distingue los dos productores de dominio de los seis aún ligados a Django. Sólo acepta el argumento secret del proveedor domain_signing_key en esos dos sitios registrados; incorpora huella del proveedor como séptima fuente. No autoriza retirada ni declara el censo transitivo completo. OTP, códigos de recuperación MFA y tokens de cuenta conservan su clasificación previa y no pasan por esta clave nueva.

## Pruebas preparadas

Recibos denuncia/derechos × fallback framework × modo heredado/fijado: ocho casos, ES/EN. La rama heredada debe mantener la revocación y replay409; la fijada debe conservar el mismo enlace y replay al expediente original, sin nuevas filas ni cambio de evidencia/fechas. Ambas mantienen entrada nueva e inspección privada auditada.

Nueve casos del proveedor cubren configuración inválida sin eco, bytes HMAC idénticos antes/después de fijar, cambio efectivo durante memo atómico y versión de publicación, y rechazo en arranque. Se amplían comprobaciones de Compose y claves de caché; la variación de proyección usa pin equivalente para preservar autoridad y exigir nuevas auditorías. La batería incluirá las regresiones afectadas de memo/estado/objetos/portabilidad, el censo estático y la transición Fernet ya existente con RustFS real. No se fija un total hasta conciliar colección/JUnit.

Antes de probar se refrescan AST, estructura de configuración y semántica documental; se congelan todas las fuentes durante la ejecución. Conservar negativos, comprobar limpieza y recibos Telegram. La aceptación sólo se extenderá al alcance demostrado, nunca a una rotación general de claves de dominio, proveedores ni apertura externa.

## Negativos preservados y correctivas de pruebas

054538-77daeb91 terminó antes de ejecutar casos con INTERNALERROR de xdist. [Auditoría](evidencias/b13-domain-key-prerequisite-negative-20261021.json): fuentes/limpieza/TelegramERROR verificados. Se observó independientemente ausencia de la imagen RustFS fijada; se recuperó por digest exacto, sin atribuir sólo por ello la causa interna del worker.

054839-d27019ab:170PASS/2FAIL/0ERROR/0SKIP,399,459sJUnit. [Auditoría funcional negativa](evidencias/b13-domain-key-functional-negative-20261021.json). Los ocho casos de recibos/modos pasan; el corte completo no es PASS. Fallos de expectativa: la clave opcional entró en VALUES y fue tratada como obligatoria; el pin equivalente se mantenía constante después del primer hijo, así que reutilizar el cálculo era correcto aunque se crearan cuatro lecturas auditadas.

Sin cambiar producto, se separa la clave opcional del registro de entradas obligatorias y se añade prueba positiva explícita de ausencia/legacy. La prueba de proyección exige una computación para el pin estable y cuatro auditorías; el fallback Fernet aleatorio por hijo conserva cuatro recomputaciones. Un caso adicional cambia realmente la clave efectiva a mitad de lote y exige ValidationError/rollback de lecturas. Se preparan13casos correctivos (10perfil/3proyección); los160PASS ajenos al alcance modificado sólo se reutilizarán con igualdad de fuentes y dependencias demostrada. No se anunciará una ejecución única de173PASS.

## Activación y límite de compatibilidad

La fijación exige que el secreto anterior ya cumpla la validación explícita de50caracteres; no rellenarlo o normalizarlo para alcanzar ese tamaño, porque cambiaría los HMAC. Los defaults débiles de desarrollo no se convierten por ello en claves productivas. Para una rotación prevista, desplegar primero código compatible en todos los productores, workers y herramientas de dominio, fijar el valor exacto anterior por canal privado y comprobar continuidad antes de cambiar DJANGO_SECRET_KEY. El cifrado MFA/safety debe seguir explícito e independiente.

Las imágenes antiguas que ignoran SAFETY_HMAC_KEY no son un rollback válido después de activar la separación y cambiar la firma Django. El ciclo145–146 acredita su pareja/corte, no esta combinación nueva. La aceptación integrada B16 debe fijar una candidata/retorno que entiendan la configuración; no volver a un secreto comprometido para aparentar continuidad. La recuperación ante compromiso de la propia clave de dominio y la clasificación restante siguen abiertas.

## Resultado verificado

060120-192516da:13PASS/0FAIL/0ERROR/0SKIP,69,203sJUnit,4workers. [Aceptación acotada](evidencias/b13-domain-key-scoped-acceptance-20261021.json):13correctivas más160PASS reutilizados estrictamente de054839 =173casos únicos; no ejecución única173PASS. Los archivos anteriores de las dos pruebas corregidas se reconstruyeron y coinciden exactamente con las huellas congeladas. Helpers y tests de proyección restantes mantienen AST idéntico; ninguna otra prueba importa el módulo de despliegue. Producto y todas las demás fuentes idénticos entre cortes.

Los ocho casos de recibos pasan: cuatro heredados revocan el enlace antiguo; cuatro con pin conservan el mismo recibo y replay al caso original, con/sin fallback y ES/EN. Ciphertext, huellas, plazos y demás campos originales se conservan. Configuración inválida falla sin eco; cambio efectivo de clave invalida memo/versión pública. El lote con cambio real de clave rechaza y revierte lecturas; pin estable permite una computación y mantiene cuatro auditorías. El ejemplo de despliegue acepta ausencia de clave opcional y propaga el valor explícito a app/worker/Beat.

Las regresiones retenidas incluyen publicación nativa/almacenada, upgrade real, memo HMAC, portabilidad, lectores de objeto y transición Fernet con RustFS real. Sus170PASS iniciales no se presentan como batería verde: se excluyen los diez PASS que se vuelven a ejecutar dentro de las correctivas y se conservan160. Ambos fallos y el INTERNALERROR previo permanecen documentados. Fuentes actuales, procesos/temporal/contenedores propios ausentes, inventario de contenedores de objeto vacío y Telegram terminal confirmados.

[Inventario actualizado de productores](evidencias/b13-domain-key-direct-producers-20261021.json): ocho sitios, dos con clave de dominio o fallback heredado y seis con firma Django; siete fuentes incluyendo proveedor. retirement_authorized=false. No se ha modificado clave normal, `.env` real, datos del entorno normal, proveedor o despliegue externo. Las migraciones no cambian. B13 sigue abierto7/18; no aceptación de recuperación por compromiso/rotación de la clave de dominio ni de rollback a una imagen que no entienda el campo activo.

La propagación al clon y la conservación del recibo tras restauración real se verificaron después en [152](152-restauracion-clave-hmac-beta-b13-20261021.md):22PASS, cinco restauraciones sobre el mismo producto. No sustituye el límite de compromiso de la clave de dominio o rollback a imagen que ignore el campo.
