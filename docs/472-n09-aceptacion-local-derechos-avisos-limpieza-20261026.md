# N09 — aceptación local de derechos, avisos y limpieza

Se acepta **N09 localmente en los escenarios y límites documentados**. El contrato pasa a **9/13 bloques obligatorios aceptados**: N00, N01, N03, N04, N05, N06, N07, N08 y N09. N02 residual conserva el diferimiento expreso al final del desarrollo; N10, N11 y N15 permanecen pendientes. N12–N14 siguen condicionados, no PASS. Producto en alpha/noindex, sin apertura, proveedores ni sujetos reales.

Esta acta actualiza el estado de ejecución posterior a 469. No altera los términos de340/341 ni incluye sus modificaciones laterales en esta entrega. Los cortes históricos que aún indiquen ocho aceptados se conservan como historia, no como el estado vigente de N09.

## Requisitos, acciones y evidencia

| Requisito de salida N09 | Acción y evidencia revisada | Resultado y límite |
| --- | --- | --- |
| Disposición del inventario completo y solapamientos | [418](418-n09-inventario-descomposicion-20261026.md), conciliación raíz [469](469-n09-conciliacion139-y-brecha-medicion-interactiva-20261026.md) y [matriz actual de 139 IDs](evidencias/n09-s-censo139-aceptacion-local-20261026.json) | Exactamente 52 derechos, 48 consumidores/productores y 39 compartidos. 127 disposiciones con límites; cuatro comandos y ocho runbooks retienen su obligación operativa en N10. No 139 funcionalidades ni 127 PASS de rendimiento |
| Autoridad, lectura privada, cobertura e integridad | Correcciones y regresión A–H, P, Q, R: [422](422-n09-a-correccion-verificada-recuperaciones-20261026.md), [425](425-n09-b-inspeccion-autoridad-verificada-20261026.md), [428](428-n09-c-operaciones-autoridad-verificada-20261026.md), [431](431-n09-d-reclamaciones-levantamiento-autoridad-verificada-20261026.md), [434](434-n09-e-fronteras-descifrado-verificadas-20261026.md), [438](438-n09-f-autoridad-rectificacion-verificada-20261026.md), [441](441-n09-g-evidencia-final-rectificacion-verificada-20261026.md), [445](445-n09-h-autoridad-destinatarios-verificada-20261026.md), [P/462](462-n09-p-autoridad-foto-reintroducida-verificada-20261026.md), [Q/465](465-n09-q-autoridad-apelaciones-verificada-20261026.md) y [R/468](468-n09-r-correccion-procesamiento-preprivado-20261026.md) | Defectos reproducidos corregidos y negativos/control legítimo verificados en sus fronteras. Revisión de fuentes, identidad y originales individualizada; no garantía universal de toda carrera o proyección privada |
| Referencia normal de colas, lecturas y decisiones | [S/470](470-n09-s-prerregistro-referencia-interactiva-20261026.md) y [S/471](471-n09-s-referencia-interactiva-verificada-20261026.md): procesamiento de cuenta, rectificación de publicación y reclamación, con colas ES/EN | Tres casos reales propios, 66 observaciones/16 grupos; 3 PASS/85,223 s QA, sin FAIL/ERROR/SKIP. Tiempo de servicio y SQL separados de preparación/QA/humano; no candidata de optimización |
| Avisos y fallos observables | [J/449](449-n09-j-referencia-outbox-verificada-20261026.md) y originales vigentes enlazados en la matriz | Lotes, continuación, skip_locked y adapter_failure con retry/failed e intentos observables; simulador local explícito. No entrega externa ni cadencia Beat inferida |
| Retención, purga lógica/física y recuperación | [I/447](447-n09-i-referencia-purgas-logicas-verificada-20261026.md), [K/451](451-n09-k-referencia-purga-fisica-verificada-20261026.md), [L/453](453-n09-l-referencia-reconciliacion-jobs-verificada-20261026.md), [M/455](455-n09-m-referencia-alertas-retencion-verificada-20261026.md), [N/457](457-n09-n-referencia-objetos-huerfanos-verificada-20261026.md), [O/459](459-n09-o-referencia-purga-exportaciones-verificada-20261026.md), puentes de evidencia N03/N06/N07 | Vencidos, vigentes/pins, progresión y fallos parciales verificados en cohortes finitas; archivos y RustFS locales cuando procedía, broker real sólo en sus testigos concretos. No extrapolar latencia entre wrappers, naturalidad del vencimiento o almacenamiento/proveedor de producción |
| Regresión y conservación | Fuentes y funciones contrastadas, JUnit original y archivos auditados por etapa, selecciones actuales de cada corrección; fuente nativa de producto intacta en S | Identidades y oráculos comprobados por root. El run histórico global ERROR y los diagnósticos fallidos originales permanecen fallidos; sólo se reutiliza cada PASS individual aplicable. No sumar ejecuciones distintas como una batería global |

SHA-256 de la matriz actual: `f48a73550e1b55feceaa40eecd3cabb9b1e6e349830d67531fe0fe2f822b84bb`. La matriz anterior y su SHA permanecen en469: la actualización no reescribe la evidencia de la brecha previa.

