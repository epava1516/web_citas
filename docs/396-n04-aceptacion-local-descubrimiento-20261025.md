# N04 — aceptación local de listado, filtros, paginación y ficha

25 de octubre de2026. Alfa. N04 queda verificado localmente con decisión **sin cambio de aplicación** en los escenarios seleccionados. N00/N01/N03/N04/N06 aceptados: **5/13 bloques obligatorios**. Producto `139ed2c`; fuentes completas en la congelación corregida N04B. No se atribuye una optimización nueva ni se abre beta.

## Requisito → acción → evidencia → límite

Contrato340, criterios354 y roadmap341/N04; estudio394 y prerregistro395. Codex contrastó las dos acciones censadas y14 fuentes de regla pública/plantillas, idénticas a B16 yN01A/B/C. Verificó15citas del revisor del instrumento, fuentes actuales y resultados originales. El informe nativo es un insumo contrastado; la aceptación es decisión de Codex.

| Acción | Decisión y candidata | Evidencia y resultado | Límite y deuda |
| --- | --- | --- | --- |
| route:R_home, I01–I04 | Conservar aplicación: estados, fallback, filtros, ranking, guards y presentación | N01A/B/C; testigos funcionales previos de autoridad inmediata, patrocinio/cupos/rotación y paginación; N04B actual:120peticiones state,24segmentos totales contando ficha,144medidas y36GET de páginas fuera de reloj | Población120, promociones sintéticas24, páginas1/5 y filtro positivo60 en páginas1/3, vacío y dos idiomas. No todas las combinaciones ni capacidad general |
| route:R_listing_detail, I05 | Conservar snapshot read-only y guard nativo en transacción heredada; sin cambio de código | N01B/C y testigos previos de localización/privacidad/retirada;24peticiones actuales de ficha dentro de N04B con guard y render reales | No navegador, entrega de imágenes ni proveedores: N05 conserva ese alcance; N07 conserva lifecycle |

La revisión original de testigos incluye cinco JUnit y57casos seleccionados comprobados contra sus archivos. Uno de esos archivos históricos contiene fallos ajenos a la selección: no se convierte en batería global verde ni se importan todos sus casos como nuevas garantías de N04. El protocolo limpio334 conserva su PASS histórico de mezcla,18 000muestras y p95 observable410,559ms. Se comprobó el JUnit y SHA del archivo original de su topología real, no una repetición de carga. La identidad de las fuentes públicas justifica su conservación en su ámbito; no representa p95 nuevo ni umbral800ms por variante. N11 mantiene la conciliación de candidata integrada.

## Referencia actual y oráculos

Run `20261025-205607-7dd0e33b`: **1PASS,0FAIL/ERROR/SKIP**,91,577sJUnit;1747huellas intactas. PostgreSQL/Redis propios, almacenamiento local y broker aislado. Directorio nativo,120publicados con60woman/en y60man/fr; dos fases ordenadas, orgánica y con24derechos sintéticos8Premium/16Top emitidos por servicios reales de órdenes/eventos sintéticos. No cobros ni proveedor real.

Pertenencia fijada por preparación y comprobada con autoridad nativa, sin usar la respuesta como su propio oráculo. Ranking congelado de B08, SHA9f700b72394edbc8aac1a671081885b66c1754ed97f6c012a9f802bc45337c29; comparte primitivas nativas y no se presenta como implementación totalmente independiente. IDs ordenados, conteos, etiquetas, no duplicados,200/no-store, idioma y ausencia de centinelas privados comprobados en cada respuesta. Recorridos completos de páginas fuera de relojes:12grupos de cobertura,36GET. Estados actuales, sin dirty; datos editoriales, revisiones y derechos intactos durante peticiones.

Los perfiles sin approved_revision son rechazados por el guard nativo por separado; PublicationContext sólo recibe filas con revisión aprobada no nula, conservando también las no publicables con esa FK. Esta corrección del borrador evita una llamada fuera del contrato de ese hidratador; no omite el negativo.

## Tiempos actuales por segmento

Milisegundos de aplicación instrumentada. Primera tras preparación y oráculos; mediana y rango de cinco posteriores. Orden fijo: no OS/PG frío ni causalidad de idioma/promoción. SQL cuenta execute, no CPU de PostgreSQL.144muestras completas; no percentiles95/99 de seis muestras.

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

## Atribución por etapas

Ejemplos ES, mediana de cinco posteriores, milisegundos. Las propiedades originales conservan ambas lenguas y todos los observadores. ModelIterable cronometra cada next real y excluye el trabajo del consumidor entre yield. Incluye SQL/materialización; contexto, validación y render contienen trabajo anidado. **No sumar columnas ni inferir porcentajes de CPU exclusiva.** Cero llamadas en una rama se registra explícitamente.

