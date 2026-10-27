# Resumen duradero del contrato de recorridos

Contrato340/roadmap341, ejecución del 25 al 27 de octubre de 2026. Este corte
custodia los resultados antes de la última operación. El estado efectivo del
cierre y la purga lo acredita exclusivamente la constancia terminal al final,
que sólo se cumplimenta después de la limpieza real; no se anticipa su ejecución.

## Candidata, entorno y alcance

Worktree `/home/felidae/proyectos/web_modelos_mod08_vps`, rama `master`.
Último cambio de aplicación: `48dfad61f71ccd378d5e6ccd979c91d4b7908cc7`.
Regresión integrada N11D sobre esa candidata. Helper de recibos externos:
`d0152061725a2989e597a3fb8fa489f8ab63e9fb`; inventario actual: `f9a01fb`;
entrega frontend: `7cca6fc`. El acta24 y el historial Git identifican el cierre documental; la constancia terminal registra la última operación.

Python de aplicación 3.12.15, Django 5.2.17, PostgreSQL17 y Redis7.4 en recursos
propios de los runners; htmx2.0.11. No se sustituye ese runtime por Python3.10
aislado de graphify ni por el kit de ingeniería. Dependencias, imágenes y huellas
de cada ejecución pertenecen a su propio freeze: no se proyectan versiones
actuales retrospectivamente. Los manifiestos y archivos técnicos retenidos
permiten consultar las identidades concretas; no contienen credenciales.

Datos exclusivamente sintéticos. Las cardinalidades, idiomas, roles, escenarios,
cuotas, cachés, concurrencia, oráculos y límites pertenecen a cada prerregistro
y aceptación enlazados. Las unidades no son intercambiables: tiempos QA, Client
instrumentado, navegador, worker real, mocks y cargas limpias permanecen separados.
No hay proveedor, cobro, despliegue externo, sujetos reales ni apertura acreditados.

## Aceptaciones y disposición heredada

Once bloques aceptados localmente antes de N15: N00,N01,N03–N11. N15 continúa
pendiente del cierre documental y de la última operación de limpieza. N02 conserva
el diferimiento expreso del usuario al final del desarrollo y los FAIL de2s/5s;
no se convierte en la decimotercera aceptación. N12/B14, N13/B15 y N14/B17 siguen
condicionados. Ver [deuda viva](../deuda-pendiente-viva.md), que también conserva
el contrato general QA aplazado hasta la primera versión estable/productiva.

Las raíces siguientes se verificaron por SHA contra la matriz integrada N11.
Conservan su alcance por escenario y no certifican toda funcionalidad o seguridad.

| Bloque | Raíz retenida | SHA256 |
| --- | --- | --- |
| N00 | [n00-verificacion-matriz-20261025.json](../evidencias/n00-verificacion-matriz-20261025.json) | `0053ad272a878b1cfb24b728cf8f8623b20d308448bf0b6803c55583f8442241` |
| N01 | [n01-aceptacion-verificacion-20261025.json](../evidencias/n01-aceptacion-verificacion-20261025.json) | `b82ab18fdf1f7816170db7dcebec7759630136ec7e931989cf2069f9e726b242` |
| N03 | [n03-aceptacion-verificacion-20261025.json](../evidencias/n03-aceptacion-verificacion-20261025.json) | `216df73c146c758ecec7322e6b4d1c2f9452fed915665b8a45d7758e7af7333c` |
| N04 | [n04-final-acceptance-verification-20261025.json](../evidencias/n04-final-acceptance-verification-20261025.json) | `7cf9ddbcce7a170e1ac6bf3d0b2509599eb1d25dc104156558f47e27445ec18c` |
| N05 | [n05-final-acceptance-verification-20261025.json](../evidencias/n05-final-acceptance-verification-20261025.json) | `c33e10a0624b095a190f9bb4791b43437938cd3ee2eb32cc312a08f988dcf7a2` |
| N06 | [n06-aceptacion-verificacion-20261025.json](../evidencias/n06-aceptacion-verificacion-20261025.json) | `b4ffc33b41efb250991724c8b6843a05dca75bf3c82ec7daad7d9964e353b242` |
| N07 | [n07-aceptacion-verificacion-20261026.json](../evidencias/n07-aceptacion-verificacion-20261026.json) | `e9d85913ee8568cea6e7b57b5875583db5a130220d52052b2b3dfc710d4378b9` |
| N08 | [n08-aceptacion-verificacion-20261026.json](../evidencias/n08-aceptacion-verificacion-20261026.json) | `49861732e8bb96a2c30274ad2e91885a966893f7d7236278403771736ac99eb7` |
| N09 | [n09-s-censo139-aceptacion-local-20261026.json](../evidencias/n09-s-censo139-aceptacion-local-20261026.json) | `f48a73550e1b55feceaa40eecd3cabb9b1e6e349830d67531fe0fe2f822b84bb` |
| N10 | [n10-e-matriz77-disposiciones-20261026.json](../evidencias/n10-e-matriz77-disposiciones-20261026.json) | `c6f504c524f4b155a46bc6bbc1ee89a49e46cbae2cb7060a3f1de8b58c88cdde` |

