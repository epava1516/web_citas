# N01F — criterios de comparación y planificación de los escenarios

25 de octubre de 2026. Decisión técnica de presupuestos anterior a cualquier candidato de aplicación de este contrato. No es un acta de aceptación de N01. Se preservan contrato340, roadmap341, las propuestas originales y todos los resultados anteriores, incluidos los FAIL. Proyecto en alfa.

## Qué debe terminar N01

Roadmap341 exige que cada escenario seleccionado tenga criterio anterior a su candidato y base comparable o razón concreta para medirla. Permite que los lotes posteriores completen su ficha antes de ejecutarse. Contrato340 exige definir presupuesto antes de medir y comparar; no convierte los objetivos propuestos en111/338 en gates automáticamente. N01 no requiere inventar un SLO de producto para cada endpoint ni ejecutar toda la aceptación N02–N10 por adelantado.

Esta decisión concreta el presupuesto de eficiencia mediante comparación con referencia, donde no existe un límite absoluto acordado. La ausencia de una medida sigue siendo ausencia de evidencia de rendimiento; impide comparar o aceptar ese candidato hasta obtener la referencia correspondiente. No difiere ninguna familia o bloque obligatorio.

## Presupuesto comparativo seleccionado

Para cada acción/estado/etapa de las fichas, usar una referencia actual y equivalente, congelada antes del candidato. No mezclar respuestas, idiomas, permisos, cardinalidades, originales o estados diferentes para obtener un valor favorable.

1. **Corrección:** cero diferencias no autorizadas en contenido, autoridad, retirada, retención, integridad, orden/conteos, idempotencia y efectos esperados. Los negativos forman parte del oráculo; ninguna reducción de coste los elimina.
2. **Coste determinista:** para cada dimensión pertinente del escenario (consultas, llamadas de etapa, bytes, objetos, intentos o elementos examinados), el presupuesto de comparación es `coste_candidato ≤ coste_referencia` con el mismo trabajo útil. Si referencia=0, candidato debe conservar0. Se concreta la dimensión objetivo antes de modificar el candidato, sin sumar dimensiones de unidades diferentes. Una mejora exige reducción estricta del coste objetivo; igualdad no se presenta como optimización.
3. **Tiempo instrumentado:** referencia y candidato miden la misma etapa. Comparar primera llamada por separado y cinco observaciones posteriores por variante cuando el coste lo permita. Registrar mediana/rango; no inferir p95/p99 de cinco muestras. El criterio elegido es no empeorar el tiempo de la misma etapa, además de reducir el coste objetivo si se afirma optimización. Si ruido, orden o recursos impiden concluirlo, el resultado temporal es inconcluso: registrar coste determinista demostrado y continuar el contraste necesario antes de aceptar una mejora temporal. No convertir inconclusión en PASS de latencia.
4. **Trabajo costoso:** si cinco observaciones implicaran horas, justificar muestras y etapas en el prerregistro de ese lote antes de ejecutar; no reducir poblaciones/oráculos. Preferir atribución de costes y testigos equivalentes ya válidos cuando existan. Toda afirmación temporal queda limitada a las muestras obtenidas. Prueba larga: persistencia, Telegram y pausa/reactivación conforme a instrucciones vigentes.
5. **Recursos:** registrar CPU/memoria/almacenamiento/colas pertinentes y conservar límites explícitos previos. No ocultar un aumento de otra dimensión por una reducción de consultas o bytes. Una compensación de coste requiere decisión técnica específica y presupuesto explícito anterior a su candidato, sin debilitar garantías del usuario; esta regla no concede excepciones automáticas.
6. **Identidad:** congelar SHA completos de producto, dependencias, migraciones, instrumentos, imágenes y datos; recursos/orden/calor/idiomas/roles declarados. Condiciones distintas no sustentan causalidad de código. El tiempo total de pytest y la duración humana no son latencia de aplicación.

Estas reglas fijan un presupuesto comparativo de eficiencia; los valores de referencia que aún falten son datos que se medirán antes de construir/comparar su candidato. No se publican como presupuestos absolutos de producción. Las fichas por lote deben concretar comandos, tamaños, selección, etapas, errores/timeouts y limpieza antes de cada nueva medición, como exige340.

## Límites absolutos que siguen vigentes

