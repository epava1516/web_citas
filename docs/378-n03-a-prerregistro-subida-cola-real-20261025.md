# N03A — referencia de subida, cola y procesamiento real

25 de octubre de 2026. N00/N01/N06aceptados3/13, N03iniciado, alfa. Corte previo revalidado1976fuentes sin cambios/SHA4a289c5161d370288b1ee81df713bd7b1fcab14529db087e76b01765a4d6e2b7, con AST/semántica focal vigente de377. Se reutiliza ese corte actual antes de analizar el hito; no se afirma reconstrucción ni extracción semántica nueva donde no cambió fuente. Consulta graphifyS07/process/fingerprintseguida de lectura directa; respuesta truncada no prueba exhaustividad.

## Detector: evidencia reutilizable y decisión previa

El original20261024-213414-574e4266de327conserva2PASS/582,988sJUnit y llamadas al detector3,199770spara1000Blobdistintos/cinco positivos y14,392127spara100densos/100positivos. Revisión independiente y verificación primaria:15fuentes relevantes idénticas, incluidosservices.py,similarity.py,instrumento,fixtures,settings,dependencias ypublication_signals.py. Las propiedades de medición delJUnitcoinciden exactamente con la auditoría original. No repetir582spara afirmar sólo frescura; no confundir construcción del corpus con llamada del detector.

Esa evidencia sólo acredita el detector finito instrumentado con firmas preparadas/calientes. No acredita subida, cola,80000fotos, retención ilimitada o índice. Denso:CPUconfirmación6,368067s,registro protegido3,709945s,comparación de firmas0,067510s; no se adoptará un índice ni un límite de candidatos por defecto. Son hipótesis futuras separadas, no candidatas implementadas: unir dos comprobaciones de exclusión sólo conservando locks/frescura/paridad, o reutilizar características del origen dentro de una sola llamada del detector conservando resultados/fallbacks. Antes de corregir se congelará referencia/coste/criterio conforme354; no se agrupan ambas en un candidato.

## Hueco elegido: S07-B, entrada al backend → cola → estado utilizable

Nuevo instrumento tests/test_photo_upload_queued_reference.py. Un caso, invocación del oráculo original completo test_photos::test_valid_photo_private_derivative_retries_exif_and_remove sin copiar sus aserciones ni recortar datos. DosPOST302de subida:JPEGsintético original conEXIFy reintento con bytes idénticos. Deben conservarse1Blob/1Photo,2UploadAttempt,ready/noaprobada,WebPsinEXIF,guardias privadas/anónimo/retirada y archivo original no expuesto. El nuevo instrumento añadecomparison_completetras espera real. No se reemplaza eagerporresta:las fixtures originales se preparan antes, y la operación medida se despacha a broker/worker reales locales.

Entorno propio:PG17/Redis7.4del runner, namespace de broker por caso, workerCeleryprefork2con rolSQLrestringido y conexión independiente verificadas porcapacity_runtime_role. Almacenamiento local privado compartido entre padre/worker, sin objetos/proveedor real,Beat/TCP/Gunicorn/carga. Se comprueban puertos/etiquetas/run/generación antes de arrancar. La preparación crea el estado original; luegoeagerFalseen padre/worker. Se preservan claves de otras generaciones, sin borrarlas ni escapar delnamespace. Elworkerusa comandos nativos sin parchear servicios ni simular finalización.

## Relojes y oráculos de la instrumentación

Medir sólo Client.request de losPOSTde subida, CPUde hilo y consultas/tiempoSQLde esa conexión. Multipart/cliente/red/navegador/setup/aserciones quedan fuera;decode/ingest/middleware dentro. Antes de cadaPOSTdrenar tareas y refresco real de publicación fuera del reloj para partir de cola quiescente declarada; no mide backlog natural ni mezcla productiva.

Correlacionar publicación→inicio y ejecución worker conIDs técnicos yPID/start-ticks propios. El primerPOSTdebe publicar exactamente1process_blob; el duplicado exactamente0. Sólo tiposprocess_blob/refresh_publication_state, ejecucionesSUCCESSno eager y sin error del observador. La duración del worker incluye el trabajo real completo deprocess/detector de esta imagen, no un perfil interno de cada función. El refresco puede solaparse: no sumar reloj de petición, espera y tareas como etapas seriales.

Registrar entrada al backend, final de petición y ready+comparison_completeobservado después de drenar tareas. La cota observada incluye sondeo/aserciones del arnés; no es el instante exacto de disponibilidad. CPUdel padre no incluye CPUdelworker; cada una conserva su unidad/ámbito. Dos operaciones diferentes, una muestra por transición: sin p95/p99ni porcentaje causal de optimización. No hay candidato de aplicación en este paso.

Presupuesto de validez:1PASS/0FAIL/ERROR/SKIP,2muestras,tipos/conteos/estados/correlación correctos,métricas finitas/no negativas,todos los oráculos originales intactos. Esperas45s,arranque60s ytimeout900s son protecciones, noSLO. No registrar SQL/params/cuerpos/contactos/credenciales/UUIDde sujetos; IDs técnicos de tareas yPIDs sólo para auditoría de proceso. Logs privados permanecen ignorados.

## Ejecución y salida

Integrar ASTdel instrumento y semántica de este protocolo antes de congelar fuentes/dependencias/migraciones/grafo/imágenes. Runneroficial serial: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --isolate-test-broker --timeout 900 --test tests/test_photo_upload_queued_reference.py`. Una pasada, sin reducción/repetición adaptativa. No pruebas de horas previstas; si cambiara esa previsión, aplicar persistencia/Telegram/pausa/compactación y mismo goal conformeAGENTS.

AuditarJUnit/propiedades/archivos de eventos,fuentesintactas,identidadesworker/rolsinprivilegios/credencialesretiradas,clavesajenaspreservadas,0clavesnuevasfuera delnamespace,PIDsausentes/código0,PG/Redis/temp retirados por inventario independiente yTelegramterminal confirmado. Conservar todoFAILsiaparece. Tabla de tiempos por etapa y límites,QAseparado. No repetir el detector válido por documentación.

N03sigue abierto: originales distintos/densidad/retención/concurrencia y recuperación/reintentos de errores deben conciliarse con sus pruebas y mediciones; duplicado idempotente no prueba autoretry deOSError. No cerrarN03por este caso. Coordinar procesado/publicación conN07sin duplicar trabajo. MOD09restante diferido por usuario367, sin proveedores/apertura ni campaña general de optimizaciónQA.
