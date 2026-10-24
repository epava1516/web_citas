# B10-365 — Conciliación de exportación, similitud y deuda

B10 queda aceptado técnicamente en local como evaluación y disposición de optimización P2, conforme al [roadmap103](103-roadmap-beta-clasificados-20261020.md) y los [acuerdos320](320-acuerdos-alcance-b10-prioridades-20261024.md). No se traslada el análisis pendiente de B10 a otro contrato: se completa aquí con fuentes, medición, atribución y decisión. La [matriz literal de ocho requisitos](evidencias/b10-local-requirement-disposition-20261024.json) identifica evidencia y alcance. Catorce de18puntos cerrados; B14–B17 pendientes, B15 opcional. Seguimos en alfa.

## Exportación: resultado y decisión

El [contraste323](323-contraste-fuentes-mod09-b10-20261024.md) identifica cambios posteriores en nueve módulos seleccionados, sin equivalencia transitiva completa. La [medición325/326](326-auditoria-medicion-actual-mod09-b10-20261024.md) ejecuta el extremo vigente completo: dos sujetos concurrentes con1500revisiones/16MiBJSON/64MiBoriginales cada uno. Conserva fuentes, cuerpos, referencias y límites propios; no hay OOM y la limpieza se contrasta independientemente.

El instrumento sigue FAIL por cobertura p95 hasta3,377s y descargas JSON/binarias hasta6,600s/6,770s frente a objetivos2s/5s. El histórico llegaba a3,328s/6,717s/6,821s. Cobertura actual es ligeramente mayor; la variación entre cortes no demuestra por sí sola una regresión causal o una mejora, y no se presenta como PASS ni como cumplimiento del histórico. Generación actual40,67–40,74s. La aceptación provisional MOD09 mantiene su alcance de prioridad/bloqueo; no se amplía a otras garantías, fases o SLO.

Los [diagnósticos308](308-descomposicion-extremos-exportacion-similitud-b10-20261024.md), [309](309-atribucion-circuito-exportacion-b10-20261024.md) y [310](310-composicion-sql-cobertura-b10-20261024.md) separan canonical aislado, cobertura y consultas de conflictos/autoridad. No acreditan que una copia sea redundante ni permiten cachear autorización o eliminar locks. Decisión: conservar la implementación y los objetivos; coste residual como mejora de aplicación en el inventario, sin reabrir el alfa por las latencias provisionalmente aceptadas.

## Similitud: justificación del estrés elegido

La población pública y la deBlob no son equivalentes. Diez mil perfiles por ocho fotos ofrece80000referencias vigentes como referencia de dimensionado; reutilización debytes reduce blobs distintos, mientras el historial retenido puede aumentarlos. No existe un máximo de retención aprobado que permita convertir ese producto en un techo universal. La prueba10002Photo/cincoBlob sólo representa reutilización, nunca la capacidad con80000originales distintos.

Se eligieron dimensiones de estrés controladas para localizar coste sin presuponer ese techo:10/100/1000Blob distintos con cinco positivos entre negativos deterministas, y100originales distintos con100candidatos/confirmaciones reales. El [ensayo327](327-escenarios-crecimiento-densidad-similitud-b10-20261024.md) conserva igualdad exacta deMatch y archivos reales; los16testigos funcionales308 incluyen recomprensión, giro, recortes, negativos y poca información. La densidad100% fuerza trabajo de confirmación por candidato; no es una previsión comercial ni un peor tiempo universal.

Con1000Blob dispersos se observan3,20s/74SQL; con100densos14,39s/1214SQL, con CPU de confirmación6,37s y registro3,71s. El detector se ejecuta desde process_blob en Celery tras commit deingest; estos tiempos instrumentados no son latencia de subida HTTP, cola o procesamiento completo. El corpus preparado tampoco incluye decode/cómputo inicial de firmas dentro de la medida.

Decisión: mantener el detector exacto actual y la [propuesta CC05](97-propuesta-indice-similitud-fotos-cc05.md) sin tecnología adoptada. Un recuperador podría reducir el recorrido disperso, pero no eliminar la confirmación ni el registro protegido de verdaderos candidatos densos. La muestra no prueba que todo índice sea inútil, ni acredita un índice concreto; no hay motivo probado para añadir dependencia ahora. No se ocultan candidatos, retiran exclusiones o guardas, ni cambian formatos. B10 no añade optimización de producto, por lo que no existe una mejora antes/después ni despliegue nuevo que revertir; los instrumentos quedan aislados y versionados.

## Deuda y límites expresos

Quedan como deuda de aplicación, identificada y priorizable desde el inventario diferencial final: objetivos2s/5s deMOD09; recorrido con muchosBlob distintos; coste de confirmación y registro bajo densidad alta; volumen retenido, concurrencia de subidas, espera y drenaje de cola. No se acepta capacidad para80000fotos o historial ilimitado. Si una apertura pretende ese escenario deberá medirlo con recursos y presupuesto definidos; B16/B17 yG01–G08 no se aceptan por esta disposición.

Esta decisión completa la selección/atribución/disposición requerida por B10; no se basa sólo en dosPASS ni afirma una capacidad no medida. No eleva prioridad sin un incumplimiento aplicable distinto de la excepción MOD09. La prioridad futura acordada sigue siendo la optimización de recorridos de la aplicación; el contrato específico de optimización QA permanece aplazado a la primera versión estable/productiva.

## Salida de etapa3

B07/B08/B09/B11 tienen sus actas16/18/19/20. B10 aporta su evaluación y decisión sin cambio de producto. Cada optimización ya adoptada conserva comparación y reversión dentro de su alcance original; no se suman tiempos de versiones diferentes como una prueba conjunta. Esta conciliación no sustituye la auditoría común B16, las exclusiones, la reconstrucción completa del grafo ni la diferencia final del inventario.
