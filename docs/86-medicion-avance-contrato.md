# Medición del avance del contrato

Estado vigente: revisión ponderada v3 al final, basada en entregas hasta `38140e9`. v1/v2 se conservan como cortes históricos; pesos y denominador no cambian.

## Corrección del seguimiento

Las cifras82% CR09 y56% contrato eran estimaciones sin desglose de pesos ni denominador verificable. Repetirlas tras entregas nuevas no permite medir avance: quedan como referencia histórica, no como medición actual. No sustituirlas por otra cifra subjetiva.

El contrato16 define15 hitos: BASE, CR01–10, GS01, BF, BB y C. El seguimiento17 declara BASE yCR01–08 verificados localmente:9/15,60% del número de hitos. Este cociente asigna el mismo peso a todos, no mide horas, complejidad, trabajo completado ni preparación de producción. CR09 sigue abierto, por lo que su trabajo parcial no cambia este contador. No afirmar que falta40% del esfuerzo.

## Avance verificable dentro de CR09

La aceptación de CR09 requiere la matriz residual de docs83, además de los recorridos funcionales y sus pruebas. Un requisito puede contener varias implementaciones, variantes y dependencias; un número de tests no mide cuánto trabajo falta.

Registrar para cada requisito: implementación entregada y commit, pruebas actuales y versión, evidencia, variantes pendientes, dependencias externas y condición concreta de aceptación. Distinguir estados pendiente, implementación parcial, verificado en alcance limitado y aceptado. No declarar aceptado todo un derecho por haber probado una operación.

Entregas recientes verificables:

- b50e69f: aplicador0100, destrucción física, comando operacional, restauración real PostgreSQL y aislamiento HTTP/worker/Beat;67 pruebas conjuntas y runtime verificado.
- c004262: trazabilidad de sustitutos firmados para fotos compartidas y dos eventos consecutivos;76 pruebas conjuntas, runtime actualizado y push confirmado.
- Entrega posterior de autoridad0100: validación compartida de sustituto vacío/privado y checkpoint esperado independiente;80 pruebas conjuntas correctas320,56s y Docker verificado.

Estos avances son reales aunque el hito siga abierto. Los defectos reproducidos y corregidos también son progreso hacia aceptación, pero no permiten estimar automáticamente cuántas horas o qué porcentaje quedan.

## Porcentaje de trabajo

Antes de publicar otro porcentaje de trabajo, descomponer todos los requisitos del contrato en unidades de aceptación concretas, asignar pesos con una base explícita, evitar contar dependencias o pruebas repetidas como entregas nuevas y mantener un denominador estable. Cada cambio de alcance/peso debe registrarse. Hasta que exista esa matriz, informar entregas y pendientes concretos; porcentaje de esfuerzo no disponible.

El contador de hitos y la aceptación de producción permanecen separados. Proveedores, revisión jurídica y gates de producción no se acreditan por pruebas sintéticas locales.

## Baseline ponderada v1 solicitada por el usuario

Se adopta una estimación por alcance y complejidad. Los pesos y grados de avance son juicio técnico explícito, no horas medidas ni aceptación formal. Referencias: contrato16, seguimiento17, matriz83 y recursos87. Los porcentajes antiguos82/56 no se reutilizan. Fórmula: suma(peso × avance estimado /100). Pesos100 en cada nivel; no cambiar denominador por repetir pruebas.

### CR09

| Bloque | Peso | Avance estimado |
| --- | ---: | ---: |
| Portabilidad y respuesta privada | 15% | 90% |
| Purga de contenido caducado | 5% | 100% |
| Flujos de denuncias y derechos por finalidad, verificación y autoridad | 20% | 65% |
| Conservación y destrucción por finalidad | 10% | 50% |
| Restauración de datos y medios | 15% | 85% |
| Sesiones, cachés, colas, logs y recursos externos | 10% | 45% |
| Comunicaciones y destinatarios | 8% | 50% |
| Atención urgente y escalado | 7% | 60% |
| Rendimiento de expedientes grandes | 5% | 30% |
| Aceptación integral CR09 | 5% | 0% |

El bloque de flujos incluye formularios públicos/colas de denuncias, expediente/verificación/autoridad y acceso/rectificación/supresión/limitación/oposición, para no ponderar únicamente lo que queda de recuperación. Portabilidad y purga poseen evidencia de entregas específicas; otros derechos siguen con aceptación por finalidad pendiente. Restauración incluye ensayos reales locales y recibos firmados; recursos locales incluyen trabajo de sesiones/colas aún sin entregar. Comunicaciones/escalado/rendimiento siguen parciales y aceptación integral no completada. Esta valoración inicial debe revisarse contra cambios concretos, sin presentar cada grado como un dato medido.

Resultado CR09:63,45%, comunicar **aproximadamente63% completado y37% pendiente**.

