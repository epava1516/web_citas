B07 aceptado técnicamente en local por acta16: línea base, diversidad y presupuestos conciliados con15evidencias y12requisitos. Contractual combinado296 PASS:18.000respuestas correctas,15subidas,p95415,657ms. Nueve de18puntos cerrados; siguiente B00. Sin aceptación beta global ni producción.

Cierre vigente: [acta16](actas/16-beta-b07-aceptacion-local-20261023.md). Los estados abiertos de cortes anteriores se conservan como historial y quedan sustituidos en este alcance.

# B07 — Conciliación de cierre y siguiente incremento

B07-286 conciliado: once evidencias nativas contrastadas con el producto628 actual. Coste281 e integración HTTP283 normal/PRODUCTIONchecked100 cubiertos; calibración combinada285 válida sólo a100. Pendiente contraste HTTP combinado comparable a escala y presupuesto; B07 abierto, ocho de18.

## Alcance comprobado

Revisión posterior a271, sin nuevas cargas. Fuentes normativas: [roadmap103](103-roadmap-beta-clasificados-20261020.md), [línea base108](108-linea-base-beta-b07-20261020.md), [contrato16§16](16-contrato-ejecucion-desarrollo.md#16-consolidación-del-rendimiento-de-lectura--mod-04), [criterios de carga](criterios-revision-benchmark-carga.md). Grafo316 consultado antes de analizar este incremento; consulta BFS truncada, contrastada con archivos completos pertinentes. No auditoría exhaustiva del corpus.

coverage274-evidence-review.json y reconcile_b07_274.py, en artifacts/beta-promotion-fix-20261020, vuelven a comprobar ocho identidades de corrida, sus JUnit terminales, huellas archivadas disponibles y628archivos de producto contra el árbol actual. PASS notificado por Telegram. Las herramientas y fixtures históricas tienen1689/1701/1702fuentes según su corte: no se declara igualdad completa entre esas corridas ni una comparación causal única. Las auditorías originales conservan el detalle de congelación, limpieza y recibos; esta revisión no las reemplaza ni reejecuta.

| Exigencia original | Evidencia y decisión | Pendiente concreto |
| --- | --- | --- |
| Versión, recursos y fixture explícitos | Huellas por corrida, cuotas8CPU8GiB/swap0, población y mezcla publicadas | Conservar por escenario; no unificar retrospectivamente fixtures |
| Escala y atribución100/1000/10000 |268/269/270 misma estrategia confirmada, controles separados, ORM/binding/filas/SQL/render;240/241/260 filtros combinados | No repetir matriz válida; métricas no medidas siguen explícitas |
| Orgánico/promocional y páginas profundas | Baseline108 y comparación109;239/240/241/260 equivalencia y coste combinado;262/265 mezcla territorial | Falta línea HTTP de ciudad+tipo+idioma+texto; las rutas TCP actuales sólo combinan ciudad y texto |
| Estados y backlog |245/246/252 contrafactuales,254/255/256/257 confirmados;229 worker real a10000 y cotas de reparación | Reutilizar cada escenario en su ámbito; no exigir residencia Redis exclusiva o edad individual no medida como requisito añadido |
| CPU/memoria por servicio |256 a1000,258 a100,271 a10000; seis identidades y fases auditadas | Cubierto como observación funcional; sin estado estable ni atribución causal por petición |
| Corto y contractual limpios |262 PASS1200respuestas y265 PASS18000/15uploads, generador válido | Cubiertos para mezcla declarada; no repetir por esta revisión |
| PRODUCTION y checked |244: equivalencia local100,210páginas y prueba obsoleta, metadata sintética explícita | Falta coste y contraste HTTP pertinente; no acredita capacidad grande ni proveedor real |
| Presupuestos de escenarios nuevos |108 conserva provisionalmente p95<800ms/errores<1%; contrato conserva generador y contabilidad | Prerregistrar mezcla exacta antes del nuevo contraste; calibración3s no acepta percentiles sostenidos |

## Decisión finita de ejecución

Primero cubrir filtros combinados por HTTP, reutilizando la distribución sintética positiva de test_combined_filter_equivalence y beta_combined_filter_cost_diagnostic: dos municipios70/30; dentro de ellos60/20porciento del total woman/en y resto man/fr; negativo woman/fr y texto ausente. Seleccionar primera/intermedia/última según el censo filtrado nativo, no el total municipal. Mantener tercios listado/búsqueda/ficha ESEN mediante slots explícitos y fichas protegidas. Antes/después verificar IDs ordenados, recuentos y patrocinios contra referencia nativa; las respuestas vacías deben ser200, nunca páginas fuera de rango convertidas en éxito.

Implementación siguiente: variante explícita del instrumento, sin activar filtros nuevos en el escenario262/265 existente. Añadir distribución y censo filtrado, rutas y verificadores dedicados; transportar la opción por launcher/controlador/settings con guards que impidan combinaciones no soportadas. Revisar tests de opciones y plan antes de una calibración nativa100; no tocar producto, recursos, GC, workers, generador ni límites. La calibración funcional sólo valida instrumento. Tras auditarla, decidir escala y contraste limpio con el coste observado; no lanzar900s por defecto. No repetir atribución, recursos ni contractual de otra mezcla.

Segundo cubrir coste PRODUCTION/checked con la fixture de244 y guards intactos. Generar dataset en no producción y activar la política local sólo después de etiquetar las pruebas sintéticas; conservar negativas de procedimiento/versionado, retirada fuera de primera página y paridad. No relajar proveedores ni presentar metadata de prueba como verificación real. Preparar protocolo de coste/HTTP después de revisar la calibración combinada, para reutilizar rutas verificadas sin mezclar permisos externos.

Esto no es aceptación B07/B08. Cierre posterior mediante matriz requisito→artefacto→límite y revisión de alcance; ocho de18 siguen cerrados. No se añaden como gates representatividad nacional, barrido concurrente exhaustivo, CPU por petición, causalidad del observador o proveedor real. Proveedor/apertura son B14/B17 separados; no publicación, pagos ni datos reales. B08 y demás puntos conservan su aceptación propia.


## Conciliación286 posterior a285

Grafo328 consultado antes de analizar: BFS180nodos,24mostrados con presupuesto1200, truncado; contraste directo con roadmap103B07,108,16§16, este documento y código de capacity_combined_filters/run_vps_capacity/check_capacity_environment. No revisión exhaustiva. Auditoría coverage286-evidence-review.json: once identidades de corrida, JUnit sin fallos/errores/omitidos, hashes archivados disponibles y628fuentes de producto contrastadas contra el árbol. Las dos pruebas por corrida281/283 se concilian por duración sumada; no se impone un caso único. No nueva carga.

| Requisito revisado | Evidencia reutilizable | Decisión y límite |
| --- | --- | --- |
| PRODUCTION/checked, equivalencia, coste e integración |244referencia nativa;281dos casos/210observaciones1470lecturas;283dos casos/210TCP210referencias | Cubierto localmente a100 con fixture sintética y sin promociones. No proveedor real ni capacidad grande; no repetir por esta revisión |
| HTTP combinado y contabilidad |285un caso/60éxitos/1upload,44oráculos antes/después,fronteras de emisión y política intacta | Instrumento calibrado100; no acepta percentiles sostenidos ni resuelve causa277 |
| Escala/atribución/recursos |240/241/260combinado secuencial;268–270atribución confirmada;271recursos10000 | Reutilizar ámbitos originales. No convertir coste secuencial en HTTP concurrente |
| Corto y contractual |262/265mezcla final confirmada, generador válido | Cubiertos para su mezcla; no repetirlos ni extender crédito a nuevos filtros |

Residual concreto: el transporte combinado está restringido expresamente a funcional100 y plan de60slots38rutas; distribute/cases fijan100 y plan fija16listados20búsquedas. No basta cambiar una variable de población: se deben derivar páginas y slots por censo filtrado, conservar tercios/ESEN/negativas, y transportar una opción explícita con guards en launcher/controlador. El coste combinado260 a10000 ya observado incluye controles separados y máximos hasta794,745ms en fase pending/promocional; eso justifica un contraste HTTP comparable, no una optimización de producto sin hipótesis.

Siguiente incremento finito: adaptar sólo el instrumento combinado para funcional1000 y10000, manteniendo100 existente y separando de262/265 y del diagnóstico de generador. Verificar guardas, plan y equivalencia antes de autorizar cada escala. Prerregistrar rutas, población, recursos, duración y decisión terminal; después de cada auditoría decidir avance. El nuevo presupuesto conserva p95<800ms/errores<1% y política contractual, con un control limpio pertinente que permita contraste sostenido; no aceptar3s como tal ni lanzar900s por defecto. La duración y cobertura exactas de ese contraste se fijarán antes de medir, según coste y alcance observado.

No segundo intento de confirmación285 ni reinterpretación277; ampliar escenarios es un nuevo incremento explícito, no repetir para verde. Sin nuevos gates nacionales, barrido concurrente exhaustivo, CPU causal por petición o proveedor real. Sin modificación de contrato externo, producto, permisos, GC, workers ni recursos. B07/B08 siguen abiertos hasta aceptación propia; el objetivo general conserva B00residual y B08–B11/B14–B17, B15opcional.
