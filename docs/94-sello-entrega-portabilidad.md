# Sello de entrega de portabilidad — diseño, no adoptado

Estado: **diseño propuesto, sin implementar ni aceptar** (2026-10-10, Claude principal MOD-07). Origen: [perfil completo a escala](evidencias/capacidad-perfil-caso-completo-20261010.json). Se aplicará solo si, tras las equivalencias exactas, una descarga válida sigue por encima de 5s p95 en el escenario objetivo, y solo con las pruebas de completitud y la aceptación propias descritas aquí. Seguimiento: [seguimiento17](17-seguimiento-desarrollo.md).

## Problema medido

Tras cerrar el expediente, cada descarga de un paquete (≤8MiB) ejecuta la validación completa de la exportación: recarga y digest del origen (17,3MB), revalidación de evaluación, selección, imágenes y cobertura, recálculo de las 1.509 páginas auditadas, reproyección del JSON de 16MiB y reconstrucción de los paquetes de 64MiB de imágenes. Con un caso y sin concurrencia cuesta ~9–10s por descarga; el objetivo es p95 ≤5s con dos expedientes simultáneos y ≥20 descargas por caso y variante.

## Garantía que se conserva

La descarga solo entrega bytes si, en la misma transacción que sirve la respuesta:

1. el recibo, la exportación, la prueba, el cierre y la autoridad siguen vigentes (comprobaciones actuales, sin cambio);
2. el **origen actual** (base de datos, binarios y, cuando aplique, Redis) es idéntico al que fundamentó la exportación: segunda lectura fresca completa y comparación de digest, como hoy;
3. **ninguna evidencia ni artefacto** ligado a la exportación ha cambiado desde que la cadena completa se validó por última vez;
4. el paquete servido descifra a los bytes exactos registrados.

Hoy el punto 3 se demuestra **re-derivando** todo. El sello lo demuestra **comparando digests** de todo lo que la re-derivación leería, calculados cuando la cadena completa se validó en el cierre.

## Sello

Fila nueva ligada uno a uno al cierre (`RightsPortabilityClosure`), escrita en la misma transacción del cierre tras la validación completa:

- versión de reglas: hash de las fuentes de los módulos de validación de portabilidad, la versión de Django y la configuración pertinente (mismo criterio que MOD-05 §17.5);
- digest del origen validado;
- digest HMAC de una enumeración canónica y ordenada de **todas** las filas que lee la validación completa, con sus columnas leídas: acciones y motivos cifrados (por digest del texto cifrado), lecturas de evaluación/selección/cobertura e hijas, decisiones, vínculos, prueba, exportación, partes e imágenes (texto cifrado por digest), borrador, revisión, respuesta y cierre;
- digests de cada parte e imagen descifradas.

## Verificación en descarga

1. Comprobaciones de autoridad y vigencia actuales (sin cambios).
2. Segunda lectura fresca del origen y comparación con el digest sellado (se conserva; no se sustituye por triggers MOD-05).
3. Versión de reglas igual; si difiere, **validación completa** como hoy.
4. Recalcular el digest de la enumeración desde las filas actuales (sin descifrar ni re-derivar) y compararlo; cualquier diferencia → validación completa, que fallará o resellará según su resultado.
5. Descifrar solo la parte solicitada y comparar con su digest sellado.

## Completitud exigida antes de aceptar

- Prueba de inventario: las tablas y columnas que lee la validación completa, obtenidas trazando las consultas de una validación real, son exactamente las enumeradas por el sello; una dependencia nueva hace fallar la prueba.
- Mutación por familia: para cada tabla y columna enumerada, alterar el valor tras el cierre hace que la descarga rechace o revalide por completo y no sirva bytes alterados; incluye acciones, motivos, lecturas, hijas, vínculos, partes e imágenes, borrado e inserción.
- Origen: cambiar una fila del origen, un binario o la fuente Redis aplicable rechaza la descarga por la segunda lectura fresca.
- Cambio de reglas: alterar la versión de reglas fuerza la validación completa.
- Equivalencia: en recorridos válidos, la descarga sellada y la validación completa aceptan y entregan exactamente los mismos bytes; en recorridos alterados, ambas rechazan.
- Concurrencia y transacción: carreras de purga, supresión y revocación durante la descarga se comportan como hoy.

## Aceptación

N2 propia con las pruebas anteriores y las baterías existentes de descarga, cierre, retención, supresión y carreras, PostgreSQL real, fuentes congeladas y cero skips. Solo después puede sustituir la re-derivación en la ruta de descarga; el cierre y las etapas previas siguen validando por completo. No acredita capacidad por sí mismo.