N11: [acta498](../498-n11-aceptacion-local-integracion-20261027.md), matriz443 y
archivos ABC/D retenidos fuera de artifacts. La conciliación dispone420acciones
con propietario local aceptado y23exclusivamenteN02; otras16comparten ese residual.
N15 actualiza el censo a444 conservando443IDs y añadiendo el callback de login de
Admin ya ligado a la evidencia N10; no añade una nueva ruta o permiso.

## Resultados terminales y fallos preservados

La siguiente tabla resume los45cortes referenciados y auditados por N11D, con
sus conteos XML originales. **No se suman como una única batería ni se convierten
en una regresión global verde.** El archivo D conserva `reuse-audit.json`, sus
puentes de fuentes, selecciones, configuración, hashes y límites completos.
Las columnas separan estados de casos; el resultado terminal es una unidad distinta.

| Run histórico | Resultado terminal original | PASS | FAIL | ERROR | SKIP |
| --- | --- | ---: | ---: | ---: | ---: |
| 20261024-094540-3a6ec8ac | ERROR | 3697 | 3 | 0 | 129 |
| 20261024-140904-a428539f | PASS | 23 | 0 | 0 | 0 |
| 20261024-141535-575cebdd | PASS | 2 | 0 | 0 | 0 |
| 20261024-144205-543aec10 | PASS | 9 | 0 | 0 | 0 |
| 20261024-144428-6598f5bf | PASS | 1 | 0 | 0 | 0 |
| 20261024-144542-a6eb827a | PASS | 1 | 0 | 0 | 0 |
| 20261024-145152-95525323 | PASS | 1 | 0 | 0 | 0 |
| 20261024-145645-013a5c10 | PASS | 1 | 0 | 0 | 0 |
| 20261024-145646-7c8733cc | PASS | 1 | 0 | 0 | 0 |
| 20261024-150052-406f7c6e | PASS | 1 | 0 | 0 | 0 |
| 20261024-152239-04da2fb0 | PASS | 1 | 0 | 0 | 0 |
| 20261024-215821-1bc5d75d | PASS | 7 | 0 | 0 | 0 |
| 20261024-235904-c98b179b | BETA_HTTP_CONTRACTUAL_PASS_NOT_GLOBAL | 1 | 0 | 0 | 0 |
| 20261025-081326-9844f827 | PASS | 2 | 0 | 0 | 0 |
| 20261025-083656-adcd31ae | PASS | 1 | 0 | 0 | 0 |
| 20261025-090357-d51eb3f9 | PASS | 1 | 0 | 0 | 0 |
| 20261025-094533-b3968c81 | PASS | 11 | 0 | 0 | 0 |
| 20261025-112239-ba9f016f | PASS | 2 | 0 | 0 | 0 |
| 20261025-154544-5fcdc190 | PASS | 2 | 0 | 0 | 0 |
| 20261025-160202-58da5277 | PASS | 3 | 0 | 0 | 0 |
| 20261025-173129-0e1fb9b8 | PASS | 1 | 0 | 0 | 0 |
| 20261025-175533-a061c196 | PASS | 1 | 0 | 0 | 0 |
| 20261025-180035-0ecdeb99 | PASS | 1 | 0 | 0 | 0 |
| 20261025-180404-86f68fb2 | PASS | 46 | 0 | 0 | 0 |
| 20261025-181549-690b123b | ERROR | 0 | 2 | 0 | 0 |
| 20261025-183022-372b5094 | PASS | 33 | 0 | 0 | 0 |
| 20261025-184432-abf4326e | ERROR | 0 | 4 | 0 | 0 |
| 20261025-184941-1ac056e3 | PASS | 37 | 0 | 0 | 0 |
| 20261025-192053-4c827d97 | PASS | 1 | 0 | 0 | 0 |
| 20261025-195610-4d4d1295 | ERROR | 3 | 8 | 0 | 0 |
| 20261025-200423-1535dac0 | PASS | 49 | 0 | 0 | 0 |
| 20261025-202704-5fab8e4c | PASS | 3 | 0 | 0 | 0 |
| 20261025-205607-7dd0e33b | PASS | 1 | 0 | 0 | 0 |
| 20261025-213715-0bcfabdc | PASS | 4 | 0 | 0 | 0 |
| 20261025-215001-a15f20f3 | PASS | 6 | 0 | 0 | 0 |
| 20261025-233639-833fd457 | PASS | 16 | 0 | 0 | 0 |
| 20261026-002326-91562ec6 | PASS | 2 | 0 | 0 | 0 |
| 20261026-004939-72f06ea0 | PASS | 3 | 0 | 0 | 0 |
| 20261026-014812-0d85aaca | PASS | 13 | 0 | 0 | 0 |
| 20261026-030555-20d5ac97 | ERROR | 3 | 1 | 0 | 0 |
| 20261026-031404-bfa5f7d6 | PASS | 1 | 0 | 0 | 0 |
| 20261026-191554-da2f750f | PASS | 10 | 0 | 0 | 0 |
| 20261026-194756-e6af8904 | PASS | 3 | 0 | 0 | 0 |
| 20261026-213503-04860762 | PASS | 2 | 0 | 0 | 0 |
| 20261026-232308-61cca37e | PASS | 1 | 0 | 0 | 0 |