### Contrato completo

| Hito | Peso | Avance estimado |
| --- | ---: | ---: |
| BASE | 5% | 100% |
| CR01 | 4% | 100% |
| CR02 | 6% | 100% |
| CR03 | 6% | 100% |
| CR04 | 5% | 100% |
| CR05 | 8% | 100% |
| CR06 | 6% | 100% |
| CR07 | 6% | 100% |
| CR08 | 4% | 100% |
| CR09 | 15% | 63.45% |
| CR10 | 5% | 0% |
| GS01 | 3% | 0% |
| BF | 10% | 0% |
| BB | 10% | 0% |
| C | 7% | 0% |

BASE/CR01–08 aportan50 puntos del contrato; CR09 aporta9,5175. Resultado59,5175%, comunicar **aproximadamente60% completado y40% pendiente**. CR09 representa15% del peso total. GS01, BF, BB y C tienen pesos propios para no equiparar un flujo pequeño con acabado y entrega. No afirmar que esas fases están iniciadas por tener componentes reutilizables de la fase cruzada.

[Datos y cálculo](evidencias/avance-ponderado-v1.json). Esta baseline sustituye la ausencia de estimación de trabajo anterior, pero no altera el contador de hitos ni declara CR09 aceptado. Los pendientes externos de producción siguen diferenciados de pruebas sintéticas/locales.

## Revisión del avance con Git solicitada por el usuario

Revisión sobre HEAD036a1a0 y remoto master confirmado al mismo hash. Desde83c9d63 hay tres entregas:

| Commit | Cambio funcional | Efecto en cierre del contrato |
| --- | --- | --- |
| b50e69f | Aplicador tipado, destrucción física, restauración real y aislamiento HTTP/worker/Beat | Recuperación antes pendiente ahora implementada/verificada localmente; CR09 no aceptado |
| c004262 | Sustitutos firmados y recuperación de eventos consecutivos | Corrige un defecto reproducido y conserva fotos ajenas; no añade un hito cerrado |
| 036a1a0 | Checkpoint esperado independiente y validación común de preflight/aplicación | Refuerza consistencia/autoridad; sigue pendiente custodia externa y aceptación integral |

El diff83c9d63..036a1a0 contiene46 archivos,2837 inserciones/47 borrados, incluyendo aplicación, pruebas y evidencias. Son señales de actividad y entregas concretas, no una medida de esfuerzo o aceptación. El historial anterior también concentra commits en portabilidad/derechos; las tres últimas entregas siguen dentro de recuperación de CR09. No se ha avanzado a CR10 ni cerrado otro hito durante este tramo.

Conclusión: avance funcional real y comprobable, sin bloqueo técnico; concentración prolongada en un subsistema y ritmo de cierre de hitos bajo. No presentar repetir regresiones o documentar un mismo componente como requisitos distintos terminados. Próximo: concluir entrega de sesiones/colas actualmente en verificación y trabajar la matriz restante de derechos/finalidades. No ampliar recuperación con requisitos inventados; resolver defectos/requisitos concretos conservando el alcance del contrato.


## Revisión ponderada v2 — 2026-10-06, 187b8e6

Conservar exactamente los pesos de v1. Solo actualizar dos juicios de avance por alcance entregado: flujos65→75 por acceso completo local y respuesta/revisión/cierre de rectificación perfil/cuenta; comunicaciones/destinatarios50→60 por cuenta sin perfil y emisión final privada/aviso único. Referencias: f252ae0,02210aa,187b8e6, docs88 y evidencias de acceso/rectificación. No elevar recursos operativos45, conservación50 ni aceptación integral0: sus pendientes siguen reales. No contar correcciones, commits, tests repetidos o filas auxiliares como nuevos requisitos.

Son estimaciones de ingeniería, no horas medidas ni aceptación formal; el grado de cada bloque conserva incertidumbre. Cambios aportan2,8 puntos a CR09 y0,42 al contrato, cuya fase CR09 pesa15%. Cálculo reproducible: **CR09 66,25% avanzado y33,75% pendiente; contrato59,9375% avanzado y40,0625% pendiente**. Comunicar66,3% y59,9% con una decimal cuando se solicite, dejando clara su naturaleza estimada. El contador de hitos sigue9/15; CR09 todavía abierto.

[Datos y cálculo v2](evidencias/avance-ponderado-v2.json). La revisión sustituye63,45/59,5175 como valoración vigente y conserva v1 como histórico. Las cifras no acreditan producción; CR10/GS01/BF/BB/C continúan pendientes como fases.


## Revisión ponderada v3 — 2026-10-06, fuente38140e9

