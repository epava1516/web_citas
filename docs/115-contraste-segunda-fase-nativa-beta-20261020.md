# Contraste de segunda fase nativa para estados pendientes

Fecha:2026-10-20. Estado: contraste elegible integrado, regresiones focal14 y común172 más escala100/1000/10000 auditadas; regresión funcional amplia preparada. El prerregistro y sus negativos se conservan. Continúa [114](114-diagnostico-estados-pendientes-beta-20261020.md); B07/B08 abiertos, corto TCP FAIL y900s bloqueado. Los rechazos111/112 se conservan sin repetir esos candidatos.

## Coste e hipótesis

114-134917 mide181–236ms frescos frente1990–2037ms con49anuncios pendientes todavía públicos, sobre1000perfiles. El fallback hidrata1000+200filas y ejecuta1200guardas en la observación; la selección mantenida hidrata24. La hipótesis es conservar la selección mantenida para anuncios sin cambios y validar todo el conjunto pendiente cuando un censo actual y una instantánea propia permiten demostrar su completitud. No se presume una mejora hasta contrastarla ni se atribuye toda la latencia a una sola función.

## Cambio exacto y ámbito

La fábrica tests/beta_extended_unknown_candidate.py exige SHA35d6b1e9b8d7a9a04e1218263416cc6025173da55aee9d638dd67507a6e50010 de apps/listings/publication_state.py. Compila una copia aislada de _state_page con dos sustituciones literales verificadas: una segunda fase tras superar el primer lote48 y una razón de observación distinta al terminar esa fase. No instala esa copia en apps/.

48 sigue siendo el umbral inicial y1000 la guarda de suciedad. Cambia la transición de trabajo: con REPEATABLE READ/READ ONLY propio, censo completo/versionado y la pista canónica _publication_state_population de discovery.candidates, leer todos los IDs pendientes compatibles hasta1001. Si caben en1000, ejecutar las guardas nativas existentes sobre todo ese conjunto y continuar selección/recuento/orden y guarda de la página. Si no caben o falta cualquiera de esas condiciones, conservar el fallback completo. La ampliación del lote nativo es una conducta nueva explícita; no se oculta bajo el nombre del límite48.

No se truncan resultados: el exceso1001 activa la población nativa completa. No subir48/1000, reparar en GET, cachear autoridad entre peticiones, cambiar cuotas ni omitir comprobaciones. Una transacción heredada READ COMMITTED, censo incompleto o queryset clonado sin pista canónica conservan el recorrido anterior. Estado, revisiones, fotografías y derechos se leen en la instantánea propia; toda fila pendiente y toda fila de la página seleccionada conservan validación nativa. Pedidos, elegibilidad, rotación, límites comerciales, locks y autosubida permanecen intactos.

La observación de éxito es route=state, reason=trusted_state_extended_unknown, native_unknown=N. El original conserva fallback/state_unknown_over_limit con49. Esta diferencia se verifica explícitamente; la paridad exigida corresponde a bytes públicos, IDs, orden, recuento y patrocinio, no a fingir la misma ruta interna. La fuente baseline114 se conserva para su versión; después de una adopción debe reproducirse con esa versión original, sin reescribir sus negativos.

## Calibración funcional previa

Primero ejecutar sólo test_extended_unknown_small_safety del instrumento explícito tests/beta_extended_unknown_roi_diagnostic.py:100perfiles/20derechos sintéticos,49marcas y todas las páginas de listadoES/búsquedaEN, original frente candidato. Exigir100IDs únicos por ruta, igualdad de bytes/recuento/patrocinio y razones internas correctas.

Con PostgreSQL real, verificar además que el candidato rechaza ampliación en READ COMMITTED heredado, queryset clonado sin pista y censo incompleto, manteniendo la respuesta nativa completa. Restaurar preparación antes del caso concurrente. Revocar un actor mediante otra conexión después de establecer el censo RR: la primera respuesta conserva su instantánea de lectura; la siguiente excluye sus anuncios/patrocinio y coincide en todas las páginas con una referencia nativa completa posterior. Son fixtures sintéticas y actor real de la BD de prueba, sin proveedor ni datos personales reales.