| Corte posterior relevante | Estado / casos | Tiempo QA y límite |
| --- | --- | --- |
| N11A `20261026-234256-cf0028d1` | 1PASS3FAIL |66,291s; POST tras revocación y oráculo positivo incompleto |
| N11B `20261026-235019-b9ec9ed8` | INVALID; XML3PASS3FAIL |78,737s; fuentesAGENTS cambiaron; no aceptación |
| N11C `20261026-235930-b380126e` |30PASS0FAIL/ERROR/SKIP |205,811s;23esperasPG,18denegaciones,5controles |
| N11D `20261027-001852-53c741ce` |44PASS0FAIL/ERROR/SKIP |196,539s;21ordinarios+23guardasunitarias |
| N15recibos `20261027-012424-b41beb6b` |6PASS0FAIL/ERROR/SKIP |JUnit0,297s/proceso2,074s; transporte mock en unitarios, aviso real del runner separado |

La regresión histórica de3829casos quedó ERROR con3697PASS3FAIL129SKIP.
La correctivaCLI de23PASS es otra ejecución; no reescribe los tres fallos originales.
Los129SKIP conservan121opt-in y8testigos suplementarios, sin contarlos como PASS.
N11A/B y sus fallos, fuentes inválidas y correcciones permanecen en el archivoABC;
N11C demostró la corrección en los escenarios seleccionados y D su convivencia.
No se repitió la batería de horas al cerrar este contrato.

N11D observó253operaciones:252asociadas a31rutas y una404sin resolver. Estados:
200:136;302:51;400:28;403:5;404:25;405:2;409:6. Las denegaciones esperadas no son
la tasa de error de una carga. No hay asignación exhaustiva de esas muestras a
las687ramas inventariadas en la entrega frontend.

## Rendimiento y comparabilidad

N02 mantiene presupuestos incumplidos; no se extrapola el detector de fotos a
los paquetes ni la duración QA a la aplicación. [367](../367-n02-d-resultado-y-diferimiento-mod09-20261025.md)
es la referencia de decisión.

| Etapa N02 | Anterior A/B | Actual A/B | Presupuesto / disposición |
| --- | ---: | ---: | --- |
| Cobertura p95 |3,377/3,368s|3,403/3,404s|2s, FAIL conservado |
| JSON por paquete p95 |6,600/6,529s|6,420/6,494s|5s, FAIL conservado |
| Binario por paquete p95 |6,645/6,770s|6,660/6,608s|5s, FAIL conservado |
| Generación por sujeto |40,744/40,667s|39,749/39,668s|Una muestra por sujeto; no p95 |

N11D sólo aporta referencias Client/SQL instrumentadas sin base temporal equivalente:
home183,577ms/32SQL; favoritos90,211ms/34SQL; retirada200,138ms/69SQL;
recuperación59,630ms/23SQL; revisiónrectificación785,601ms/239SQL.
No son p95, SLA, capacidad o mejoras causales. Las tablas siguientes proceden
literalmente de las aceptaciones conservadas y mantienen sus unidades y límites.

### Tablas retenidas de [377](../377-n06-aceptacion-local-cuenta-panel-representacion-20261025.md)

| Editores | Idioma | Antes(ms) | Después(ms) | Diferencia(ms) | Reducción observada | SQLantes→después |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | EN | 22.742 | 16.915 | -5.827 | 25.62% | 9→8 |
| 1 | ES | 15.539 | 13.539 | -1.999 | 12.87% | 9→8 |
| 10 | EN | 43.430 | 16.901 | -26.529 | 61.08% | 18→8 |
| 10 | ES | 41.634 | 22.321 | -19.313 | 46.39% | 18→8 |
| 100 | EN | 225.516 | 46.849 | -178.667 | 79.23% | 108→8 |
| 100 | ES | 279.575 | 54.110 | -225.466 | 80.65% | 108→8 |

