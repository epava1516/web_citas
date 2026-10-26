# N07C — prerregistro de colas, formularios y decisiones

25 de octubre de2026. Alfa, base34c3f30. N07 permanece abierto6/13bloques obligatorios. Contratos340/354/S03-A, roadmap341, inventario39IDs y aceptaciones parciales402/405 conservados. Objetivo: completar referencias de servicio/HTTP donde sólo había testigos funcionales. No hay candidato de aplicación ni campaña de optimización marginal.

## Corte y selección

Corte previo verificado sin diferencias:2017fuentes,19245nodos/82681relaciones/922comunidades, SHA998dda2edc5f3ad510ebb22bdd0c08e5105ad0e5e22f322105c981258234effb. Refresco focal AST/semántica nativa acumulada, no reconstrucción global ni evidencia runtime. Consulta del grafo con vocabulario moderation/appeal/queue/match y contraste de handlers, modelos, fixtures y middleware.

Un escritor nativo creó un instrumento en worktree aislado34c3f30, propiedad exclusiva de tests/test_listing_review_queue_reference.py y su reporte; Codex leyó el archivo completo, transitividad de fixtures y fuentes antes de integrar. El reporte no acredita ejecución. Root añadió reactivación del idioma después de fixtures con peticiones /es/, comprobación de LANGUAGE_CODE/Content-Language reales y una medida separada de formularios positivos. Lint previo aprobado; sin cambios de producto.

Lote previsto: **16casos**: ocho del nuevo instrumento (cuatro familias×ES/EN) y ocho testigos originales sin editar. Las familias son cola de moderación de anuncios, reclamaciones de anuncio, coincidencias de fotos y reclamaciones de fotos. Fixture y oráculos nativos existentes; PostgreSQL real desechable propio y almacenamiento sintético. Preparación eager declarada fuera de los relojes GET; no broker/worker, proveedor o navegador acreditados por este lote.

## Colas y formularios

| Familia | Estado poblado y oráculo independiente | Transición real hasta vacío |
| --- | --- | --- |
| Moderación | Una revisión pending de la fixture y su enlace exacto | POST approved del revisor; revisión aprobada y cola0 |
| Reclamación de anuncio | Cola0, POST del titular crea una reclamación y enlace exacto | POST upheld independiente; reclamación resuelta y revisión sigue rechazada |
| Coincidencias | Dos IDs recíprocos de la pareja, orden por fechas distintas de fixture | POST distinct_people; ambas resueltas y cola0 |
| Reclamación de fotos | Una reclamación de la fixture, ID/enlace exactos | POST upheld independiente; reclamación resuelta y cola0 |

Por idioma/estado: primera GET y cinco posteriores, sin vaciar caché de OS ni llamar fría a la primera.18segmentos de cola y108GET; formularios de revisión abiertos: ocho segmentos y48GET adicionales, separados. Pared, CPU del proceso, SQL de esa conexión/tiempo de execute y bytes lógicos de respuesta. El formulario debe corresponder al objeto solicitado, contener form y conservar200/private,no-store. No sumar las dos superficies ni tiempos de estados distintos.

Cada GETpositivo exige idioma real de request y Content-Language coincidentes con ES/EN; el metadato de parametrización por sí solo no prueba traducción. Cola: IDs/orden/conteos exactos, sin duplicados, enlaces presentes y desaparición al terminar. Anónimo302, propietario sin permiso403, sesión MFAobsoleta302hacia desafío y revocación real de permiso403; restaurar MFApara continuar. Sin enlaces privados en denegaciones. SecurityHeadersMiddleware exige private,no-store en respuestas autenticadas; no se inventa ese header en redirección anónima.

Se representa deliberadamente0/1/2elementos mediante flujos válidos, porque se busca lectura/autoridad/transición de estas familias sin candidato de crecimiento. El límite100de los handlers se contrasta en fuente; este lote no acredita tiempo o capacidad al máximo100. La frecuencia/volumen reales son desconocidos y el producto sigue en alfa. Una señal de coste que justifique comparación se estudia con una ficha equivalente antes de cambiar producto; sin mejora clara se aplica el diferimiento expreso del usuario, sin quitar correcciones funcionales o de seguridad.

## Decisiones y testigos originales

