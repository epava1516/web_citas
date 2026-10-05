# Portabilidad de conjuntos con origen mixto

Estado: implementación parcial verificada; exportación y aceptación integral pendientes. No aceptación de CR09. Complementa las condiciones y fuentes de docs76 y el flujo de docs77. Los registros de avance inferiores conservan el orden histórico; el último describe la cobertura vigente.

## Problema actual

La evaluación por conjuntos rechaza mixed como eligible. Esto protege frente a exportar todo un conjunto, pero todavía impide seleccionar su parte admisible: relaciones de agencia, revisiones o verificaciones pueden contener campos con procedencias distintas. No resolver esta limitación declarando provided a todo el conjunto ni excluyéndolo automáticamente.

## Evaluación y selección

Introducir un estado explícito de evaluación granular para conjuntos que requieren decisiones por campo. La evaluación del conjunto sigue ligada a su fuente, prueba, versión y revisión independiente. Su aprobación habilita preparar decisiones granulares; no aprueba ningún valor por sí sola. Desconocidos sin evaluación suficiente permanecen pendientes.

Cada decisión granular identifica conjunto, referencia HMAC de fila y camino escalar, más base, origen, automatización, relación con el interesado, revisión de terceros, motivo y evidencia. Incluir un campo requiere condiciones elegibles explícitas para ese campo. No heredar automáticamente las del conjunto ni permitir contenedores. Mantener diferencias entre facilitado, observado, inferido, tercero y mixto según la evaluación documentada existente.

El cuerpo cifrado de selección conserva las decisiones granulares junto a los selectores. Firmar ambos en guardado, edición por páginas, consulta, revisión y uso. Un cambio de evidencia o condición invalida el replay y la aprobación anterior igual que un cambio de campo. La revisión independiente muestra los valores y las decisiones antes de permitir aprobar o rechazar, sin restaurarlos en GET.

## Edición y cierre

Las páginas siguen vinculadas a consulta exacta, actor, épocas, prueba, fuente y base de borrador. Editar una página preserva selectores y evidencias de las otras; desmarcar un campo elimina su inclusión, y cambiar su evaluación no puede dejar una aprobación aplicable. Reiniciar crea un borrador vacío y conserva auditoría histórica.

La copia generada incluye únicamente campos seleccionados y aprobados, sin motivos, evidencia interna, identificadores de auditoría ni huellas HMAC privadas. Una decisión pendiente o inferida no habilita incluir ese campo. La respuesta final debe reflejar alcance y omisiones evaluadas; no declarar portabilidad integral solo por exportar una selección parcial.

## Evidencia requerida

Probar origen mixto con campos del interesado y de terceros en una misma fila, manipulación de evidencia/firma/vínculo de consulta, campos adicionales por cliente, corrupción de cuerpo, fuente o prueba cambiadas, caducidad y épocas revocadas durante bloqueos observados. Cobertura de perfil y cuenta, edición por páginas, revisión independiente, aprobación/rechazo, inventarios no vacíos, purga, HTTP y móvil ES/EN, exportación y descarga revalidadas. Repetir regresión común y runtime actualizado antes de entregar. Mantener identidad sintética y producción real diferenciadas.

## Avance inicial

Estado granular y guardas de campos implementados. Un conjunto mixto aprobado habilita evaluación por hojas, pero una selección no vacía exige evidencia exacta de todas sus hojas con condiciones elegibles. Evidencia forma parte de cuerpo cifrado y firma; consulta independiente muestra datos y evidencia, uso devuelve únicamente valores seleccionados. Un conjunto granular vacío no autoriza ningún campo. Editor de páginas rechaza modificar un cuerpo con evidencia granular hasta implementar preservación y edición de esas decisiones; no elimina evidencia silenciosamente. Unitarias9 correctas0,50s; persistencia/revisión/uso HTTP PostgreSQL en prueba.

Persistencia/revisión/uso inicial verificados en batería12 (9unidad+3PostgreSQL/HTTP)55,27s: metadatos elegibles por campo cifrados y firmados, campos de tercero rechazados, firma de evidencia impide replay distinto, consultaPOST muestra evidencia, GET la oculta y uso entrega proyección sin evidencia interna. Copia y cierre completos siguen pendientes, al igual que editor granular UI y cobertura de perfil/concurrencia.

Edición de decisiones por páginas backend inicial añadida: campo granular en token, hechos de página visibles solo tras consulta auditada; decisiones entrantes corresponden exactamente a campos elegidos. Preserva campos y evidencia de otras páginas, y desmarcar elimina únicamente la inclusión/evidencia de la página editada. Guardado cifra y firma selector más todas las decisiones. Pruebas PostgreSQL en curso; formulario granular en pantalla aún pendiente.

Edición por páginas verificada en2 pruebas PostgreSQL/HTTP49,55s: nuevos campos preservan otras hojas y evidencia, cambio de origen por campo queda firmado, desmarcar elimina solo evidencia correspondiente. Flujos previos de páginas/reinicio y revisión/uso pasan. Formulario granular de hechos todavía pendiente.

Formulario granular conectado y verificado con PostgreSQL/cliente Django:2 pruebas49,64s. Controles por hoja traducidos, máximo50, caminos exactos de página firmada y condiciones elegibles para campos marcados. Precarga evidencia tras consulta auditada; hechos de tercero/path sustituido rechazados, cambio de base queda cifrado/firmado/revisable y evidencia desaparece de GET/guardado. Móvil, perfil y carreras específicos todavía pendientes.

Preparación/revisión móvil granular ES/EN verificadas junto al recorrido simple:4 pruebas PostgreSQL/Chromium390px83,35s. Autor completa condiciones/evidencia por campo en UI, revisor separado ve hechos tras consulta y aprueba; proyección aprobada posterior no incluye evidencia interna. Datos/evaluación previa sintéticos. Perfil y carreras granulares específicas, exportación y aceptación integral todavía pendientes.

Concurrencia granular terminal verificada: sesión11404 exit0,14 correctas y14 variantes simples deseleccionadas120,81s; XML /tmp/portability-mixed-observed-races.xml y log homónimo. Perfil/cuenta × replay/conflict/permission/proof/session/mfa/source, evidencia elegible exacta por hoja mostrada en consulta independiente, dos conexiones y holder con bloqueo observado. Replay decide una vez; conflicto admite una decisión; revocación/cambio durante espera rechaza ambas sin acciones parciales. Inventarios no vacíos conservan selección/lectura/decisión en admisiones para ambos ámbitos. Ejecución separada, no sumar como pruebas únicas a suites anteriores. Carreras restantes de guardado/lectura/uso/reset, exportación/descarga/respuesta final/runtime0088/workerBeat/regresión común y contrato entero siguen pendientes.