| Escenario/etapa | Antes disponible | Referencia posterior/disposición | Mejora atribuible |
| --- | --- | --- | --- |
| Inicio de revisión/corrección, petición |N01D349,918/390,576/566,035msen fixtures originales|N06B109,875/114,054/131,019msen modalidad encolada y otro observador; no mismo escenario temporal|No evaluable; aplicación no cambió entre esos diagnósticos|
| Cola/ejecución de tareas del inicio |Sin referencia real por esa etapa enN06A|N06Bpublicación→inicio3,689–7,606ms,ejecución208,415–247,054ms; disponibilidad observada después de petición460,337–514,251ms|Nueva referencia; tareas solapadas, no sumar|
| Revocar representación,ClientPOST302 |Sin base equivalente|N06C148,059ms,44SQLen esa transición|No evaluable; sin candidato|
| Token/aceptación/MFA/transferencia/reclamación/guía privada |Referencias parciales351/369; otras17rutas no medidas|N06F120peticiones; tabla374con tiempo/estado/SQLyvalorescompletos por caso|Sin candidato ni porcentaje agregado|
| Cuatro colas,cohortes0/1/10/100/101 |Sin base equivalente|N06Gtabla376:7SQLconstantes; con100registros medianas17,121–37,833mssegún cola/idioma|Nueva referencia; trabajo distinto por tamaño, no ganancia causal|


### Tablas retenidas de [393](../393-n03-aceptacion-local-procesamiento-similitud-20261025.md)

| Acción / escenario / medida | Antes | Después | Diferencia y límite |
| --- | ---: | ---: | --- |
| Detector denso100, pared primera |15,522s|12,901s|−16,9% observado; una muestra por versión |
| Detector denso100, pared mediana5 |14,954175s|12,729232s|−2,224943s / −14,878%; rangos14,761–15,314→12,455–13,287s |
| Detector denso100, CPU del hilo mediana5 |11,992421s|10,128819s|−1,863602s / −15,540%; rangos11,761–12,367→9,960–10,524s |
| Extracciones ORB / SQL / Match por llamada |200/1012/100|101/1012/100|99 extracciones menos; SQL y Match iguales, paridad de todos los campos MatchResult y método/score |
| Subida nueva: petición Client / entrada→ready observado (379,n=1) |Sin base equivalente|170,196ms /1393,651ms|Mejora no evaluable; referencia histórica sin retimar tras B/F1 |
| Subida nueva: publish→inicio / process en worker (379,n=1) |Sin base equivalente|4,622ms /1087,446ms|No evaluable; cola quiescente y prefork2, sin TCP/p95/SLA |
| Duplicado exacto: petición (379,n=1) |Sin base equivalente|81,640ms /20SQL /0 tareas nuevas|No evaluable; transición distinta de la subida nueva |
| Selector D: primeras cohortes |Referencia3–6ms|Candidata9–23ms|Coste mayor visible; contraste funcional, no ensayo de aceleración. Una SQL conservada |
| F1: ACK real de mensaje agotado (n=1) |Sin base equivalente|59,277ms|No evaluable: antes hacía trabajo prohibido; ACK SUCCESS conserva Blob failed4 |
| F1: primera publicación Beat / publish→ready de cohorte (n=1) |Sin pareja comparable|61,352s /1,267s|No evaluable; calendario60s, no CPU ni SLA |
| Detector con histórico0→10→100: mediana5 por cohorte |156,429ms(0)|175,145ms(10) /202,129ms(100)|Mismo código y distinta población: no aceleración causal.22SQL/1confirmación/1Match constantes |
| Callback de cuenta dispatch:0 |No aplica a fotografía|Sin nueva medida fotográfica|Asignación compartida conservada; no inventar latencia de fotos |


### Tablas retenidas de [396](../396-n04-aceptacion-local-descubrimiento-20261025.md)