Ocho selectores existentes, sin reescribir cuerpos ni negativos:

- tests/test_listing_moderation.py::test_permission_mfa_self_review_rejection_and_concurrency
- tests/test_listing_moderation.py::test_approval_exposes_exact_revision_and_only_derivative
- tests/test_appeals.py::test_appeal_private_idempotent_and_independent_review
- tests/test_match_review.py::test_confirmed_conflict_pauses_publication_and_remains_blocking
- tests/test_match_review.py::test_exact_not_false_positive_and_permissions_cover_both_people
- tests/test_photo_appeals.py::test_photo_appeal_reopens_pair_without_publication_or_counterpart_data
- tests/test_photo_restrictions.py::test_photo_restriction_notice_is_private_and_has_no_other_account_data
- tests/test_match_review.py::test_distinct_authorized_people_resolves_both_directions_without_suspension

Cubren aprobación/rechazo, versión exacta, derivados, consentimiento retirado, independencia y coincidencias, resolución simultánea, reintentos, reapertura sin publicación automática y ausencia de datos de la contraparte. Son flujos ES concretos; la nueva referencia de colas/formularios sí comprueba ES/EN. El plugin existente http_operation_metrics, aceptado en N01D, añade sólo observación Client.request/SQL en call. No se vuelve a probar por documentación; se ejecutan aquí esos selectores para obtener la referencia HTTP/servicio aún ausente, manteniendo sus oráculos.

La concurrencia del caso original de rechazo conserva dos conexiones/hilos y resultados302/400; no se mezcla su espera de lock con decisiones seriales. El plugin guarda orden de finalización, no una cronología completa de inicios. Las denegaciones previstas no constituyen errores de carga. Snapshot/validación/transacción/formulario permanecen dentro de la operación HTTP pertinente; no se adjudican tiempos internos individuales que el observador no separa.

## Instrumentación, comando y límites

Comando: `.venv/bin/python scripts/run_local_ci.py --profile focused --workers 1 --timeout 900 --native-source /tmp/web-modelos-librdb-v2.4.0 --observe-http-operations --test tests/test_listing_review_queue_reference.py` más un `--test` por los ocho selectores anteriores. Sin switches de carga. Congelar fuentes, selección, instrumentos, dependencias y manifiesto nativo después del refresco focal de grafo y antes de ejecutar. Si no se confirma un selector o el modelo/fixture, resolver antes; no sustituir oráculos para que pase.

En el nuevo instrumento hay dos capas de observación SQL/HTTP sobre la misma llamada; no sumar sus consultas/tiempos como trabajo distinto. Las medidas GETpropias separan preparación/POST/controles. El journal global de esos ocho casos puede incluir las peticiones de fixtures solicitadas dinámicamente durante call; no adjudicarlas como lectura pura de cola. En los ocho casos originales, setup ordinario queda fuera de call. Cualquier excepción/fallo del observador invalida la muestra correspondiente y se conserva. Campos seguros: familia/idioma/estado/ruta nombrada/status/tiempos/contadores/bytes/header; no cuerpos, URLs con IDs, credenciales, razones o sujetos en métricas/Telegram.

Client no acredita TCP/Internet ni reloj humano de revisión. El tiempo de una FileResponse termina al construir la respuesta si su cuerpo se consume después: la lectura de imagen no es una nueva medida de descarga completa; N05/399 conserva el transporte con cuerpo. CPU del proceso no es CPU de PostgreSQL. No p95/p99, crecimiento100, carga, proveedor ni apertura. CSRFy otras autoridades conservan testigos específicos previos; Client estándar no es nueva prueba de CSRFreal.

Salida: JUnit exacto16casos, métricas finitas y oráculos completos, tabla de referencias por familia/superficie/estado/idioma con primera/mediana5/rango/SQL/bytes, operaciones originales agrupadas sin mezclar ramas y limpieza propia/Telegram sent. Los errores/FAIL/timeout se preservan, no se convierten en PASS. QAse informa aparte de latencia. N07no queda cerrado automáticamente por este lote: falta conciliar39disposiciones y reutilización de testigos con identidad, tareas/retención y otros propietarios compartidos N09/N10. N03/N04/N05/N06/N07A/N07B conservan sus ámbitos; MOD09 restante al final.
