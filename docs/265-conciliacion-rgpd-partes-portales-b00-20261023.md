# B00-306 — RGPD por partes y portales institucionales

Fecha: 2026-10-23. Revisión documental histórica; sin implementación ni aceptación jurídica o funcional del producto.

B00-306: 223 de 295 fuentes únicas conciliadas; quedan 72. La primera captura RGPD se revisa mediante tres partes unidas sin huecos; la segunda reutiliza texto idéntico y todas sus diferencias se han leído. Se añaden dos portales institucionales. B00 sigue abierto; nueve de los 18 puntos de beta están cerrados.

## Alcance y unidad de cómputo

Se incorporan cuatro fuentes únicas sobre 923.037 caracteres capturados: dos capturas del mismo Reglamento 2016/679 y dos portales institucionales. La primera captura de 412.312 caracteres se dividió antes de delegar en tres intervalos contiguos. Cada revisor sólo declaró completa su parte; el principal verificó la unión, las huellas completas y parciales, las citas y los extremos antes de contabilizar la fuente una sola vez.

| Parte | Intervalo Unicode [inicio,fin) | Caracteres | Alcance |
| --- | --- | ---: | --- |
| 1 | [0,139775) | 139775 | Navegación, preámbulo, considerandos 1–120 y encabezado 121 |
| 2 | [139775,279984) | 140209 | Cuerpo del considerando 121, resto de considerandos y articulado hasta marcador 39.1c |
| 3 | [279984,412312) | 132328 | Continúa 39.1c, artículos 40–99, notas y navegación final |

El corte tras el encabezado 121 y el marcador 39.1c conserva explícitamente el contexto entre partes. Ninguna frontera deja un hueco ni supone un artículo íntegro donde sólo se leyó un encabezado. Los identificadores de fuente sin prefijo aportados por los revisores 2 y 3 se normalizaron al mismo source_id conocido, preservando sus valores originales en el informe de partes. No se crearon fuentes nuevas por esa normalización.

El revisor de la parte 3 y el de los portales recuperaron individualmente los segmentos afectados por salidas agregadas truncadas antes de declarar sus lecturas completas. Se conservan esas limitaciones de procedimiento. Cuatro lectores nativos trabajaron sin escribir archivos ni ejecutar ejemplos o destinos enlazados. No hubo nuevas invocaciones Claude V1; su consumo anterior permanece intacto.

El [registro de fuentes](evidencias/b00-current-source-review-ledger-20261023.json) pasa de 219 a 223 disposiciones únicas. La base219, plan previo, informes de partes, mapas, diferencias, propuestas y auditoría están en `artifacts/beta-promotion-fix-20261020/b00-306-*`. El verificador idempotente `verify_b00_306.py` comprueba las 295 capturas, tres partes, dos mapas y las citas, y sólo integra sobre la base o su resultado idéntico. El reemplazo del registro se realiza de forma atómica. Los originales no se modificaron.

## Segunda captura: reutilización exacta comprobada

La segunda captura contiene 414.178 caracteres. Se leyeron sus 87 líneas que no aparecen en la primera; todas son URL, con 8.580 caracteres incluyendo repeticiones. El resto del texto coincide exactamente y en el mismo orden al excluir sólo líneas de URL. La comparación es auxiliar: el control principal conserva todas las líneas, incluidas las URL, mediante mapas de emisiones y reutilización exactas con su primera procedencia. No se usa semejanza semántica ni se descartan líneas para acreditar cobertura.

Cada mapa tiene 5.245 entradas. La segunda captura aporta 53 primeras emisiones, 6.160 caracteres únicos; sus otras líneas apuntan a texto ya leído en la primera captura o a esas primeras emisiones. Se verificaron todas las referencias y que cada intervalo nuevo corresponde a una diferencia leída por el principal. El mapa de la primera captura se reconstruyó después de la lectura literal por partes; no se presenta como log original de esa lectura ni como prueba autónoma de comprensión.

Son dos identidades de captura de una misma norma, no autoridades independientes. Sus títulos contienen EN, pero el contenido jurídico es español y la navegación es principalmente inglesa. La clasificación se corrige en la capa de revisión, sin alterar títulos, textos o huellas originales.

## Contenido y límites normativos

Se leyeron los considerandos y el articulado con sus condiciones. La captura distingue finalidad y minimización, bases de licitud, condiciones del consentimiento, categorías especiales, derechos, responsabilidades, seguridad y mecanismos institucionales. Los considerandos no sustituyen el articulado; una cita breve tampoco sustituye sus excepciones o contexto.

Para B15 se conserva la separación ya acordada entre edad y términos, cookies y personalización, con preferencias expresas modificables y posibilidad de borrado y desactivación. El análisis documental no asigna una base del artículo 6, una condición del artículo 9 ni una necesidad concreta de EIPD a un catálogo de preferencias que sigue pendiente. La captura incluye datos de vida u orientación sexual en categorías especiales; no permite clasificar todos los posibles atributos físicos de forma uniforme ni resolver la cuestión por una aceptación genérica.

