# N09 — conciliación de 139 identificadores y medición interactiva pendiente

Estado: conciliación de fuentes y testigos, **sin aceptación final de N09**. Continúan 8/13 bloques obligatorios aceptados; alpha/noindex. La corrección R queda verificada en [468](468-n09-r-correccion-procesamiento-preprivado-20261026.md). Esta nota actualiza la continuación, no los resultados históricos de los prerregistros.

## Disposición y custodia

La [matriz individual](evidencias/n09-r-censo139-conciliado-20261026.json) conserva exactamente los IDs de [418](418-n09-inventario-descomposicion-20261026.md), fuentes actuales con SHA-256, pruebas originales identificadas, suplementos de corrección, invariantes, tiempos disponibles, límites y propietarios. SHA-256 del JSON: `99b881d5a9a2e9f7bb903da3ff94c1bcc45e576591b6293e3deeab1324d0f3d5`.

| Frente | IDs | Disposición actual | Límite de la evidencia |
| --- | ---: | --- | --- |
| Derechos interactivos | 52 rutas | Fuentes y testigos funcionales conciliados; correcciones B/C/E/F/G/H/P/R incorporadas | Falta referencia normal de máquina del escenario seleccionado S03A; los tiempos QA no la sustituyen |
| Consumidores y productores | 48: 21 tareas, 21 Beat, 6 dispatch | Referencias finitas I–O y testigos compartidos de N03/N06/N07 conciliados | Los seis IDs dispatch representan cuatro puntos de publicación; Beat declarado no acredita su cadencia en ejecución |
| Rutas compartidas | 27 rutas | Originales y correcciones A/D/Q conciliados, conservando propietarios anteriores | Medidas N07 limitadas a sus familias/estados; sin acreditación humana o externa |
| Operación compartida | 4 comandos propios y 8 runbooks | Obligación operativa retenida explícitamente en N10 | Registro y lectura no equivalen a ejecución; los testigos anteriores no cierran el ensayo operativo actual |

Son **127 disposiciones con límites y 12 obligaciones compartidas de N10**, no 127 pruebas de rendimiento correctas ni 139 funciones independientes. La matriz no convierte a PASS los pendientes de rendimiento u operación.

La revisión propia verificó las identidades de los 52 derechos y 48 consumidores/productores, los testigos originales y archivos de evidencia por etapa I–O, cuatro puentes de función y las 21 declaraciones Beat. Para los 39 compartidos contrastó fuentes, puentes D/Q y 161 testigos originales individuales con su XML y la huella del instrumento original. Cada testigo conserva el ámbito de su caso, sin sumar ejecuciones diferentes como una batería global. El run histórico `20261024-094540-3a6ec8ac` permanece ERROR, con sus FAIL/SKIP; se reutilizan únicamente los resultados individuales contrastados.

El puente R compara la fuente anterior con la actual tras retirar exactamente las dos guardas añadidas, verifica su identidad congelada y enlaza los diez casos reales. No atribuye al camino final independiente de procesamiento una prueba de espera que no lo ejercitó. Los originales fallidos de R se conservan.

El primer verificador de conciliación usaba por error la clave `command` para los cuatro comandos propios; el censo original utiliza `own_command`. Se corrigió sólo esa aserción y se conservó la comprobación fallida. No fue un fallo de producto ni se repitió QA de aplicación.

## Tiempos: referencia y después

| Etapa seleccionada | Referencia medida | Después | Interpretación |
| --- | ---: | --- | --- |
| CopyInformation, primer lote de 100 vencidos | 5,991 ms; 2 SQL | Sin candidata | Una observación de Task.run; no latencia de otros nueve modelos |
| Outbox, primer lote de 100 avisos simulados | 1.402,331 ms; 802 SQL | Sin candidata | Ejecución local del consumidor y simulador, sin entrega externa |
| Exportaciones, primer lote de 1.000 del volumen 1.001 | 2.097,922 ms; 1.007 SQL | Sin candidata | Incluye efectos locales de archivos, sin medir transporte HTTP |
| R, creación/repetición con revocación durante espera | Dos FAIL originales; QA por caso en 468 | Denegación antes de descifrar; diez casos correctos | Corrección de autoridad; QA no mide aceleración de aplicación |
| Derechos/rectificación/reclamaciones, servicio normal seleccionado S03A | Pendiente | No hay comparación temporal | Obtener referencia antes de afirmar rendimiento o aceptar este escenario |

Fuentes de tiempo de máquina: [I/447](447-n09-i-referencia-purgas-logicas-verificada-20261026.md), [J/449](449-n09-j-referencia-outbox-verificada-20261026.md) y [O/459](459-n09-o-referencia-purga-exportaciones-verificada-20261026.md). K/L/M/N conservan sus referencias y límites propios en la matriz. Las muestras pertenecen a estados concretos y no son percentiles ni un SLO. Sin segunda candidata equivalente no hay mejora causal atribuible. No se suman unidades, colas, trabajo humano o proveedor.

## Salida pendiente y próximo paso

Contrato340, criterios354 y escenario S03A exigen separar el tiempo normal de snapshot/validación/transacción de la preparación y la revisión humana. Las campañas A–H/P/Q/R aportan corrección y regresión, pero sus tiempos de cuerpo de caso/JUnit no satisfacen por sí solos esa medición. Antes de cerrar N09 se preparará un perfil finito de los servicios interactivos seleccionados, con fuente/cohorte/oráculo, etapa, medidas y límites prerregistrados y congelados. No se repiten las campañas válidas ni se exige medir todos los endpoints o posibles calendarios por registrar esta brecha.

La conciliación de 139 IDs ya permite identificar exactamente qué se sabe y qué falta; no permite cerrar el bloque por documentación. Permanecen las incertidumbres de fuente `moderation.decide` y `match_review.resolve` para la revisión integrada pertinente de N11; no son vulnerabilidades reproducidas ni reciben certificación de seguridad aquí.

N10, N11 y N15 siguen pendientes. N02 residual permanece al final del desarrollo por decisión del usuario; N12–N14 condicionados. N15 mantiene la reconstrucción completa del grafo, diferencial de inventario y relevo frontend, acta y limpieza completa final de artifacts tras resumen duradero. No se activa htmx4, proveedores, servicios, migraciones, carga, CI o despliegue por esta conciliación.
