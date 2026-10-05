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
