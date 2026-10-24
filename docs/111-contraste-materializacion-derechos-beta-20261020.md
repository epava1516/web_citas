# Contraste finito: consumo completo de derechos promocionales

Fecha:2026-10-20. Estado: experimento terminado; materialización sola rechazada, propuesta no aplicada. Continúa [110](110-contraste-tcp-beta-b07b08-20261020.md). B07/B08 abiertos; no aceptación beta ni autorización para900s desde el cortoFAIL.

El perfil115651 auditado localiza80–127ms inclusivos en la selección comercial con2000derechos. Execute no incluye FETCH del cursor: esos valores y los planesSELECT no prueban por sí solos que streaming sea peor. [Django5.2](https://docs.djangoproject.com/en/5.2/ref/databases/#server-side-cursors) documenta el cursor de iterator y su posible planificación para consumo parcial; [PostgreSQL17](https://www.postgresql.org/docs/17/runtime-config-query.html#GUC-CURSOR-TUPLE-FRACTION) describe cursor_tuple_fraction. La hipótesis concreta es que consumir siempre todos los derechos estrechos puede favorecer una consulta ordinaria. Comprobarla sin tocar configuración ni autoridad.

## Cambio experimental exacto

El instrumento tests/test_beta_rights_materialization_roi.py exige SHA79665c4cd351f668f4f8378ead3ce514b6fdd6491f737e1b6c8294b31913009e del módulo actual. Compila una copia local de _snapshot_order_population sustituyendo únicamente `rights.iterator(chunk_size=500)` por `rights`; la consulta values_list y todo el cálculo permanecen iguales. A/B llaman al original idéntico y C a esa copia mediante el mismo dispatcher. Ninguna modificación de producto, global del driver o configuración del planificador. Sin cache de resultados entre peticiones ni truncamiento de candidatos/derechos.

El consumo normal materializa temporalmente las tuplas estrechas y puede aumentar memoria; no hidrata perfiles completos ni cambia el orden o la guarda. Medir ese coste en observación separada y revisarlo antes de adoptar. El camino heredado READCOMMITTED, elegibilidad, locks y autosubida no se cambian por este experimento.

## Datos, recorrido y recursos

PostgreSQL/Redis propios del runner oficial, un worker pytest, misma fixtureTCP:10000perfiles y2000derechos sintéticos emitidos mediante servicios,20%Top/Premium y sin autobump. Agencia/foto/geografía compartidas, no distribución nacional ni proveedores/pagos/datos reales. Rebuild explícito y estado limpio; READ_REPAIRdesactivado. Sin otra batería concurrente ni más recursos; host compartido con actividad normal.

Dos recorridos: listadoES y búsquedaEN q=synthetic. Seis permutacionesABC/ACB/BAC/BCA/CAB/CBA por ruta. Cada brazo abre backend nuevo, hace una lectura de calentamiento fuera de control y tres lecturas medidas. Total36calentamientos+108controles=144HTTPClient. Exigir en todos bytesSHA, IDs ordenados, recuento, etiquetas, HTTP200 y no-store idénticos; cada página24filas y patrocinio. Marcadores limpios antes/después; no cambios en publicación durante los controles.

Medir wall y CPUthread de aplicación por lectura. Identificar el backend PostgreSQL mediante SQLPID y propiedad Docker/cgroup/start_ticks; leer su CPUreal con schedstat antes/después del bloque de tres peticiones, fuera de los controles. Restaurar/verificar identidad y cursor_tuple_fraction. GCnormal, sin collect artificial, desactivación o cambio de umbrales. Sin profiler ni wrapperSQL dentro de los108controles. Preparación/conexión/calentamiento/lecturas de recursos fuera del reloj.

## Criterios prefijados

Por cada ruta: estabilidadA/A dentro10% en mediana wall/CPUapp y CPUbackend por lectura; C debe reducir wall al menos10% frente mediaA/B, no aumentar CPUapp ni CPUbackend más5%, y no regresar en al menos4de6bloques. Exigir todos los criterios en ambas rutas. Un pytestPASS con eligible=false conserva un experimento íntegro y rechaza adopción; no reinterpretarlo como mejora ni encadenar repeticiones hasta obtener un positivo.

Un eligible=true sólo permite revisar la candidata: no acepta capacidad ni incorpora producto. Conciliar memoria y paridad, comprobar los alcances funcionales afectados sobre una versión congelada y después volver al cortoTCP con todos sus presupuestos originales. El contractual900s sigue dependiendo de un PASS completo auditado del corto.

## Observaciones separadas posteriores

Después de todos los controles: cuatroHTTPClientobservados (A/C por ruta), total148peticiones. Sólo allí instrumentar execute comercial y fetchmany de cursor mientras la función comercial está activa; no atribuir FETCH de widgets a derechos. Tracemalloc registra pico/incremento de heapPython de la función y se restaura; tiempos incluyen instrumentación, no comparar con controles ni sumar inclusivos. No son RSS de servicios, memoriaPG ni perfil de todo el host.

Capturar únicamente en memoria el SELECT de derechos. Después comparar sus planes de planificación SELECT y DECLARE NO SCROLL WITHOUT HOLD, con EXPLAIN FORMATJSON, en nueva instantánea REPEATABLE READ READ ONLY. [EXPLAIN17](https://www.postgresql.org/docs/17/sql-explain.html) admite DECLARE; no usarANALYZE ni presentar tiempos de ejecución desde estos planes. Redactar literales/UUID mediante el mecanismo anterior; ningún SQL/parametro/cuerpo de mensaje guardado. No cambiar cursor_tuple_fraction ni otras políticas para forzar resultado.

Conservar resultado, fuentes congeladas, JUnit, muestras por brazo, identidades/CPU, observaciones separadas y planes redactados. Auditar terminal, integridad, frescura y limpieza antes de editar fuentes; Telegram terminal y recibo obligatorios. No restaurar el grafo desde semántica antigua ni declarar cobertura exhaustiva por refrescar este incremento.

## Resultado auditado y decisión

Ejecución20261020-122947-9cc70ea7:1PASS/0FAIL/0ERROR/0SKIP de integridad experimental, no de mejora. [Auditoría](evidencias/b08-rights-materialization-roi-audit-20261020.json):148 lecturas, igualdad de bytes/IDs/recuento/patrocinio y A/A estable en ambas rutas. Fuentes congeladas, limpieza e identidad de procesos y Telegram terminal1792500351350943425-3975814 confirmados antes de las siguientes ediciones.

Listado: C270,500ms frente al agregado A/B, mejora22,8%; búsqueda: C316,182ms, mejora8,5%. El criterio prerregistrado exige al menos10% en ambas rutas. candidate_eligible=false: se rechaza la materialización sola como cambio global. CPU de aplicación y backend no regresa; esto no permite ignorar el umbral de búsqueda. No se modifica producto ni se repite el mismo contraste para cruzar el umbral.

Observación separada: cursor original cinco fetch de derechos por ruta, candidato cero; la materialización aumenta el pico Python observado en141051/248362bytes. Una observación por ruta no demuestra presupuesto RSS del servicio. Los planes sin ejecución SELECT/DECLARE difieren, pero no atribuyen tiempo ni CPU. Ninguna configuración del planificador cambiada.

Siguiente hipótesis distinta, aún no aplicada: reutilizar el texto del UUID dentro del cálculo comercial, donde el perfil10k registra6096 conversiones globales por ruta. Requiere protocolo propio, mismo umbral y paridad; no convierte este rechazo en aceptación. B07/B08 abiertos; el corto TCP previo sigue FAIL y900s bloqueado.

La hipótesis distinta queda prerregistrada en [112](112-contraste-materializacion-uuid-beta-20261020.md); este rechazo y los umbrales originales permanecen vigentes.
