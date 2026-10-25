# Contrato alfa — medición, corrección y optimización de recorridos

Versión 1.2, 25 de octubre de 2026. Ejecución autorizada por el usuario: «empieza con el nuevo contrato procediendo como lo haciamos en el anterior, hasta el finales». N00 aceptado por [343](343-n00-aceptacion-local-20261025.md);1/13bloques obligatorios. N01 en curso con prerregistro344. La preparación documental1.0 permanece en el commit5118a05 y sus evidencias. El producto permanece en alfa durante y después del contrato, hasta una decisión posterior del usuario.

Estado posterior de ejecución: N00 y N01 aceptados, **2/13**, por [acta355](355-n01-aceptacion-local-20261025.md). El párrafo inicial conserva el corte de inicio1.2; esta nota actualiza sólo seguimiento, sin alterar términos ni garantías. Los criterios comparativos se concretan en [354](354-n01-f-criterios-comparacion-escenarios-20261025.md).

## 1. Objeto y precedencia

Medir, corregir y optimizar las acciones reales de la aplicación y de su operación local, usando como primera prioridad el inventario actualizado I01–I28. Incorporar la deuda trasladada con su estado y condiciones, sin reabrir las aceptaciones anteriores ni dar por implementadas funciones opcionales.

El [roadmap341](341-roadmap-recorridos-optimizacion-alpha-20261025.md) concreta orden, dependencias, entregables y salida por bloque N00–N15. Esta descomposición técnica ejecuta los acuerdos; no añade decisiones de producto. Las instrucciones del usuario prevalecen. Este contrato gobierna el nuevo trabajo; las garantías técnicas del [contrato16](16-contrato-ejecucion-desarrollo.md) siguen aplicando donde no haya una sustitución expresa aquí. Las obligaciones finales de aquel contrato ya se cumplieron y no vuelven a quedar abiertas por esta referencia.

Fuentes de alcance:

- [Acta23 de cierre anterior](actas/23-cierre-contrato-clasificados-alpha-20261025.md), commit de cierre `16ac270835e0f9fe0bd0f749aba251bcac3712ee` y [verificación final](evidencias/contrato-cierre-final-verificacion-20261025.json).
- [Acuerdos320](320-acuerdos-alcance-b10-prioridades-20261024.md) y [disposición336](336-deuda-siguiente-contrato-y-cierre-alpha-20261025.md): inventario primero, B14/B15/B17 diferidos, QA específico aplazado.
- [Inventario338](338-inventario-acciones-recorridos-alpha-20261025.md), [diferencial339](339-diferencial-inventario-recorridos-20261025.md), [censo de fuentes](evidencias/inventario-acciones-final-20261025.json) y [verificación](evidencias/inventario-acciones-verificacion-20261025.json). Original111 preservado como antecedente.
- [Contrato funcional14](14-contrato-funcional-v1.md), decisiones vigentes y [DAFO98](98-dafo-clasificados-citas-romanticas-20261020.md). El roadmap103 conserva el contrato anterior y sus cortes históricos;341 es el roadmap de este contrato.

No se modifica el modelo: clasificados de personas adultas que buscan citas románticas, panel centrado en completar el perfil, renovación y exposición Top/Premium conforme a lo ya acordado. Se conservan ES/EN, contacto externo, revisión y autoridad de publicación. Las preferencias físicas B15 permanecen opcionales.

## 2. Base aceptada y unidades

El contrato anterior conserva15/18puntos aceptados localmente: B00–B13 y B16. B14/B15/B17 son deuda, no PASS. B10 está resuelto como evaluación y disposición; se heredan sus problemas medidos y límites, no un supuesto B10 sin iniciar.

Base del inventario:28familias,170declaraciones propias de ruta con nombre,27tareas,15comandos propios y31del framework,11recorridos operativos,129plantillas y tres JavaScript propios. Los366patrones URL distintos incluyen idiomas y Admin; los154valores de controles no son154acciones independientes. Estos conjuntos no se suman como funcionalidades o pruebas.

Base de navegación: grafo final anterior1925fuentes,17870nodos,79571relaciones y848comunidades, identificado por [registro final](evidencias/contrato-grafo-registro-final-20261025.json). La extracción semántica es selectiva, las vistas de seguimiento son parciales y las referencias estáticas no prueban coste, permiso efectivo ni PASS. Su centralidad no ordena por sí sola el trabajo.

## 3. Alcance obligatorio

