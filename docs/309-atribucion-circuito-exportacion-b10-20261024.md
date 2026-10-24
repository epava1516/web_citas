# B10-348 — Atribución del circuito de exportación

B10 continúa abierto tras308; se mantiene12/18puntos cerrados. Se prerregistra una medición del circuito nativo actual con10/100revisiones retenidas sintéticas y descripciones5400caracteres. No sustituye el extremo original1500revisiones/16MiBJSON/64MiBoriginales/doscasos ni convierte su FAIL en PASS.

## Instrumento y límites previos

El diagnóstico tests/test_export_flow_stage_cost.py reutiliza los ayudantes del cierre nativo ya existente: elegibilidad/selección, cobertura e inspección de todas las páginas mediante lotes nativos, generación, preparación/inspección/aprobación final, cierre y replay, descarga de manifiesto, original WebP y ZIP. Comprueba una sola respuesta/cierre/aviso, versiones y contenido binario íntegro contra manifiesto y ZIP; las respuestas privadas conservan no-store. La identidad y procedencia son fixtures simuladas, no proveedores ni acreditación jurídica. La historia queda mayormente excluida de campos entregados: no afirmar transporte del JSON de esa historia o carga binaria masiva.

Se envuelven funciones reales por identidad en módulos apps.safety ya importados, conservando alias; importaciones posteriores observan el módulo actualizado. Se registran cantidad de alias, llamadas, tiempo transcurrido/CPU de hilo y consultas para source_copy, canonical, seal/unsealJSON e image_contents, además de fases completas. Los wrappers siempre delegan al cuerpo original: no inventan veredictos, fuente, criptografía o autoridad. Los tiempos y SQL son inclusivos y anidados, no aditivos; no son percentiles ni coste de producción. No registrar parámetros SQL, contenido de copia, identificadores, credenciales o sujetos.

Selección prevista: dos diagnósticos completos y cuatro controles existentes de cierre con aprobación/rechazo y perfil/cuenta. PostgreSQL/Redis propios, un worker, timeout1200s y RSS del proceso Python menor de1GiB como topes del instrumento; no presupuesto efectivo del sistema completo ni nuevo SLO. Sin cambios de aplicación, dependencias o controles de autoridad.

Primero validar fuentes congeladas, JUnit, limpieza de servicios/directorio/PID y recibo Telegram. Localizar coste antes de plantear un cambio; conservar fallos si los hay. No ampliar cargas o adoptar tecnología por estos datos solos.

## Límite descubierto y corrección de sonda

Primera ejecución20261024-081145-a940c7e2:6PASS/0omisiones,177.830sJUnit,1720fuentes y637rutas de producto/estáticos idénticas al corte anterior; limpieza y Telegram verificados. La sonda image_contents sólo medía creación del generador, no su iteración: sus tiempos/SQL no representan lectura. Se conserva el testigo completo y se cambia únicamente esa sonda al lector real _read_image_blob, manteniendo tamaños, selección y topes; comparación posterior pendiente.

## Resultado corregido

Ejecución corregida20261024-081739-bc754999:6PASS/0FAIL/0ERROR/0SKIP,184.852sJUnit,1720fuentes congeladas verificadas y637rutas de producto/estáticos idénticas al diagnóstico anterior. Limpieza de contenedores/directorio/PID y Telegram confirmados. No se modifica la aplicación ni se acepta B10 completo.

[Auditoría corregida](evidencias/b10-closed-export-flow-attribution-20261024.json) y [primer instrumento con su límite](evidencias/b10-first-export-flow-instrument-limit-20261024.json).

| Observación inclusiva | 10 revisiones | 100 revisiones |
|---|---:|---:|
| Recorrido observado | 19,342937s | 51,887883s |
| SQL total | 7374 | 18110 |
| Páginas de cobertura auditadas | 21 | 111 |
| Tiempo de esas páginas | 5,379485s | 31,458253s |
| SQL de esas páginas | 2226 | 11766 |
| source_copy llamadas / SQL | 57 / 893 | 79 / 1245 |
| source_copy tiempo | 2,500604s | 4,735481s |
| canonical() llamadas / tiempo | 1148 / 0,074211s | 4411 / 0,311020s |
| seal JSON llamadas / tiempo | 96 / 0,027543s | 295 / 0,077508s |
| unseal JSON llamadas / tiempo | 930 / 0,145750s | 3342 / 0,598155s |
| Lecturas WebP / tiempo | 42 / 0,007510s | 132 / 0,024985s |
| Generación cubierta | 1,905957s | 2,502218s |
| Preparación final | 0,480420s | 0,698696s |
| Cierre | 0,756134s | 0,943074s |
| Descarga manifiesto / WebP / ZIP | 0,374988 / 0,360135 / 0,340381s | 0,388452 / 0,430794 / 0,397594s |

En100revisiones, cobertura111páginas/11766SQL/31,458253s frente a51,887883s del recorrido instrumentado; source_copy79llamadas/1245SQL/4,735481s. La sonda canonical() observa4411llamadas/0,311020s, sin abarcar todas las llamadas directas a canonical_bytes() u otros serializadores. _read_image_blob observa132lecturas/0,024985s del WebP pequeño local, no almacenamiento remoto ni binario masivo.

Los dos cortes conservan las mismas llamadas y SQL de todas las sondas comunes y el mismo SQL total por tamaño; la sonda de generador se retira, no se compara su tiempo con el del lector. No es una mejora causal: no hubo cambio de aplicación y los tiempos varían entre ejecuciones. Ambos cortes verifican contenido íntegro y controles de aprobación/rechazo; el WebP entregado ocupa10516bytes y su ZIP10696bytes. El RSS máximo acumulado es293296/317776KiB y no equivale al pico de una fase o del sistema completo.

## Decisión y continuación

El componente observado con mayor tiempo dentro de este recorrido es la inspección página a página de cobertura; mantiene106consultas por página en ambos tamaños. Corresponde estudiar su composición antes de proponer un cambio. No se prueba que esas consultas sean redundantes: inspect_page conserva autoridad actual, revisión independiente, fuente y proof; inspection_source toma un snapshot y exige comprobación fresca a la salida. No eliminar auditorías, ampliar la vida de un cache ni compartir autoridad entre peticiones para reducir el contador.

B10 sigue abierto para justificar el extremo de similitud y conciliar la deuda separada de exportación con la salida de etapa3. El escenario original MOD09 y sus objetivos2s/5s permanecen; estas llamadas con10/100revisiones y entrega pequeña no lo sustituyen. No elevar prioridad sin impacto beta demostrado. La propuesta de índice sigue sin tecnología adoptada. Se mantienen12/18puntos cerrados; objetivo completo activo.
