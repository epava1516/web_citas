# B00-314 — Propiedad intelectual y límites de la captura penal

Fecha: 2026-10-23. Conciliación documental de capturas, sin dictamen vigente o aceptación global de beta.

B00-314: 236 de 295 fuentes únicas conciliadas; quedan 59. Las 23 capturas del cuaderno legal tienen disposición textual. Se completan las capturas de propiedad intelectual y Código Penal, pero esta última no contiene los cuerpos posteriores al artículo 340 quinquies. No se acredita lectura del Código completo ni cumplimiento jurídico. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura de las capturas

Diez lectores nativos de sólo lectura cubrieron 1.324.398 caracteres mediante partes fijadas antes de delegar, con un máximo de tres lectores simultáneos. Propiedad intelectual tiene cuatro partes y la captura penal seis. Cada una conserva hashes completos/parciales y alcance declarado. Un lector realizó además una ronda de corrección de una descripción de frontera, sin lectura ni crédito adicionales.

| Fuente y parte | Intervalo Unicode [inicio,fin) | Caracteres |
| --- | --- | ---: |
| LPI — 1 | [0,133453) | 133453 |
| LPI — 2 | [133453,266963) | 133510 |
| LPI — 3 | [266963,400301) | 133338 |
| LPI — 4 | [400301,533946) | 133645 |
| Captura penal — 1 | [0,131988) | 131988 |
| Captura penal — 2 | [131988,263808) | 131820 |
| Captura penal — 3 | [263808,395992) | 132184 |
| Captura penal — 4 | [395992,527957) | 131965 |
| Captura penal — 5 | [527957,659994) | 132037 |
| Captura penal — 6 | [659994,790452) | 130458 |

Cada parte LPI se emitió en doce salidas literales; las penales, en once o doce según longitud, contiguas y de hasta 12.000 caracteres individualmente. No se declararon truncamientos de esas salidas. Eso no significa que la captura penal contenga toda la norma original.

El principal comprobó las uniones sin huecos, hashes, veintidós cotejos de cita en veinte intervalos distintos y sus contextos. Las 295 capturas se verificaron contra sus hashes y longitudes de inventario. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de 234 a 236 disposiciones de captura, con 59 pendientes. Ninguna parte se cuenta como fuente separada.

Plan, protocolo, informes íntegros, propuesta, auditoría y contextos están en `artifacts/beta-promotion-fix-20261020/b00-314-*`. `verify_b00_314.py` sólo integra sobre su base234 o resultado idéntico, mediante reemplazo atómico con permisos preservados. Comprueba también la reparación y el límite de captura. No se acredita revisión visual, lectura de enlaces, versiones alternativas o vigencia normativa actual.

## Propiedad intelectual: derechos y supuestos separados

Fuente `source:92o9d7zwbrxi0gp8i5qc`, 533.946 caracteres en español. Incluye navegación, preámbulo y texto refundido, derechos de autor y afines, contratos, programas, fotografías, bases de datos, protección, gestión colectiva, ámbitos, disposiciones y anexo. Se distinguen cuerpo principal, notas editoriales, derogaciones y transitorios.

La captura separa autoría, derechos morales y modalidades de explotación. Propiedad de un soporte, autorización para publicar, derechos sobre la fotografía y derecho de imagen no se sustituyen entre sí. La subida de una imagen o su hash no prueban autoría ni una licencia suficiente. Tampoco se trasladan al portal las presunciones de contratos audiovisuales, laborales, editoriales o de representación sin sus hechos específicos.

La protección de la estructura de una base de datos, los derechos sobre su contenido y el derecho del fabricante por inversión conservan ámbitos propios. Las excepciones de copia privada, usuario legítimo, accesibilidad, obras huérfanas o interoperabilidad tienen condiciones y beneficiarios: no autorizan por sí solas la copia de perfiles o fotografías, crawling o reutilización pública. La salvaguardia de datos personales y otros regímenes permanece separada.

Los requisitos de entidades de gestión, operadores independientes, autorizaciones musicales y reparto no son requisitos generales del portal. La retirada civil o administrativa y sus procedimientos tampoco equivalen a una calificación penal automática. Legitimación, conocimiento, autorización, proporcionalidad, funciones de autoridad y condiciones de medidas tecnológicas se mantienen con su contexto. Sus plazos no fijan conservación de perfiles o evidencias de la aplicación.

