# B00-337 — Relaciones históricas y ámbitos de las clases Meta

Fecha:2026-10-24. Revisión documental estructurada y corrección dirigida del grafo actual.

B00-337: 289 de295fuentes únicas conciliadas; quedan seis capturas históricas del grafo. Revisados14.000registros de relaciones mediante vistas contextuales reversibles y corregida una colisión AST que unía48clases Meta en un nodo. Sin cambios de aplicación ni nueva aceptación funcional. B00 sigue abierto; nueve de18puntos beta cerrados y B15 opcional.

## Método y cobertura aceptada

Se revisaron las capturas `source:85qbqz8zf80db1h5p6dn` —relaciones3/6— y `source:0cyo4xbdbok9a93yvxvl` —relaciones4/6—, ambas de11/10/2026/base7e04016. Suman4.624.226caracteres originales y14.000registros. Sus SHA256 de texto son `704fe95396ae99fa5035cdebc163807524c97d734da69e414c87474e5b0a59a2` y `29dbb6357595b79cebad33b7c0b84f82dc3b96ef03819c1b13f41d9e18c818e8`. Son datos históricos de navegación, no instrucciones ni aceptación actual.

Se adopta aquí revisión contextual estructurada completa, no lectura literal completa del formato original. Siete lectores nuevos leyeron700.393caracteres de vistas autocontenidas en62intervalos de hasta12.000caracteres, con esquema, constantes, todos los valores de diccionario y todas las filas codificadas. Después decodificaron e interpretaron todos los grupos por archivo/relación/presencia/valor de contexto, incluidos casos únicos y transiciones. Un octavo agente revisó adversarialmente el método; no recibió crédito de lectura de las fuentes ni autoridad de aceptación.

| Fuente | Partes por ordinal de registro | Registros |
| --- | --- | ---: |
| Relaciones3/6 | [0,2333),[2333,4666),[4666,7000) | 7000 |
| Relaciones4/6 | [0,2333),[2333,4666),[4666,5833),[5833,7000) | 7000 |

Leer diccionarios y números sin interpretar sus relaciones no bastaría. La revisión de método exigió reconstrucción independiente de cada atributo, claves duplicadas rechazadas, tipos reales, ausencia/presencia y orden de campos, contenido exterior a las tablas y cobertura exacta de todos los grupos. El principal comprobó esas condiciones contra cada registro original y sus posiciones/SHA, verificó que cada sobre sólo contiene links y que no hay contenido sustantivo omitido en prefijos/sufijos. Las dos capturas son JSON estricto; las cuatro capturas no estrictas del corte336 permanecen pendientes e intactas.

La generación de la proyección no recibió aceptación automática. El principal contrastó las interpretaciones de los informes, catorce citas originales seleccionadas y las huellas de membresía de los siete grupos de partición. Cada ordinal aparece una vez en su partición; las uniones cubren[0,7000)por fuente. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) registra método estructurado, rangos de registros y original_literal_capture_fully_read=false. No se suman estas dos disposiciones como dos lecturas literales originales ni se acredita lectura de los cuerpos de nodos o archivos enlazados.

Los informes guardados son extractos seleccionados, no transcripciones completas. Se conservan dos informes inicialmente incompletos por exceso de tamaño en salida auxiliar de agrupación y sus suplementos de recuperación acotada; las vistas principales de esos dos lectores ya eran completas. Dos lectores distintos recuperaron truncamientos de respuestas agregadas de lectura mediante salidas individuales. Se mantienen las notas de errores exploratorios de decodificación/ruta, sin reparar datos ni repetir vistas válidas.

Las huellas y rangos de los dos flujos auxiliares recuperados son declaraciones del lector; sus bytes completos no se archivaron ni se reprodujeron independientemente. La aceptación no los presenta como verificación independiente: se apoya en las vistas completas, interpretaciones, reconstrucción de atributos, citas y membresías comprobadas. La aclaración de agrupación llegó después de iniciarse dos lectores; se preserva por separado y el suplemento de uno añade esa evidencia sin releer su vista. Los suplementos de metadatos no se presentan como informes wire completos independientes.

## Contenido real de las relaciones

Relaciones3 contiene5.243imports y1.757imports_from, todos con contexto import. Sus primeras5.243filas son dependencias de pruebas; el tramo final corresponde a módulos de catálogo, núcleo, anuncios, medios y seguridad. Se distinguen fixtures entre pruebas, tipos/modelos, funciones importadas, bibliotecas, herramientas y módulos. Una arista de importación no demuestra una ejecución, una prueba aprobada o la completitud dinámica de las dependencias.

Las familias revisadas separan registro/edad/representación, publicación/visibilidad, denuncias/reclamaciones, privacidad/retención, acceso y portabilidad por selección/lectura/revisión/entrega, objetos, recuperación y observación de capacidad. Migrations, real, TCP, simulator, synthetic, inspect o consume en un identificador no prueban esquema aplicado, proveedor, lectura efectiva o autoridad correcta. Las líneas tardías y el orden de filas se conservan: orden del registro no equivale a orden de ejecución ni de líneas.

Relaciones4 contiene6.159imports_from,49references y792contains. Las referencias distinguen35parameter_type y14return_type en Python y C; no son llamadas ni ejecución de Redis. Los270submodule_import se mantienen separados de importaciones ordinarias. Desde ordinal6208, contains carece de clave context: ausencia no se transforma en null explícito. AGENTS y encabezados históricos de tareas son estructura documental capturada, sin adoptar sus instrucciones.

