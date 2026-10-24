# B00-331 — Pruebas de portabilidad, objetos y autoridad

Fecha: 2026-10-24. Conciliación de capturas históricas y contraste estático acotado.

B00-331: 271 de 295 fuentes únicas conciliadas; quedan 24 de arquitectura. Completada la lectura de las once capturas de pruebas, con portabilidad, objetos, autoridad e interfaz contrastados en fuentes actuales. Sin cambios de aplicación o pruebas, defecto nuevo demostrado ni nueva aceptación funcional. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Procedencia y disposición

Nueve lectores nativos nuevos de sólo lectura, máximo tres simultáneos, cubrieron 921.203 caracteres en nueve partes. Se emitieron y leyeron 85 intervalos contiguos de hasta 12.000 caracteres Unicode por salida, sin truncamientos declarados. Los informes guardados son extractos seleccionados del principal, marcados como tales; no son transcripciones completas. Se conservan las ocho invocaciones Claude V1 históricas y su consumo; cero nuevas V1, sin estimación de tokens nativos.

| Captura | Fuente | Caracteres | Particiones |
| --- | --- | ---: | --- |
| Pruebas y verificacion — parte 9/11 | `source:aip1oxdboy54a6f6qyv3` | 326369 | [0,108789), [108789,217579), [217579,326369) |
| Pruebas y verificacion — parte 10/11 | `source:9bs1ik0dm0aapoc7dvmd` | 300698 | [0,100232), [100232,200465), [200465,300698) |
| Pruebas y verificacion — parte 11/11 | `source:n8ltvkevg3bdqkycuvia` | 294136 | [0,98045), [98045,196090), [196090,294136) |

Huellas completas verificadas:

- `source:aip1oxdboy54a6f6qyv3`: `c2a8d4dc42bbede33cd5eca452d621e6b866a9e4c47d4bd26794409d58ed2964`.
- `source:9bs1ik0dm0aapoc7dvmd`: `4e69f29cbf6a55e96b002550c0e0acaf6d4ed32712f1823f4acd9c85ad4bdbae`.
- `source:n8ltvkevg3bdqkycuvia`: `7831760d2d38a263433a1e137bc1c05bf8a2a2a8c46f462d6f9b5d39f402307f`.

Las capturas declaran snapshot 2026-10-11 y base 7e04016. Contienen alteraciones de formato; la última además escapa numerosos guiones bajos. No se normalizaron las posiciones para las citas ni se acreditan bytes ejecutables actuales, lectura de imports o documentos solamente referidos. El principal cotejó las nueve huellas declaradas, dieciocho citas y contextos/fronteras. El verificador efectúa veintiún cotejos sobre esos dieciocho intervalos, verifica las tres uniones completas y revalida las 295 capturas. La disposición se acepta por fuente completa, no contando cada lector como fuente. Un lector informó un cwd antiguo, pero aclaró que todas sus lecturas usaron la ruta absoluta designada del worktree vigente; coincidieron las huellas y citas contra ese original. Se conserva la aclaración, sin atribuirle una lectura reparada o nueva.

El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de 268 a 271 disposiciones, y de 27 a 24 pendientes. Base268 fijada por SHA256, actualización atómica y permisos conservados; el verificador sólo admite esa base o su resultado exacto. Artefactos `artifacts/beta-promotion-fix-20261020/b00-331-*`; los informes no acreditan ejecución de pruebas.

## Contenido conciliado

La captura9 reúne sellos y cadena de evidencia, roles PostgreSQL, exportaciones/retención, ampliaciones de plazo, lectura física de imágenes, información ligada a políticas, ingreso/enlace/mensajes, equivalencia canónica nativa, inventarios, codecs, entrega privada, clientes de objetos, caches locales a operación, paquetes y cierre. Se diferencia autenticación LOGIN de SET ROLE; una comprobación de contexto falso no acredita PostgreSQL. Las pruebas nativas pueden omitir casos si falta un kernel validado; fallback no demuestra ejecución nativa.

Los tests de objetos distinguen mocks de orden/limpieza y procedimientos con RustFS local fijado por digest. El diseño espera verificación física fresca, cierre de cuerpos/clientes, autenticación antes de revelar bytes y tombstones que impidan revivir objetos borrados. Reutilizar transporte o un digest no reutiliza autoridad ni elimina auditorías por cada hijo. Los límites de entradas/bytes y el escenario finito de 64 lecturas/16 hashes no prueban RSS, pico combinado o capacidad contractual. Un umbral de empaquetado reducido tampoco acredita la carga nominal.

