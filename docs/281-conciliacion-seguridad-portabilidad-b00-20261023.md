# B00-322 — Seguridad, portabilidad y autoridad de consulta privada

Fecha: 2026-10-23. Conciliación documental y corrección funcional acotada; sin aceptación global de beta.

B00-322: 252 de 295 fuentes únicas conciliadas; quedan 43 de arquitectura. Las siete capturas históricas de seguridad tienen disposición textual. Corregida una consulta privada de denuncias que conservaba autoridad revocada tras bloqueos: reproducción con cuatro fallos y regresión PostgreSQL de 31 pruebas aprobadas. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura y procedencia

Siete lectores nativos de sólo lectura cubrieron683.050caracteres en siete partes, con61salidas literales contiguas de hasta12.000caracteres. Cada parte recibió un contexto fresco de menos de150.000caracteres, con un máximo de tres lectores simultáneos. Sin truncamientos declarados ni reparaciones de lectura o serialización. No hay nuevas invocaciones ClaudeV1 ni estimaciones de tokens nativos; su consumo histórico se conserva.

| Fuente | Caracteres | Particiones contiguas |
| --- | ---: | --- |
| `source:bl4c4x5ylza9auieh2t1`, seguridad5/7 | 313029 | [0,104343), [104343,208686), [208686,313029) |
| `source:cst7ib7ihogamoa9vzom`, seguridad6/7 | 308213 | [0,102737), [102737,205475), [205475,308213) |
| `source:6rzqxurveepeg9rnwdaj`, seguridad7/7 | 61808 | [0,61808) |

Hashes completos respectivos: `7414ac63ba36cd8991cc8075e23f9ea006625f50f863fd65598df21ded53843e`, `988a81f747bb9bcd6178783147ffbc67f5da94a52dcc37706c9f90c1dbc3ad4d` y `638315aa60fa64cbed10ead6e204b61416b91cd80643e78008f5a1320244b611`. El principal inspeccionó fronteras y catorce citas con contexto; el verificador realizó diecisiete cotejos sobre esos catorce intervalos, comprobó las uniones y volvió a validar hashes y longitudes de las295capturas.

Plan, protocolo, tareas, propuestas, extractos, contextos, contrastes y auditorías están en `artifacts/beta-promotion-fix-20261020/b00-322-*`. Los informes persistidos son extractos seleccionados y marcados, no transcripciones íntegras de las respuestas. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de249a252disposiciones y de46a43pendientes, mediante reemplazo atómico que conserva permisos y sólo admite la base249 fijada o el resultado idéntico. La integración requiere también la auditoría positiva de la corrección actual. Las partes no se cuentan como fuentes distintas.

## Interpretación histórica

Snapshot11/10/2026/base7e04016, anterior al contrato romántico y con formato alterado. No son bytes canónicos ejecutables ni instrucciones vigentes. No reciben crédito los archivos únicamente importados o referidos. Las fronteras internas atraviesan archivos, mientras la unión cubre cada captura completa.

Seguridad5 comienza en rights_access_supplement_views y termina en rights_portability_coverage_review. Incluye cuenta propia y representación, acciones y comunicaciones, revisión paginada de copias, inventarios, exportaciones, información y política versionada, objetos privados y cobertura de portabilidad. Organización propietaria no equivale a autoridad sobre todos sus perfiles. Una copia parcial, un censo o una excepción revisada no resuelve por sí sola la solicitud.

Seguridad6 comienza en rights_portability_coverage_review_views y termina en rights_validation_seal. Incluye inspección y uso de cobertura, exportación, imágenes, trabajos durables, selección paginada, reinicio explícito de borrador, respuesta y revisión, rectificación, ámbitos y aceleradores opcionales. Cobertura declarada, selección aprobada, respuesta final y entrega son decisiones distintas; las revisiones deben conservar pruebas, versiones, páginas y actores correspondientes.

Seguridad7 comienza en rights_verification y termina en views.decision. Incluye verificación sintética, tareas de caducidad/purga, alertas urgentes, rutas e ingreso/consulta de denuncias. La verificación sigue excluida en producción y no acredita proveedor real. Enumerar rutas no acredita los módulos importados.

Con los cortes [279](279-conciliacion-seguridad-derechos-b00-20261023.md), [280](280-conciliacion-seguridad-acceso-b00-20261023.md) y éste, las siete capturas tienen disposición textual. Esto no equivale a lectura de todos los bytes del módulo actual, auditoría exhaustiva de seguridad o aceptación técnica de todos sus flujos.

## Contraste actual seleccionado

Se fijaron hashes y32comprobaciones literales en12archivos actuales, con el alcance limitado de b00-322-current-contrast.json. Las pruebas funcionales se registran aparte.

