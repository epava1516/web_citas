# N15 — prerregistro de recibos terminales fuera de artifacts

El contrato340 exige que la purga completa sea la última operación yque el aviso no vuelva a crearartifacts. La fuente actual del notificador siempre guardaba allí sus recibos. Se prepara un parámetro keyword-only interno **receipt_dir**, opcional:sinvalor conserva exactamente el destino predeterminado; convalor escribe sólo enese directorio, sin fallback. No modifica transporteOpenClaw/configuración,veredictos,redacción de errores oreglas de notificación única porrunner.

Destino final lo fijará el controlador de cierre a una ruta propia de docs/actas; no proviene de datosHTTP. Revisar ruta resuelta ypropiedad antes de la limpieza. El parámetro sólo selecciona dónde guardar metadatos: no añade cuenta/proveedor, logs, credenciales ocontenido privado. Unfallo de transporte mantiene el veredicto de la prueba; unfallo de escritura se declara receipt_error yel cierre no lo aceptará como recibo confirmado. Ningúnfallo del destino explícito debe recrear el predeterminado.

## Fuente, revisión y seis casos

Basefa7dee3. Únicosdosarchivos de código afectados: scripts/test_notifications.py ytests/test_test_notifications.py. Se preservan los tres casos originales:transporte sincredenciales,fallo que no reescribe elveredicto yredacción,ausencia de duplicadosworker/runner. Se añaden dos variantes de destino explícito (proveedor correcto/fallido) yuncaso de directorio bloqueado porarchivo. Los tres nuevos escenarios usan raíz yconfiguración sintéticas,transporte sustituido,yexigen que no exista artifacts ni fallback; configuración yarchivo bloqueado deben conservarse.

Revisión focal Python/seguridad:parámetro sólo para callers internos fiables,argvsininterpolación,configuración de canal no expuesta,receipt sinstderr,comportamiento predeterminado conservado. Noendpoint,modelo,migración,settings deaplicación,workflow oservicio cambiado. No repetición deC30/D44 ni nueva campañaQA.

Grafo previoN11preservado una sola vez en graphify-out/history/pre-n15-20261027, SHA33ab425166999f2088acc47a20e34bfe9c0d10ea998ed91f70d7240c6cd78238. Antes de freeze: AST fresco de dosfuentes ysemántica literal500/seguimiento,verificación/Ruff; éste es unrefresco focal,no reconstruccióncompletaN15. Los13registros/documentos nuevos de la integración lateral entrarán en el corpus del rebuildfinal, no se pretende que este delta los haya analizado todos.

Runneroficialfocusedserial1,PG17/Redis7.4propios yparsernativo,selector sólo tests/test_test_notifications.py,**6casos esperados**,timeout600s. Son unitarios contransporte simulado, no pruebafuncional dePostgreSQL/Redis oproveedor porlosseiscasos. Elaviso terminal real del runner,después decleanup,confirma porseparado la configuración existente. Congelar fuentes/test/docs/grafo eIDs imágenes pre/runtime,sin editar durante elensayo.

Esperado6PASS0FAIL/ERROR/SKIP,fuentesestables,recibounitario correcto/sinsecretos yningúnartifactscreado por destino explícito,limpieza yTelegramterminalsent. Conservar cualquierfallo yresolver antes de usar la API para el cierre. Después registrar elresultado,commit/push propio separado de losregistros laterales yproceder al grafo completo/diferencial/relevo deN15.

N15permaneceactivo11/13; todavía no seborra artifacts. N02/MOD09end,N12/B14,N13/B15,N14/B17condicionados yQAglobal hasta estable conforme deuda-pendiente-viva. Alpha/noindex. La constancia terminal del resumen final acreditará la purga; el grafo describirá la obligación sin fingir ejecución previa.
