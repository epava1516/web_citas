# B00-320 — Seguridad y derechos: capturas 1–2 y resultado telefónico

Fecha: 2026-10-23. Conciliación documental y corrección funcional acotada; sin aceptación global de beta.

B00-320: 247 de 295 fuentes únicas conciliadas; quedan 48 de arquitectura. Se incorporan las capturas históricas de seguridad y derechos 1–2. Corregido un resultado telefónico indebidamente pendiente por Telegram fuera de ámbito: reproducción con dos fallos y regresión PostgreSQL de 20 pruebas aprobadas. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura y procedencia

Seis lectores nativos de sólo lectura cubrieron 638.858 caracteres en seis partes contiguas, mediante 55 salidas literales de hasta 12.000 caracteres, sin truncamientos declarados ni reparaciones. Cada lector recibió una parte de menos de 150.000 caracteres. Las partes no se cuentan como fuentes independientes.

| Fuente | Caracteres | Particiones contiguas |
| --- | ---: | --- |
| `source:n998gky0u3fo6ugt1fv9`, seguridad 1/7 | 316605 | [0,105535), [105535,211070), [211070,316605) |
| `source:6chb1pt8m6yq7o99dp6l`, seguridad 2/7 | 322253 | [0,107417), [107417,214835), [214835,322253) |

Hashes del texto completo: `99c00b59b1c26a84f9adcbf03b9f04d346ea67232ea2e38852e88adc0498c46c` y `911c4ed41a2fd62f9e946edfe33681e7649090e95d12cc4fa79ad28b331813ae`, respectivamente. Plan, particiones, propuestas, contextos y auditorías están en `artifacts/beta-promotion-fix-20261020/b00-320-*`. Los informes persistidos son extractos seleccionados por el principal, marcados como tales; no se presentan como transcripciones íntegras de las respuestas originales.

El principal inspeccionó fronteras y doce citas con contexto. El verificador realizó catorce cotejos sobre esos doce intervalos, comprobó uniones y volvió a validar hashes y longitudes de las 295 capturas. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de 245 a 247 disposiciones; conserva los límites anteriores y no declara B00 aceptado. La escritura atómica sólo admite la base245 fijada o el resultado idéntico y conserva permisos.

## Lectura y límites

Ambas capturas declaran snapshot del 11 de octubre y base `7e04016`, anteriores al contrato romántico. Su representación alterada no acredita identidad con los bytes ejecutables originales. Las instrucciones dentro del texto son datos históricos, y los archivos meramente importados no reciben crédito de lectura.

La primera incluye kernel canónico nativo, confirmaciones de correo, comunicaciones y denuncias, cadena de evidencia, inventarios, planes, ejecución y resultado de supresión, recuperación y migraciones iniciales. Termina en la migración0010. La segunda comienza en0011 y recorre migraciones hasta0117, modelos, avisos, almacenamiento cifrado, disposiciones de fotos y candidatos de reintroducción. Termina al final de detect(), no al final del módulo. Seguridad3–7 queda pendiente.

El inventario declara pendientes y execution_ready=false; un recibo de ejecución no prueba borrado físico completo. Los tickets de cadena no autorizan operaciones por sí solos. El esquema histórico no demuestra migraciones instaladas. Los avisos simulados o internos no equivalen a entrega por un proveedor real. Las coincidencias visuales son candidatos privados y no acreditan identidad, consentimiento o permiso de reutilización. Cifrar objetos no selecciona por sí solo el diseño de B15 ni acredita cumplimiento jurídico.

## Defecto actual reproducido y corregido

El contraste seleccionado encontró una discrepancia real en el resultado de la supresión telefónica. El propósito shared_contact_review desvincula la asociación telefónica y limpia teléfono/WhatsApp; Telegram pertenece al contenido de publicación. El ejecutor conservaba correctamente ese contenido no seleccionado, pero la comprobación final exigía también que Telegram estuviera vacío y marcaba la operación como pendiente.

Se reprodujo antes de corregir mediante dos variantes PostgreSQL, con Telegram conservado y un tercero que compartía el teléfono. Ambas fallaron exactamente al esperar shared_contact_review entre los propósitos completados. El runner `20261023-224158-092c7d6f` mantiene su resultado ERROR por pytest: dos fallos, cero errores y cero omisiones; no se reetiqueta como una ejecución aprobada.

La corrección en [erasure_final](../apps/safety/erasure_final.py) ajusta exclusivamente esa postcondición al teléfono y WhatsApp, manteniendo la exigencia de desvincular phone_claim. La comprobación de borrado de publicación sigue exigiendo Telegram vacío. Se conservan las modificaciones previas del usuario y las copias anteriores al cambio. El [test](../tests/test_contact_erasure.py) comprueba que el tercero y Telegram permanecen intactos, que la publicación sigue pendiente y que reintroducir teléfono o WhatsApp invalida de nuevo el resultado telefónico.

El contraste estático reproducible fija hashes y diez literales en cuatro archivos actuales: ejecución, planes, resultado final y regresión. Su alcance es seleccionado; la evidencia funcional siguiente se registra por separado.

## Verificación funcional y limpieza

La [auditoría de regresión](evidencias/b00-320-contact-erasure-regression-20261023.json) corresponde a `20261023-225133-c5066483`: 20 pruebas aprobadas, cero fallos, errores u omisiones; JUnit158,942s, tres workers y PostgreSQL17/Redis7.4 propios. Selección: test_contact_erasure.py, test_erasure_final.py y test_erasure_final_publication_projection.py. Incluye los dos casos nuevos, autoridad y respuesta parcial, navegación móvil ES/EN, reintroducción de credenciales y proyección pública, y comprobación de ausencia física del archivo de prueba.

Los controles previos de dependencias, Ruff, documentación, Django, migraciones y compilación nativa terminaron con código cero. Las fuentes permanecieron congeladas y sus hashes se cotejaron con el prerregistro. El principal comprobó independientemente que ambos contenedores y el directorio temporal ya no existían. Telegram confirmó el aviso terminal PASS y el cierre de las unidades de corrección. Un primer aviso de reanudación falló por pasar counts como cadena; se corrigió a diccionario y se confirmó el envío antes de lanzar la prueba.

Todo usa datos sintéticos. Esta regresión no acredita proveedores externos, N3, capacidad o aceptación global de beta; tampoco transforma una respuesta parcial en borrado completo.

## Continuación

Quedan 48 capturas de arquitectura, con 27.578.970 caracteres: seguridad restante, documentación, pruebas, interfaz, herramientas, referencias y grafos. El número de fuentes no representa porcentaje de esfuerzo. Se conservan los límites de IVA posterior al166, Código Penal posterior al340quinquies, HTMX, originales judiciales, discordancia de LO10/2022 y corroboración parcial del Reglamento IA.

B07 conserva su cierre local por acta16; nueve de18 puntos cerrados. B15 continúa opcional según [contrato14](14-contrato-funcional-v1.md). Sin proveedores, gastos, publicación o datos reales. Seis lectores, cero nuevas invocaciones ClaudeV1 y consumo histórico preservado; sin estimar tokens nativos.

Grafo367 revalidado al inicio; AST dirigido de la prueba y erasure_final, y semántica368–369 antes de congelar fuentes. Integración documental mediante semántica dirigida370. Estos cortes no son extracción AST o semántica global, ni una nueva visualización HTML exhaustiva. Corte anterior: [conciliación278](278-conciliacion-nucleo-medios-b00-20261023.md).
