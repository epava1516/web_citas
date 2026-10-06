# Copias de datos por paquetes: diseño de entrega

Estado: transporte por paquetes, descarga y reconstrucción verificados localmente; generación/revisión de gran volumen y aceptación integral pendientes. CR-09 sigue abierto.

## Requisito

Entregar datos ya revisados de la copia privada en paquetes de tamaño acotado cuando el JSON completo supere el umbral operativo. Mantener separación de sujeto, revisión, prueba, canal, caducidad, replay y auditoría actuales. No seleccionar datos nuevos ni declarar acceso/portabilidad integral por dividir archivos.

## Formato previsto

Serializar la copia revisada en JSON UTF-8, conservar el orden de los bytes y dividirla en fragmentos numerados dentro de ZIPs privados. El manifiesto indica identificador y posición de cada paquete, tamaño y SHA-256 del fragmento, además de tamaño y SHA-256 del documento completo. La reconstrucción concatena los fragmentos en orden, verifica sus hashes y el hash total, después decodifica UTF-8 y analiza JSON. Un fragmento individual puede terminar en mitad de un carácter; nunca decodificarlo por separado. Nombres fijos sin datos personales, rutas ni nombres originales.

## Integración y límites

Reutilizar RightsExportPart y su descarga privada ZIP. El manifiesto de la copia principal conserva indicadores de copia parcial/simulación y referencias a paquetes; los datos completos están en los fragmentos cifrados. Numeración continúa tras paquetes de imágenes. Caducidad y supresión técnica vacían también los paquetes de datos por el mecanismo existente. Las copias pequeñas conservan el formato actual.

Esta entrega acota el transporte por paquete. La fuente y la revisión actuales materializan el documento completo; generación asíncrona, revisión paginada y medición de grandes volúmenes siguen pendientes y deben acreditarse por separado. No convertir un límite de tamaño en una exclusión silenciosa de registros.

## Aceptación requerida

Reconstrucción idéntica con Unicode y fronteras de fragmento; ZIPs dentro del límite; hashes válidos; caso vacío/pequeño conservado; integración PostgreSQL preview/revisión/generación/acuse/descarga; rechazo de paquete de otro expediente, CSRF y replay; caducidad/purga; interfaz ES/EN y Docker. Probar corrupción sin registrar descarga exitosa.

Implementación: `apps/safety/rights_data_parts.py`, umbral operativo 8MiB; ZIPs de hasta 8MiB. El manifiesto usa schema rights-data-manifest-v1 y document_schema original, size/sha256 del JSON, encoding utf-8, data_parts por fragmento e imágenes en parts. La prueba de integración reduce el límite a4096 para verificar partición sin presentar ese ensayo como carga de producción.

## Reconstrucción local

Guardar el manifiesto JSON y todos los archivos `rights-data-part-N.zip` de esa copia en una carpeta privada. Con Python 3, sin Django ni conexión a la web:

```bash
python3 scripts/reconstruct_rights_copy.py manifiesto.json carpeta-paquetes copia.json
```

La herramienta no extrae rutas del ZIP, no envía datos a servicios, verifica hashes/tamaños/orden y UTF-8, escribe por bloques en un temporal0600 y crea el resultado sin sobrescribir un archivo existente. Si falla, elimina el temporal; la validación del contenido JSON original corresponde al generador. Guardar la copia de acuerdo con su sensibilidad; los archivos descargados quedan bajo control del destinatario y no se borran desde el servidor al caducar.

## Evidencia local de la entrega de transporte

Regresión común13901:40 correctas207,78s. Dirigida47135:3 correctas40,26s (móvil ESEN con umbral4096 y unidad de límite8MiB), no sumar como una sola batería43. Docker:5 hashes iguales en aplicación/worker/Beat, UID10001 y comprobaciones/health correctos. Evidencias copia-paquetes-regresion.json, copia-paquetes-movil-tamano.json y copia-paquetes-runtime.json. No acredita generación asíncrona, revisión paginada, POST8MiB, carga concurrente ni inventario integral de datos.

## Serialización incremental en desarrollo

La ampliación posterior sustituye JSON completo en bytes por JSONEncoder.iterencode y consumo por fragmentos. Prefijo hasta el umbral más un bloque decide si mantener copia pequeña; los ZIPs y el hash global se generan secuencialmente. La fuente/revisión aún materializa objetos y el encoder puede crear una cadena grande para un solo campo. Esta mejora no acredita memoria acotada de todo el procedimiento ni POST grande, generación asíncrona o revisión paginada. Batería59816 terminal0:23 correctas68,53s.

## Lectura por lotes en desarrollo

La prueba con30 revisiones adicionales reproduce14→193 consultas en la fuente antigua. La ampliación conecta geografía por select_related y cinco relaciones por prefetch, con iterator de50 revisiones y locks sobre Revision únicamente para permitir joins geográficos nullable. La salida completa aún se materializa; el lote reduce consultas y cachés intermedias, sin completar revisión paginada ni generación asíncrona. Batería8914 terminal0:33 correctas128,55s. Medición66900:31 revisiones12 consultas;81 revisiones17 consultas;2 correctas38,55s, evidencia separada. Runtime incremental verificado en copia-generacion-incremental-runtime.json.


## Preparación de origen, lote250 — 2026-10-06

Fuente5df91ea mantiene queryset/locks/orden/proyección e iterator con250 revisiones por lote. Comparación íntegra contra lote50 y relaciones pobladas/31 y281 revisiones correctas; batería afectada12 PG correcta. Primera página de cobertura sobre1500 revisiones/9893757bytes:764→284 consultas,11,529→9,940s instrumentados,41651227→41695648bytes pico Python. [Evidencia](evidencias/copia-origen-lote2500110.json), [Docker](evidencias/copia-origen-lote250-runtime0110.json). La materialización final de la copia permanece y el lote de revisiones no limita cardinalidad de todas las relaciones. No p95/throughput ni aceptación de cierre/descarga grande; seguimiento vigente en17.
