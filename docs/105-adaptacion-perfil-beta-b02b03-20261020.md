# Adaptación del perfil romántico — B02–B03

Fecha: 2026-10-20. Estado: B02–B03 aceptados técnicamente en local por [acta12](actas/12-beta-b02b03-aceptacion-local-20261020.md) y candidata común192PASS/0FAIL/0SKIP. Este incremento aplica el [contrato funcional1.1](14-contrato-funcional-v1.md) y AD01–05/AD09–10 de la [matriz](104-consolidacion-contrato-beta-b00b01-20261020.md). No acepta beta, apertura o proveedores reales.

## Comportamiento implementado

Cada revisión tiene `content_contract`. La migración0023 marca las existentes `legacy-professional-v1`; las nuevas usan `romantic-v1`. El catálogo `romantic-dating` tiene identidad propia, sin renombrar IDs antiguos. Las categorías profesionales conocidas y sus servicios quedan inactivos. Se invalida la elegibilidad almacenada para aplicar las nuevas reglas.

El anunciante accede a «Mi perfil», conserva ubicación, texto, contactos autorizados, fotos y revisión. El formulario no solicita categorías/servicios profesionales, recepción/desplazamiento ni tarifas. Los campos profesionales enviados manualmente se rechazan. La búsqueda devuelve400 ante filtros profesionales antiguos; no los ignora ampliando silenciosamente los resultados. Ficha y tarjetas presentan el perfil romántico.

El panel y la gestión de publicación incorporan estados y orientación ES–EN. Los cambios en borrador/revisión se muestran separados de la publicación aprobada. Para afirmar visibilidad se consulta la guarda pública vigente, no sólo el estado almacenado: caducidad o consentimiento revocado deben mostrarse como no visibles. Se conservan permisos, acciones y versiones de concurrencia. Verificación específica024215:41PASS, incluyendo20casos de estado, ciclo de vida, teclado ES–EN390/1280 y recorridos de revisión.

La validación compartida de envío, moderación y exposición rechaza contrato desconocido/heredado, catálogo incompatible o datos profesionales residuales. La versión de reglas incluye el nuevo módulo de política. Se mantienen autorización por persona, representación, consentimientos, edad, contacto, fotos y revisión aprobada; el panel particular no elimina las herramientas autorizadas de agencia.

El tipo de perfil pasa a ser voluntario: valor vacío para nuevas revisiones, opción «Sin indicar» y ninguna asignación automática a mujer. La migración0024 cambia sólo el estado del campo; conserva todos los valores existentes. La presentación admite ausencia de tipo y los filtros distinguen ausencia de una declaración concreta. El seed usa una declaración sintética explícita. Corrección verificada por025250:27PASS/0FAIL/0SKIP, incluidos migración/reversión, publicación sin tipo, filtros, paridad y navegador.

La etiqueta trans se separa mediante `show_trans_label`, opcional y no seleccionada por defecto (migración0025). No modifica el tipo declarado ni infiere identidad: una persona puede indicar mujer y marcar o no la etiqueta pública. La ficha evita duplicar la etiqueta cuando el tipo ya es trans, y el filtro trans incluye declaraciones y etiquetas elegidas, sin quitar el perfil de mujer/hombre. Copia privada y lectura tipada incluyen el booleano; supresión y recuperación lo borran en su ámbito. La rectificación acepta datos históricos sin el campo y los aplica sin seleccionar ni borrar esa opción posterior; los datos nuevos exigen booleano explícito. Verificación focalizada032355:32PASS/0FAIL/0SKIP, incluidos publicación/filtros, copia, supresión/recuperación y navegador. La rectificación completa ampliada conserva negativos y correctiva033853:1PASS; las ocho variantes pasan en la candidata común034242.

Los documentos sintéticos de publicación y contenido usan `dev-romantic-1`. El bootstrap crea versiones nuevas y conserva documentos/aceptaciones anteriores sin reescribir sus cuerpos. Sigue siendo material de desarrollo, sin aprobación jurídica real.

## Compatibilidad y reversión

