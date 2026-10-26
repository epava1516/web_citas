# N08B — referencia aceptada; N08C pendiente de repetir un caso

Aceptación local parcial de [N08B/413](413-n08-b-prerregistro-comercial-20261026.md), sin cambio de aplicación ni mejora temporal atribuida. N08 sigue abierto, 7/13 bloques obligatorios aceptados. El objetivo completo continúa activo.

## Evidencia y alcance

Ejecución `20261026-030555-20d5ac97`: **3 PASS y 1 FAIL**, cero errores o skips, 82,271 segundos JUnit. No es una batería completamente verde. Las 1.759 huellas congeladas se mantuvieron durante la ejecución: 1.756 del runner y tres documentos verificados aparte. PostgreSQL y Redis desechables reales; limpieza y aviso terminal Telegram `delivery: sent` comprobados.

Los tres casos comerciales válidos aportan 396 GET medidos en 66 segmentos, 30 GET negativos y 10 POST distintos del catálogo: **436 llamadas propias**, coincidentes con las 436 observadas globalmente en esta ejecución; no sumarlas de nuevo. Contadores independientes `execute_wrapper` coinciden para cada ruta/estado/ordinal con el observador global. La auditoría comprueba los originales JUnit, selección, fuente congelada, ausencia de modificaciones de dominio en GET, controles, recuentos y limpieza.

Se observaron todas las páginas nativas de historial25 y catálogo/versiones50 para las cohortes prerregistradas, opciones sin paginar separadas del historial, ES y EN, PK y orden exactos, comprador ajeno excluido, sesiones/MFA/permisos y revocación de permiso. Las dos secuencias nativas del catálogo produjeron ocho auditorías en total; repetir la publicación no añadió auditoría ni alteró el contenido publicado. Ninguna compra, pago ni concesión se deriva de editar o publicar el catálogo. Los nueve modelos comerciales se compararon por todos sus campos escalares fuera de los relojes; sólo se exportaron resúmenes. Las cohortes de pedidos son preparación sintética, no cien compras nativas.

Los 77 testigos anteriores de 16 módulos mantienen sus fuentes y alcance histórico; la cadena de 1.507 fuentes ejecutables conserva 1.498 idénticas y las nueve variantes ya aceptadas. Diez de esos originales se ejecutaron dentro de los 13 PASS de N08A2; no son 87 casos nuevos. No se repiten por documentación o skills ni se presenta la batería histórica con fallos/skips como una ejecución completamente verde.

## Tabla de referencia y decisión

Milisegundos de pared del Client, mediana de las cinco observaciones posteriores a la primera. Cohorte100, primera página cuando hay paginación; detalle y borradores corresponden a un objeto, no a cien objetos renderizados. El JSON conserva primera observación, rango, CPU del proceso, bytes y todos los 66 segmentos, incluidas las demás páginas/cohortes. CPU no incluye PostgreSQL; no es latencia de red, navegador o p95.

| Acción y alcance | ES actual (ms) | EN actual (ms) | SQL por petición | Después de otro candidato |
| --- | ---: | ---: | ---: | --- |
| Historial100, página1 de25 | 58,935 | 42,734 | 9 | No medido |
| Detalle de un pedido propio | 24,941 | 15,778 | 6 | No medido |
| Opciones:100 anuncios, un producto | 53,137 | 42,648 | 8 | No medido |
| Opciones:100 productos, un anuncio | 44,543 | 52,704 | 8 | No medido |
| Catálogo100, página1 de50 | 27,467 | 26,870 | 9 | No medido |
| Versiones100, página1 de50 | 53,613 | 40,944 | 10 | No medido |
| Edición de un borrador | 27,502 | 25,224 | 8 | No medido |
| Vista previa de un borrador | 21,177 | 27,568 | 8 | No medido |

No hay par antes/después de aplicación en este frente y no se calcula un porcentaje de mejora. Se conserva el comportamiento actual y se avanza: no aparece una justificación clara para prolongar N08B con optimizaciones marginales, conforme a la decisión del usuario sobre tiempos alfa aceptables. Las ganancias pareadas de favoritos/sitemap permanecen documentadas exclusivamente en [N08A2/412](412-n08-a2-resultado-contraste-por-lotes-20261026.md).

## N08C: fallo del instrumento y corrección prerregistrada

El cuarto caso falló en 1,295 segundos, antes de solicitar `directory` y sin arrancar worker o Beat: comprobaba `celery_app.conf.task_always_eager` antes de que `photo_environment` configurase el modo de preparación. Las fuentes verificadas son `tests/test_discovery.py:16` (solicita la fixture) y `tests/test_photos.py:43` (habilita eager). La inicialización nativa `setup(request, settings)` solicita esa cadena.

Corrección mínima del instrumento: mover la misma aserción después de `setup`, conservando fixture, datos, guardas, modo de preparación, rol, procesos, entrada nativa de60 segundos y oráculos de [N08C/414](414-n08-c-prerregistro-autosubida-nativa-20261026.md). No cambia aplicación ni servicios y no convierte eager en verificación real. El archivo original, el fallo, la congelación y la auditoría de los tres casos válidos quedan preservados.

Siguiente ejecución autorizada: **sólo** `tests/test_promotion_worker_cadence_reference.py`, un caso. Antes: lint acotado, AST de su corrección y semántica de este resultado/seguimiento, validación del grafo y nueva congelación. Conservar sin repetición los tres casos comerciales válidos. La repetición deberá acreditar por sí misma worker restringido, dos ticks Beat nativos60s y limpieza; el primer fallo no acredita ninguna de esas propiedades. N08 sólo se cerrará tras esa evidencia y la conciliación completa de sus 17 identificadores.

## Reproducción conservada

Auditoría local: `artifacts/recorridos-n08-b-20261026/reference-b-audit.json`; contiene las referencias actuales y el veredicto parcial explícito. Prerregistro, propuesta nativa, fuentes originales/corregidas, huellas y recibos permanecen en los directorios de evidencia N08B y N08C. Su paquete versionado se conciliará al cerrar el resultado final; este documento no afirma que ya se haya archivado. No beta, proveedor, pago real ni cambio de contrato.
