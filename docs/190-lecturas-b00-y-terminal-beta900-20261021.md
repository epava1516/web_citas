# Lecturas B00 y cierre de la secuencia beta900

B00 y B07 siguen abiertos; ocho de dieciocho puntos cerrados localmente. El [terminal189](189-protocolo-beta-http-900s-b07-20261021.md) conserva INVALID por máximo del generador, sin repetición automática.

## Fuentes leídas durante la espera

La [procedencia de dos fuentes DB](evidencias/b00-additional-db-source-provenance-20261021.json) verifica capturas completas pytest-django Database access27696caracteres y Django5.2 Database access optimization35366caracteres. Son dos IDs adicionales a los trece identificados anteriores, no una auditoría global de295fuentes ni documentación online actual verificada. No se ha aplicado una optimización por estas lecturas.

pytest-django exige preservar aislamiento, repoblación tras flush, migraciones y separación de bases por worker. reuse-db no adapta automáticamente cambios de esquema; desbloquear acceso no revierte escrituras. Django aconseja medir consultas y memoria: only/defer o exists/count pueden añadir consultas. Lectura del Django5.2.17 instalado corrige dos generalizaciones de la captura: QuerySet.get limita resultados cuando backend/bloqueos lo permiten; Collector.delete contempla señales y comprueba listeners antes de fast-delete. No justificar por esa captura que delete masivo siempre omite señales.

La [procedencia del registro de vigencia](evidencias/b00-control-register-provenance-20261021.json) añade un ID distinto,9309caracteres completos; conjunto identificado16, sin aceptación B00. Sus afirmaciones291fuentes/189contexto/102sintexto son históricas y el propio registro las corrige con textos originales e indexación en curso. No acreditan estado actual, finalización de cola, defectos actuales de API ni comprobación jurídica. Los cuatro originales legales no identificados siguen pendientes; reinicios o eliminaciones narrados no se han ejecutado.

## Continuidad

La comprobación de procedencia se ejecutó tras el terminal, no durante la carga. Se conservan ocho invocaciones V1 históricas y su consumo; ninguna nueva. La siguiente investigación B07 debe explicar la invalidez del generador con evidencia existente y fijar un protocolo nuevo antes de cualquier nueva carga. No modificar umbrales ni atribuir causalidad a partir de una coincidencia temporal. Permanecen las mezclas y garantías pendientes de la matriz180.
