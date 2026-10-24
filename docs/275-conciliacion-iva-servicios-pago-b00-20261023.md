# B00-316 — IVA y servicios de pago: condiciones y límite de captura

Fecha: 2026-10-23. Conciliación documental de capturas históricas, sin aceptación fiscal, jurídica, comercial o global de beta.

B00-316: 239 de 295 fuentes únicas conciliadas; quedan 56, todas de arquitectura. Las 18 capturas comerciales tienen disposición textual. Se incorporan IVA y servicios de pago en España; la captura de IVA termina en el artículo166 y no acredita los cuerpos posteriores. Sin dictamen vigente ni cobros. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura comprobada

Nueve lectores nativos readonly cubrieron1.162.742caracteres, mediante partes fijadas previamente y un máximo de tres lectores simultáneos. Los informes completos se conservan con sus declaraciones de alcance, hashes, citas y límites. No hubo rondas de reparación ni truncamientos declarados en sus salidas literales. Las partes no se cuentan como fuentes independientes.

| Captura | Partes | Intervalos Unicode [inicio,fin) |
| --- | ---: | --- |
| RDL19/2018, servicios de pago | 3 | [0,132274), [132274,264548), [264548,396822) |
| Ley37/1992, IVA | 6 | [0,127653), [127653,255306), [255306,382960), [382960,510613), [510613,638266), [638266,765920) |

Los lectores emitieron104salidas individuales contiguas, de hasta12.000caracteres cada una. El principal inspeccionó fronteras, inicio y cola de ambas capturas, además de dieciocho citas con sus contextos. El verificador realizó veinte cotejos de cita en esos dieciocho intervalos distintos, comprobó uniones, hashes declarados y las295capturas inventariadas.

Plan, protocolo, nueve informes íntegros, propuestas, contextos, límite y auditoría están en `artifacts/beta-promotion-fix-20261020/b00-316-*`. El verificador deriva del corte314 mediante un diff guardado y revisado; sólo integra sobre la base237 fijada por hash o un resultado idéntico, con reemplazo atómico y permisos preservados. No se convierte el parseo o un hash en evidencia de lectura semántica. El [ledger vigente](evidencias/b00-current-source-review-ledger-20261023.json) pasa de237a239disposiciones y de58a56pendientes.

## Servicios de pago en España

Fuente `source:l5oe94ne9va3d4vcwzm5`,396.822caracteres, SHA-256 `ba4812557ca9fef2aaef7c343f6d3767e847f029025f5b9e357034abb988ee61`. Es una captura informativa BOE con actualización indicada de28/12/2023. Contiene navegación, preámbulo, articulado, disposiciones adicionales y transitorias, derogatoria y finales, y un cierre normativo e institucional reconocible. No se acredita autenticación externa o vigencia actual por la advertencia informativa y el cierre de la captura.

La norma capturada distingue prestación profesional de servicios de pago, actividades reservadas, exclusiones y categorías de proveedores. Las exclusiones de soporte técnico, agente comercial o red limitada conservan sus condiciones; no se deducen por llamar al proyecto portal o intermediario. La exclusión técnica no alcanza automáticamente iniciación de pagos o información sobre cuentas. Exenciones de ciertos proveedores no eliminan registro u otras obligaciones que correspondan.

Capital, salvaguardia, autorización, agentes, externalización, conservación prudencial, supervisión y reporte de incidentes de proveedores no se trasladan al portal por vender visibilidad propia. Tampoco se asume que un beneficiario comercial carezca de obligaciones: la captura contempla reglas del beneficiario sobre gastos por instrumento, ventajas, autenticación y determinados pagos entre profesionales. Si se concreta monetización, habrá que verificar sus hechos, sujetos, ámbito, redacción vigente y relación contractual con el proveedor.

Consentimiento, información, modificaciones del contrato marco, ejecución, prueba, responsabilidad, devoluciones y reclamaciones tienen condiciones y sujetos distintos. El contrato marco de servicios de pago no se identifica automáticamente con el contrato de publicar o promocionar un perfil. Los transitorios históricos no autorizan un negocio nuevo, y las modificaciones de normas sobre instituciones de inversión, dinero electrónico o mercados no convierten Top en producto financiero.

