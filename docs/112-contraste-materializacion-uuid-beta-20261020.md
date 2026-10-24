# Contraste finito: materialización y texto UUID reutilizado

Fecha:2026-10-20. Estado: ejecutado y rechazado, propuesta de producto no aplicada. B07/B08 abiertos; corto TCP previo FAIL, sin autorización técnica para900s. Continúa [111](111-contraste-materializacion-derechos-beta-20261020.md); aquel resultado queda rechazado e inmutable. Este documento no cambia sus umbrales.

## Hipótesis distinta y cambio exacto

El perfil115651 registra6096 llamadas globales UUID.__str__ por ruta,6–12ms propios observados. El helper comercial convierte tres veces cada UUID promocionado: digest diario, desempate y clave de posiciones; la rama autobump también convierte. Esa observación es instrumentada, no una mejora demostrada. La combinación anterior sólo materializaba; ahora se contrasta la eliminación de conversiones repetidas junto al consumo completo de derechos. No repetir el mismo candidato hasta cruzar el umbral ni atribuir de antemano el beneficio a UUID.

Nuevo instrumento tests/test_beta_rights_materialization_uuid_roi.py, copia separada del anterior. Exige SHA79665c4cd351f668f4f8378ead3ce514b6fdd6491f737e1b6c8294b31913009e del módulo de producto. Compila una copia aislada de _snapshot_order_population con exactamente estos cambios: iterator(chunk_size=500) por QuerySet normal; bucle por raw_pk con pk=str(raw_pk) una vez por derecho; cuatro expresiones posteriores str(pk) por pk. UUID canónicos en texto se usan coherentemente como claves internas y en digest/desempate. El mapa ya se serializaba con esas claves. Consulta, autoridad, población, fecha UTC, prioridades, empates y guarda de página permanecen iguales; sin cache entre peticiones ni límite previo.

READCOMMITTED heredado sigue en su camino SQL original; no se tocan elegibilidad, locks, renovación, autosubida ni configuración cursor_tuple_fraction. La propuesta sigue dentro del instrumento: no cambia apps/catalog/promotion_paging.py. Eventual adopción exige además los casos de paridad existentes con autobump/solapamientos/revocación y la regresión común afectada.

## Protocolo congelado antes de ejecutar

Mismo diseño que111:10000perfiles/2000derechos sintéticos20%Top/Premium, PostgreSQL/Redis propios, un worker pytest, misma CPU/cuotas sin ampliación, host compartido. Rebuild explícito y estado limpio, READ_REPAIR real desactivado. Sin otra batería concurrente. No proveedores/pagos/datos reales. El catálogo y geografía compartidos de esta fixture no acreditan distribución nacional.

Dos rutas, listadoES y búsquedaEN q=synthetic; seis permutaciones de A/B/C por ruta. A/B nativos idénticos mediante el mismo dispatcher; C copia nueva. Cada brazo conexión física nueva, una lectura caliente fuera del reloj y tres controles. Total36calentamientos+108controles+4observaciones=148HTTPClient. Exigir HTTP200/no-store, bytesSHA/IDs/recuento/patrocinio idénticos y24filas patrocinadas, estado limpio. Esto no acredita latencia TCP ni capacidad.

Medir wall y CPUthread de aplicación por lectura; CPU real del backend PostgreSQL identificado y verificado por propiedad/cgroup/start_ticks con schedstat fuera de los controles. GC normal sin collect artificial, cambio de umbrales o desactivación. Ningún profiler, SQL wrapper ni contador UUID dentro de los108controles.

Criterios por ruta, TODOS obligatorios: A/A con diferencia absoluta máxima10% en wall/CPUapp/CPUbackend; mediana C al menos10% menor que promedio de medianas A/B; CPUapp y CPUbackend C como máximo105% de la referencia; al menos4de6bloques sin regresión wall. Ambas rutas deben cumplir. Un PASS pytest sólo demuestra integridad del experimento; eligible=false rechaza adopción. No rebajar umbral, elegir sólo la ruta favorable ni repetir un resultado negativo sin mecanismo distinto.

Después de controles, cuatro lecturas observadas A/C por ruta: execute/FETCH comercial, tracemalloc y contador UUID.__str__ sólo dentro del helper. Exigir conversiones positivas y C como máximo la mitad de A; restaurar todos los hooks. Memoria Python observada no es RSS ni presupuesto del servicio. Comparar planes SELECT/DECLARE sin ejecución después de las lecturas; no inferir tiempo/CPU de esos planes ni cambiar planificador. Registrar datos en beta-rights-materialization-uuid-roi.json y auditoría independiente, incluyendo resultados negativos, hashes, fuentes congeladas, limpieza y Telegram terminal.

## Reutilización acotada de evidencia

La corrección de interfaz posterior a111 cambió sólo templates/base.html y retiró templates/core/home.html:621 fuentes de producto iguales al común162/622 actuales. La QA específica de cuentas/SEO/navegación tiene su propio corte y el experimento nuevo compara A/B/C sobre la misma interfaz actual. No afirmar que el común162 anterior ya probó el delta. El producto promocional conserva su SHA original durante la comparación. Cualquier aceptación posterior debe identificar el nuevo conjunto completo de fuentes y repetir lo afectado.

## Resultado auditado y decisión

130958-cc984087:1PASS/0FAIL/0ERROR/0SKIP de integridad,148lecturas/paridad exacta, fuentes congeladas/limpieza/Telegram1792502752921317372-29244 confirmados antes de nuevas ediciones. [Auditoría](evidencias/b08-rights-materialization-uuid-roi-audit-20261020.json). candidate_eligible=false: RECHAZADO, sin modificación del producto promocional.

Listado: A318,229ms/B322,597ms/C321,834ms; ratioC/AB1,0044, sin10%de mejora. A/A estable y6de6bloques no regresivos no sustituyen ese umbral. CPUapp ratio0,9255 y CPUbackend0,8972. Búsqueda: A348,279ms/B295,107ms/C345,459ms; ratio1,0739, A/A inestable y2de6bloques no regresivos. No atribuir la variación a una causa externa no medida ni inferir un beneficio estable.

Observación separada confirma6000conversionesUUID originales y2000delcandidato en cada ruta. Pico Python observado listado886303/883190bytes y búsqueda777198/887159bytes A/C; no es presupuesto RSS ni comparación controlada con el experimento111, cuyo observador era distinto. Reducir llamadas no demuestra mejorar latencia completa.

No repetir esta variante para cruzar el umbral, reinterpretar la mediana o elegir únicamente los bloques favorables. El original sigue SHA79665c...; corto TCP FAIL y900s bloqueado. Tras la auditoría, los instrumentos se trasladan según [113](113-instrumentos-diagnosticos-beta-20261020.md), conservando sus fuentes originales y funciones. Próximo diagnóstico distinto [114](114-diagnostico-estados-pendientes-beta-20261020.md) cubre49estados pendientes públicos; no adopta una optimización.
