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

## Persistencia inicial — en verificación

RightsPortabilityCoverage0091 vincula request/actor/action/selection_review/proof, huellas de fuente/selección/cobertura, épocas originales, versión propia y cuerpo cifrado/caducidad/purga. save_coverage reutiliza consumo auditado de selección aprobada con clave UUID hija, registra intención coverage_save y firma cuerpo/motivo/prueba/versión. Revalida autoridad/fuente al terminar y conserva versión/estado/plazo del expediente. Guardar no aporta aprobación independiente de cobertura ni autorización de cierre.

Inventarios perfil/cuenta incluyen el nuevo registro (censo cuenta59). Purga de cuerpos caducados en lote100, skip_locked, conserva metadatos; Beat60s configurado pero aún sin prueba de ejecución efectiva de esta tarea. Modelo/migración/servicio nuevos no incorporados todavía al runtimeDocker0090. PostgreSQL/HTTP de interfaz y revisión pendientes; batería de guardado `/tmp/portability-coverage-storage.xml/log` en curso, no resultado acreditado todavía.

Resultados parciales:22correctas59,14s (19puras+2PGperfil/cuenta+censo59) tras corregir serialización UUID de prueba en firma; evidencia `evidencias/portabilidad-cobertura-guardado-parcial.json`. Ampliación de integridad2PG48,64s comprueba motivo cifrado, actor atribuido y cuerpo manipulado, sin nuevas acciones/cierre, evidencia `evidencias/portabilidad-cobertura-evidencia-integridad.json`. Runs separados, no suma de pruebas únicas. Host check/makemigrations--check pasan. Interfaz, lectura/revisión de cobertura, carreras propias y ejecución efectiva nueva purga siguen pendientes.


Preparación incremental: `compile_coverage(..., allow_partial=True)` admite declaraciones ausentes y hojas omitidas todavía pendientes. No inventa exclusiones: cuenta `pending_fields`/`pending_images`, conserva las decisiones definitivas y rechaza referencias ajenas, solapamientos o motivos desconocidos. Usa schema `portability-coverage-pending-v1`; `complete` solo indica coherencia declarativa, nunca revisión independiente. El modo completo por defecto sigue rechazando toda omisión sin justificar. `save_coverage` incorpora el modo parcial al cuerpo cifrado y su firma, de modo que un replay no puede cambiarlo. Falta interfaz guiada, lectura/revisión independiente y consumo final con compilación estricta.

Preparación guiada escalar (servicio, todavía sin pantalla): páginas de hasta50 hojas omitidas por fila, con token firmado30min, actor/caso/sesión/MFA/selección aprobada/borrador y posiciones. Operación coverage_page firma fuente/prueba/digests/borrador cifrado/página/propósito antes del descifrado; auditoría previa de consumo de selección. Guardar preserva otras páginas y exclusiones binarias, transforma all en decisiones individuales y permite retirar una justificación devolviendo la hoja a pendiente. Reintentos usan baseline original; página obsoleta/ciphertext/firma alterados rechazan. Revalidación de fuente/prueba/autoridad al terminar. No revisión independiente, cierre ni aprobación de cobertura; todos los datos de prueba son sintéticos.

Pantalla privada inicial: rights_portability_coverage con selección aprobada propia, conjunto/registro/página y motivo de consulta; valores de campos omitidos solo tras POST auditado. Cada exclusión seleccionada requiere condiciones, motivo y evidencia definitivos; desmarcar deja pendiente. Formset50, protección CSRF, MFA/permisos/asignación y respuestas no-store. GET nunca restaura evidencias/valores. Sigue pendiente navegador móvil, omisiones binarias guiadas y revisión independiente.

Omisiones binarias: servicio prepare_images/save_images, páginas20 de metadata de imágenes no incluidas, decisiones explícitas porphoto. No autoriza ni lee bytes, no deduce exclusión por faltar archivo/decisión. Auditcoverage_images antes de descifrarbaseline, token30min y revalidación de autoridad/prueba/fuente al final. Guardado parcial preserva campos/otraspáginas; retirar decisión vuelvependiente. Primera prueba PostgreSQL sintética correcta; interfaz/revisión y pruebas multipágina/concurrencia pendientes.

Interfaz de imágenes omitidas: rights_portability_image_coverage, enlace desde cobertura, selección aprobada propia/página/motivo, formulario común de exclusiones definitivas porfoto. Muestra referencia y estado metadata solo tras POST, nunca bytes de imagen. Conserva declaraciones de campos y guarda borrador parcial. Tres pruebasHTTP PostgreSQL incluyen regresiones de campos; navegadorbinario/revisión independiente pendientes.

Lectura independiente escalar: inspect_page muestra hasta50 hojas de una fila, con valor/status/condiciones; incluye omitidas para poder revisar sujustificación. Requiere actor distinto, permisosMFA/lectura expediente-respuestas, aprobaciónselección/prueba/fuentevigentes; coverage_inspect liga página y ciphertext antesdescifrado. Valida originalfirmaautor/epochs y revalidaautoridad/fuente alfinal. Dos casos PostgreSQL perfil/cuenta correctos, auditoría antesdescifrado observada. No aprobación de cobertura, interfaz, consulta binaria ni cierre.

