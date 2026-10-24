# B07 — Escala funcional territorial con49candidatos pendientes

Estado: secuencia215 terminada y auditada; equivalencia funcional verificada, sin aceptación de capacidad.

B07-214: preparada equivalencia49 a1000/10000, con0derechos y20%promocionados; censo nativo completo y páginas primera/intermedia/última ESEN en cuatro fases. Revalidación100 justificada por generalizar el helper y comprobar etiquetas por identidad. Sin producto nuevo, TCP ni worker; B07 abierto8de18.

## Incertidumbre y alcance

El [control213](207-equivalencia-territorial-49pendientes-b07-20261022.md) prueba100perfiles y160páginas en total. La [escala199](198-escala-equivalencia-territorial-b07-20261021.md) prueba1000/10000 frescos con promociones. Ninguno demuestra esta combinación de49elegibles pendientes, un retirado y dos regímenes transaccionales a volumen. Reutilizar ambos resultados en su alcance; no repetir carga TCP ni reabrir hipótesis rechazadas.

Generalizar `verify_territorial_unknown49_equivalence` sin cambiar rutas ni constantes de producto. Dos cohortes por escala: orgánica con pipeline habilitado y cero derechos, y20%Top/Premium emitidos por servicios reales y eventos firmados sintéticos.1000→700/300 y10000→7000/3000; mismo límite de agencia/fotografía y sólo dos municipios sintéticos, sin representatividad nacional. Preparación PostgreSQL propia, ocho tablas finalizadas y refresh inicial explícito.

Mutar por triggers reales49perfiles aún elegibles del primer municipio y retirar otro distinto (promocionado cuando haya derechos).50marcas:49elegibles y1retirado; visibilidad999/9999. Conservar las50tras ambas lecturas sucias; después de reparación manual,0. READ_REPAIR desactivado, Celery eager desactivado después del fixture; no worker ni sustitución de reglas. NATIVE_UNKNOWN_LIMIT48 y DIRTY_LIMIT1000 intactos.

Cuatro fases: fresca, dirty49 en instantánea propia, dirty49 en READCOMMITTED heredado verificado por SHOW, y reparada manualmente. Referencia comercial independiente comparte autoridad nativa y relevancia PostgreSQL; no usa helpers de orden comercial. En cada ciudad y consulta vacía/photography, construir referencia completa, comprobar unicidad y conjunto igual al censo publicado actual; registrar count y SHA256 de secuencia completa. No comparar sólo muestras del censo.

En1000/10000 recorrer primera, intermedia `(last+1)//2` y última página por municipio/consulta/ESEN:24páginas por fase,96porcaso. Últimas páginas del primer municipio30/292 y del segundo13/125; retirar uno no altera esas últimas páginas. Comparar IDs ordenados y recuentos exactos de cada página, no solapamientos entre páginas seleccionadas, ausencia del retirado y etiquetas patrocinadas por identidad de derechos válidos de la cohorte. No afirmar recorrido exhaustivo de las páginas intermedias omitidas. Las firmas dirty/READCOMMITTED/reparada deben coincidir.

En ambas escalas: fase dirty propia12páginas trusted_state_extended_unknown con49native_unknown y12state normales. READCOMMITTED heredado12fallback state_unknown_over_limit y12state. Fresca/reparada24state. El control100 conserva20páginas por fase,12extendidas/8normales y12fallback/8normales; patrocinio total80→76en cohorte20derechos y0en orgánica.

## Secuencia215 congelada y criterios

Tres gates oficiales secuenciales, un worker y broker aislado, fixture snapshots y kernel canónico nativo de `/tmp/web-modelos-librdb-v2.4.0`:

1. `tests/test_backlog_territorial_equivalence.py`: dos casos100, timeout900s. Repetición afectada por la extracción del helper común y nuevas aserciones de etiquetas/censo; no nueva medición de capacidad.
2. Nodos `tests/test_capacity_backlog_territorial_equivalence.py::test_large_territorial_unknown49_equivalence[organic-1000]` y `[promoted-1000]`, timeout7200s.
3. Mismos nodos con10000, timeout21600s.

Cada gate usa `scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --fixture-snapshots --isolate-test-broker`, con dos `--test` cuando se seleccionan nodos. Aceptar sólo2+2+2PASS/0FAIL/0ERROR/0SKIP y fuentes idénticas al prerregistro en todos los gates. Cualquier fallo detiene la secuencia; conservarlo y auditar antes de corregir o repetir.384páginas seleccionadas grandes más160del control100=544páginas totales; nunca todas las páginas grandes.628fuentes producto deben permanecer iguales al corteB13.

La duración depende del oráculo nativo completo y puede ser de horas. Ejecutar persistentemente, archivo de salida por gate, PID+startticks y sesión propios; ninguna prueba/build paralela. Runner notifica terminal tras limpieza; secuencia emite aviso global, vigilante comprueba el terminal y callback reactiva el mismo goal sin nuevo objetivo ni pérdida de consumo. Confirmar aviso previo Telegram, persistencia y callbacks antes de pausar. Solicitar compactación tras pausa, sin sondeos del modelo. El callback no acepta pruebas ni inicia otra batería.

Guardar protocolo original y SHA256, fuentes completas, JUnit, resultados, recibos y pruebas de contenedores/temporales/procesos retirados. No editar código/docs/grafo durante la secuencia. La auditoría posterior verifica las propiedades y la evidencia real; una solicitud de compactación confirmada no demuestra por sí sola el contenido final compactado. Sin proveedores, datos reales, publicación, nuevo corto o900automático.

B07 permanece abierto8de18: recursos a volumen, reparación por workers con backlog grande, colas completas, mezcla de estados TCP y PRODUCTION/checked no quedan cubiertos por esta equivalencia funcional.

## Resultado auditado215

B07-215: equivalencia territorial49 auditada en PostgreSQL real: 6PASS/544páginas, cohortes100/1000/10000 con0/20%derechos. Censo nativo completo; páginas grandes primera/intermedia/última, sin recorrido exhaustivo. Instantánea propia y READCOMMITTED coinciden con reparación manual;628fuentes producto intactas. Limpieza, Telegram, reactivación del mismo objetivo y solicitud de compactación confirmados. Sin crédito de capacidad ni worker; B07 abierto8de18.

Evidencia: [auditoría215](evidencias/b07-equivalence215-unknown49-scale-20261022-audit.json). Gates reales `20261022-014255-7281f1c3`, `20261022-014749-a1fe6d16` y `20261022-021545-372e0172`, dos casos cada uno, cero fallos/errores/omisiones. Tiempos JUnit por cohorte:135,048/118,951s;729,599/906,322s;6576,248/8855,917s. Son duraciones de pruebas con oráculo, no latencias del servicio.

Protocolo original congelado SHA256 `d268b88f1d8234e73efbb1ff3d0f6a24749b147f8df6d1fb29d74f5b44233d67`, conservado en artifacts. La auditoría comparó las fuentes antes de esta actualización documental. Las50marcas permanecen tras ambas lecturas sucias y desaparecen tras reparación manual; los límites48/1000 no cambian. Sin nueva medición TCP ni repetición900. Pendientes recursos a volumen, reparación real de backlog grande, colas y mezcla de estados TCP según matriz180.
