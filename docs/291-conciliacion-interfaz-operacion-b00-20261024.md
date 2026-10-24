# B00-332 — Interfaz SSR y herramientas de operación

Fecha: 2026-10-24. Conciliación histórica y contraste estático acotado.

B00-332: 274 de 295 fuentes únicas conciliadas; quedan 21 de arquitectura. Incorporadas interfaz SSR y las dos capturas de herramientas; contrastadas plantillas románticas, límites de representación y preparación operativa actual. Sin cambios de aplicación o pruebas, defecto nuevo demostrado ni nueva aceptación funcional. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Procedencia y disposición

Seis lectores nativos nuevos de sólo lectura, máximo tres simultáneos, cubrieron 529.075 caracteres en seis partes. Se emitieron y leyeron 47 intervalos contiguos de hasta 12.000 caracteres Unicode por salida; sin truncamientos declarados. Los informes persistidos son extractos seleccionados del principal, identificados como tales, no transcripciones completas. Cero nuevas invocaciones Claude V1; se conservan las ocho históricas y su consumo, sin estimación nativa.

| Captura | Fuente | Caracteres | Particiones |
| --- | --- | ---: | --- |
| Interfaz SSR y recursos | `source:uj4cq4iefqbo8ek4dk3p` | 175364 | [0,87682), [87682,175364) |
| Operacion y herramientas — parte 1/2 | `source:py71iabdof80ewvh4ugc` | 276817 | [0,92272), [92272,184544), [184544,276817) |
| Operacion y herramientas — parte 2/2 | `source:tcvw7mmpw8ocmwg4h8rm` | 76894 | [0,76894) |

Huellas completas verificadas:

- `source:uj4cq4iefqbo8ek4dk3p`: `3ed433aca5af96d6743548197132be4e55bd6d2ffd32cd75d232fd297e534a12`.
- `source:py71iabdof80ewvh4ugc`: `72a13bcc5e2bb9adf118701b9c30fc7a80c1bab184284b28563d7ac16454ad8a`.
- `source:tcvw7mmpw8ocmwg4h8rm`: `961a48b982b2fca75680cd149775bd69836cd541e78b4fe4c7a7769d53286c7d`.

Snapshot declarado 2026-10-11/base7e04016. La representación escapa identificadores y convierte o pierde fragmentos; no equivale a los bytes ejecutables actuales. Completar el texto capturado no acredita contenido ausente, imports, archivos referidos ni resultados de ejecución. El principal cotejó las seis huellas declaradas y doce citas con sus contextos/fronteras. El verificador realiza quince cotejos sobre esos doce intervalos, comprueba las tres uniones completas y revalida integridad de las 295 capturas.

El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) avanza de 271 a 274 disposiciones y de 24 a 21 pendientes. Base271 fijada por SHA256, escritura atómica y permisos conservados; no sobrescribir un ledger futuro con este verificador. Las particiones no se cuentan como fuentes adicionales. Tres lectores informaron un cwd antiguo, pero usaron la ruta absoluta designada; coincidieron huellas de parte/fuente y citas contra el original vigente. Se conserva su procedencia, sin atribuir nuevas lecturas o reparaciones. Artefactos `artifacts/beta-promotion-fix-20261020/b00-332-*`.

## Interfaz capturada y fuentes actuales

La captura de interfaz contiene CSS, scripts de recuperación de errores y geografía, README/dependencia HTMX y fragmentos SSR públicos/privados. El CSS expresa objetivos de foco, reflow, contraste y movimiento reducido; no acredita conformidad medida. El filtrado geográfico cliente mejora la interacción, pero no sustituye validación servidor. Foco de errores y conservación de selección no demuestran por sí solos accesibilidad completa.

Varias plantillas se reducen a cabeceras o directivas. El bloque capturado de base.html ocupa sólo 76 caracteres —incluida su cabecera— y conserva la directiva load, sin la estructura HTML. El principal lo cotejó con la plantilla actual completa, que contiene estructura, navegación y descripción romántica. Esa comparación está preservada y verificada: es pérdida de representación, no ausencia demostrada de interfaz. Tampoco se inventa el cuerpo de resultados, promociones, portabilidad, finalización o includes privados que la captura no conserva.

Los fragmentos sustantivos describen borradores, fotografías, moderación, apelaciones, comprobaciones simuladas, denuncias, recibos privados, supresión/restricciones/rectificación, revisión de destinatarios y copias. Los permisos de plantilla y la visibilidad de enlaces no acreditan autorización del endpoint. Preparación, revisión independiente, ejecución, cola, notificación, recepción y cierre conservan requisitos distintos. Inventariar no borra; reencolar medios no acredita borrado físico; desasociar medios compartidos no borra el archivo de un tercero. El historial y las evidencias retenidas no desaparecen por cambiar una pantalla.