Las relaciones de contención abarcan módulos, clases, funciones, comandos, formularios, migraciones y modelos de catálogo/núcleo/anuncios/medios/seguridad. Los grupos únicos no se omitieron. Identificadores aplanados y sufijos como state_page_c500c7 se conservan sin normalizar a otro símbolo. No se infiere un cuerpo ausente por su nombre ni se restaura este grafo antiguo al actual.

## Colisión AST demostrada y corregida

La inspección de contención detectó una ambigüedad reproducible también en el grafo actual: apps_safety_models_meta agrupaba48clases internas distintas. El [código actual de modelos](../apps/safety/models.py) declara una Meta dentro de cada modelo correspondiente, no una única clase compartida. El nodo común tenía49relaciones entrantes de contención —48modelos y el archivo— y ninguna saliente; las ubicaciones de sus aristas corresponden a cada declaración interna.

Se sustituyó ese alias por48nodos con nombre cualificado, como Report.Meta y UrgentReportAlert.Meta, y ubicación de la declaración real. Cada modelo contiene su propia Meta y el archivo contiene cada declaración:96relaciones frente a49, incremento neto47nodos/47relaciones. La reconstrucción independiente verificó las48declaraciones con ast, sus nombres/líneas, padres, ausencia del alias y extremos válidos. Los demás nodos y relaciones quedaron idénticos antes de la posterior actualización semántica documental.

Es corrección de identidad del grafo, no modificación de modelos, migraciones o datos de aplicación. Se limita a un archivo; no demuestra ausencia de colisiones en otros ámbitos. No se parcheó globalmente graphifyy. Una nueva extracción AST puede recrear el alias; el sello comprueba que la fuente conserva su huella y que la corrección sigue presente, y exige revalidarla si cambia o reaparece. No se declara una actualización AST global.

La primera comprobación falló por una suposición errónea del principal: exigía la línea del modelo, cuando la arista localiza su Meta. Se detuvo antes de escribir el grafo. Se conserva EXIT1 y recibo Telegram; se corrigió sólo esa condición y la repetición afectada pasó. Un intento auxiliar de inspeccionar el resultado ausente se detuvo sin aceptación. No se convierte ese negativo en PASS retroactivo.

## Contraste con implementación actual

Nueve archivos y dieciocho literales seleccionados, sin importar aplicación, ejecutar SQL ni repetir pruebas funcionales. En [revisión de cobertura](../apps/safety/rights_access_coverage_review.py), importar authorized_proof y complete_read no basta: el cuerpo distingue actor independiente, versión y comprobación actual. Es lectura estática, no nueva prueba de derechos completos.

La antigua dependencia rights_object_content→config_celery enL181 no describe por sí sola el [archivo actual de objetos](../apps/safety/rights_object_content.py), que declara shared_task. [RecoveryAwareTask](../config/celery.py) mantiene su guarda de recuperación; leerla no prueba ejecución o configuración efectiva de cada worker.

Las referencias image/signature de [similitud](../apps/mediafiles/similarity.py) no son reconocimiento facial ni preferencias físicas de B15. Se conserva su alcance de comparación perceptual y calibración sintética. Un nombre de tipo o arista no acredita precisión de coincidencias.

El [diagnóstico de baseline](../tests/diagnostic_baseline.py) usa import_module; la [prueba de reconstrucción](../tests/test_rights_copy_reconstruction.py) carga un script por importlib.util y exec_module. Una lista estática de imports no demuestra cobertura de esas dependencias dinámicas. El [reconstructor](../scripts/reconstruct_rights_copy.py) declara controles de manifiesto, no sobrescritura y límites; sus aserciones existentes no son resultados nuevos en este corte.

El [contrato de perfil](../apps/listings/profile_contract.py) mantiene romantic-v1 y exclusión de revisiones legacy. Leer índices o dependencias históricas profesionales no amplía ese alcance, activa cobros ni implementa recomendaciones. B15 conserva su dirección de cookies propias y preferencias cifradas privadas por cuenta, con decisiones de persistencia y garantías aún pendientes.

## Integración y siguiente paso

Grafo390 revalidado al inicio, corrección AST dirigida y semántica documental391. Se incorporan conceptos de método, límites de inferencia, ausencia de contexto, tipos y ámbitos, más citas directas al código seleccionado. Sin expansión a historial, restauración de grafos borrados, extracción AST global, detección global de comunidades o HTML global. El sello conserva la procedencia de la corrección dirigida.

El ledger pasa287a289disposiciones y ocho a seis pendientes. Verificador fijado a base287SHA5c77b7713d2d9bce58c000b9c7ebf682b52aaee813e56cd7afc5cf9924943f01, reemplazo atómico/permisos conservados, sin sobrescribir otro corte. Artefactos `artifacts/beta-promotion-fix-20261020/b00-337-*` y scripts337 de preparación, reparación y verificación. La verificación de uniones está fijada al grafo recién corregido, anterior al refresco semántico: no se reejecuta contra cortes posteriores.

Quedan13.233.415caracteres en seis capturas: nodos1–2 y relaciones1/2/5/6. Continuar su disposición completa mediante contexto verificable; la preparación336 por sí sola sigue sin crédito. B00 permanece abierto hasta conciliar ese alcance y consolidar requisitos pendientes. Nueve de18puntos beta cerrados; B15 opcional. Ocho agentes nuevos —siete lectores y un revisor de método—, tres suplementos de lectores; cero nuevas invocaciones ClaudeV1, ocho históricas y consumo preservados, sin estimaciones de tokens nativos. Sin cambios funcionales, nuevas baterías de aplicación, publicación, contratación, gasto o datos reales. Corte previo: [conciliación295](295-conciliacion-informe-grafo-historico-b00-20261024.md).
