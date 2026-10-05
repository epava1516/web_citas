# Cobertura declarada de portabilidad — base técnica parcial

Fecha:2026-10-05. Requisito:REQ-CR09-PORTABILITY-COVERAGE-01. Estado:validador puro; persistencia, interfaz y aceptación integral pendientes.

`apps/safety/rights_portability_coverage.py` contrasta declaraciones con fuente, evaluación y selección ya suministradas por el llamador. No concede permisos, no consulta archivos, no guarda datos y no aprueba ni cierra un derecho. La coherencia de una declaración no demuestra su verdad ni suficiencia jurídica.

## Declaraciones exactas

La evaluación debe cubrir los9conjuntos conocidos y no contener pending. La proyección seleccionada conserva las condiciones propias de campos mixtos. `omissions` contiene exactamente los9conjuntos, también vacíos. En conjuntos elegibles/granulares, cada fila con hojas no seleccionadas tiene una declaración `{all: condiciones_excluded}` para todas las omitidas o `{fields: {path: condiciones_excluded}}` con caminos exactos. Las condiciones excluded exigen motivo/evidencia y un hecho negativo definido según el validador de evaluación; unknown por sí solo no basta. Filas ajenas o ya enteramente elegidas se rechazan. Una exclusión de conjunto declarada en la evaluación cubre sus filas sin decisiones adicionales contradictorias.

Los binarios se cuentan aparte. Seleccionar `/images/.../photo` o todos sus metadatos no incluye bytes. `images` debe cumplir declaraciones de imagen elegibles y `image_omissions` cubrir exactamente los UUID de fuente no incluidos, con condiciones de exclusión propias. No se permite incluir y excluir el mismo UUID ni repetir referencias binarias en fuente. Exclusión de revisions cubre sus binarios sin declaraciones contradictorias.

La salida `portability-coverage-v1` resume filas/hojas e imágenes incluidas/excluidas y contiene la proyección elegida. El estado covered indica coherencia de declaraciones, no revisión independiente. No devuelve motivos, evidencia ni referencias HMAC de las filas; el llamador debe conservar y firmar las declaraciones exactas por separado si las persiste.

## Evidencia y trabajo restante

16pruebas unitarias correctas0,47s, XML `/tmp/portability-coverage-schema-final.xml`: faltantes/unknown/filaajena/evaluaciónpendiente/formabinaria inválida, caminos omitidos exactos y vacíos, metadatos frente a bytes, exclusión de conjunto y condiciones propias de campos mixtos. No PostgreSQL ni archivo leído por esta batería.

Pendientes: cuerpo cifrado/firma ligada a selección y fuente/prueba/actor/versiones; autoridad fresca y clave global; lectura privada paginada de datos omitidos y páginas exactas; revisor independiente; interfaz ES/EN; inventarios/purga; consumo de aprobación y vínculo a entrega/respuesta final/cierre. Caso/fuente/canal/prueba caducados o revocados deben bloquear uso/replay después de esperas observadas. Estas condiciones figuran en actas/04-cr09-auditoria-pendiente.md y no están satisfechas por el validador.

La regresión conjunta62398 fue recogida antes de añadir este módulo/test y no los verifica. El módulo no está importado por los flujos actuales ni incorporado al runtime Docker; no cambiar esa situación hasta aplicar su integración y comprobarla.
