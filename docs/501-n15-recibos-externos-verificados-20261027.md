# N15 — recibos externos verificados

## Resultado y candidata

Sobre `fa7dee354374cc616787c3230fdbd97ed758f4ea`, ejecución real
`20261027-012424-b41beb6b`: **6 PASS, 0 FAIL, 0 ERROR, 0 SKIP**.
JUnit: 0,297 s; proceso pytest: 2,074 s. Son tiempos de QA, no de la aplicación.
Se conservaron las 1.800 huellas del runner, las seis fuentes adicionales y el
prerregistro500 durante la ejecución. PostgreSQL17 y Redis7.4 propios usaron las
imágenes congeladas previamente; se comprobó su identidad durante el ensayo y
su ausencia tras la limpieza. El proceso y su directorio temporal terminaron.
El aviso terminal real del runner tiene `delivery=sent`.

JUnit SHA256: `5b0e80c6ee126b06a0ffd07bef3495a59ef3387488eb393b8c59107ec50c8ed3`.
La [custodia compacta](evidencias/n15-recibos-custodia-20261027.json) conserva
identidad, casos, huellas, imágenes, limpieza y límites. La ejecución original
está en `artifacts/local-ci/20261027-012424-b41beb6b` hasta la purga final
obligatoria; después esa referencia será histórica y el bruto no estará disponible.

## Cambio y revisión propia

`notify` acepta ahora `receipt_dir`, keyword-only y opcional. Sin valor conserva
el destino original. Con valor sólo escribe en ese directorio, sin fallback a
artifacts. No cambia transporte, configuración, resultado, redacción de errores
ni supresión de duplicados de worker/runner. Los únicos archivos de código
modificados son `scripts/test_notifications.py` y `tests/test_test_notifications.py`.

Revisión focal con django-reviewer y code-security: el destino es de callers
internos fiables, no de entrada HTTP; se mantiene argv separado y no se guarda
stderr del proveedor. El controlador de cierre deberá fijar y revisar una ruta
propia fuera de artifacts, rechazar enlaces o destinos ajenos y exigir tanto
`delivery=sent` como ausencia de `receipt_error`. El helper permite seleccionar
el destino; no constituye por sí solo una política de aislamiento de rutas.
No se encontraron defectos que requieran otro cambio dentro de este alcance.

Los tres casos originales permanecen. Los tres nuevos cubren transporte correcto,
transporte fallido y escritura bloqueada: resultado intacto, redacción, recibo
correcto cuando es posible y ausencia de artifacts/fallback. Usan archivos y
configuración sintéticos y transporte sustituido: **no prueban el proveedor real
ni la integración PostgreSQL/Redis**. El aviso real del runner acredita por
separado el canal configurado. Ruff y las comprobaciones oficiales del runner
terminaron correctamente; no se repitió ninguna batería ya válida.

## Continuación

N15 sigue abierto, con 11/13 bloques obligatorios aceptados. El insumo nativo
estático de frontend pasó revisión independiente de 136 archivos y 3.524 citas,
pero queda como propuesta de entrada, sin aceptación de runtime/frontend.

Faltan reconstrucción completa del grafo, diferencial338/339, relevo de frontend,
conciliación documental, acta/Git y purga final de artifacts con constancia y
recibos externos. El grafo focal500 previo no sustituye la reconstrucción.
Se conserva [la deuda viva](deuda-pendiente-viva.md): N02/MOD09 al final del
desarrollo, N12/B14, N13/B15 y N14/B17 condicionados y QA general hasta estable.
Alpha/noindex; no se autoriza apertura ni reescritura del frontend en este contrato.
