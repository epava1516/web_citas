# N02A — comparación pareada de metadatos de imágenes

25 de octubre de 2026. [Protocolo360](360-n02-a-prerregistro-metadatos-imagenes-20261025.md), candidata instrumental1a63762, run20261025-124023-9c86548f. **5PASS,0FAIL/ERROR/SKIP**,24observaciones. [Auditoría](evidencias/n02-a-metadatos-auditoria-20261025.json), [evidencia y reproducción](evidencias/n02-a-metadatos-evidencia-20261025.tar.gz), [congelación corregida](evidencias/n02-a-prerregistro-v2-congelacion-20261025.json). N00/N01aceptados2/13;N02/N06abiertos,alfa. No cambia código de aplicación.

## Tiempos de la etapa: mecanismo individual frente a lote existente

Mismos sujetos, archivos, entradas, instrumento y proceso. Cada cohorte tiene1500revisiones/~16MiBJSON y16WebP reales/~64MiB. Seis parejas por cohorte con orden alterno; primera separada y cinco posteriores para mediana/rango. La medición incluye consultas/locks, lectura completa y SHA256, con DEBUG=False; excluye preparación y BEGIN/COMMIT. Unidad de todas las columnas temporales: milisegundos.

| Cohorte | Individual: mediana5 | Lote: mediana5 | Reducción absoluta | Reducción relativa | Rango individual5 | Rango lote5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 335.200 | 219.565 | 115.635 | 34.497% | 295.762–367.329 | 207.162–231.429 |
| 2 | 324.301 | 238.831 | 85.470 | 26.355% | 305.446–408.613 | 209.001–244.039 |

Primera pareja: cohorte1 individual316,472ms/lote216,107ms; cohorte2 individual343,211ms/lote221,322ms. No se afirma caché fría: la preparación toca los archivos y el SO puede servirlos de caché. No hay cuotas dedicadas ni carga concurrente de los dos sujetos. Cinco muestras posteriores no permiten afirmar p95/p99.

Cada observación conserva16aperturas/lecturas completas por la interfaz de almacenamiento y todos sus hashes; no son lecturas de disco físico forzadas. Volumen por llamada67095050bytes/cohorte1 y67095042/cohorte2, idéntico entre métodos. MetadatosSELECT48individual/3lote:45menos,93,75%menos consultas de esta etapa. Orden/contenido/filas intactos en todas las muestras. No hay caché de bytes ni digest sustituyendo lectura.

**La reducción temporal es una comparación de mecanismos existentes; no una mejora integrada de la aplicación.** El llamador _verify_current_images permanece con image_content por declaración. Este resultado justifica estudiar el candidato, pero no acredita autorizaciónHTTP, entrega completa, cola, generación, concurrencia contractual ni cumplimiento de MOD09. No se traslada26,355–34,497% a una descarga completa. Los objetivos2s/5s, FAIL anterior y excepción provisional conservan su alcance.

## Corrección funcional, fallo conservado y limpieza

Los cuatro testigos originales pasan sin cambios:64lecturas en cuatro llamadas, frescura/pertenencia/duplicados/orden, cambio de mapping durante espera real de Blob y lectores inversos con PostgreSQL. El lector single de ese último test sólo lee una imagen: no prueba ausencia universal de interbloqueos entre dos recorridos single de varias imágenes ni con bulk. Antes de integrar hay que contrastar locks reales de los llamadores y negativos de contenido/autoridad/rollback.

El [primer intento](evidencias/n02-a-intento-inicial-20261025.json) conserva4PASS/1FAIL en calibrated_rows, sin muestras. Se corrigieron sólo etiquetas del instrumento a las del generador original; no generador, límites ni tamaños. La repetición completa verifica también aislamiento tras crear las cohortes grandes; el fallo no se borra ni se cuenta comoPASS.

Auditoría independiente: cinco casos exactos,15eventos setup/call/teardownPASS,24muestras finitas, pares completos y mismo digest/volumen por cohorte. Fuentes congeladas intactas antes de documentar; contenedores propios y temporal retirados, aviso terminalTelegramsent. Pytest informado102,50s; comando del runner104,551s incluyendo arranque de pytest y preparación. Ambos son tiempoQA, no latencia de aplicación. La auditoría ampliada comprueba también journal/selección/temporal; no repite la aplicación.

## Siguiente decisión y alcance pendiente

[Revisión independiente del llamador](evidencias/n02-llamador-investigacion-20261025.json) aceptada sólo como análisis de fuentes:21SHA contrastados y rutas clave inspeccionadas por el principal. El sello válido reproduce SELECTs del validador completo, incluidos locks de imágenes, antes del guard físico; no se demuestra un deadlock nuevo por sustituir este guard. Falta observarlo en PostgreSQL y verificar regresiones del llamador; sin adopción. Antes de cambiar: comprobar sello/replay y transacción, autoridad y pertenencia tras esperas, orden de bloqueos y errores, relectura física/rollback; prerregistrar candidato y regresión adversarial y medir la misma etapa integrada. Cobertura/entrega completa y sus otros costes siguen pendientes de atribución y verificación; N02no se cierra con este ensayo. Cuenta/representación/crecimiento de N06 y los demás bloques obligatorios siguen abiertos conforme a341.
