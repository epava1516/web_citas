# B13 — Censo de columnas cifradas y dependencias HMAC, 2026-10-21

Estado: censo acotado verificado en local; no retirada de claves ni aceptación B13. Siete de18puntos cerrados; B13 sigue abierto. Continúa [142](142-rotacion-secretos-beta-b13-20261021.md), sin retirar claves ni modificar datos reales.

## Registro de esquema y productores

Registro explícito de54columnas cifradas: MFA de core.User, cuerpos/campos safety y rutas cifradas de medios. La comparación con modelos cargados reconoce la convención encrypted_/_encrypted y falla ante columna nueva con esa convención, ausente o duplicada. Cualquier formato o campo cifrado fuera de esa convención requiere revisión y clasificación explícitas; no se promete detección semántica automática. Dos campos RightsExportImage/Part admiten Fernet legacy o referencia wmblob1; se inspecciona sólo el sobre de la referencia. No verificar contenido, existencia ni autoridad de un objeto por descifrar su descriptor.

scripts/secret_dependencies.py localiza ocho productores HMAC directos de la aplicación y rechaza productores nuevos, alias no clasificados, salts dinámicos o uso explícito de otra clave. [Inventario estático](evidencias/b13-direct-hmac-dependencies-20261021.json). El registro distingue:

| Productor | Efecto de cambiar SECRET_KEY | Respuesta local |
| --- | --- | --- |
| limited / rate-window | Cambia namespace de límites | No presentar los nuevos contadores como continuidad del historial |
| token_user_state | Tokens de cuenta anteriores dejan de coincidir | Revocar/reemitir mediante flujo normal; no copiar huella nueva sobre token anterior |
| recovery_digest | Códigos de recuperación MFA anteriores no coinciden | Regenerar tras autenticación/MFA frescas, sin exponer códigos viejos |
| phone_start y phone_confirm | OTP pendientes dejan de verificar | Reiniciar desafío válido, sin confirmar teléfono por error |
| synthetic_signature | Firma sintética anterior no coincide | No aceptar evento viejo ni tratar simulación como pago real |
| crypto.digest | Recibos, deduplicación y huellas de varios dominios | Censo de consumidores, revocación/reemisión por dominio antes de cambiar firma |
| rights.fingerprint | Aprobaciones, bindings y evidencia de derechos | No rehash ciego de evidencia inmutable; mantener historial y usar nuevas revisiones autorizadas |

Ocho puntos no equivalen al censo transitivo completo de todos los consumidores. Django/terceros y sesiones/firma del framework conservan tratamiento separado; la sesión anterior fue probada en142. Un digest SHA256 sin clave, como AccountToken.digest del token aleatorio, no se equipara a AccountToken.user_state producido por HMAC.

## Censo privado de valores actuales

Comando administrativo preparado:

```sh
.venv/bin/python manage.py encryption_key_inventory --inspect-ciphertext --max-cells 1000
```

No ejecutarlo contra datos reales como parte de este ensayo. La opción explícita reconoce lectura de ciphertext privado; no autoriza acceso que la cuenta DB no tenga. No hay endpoint, scheduler, proveedor ni operación de retirada. PostgreSQL y transacción propia REPEATABLE READ READ ONLY; rechaza transacción heredada/autocommit desactivado, fija statement_timeout5s por sentencia y sanea errores sin JSON parcial.

Recorre valores no vacíos incluso si su fila está caducada o purgada lógicamente: la necesidad de descifrado no desaparece por ese estado. Usa managers base del alias de conexión actual. Clasifica por familia MFA/safety y por clave activa o posición de clave anterior, o ilegible. Las posiciones son relativas a la configuración de esa invocación; no son IDs permanentes de clave. Si la configuración cambia durante el censo, se rechaza el informe.