| Materia | Evidencia y límite |
| --- | --- |
| Entrega privada | rights_object_views exige secreto de proxy, GET reenviado, ausencia de Range y URI acotada. rights_object_delivery relee dominio, caducidad, generación, descriptor y vínculo, comprueba archivo regular/tamaño/hash y consume la concesión. La aplicación verifica el archivo y el proxy abre posteriormente su ruta; el aislamiento y la identidad al servir requieren evidencia de despliegue distinta. No se ha demostrado un actor no autorizado capaz de sustituirlo. |
| Optimización pura | rights_operation_fingerprints compara valores y secreto actual dentro de límites de operación. rights_operation_content_digests sólo reutiliza el digest de bytes recién leídos e iguales dentro del contexto adecuado. Ninguno valida acceso o evidencia. |
| Sellos y origen | rights_validation_seal vincula resultados consumidos, configuración, llamadas y caducidades, rechaza entradas no soportadas y retorna al camino completo ante errores. rights_inspection_source impide conservar el contexto entre operaciones y detecta mutación o deriva antes de devolver. Estos fragmentos no prueban todo el comportamiento de PostgreSQL, orden o concurrencia. |
| Política y selección | rights_information_policy comprueba documento publicado y digest, sin aprobación jurídica. rights_portability_reset_selection exige confirmación y baseline vigente y conserva el historial. Reiniciar borrador no autoriza exportar. |
| Actores y trabajos | rights_copy_page_review comprueba sesiones/MFA actuales. rights_portability_jobs conserva credenciales originales, revalida autoridad/prueba, liga intentos a tokens y limita reintentos. La fila durable y un envío al broker no acreditan finalización. |
| Verificación y texto | rights_verification mantiene simulación fuera de producción y caducidad/ámbito. rights_response_text verifica texto motivado y minimizado, sin conceder acceso ni autoridad de cierre. Estas piezas no seleccionan almacenamiento B15 ni acreditan RGPD por usar cifrado. |

Las hipótesis de los lectores quedan en b00-322-reader-hypotheses.json: orden de auditoría interno, soportes de parámetros SQL, correspondencia de familias de filas, contexto de cachés y ruta de entrega. No se elevan a fallos actuales por comentarios históricos. La falta de refresco de autoridad en consulta de denuncias sí se reprodujo como se describe abajo.

La cola ordinaria de denuncias aún materializa candidatos antes de filtrar conflictos. Queda registrada como candidata a paginación SQL acotada para B08; no se declara optimizada o medida en este corte.

## Defecto de autoridad reproducido y corregido

[views.inspect](../apps/safety/views.py) comprobaba permiso y MFA antes de esperar los bloqueos del expediente, pero conservaba request.user para autorizar el descifrado posterior. La reproducción `20261023-232549-7314c0f1` falló en las cuatro variantes de revocación: permiso, versión de sesión, versión MFA y cuenta inactiva, con HTTP200 frente403. Runner ERROR y cuatro fallos, cero errores u omisiones, se conservan como reproducción negativa.

El intercalado de revocación es controlado al obtener el expediente bloqueado; las consultas PostgreSQL, HTTP, autorización y descifrado son reales sobre datos sintéticos. No se afirma una espera concurrente real ni acceso de un sujeto real.

Se extrae sin relajar su contenido la comprobación fresca existente de alertas urgentes a [report_authority](../apps/safety/report_authority.py). La consulta la aplica tras los bloqueos y antes de descifrar, usa ese actor para permisos/registro y repite la comprobación antes de devolver. Si la autoridad cambia durante la lectura, responde403privado y revierte el registro de acceso de esa transacción. La ruta de alertas urgentes conserva las mismas condiciones de autoridad.

Los [tests nuevos](../tests/test_report_inspection_authority.py) cubren ocho variantes: cuatro revocaciones tras bloqueo y las mismas durante el descifrado. Exigen rechazo, ausencia del contenido en la respuesta y ausencia de ReportAccess; también comprueban no haber descifrado antes de una revocación temprana y las cabeceras privadas. En la variante tardía el descifrado inicial ocurrió bajo autoridad válida, pero la respuesta se bloquea y el registro se revierte. Se conservan las modificaciones previas y los backups/delta propio.

La [auditoría positiva](evidencias/b00-322-report-authority-regression-20261023.json) corresponde a `20261023-233146-c4ca9ca1`:31pruebas aprobadas, cero fallos, errores u omisiones; JUnit156,029s, tres workers y PostgreSQL17/Redis7.4 propios. Selección: test_report_inspection_authority.py, test_report_inspection.py y test_urgent_report_alerts.py. Incluye flujos privados y móviles, conflictos, acceso motivado, reconocimiento concurrente y revocación en alertas, además de las ocho variantes nuevas.

El intento positivo previo `20261023-233002-ecb281bf` se detuvo en Ruff por orden de importaciones; no ejecutó pytest y mantiene ERROR. Se corrigió únicamente ese orden y se revalidó el grafo antes de repetir. Dependencias, Ruff, documentación, Django, migraciones y compilación nativa del intento aceptado terminaron con código cero.

Las fuentes se mantuvieron congeladas y sus hashes se cotejaron con el prerregistro. El principal comprobó independientemente contenedores y directorio temporal ausentes, y el recibo Telegram PASS más los cierres de las unidades de corrección. No se acredita proveedor real, carga N3, capacidad o aceptación global de beta.

## Continuación y grafo

Quedan43capturas de arquitectura,26.276.756caracteres: documentación, pruebas, interfaz, herramientas, referencias y grandes grafos. El conteo no representa porcentaje de esfuerzo. Se conservan los límites de IVA posterior al166, Código Penal posterior al340quinquies, HTMX, originales judiciales, discordancia de LO10/2022 y corroboración parcial del Reglamento IA.

Grafo373 revalidado al inicio. AST dirigido del test y archivos afectados y semántica374–375 antes de congelar fuentes; el orden de importaciones motivó otro refresco dirigido sin ampliar semántica. Integración documental mediante semántica dirigida376; sin AST/semántica global ni HTML nuevo exhaustivo. B07 mantiene acta16 y B15 sigue opcional; nueve de18puntos cerrados. Sin publicación, contratación, gasto o datos reales. Corte anterior: [conciliación280](280-conciliacion-seguridad-acceso-b00-20261023.md).