| Fase | Idioma | Segmento | Primera ms | Mediana5 (rango ms) | CPU hilo mediana ms | SQL |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| organic | es | page1 | 174.892 | 151.055 (145.527–339.205) | 112.506 | 32 |
| organic | es | last_page5 | 156.023 | 178.605 (147.682–196.538) | 128.615 | 32 |
| organic | es | combined_page1 | 146.254 | 176.657 (153.630–324.132) | 119.832 | 32 |
| organic | es | combined_last_page3 | 136.063 | 142.549 (114.919–173.221) | 91.082 | 32 |
| organic | es | empty_combined | 53.384 | 56.393 (53.272–62.390) | 42.389 | 16 |
| organic | es | detail | 61.123 | 55.113 (47.842–56.083) | 31.239 | 22 |
| organic | en | page1 | 137.216 | 159.665 (147.876–169.798) | 119.814 | 32 |
| organic | en | last_page5 | 160.092 | 159.803 (145.817–291.834) | 115.155 | 32 |
| organic | en | combined_page1 | 184.460 | 200.238 (145.587–209.754) | 143.066 | 32 |
| organic | en | combined_last_page3 | 263.895 | 143.436 (128.271–159.623) | 100.607 | 32 |
| organic | en | empty_combined | 72.772 | 65.495 (60.923–271.806) | 47.179 | 16 |
| organic | en | detail | 51.498 | 51.404 (41.388–53.278) | 30.537 | 22 |
| synthetic_promoted | es | page1 | 162.748 | 190.524 (174.894–227.893) | 129.705 | 33 |
| synthetic_promoted | es | last_page5 | 175.383 | 167.739 (149.454–319.177) | 133.575 | 33 |
| synthetic_promoted | es | combined_page1 | 152.013 | 186.950 (170.279–199.805) | 137.177 | 33 |
| synthetic_promoted | es | combined_last_page3 | 144.704 | 165.545 (146.648–177.146) | 107.455 | 33 |
| synthetic_promoted | es | empty_combined | 252.585 | 98.010 (71.396–117.164) | 68.262 | 17 |
| synthetic_promoted | es | detail | 52.887 | 47.954 (44.469–53.107) | 31.296 | 22 |
| synthetic_promoted | en | page1 | 231.174 | 174.252 (158.012–217.858) | 127.106 | 33 |
| synthetic_promoted | en | last_page5 | 182.513 | 181.847 (166.573–218.978) | 138.303 | 33 |
| synthetic_promoted | en | combined_page1 | 178.765 | 231.785 (169.289–369.190) | 162.183 | 33 |
| synthetic_promoted | en | combined_last_page3 | 193.897 | 197.405 (154.258–272.360) | 119.901 | 33 |
| synthetic_promoted | en | empty_combined | 106.515 | 101.021 (91.705–147.407) | 59.347 | 17 |
| synthetic_promoted | en | detail | 96.159 | 59.787 (47.291–61.981) | 35.635 | 22 |

| Acción / escenario | Antes disponible | Después disponible | Diferencia atribuible |
| --- | ---: | ---: | --- |
| R_home, ES orgánico inicial |N01C100:147,753ms|N04B120:151,055ms|No evaluable: población/instrumentación distintas, mismo código público |
| R_home, EN orgánico inicial |N01C100:147,674ms|N04B120:159,665ms|No evaluable; sin candidato |
| R_home, ES promocionado inicial |Sin base equivalente por etapa|N04B120:190,524ms|No evaluable; referencia nueva, no mejora |
| R_home, ES última página5 orgánica |Sin base equivalente por etapa|N04B120:178,605ms|No evaluable; paridad completa de páginas comprobada |
| R_home, ES combinado última página3 |Sin base equivalente por etapa|N04B60seleccionados:142,549ms|No evaluable; selectividad explícita |
| R_listing_detail, ES |N01C100:41,660ms|N04B120orgánico:55,113ms|No evaluable: fixture/observadores distintos |
| R_listing_detail, EN |N01C100:51,813ms|N04B120orgánico:51,404ms|No evaluable; no presentar descenso como optimización |
| Guards/filtros/orden/etiquetas |Testigos funcionales finitos conservados|Paridad actual en144+36respuestas|Sin cambio de aplicación; nueva atribución, no nueva funcionalidad |


### Tablas retenidas de [399](../399-n05-aceptacion-local-imagenes-navegador-20261025.md)

| Idioma | Subida→preview observado (s) | Recarga→preview (s) | Primer API (ms) | Mediana5API (rango ms) | Bytes/cuerpo |
| --- | ---: | ---: | ---: | ---: | ---: |
| es | 1.376 | 0.342 | 212.760 | 101.944 (96.217–139.426) | 9344 |
| en | 1.152 | 0.261 | 185.797 | 141.820 (120.377–148.220) | 9344 |

| Idioma | Solicitud | Estado | Duración observada ms | Cuerpo decodificado bytes |
| --- | ---: | --- | ---: | ---: |
| es | 1 | queued | 110.353 | 456 |
| es | 2 | queued | 57.091 | 456 |
| es | 3 | running | 133.068 | 455 |
| es | 4 | rejected | 62.565 | 185 |
| en | 1 | queued | 111.655 | 450 |
| en | 2 | queued | 85.708 | 450 |
| en | 3 | running | 44.962 | 456 |
| en | 4 | rejected | 40.345 | 170 |

