# Paridad e integridad canónica dentro de Docker

Imagen `web-modelos-cr09-native:20261016`, ID `bb8bc8e5497c`, fuente del cambio `0c86d9f` y hashes del [recibo de construcción](cr09-docker-native-terminal-20261016.json). Se ejecutan sin modificar `test_canonical_kernel_loader.py`, `test_rights_native_canonical_equivalence.py` y `test_canonical_stack_gate.py`: **118 PASS en 11,60 s**, cero fallos, errores o skips. [Recibo por caso e identidad](cr09-docker-kernel-parity-terminal-20261016.json).

Los controles cubren validación y bytes del encoder, números extremos/no finitos, Unicode, tipos no admitidos, mutación/orden de diccionarios, ciclos/profundidad/recursión y callbacks; además manifiesto/ABI/hash alterados, symlinks/FIFO/límites de archivo, carga concurrente, sellos inmutables, sustitución de callable/binario, inicialización fallida y fork. Algunos negativos fuerzan explícitamente la referencia o un loader sintético: son controles de esa rama, no evidencia de ejecución nativa en esos casos. Los fixtures que requieren nativo cargaron el artefacto real y no se omitieron.

Se usan Python y dependencias de aplicación de la imagen, UID10001 y raíz de sólo lectura, red none, dos CPU/1536MiB sin swap, pids128 y tmpfs256MiB. Sólo pytest9.1.1/pluggy1.6.0/iniconfig2.3.0/packaging26.3/pygments2.21.0 se copian del entorno congelado a un montaje separado de herramientas; no se monta el site-packages completo ni se instalan herramientas en la imagen. Autoload de plugins desactivado, configuración pytest vacía y Django inicializado sin DB; DB deliberadamente127.0.0.1:9. No prueba integración PostgreSQL ni recorridos de derechos.

Un contenedor posterior comprueba hashes de los tres tests dentro de la imagen iguales al host y reafirma native-sealed/binario2caa578c…. JUnit bruto, log y adaptador conservados en `artifacts/cr09-docker-kernel-parity-20261016/`. Contenedores de ejecución y testigo ausentes, comprobados independientemente. Sin cambios de aplicación ni nuevo p95.

Fallos del instrumento preservados: primer intento no importó pytest por permisos750/640 en el montaje de herramientas; se corrigió sólo la copia a755/644. Segundo intento pasó118casos11,61s pero no recuperóXML desde tmpfs después de detenerse. Se conserva log/resultado como fallo de exportación; la ejecución final exporta XML antes de salir. No se cuentan ejecuciones como casos únicos ni se ocultan los fallos.

Esto amplía el smoke de construcción/PG/migraciones/health, sin aceptar CR09 ni N3. Faltan recorridos pertinentes y capacidad de esta imagen; no se le atribuye el p95 del host.