La captura10 cubre cierre concurrente, compilación y persistencia de cobertura, páginas/lecturas originales, revisión independiente y consumo, exportaciones y selección de imágenes/campos, trabajos durables, respuesta final y revisiones. Compilación coherente no equivale a autorización, persistencia o revisión independiente. Cobertura completa puede mantener simulation=true y final_response pendiente. Acuse, descarga, emisión y cierre tienen registros y requisitos distintos; hechos de procedencia o elegibilidad introducidos por fixtures no son conclusiones jurídicas.

Las pruebas de trabajos sustituyen dispatch en recorridos de dominio y ejecutan jobs.run directamente. Los procedimientos Redis/Celery se definen por separado. Polling móvil con jobs.run controlado no acredita un broker real. La relación entre límites de tarea y lease no demuestra que la generación cumpla su tiempo objetivo. Los escenarios de historial/imágenes grandes reconstruyen contenido sintético y registran tiempos; algunas imágenes se crean ready sin atravesar ingestión. Eso limita la conclusión sobre el flujo completo y la sanitización.

La captura11 completa selección, prioridad, grants privados, aclaraciones, rectificación, respuestas, sellos/huellas y verificación/retirada; incluye orígenes retenidos Redis/logs, SQL de búsqueda, formularios, redacción de medios compartidos, teclado, registro, sitemap, envíos, denuncias urgentes y comparación de workers. Las comprobaciones de viewport y localización no establecen accesibilidad completa o calidad de traducción. Un experimento secuencial de workers no se convierte en gate de carga por su nombre. Los fixtures históricos con lenguaje profesional o representación no sustituyen el contrato romántico vigente.

## Contraste actual y límites

Se contrastaron catorce archivos actuales y treinta literales: diez módulos de pruebas y cuatro módulos de producción. Las selecciones incluyen LOGIN/validación de sellos, mocks frente a RustFS, exportación cubierta tras espera observada, trabajos y publicación durable, cierre del contexto de transporte, caducidad final del sello, actor fresco en respuestas/replay, grants separados, medios compartidos, documento de búsqueda sin autoridad y límites de la comparación de workers. Son fragmentos estáticos seleccionados, no revisión completa de esos subsistemas ni resultados de ejecución.

El código seleccionado conserva comprobación de prueba antes de publicar el trabajo durable, reseteo del contexto de clientes, revisión de caducidad después de reproducir resultados SQL y recarga del actor tras bloqueo antes de responder/reutilizar una respuesta. Las aserciones actuales distinguen tokens y lecturas físicas frescas, conservan archivos de terceros y excluyen perfiles cuya autorización se retira. No se ha demostrado un defecto nuevo en esta selección. Sin cambios de aplicación o pruebas; no se ejecutó ni repitió ninguna batería funcional por esta lectura. Las correctivas320/321/322/329/330 y la capacidad B07 mantienen sus cortes y alcances propios, sin aceptación adicional.

El primer borrador del contraste usó worker en vez de pid para un literal de observe_blocked. La preparación se detuvo antes de guardar el artefacto o modificar el ledger; se corrigió contra la línea real y se conserva nota auxiliar. No fue un fallo del producto ni motivo para repetir pruebas.

Grafo384 revalidado antes del análisis; integración semántica dirigida385 al incorporar este documento y seguimiento. Sin nuevo AST global, semántica exhaustiva, HTML global o nueva medición de capacidad. Se conservan las limitaciones de referencias externas y self-loops del sello.

Quedan 24 fuentes y 20,058,684 caracteres de arquitectura, con interfaz, herramientas, referencias y grandes grafos pendientes. El número de fuentes no expresa porcentaje de esfuerzo. B00 sigue abierto; no se cambia el orden de beta ni se declara cumplimiento legal o producción. B15 conserva la dirección ya documentada en contrato14§6.1: cookies propias para visitante y evaluación de preferencias privadas cifradas con cuenta; formato/ubicación de objetos, claves y retención pendientes, sin implementación o cumplimiento RGPD por el mero cifrado. Sin publicación, contratación, gasto o datos reales. Corte previo: [conciliación289](289-conciliacion-derechos-supresion-b00-20261024.md).