| Acción / medida | Antes disponible | Después / referencia actual | Diferencia y límite |
| --- | ---: | ---: | --- |
| Galería, imágenes iniciales |B09antes:8|B09después yN05C156:1|−7/−87,5%, optimización anterior confirmada, cuatro contextos |
| Galería, bytes iniciales decodificados |135824|11110|−124714/−91,82%, misma fixture y cuerpos; no ahorro total si se recorren todas |
| Galería completa, cuerpos/dimensiones |8/135824bytes|8/135824bytes y hashes exactos|Sin cambio de calidad/codec introducido por N05 |
| Entrega privada ES, mediana5API |Sin base temporal equivalente|101,944ms|No evaluable como mejora; cliente+lectura,9344bytes |
| Entrega privada EN, mediana5API |Sin base temporal equivalente|141,820ms|No evaluable; condiciones/idioma no son versiones de candidato |
| Subida→preview ES/EN |Testigo funcional, sin tiempo aislado|1,376/1,152s|No evaluable; eager explícito, no cola real |
| Recarga→preview ES/EN |Sin base temporal equivalente|0,342/0,261s|No evaluable; nueva observación del cliente |
| Sondeos de estado |Funcional y every3s, sin intervalos aislados|3,068–3,154s; cuatro XHR por idioma|Referencia actual; cero nuevos durante6,506s terminales, no mejora causal |
| CSS/form-errors en contexto representado |12412/962bytes|12412/962bytes|Iguales; HTMX sólo donde realmente se entrega |
| Teclado/estado/privacidad |Testigos anteriores con límites|Cuatro casos de foco156 y actuales de entrega/sondeos|Sin latencia individual ni certificación global inventadas |


### Tablas retenidas de [408](../408-n07-aceptacion-local-medios-publicacion-ciclo-20261026.md)

| Acción / etapa / muestras | Antes | Después o referencia | Diferencia y límite |
| --- | --- | --- | --- |
| Reorder tras remove confirmado, ES/EN |500/StopIteration,2FAIL |404controlado, retirada/orden/versión conservados;4PASS |Corrección funcional; tiempos de petición no comparados |
| Cola abierta, mediana5 ES/EN |Sin base temporal equivalente |Moderación21,976/25,599ms; apelación28,467/20,965ms; matches44,285/43,920ms; foto47,284/51,947ms |Referencia actual sin candidato; tabla407 separa primera/rango/estado/SQL |
| Formulario revisión abierto, mediana5 ES/EN |Sin base equivalente |Moderación93,929/64,778ms; apelación41,323/31,965ms; matches59,183/88,931ms; foto68,469/58,657ms |Nueva referencia; no aceleración causal ni tiempo humano |
| Refresh Beat, dos ejecuciones nativas |Sin base equivalente |177,410/273,180ms de tarea;24,851/10,529ms de cola |n1por fase distinta, no mediana; intervaloBeat29,991871s |
| Expiry Beat nativo |Sin base equivalente |122,627ms tarea/7,390ms cola;61,494s tras spawn |Edad de evento64,572947s observada, no SLA |
| Sweep manual y reparación posterior |Sin base equivalente |452,045/275,777ms tarea |Procesos distintos, no suma como latencia universal; sin calendario3600s |
| Cancelación manual inicial ES/EN, n1por idioma |Opción disponible sin testigo de ejecución localizado |121,143/325,137ms;45SQL y302 |Referencia de ramas separadas, no mejora; detalle de restantes reintentos en auditoría |
| Retry antiguo de cancelación ES/EN, n1 |Sin referencia equivalente |34,278/46,517ms;13SQL y302; nueva ventana intacta |Sin nuevo evento; no promediar con mutación |
| QA de lotes A/B/C/cancelación |Baterías distintas |57,786s/118,068s/136,563s/54,192s respectivamente |No sumar como una ejecución ni usar como latencia de app |


### Tablas retenidas de [417](../417-n08-aceptacion-local-superficies-comerciales-20261026.md)

| Acción / estado | Mediana5 antes (ms) | Mediana5 después (ms) | Diferencia (ms) | Cambio | SQL antes→después |
| --- | ---: | ---: | ---: | ---: | --- |
| Favoritos100, página1, ES normal |2217,110|244,720|−1972,391|−88,962%|563→30|
| Favoritos100, página1, EN normal |2141,365|210,281|−1931,084|−90,180%|563→30|
| Favoritos100, página1, ES uno revocado |2034,547|222,085|−1812,462|−89,084%|546→30|
| Favoritos100, página1, EN uno revocado |2163,705|207,346|−1956,360|−90,417%|546→30|
| Sitemap100, normal |9009,700|375,775|−8633,925|−95,829%|2402→18|
| Sitemap100, uno revocado |9292,321|277,708|−9014,613|−97,011%|2385→18|