1. Contrastar I01–I28 contra fuentes actuales y cambios posteriores; clasificar cada acción por autoridad, dependencias, datos/estados, cobertura funcional, evidencia de rendimiento, riesgo y coste conocido. Registrar añadidos, cambios, retirados y conservados.
2. Definir escenarios y presupuestos antes de comparar candidatos. Medir los recorridos sin evidencia aplicable o con incertidumbre relevante; reutilizar evidencia sólo con identidad y escenario justificados. Todos los elementos del inventario deben recibir una disposición trazable; el muestreo debe justificar qué representa y qué deja sin medir.
3. Resolver defectos de producto encontrados y optimizar costes demostrados con comparación, paridad y reversión. No exigir una modificación de código cuando la referencia ya cumple: puede aceptarse «sin cambio necesario» con evidencia suficiente. No forzar un porcentaje de mejora inventado.
4. Evaluar I22/MOD09 e I14 dentro de la priorización fundada de N00, sin precedencia automática por su deuda: cobertura y paquetes, detector y confirmación/registro, densidad, cardinalidad de originales, retención, concurrencia y colas. Distinguir consulta, materialización, cifrado/serialización, objetos, entrega y trabajo asíncrono; no atribuir a toda la aplicación el tiempo de una prueba.
5. Cubrir descubrimiento público, entrega/navegador, panel/cuenta, medios/publicación, superficies secundarias/comerciales sintéticas, derechos/avisos/limpieza y operación. El roadmap asigna las28familias sin eliminar las de menor tráfico supuesto.
6. Conciliar los cambios en una candidata final identificada, con regresión pertinente, recuperación donde se afecte y actualización final del inventario y del grafo. Emitir acta local con resultados y deuda individualizados.

## 4. Deuda condicionada y exclusiones

| Origen | Tratamiento en este contrato | Condición para ejecutar o aceptar |
| --- | --- | --- |
| B14 → N12 | Conservar interfaces, fallos, reintentos, revocación y minimización; identificar insumos pendientes y revalidar guardias si otro cambio las afecta. | Proveedor elegido y autorización separada antes de integración real, contacto o gasto. Sin ellos, diferido documentado; nunca integración real PASS. |
| B15 → N13 | Mantener diseño y decisiones pendientes en un bloque opcional. | Decisión expresa de incorporarlo y contrato de datos/escenarios antes de implementar. No se activa por generar este documento. |
| B17 → N14 | Mantener matriz de preparación y dependencias reales, con responsables por identificar. | G01–G08 y autorización futura de apertura; este contrato no obliga a abrir beta ni asigna personas ficticias. |

Para B15 se conservan: preferencias físicas elegidas y atributos declarados; decisiones separadas de mayoría de edad/términos, cookies y personalización; búsqueda normal disponible; cookies propias del visitante con duración/contenido por diseñar; evaluación de persistencia cifrada privada para cuenta, claves, modificación, borrado y retirada. No se importa automáticamente la preferencia del navegador a la cuenta ni se infiere desde fotos. El cifrado no acredita por sí solo cumplimiento normativo. No se fija proveedor o medio de almacenamiento sin la decisión pendiente.

Quedan fuera: apertura, despliegue externo, contratación, cobros reales, sujetos reales y validaciones con participantes; expansión de producto no acordada; reescritura integral o adopción automática de índices/servicios. La propuesta de índice de similitud requiere corpus, paridad, coste y decisión técnica justificados, incluidos negativos.

El contrato específico de medición/corrección/optimización de QA sigue aplazado hasta la primera versión estable/productiva. Siguen siendo parte del desarrollo las correcciones de pruebas defectuosas o bloqueantes y las verificaciones pertinentes. No se programa aquí una campaña general de paralelización o reducción de cobertura.

## 5. Método de medición y aceptación por escenario

Antes de cada medición relevante se registra una ficha con: ID N/I/acción, requisito y propósito, hipótesis, SHA de producto/dependencias/migraciones/instrumentos, datos sintéticos y distribución, estados, cardinalidad, idiomas, permisos, modalidad y concurrencia, cuotas/hardware, caché fría/caliente, procesos y colas, oráculos, carga, duración, contabilidad de errores/timeouts, limpieza y presupuesto aplicable. HEAD solo no identifica una candidata.