Un fallo bloquea ROI hasta corregir y auditar. Esta calibración sólo prueba las condiciones y escenarios declarados; no equivale a regresión común, escala10000 o capacidad.

## ROI finito posterior

Sólo tras PASS auditado anterior, mismo entorno del runner, un worker pytest,1000perfiles/200derechos20%Top/Premium mediante servicios y49marcas públicas compatibles con synthetic; sin worker de refresco ni READ_REPAIR, GC normal. Sin otra batería ni más recursos, host compartido. Agencia/foto/geografía compartidas no acreditan distribución nacional; no proveedores/pagos/datos reales.

Por cada ruta listadoES/búsquedaEN comparar primero todas las42páginas A/C:168HTTPClient, bytes/IDs/recuento/patrocinio iguales,1000IDs únicos por ruta. Después seis permutaciones ABC por ruta, A/B original idéntico y C copia mediante el mismo dispatcher interno. Backend físico nuevo y lectura caliente fuera del reloj en cada brazo, luego tres controles.36calentamientos+108controles; CPUthread de aplicación y CPU real del backend PG identificado por SQLPID/propiedad Docker/cgroup/start_ticks, schedstat fuera de los relojes. Ningún profiler, wrapperSQL, constructor sustituido ni cambio de GC en controles. Contrastar el mismo día UTC y49marcas persistentes.

Criterios por ambas rutas: diferencia A/A absoluta≤10% en wall/CPUapp/CPUbackend; mediana C≤90% del promedio de medianas A/B; CPUapp/CPUbackend C≤105% de su referencia; al menos4de6bloques sin regresión. Todos obligatorios. PASS pytest acredita integridad experimental; eligible=false rechaza adopción. No cambiar umbrales o agregación, seleccionar bloques favorables ni repetir un candidato negativo sin mecanismo distinto.

Cuatro observaciones A/C por ruta, separadas de controles: execute sin incluir las sondas de modo; cantidad de filas y tiempo inclusivo de contextos; modo PG tras el constructor; tracemalloc del recorrido completo. Esperar contextos1000+200 en A y como máximo97filas hidratadas en C, con RR/read-only efectivo en C. Sondas y tracing afectan esas observaciones; execute excluye FETCH, tiempos inclusivos se superponen y pico Python no es RSS. No inferir CPU PG de execute. Total316lecturas:168paginación+36warm+108control+4observación.

Guardar beta-extended-unknown-roi.json, JUnit, fuentes congeladas, auditoría independiente, limpieza y Telegram terminal. No se toca producto durante esta comparación. Eventual adopción necesita revisar memoria y riesgos, aplicar cambio mínimo, probar regresión afectada/paridad/concurrencia sobre la fuente integrada y contrastar10000. No habilita900s ni arregla por sí sola el corto limpio20RPS; ese frente sigue pendiente.

## Primera calibración negativa

142712-3aaf459a:0PASS/1FAIL/0ERROR/0SKIP. Tras comprobar el rechazo por censo incompleto, la preparación llamaba refresh_all sin marcar el estado eliminado; ese comando consume pendientes y no lo reconstruyó. El gancho concurrente no llegó a ejecutarse porque el censo seguía incompleto. Auditoría b08-extended-unknown-small-negative-20261020.json confirma fuentes congeladas, limpieza y Telegram entregado. Corregir sólo preparación: mark_stale, refresh_all y aserción de censo completo antes de restaurar49marcas. No alterar candidato, expectativas, producto ni protocolo ROI. Repetición pequeña pendiente; ROI bloqueado hasta PASS auditado.

## Segundo negativo y precisión del caso concurrente

