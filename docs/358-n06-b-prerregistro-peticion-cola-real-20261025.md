# N06B — referencia de petición y trabajo encolado reales

25 de octubre de 2026. N00/N01aceptados2/13; N06abierto. [N06A357](357-n06-a-resultado-atribucion-revisiones-20261025.md) atribuyó116/116/124SQL a11create_draft+2gestor+14resto y89/89/97tareas eager. Este lote obtiene una referencia no eager: no cambia código de aplicación ni convierte un cambio de modalidad en optimización. Se mantiene la exigencia del usuario de mostrar tiempos anteriores/posteriores y diferencias sólo válidas con equivalencia.

## Fuentes, selección y datos

`tests/test_listing_start_queued_baseline.py::test_listing_start_real_queue_baseline`, variantes approved/rejected_correction; dos casos y tres POST302esperados. Reutiliza la fixture published y los cuerpos originales de test_revised_listings de versión aprobada/rechazo. Mismos datos sintéticos, titular/moderador, foto y bytes compartidos; tarifa histórica privada en la variante de rechazo como oráculo de aislamiento. Sin datos reales ni proveedores.

La preparación original sigue eager y queda fuera de los relojes. Tras prepararla, sólo el escenario medido usa CELERY_TASK_ALWAYS_EAGER=False y un worker real; no se altera la fixture original ni se eliminan sus aserciones. El padre ejecuta Django Client como en los diagnósticos anteriores; no se mide TCP, proxy ni Gunicorn. Esperar a tareas después de parar el reloj de la petición permite ejecutar las mismas aserciones originales de comparación completa/instantánea, fotos privadas, rechazo, contenido público e historial intacto.

## Propiedad, roles y procesos

Runner oficial focused serial, --workers1, --isolate-test-broker y selección explícita del archivo. PostgreSQL17/Redis7.4 propios, librdbv2.4.0 y dependencias bloqueadas. El plugin existente valida contenedor/puerto/namespaceRedis; _owned_database valida el PostgreSQL real desechable, su usuario y base. No fallback a Redis normal ni lectura del .env de otros servicios.

Worker Celery real prefork2 con comando normal, namespace propio por caso, base de prueba y MEDIA_ROOT/RIGHTS_DELIVERY_ROOT privados de esa fixture. runtime_role_environment provee y verifica por TCP un rol restringido (no superusuario/createdb/createrole/bypassrls ni propietario de evidencia); contraseña sólo en archivo0600 temporal. Se retira al cerrar conexiones/procesos, sin terminar backends ajenos. El proceso padre conserva el rol migrador del arnés: no se afirma prueba universal de autorización SQL del servidor web.

No se arranca Beat en este lote: se estudian tareas encoladas por la acción y un refresh nativo explícito de preparación. No acredita cadencia periódica ni toda la topología desplegada. Antes de cada POST medido se drenan trabajos previos, se solicita refresh al worker y se verifica estado actual sin pendientes; esa preparación no entra en la petición ni en disponibilidad posterior. Las tareas medidas siguen el despacho real on_commit de la aplicación.

## Instrumentos y relojes

- Petición: Client.request con execute_wrapper y clasificador de stack sql_stage de N06A. Pared instrumentada y SQL por etapa en la conexión del padre. Sin tareas eager dentro de esa conexión; no inferir el número esperado por resta del total anterior.
- Publicación→inicio: señal before_task_publish del padre y evento task_prerun del worker con mismo task ID técnico y reloj monotónico del host. Incluye transporte desde la señal de publicación; no es tiempo puro esperando dentro de Redis.
- Ejecución: observador existente benchmark_celery_observer, wall de tarea y resultado real SUCCESS/eagerFalse en un PID prefork propio. El observador de refresh incluye consultas diagnósticas: no equivale a un worker sin instrumentar.
- Disponibilidad observada: después de terminar el reloj de petición, el arnés espera tareas correlacionadas y comprueba fotos de la nueva revisión completas/blob ready. Ese intervalo incluye sondeo y verificaciones: es cota observada de disponibilidad, no instante exacto de transición ni latencia de red. Puede haber tareas finalizadas antes del retorno de la petición.

Los únicos IDs persistidos por observación son IDs técnicos aleatorios de tareas para correlación y PIDs/start-ticks propios; no UUID de perfiles/fotos/blob, paths de petición, SQL, parámetros, contenidos, mensajes de excepción o credenciales. Los logs brutos del worker quedan locales; conservar eventos estructurados sin argumentos/cuerpos. Las ocurrencias anteriores no se convierten en porcentaje causal de mejora.

## Muestras y presupuesto de validez

Una pasada, tres inicios por los dos estados originales; sin p95/p99. Exigir dos casos PASS, tres muestras302, todos los oráculos originales, tareas originales publicadas y ejecutadas SUCCESS/eagerFalse, PID hijo propio, partición SQL sin pérdidas y números finitos no negativos. Deben aparecer process_blob y refresh_publication_state en cada inicio, sin falsificar resultados ni suprimir tareas. Conservar cuenta/bytes/autorización e instantánea; los jobs corren con rol restringido real.

El objetivo es fijar referencia y atribuir etapas, no optimizar. No hay candidato, techo de latencia inventado ni gate27SQLdeducido de N06A. Antes de un candidato se concretará presupuesto por estado/etapa según354. Tiempo de disponibilidad, trabajo de worker y petición son dimensiones distintas; no sumarlos como si fueran duración serial sin solapamiento.

Límites de ejecución: readiness del worker60s y observación de cada drenaje45s, timeout900s por comando; protecciones diagnósticas, no SLO de producto. Sin cuotas CPU/RAM dedicadas, carga concurrente o frío controlado. La concurrencia prefork2 y proceso/conexiones/calor se declaran y no se equiparan a capacidad de producción.

## Conservación y salida

Antes de medir: AST del instrumento y semántica de este protocolo, verificación de fuentes, congelación completa de producto/dependencias/migraciones/instrumentos/grafo/imágenes. El diagnóstico sólo se ejecuta explícitamente y en serie; fuera de esa selección declara SKIP diagnóstico, que no se cuenta como PASS funcional ni cobertura nueva. En la ejecución prevista no se permite SKIP.

Al terminar: comprobar2casos/3muestras, eventos de publicación/ejecución correlacionados, tiempos, contenido limitado de propiedades y métricas, fuentes intactas, PID/start-ticks ausentes, rol/archivo privado eliminados, claves Redis previas preservadas y sin nuevas claves fuera del namespace. El runner retira sus contenedores y temporales y confirma Telegram terminal. Ante fallo, conservar evidencia parcial y corregir causa sin declarar simuladores o pruebas no ejecutadas como verificación real.

Presentar tabla de tiempos: referencia eager de N06A frente a nueva referencia encolada, con modalidad/condiciones distintas claramente marcadas, sin porcentaje de optimización de código. Un futuro antes/después de candidato necesitará misma modalidad e instrumento. N06 seguirá abierto hasta cubrir cuenta/panel/edición/representación y sus disposiciones; tabla final de bloque con tiempos de aplicación y límites.