| Acción / escenario | Antes de otro candidato | Referencia actual (ms) | Después de otro candidato / mejora |
| --- | --- | --- | --- |
| Alta de favorito y replay, dos estados n1 en regresión412 |Sin par equivalente|106,023/102,949;42/39SQL|No medido / no evaluable|
| Baja propia de favorito, n1 en regresión412 |Sin par equivalente|19,207;12SQL|No medido / no evaluable|
| Robots desarrollo / índice vacío / directorio, n1 separados412 |Sin par equivalente|1,529 /58,395 /2,003|No medido / no evaluable|
| Índice legal100 ES/EN, mediana5,1SQL |Sin par equivalente|10,226/8,759|No medido / no evaluable|
| Detalle legal ES/EN con100activos, mediana5,1SQL |Sin par equivalente|2,982/3,466|No medido / no evaluable|
| Historial100 página1de25 ES/EN, mediana5,9SQL |Sin par equivalente|58,935/42,734|No medido / no evaluable|
| Detalle pedido ES/EN, mediana5,6SQL |Sin par equivalente|24,941/15,778|No medido / no evaluable|
| Formulario100anuncios /100productos ES/EN, mediana5,8SQL |Sin par equivalente|53,137/42,648 y44,543/52,704|No medido / no evaluable|
| Catálogo100 /versiones100 página1de50 ES/EN, mediana5 |Sin par equivalente|27,467/26,870 y53,613/40,944|No medido / no evaluable|
| Edición /vista previa borrador ES/EN, mediana5,8SQL |Sin par equivalente|27,502/25,224 y21,177/27,568|No medido / no evaluable|
| Tarea preencolada /replay /dos ticks Beat, n1por etapa |Sin par equivalente|397,838 /288,758 /233,881 /191,542|No medido / no evaluable|


### Tablas retenidas de [472](../472-n09-aceptacion-local-derechos-avisos-limpieza-20261026.md)

| Etapa o corrección | Antes / referencia anterior | Estado o referencia actual | Después de otra candidata de rendimiento |
| --- | --- | --- | --- |
| Cola de derechos ES, un expediente | Sin base normal equivalente inspeccionada | Primera 155,940 ms; mediana de cinco posteriores 21,264 ms; 7 SQL | Sin candidata |
| Inspección nueva de plan | Sin base normal equivalente inspeccionada | 328,939 ms y 122 SQL; N=1 | Sin candidata |
| Aprobación nueva de rectificación | Sin base normal equivalente inspeccionada | 655,886 ms y 222 SQL; N=1 | Sin candidata |
| Resolución upheld nueva de reclamación | Sin base normal equivalente inspeccionada | 86,576 ms y 26 SQL; N=1 | Sin candidata |
| CopyInformation, lote de 100 vencidos | Referencia I: 5,991 ms y 2 SQL | Conservada, sin repetirla ni transferirla a otros modelos | Sin candidata |
| Outbox, 100 avisos simulados | Referencia J: 1.402,331 ms y 802 SQL | Conservada; fallos/reintentos siguen observables | Sin candidata |
| Purga de exportaciones, lote de 1.000 del volumen 1.001 | Referencia O: 2.097,922 ms y 1.007 SQL | Conservada; efectos locales y retención verificadas | Sin candidata |
| Plan privado tras revocación durante espera, R | New descifra antes de denegar; replay devuelve cuerpo privado | Ambos deniegan antes del descifrado seleccionado; diez casos correctos, tabla QA por pareja en468 | Corrección de autoridad; sin comparación de latencia normal |


### Tablas retenidas de [491](../491-n10-aceptacion-local-operacion-20261026.md)

| Acción | Antes | Después verificado | Interpretación |
|---|---|---|---|
| GroupAdmin tras revocación durante espera | 1 PASS/1 FAIL,55,892 s QA | 16 PASS,159,971 s QA | Corrección funcional; no mejora de latencia |
| Login Admin epoch1 | 1 PASS/1 FAIL,59,198 s QA | 10 casos únicos entre primera candidata y focal | Primera candidata7 PASS/3 FAIL por oráculo RateWindow; focal4 PASS,76,644 s; seis reutilizados por identidad |
| Arranque Gunicorn propio | Sin comparador equivalente | 4 workers listos en1,690 s | Sondeo50ms, no SLA |
| Health | Sin comparador equivalente | Primera62,325 ms; mediana cinco3,164 ms | TCP local, cohorte fija |
| operational_snapshot nativo | Sin positivo CLI comparable | Primera129,319 ms; mediana cinco127,491 ms,50 SQL | In-process; no coste de spawn Python |
| Group changelist ES / EN | Sin comparador equivalente | Primera49,497 /39,126 ms; mediana cinco29,618 /40,819 ms,9 SQL | Cohorte de un target, no crecimiento |
| Password Admin ES / EN | Sin comparador equivalente | 230,965 /256,933 ms,12 SQL | Una muestra por idioma |
| Sesión peer tras cambio ES / EN | Sin comparador equivalente | 10,036 /15,265 ms,4 SQL | Hash antiguo invalida sesión; no revocación universal de tokens |
| Logout Admin ES / EN | Sin comparador equivalente | 16,658 /18,222 ms,6 SQL | POST/CSRF nativos y efecto exacto |
| Retorno actual→anterior→actual | Sin comparador equivalente actual | F:1 PASS,57,716 s QA; tiempos de proceso/HTTP en490 | QA y latencia separados; no image switch |


