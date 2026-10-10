# MOD-08 — generación asíncrona de portabilidad

Contrato HTTP: `POST rights_portability_export` valida autoridad y referencias vigentes,
crea o recupera un trabajo durable y responde **302** a su URL canónica. No crea la
exportación dentro de la petición. La misma clave y los mismos inputs recuperan el mismo
trabajo; cambiar actor, versiones, revisión, cobertura o motivo con esa clave se rechaza.
GET de preparación y estado no genera datos ni responde/cierra el expediente.

El trabajo guarda referencias y versiones originales de sesión/MFA, HMAC de inputs y
motivo cifrado. Broker Celery recibe sólo el UUID del trabajo; no contiene motivos,
selección, imágenes, valores personales ni tokens de descarga. La proyección de broker
vivo e histórico valida el esquema y admite sólo UUIDs del ámbito autorizado; los parsers
de orígenes siguen siendo puros y reciben ese ámbito explícitamente.

Worker reclama lease durable y bloquea el trabajo durante una transacción. Usa la misma
función `generate`, que mantiene locks, autoridad/prueba/fuente frescas y validación de
selección/cobertura, firma e imágenes. Sesión/MFA originales nunca se sustituyen por las
versiones actuales; una revocación mientras espera también impide la generación. Export,
acciones de dominio y éxito del trabajo se confirman juntos. Caída antes del commit
revierte todo; redelivery no vuelve a generar un trabajo exitoso.

Estado y progreso por fase: espera, validación/generación, éxito, rechazo por cambios,
fallo técnico. No se inventa porcentaje. Sondeo HTMX local ES/EN con URL GET y enlace
manual canónicos para navegar sin JavaScript. Estado privado restringido al actor
original con autoridad actual y las mismas versiones originales; sin valores/motivo.

Recuperación: `reconcile_portability_export_jobs` cada 60s reenvía pendientes no despachados
o estancados y recupera leases vencidos de 10min. Hasta tres intentos técnicos, espera
30s × intento; fallos de autoridad/dominio no se reintentan. TTL de selección/cobertura
limita el trabajo y el reconciliador purga el motivo de trabajos vencidos aun sin worker.
Motivo vacío en todo terminal; referencias/estado mínimos durables preservan idempotencia
y permiten inventario de derechos por persona y cuenta. RecoveryAwareTask conserva el
bloqueo de ejecución durante recuperación; epochs restaurados/invalidados se revalidan.

`generate` continúa siendo síncrono para consumidores internos y mantiene sus guards.
Pruebas HTTP previas pasan ahora por 302 → trabajo → generación → exportación y conservan
las pruebas de payload, descarga, corrupción, replay y privacidad.

Capacidad: **generar ≤120s** sigue significando encolado → copia completa lista, incluyendo
espera de cola. Un 302 rápido no acredita ese objetivo. N3 con worker/broker reales y dos
casos objetivo, RSS/memoria/CPU/almacenamiento originales sigue pendiente; esta pieza no
acepta CR09 ni el contrato integral.

## Evidencia local

Primera N2 `20261010-122659-14afabde`: 140 casos, 121 correctos y 19 fallidos, cero skips,
723.789s JUnit. Fallos de los parsers históricos al inferir un ámbito de trabajos desde
metadata sin persona; corregido pasando job_ids explícitos desde el consumidor autorizado.
Worker/broker reales, Chromium ES/EN, concurrencia/replay/revocación, guards síncronos e
inventarios originales dentro de los 121 correctos. Fuentes congeladas y recursos
PG/Redis/tmp retirados. No es PASS ni aceptación; N2 correctiva pendiente.

N2 correctiva final `20261010-130443-c476a607`: 3 PASS, 0 FAIL, 0 skips, 57.21 s. PostgreSQL/Redis reales, publicación UUID y proyección privada positivas persona/cuenta; transporte/eager y shards comprobados. Fuentes congeladas; limpieza real confirmada. Causa del harness: eager heredado; fijado False explícitamente en prueba broker. Evidencia complementaria: tercera N2 23 PASS (worker real, revocación tras espera PG, retries, lease, HTTP ES/EN); segunda N2 109 PASS (orígenes históricos, HTTP previo, Chromium ES/EN/sin JS, binarios); primera N2 export races/inventarios originales PASS. Terminales negativos anteriores se preservan. Integración conjunta y N3 capacidad siguen pendientes; no aceptación integral.