Se mantiene todo el denominador de v2. Solo flujos por finalidad/verificación/autoridad pasa75→85: supresión, limitación y oposición incorporan respuestas parciales propias con preparación/lectura/revisión/emisión/acuse, perfil/cuenta/publicación/calendario, medios y concurrencia. El motor compartido y el acuse mantienen supresión/portabilidad en batería integrada20 y Docker verificado. El incremento corresponde a alcance funcional entregado, no al número de pruebas. Siguen pendientes sus cierres integrales y el censo operacional real, conservación y comunicaciones: los grados de esos bloques y aceptación integral no aumentan.

CR09:66,25 + (20 ×10/100) = **68,25% avanzado /31,75% pendiente**. Contrato:59,9375 + (15 ×2/100) = **60,2375% avanzado /39,7625% pendiente**. Comunicar68,3% y60,2%. CR09 conserva peso15% del contrato y continúa abierto. Son estimaciones de ingeniería explícitas, no esfuerzo medido ni aceptación de producción. [Cálculo v3](evidencias/avance-ponderado-v3.json), [resultados](evidencias/limitacion-oposicion-final0108-en-desarrollo.json), [runtime](evidencias/limitacion-oposicion-final-runtime0108.json).


## Revisión ponderada v4 — 2026-10-06, 637e456

Conservar todos los pesos y todos los grados de v3 excepto comunicaciones/destinatarios60→70. Ahora existe evaluación/revisión independiente, entrega interna mínima por ejecución y destinatario vigente, buzón/consulta/acuse auditado, reevaluación y consumo en respuesta final parcial para supresión/limitación/oposición, incluyendo PostgreSQL/HTTP/móvil/concurrencia y Docker0110. [Alcance y resultados](evidencias/comunicaciones-derechos-integradas0110.json), [runtime](evidencias/comunicaciones-derechos-runtime0110.json). Destinatarios históricos, destinos/censo externos y aceptación integral permanecen abiertos:70 es estimación de ingeniería, no cobertura porcentual medida ni aceptación jurídica.

El cambio aporta0,8 puntos a CR09 y0,12 al contrato: **CR0969,05% avanzado/30,95% pendiente; contrato60,3575% avanzado/39,6425% pendiente**. [Cálculo v4](evidencias/avance-ponderado-v4.json). Ningún hito nuevo aceptado y ningún aumento por número de pruebas/commits. El estado vigente se mantiene únicamente en seguimiento17.


## Revisión ponderada v5 — MOD-01, 2026-10-06

Pesos de v4 intactos. Recursos45→55 por sesiones propias caducadas/correo console en copia revisada/límites Redis reales/cache sin almacén/histórico AOF tipado ligado al paquete; no censo histórico/host externo completo. Urgentes60→70 por seguimiento reconocido no terminal con responsable/paso a consulta existente ES/EN/móvil; escalado humano/canal externo pendientes. Rendimiento30→35 por calendario1100 entradas sin materializar listado completo y AOF40,5MB incremental medido; falta rendimiento integral del expediente. Conservación permanece50: seguimiento ya existía y corregir revocación de autoridad no añade política/finalidad. Ningún otro grado cambia. Alcance entregado localmente y runtime8a689fc, no suma de pruebas ni aceptación de fase.

DeltaCR09=(10×10+7×10+5×5)/100=1,95; **CR0971,00% avanzado/29,00% pendiente; contrato60,65% avanzado/39,35% pendiente**. CR09 pesa15%; aceptación integral permanece0 y fases posteriores sin aceptar. [Cálculo v5](evidencias/avance-ponderado-v5.json). Estimación de ingeniería explícita, no horas/cobertura jurídica medidas.


## Revisión ponderada v6 — 2026-10-06, fuente8114457

Pesos y demás grados de v5 intactos. Recursos55→60 por un tipo nuevo de recurso retenido entregado: procedencia de28 claves de resultado worker sintético mediante identidades exactas/actas/log con SHA/script original Git;54 observaciones validadas y adaptación de contador periódico explícito con evidencia HMAC, negativos/PG y Docker70 hashes. Corte de secuencia base/prefijo/sufijo observado estable y caducidad offline sin pérdida en este corte, sin sustituir revisión por expediente ni censo host/backups/otras fuentes. [Procedencia](evidencias/redis-resultados-procedencia-actas0110.json), [pruebas](evidencias/redis-periodicos-contadores0110.json), [runtime](evidencias/redis-periodicos-runtime0110.json). El grado es juicio de ingeniería por alcance nuevo, no proporción de claves ni número de pruebas.

DeltaCR09=10×5/100=0,50; **CR0971,50% avanzado/28,50% pendiente; contrato60,725% avanzado/39,275% pendiente**. CR09 pesa15%, de modo que el cambio completo aporta0,075 puntos. Conservación50/rendimiento35/aceptación integral0 y fases posteriores intactos. SEO independiente preparado no se cuenta como fase aceptada. [Cálculo v6](evidencias/avance-ponderado-v6.json). Estado/cola únicos en seguimiento17.