Separar medición instrumentada del ensayo de carga limpia y del tiempo de preparación/QA. Registrar p50/p95/p99 cuando el tamaño de muestra lo permita, errores, SQL/planes, CPU/memoria, bytes, cola/reintentos y tiempos de cada etapa pertinente. Para navegador: dispositivo/viewport, recursos, bytes, interacción y estados. Para operación: autoridad, efectos, integridad, recuperación y exposición; un registro offline de comandos no prueba su ejecución.

La comparación antes/después conserva escenario, selección y recursos, informa variabilidad y factores de confusión y usa repeticiones justificadas. No fija por defecto una batería de horas. Se atribuye mejora causal sólo con evidencia compatible. No se reduce el dataset, la duración, la mezcla ni las comprobaciones para aparentar una mejora.

Los presupuestos propuestos en111/338 no pasan a ser gates por este contrato. N01 concreta los pendientes antes de medir mediante la delegación técnica vigente y documenta los supuestos; los cambios de alcance o garantías del usuario requieren su decisión. Se mantienen los criterios contractuales aplicables de16, incluida la mezcla pública p95 observable<800ms y errores<1% bajo su protocolo, sin convertirla en umbral universal de cada endpoint.

MOD09 mantiene los objetivos originales2s/5s y la aceptación provisional expresa. Los FAIL históricos y actuales no se reescriben. N02 debe producir evaluación actual, corrección/optimización justificada o descarte de candidatos con evidencia; repetir la excepción antigua sin ese trabajo no completa N02. Si siguen incumplimientos, separar el estado técnico FAIL del escenario de la disposición contractual provisional, con latencias, impacto y deuda explícitos; no revocar ni ampliar automáticamente la excepción. Un escenario adicional no cubierto por ella conserva su propio criterio y pendiente.

Cada aceptación contiene requisito → acción → cambio o decisión sin cambio → candidata → prueba/medición → resultado → límite → deuda. Estados: pendiente, en curso, verificado localmente, verificado con límite declarado, FAIL, diferido por condición o no aplicable justificado. Cobertura funcional y rendimiento se registran por separado. SKIP o falta de muestras no equivalen a PASS. Un pendiente obligatorio sin evidencia impide el cierre; no se cambia a diferido por comodidad.

### Tabla obligatoria de antes y después por bloque

Instrucción posterior del usuario del25deoctubre: «Al finalizar cada bloque del inventario haz una tabla del antes y despues». Es requisito de cierre de cada bloque de recorridos y de su informe al usuario. Registrar filas por acción/escenario y medida relevante: versiones base/candidata, datos y recursos comparados, tamaño de muestra, métrica y unidad, antes, después, diferencia absoluta/porcentual cuando sea válida, resultado y límites. Enlazar evidencias originales y oráculos de paridad.

Aclaración posterior del usuario: la tabla debe incluir los **tiempos de rendimiento anteriores y posteriores**, con unidad, etapa/escenario, muestra, diferencia absoluta y porcentual cuando sea comparable. Una tabla sólo de estado, cobertura o consultas no sustituye esa comparación temporal en un bloque de optimización. Mostrar tiempo de aplicación, separado de preparación/QA. Sin candidato o equivalencia, registrar los tiempos disponibles y «no evaluable» para la mejora atribuible; nunca inventar un después o un porcentaje.

Separar latencia, SQL, bytes, CPU/memoria, cola y corrección funcional; sólo usar las métricas que correspondan. No mezclar preparación de QA con tiempo de aplicación ni agregados de escenarios diferentes. Indicar variabilidad y condiciones de caché/concurrencia cuando importen. Conservar regresiones y resultados sin mejora.

Si no hay base comparable, consignar «sin base comparable» y el motivo, sin porcentaje o mejora causal. Si no cambia producto, explicitarlo; un bloque de inventario/prerregistro puede comparar cobertura, incertidumbre y disposición, sin inventar latencias. Para bloques condicionados no activados, comparar el estado de la condición y registrar no aplicable a rendimiento. La tabla no sustituye la evidencia ni permite cerrar un obligatorio pendiente.

## 6. Invariantes técnicos

Preservar autoridad fresca antes de leer o descifrar datos privados, sesiones/MFA/CSRF, grants y su revocación, identidad de sujeto/versión/finalidad, locks y transacciones, idempotencia, retención y retirada inmediata en todas las superficies. Cachés, índices, paginación, señales, bulk/rawSQL y worker no pueden reintroducir perfiles inelegibles ni exponer estados antiguos. Los valores físicos desconocidos no se inventan.