- Mezcla pública: p95 observable<800ms y errores<1% únicamente bajo su protocolo contractual. Los lotes discovery A/B/C y los Client de N01D no equivalen a ese ensayo de carga.
- MOD09: cobertura p95≤2s y entrega JSON/binaria por paquete p95≤5s bajo el protocolo original. No son límites universales de generación, revisión humana ni endpoints nuevos. Excepción provisional y FAIL históricos conservados; N02 sigue obligado a evaluar/corregir o descartar candidatos con evidencia.
- S09-A observado:≤50consultas por collect_snapshot para backlog de publicación0/10/100, demás tablas de trabajo vacías y el servicio/oráculos de353. No es SLO de pared ni garantía con otros contenidos del diagnóstico.
- Similitud:128MiB de corpus,1GiB de RSS y1200s del diagnóstico existente son protecciones, no SLO ni aceptación80000fotos. No se importan otros números de111/338 como gates.

## Disposición individual y razón de nueva medida

La [matriz de ejecución](evidencias/n01-f-criterios-escenarios-20261025.json) conserva las19fichas de352, fuentes/selectores/oráculos/roles y sus criterios por modalidad. Añade criterio comparativo explícito, base disponible y motivo/etapa de cualquier medición pendiente. S01 conserva los protocolos344/346/348 y resultados345/347/349, sin aceptación de mezcla pública por diagnósticos.

| Escenario | Base utilizable en su ámbito | Por qué queda una medida posterior |
| --- | --- | --- |
| S02-A | N01D: HTTP de lifecycle y renovación | Direct expire_one no mide cola/Beat; aislar etapa si se cambia trabajo asíncrono |
| S02-B | N01C: preparación state y paridad de consulta en cohorte100 | No cubre todas las mutaciones ni retraso real del worker; fijar variante concreta |
| S03-A | Fuentes/oráculos de revisión independiente; sin tiempo de servicio actual | Atribuir snapshot/validación/transacción sin incluir revisión humana ni preparación |
| S03-B | Oráculos de outbox/simulador y recuperación | Separar enqueue/claim/adapter/commit de espera natural; nunca entrega externa PASS |
| S03-C | Oráculos de purga acotada y conservación de evidencia emitida | Medir lote y continuación con datos expirados/frescos; no duración de toda QA |
| S04-A | N01D:10operaciones activación/login y negativos, más signup/throttle | Cambios adicionales necesitan mismas ramas/estado, no agregado entre denegación y éxito |
| S04-B | N01D:11/8operaciones de revisión y rechazo; señal116/124SQL | Atribuir consultas/coste de listing_start con mismo estado antes de modificarlo |
| S04-C | Fuentes/oráculos de agencia, asignación, MFA y revocación | Base HTTP actual de esos actores, no extrapolar desde titular individual |
| S05-A | Fuente de diagnóstico Chromium,8fotos,ES/EN,móvil/escritorio | Reutilizar sólo evidencia con versiones/contextos equivalentes o medir bytes/recursos actuales |
| S05-B | Fuente de flujo navegador de subida/previsualización/retirada | Medir navegador real; Client no acredita esa interacción ni entrega |
| S06-A | Objetivos y FAIL MOD09 preservados; paquete real>64MiB como escenario distinto | Atribuir cobertura/generación/partes/entrega sin ampliar la excepción a casos nuevos |
| S06-B | Oráculos de autorización de un uso y revocación fresca | Separar autorización/consumo/bytes de entrega real por proxy |
| S07-A | Cohortes e instrumento distintos1000/densos100 y referencia exhaustiva | Verificar identidad del testigo o medir detector/confirmación/registro; no asumir cola ni80000 |
| S07-B | Oráculo eager de subida privada y reintento | Medir receive→cola→process→ready con broker/worker reales locales cuando se analice esa etapa |
| S08-A | N01D:11operaciones favoritos | Cohortes de crecimiento1/10/100 siguen por manifestar antes de medirlas |
| S08-B | N01D:17operaciones sitemap/idiomas/retirada | Mayor cardinalidad/cambio de paginación requiere base propia equivalente |
| S08-C | N01D:11operaciones por idioma de pedido simulado | Conservar consumo único/propiedad; no sustituye proveedor o cobro real |
| S09-A | N01E:18servicios0/10/100,50SQL y sólo lectura | Cualquier ampliación de otras tablas necesita ficha propia; no repetir por documentación |
| S09-B | Fuente de matriz2×2 de backup/clave y oráculos antiresurrección | Ejecutar o justificar testigo de restauración equivalente; no inferirla del snapshot vacío |

Para todos los pendientes, la matriz fija la condición: primero fuente/cohorte/oráculo y referencia congelados; después candidato. Ningún bloque podrá cerrarse alegando que esta planificación ya verificó su rendimiento. Revisión de suficiencia N01 pendiente; no cambia todavía el contador1/13.