Por defecto inspecciona hasta1000celdas en total, máximo configurable10000; cada ciphertext debe tener como máximo256KiB medidos en SQL mediante OCTET_LENGTH. Los mayores se cuentan como oversized_unmeasured sin descargarlos al proceso. Los valores elegibles que exceden el presupuesto se cuentan como not_sampled. No interpretar una muestra parcial como censo completo. El coste sobre tablas productivas grandes no está aceptado ni se programa una frecuencia automática.

La salida contiene nombres de modelos/campos y agregados; nunca claves, ciphertext, plaintext, UUID ni contactos. Descifra temporalmente para autenticar sobres, sin exportar contenido; no se promete borrado seguro de memoria Python. No ejecuta servicios de dominio, cambia autorización ni reescribe auditoría. Que un sobre se descifre no prueba validez semántica ni vigencia del contenido.

RecoveryOutbox.encoded_record se cuenta sólo como JSON opaco: su cifrado/firma de ledger son independientes y no se intentan leer con safety. Objetos/tombstones, logs y orígenes Redis retenidos, backups y ledger externo siguen sin medir. retirement_authorized siempre es false, también con todas las columnas vacías o todas bajo activa: ese estado no acredita ausencia de copias anteriores.

## Preparación de verificación

Selección prevista36casos,4workers:14PostgreSQL del censo,6del registro HMAC y16de transición de claves existentes. Sin cambios en cipher, cifrado/desplegado anterior o claves reales. Casos de censo: esquema vacío/readonly, claves de familias distintas, activa/anterior/ilegible, rutas de medios, tamaño/budget parciales, referencia de objeto sólo en DB, deriva de esquema/configuración, transacción heredada, error DB/conexión/configuración sin datos ni salida parcial y CLI explícita. Los sobres de referencia de prueba no se presentan como objetos físicos válidos. RustFS real corresponde a los casos de transición existentes.

Antes de verificar se refresca grafo por las fuentes/documento afectados; las fuentes quedan congeladas hasta la salida terminal, limpieza y aviso Telegram. Conservar negativos. El siguiente criterio B13 permanece: inventario transitivo de huellas y política de revocación/revalidación, retención externa y procedimientos de otras clases de secreto, restauración/retirada/rollback. Este comando no los sustituye.

## Resultado vigente

033513-5fb473ba:36PASS/0FAIL/0ERROR/0SKIP,4workers,67,235sJUnit.14casos del censo,6del registro HMAC y16de transición. [Auditoría terminal](evidencias/b13-key-inventory-terminal-audit-20261021.json): fuentes actuales, cuatro colecciones idénticas, contenedores/temporal/procesos del runner ausentes y TelegramPASS confirmados. Los casos RustFS de transición conservan su limpieza propia verificada; los de referencia sólo en DB no reciben crédito de almacenamiento físico.

Ningún producto existente cambió respecto al corte de transición142: sólo se añaden módulo/registro/CLI del censo y comprobador estático. PostgreSQL comprueba READ ONLY y restauración del estado del llamador. Clasificación validada con claves distintas por familia, valores actuales/anteriores/ilegibles y rutas de medios; payloads y filas anteriores intactos, sin exportar claves, UUID, ciphertext o contenido. Tamaño y presupuesto mantienen pendientes explícitos. Deriva de esquema/configuración y errores DB/conexión/clave no devuelven informe parcial.

El informe conserva retirement_authorized=false aun con base vacía. RecoveryOutbox.encoded_record y archivos externos no se declaran descifrados. Ocho productores HMAC directos concuerdan con fuente actual; sesiones del framework y consumidores transitivos siguen fuera del censo estático.

Siguiente acción B13: completar consumidores transitivos de crypto.digest/rights.fingerprint y su revocación/revalidación, y ensayar los procedimientos restantes de claves/credenciales, restauración, retirada urgente y rollback del contrato beta. La retirada de claves antiguas requiere cerrar la retención externa correspondiente; no borrar o recifrar auditoría inmutable para vaciar contadores. Siete de18puntos cerrados; B07FAIL y B13abierto.
