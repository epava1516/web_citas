# MOD-08 — investigación de lectura final fresca, 2026-10-12

Código observado: ee42079. [Resultados compactos](mod08-lectura-fresca-investigacion-20261012.json).
Dos hipótesis acotadas, sin cambio en producción ni runners HTTP. Se usa el codec
AES-GCM y ObjectRepository reales con transporte EN MEMORIA: prueba de lógica y
contraejemplo sintético, NO RustFS/PostgreSQL real, N2, capacidad ni aceptación.
Scripts/datos completos y hashes bajo artifacts/vps-preparation, sin claves,
payloads ni ciphertext versionados. Ningún servicio creado; sin limpieza Docker
necesaria. Se conservaron dos errores de preparación anteriores al experimento,
registrados en JSON; no fallos de producto.

## Reutilizar la lectura temprana: descartado como equivalente

Contraste actual: verify seleccionado → comprobaciones restantes del conjunto →
read seleccionado → entrega. Candidata: read seleccionado durante comprobación
del conjunto → comprobaciones restantes → entrega de bytes retenidos.
Se inyectó purga o corrupción tras la primera fase. Con el flujo actual se
rechazaron ambas y salieron cero bytes; con reutilización temprana se entregaron
los 24 bytes guardados en ambos casos. Sin mutación ambos entregan lo mismo.
El resultado demuestra una diferencia de ventana de frescura, aunque el mock no
prueba el funcionamiento de purga real S3. Añadir sólo un tombstone final cubre
purga, pero NO corrupción del ciphertext. HEAD/ETag no sustituye silenciosamente
la lectura/hashing/autenticación vigente ni prueba bytes almacenados intactos.

## Otra candidata: evitar staging cifrado en la lectura final

La lectura actual repository.read usa _verified_ciphertext: primero escribe todo
el ciphertext en tempfile, verifica tamaño/SHA y tombstone; después decrypt
escribe plaintext autenticado en otro tempfile y lo copia al destino.
Un prototipo aislado mantiene la lectura FINAL en el mismo lugar y usa
_HashedBodyReader → máquina AEAD existente → tempfile plaintext privado. Retiene
el error del codec, termina la lectura/digest físicos, verifica tombstone final,
y sólo entonces publica los bytes o expone el error criptográfico. Se elimina
el tempfile cifrado, no la lectura física ni la validación del conjunto.
No usa BytesIO sin límite para el staging: el límite vigente del codec es 1GiB,
por lo que un buffer de ese tamaño sería una regresión respecto al almacenamiento
acotado en disco. La configuración de entrega mantiene su límite propio 8MiB.

### Contraste sintético de escrituras, no rendimiento HTTP

| Métrica, objeto plaintext de 2097159 bytes | Actual | Prototipo | Diferencia |
| --- | ---: | ---: | ---: |
| Bytes escritos a temporales privados | 4194706 | 2097159 | 2097547 menos, aproximadamente 50% |
| Lecturas físicas del body, incluido EOF | 4 | 4 | ninguna |
| Comprobaciones de tombstone | 2 | 2 | ninguna |
| Bytes entregados | 2097159 | 2097159 | ninguna |

Contador de write en temporales, no bytes de disco persistidos ni fsync/CPU/p95.
No se midió tiempo: no convertir el ahorro de escritura en ahorro del request.
Afecta la lectura seleccionada; el resto del conjunto y la segunda transacción
GET continúan comprobándose. Un JSON sin binario seleccionado no recibe este ahorro.

Dieciséis escenarios comparan clase/mensaje de resultado, tamaño y SHA256 de salida,
secuencia física exacta, orden de guards y cierre de body: sin cambios,
fragmentación, magic, tag, truncamiento, trailing, contexto, clave, grow, tamaño,
digest, magic+digest, magic+IO tardío, purga inicial, purga final y contexto+purga.
Todos coincidieron; todos los fallos dejaron destino vacío. Los JSON compactos
conservan hash y conteo de secuencia; los completos siguen locales.

## Límites pendientes antes de adoptar

- Prototipo invoca funciones privadas del codec: diseñar API explícita compartida,
  sin una segunda implementación de criptografía.
- Fallos del tempfile, límites y disco lleno: el orden interno cambia y puede
  introducir errores que antes no ocurrían si el digest físico ya era inválido.
  No afirmar equivalencia general a partir de 16 escenarios.
- Comparar max_bytes, excepciones del destino y cancelación/KeyboardInterrupt;
  confirmar cero salida previa a todos los guards y cierre de recursos en fallos.
- Integración RustFS propia con corrupción rehashed, purge durante body y cierre;
  integración LOGIN PostgreSQL/Caddy de la descarga con negativas del conjunto.
- Sólo después de gates, medida limpia con el mismo contrato. No se ejecutó otra
  medida especulativa ni se cambió un criterio para hacer pasar la candidata.

El prototipo confirma una eliminación física concreta de trabajo temporal y
preserva los escenarios contrastados; no se ha incorporado al código de aplicación.
La reutilización temprana queda rechazada. La lectura final streaming es la
siguiente candidata acotada a verificar, sin promesa de alcanzar el p95.
