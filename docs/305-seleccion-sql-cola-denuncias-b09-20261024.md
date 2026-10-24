# B09-344 — Selección SQL de la cola de denuncias

La referencia343 verifica N+1: 30/210 consultas para 10/100 denuncias a agencia, con dos consultas por fila. B08 aceptado y once de 18 puntos cerrados. El grafo403 se revalida antes de este hito; no es extracción global nueva.

## Prerregistro de equivalencia antes del cambio

Se añade test_report_queue_selection_parity.py: siete casos PostgreSQL. Seis roles (moderador, particular, propietario, sujeto representado, editor activo/inactivo), cada uno con cuatro peticiones ES/EN y con/sin review_restriction, sobre 45 denuncias sintéticas que combinan nueve formas de objetivo y cinco estados. IDs completos, orden, unicidad, cabecera privada y ausencia del cuerpo privado frente a permitted actual. Se exigen además negativos conocidos y la diferencia entre pertenencia activa/inactiva. El séptimo caso cambia pertenencia y propiedad en base de datos y verifica seis peticiones siguientes con recuentos2/1/0/2/0/2. Las escrituras son fixtures de autoridad, no prueba de trámites productivos de transferencia o recepción pública de denuncias.

Antes de modificar aplicación se ejecutará ese archivo: siete casos, un worker y timeout1200s por comando en el runner oficial. La referencia de coste343 se conserva sin repetirla; fuentes de aplicación iguales. La selección posterior se declarará después de revisar esta primera ejecución.

## Diseño candidato

La cola conservará sus controles de permiso/MFA y la selección de estados. La pertenencia a agencia denunciada se excluirá con Exists sin filtrar active; la pertenencia a la agencia del perfil sí requerirá active. Propietarios, sujetos/particulares denunciados, actor y objetivo legacy sin manager_version permanecerán excluidos. Los predicados estarán en la consulta completa, sin prelimit; ordering del modelo se conserva. Se leerán únicamente los campos de la plantilla de cola. No se carga un mapa de autorización entre peticiones ni se reemplazan permitted/inspect.

Se guarda la fuente previa de views.py y las huellas AST de permitted/inspect. Cualquier cambio fuera de queue/import nuevo necesita justificación propia. Tras aplicar sólo se aceptará la optimización con oráculo funcional, mismo diagnóstico10/100, controles existentes de cola y reautorización privada afectados, fuentes/limpieza/Telegram y comparación explícita del número de consultas. No se atribuirá ahorro temporal a las dos muestras seriales. Imágenes/activos/backlog siguen pendientes B09.

## Referencia previa verificada y cambio aplicado

La ejecución20261024-054506-67458735 verifica siete PASS, cero fallos/errores/omisiones,87,568 s sumados JUnit y1714 fuentes congeladas. Los 24 comparadores de rol/idioma/permiso y seis cambios siguientes de autoridad pasan. Auditoría b09-344-baseline-audit.json con limpieza, identidad de proceso y Telegram verificados.

Se añade apps/safety/report_queue.py y queue lo invoca. Las exclusiones ORM con negación/Exists conservan casos NULL, objetivos y las dos clases de pertenencia; no hay límites ni consulta por fila. La selección pertenece al snapshot de la sentencia: no es autorización reutilizable para consultar evidencia privada. Sólo se proyectan id, fecha, motivo, modo y prioridad; no se hidratan modelos objetivo ni ciphertext que la plantilla no usa. AST del resto de views.py es idéntico al corte previo, excluyendo queue y el único import nuevo; permitted e inspect permanecen intactos.

Regresión prerregistrada:18 casos, cuatro selectores y tres workers, timeout1200s por comando. Siete del nuevo archivo de paridad, dos del instrumento de coste343 idéntico por bytes, el caso existente test_queue_permissions_mfa_coi_and_public_route_account_gate y ocho intercalados de autoridad privada de test_report_inspection_authority.py. PostgreSQL/Redis/nativos propios, sin navegador ni carga TCP. No se aceptará reducción de consultas sin paridad, cierre correcto y recibo Telegram. B09 permanece abierto.

## Regresión y comparación verificadas

La ejecución20261024-055055-56ead958 termina con 18 PASS, cero fallos, errores u omisiones;235,355 s sumados de casos JUnit, tres workers y94,71 s de pytest. La [auditoría correctiva](evidencias/b09-queue-corrected-audit-20261024.json) verifica1715 fuentes congeladas, limpieza de contenedores/temporal/proceso y envío Telegram. La [referencia de autoridad](evidencias/b09-queue-baseline-audit-20261024.json) conserva los siete casos previos.

| Denuncias | Consultas antes | Consultas después | Lecturas de agencia por fila después | Lecturas de pertenencia por fila después |
| --- | --- | --- | --- | --- |
|10|30|10|0|0|
|100|210|10|0|0|

La [comparación reproducible](evidencias/b09-queue-comparison-20261024.json) confirma el instrumento de coste idéntico por bytes al343, el archivo de paridad idéntico entre ambas fases y los mismos 24 resultados de rol/idioma/permiso y seis resultados de autoridad siguiente. Los ocho casos privados de reautorización pasan; permitted/inspect y el resto de views fuera de queue/import son idénticos por AST. De 629 archivos de producto previos,628 permanecen iguales, sólo cambia views.py y se añade report_queue.py.

La reducción es de viajes de consulta desde la aplicación, no de trabajo SQL constante. Persisten filtrado, subconsultas correlacionadas, ordenación y materialización de los casos permitidos; no se demuestra cota de memoria. Los workers y el calentamiento difieren entre cortes, por lo que no se atribuye ahorro de tiempo o CPU ni nueva capacidad a las muestras. No se añade índice ni límite arbitrario.

## Reversión y alcance restante

La reversión local consiste en deshacer únicamente el import y el cuerpo de queue identificados en b09-344-queue-only.diff, y retirar el helper propio si ya no tiene consumidores. No restaurar views.py completo desde un snapshot: contiene cambios previos del usuario que deben preservarse. Es un procedimiento definido, no una reversión ejecutada ni una prueba de despliegue productivo.

La optimización de estas dos familias N+1 queda verificada en el alcance funcional y de consultas descrito. B09 continúa abierto para imágenes/activos, observación del backlog/fallback y conciliación de los demás costes vigentes. Once de 18 puntos cerrados; B16 mantiene la candidata conjunta. No publicación, datos reales o proveedor contratado.

Decisión posterior: [acta19](actas/19-beta-b09-aceptacion-local-20261024.md) y [conciliación307](307-conciliacion-lectura-entrega-b09-20261024.md) aceptan B09 técnicamente en local; los pendientes indicados antes corresponden al corte propio de este documento.
