# B13 — Matriz vigente de requisitos y autoridad de recuperación

Estado: B13 aceptado técnicamente en local por acta15; ocho de18puntos cerrados. Esta matriz distingue requisitos literales del [roadmap103](103-roadmap-beta-clasificados-20261020.md) de límites y controles de apertura; no sustituye el objetivo completo B00–B17.

| Requisito literal B13 | Evidencia local vigente | Qué falta / límite |
|---|---|---|
| Runbook caída worker/broker |141: caída real de servicios propios, outbox PostgreSQL y recuperación idempotente | Dos casos repetidos PASS sobre candidata actual; entrega final usa simulador explícito, no proveedor real |
| Revisión, denuncia y retirada urgente |144/B06: revisión previa, restrict ES/EN y superficies públicas con proyección obsoleta | Dieciséis casos urgentes repetidos PASS; guardia/personas/cobertura reales pertenecen a apertura |
| Rotación de secretos |142/148–154: readers Fernet, firma Django/HMAC separado, DB/Django, Redis/Kombu, proxy Caddy | No retirar readers por una muestra; no prometer migración de bindings ante clave HMAC distinta o comprometida |
| DB+medios restaurados en aislamiento |152: cinco restauraciones reales, tres con firma nueva/pin y lectores anteriores, origen intacto | No listener/worker sobre clon; custodia/offsite/PITR e infraestructura real no acreditados |
| Derechos/sesiones/grants/publicación antes de exponer |144/152: ledger independiente, sesión inválida, grants purgados, reconstrucción de publicación y publication_authorized=false | Mantener aislamiento hasta comprobar todos los pasos; el flag no sustituye aislamiento externo |
| Rollback de aplicación |158: candidata5a0751c1→retorno66c6d381→candidata, HMAC activo, recibos/once tablas/medios/escrituras y tres workers verificados | Correo explícito permitido obligatorio en ambos; histórica80d66b10 sigue incompatible. No downgrade ni aceptación de infraestructura real |
| Estrategia de migraciones |145: no bajar a alfa eliminando content_contract; guardia de etiqueta y upgrade real | Retorno conservando esquema; comprobar código candidato, no borrar filas ni manipular django_migrations |
| Personas, sustitutos y cobertura | B17/G03/G06/G07 | Pendiente externo explícito; no se acredita con fixtures o pruebas locales |

## Autoridad de claves de ledger

RecoveryLedger tiene una pareja propia de cifrado/firma; su identidad de checkpoint es ledger/sequence/head. La implementación no declara protocolo de rollover de claves entre streams. No sustituir valores de entorno sobre una cadena existente creyendo que eso recifra, resigna o reconcilia historia. Los30casos codec/store de153 comprueban rechazo de claves/checkpoints incorrectos, integridad antes de descifrar y archivos/permisos; el caso de independencia demuestra que cambiar claves de aplicación no altera esa autoridad.

Ensayo nuevo: dos casos PostgreSQL, claves incorrectas de cifrado/firma por separado. Con un recibo real y autoridad persistida propia, check_recovery_ledger, apply_recovery_ledger y clear_recovery_sessions deben fallar antes de cambiar tablas de reconciliación, sesiones o bytes de ledger/medios. Sin JSON parcial y manteniendo RECOVERY_MODE. Restablecer las claves correctas retenidas debe permitir preflight de la cadena original sin aplicar efectos. No es un rollover ni recuperación de una clave perdida.

Si las claves de la cadena no están disponibles o no son confiables, mantener recuperación aislada y preservar los artefactos; no fabricar otro checkpoint para que pase. OP005 exige aislamiento, revocación/rotación según alcance, reconstrucción confiable y verificación antes de reabrir. No obliga a afirmar que un software descifra sin clave ni autoriza aceptar una autoridad nueva sin continuidad diseñada. Custodia, elección de cadena de destino y respuesta de incidente real requieren sus controles de apertura. El rollover permanece como limitación técnica explícita, sin inventar implementación.

## Verificación focal preparada