El artículo 32 capturado enumera cifrado junto a otras medidas dentro de una evaluación de seguridad adecuada al riesgo. Esto no convierte un objeto cifrado en cumplimiento demostrado ni decide claves, acceso, conservación, recuperación o almacenamiento de preferencias. Certificación, códigos, autoridades y mecanismos de transferencia descritos tampoco acreditan certificación, proveedor adecuado o transferencia autorizada del proyecto.

La página capturada indica que el acto ha cambiado y muestra una referencia a versión consolidada de 04/05/2016. Son metadatos capturados: no se ha verificado con ellos la actualidad del texto, una consolidación vigente o su aplicabilidad concreta. La fecha de aplicación de 2018 reproducida en el artículo 99 tampoco sustituye esa comprobación. Esta revisión no es una aceptación legal ni autoriza implementar B15.

## Disposiciones de las cuatro fuentes

| Fuente | Caracteres | Disposición |
| --- | ---: | --- |
| `source:9b7spltl0q7anf9xz0yf` — Reglamento - 2016/679 - EN - GDPR - EUR-Lex | 412312 | Texto jurídico español capturado del Reglamento 2016/679 con navegación principalmente inglesa, aunque el título incluye EN. Primera captura unida sin huecos desde tres partes; la segunda conserva idéntico texto no URL en el mismo orden y añade sólo URL. Se conservan dos procedencias de una misma norma, no autoridades independientes. Articulado, considerandos y notas leídos como captura histórica; no presume texto consolidado vigente ni cumplimiento, base jurídica, condición del artículo 9, EIPD, certificación o transferencias autorizadas para B15. Cifrado es parte de la evaluación de seguridad, no solución jurídica suficiente. |
| `source:x07n0s53tnie0qvlbxp8` — Reglamento (UE) 2016/679 (RGPD) - EUR-Lex | 414178 | Texto jurídico español capturado del Reglamento 2016/679 con navegación principalmente inglesa, aunque el título incluye EN. Primera captura unida sin huecos desde tres partes; la segunda conserva idéntico texto no URL en el mismo orden y añade sólo URL. Se conservan dos procedencias de una misma norma, no autoridades independientes. Articulado, considerandos y notas leídos como captura histórica; no presume texto consolidado vigente ni cumplimiento, base jurídica, condición del artículo 9, EIPD, certificación o transferencias autorizadas para B15. Cifrado es parte de la evaluación de seguridad, no solución jurídica suficiente. |
| `source:431a0t1dyvxb0w4a79z7` — Innovación y Tecnología | AEPD | 76167 | Portal temático AEPD con introducciones breves e índice amplio de guías, herramientas, informes y referencias. No reproduce íntegramente destinos. Su aviso de cookies técnicas describe el portal, no el proyecto. VALIDA-CRIPTO como enlace no acredita evaluación, certificación o ejecución. No adopta IA, herramientas, proveedores ni decide aplicabilidad de EIPD, cifrado o cookies. |
| `source:u09oolq9q5tku9xah8zq` — Agencia Tributaria: Inicio | 20380 | Portada AEAT y directorio de gestiones, campañas, declaraciones, identificación, categorías tributarias, censos, certificados, SII y SIF/VERI*FACTU. Descripciones generales y enlaces no determinan impuestos, altas, exenciones, plazos o fiscalidad de la beta gratuita. No acredita lectura de normas/manuales ni ejecución de simuladores o certificaciones del proyecto. |

## Portales y estado del proyecto

El portal Innovación y Tecnología de AEPD contiene introducciones e índices de recursos. Su aviso de cookies técnicas describe el propio portal; no evalúa las cookies del proyecto. La referencia a VALIDA-CRIPTO es un enlace, no una herramienta ejecutada o una certificación del cifrado existente. Los destinos de riesgo, EIPD, nube, biometría o IA no se consideran leídos por figurar en el índice, ni autorizan incorporar herramientas o proveedores.

La portada AEAT orienta hacia información y gestiones, sin resolver fiscalidad, altas, impuestos, exenciones, plazos o SIF/VERI*FACTU de la beta. No se realizaron gestiones, consultas autenticadas o simulaciones. La gratuidad del lanzamiento sigue siendo una decisión de alcance; no una conclusión fiscal derivada de una portada.

No se cambió el producto ni se ejecutaron pruebas funcionales. Se conservan B07 cerrado local, B15 opcional y los originales judiciales externos y límites de capturas pendientes. Quedan 72 fuentes: 56 de arquitectura, dos de privacidad, ocho legales, tres de moderación y tres comerciales. B00 y la aceptación global de beta siguen abiertos. El corte anterior se conserva en la [conciliación264](264-conciliacion-concurrencia-recursos-medios-b00-20261023.md).
