# N02A — ensayo pareado de metadatos y lectura de imágenes

25 de octubre de 2026. N00/N01aceptados2/13;N02yN06abiertos. [Investigación por fuentes](evidencias/n02-investigacion-coste-20261025.json) propone dos hipótesis sin adopción. Este lote caracteriza la segunda: `_verify_current_images` usa image_content por declaración; existe image_contents con metadatos por lote. No se modifica el llamador de aplicación ni se acepta MOD09 por comparar esas primitivas.

Grafo actualizado antes del análisis:1952fuentes, ASTprevio y semántica359/341/README/vista17 conciliados y SHAcomprobados. N06B tiene referencia real encolada, pero no constituye una base de exportación MOD09. Mantener objetivos de cobertura p95≤2s y entrega JSON/binaria por paquete p95≤5s, FAIL y excepción provisional en su ámbito original.

## Datos y selección previa

Instrumento `tests/test_current_image_metadata_benchmark.py::test_current_image_metadata_paired_reference`. Un caso con dos cohortes secuenciales de sujetos sintéticos distintos, usando capacity_target_fixture.populate sin reducir sus dimensiones:1500revisiones/~16MiB de campos JSON seleccionados y16WebP reales/~64MiB por sujeto, tolerancia1% del generador existente. Píxeles sintéticos decodificados/sanitizados, originales y derivados iguales según esa receta, sin bytes añadidos para simular tamaño. No datos reales ni proveedores.

Ambos sujetos coexisten en PostgreSQL de prueba. El generador y preparación de archivos quedan fuera del reloj; almacenamiento local privado de photo_environment, objetos desactivados. Esa fixture conserva su preparación eager original, no es una medida de colas o publicación. Se comprueba el número real de revisiones/fotos y el volumen de cada cohorte antes de medir. Esto no crea ni acredita un caso de derechos autorizado o exportación cerrada: mide sólo metadatos/locks y lectura de archivos bajo un parámetro person conocido del arnés.

Por sujeto: seis rondas, ambas primitivas en cada una, con orden alterno single→bulk/bulk→single. Primera pareja separada; cinco parejas posteriores para mediana/rango.24observaciones totales, cada una16lecturas completas. Orden de declaraciones fijo e inverso al ordenPK de las fotos, idéntico para ambas primitivas. Sin p95/p99 ni concurrencia de los dos sujetos; no equivale al ensayo contractual de dos sujetos concurrentes.

## Instrumentación y criterios antes de medir

Dentro de una transacción PostgreSQL real por observación, ejecutar la misma secuencia de IDs y verificar orden, SHA256 y tamaño de **todos** los contenidos. Leer/hash cada archivo en cada llamada: no sustituir bytes por caché de aplicación, digest precalculado o stub. La envoltura de _read_image_blob llama siempre al método nativo y sólo cuenta aperturas/bytes devueltos. La caché del sistema operativo puede servirlos; no se fuerza frío ni se afirma lectura de disco físico en cada repetición.

Medir pared instrumentada y CPUdelhilo de lectura+verificación, consultas/ejecuciónSQL. BEGIN/COMMIT de la transacción, creación de datos y comparación de filas posteriores quedan fuera del reloj. Misma instrumentación, sujeto, filas, archivos, orden y proceso en las dos formas. DEBUG=False en ambas; IDs de entrada como strings, igual que las declaraciones del llamador. Es comparación de mecanismos ya existentes, no tiempoHTTP ni antes/después de un cambio integrado.

Presupuestos de validez/coste:16lecturas completas y mismo volumen/manifest digest por observación; cero diferencias de orden/contenido y cero mutaciones de filas; consultasSELECTesperadas48(single=3porimagen) y3(bulk) conforme al código y las pruebas existentes. Si no se cumplen, conservar fallo y atribuir antes de decidir candidato. El criterio temporal comparativo354 exige no empeorar la misma etapa; registrar mediana/rango y cualquier inconclusión, sin elegir sólo la pareja favorable. No hay SLO temporal nuevo ni objetivo de reducción porcentual inventado.

No persistir SQL, parámetros, cuerpos, UUID de sujetos/fotos/blob o imágenes. Propiedades sólo etiquetas de cohorte/método/ronda, conteos/bytes, tiempos finitos y digest agregado de contenidos sintéticos. Conservar variantes sin mejora y su variabilidad.

## Oráculos existentes y ejecución

Además del caso nuevo, seleccionar los cuatro testigos originales de tests/test_rights_image_contents_bulk.py:

- test_sixteen_images_four_calls_keep_sixty_four_physical_reads
- test_bulk_fresh_metadata_is_three_queries_and_preserves_single_bytes
- test_bulk_rejects_mapping_changed_during_actual_blob_lock_wait
- test_reverse_bulk_and_single_readers_complete_with_real_pg_locks

Cinco casos esperados,0SKIP en selección explícita. Los testigos pequeños son regresión de frescura, pertenencia, duplicados/vacío, orden y espera de locks reales; sus tiempos no se mezclan con la cohorte grande. Cambio físico tardío/rollback de auditorías y restantes negativos seguirán siendo obligatorios antes de integrar un candidato en su llamador; estas primitivas no prueban por sí solas equivalencia del orden de errores/autoridad de todo el flujo.

Runner oficial focused serial --workers1, PostgreSQL17/Redis7.4 propios y librdbv2.4.0. Techo900s por comando como protección, sin cuotas dedicadas ni carga/proxy/TCP/objetos/worker de exportación. Revalidar propiedadPG antes de crear datos. El caso de rendimiento es diagnóstico explícito; SKIP fuera de selección directa no cuenta como coberturaPASS. No recortar QA existente ni convertir duraciónpytest en latencia de aplicación.

## Salida y límites

Antes de ejecutar: AST nuevo y semántica de este protocolo, verificación y congelación completa de fuentes/dependencias/migraciones/instrumentos/grafo/imágenes. Después: comprobar cinco casos/24muestras, consultas/lecturas/bytes/orden/digests y filas intactas, recursos propios retirados, fuente sin cambios hasta auditoría y Telegram terminal entregado.

Publicar tabla single/bulk con tiempos medidos, diferencia absoluta/porcentual de **esta etapa** cuando sean comparables y variabilidad/muestras. No trasladar ese porcentaje a descarga completa. Si el mecanismo aporta ahorro y se adopta después, prerregistrar primero el candidato de llamador, sus condiciones post-lock-wait y regresión adversarial; completar medición de entrega/cobertura correspondiente. Ninguna lectura, hash, comprobación de autoridad/retirada o un uso puede eliminarse para alcanzar2s/5s. N02permanece abierto.