Selección prevista52casos:2nuevos de autoridad CLI,1preflight,1comando de recuperación,30codec/store,2caída worker/broker,2retirada beta y14drill urgente. Se verifican sobre fuentes congeladas y PostgreSQL propio, con aislamiento de broker, medios y servicios auxiliares; casos de codec/filesystem no reciben crédito de DB por compartir runner. No se acredita proveedor ni identidad humana reales. Conservar negativos, verificar limpieza y Telegram terminal.

No se cierra B13 por esta conciliación ni se convierte cada límite externo en una obligación de implementación local. El pendiente de rollback de la candidata y la revisión de la evidencia final siguen visibles; B07 conserva su FAIL y B16 exige una candidata integrada con su alcance común.

## Resultado verificado

070837:50PASS/2FAIL de preparación y3avisos AlwaysEagerIgnored en continuidad real. La selección de finalidades se corrigió sólo en el test nuevo a media; ninguna guardia de producto cambió. 071731:2PASS sin advertencias. Ambas claves erróneas bloquean las tres CLI sin efectos y las claves retenidas verifican la cadena original. Son52casos únicos por composición50+2, no una ejecución común verde. [Auditoría](evidencias/b13-ledger-authority-terminal-audit-20261021.json): fuentes congeladas, igualdad del resto de fuentes, única sustitución de fixture, limpieza de PostgreSQL/Redis/temporales/PIDs y Telegram terminal comprobados.

Próxima acción B13: preparar y ensayar un retorno compatible con la configuración HMAC activa; la pareja145–146 anterior no adquiere esa compatibilidad por estos resultados. No hay rollover implementado ni aceptación B13/global.

## Contraste real de imagen histórica con HMAC activo

Candidata66c6d381 construida desde fuentes funcionales de071731:726archivos comprobados dentro de la imagen, dependencias idénticas a la base histórica. Retorno histórico80d66b10 posterior a la corrección de grants:724archivos verificados. Tres procesos Docker reales candidata→histórica→candidata, UID10001/kernel nativo sellado/red deshabilitada y misma configuración sintética de Django/HMAC. Ambos productores report/rights cambian de firma en la histórica, que ignora SAFETY_HMAC_KEY; al volver a candidata ambos testigos originales coinciden. No se modificó ni reactivó una clave antigua. [Evidencia](evidencias/b13-hmac-rollback-compatibility-20261021.json). Los contenedores de ensayo se eliminaron y ambos avisos terminales se entregaron.

Resultado: incompatibilidad demostrada; no aceptación del rollback. No hubo ciclo DB/medios/HTTP en este contraste y no se extrapola el ciclo145–146. La diferencia de fuentes comprende ocho módulos de aplicación/configuración de HMAC y dos herramientas de inventario; aplicar todas esas diferencias a la histórica reproduciría la misma aplicación candidata y no demostraría retorno de código. No presentar dos builds de esa misma aplicación como versiones funcionales distintas. Falta un destino de retorno compatible y su ensayo integrado; mientras no exista, la histórica no es destino admisible con HMAC activo. Este pendiente local permanece separado de custodia/personas B17 y no detiene los frentes independientes B07–B11.

## Estado posterior al ciclo158

El retorno compatible HMAC de la candidata con guardia de correo queda verificado por [158](158-retorno-hmac-correo-beta-b13-20261021.md). La siguiente acción de preparar/ejecutar ese contraste anotada arriba corresponde al corte anterior y queda sustituida: falta la conciliación literal final de B13 sobre evidencias y límites actuales, sin extender aceptación al rollover no implementado o a los controles de apertura B17. Mantener7/18hasta emitir su aceptación técnica con matriz revisada.

## Resolución posterior

La conciliación literal final está resuelta por [160](160-conciliacion-final-beta-b13-20261021.md), [matriz auditada](evidencias/b13-local-requirement-acceptance-matrix-20261021.json) y [acta15](actas/15-beta-b13-aceptacion-local-20261021.md). Sustituye el pendiente de revisión/retorno de los cortes anteriores. Los límites de retiro/recifrado, rollover, recuperación sin clave y apertura real siguen explícitos; no hay una aceptación universal de recuperación por compromiso.