La terminología profesional histórica —tarifas, categorías de servicios y portada anterior— no modifica el [contrato romántico](14-contrato-funcional-v1.md). En las plantillas actuales seleccionadas, el borrador se presenta como Mi perfil y el listado invita a buscar citas románticas; base describe perfiles personales adultos. No se declara auditada toda la UI por esos tres archivos ni se reabre como defecto actual el catálogo antiguo del snapshot. Las garantías de autorización, privacidad, cookies y elegibilidad deben probarse en sus entregas correspondientes.

## Herramientas, mediciones y límites

La primera captura reúne contabilidad de carga, transporte asíncrono, observadores de Celery/GC/publicación/recursos/consultas, compilación canónica y artefactos, controlador de entorno, documentación, orígenes retenidos, herramientas nativas, probes de workers y recuperación. La segunda incluye almacenamiento durable de recuperación, lanzadores aislados/CI/detach, diagnóstico de recursos fechado, comparación de workers, preparación de logs/Redis, población sintética y catálogo promocional.

La contabilidad separa programadas, emitidas, no emitidas, fallidas y pendientes, invalida un generador inadecuado y conserva errores/timeouts en la población de latencia. Contadores de espera muestreados no son duraciones de espera; tiempos SQL no son CPU PostgreSQL; RSS no suma memoria física y métricas compartidas no se atribuyen íntegramente al escenario. Observación de solapamiento GC no demuestra causalidad. Instrumentación y perfiles diagnósticos tienen coste propio y no sustituyen el escenario contractual combinado.

Los controladores y probes describen topologías aisladas, límites, manifiestos, versiones, servicio/worker/Beat, vigencia de autorización y limpieza. Son procedimientos con efectos potenciales; leerlos no los ejecuta ni autoriza sus comandos históricos. Readiness, fixture válido, diagnóstico, selección y entrega completa no son un único PASS. El runner actual de CI comprueba limpieza exacta y fuentes sin cambios antes de escribir resultado y enviar el aviso terminal; un recibo de Telegram debe comprobarse aparte. El lanzador detach conserva sesión/PID/tiempo de inicio/log propio, pero por sí solo no acredita notificación o reactivación automática del goal: esas garantías requieren el mecanismo completo documentado y recibos de cada ejecución.

El script run_post_cleanup_resource_checkpoint.py conserva rutas fijas del antiguo web_modelos, temporal0110 y referencias a recursos compartidos de aquel diagnóstico. Se identifica como procedimiento fechado, no como sustituto del CI aislado actual. No se ejecutó, importó ni reconectó a esos servicios. La autorización vigente de pruebas largas sigue AGENTS, con aviso previo, ejecución persistente, relevo y mecanismo AppServer verificado; esta lectura no acredita un nuevo ensayo de ese mecanismo.

Orígenes retenidos se ligan a expediente/inventario/cutoff y digests; un inventario de ciphertext suministrado no descubre todo el host ni demuestra asociación con el sujeto. Decodificación RDB, metadatos físicos y AUX mantienen límites propios; no se equiparan a revisión de divulgación o exhaustividad. Capturar logs Compose actuales no incluye contenedores eliminados, backups o todas las fuentes históricas. El almacén durable local con checkpoint separado no constituye backup externo independiente ni prueba de RPO/RTO. Los campos simulados de edad/teléfono e identificadores de broker no acreditan proveedor real.

## Contraste actual, grafo y continuación

Quince archivos actuales y treinta literales: tres plantillas SSR, dos scripts de navegador y diez herramientas/lanzadores. Se contrastaron estructura/texto romántico y formularios, recuperación de errores, geografía, sesión separada y log nuevo del detach, propietario de aviso terminal, limpieza/fuentes CI, diagnóstico fechado, preparación Redis privada y acotada, checkpoint separado, herramientas nativas fijadas y separación entre readiness y aceptación de capacidad. La selección no es auditoría completa de todas las herramientas o controles de seguridad.

Sin defecto nuevo demostrado, cambios de aplicación/pruebas o nueva ejecución funcional. Las correctivas anteriores y B07 conservan sus cortes; no se repiten baterías sin cambio, fallo o incertidumbre que lo justifique. Grafo385 revalidado antes del análisis e integración semántica dirigida386 al incorporar esta conciliación. Sin nuevo AST global, semántica exhaustiva o HTML global; límites de self-loops y referencias externas preservados.

Quedan 21 fuentes, 19,529,609 caracteres, principalmente referencias técnicas y grandes grafos. Conteo de fuentes no equivale a porcentaje de esfuerzo. B00 abierto y nueve de18puntos beta cerrados; B15 opcional mantiene lo acordado sobre cookies y preferencias privadas cifradas, con diseño y garantías pendientes. Sin publicación, proveedores contratados, gasto o datos reales. Corte previo: [conciliación290](290-conciliacion-pruebas-portabilidad-b00-20261024.md).