| Fase | Segmento | SQL execute | ModelIterable | Contexto | Validación binding | Render |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| organic | page1 | 40.119 | 70.071 | 76.187 | 11.991 | 37.774 |
| organic | last_page5 | 42.707 | 75.976 | 74.574 | 12.696 | 37.883 |
| organic | combined_page1 | 49.978 | 77.646 | 69.301 | 12.607 | 40.757 |
| organic | combined_last_page3 | 47.085 | 79.781 | 66.468 | 6.359 | 28.870 |
| organic | empty_combined | 12.126 | 23.403 | 20.570 | 0.000 | 22.964 |
| organic | detail | 26.435 | 40.121 | 41.868 | 0.680 | 3.635 |
| synthetic_promoted | page1 | 50.261 | 81.731 | 81.055 | 12.948 | 41.536 |
| synthetic_promoted | last_page5 | 35.631 | 61.634 | 65.571 | 11.826 | 40.325 |
| synthetic_promoted | combined_page1 | 45.338 | 69.972 | 73.572 | 12.304 | 40.181 |
| synthetic_promoted | combined_last_page3 | 55.473 | 71.071 | 62.943 | 6.261 | 37.433 |
| synthetic_promoted | empty_combined | 22.307 | 34.387 | 28.079 | 0.000 | 30.211 |
| synthetic_promoted | detail | 17.223 | 33.046 | 34.712 | 0.757 | 4.291 |

También se registran inicialización/describe/photo de PagePresentation, aliases de guards/validación, formularios y objetos construidos por modelo. Son observadores que delegan funciones reales; no se sustituye state_page ni se fuerza fallback. El máximo RSS high-water del proceso es276748KiB, bajo el límite diagnóstico1GiB; no memoria exclusiva por petición o de todos los servicios. El host compartido tiene afinidad de8CPU, sin equivalencia productiva o aislamiento exclusivo afirmados.

## Antes y después del bloque

No hay candidata de aplicación. N01C usaba100perfiles y otro observador; N04B usa120, preparación y observadores distintos. Se muestran las medidas disponibles, sin convertirlas en porcentaje de optimización.

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

## Fallos del instrumento y auditoría

Primera ejecución `20261025-205210-f0b7e1ab`:1FAIL,0ERROR/SKIP,61,180sJUnit; se conserva. La comprobación nueva leía entitlement.order de la instancia original en caché y encontraba pending. receive_event bloquea/recarga otra instancia y persiste paid. El instrumento corregido consulta la orden por su ID y exige paid/sintética:24lecturas persistidas paid frente a24objetos en caché pending. Ningún guard o dataset se redujo. Sólo cambió el diagnóstico y el registro de trabajo; la aplicación y el helper previo permanecen intactos.

Lint inicial I001 se corrigió antes de congelar. El primer auditor de cierre buscó la carga B16 en local-ci en vez de capacity-environment: error de localización preservado, corregido contra su original real antes del PASS. No se repitió esa carga ni pruebas por documentación.91,577s y61,180s son tiempos de QA, no de una petición.

Auditoría independiente: JUnit/144muestras/24segmentos/12coberturas/estados/pagos sintéticos y huellas contrastados; recursos etiquetados y temporal propios ausentes después de limpieza, Telegram terminal sent confirmado en ambas ejecuciones. La revisión nativa no identificó defecto material del oráculo/observadores; Codex verificó sus citas y fuentes. No se suman muestras de ejecuciones distintas para crear un único PASS.

## Decisión y límites residuales

La referencia actual delimita consulta, hidratación, validación, presentación y render, con32SQL orgánicas/33promocionadas para listados y22 para ficha. La consulta adicional con promoción representa autoridad/orden comercial en esta cohorte, no una regresión de un candidato. El coste de contexto/guards permanece visible; no se quita por rapidez. Con tiempos aceptables en alfa y sin un candidato justificado, se acepta **sin cambio necesario en este alcance**, sin forzar otro ciclo marginal de optimización.

Persisten límites explícitos: selección finita, ninguna representación nacional, páginas mayores o combinaciones no medidas sin latencia propia, tiempos inclusivos con observador y preparación previa, sin p95 nuevo, navegador, proveedor o apertura. Estos límites no se convierten en obligatorios diferidos para ocultar ausencia de evidencia: los escenarios seleccionados y la salida N04 están verificados. N05/N07/N11 mantienen sus obligaciones; MOD09 restante conserva su diferimiento expreso al final y B14/B15/B17 sus condiciones.

Siguiente bloque: N05, imágenes y experiencia de navegador, I06/I26; estudiar identidad de testigos Chromium/entrega antes de decidir nuevas mediciones.