Los registros antiguos, sus IDs, tarifas, relaciones y aceptaciones se conservan como historial privado. Una revisión heredada no se reclasifica al editar ni se copia automáticamente a un borrador nuevo. El gestor autorizado recibe409 con acceso a iniciar un perfil romántico dentro de la misma publicación. No se crean publicaciones adicionales por persona. Se impiden mutaciones de medios heredados; lectura privada y derechos conservan su finalidad y autorización.

La prueba de migración recorre0022→0025→0022 y comprueba conservación de registros. La reversión de0025 se rechaza si existe alguna etiqueta seleccionada, para impedir perderla al eliminar la columna; con todos los valores false se permite la ida/vuelta. Ambos casos están verificados por032355. La reversión de esquema no reactiva categorías ni publicaciones: es deliberadamente conservadora. Una reversión operativa requiere aislamiento de exposición, restauración coherente de código/esquema y reconciliación de elegibilidad antes de reabrir. Esta prueba no equivale a un ensayo completo de restauración de beta (B13).

Las copias privadas incorporan la versión de contrato de cada revisión para distinguir historia y contenido actual. La lectura de campos de derechos admite ese escalar; categorías y tarifas históricas se conservan en las copias autorizadas, aunque no sean campos publicables actuales. No se cambia el formato histórico de aceptaciones o snapshots comerciales.

## Verificación disponible

[Evidencia de ejecuciones](evidencias/beta-perfil-verificacion-inicial-20261020.json), conservada por selección y con huella del resultado. No sumar ejecuciones diferentes como una batería común del producto final.

| Ejecución local | Resultado | Alcance |
| --- | --- | --- |
| 020212-c8902cbe | 45PASS/1FAIL/0SKIP | Contrato/migración, borradores, envío y moderación; fallo de fixture sin `published_at` |
| 020757-a8f1023d | 1PASS/0FAIL/0SKIP | Correctiva del fixture, sin cambio de producto |
| 020950-9493b4bd | 19PASS/0FAIL/0SKIP | Búsqueda, validación por contexto y navegador móvil ES |
| 021300-c69afe85 | 32PASS/0FAIL/0SKIP | Navegador ES–EN390/1280, moderación, ciclo de vida, fotos, agencias y verificación |
| 021658-7ef1571b | 51PASS/0FAIL/0SKIP | Estado derivado/nativo, dependencias/carreras, exportación de derechos y revisión independiente |
| 023414-68362bfb | 1PASS/0FAIL/0SKIP | Descarga privada conserva contratos actual y heredado en una misma copia |
| 024215-306f6524 | 41PASS/0FAIL/0SKIP | Resumen de estados, visibilidad fresca, cambios pendientes, ciclo de vida y teclado/navegador ES–EN |
| 025250-084b9c50 | 27PASS/0FAIL/0SKIP | Tipo voluntario omitido/vacío, migración y reversión, publicación, filtros/paridad y navegador |
| 030036-4f65eb63 | 4FAIL/0PASS/0SKIP | Fallo de montaje: ORM síncrono dentro del eventloop de Playwright; negativo conservado |
| 030452-507b53e0 | 4PASS/0FAIL/0SKIP | Correctiva del montaje y recorrido integrado ES–EN390/1280 |
| 032355-b46cac41 | 32PASS/0FAIL/0SKIP | Etiqueta voluntaria, derechos, migraciones y recorrido integrado actualizado |
| 032848-c5101953 | 1PASS/7FAIL/0SKIP | Pruebas heredadas suponían tarifas/servicios en fixture romántica; negativo conservado |
| 033237-fa109852 | 1PASS/7FAIL/0SKIP | Fixture histórica explícita; expectativas del rechazo anterior al contrato beta |
| 033629-a25fad14 | 0PASS/1FAIL/0SKIP | Regresión real: estado de historial rectificado devolvía409 en lugar de404 |
| 033853-204961b1 | 1PASS/0FAIL/0SKIP | Correctiva de precedencia; recorrido completo con desmarcado explícito de etiqueta |
| 034242-6e8e508e | 192PASS/0FAIL/0SKIP | Candidata común B02–B03:24selectores, incluidas ocho variantes de rectificación; auditoría terminal independiente |