Se conserva la preparación comercial del [contrato14](14-contrato-funcional-v1.md), sin proveedor elegido, custodia, pagos entre usuarios, recurrencia, recargos o cobros reales. Una captura revisada no acredita aceptación de la actividad por una pasarela ni una integración realizada. La lectura complementa la [PSD2 capturada](274-conciliacion-psd2-b00-20261023.md), sin reemplazar la revisión aplicable cuando exista un flujo de pago concreto.

## IVA: clasificación condicionada

Fuente `source:c83d52gwn69xopcqgaya`,765.920caracteres, SHA-256 `746aef918f9967a918a651eda0d630a0df3c87df84b4ba756217c5bea9b04141`. Mezcla texto articulado seleccionado, exposición histórica, índices, reformas, notas y enlaces. No se adoptan como parámetros fiscales actuales los importes o tipos del preámbulo, el historial o las redacciones de la captura.

Ámbito territorial, hecho imponible, empresario o profesional, no sujeción y exención son cuestiones separadas. Gratuidad del servicio no resuelve por sí sola todos los hechos fiscales posibles; la captura conserva salvedades, operaciones asimiladas y contraprestaciones de terceros. Las exenciones de sectores, bienes o interfaces de entrega de bienes tienen supuestos propios: no se trasladan a perfiles o promociones por analogía ni por ser una web.

La localización de prestaciones depende de la naturaleza efectiva del servicio y circunstancias del prestador y destinatario. Comunicación por correo electrónico no basta por sí sola para clasificar un servicio como electrónico. Los umbrales y opciones descritos pertenecen a operaciones delimitadas; no son exenciones universales. Devengo, anticipos, base, modificaciones, sujeto pasivo, inversión, repercusión y tipo no se confunden. No se fija aquí tipo, deuda, régimen o conclusión fiscal individual para el proyecto.

Deducción, gastos preparatorios, afectación, prueba documental, prorrata, regularización y devolución mantienen sus requisitos. Los regímenes especiales de agricultura, usados, oro, viajes, recargo, grupo, caja, Unión u otros conservan sujetos, operaciones y opciones específicas; no se seleccionan para el portal. Los plazos de registros de ciertos regímenes o de entidades no se convierten en retención general de perfiles, imágenes o preferencias.

## Límite real de la captura IVA

La captura disponible no contiene toda la Ley IVA. El último encabezado con cuerpo es artículo166, «Obligaciones contables», en757614; su cuerpo incluye los apartados uno a tres. La última nota editorial termina incompleta en758592, con «de la citada». Desde758593hasta765920 sólo hay espacios, URLs y selectores de fecha:177líneas no vacías, clasificadas íntegramente por el verificador.

El principal y el último lector confirmaron ese límite. Se conserva `b00-316-capture-limit.json`, su contexto y el hash de la cola `8bd67f49b83460e54d3fb3da0d6a9b994acb657a67b82f2d1628348f7f395580`, además de `capture_limits_316` en el ledger. No se acredita lectura de los cuerpos posteriores al166, disposiciones o anexo ausentes como cuerpos, ni de la continuación de la última nota. Índice, enlaces y selectores no los sustituyen. La causa de la omisión no está determinada.

## Resultado y continuación

Las18capturas del cuaderno comercial tienen disposición textual; no significa que todas las normas originales estén completas o vigentes, que exista dictamen fiscal o que el comercio esté listo. El cierre de ese cuaderno conserva explícitamente el límite de IVA y los límites legales anteriores: cuerpos penales ausentes, originales judiciales, discordancia de LO10/2022 y corroboración parcial del Reglamento IA. También se conserva el límite HTMX.

Quedan56capturas de arquitectura,28.924.086caracteres. Su volumen supera ampliamente el de estas dos fuentes; el porcentaje de fuentes revisadas no mide porcentaje de trabajo terminado. Siguen pendientes snapshots de código, contratos, pruebas y grandes grafos. Parseo, inventario, AST o proyecciones preparadas no acreditan por sí solos lectura semántica.

B00 sigue abierto. B07 conserva su cierre local por acta16, sin nueva carga. B15 continúa opcional, con catálogo, persistencia y condiciones legales pendientes. Sin cambios de aplicación o pruebas funcionales en este corte; sólo verificaciones documentales y del grafo. Nueve lectores nativos, cero nuevas invocaciones ClaudeV1, consumo histórico preservado y sin estimación de tokens nativos. Grafo363 revalidado al inicio y semántica dirigida364 al integrar; sin nueva extracción AST, semántica exhaustiva o HTML global. Corte anterior: [conciliación274](274-conciliacion-psd2-b00-20261023.md).