Conservar IDs, ordenación y patrocinio exigidos, cupos/rotación, exclusiones, conteos y paginación sin duplicados ni omisiones. Las optimizaciones de medios mantienen formatos, contenido autorizado, aislamiento de originales y calidad necesaria. Las de derechos mantienen cobertura, integridad, separación, evidencia y revocación en entrega; no aceptar rapidez sacrificando contenido.

PostgreSQL real obligatorio en integración. Broker, objetos, proxy y navegador reales locales cuando el recorrido lo requiera. Simuladores explícitos sólo para sus límites; ninguna prueba local demuestra proveedor real. Datos siempre sintéticos. Migraciones con compatibilidad/reversión comprobables donde corresponda. Diagnóstico y telemetría sin identidades, contactos, preferencias íntimas, credenciales o datos de sujetos.

## 7. Ejecución, seguimiento y pruebas

Ingeniería decide la implementación ordinaria dentro del alcance. Descomponer cada bloque, refrescar el grafo antes del hito con fuentes afectadas y declarar alcance AST/semántico, medir, corregir y verificar. No hay pausas de aprobación rutinarias. La [sección vigente de seguimiento17](17-seguimiento-desarrollo.md) será la única cola al iniciar ejecución;341 expresa dependencias y condiciones, no otra cola independiente.

No repetir pruebas ya válidas por actualizar documentos. Elegir focales y regresión por cambios/riesgo y registrar reutilización, selección, PASS/FAIL/ERROR/SKIP y negativos. La regresión integrada final no suma ejecuciones distintas como si fueran una sola. Reparar defectos de pruebas conservando negativos; la ausencia de un fallo no demuestra alcance no ejecutado.

Notificar por Telegram OpenClaw inicio y resultado/bloqueo de cada paso, y resultado terminal de toda prueba. pytest y run_local_ci usan sus mecanismos existentes; otros comandos de pruebas pasan por `scripts/run_notified.py`. Comprobar recibo de envío. Una notificación fallida no transforma una prueba en PASS.

Para pruebas previsiblemente largas: lanzamiento persistente, comprobación del proceso y aviso previo con motivo/prueba; si hay goal activo, pausarlo explícitamente sólo conforme a la autorización aplicable, sin detener la prueba. Guardar relevo y compactar durante la espera. La instrucción posterior del21deoctubre mantiene notificación terminal y reactivación automática del mismo goal por el mecanismo soportado existente, preservando objetivo/consumo, sin sondeos del modelo. Comprobar recibos y registrar fallos; no recrear goals ni lanzar baterías por el mero mecanismo de notificación.

Trabajar sobre master como base simple, con commits/push periódicos de entregas coherentes ya autorizados. Los escritores paralelos, si aportan valor y están autorizados, usan worktrees aislados con propiedad explícita de archivos y aceptación independiente por Codex; no introducir una rama intermedia permanente. Preservar cambios del usuario y evidencias; nunca stage de cambios ajenos.

## 8. Cierre del contrato

N00–N11 y N15 son13bloques obligatorios. N12–N14 son tres bloques condicionados, con estado explícito aunque no se activen. No se contará16/16PASS por documentar tres diferimientos. La creación de estos documentos completa sólo la preparación documental, no alguno de los13bloques técnicos.

Para cerrar: las28familias y todas las acciones censadas tienen disposición trazable; los escenarios prioritarios disponen de medición/corrección y evidencia aplicable; cada cambio conserva invariantes y regresión; presupuestos y excepciones permanecen visibles; no quedan defectos críticos de acceso, exposición o pérdida de datos en el alcance aceptado. Los pendientes nuevos no críticos necesitan disposición individual conforme a alcance/autoridad, sin sustituir el trabajo obligatorio. N11 y N15 concilian la candidata y los entregables.

Orden final N15: auditoría técnica → preservar el grafo y reconstruir una vez desde cero el corpus final definido con AST/semántica y comprobaciones → diferencial del inventario338/339 y su censo, conservando111 e IDs → integración semántica de entregables y verificación documental → acta final y registro Git. Un refresco focal por hito no sustituye esa reconstrucción final. Registrar exclusiones, referencias no resueltas, vistas parciales, herramientas, huellas y consumo disponible; no exigir exhaustividad semántica ficticia. Si una corrección posterior afecta corpus/recorridos, reconciliar antes del acta.

El acta final separará aceptaciones locales, incumplimientos, excepciones y B14/B15/B17 condicionados, y fijará prioridades futuras. El resultado sigue siendo alfa. Abrir beta o producción requerirá otro alcance y autorización expresa.