Se usaron PostgreSQL y Redis reales aislados; fuentes congeladas y limpieza comprobadas. Los avisos terminales de Telegram tienen recibo confirmado. Los simuladores de identidad/comunicaciones siguen siendo simuladores. Ningún resultado acredita proveedor real ni nueva capacidad HTTP. El negativo inicial se conserva.

La ampliación de rectificación prepara registros profesionales históricos explícitos, conservando tarifas, servicios y etiquetas seleccionadas sin convertirlos en contenido publicable. Las propuestas antiguas omiten el campo nuevo; las nuevas pueden marcarlo o desmarcarlo. Se detectó y corrigió un defecto de precedencia en `revision_status`: la exclusión de historial rectificado se aplica antes de presentar la indicación para crear un perfil romántico. El caso033629 reproduce409 frente a404;033853 verifica la corrección mediante el recorrido completo. Las comprobaciones de autoridad y publicación se conservan.

## Residual y siguiente paso

Comprobada la descarga con contratos actual y heredado en una misma copia por la ejecución023414. Resumen de estados y recorridos verificados por024215, sin omisiones. El residual de tipo obligatorio/predeterminado se ha corregido mediante0024 y formulario/presentación y verificado por025250. El recorrido integrado ES–EN390/1280 desde un perfil sintético pendiente está verificado por030452:4PASS, con aprobación, rechazo de cambios, corrección, nueva aprobación, pausa/reanudación, renovación y retirada. Cuenta, consentimientos y fotografía inicial se preparan con fixtures explícitas; la ventana de renovación se abre ajustando únicamente la caducidad sintética en PostgreSQL. No se simula la autorización ni la decisión de publicación. La [matriz de criterios](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md) se concilia con la [auditoría común](evidencias/b02b03-common-terminal-audit-20261020.json):192PASS/0FAIL/0SKIP sobre la misma candidata, fuentes/limpieza/Telegram comprobados de nuevo. [Acta12](actas/12-beta-b02b03-aceptacion-local-20261020.md) cierra B02/B03 en su alcance local. El grafo se refresca por corte con alcance explícito; no aceptación beta global.

Los atributos físicos continúan diferidos: no hay nuevas medidas, inferencia de imágenes ni preferencias privadas persistidas. Antes de incorporarlos se requiere contrato de opciones/unidades, finalidad y exposición. Las recomendaciones B15 siguen opcionales.

Continuar B04–B06 con semántica de renovación/autosubida, exposición comercial y elegibilidad en todas las superficies. Después mantener B07–B17 según dependencias del roadmap. B00 conserva la auditoría exhaustiva residual del corpus; G01–G08 y apertura permanecen separados.

## Corrección posterior de residuos de interfaz,2026-10-20

Tras congelar y auditar el contraste122947, se sustituyen únicamente dos descripciones generales ES/EN de templates/base.html por perfiles personales de adultos que buscan citas románticas. Se retira templates/core/home.html: plantilla antigua sin referencias entrantes en el grafo ni referencias de ejecución; apps/core/views.py delega home en discovery.results. No cambios de modelos, datos ni rama SEO.

El delta está auditado en [evidencia](evidencias/beta-copy-residual-delta-20261020.json):621 fuentes de producto intactas y622 actuales; la plantilla retirada estaba sin cambios locales previos. Pruebas existentes de cuentas, SEO público y navegación real ES/EN verificadas:17PASS/0FAIL/0ERROR/0SKIP en130446-378a1c88, fuentes congeladas, limpieza y Telegram auditados. La aceptación local anterior queda documentada en su propio corte; no se extiende automáticamente a estos cambios.

La primera ejecución130124-a2d3c51e dio14PASS/3FAIL/0ERROR/0SKIP por expectativas antiguas de títulos profesionales; [negativo conservado](evidencias/beta-copy-negative-terminal-audit-20261020.json). Se actualizan sólo esos títulos esperados al contrato romántico y se comprueba la descripción privada ES/EN en el caso existente. [Auditoría posterior](evidencias/beta-copy-functional-terminal-audit-20261020.json):17casos completos con Chromium real, sin omitidos. Se acepta técnicamente este delta local; no implica beta ni capacidad.
