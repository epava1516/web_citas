# MOD08 — Siguiente vía tras el coste escalar — 2026-10-11

Deliberación solicitada por el usuario, con [resultados anteriores](mod08-scalar-consumers-20261011.md)
y opiniones reales de Claude y NotebookLM. [Transcripción completa](../../.ai/rooms/mod08-siguiente-20261011/transcript.md).
El turno extenso de NotebookLM fue rechazado como invalid request; el error queda registrado.
La consulta reducida posterior sí recibió respuesta. No se presume una causa del rechazo.
Claude actuó sin herramientas ni edición bajo la excepción previa; consumo conservado.

## Decisión

Preparar como siguiente trabajo **un solo bloque de 20 controles A/A**, sin optimización
productiva, antes de abrir otro diagnóstico. La variación de controles de aproximadamente
0.8 a 1.6 segundos, también en CPU, sigue sin explicación. El coste escalar de unos 23ms
no justifica perseguir esa rama para resolver un déficit de segundos.

1. Preservar modificaciones previas y congelar manifiesto exacto de fuentes, entorno/dependencias y fixture. No exigir árbol limpio ni modificar archivos durante runner. PostgreSQL/Redis privados reales, rolruntime separado, datos sintéticos, clon idéntico por request, commit normal y comprobación independiente de cuatro lecturas/ocho eventos. Mismo historial548eventos/1500revisiones/16MiB. Retirada comprobada al terminar.
2. Un único worker Gunicorn sync para eliminar mezcla de PIDs; escenario diagnóstico distinto de dosworkers y de capacidad contractual. Sin comparar absolutos como regresión o mejora. Fijar PID y comprobar backend nativo sellado efectivo desde ese worker fuera del cronometraje, sin dar por suficiente la validación del padre. Dos warmups reales descartados, verificados y contabilizados aparte. No refrescar/cambiar recursos globales ni deshabilitar/forzar GC.
3. Veinte controles secuenciales sobre veinte clones equivalentes, sin cProfile, SQLhooks, per-next ni nuevos spans internos. TCP completo y wall/CPUdelhiloWSGI con límites definidos, separar cierreWSGI que puede terminar después de cuerpoTCP. Registrar orden/PID y estadísticasGC. RSS/cargahost/metadatosPG sólolectura antes/después de bloques, fuera del reloj; sus correlaciones no prueban causalidad.
4. Compuerta predeclarada: cuantiles con interpolación lineal reproducible; P90-P10 <=10%medianaTCP y <=10%medianaCPU; diferencia absoluta entre medianas primeras5/últimas5 <=10%mediana del mismo indicador, paraTCPyCPU. Son heurísticas de reproducibilidad de ESTEcontrol, no umbral contractual ni prueba estadística de ausencia de bimodalidad. Publicar muestras, rangos, dispersión, deriva y cualquier anomalía/backend/PID/fuente que invalide la campaña. Límite20medidas+2warmups; ningún rerun automático por querer pasar.
5. Si falla o se invalida: terminar ese diagnóstico como variable/inconcluyente, sin candidata de rendimiento ni causa atribuida. No declarar cerrado o fallido todoMOD08. Si pasa: decidir con datos un segundo bloque independiente de pocas fases grandes existentes, concontrolesadyacentes y tiempos exclusivos sólorespectoahijosobservados. No ejecutar automáticamente bloquesB/C de Claude. No cronometraje de creación de generadores/contextmanagers como ejecución. No sumar inclusivos, no restaroverhead como ganancia.

Criterio para futura candidata: mecanismo concreto de trabajo evitable localizado por medición y conteo, semántica/frescura conservadas por código y pruebas concurrentes, comparaciónA/B independiente que supere ruido observado. No exigir una reducción previa a instrumentos que no cambian producto. No prometer2s/5s ni convertir20controlesenp95contractual.

Correcciones: source_copy es mayorentreconsumidoresobservados, no dominante demostrada delrequest. A/Aescalar no fue comparaciónoptimizada. Variación puede proceder de entorno/backend/GC u otros factores, no demostrado. No pausarGC. Spans anidados no inválidosporprincipio, requieren límites/costes claros. Claude propuso20+15+15=50medidas,no55, pero no se adopta ese presupuesto amplio. Notebook confundió medición conreducción y cierre de diagnóstico con cierre general; rechazado. ModeloNotebook desconocido; sin fuentes añadidas/eliminadas.