## Tabla de referencia y después

| Etapa o corrección | Antes / referencia anterior | Estado o referencia actual | Después de otra candidata de rendimiento |
| --- | --- | --- | --- |
| Cola de derechos ES, un expediente | Sin base normal equivalente inspeccionada | Primera 155,940 ms; mediana de cinco posteriores 21,264 ms; 7 SQL | Sin candidata |
| Inspección nueva de plan | Sin base normal equivalente inspeccionada | 328,939 ms y 122 SQL; N=1 | Sin candidata |
| Aprobación nueva de rectificación | Sin base normal equivalente inspeccionada | 655,886 ms y 222 SQL; N=1 | Sin candidata |
| Resolución upheld nueva de reclamación | Sin base normal equivalente inspeccionada | 86,576 ms y 26 SQL; N=1 | Sin candidata |
| CopyInformation, lote de 100 vencidos | Referencia I: 5,991 ms y 2 SQL | Conservada, sin repetirla ni transferirla a otros modelos | Sin candidata |
| Outbox, 100 avisos simulados | Referencia J: 1.402,331 ms y 802 SQL | Conservada; fallos/reintentos siguen observables | Sin candidata |
| Purga de exportaciones, lote de 1.000 del volumen 1.001 | Referencia O: 2.097,922 ms y 1.007 SQL | Conservada; efectos locales y retención verificadas | Sin candidata |
| Plan privado tras revocación durante espera, R | New descifra antes de denegar; replay devuelve cuerpo privado | Ambos deniegan antes del descifrado seleccionado; diez casos correctos, tabla QA por pareja en468 | Corrección de autoridad; sin comparación de latencia normal |

La tabla completa de los 16 grupos, con primera muestra, cinco seguimientos cuando proceden, rango, SQL y límites, está en471 y su evidencia compacta. Son tiempos instrumentados de etapas concretas; no percentiles, garantía de mezcla pública ni total humano del procedimiento. Las primeras y siguientes llamadas del mismo producto no son un antes/después de optimización. No se acredita una mejora causal por comparar creación con replay, éxito con denegación o baterías de distinto tamaño.

Decisión técnica: conservar las implementaciones actuales tras las correcciones necesarias. Las referencias finitas no muestran un defecto adicional o incumplimiento de presupuesto de estos escenarios que justifique otra candidata. Los costes quedan visibles, incluidos los 222 SQL de rectificación; no se eliminan controles para reducirlos ni se abre una búsqueda de mejora marginal. Los objetivos y FAIL2s/5s de MOD09 no se convierten a PASS ni se aplican a estos endpoints privados.

## Alcance de la aceptación

La selección responde al riesgo y a formas diferentes de trabajo: cuenta frente a publicación, lectura auditada frente a decisión independiente y reclamación con outbox; las referencias asíncronas cubren volumen/progresión, concurrencia y fallos seleccionados. Las restantes acciones conservan su disposición individual, fuentes, invariantes, originales y límites. No reciben una latencia prestada por pertenecer a la misma familia. Se acepta la evidencia suficiente de los escenarios elegidos, no una medición exhaustiva de todos los endpoints, backlogs o calendarios.

La nueva referencia comparó 173 modelos instalados, relaciones automáticas, permisos/sesiones y ocho archivos por caso; efectos exactos, replay sin duplicados y publicación intacta. La revisión técnica propia y los reportes nativos no se confunden: los reportes son propuestas; root verificó fuente, originales, ejecución y custodia. El escritor S no ejecutó pruebas ni modificó aplicación. Los IDs inmutables de imágenes S se observaron durante la ejecución y no estaban en reference-freeze previo; se conserva explícitamente ese límite en471, sin afirmar un prerregistro perfecto ni repetir QA válida.

No quedan defectos N09 confirmados abiertos en los escenarios aceptados. Esto no certifica toda autorización posterior a la última lectura ni todo contenido interno; las incertidumbres de fuente `moderation.decide` y `match_review.resolve` permanecen para la revisión integrada pertinente de N11, sin presentarlas como vulnerabilidades reproducidas o caminos seguros. Los supuestos legales/humanos y proveedores permanecen fuera de lo acreditado con sintéticos.

## Continuación obligatoria

N10 debe conciliar su inventario propio y los cuatro comandos/ocho runbooks compartidos: ensayos operativos locales aplicables, identidad, autoridad, efectos, limpieza y recuperación; registro no equivale a ejecución. N11 congelará y conciliará la candidata integrada, regresión común, exclusiones, deuda e incertidumbres de fuente. Esta acta no los acepta por anticipado.

N15 sigue obligado a reconstruir el grafo completo antes del diferencial final, actualizar inventarios y relevo frontend, entregar el acta final y limpiar completamente artifacts como última acción operativa después del resumen duradero acordado. No limpiar ahora las evidencias que aún usa el contrato. La evidencia compacta S y la matriz actual están fuera de artifacts para esa custodia final.

Se conservan los 15 cambios laterales fuera del commit de desarrollo, alpha/noindex, las notificaciones Telegram y la rama master simple. El objetivo completo sigue activo; esta aceptación de N09 no declara finalizado el contrato.