142935-ae8217ae:0PASS/1FAIL/0ERROR/0SKIP. El gancho concurrente se ejecutó y la instantánea conservó la primera respuesta, pero la prueba suponía incorrectamente que desactivar al comprador revocaba el consentimiento de todos los perfiles de su agencia. La referencia nativa confirma la distinción: desactivación retira patrocinio; consentimiento personal gobierna publicación. Auditoría b08-extended-unknown-small-negative-2-20261020.json confirma fuentes, limpieza y recibo terminal. Antes de repetir se precisa el caso: en la conexión concurrente desactivar comprador y revocar consentimiento de una persona concreta; siguiente respuesta debe retirar ese perfil y todos los patrocinios del comprador, coincidiendo con referencia nativa completa. No cambiar reglas/producto/candidato/criterios ROI. Dos negativos conservados; ROI todavía bloqueado.

## Calibración115 auditada

143211-5ce55a8f:1PASS/0FAIL/0ERROR/0SKIP,65,40s, auditoría b08-extended-unknown-small-audit-20261020.json. Todas las páginas ES/EN idénticas al original,100IDs únicos por ruta; rechazo en READ COMMITTED heredado, clon sin pista y censo incompleto. Revocación concurrente del consentimiento de una persona y del comprador: primera lectura conserva su instantánea RR/read-only, siguiente coincide con referencia nativa completa y retira perfil/patrocinios según reglas distintas. Dos negativos anteriores de preparación/suposición conservados. Fuentes congeladas comparadas de nuevo, recursos retirados y Telegram1792506827832097517-515226 entregado. Candidato/producto sin modificar. Queda autorizado por protocolo el contraste finito1000/316lecturas, todavía no ejecutado; no10k/TCP/aceptación beta.

## Contraste elegible e integración mínima

143620-80f3e805:1PASS/0FAIL/0ERROR/0SKIP,569,29s;316HTTP y todas las42páginas por ruta A/C idénticas. Auditoría independiente b08-extended-unknown-roi-audit-20261020.json verifica fuentes, limpieza y Telegram1792507582129928011-544290. A/A estable en wall/CPUapp/CPUbackend,6de6bloques sin regresión por ruta; todos los criterios prerregistrados se cumplen.

ListadoES: medianaA2096,280ms/B2157,795ms/C433,555ms;C/AB0,20383,−79,6%. CPUappC/AB0,15355 y CPUbackend0,50847. BúsquedaEN:A2064,359/B2059,035/C409,879ms;C/AB0,19881,−80,1%;CPUapp0,15094 y CPUbackend0,52501. Son controles HTTPClient balanceados, no TCP ni SLO.

Observaciones separadas: contextosA1000+200 frenteC73+24, modosC RR/read-only; pico Python listado19852274→1976206bytes y búsqueda20617640→1975436bytes. No RSS ni tiempos limpios bajo tracing. execute47→55 excluyendo sondas/FETCH: mejora por menos trabajo total, no por menos sentencias. No sumar tiempos inclusivos ni atribuir toda latencia a una operación.

Se aplica exactamente la función candidata, sin otro cambio de producto: fuente integrada publication_state.py SHA282f88e5af3c3f49f618aaf9bf3c5949e0d038f7699bfe6ca79ac880998703c6;621de622fuentes de producto permanecen idénticas. Prueba estática b08-extended-unknown-integration-delta-20261020.json; fuente anterior byteexacta b08-publication-state-original-20261020.py.txt. El instrumento histórico115 mantiene su guarda del original: para repetir A/A/C exige esa fuente anterior, no reescribir su baseline como si fuese producto actual.

Nueva regresión test_publication_pending_batch.py usa producto integrado contra referencia nativa completa: todas las páginasESEN, guardasRC/clon/censo, techo reducido sólo dentro del test para comprobar que no trunca, concurrencia real de consentimiento personal y comprador. No depende de la fábrica experimental. Regresión focalizada prevista14casos: nuevo1, paridad comercial4, límites de snapshot4, membresía4 y migración de invalidación1. Pendiente ejecución, no se acreditan resultados todavía.