Lectura independiente binaria: inspect_page(binary=True,dataset=revisions,row_index=0) pagina20 metadatos porimagen y muestra decisión propia incluida/excluida/pendiente. Modo firmado y ligado a childaudit; cambiarlo con mismaclave rechaza. No bytes ni aprobación. Tres pruebasPostgreSQL incluyen regresiónlecturaescalarperfil/cuenta.

Constancia de lectura0092: RightsPortabilityCoverageRead conserva IDs de auditoría/cobertura/prueba, digestsfuente/cobertura/página,épocas,conjunto/registro/página/modobinario yfecha. No contiene valores ni notas. Lectura exactareplay valida registro, manipular huellapágina rechaza. Inventariosperfil/cuenta censan nueva dependencia60modeloscuenta; falta ensayo no vacío/sensibilidad, puerta de todaspáginas/aprobación y actualizaciónruntime.

Puerta lecturas completas: censo server-side de todaspáginas50hojas/20binarios, incluye conjuntos y binarios vacíos; lecturas ligadas a revisor/version/prueba/source/coverage/épocas. Exige conjuntoexacto y revalida cadaacciónoriginal contra contenidoactual, no sustituye lecturas alreintentar. IDs explícitos originales para futura aprobación/replay. PruebaPGcuenta: faltantes/IDsparciales/digestalterado rechazados, conjuntoexacto aceptado. No aprobación/cierre integrado todavía.

Decisión independiente0093: exige cobertura másreciente, lecturaexacta de todaspáginas y compilaestricto antesaprobar; pendientes solo permitenrechazo. Decisiónfirma proof/source/ciphertext/IDsoriginales/motivo/outcome/épocas, replay revalida IDsoriginales aunquenuevaslecturasexistan. Inventariosreview61modeloscuenta. TrespruebasPGcuentaparcial/completa+censo correctas; hechoslegales sintéticos, no revisiónreal ni UI/consumofinal/cierre.

RevisiónHTTP inicial rights_portability_coverage_review(case,coverage): GET sinrestaurarvalores/evidencias, autor403; POSTinspect páginasdadas/binary y POSTreview exige puerta vigente. DospruebasPGHTTPperfil/cuenta recorren todaspáginas/rechazocoberturaparcial/replay/CSRF; navegador/aprobaciónUI/enlacesdescubrimiento yvisualizaciónbooleanaspendientes.

Navegación: consulta expediente ofrece coberturas ajenas vigentes paginadas50 bajo permisos/MFA/ámbitoindependiente; sinvalores/evidenciasGET. Revisión muestra condicionesautomated/subject_related/third_party_reviewed sí/no/desconocido junto a base/origen/motivo/evidencia. DospruebasPGHTTPperfil/cuenta correctas paraenlacesycondiciones, navegador/aprobaciónUI pendientes.

Aprobación móvil:4 recorridosChromium/PostgreSQL ESENperfil/cuenta390px correctos, navega expediente→revisión, deniega aprobar sin lecturas y aprueba tras leer todaspáginas, GETsinhechos/nooverflow/plazointacto. Datoslegales sintéticos; sesiones autenticadasMFA(noTOTPnuevo). No cierre delderecho ni consumo deaprobación; runtime0091–93/regresiónconjunta pendientes.

Inventarios nuevos registros probados no vacíos: cuatrocasos PostgreSQLperfil/cuenta×parcial/completa verifican countsdelecturas yreview, ausenciaciphertext/evidencia, cambio state_digest alalterarpage_digest ocoverage_digest yrestauración. No borrar registros ni aceptar conservaciónrestauraciónintegral por estos inventarios.

Concurrencia lecturacuenta:8 escenariosPGcon2workers/holder/pg_blocking_pids observados correctos: replayúnico ydenegación tras revocarpermiso/prueba/sesión/MFA/fuente/ciphertext/caducidad,sinauditoríapersistida deoperaciónrechazada. No prueba deaprobación/perfil/binarios; no aceptar concurrenciaintegral.

Carrerasdecisionescuenta:8approved y8rejected enejecucionesPGseparadas,2workers/holder/pg_blocking_pids observados. Replay1decisión, cambio depermiso/prueba/sesión/MFA/fuente/ciphertext/expiry deniegasinaccionesnuevas yconservalecturasprevias. No perfil/binarios/conflictoclavesdistintas ni cierrederecho acreditados.

## Regresión conjunta de cobertura0093

Sesión88778 terminal0:294 pruebas correctas en2153,09s, sin fallos, errores ni omisiones. Las640 huellas de fuente coinciden al finalizar. Cuatro avisos de record_property/xunit2;13 propiedades conservadas en XML. Evidencia: `evidencias/portabilidad-cobertura-regresion-conjunta0093.json`. Las12 pruebas complementarias se acreditan por separado, sin incorporarlas al recuento294. Runtime0093 y purga worker/Beat constan en sus evidencias respectivas. Es una entrega parcial de CR09: consumo de cobertura aprobada, respuesta final, cierre y restantes requisitos siguen pendientes.