El [contrato14](14-contrato-funcional-v1.md) y el [apartado legal](15-apartado-legal-publico.md) ya separan autorización de representación, contenido, imágenes y licencia necesaria. La lectura no da por verificadas las autorizaciones de personas reales ni incorpora usos publicitarios externos o entrenamiento de modelos.

## Corrección de la frontera del artículo 183

La descripción inicial de la parte LPI3 afirmaba que el artículo 183 terminaba antes de la frontera400301. El principal leyó el contexto continuo y comprobó que después siguen obligaciones sobre repertorio musical, una lista y otro párrafo antes de las notas editoriales. El lector rectificó expresamente: el artículo queda parcial en la parte3 y continúa en la4.

Se conservan el informe inicial y el corregido, sus hashes y `b00-314-boundary-repair.json`. Los rangos, hashes de fuente/parte, intervalos y citas son idénticos; no hubo hueco de lectura ni una fuente nueva. Se rechazó la afirmación de artículo completo, no se alteró silenciosamente el informe. El verificador comprueba esa invariancia y el contexto literal. La ronda de corrección no se presenta como una nueva lectura.

## Código Penal: condiciones, competencias y límite real

Fuente `source:l7jsbeytuexnajsscwgj`, 790.452 caracteres. La captura incluye navegación y exposición de motivos, reglas generales, responsabilidad personal y de personas jurídicas bajo sus condiciones, penas, medidas, responsabilidad civil, decomiso, extinción y tipos sucesivos. Se conservan sus elementos, sujetos, fines, conocimiento, medios, perjuicio y garantías; denuncia, coincidencia visual o uso del portal no acreditan por sí solos delito.

Las materias leídas abarcan vida e integridad, libertad, trata, libertad sexual, intimidad e imagen, honor, familia, patrimonio, seguridad informática, propiedad intelectual e industrial, mercado, obligaciones fiscales y laborales, ambiente y animales. No se convierten en categorías del perfil, vigilancia, biometría o retenciones automáticas. La responsabilidad personal, la jurídica condicionada y la civil no se confunden. Medidas judiciales y policiales conservan autoridad y procedimiento.

Los supuestos de trata, imágenes no consentidas, perfiles falsos y contenidos especialmente definidos mantienen todas sus condiciones. En los preceptos de propiedad intelectual, beneficio directo o indirecto, autorización, perjuicio y facilitación activa no neutral no se eliminan por una etiqueta ni se deducen automáticamente de un listado. No se califica penalmente al operador o a los usuarios, ni se presenta la gratuidad como inmunidad.

**La captura no contiene todo el Código Penal.** El último encabezado sustantivo observado es artículo340 quinquies, en posición775048. Después aparecen títuloXVII y capítuloI; desde776271 hasta790452 sólo hay URLs y selectores de fecha: 434 líneas no vacías, clasificadas íntegramente. No constan allí los cuerpos posteriores al340 quinquies. El índice y los enlaces no acreditan lectura de los artículos341 y siguientes.

El principal y el último lector confirmaron el límite. Se conserva `b00-314-capture-limit.json`, el hash de esa cola y `capture_limits_314` en el ledger. La causa de la omisión no se ha determinado; no se culpa a un transporte o parser sin evidencia. Se han leído todos los caracteres de la captura disponible, pero el texto sustantivo posterior permanece sin revisar. No se declara lectura integral del original.

## Resultado y continuación

Las 23 capturas del cuaderno legal tienen disposición documental, incluidas conversaciones, material auxiliar y límites propios. Son fuentes compartidas o revisadas en distintos incrementos: este corte añade sólo dos. No equivale a que todas las normas originales, jurisprudencia y correcciones estén completas o autenticadas, ni a una evaluación jurídica de la actividad real.

Quedan 56 fuentes de arquitectura y tres comerciales en el inventario capturado. Además siguen explícitos los límites de originales o textos ausentes, incluidos éste, HTMX y los originales judiciales anteriores. El cierre documental del cuaderno no elimina esos pendientes ni cierra B00, B14, B16, B17 o gates productivos.

Se conserva el producto romántico, el lanzamiento gratuito, promociones preparadas y B15 opcional. No se añaden funciones, tratamientos, proveedores o acciones externas. Sin cambios de aplicación o pruebas funcionales; sólo comprobaciones documentales y del grafo. Diez lectores nativos y una ronda de corrección; sin nuevas invocaciones ClaudeV1 y con su consumo histórico preservado. Corte anterior: [conciliación272](272-conciliacion-consumidores-libertad-sexual-b00-20261023.md).
