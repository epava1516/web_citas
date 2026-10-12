# MOD-08 — lectura final sin staging cifrado, 2026-10-12

Usuario autoriza proceder después de la investigación. [Diseño previo y límites](mod08-lectura-fresca-investigacion-20261012.md).
[Evidencia funcional compacta](mod08-lectura-fresca-integrada-20261012.json).

## Cambio y garantía

codec.authenticated_plaintext comparte la máquina existente de frames AES-GCM,
SHA plaintext y EOF con decrypt. Retiene plaintext en TemporaryFile privado y
cierra el stream al salir; respeta max_bytes sin buffer ilimitado en memoria.
repository.read mantiene una lectura física fresca en el mismo punto del flujo;
_HashedBodyReader cuenta/hash bytes físicos mientras se autentican frames. El
codec/scratch puede fallar antes, pero su error se retiene hasta terminar el body,
comprobar tamaño/SHA físicos y tombstone final: fallos físicos preceden al error
criptográfico. Sólo tras TODOS los guards se copia al destino. Cancelación no
se convierte en éxito ni en un drenaje/reintento, y cierra body y scratch.

No se elimina la lectura seleccionada, no se reutilizan bytes de otra fase, no
se modifica formato v1, referencias, claves, contexto, límite, autorización,
comprobaciones del conjunto, replay SQL ni GET de entrega. _verified_ciphertext
sigue disponible para la rotación, donde sí se necesita una copia cifrada estable.
El código entra por una API compartida, sin nueva implementación de criptografía.

| Comportamiento por lectura seleccionada | Antes | Ahora |
| --- | ---: | ---: |
| Temporales privados | 2 (ciphertext + plaintext) | 1 (plaintext) |
| GET S3 (tombstone/objeto/tombstone) | 3 | 3 |
| Momento de publicación | tras integridad completa | tras integridad completa |

La eliminación de una escritura/lectura de ciphertext es concreta; el p95 aún
no está medido para este cambio. También se empieza la autenticación antes de
terminar el digest físico: no atribuir igualdad de trabajo interno a entradas
corruptas. Se conserva rechazo y prioridad de errores contrastados; las operaciones
sobre el temporal eliminado ya no pueden producir un error de ese recurso.

## Verificación

- 108 pruebas locales iniciales PASS; después del caso adicional max_bytes,
  184 pruebas codec/repository/transport PASS y 1 nodo DB reservado para integración.
  Incluyen RustFS real y contrastes mock de errores/contexto/truncamiento/EOF,
  digest, purga, fragmentación, scratch create/write/seek, cancelación y destino.
- PostgreSQL17 propio, LOGIN runtime real no propietario, RustFS y Caddy propios:
  25 PASS, 0 fallos/errores/skips, 1 test Celery ajeno excluido, 314.783 segundos.
  Cadena/head intacto con fuente alterada, ACL y proof expiry; sello válido con
  corrupción externa; paquetes grandes S3, cambios de imágenes/originales,
  revocación/archivo/grant/restauración, entrega Caddy y replay de un solo uso.
- Ruff, docs y 120 tests rápidos de instrumental PASS.
- Primer intento de transporte se interrumpió antes de resultados para reservar
  el nodo DB al entorno propio. Primera ejecución restringida: 103 PASS/1 FAIL,
  assertion histórica esperaba 2 temporales; se ajustó a 1 y se conservó el fallo.
  No se quitó ningún rechazo por corrupción/revocación para hacer pasar el gate.

El gate de integración registra parent SHA140d627 más cambios sin commit y sus
fuentes idénticas antes/después; los hashes del JSON identifican el código exacto
que después se incorpora al commit. Todos los datos son sintéticos. Fuentes sin
cambios durante integración, PG retirado y ausencia de contenedores object-tests
comprobada. Sin modificación de producción ni permisos/proveedores externos.

RAM host limitada a4GiB de espacio de direcciones, CPU0; PG CPU1/1CPU/512MiB,
RustFS0.5CPU/512MiB y Caddy0.5CPU/128MiB, servicios sin swap. RSS máximo de hijos
325108KiB no es pico agregado. Los límites y evidencias del ciclo HTTP se
registrarán por separado, sin perfiladores durante measure. No aceptación global/N3.