## Reconstitución y reproducción, sin ejecución automática

Conservar el checkout candidato y las dependencias fijadas por `requirements`
y los manifiestos de cada freeze; disponer de Docker, fuentes nativas y runner
oficial indicados en esos manifiestos. Usar sólo PostgreSQL de integración y los
recursos sintéticos propios del runner, nunca una base real. Toda nueva ejecución
debe conservar los avisos Telegram y producir sus propios recibos/versiones.
La purga pierde el bruto histórico exacto: reproducir genera evidencia nueva.

Para reconstruir la selección N11D, leer sin extraer a disco
`n11d/selection.json` del [archivoD](../evidencias/n11-d-regresion-conciliacion-20261027.tar.gz).
El comando es `.venv/bin/python scripts/run_local_ci.py --profile focused
--workers 1 --timeout 1800 --observe-http-operations`, añadiendo `--test <selector>`
por cada elemento de `selection` en su orden;21selectores/44casos esperados.
Los fixtures de esos tests describen sujetos sintéticos, idioma, permisos,
estados y configuraciones eager/mocks o reales de cada escenario. Conservar
los límites de [496](../496-n11-d-prerregistro-regresion-comun-integrada-20261027.md).

Para el helper de recibos, la selección es `--test tests/test_test_notifications.py`
en perfil focused/1worker; no convertir sus seis mocks en una integración externa.
La custodia está en [501](../501-n15-recibos-externos-verificados-20261027.md).
Los otros bloques remiten a sus prerregistros y archivos retenidos desde las
raíces de aceptación: no se proporciona una batería única que mezcle escenarios,
presupuestos, workers o versiones incompatibles. No lanzar estas órdenes por
consultar este resumen ni después de la purga dentro de este contrato.

## Entregables que permanecen fuera de artifacts

- Fuentes, Git, docs y evidencias originales: no forman parte de la limpieza.
- [Inventario actual](../evidencias/inventario-acciones-actual-20261027.json),
  [338](../338-inventario-acciones-recorridos-alpha-20261025.md) y
  [339](../339-diferencial-inventario-recorridos-20261025.md), con111yJSON25inmutables.
- [Entrega frontend507](../507-n15-base-y-contratos-frontend-20261027.md), sus
  contratos técnicos autocontenidos y verificaciones. htmx4 no implementado.
- Grafo completo en `graphify-out`, incluyendo el checkpoint de reconstrucción;
  [503](../503-n15-grafo-total-reconstruido-y-verificado-20261027.md) y
  [508](../508-n15-conciliacion-semantica-frontend-20261027.md) identifican sus cortes.
- Archivos ABC/D de N11, custodia501 y archivos de aceptación de cada bloque.
  Son entregables ya seleccionados, no una copia de los brutos que se van a purgar.

Las referencias bajo `artifacts` en documentos anteriores pasan a ser históricas
tras la purga; no se promete que sobrevivan. Las fuentes/citas y la procedencia
de la entrega frontend están embebidas fuera de esa carpeta. No hay nuevas
obligaciones por skills instaladas ni servicios habilitados en el cierre.

## Límites, deuda y siguiente contrato

Alpha/noindex. Alcance local por escenarios, sin certificación universal de
seguridad, RGPD, accesibilidad, SLA o capacidad. N02 y los condicionados N12–N14,
así como QA general aplazado, se trasladan explícitamente al siguiente contrato.
La siguiente etapa UI/UX/Front sigue Django Templates, UI/UX Pro Max y dirección
htmx4 con preparación de sus skills oficiales; no se ejecuta aquí la reescritura.

## Constancia terminal de limpieza — pendiente

**No ejecutada en este corte.** Antes del borrado faltan acta/Git, conciliación
documental final y comprobación de procesos, descriptores y montajes/dependencias.
Ruta autorizada única: `/home/felidae/proyectos/web_modelos_mod08_vps/artifacts`.
Debe vaciarse íntegramente, incluidos ocultos, como última operación obligatoria.
No alcanza fuentes, Git, docs/evidencias, datos, volúmenes, servicios ni otros worktrees.
Registrar aquí UTC, ocupación y libre antes/después, bytes recuperados y carpeta
vacía tras ejecutar; avisos y recibos fuera de artifacts. Después sólo constancia
documental y Git, sin nuevas pruebas ni regeneración de artefactos.
