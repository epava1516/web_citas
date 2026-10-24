# Acta15 — Aceptación técnica local B13

Estado: B13 aceptado técnicamente en local, 2026-10-21. Ocho de18puntos cerrados: B01–B06 y B12–B13. No aceptación beta global ni apertura a usuarios.

Decisión de Codex tras revisión de los siete requisitos locales de [roadmap103](../103-roadmap-beta-clasificados-20261020.md), sus runbooks y las pruebas efectivas. [Matriz literal auditada](../evidencias/b13-local-requirement-acceptance-matrix-20261021.json), [conciliación160](../160-conciliacion-final-beta-b13-20261021.md). Requisitos de personas, sustitutos y cobertura reales para apertura conservan B17/G03/G06/G07.

## Candidata y evidencia

BaseGit920ea36 con cambios locales identificados por huellas, no por HEAD solamente. Runtime726 idéntico al de imagen5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede; retorno66c6d38100555484d9a822c2b2cf292aa85f0c3f576d9a873d4e0cf149724b75. Fuentes/dependencias/kernel nativo/UID comprobados en ambas imágenes. El retorno no incorpora la guardia nueva de correo: exige backend explícito permitido y conserva HMAC activo.

Conjunto final124228-3c690d3d:26PASS/0FAIL/0ERROR/0SKIP,4workers, tres avisos AlwaysEagerIgnored conservados de send_task con worker real. [Auditoría](../evidencias/b13-final-gate-terminal-audit-20261021.json):5restauraciones reales,2caídas de servicios,14drills urgentes,2retiradasES/EN y3testigos de migración. Todas las propiedades relevantes, fuentes actuales, limpieza de servicios anidados/runner/temporales/PIDs y Telegram terminal comprobados.

Incidente de dominio085523:21PASS sin advertencias en otra ejecución,4casos nuevos y17del proveedor/modos previos. Revocar la clave explícita cierra enlaces antiguos y replay, conserva evidencia y permite nueva entrada y nuevo acceso con finalidad auditada; no revalida todo historial derivado. [Auditoría](../evidencias/b13-domain-key-incident-terminal-audit-20261021.json). No afirmar una ejecución única47PASS ni una regresión completa.

El ciclo158 real de aplicación candidata→retorno→candidata verifica once tablas, medios, recibos originales, tres ediciones, tres acciones, seis replays y tres workers cruzados, con18fichas/6fotos/12recibos TCP internos. Nueva firma Django y pin HMAC se conservan durante el runtime. [Auditoría](../evidencias/b13-hmac-mail-rollback-terminal-audit-20261021.json). Sin downgrade de esquema ni cambios en servicios normales.

## Cumplimiento literal local

| ID | Requisito y evidencia comprobada |
| --- | --- |
| L01 | Runbook worker/broker: caída real propia, outbox durable y recuperación/replay idempotentes;26final y141. |
| L02 | Revisión/denuncia/retirada:14drills y2casos ES/EN con estado obsoleto/promociones, pares e historial preservados;26final y144/B06. |
| L03 | Runbooks/ensayos por familia: Fernet activo/readers, Django/firma, revocación HMAC de dominio, PostgreSQL/Django, Redis/Kombu y proxy Caddy;142/148/149/151/154/159. Fuentes de test/locks y compatibilidad runtime comprobadas; no hot reload universal. |
| L04 | DB y medios: cinco pg_dump/pg_restore reales, tres copias cifradas y tres transiciones con lectores/pin; clon sin listener/worker y origen conservado;26final/152. |
| L05 | Antes de exponer: autoridad independiente, derechos reconciliados, sesión/grants inválidos y estado reconstruido; publication_authorized=false. Ledger incorrecto bloquea tres CLI sin efectos;26final/155. Aislamiento de copia/servicios además del flag. |
| L06 | Retorno real158 con HMAC activo, datos/medios/recibos/escrituras y workers entre versiones; configuración de correo compatible obligatoria. |
| L07 | Migraciones: contenido legado no se convierte en romántico, etiqueta seleccionada impide descenso destructivo y upgrade invalida estado anterior; esquema retenido en el ciclo. Tres testigos reales del conjunto26 y estrategia145. |

## Límites que permanecen vigentes

Se acepta el cumplimiento local ensayado de B13. No se aceptan retirada exhaustiva de claves/recifrado, migración automática de todos los bindings HMAC, revalidación de decisiones antiguas, rollover de ledger o recuperación de claves perdidas. Esos mecanismos no se inventan: mantener bloqueadas las operaciones cuya autoridad no esté verificada y no retener un token comprometido para reabrirlas. La preservación del pin durante una rotación Django no es el procedimiento de compromiso de ese pin.

Los runbooks distinguen esas situaciones y sus condiciones de aislamiento/verificación. El censo acotado no autoriza retirar lectores; un aviso simulado no acredita SMTP ni proveedor; una caída antes de consumir no acredita fallo a mitad de tarea o reboot. No garantía de cero interrupciones, custodia/offsite/PITR, identidad humana, canal/guardia/cobertura reales, revisión jurídica o revisión externa independiente.

Personas y operación de destino, proveedores y G01–08 permanecen en B14/B17 según su requisito. B07 conserva el cortoFAIL y900s bloqueado. B00 residual, B07–B11 y B14–B17 pendientes; B15 opcional sin incorporación implícita. B16 debe integrar y verificar la candidata completa; esta acta no lo sustituye ni autoriza publicación/gasto/datos reales.

Negativos, fixtures corregidas y pruebas previas se conservan en sus cortes; sus marcas B13_abierto describen el incremento previo y quedan sustituidas por esta decisión para la aceptación local, sin transformar sus límites o fallos en PASS. Ocho invocaciones Claude V1/consumo anterior preservados; ninguna nueva. No push, proveedor, compra o despliegue externo.