La edición invalida rules_version: hasta recomputar estados de esa versión sigue siendo obligatorio el fallback nativo completo. Sin despliegue ni reparación en GET. La elegibilidad experimental autoriza revisar/integrar, no acepta10k, regresión común, cortoTCP20RPS,900s ni beta. El corto limpio previo sigue FAIL y no se repite por esta rama si su carga no la activa.

## Regresión integrada: negativo de migración y corrección de expectativa

145121-b0b597fc:13PASS/1FAIL/0ERROR/0SKIP,220,03s. Nuevo caso integrado, paridad comercial, snapshots y membresía pasan; falla test_publication_state_upgrade al exigir elegibilidad/versiones intactas después de ejecutar también0023. La migración del contrato romántico establece deliberadamente eligible=False/rules_version=romantic-contract-migration. Auditoría b08-extended-focused-negative-terminal-audit-20261020.json confirma negativo, fuentes, limpieza y Telegram1792508132681264415-635249. No fallo de privacidad ni permiso a conservar autoridad obsoleta.

Se corrige sólo la prueba antigua: migrar16→17 y exigir conservación exacta de todos los campos más invalidación/activación de triggers; después migrar hasta la actual y exigir mismos registros/campos salvo exactamente eligible=False y versión de política romántica. Al refrescar, exigir censo actual sin pendientes. No relajar conservación de datos ni reactivar contenido heredado. Producto622 intacto desde integración; repetir14focal antes del común172 previsto. Negativo13/1 preservado.

## Regresión focal integrada auditada

145653-5088b061:14PASS/0FAIL/0ERROR/0SKIP,219,42s; auditoría b08-extended-focused-terminal-audit-20261020.json, fuentes comparadas de nuevo/limpieza/Telegram1792508464384608006-669984 confirmados. Caso nuevo, paridad comercial, snapshots, membresía y migración con distinción17/23 pasan. Negativo13/1 conservado, producto sin otra edición. Común172 previsto en29selectores/2workers antes de escala116; todavía no ejecutado. Protocolo116 preparado para100→1000→10000 con auditoría entre tamaños, no medición realizada ni capacidad.

## Común integrado172 auditado

150424-ac634094:172PASS/0FAIL/0ERROR/0SKIP,29selectores/2workers. Auditoría b08-extended-common-terminal-audit-20261020.json confirma todas las selecciones, fuentes congeladas comparadas de nuevo, contenedores/temporales/procesos retirados, Telegram1792509208990615425-717893 y prueba real de worker/Beat con jobs/logs/cierre. PostgreSQL/Redis/Chromium reales locales. Cubre regresión focal, superficies, caducidad, promociones, privacidad y SEO sobre fuente integrada; producto622 inalterado desde integración. Corrección aceptada en este alcance funcional local, sin aceptación globalB08/beta ni capacidad. Sigue [escala116](116-escala-estados-pendientes-integrada-beta-20261020.md):100,1000,10000 de forma secuencial y con auditoría antes de ampliar, todavía no ejecutada. Corto limpio20RPS sigueFAIL; no900s.

## Escala integrada116 verificada

151704/151920/152335 auditados1PASS cada uno,74/148/898HTTP y5/42/417páginasES por fase con paridad exacta; manifiestos completos idénticos en los tres tamaños. A10000 medianas frescas262–350ms y con49pendientes473–587ms; contextos observados24 frente máximo97, no validación de población completa. Recibos/limpieza/fuentes confirmados, sin otra edición de producto. [116](116-escala-estados-pendientes-integrada-beta-20261020.md) conserva medidas y límites; no nuevo ROI causal a10000 ni TCP. Preparada [regresión amplia117](117-regresion-funcional-amplia-beta-20261020.md) por los cambios globales de perfil/esquema/publicación; todavía no lanzada. Corto20RPS sigueFAIL y900s bloqueado.
