# Matriz final de conciliación de B00

Fecha:2026-10-24. Estado: matriz conciliada y aceptada para B00local por [acta17](actas/17-beta-b00-aceptacion-local-20261024.md), con corrección299verificada25PASS. No aceptación beta ni producción.

La [matriz original104](104-consolidacion-contrato-beta-b00b01-20261020.md#matriz-de-adaptación-y-evidencia-de-implementación) conserva la base observada el20deoctubre. Esta matriz establece qué corresponde al producto actual y qué sigue diferido. Se cruzan las decisiones CB01–CB10, el contrato funcional1.1, el [DAFO98](98-dafo-clasificados-citas-romanticas-20261020.md), la disposición de las295capturas y las actas posteriores. Las aceptaciones históricas se conservan en su versión; no se suman como candidata actual.

[Datos completos por fila](evidencias/b00-final-adaptation-matrix-20261024.json) y [puente de identidad](evidencias/b00-ad-identity-bridge-20261024.json). Cada fila contiene decisión, estado actual, objetivo, archivos, migración, criterio, evidencia, límites y residual.

## Matriz de cambios y evidencia

| ID | Decisión | Estado conciliado | Residual |
| --- | --- | --- | --- |
| AD01 | CB01/CB06: catálogo romántico; IDs e historia conservados | Seed crea romantic-dating; migración0023 desactiva categorías/servicios previos e invalida elegibilidad. Revisiones legadas no se renombran ni republican. | Sin cambio nuevo de catálogo requerido por la conciliación. B16 conserva candidata común. |
| AD02 | CB02/CB06: panel de perfil sin precios por cita/servicio | DetailsForm limita campos personales y rechaza POSTprofesional; nuevo recorrido no crea Rate. El guard romántico rechaza tarifas/servicios/desplazamiento almacenados. | Estado profesional de la matriz inicial deja de describirse como actual. |
| AD03 | CB01/CB05: público romántico ES–EN y GETantiguo explícito | Listado/ficha presentan perfiles; filtros profesionales conocidos se rechazan. Las superficies privadas/incompatibles se excluyen con perfil par preservado. | B08–B11optimizaciones y B16integración mantienen sus alcances. |
| AD04 | CB10: validación única, estado conservador y autoridad actual | Envío reconstruye DetailsForm y valida contrato; publicly_visible comparte guardas. Estado derivado conserva caducidad SQL, versiones e invalidación; página revalidada. | La corrección privada de cobertura B00-340 tiene reproducción/regresión propia y no se atribuye a estos testigos públicos. |
| AD05 | CB02: Mi perfil como entrada principal | Se reutiliza persona/listing/borrador; nueva revisión no altera aprobado ni copia legado incompatible. Navegación y acciones dependen de estado/rol. | B16mantiene candidata común; no queda la simplificación de panel íntegra por implementar. |
| AD06 | CB03: renovar gratuito7/30 separado de autosubida | Renovar exige revisión aprobada/confirmación y ventana7d; fija30d/fecha editorial, conserva pausa y no reanuda retirado. No concede Top ni pedido. | Siguiente paso vigente no es empezar B07: tras B00, B08–B11. |
| AD07 | CB03/CB09: promoción sintética de elegibles | PRODUCTION/RECOVERY_MODE excluyen promociones; elegibilidad exige comprador activo/gestión actual/snapshot/visibilidad. Ranking revalida lote y deduplica publicaciones. | Ventas/proveedor/condiciones reales no activadas; no nuevo defecto por código histórico privado. |
| AD08 | CB07/CB08: atributos y preferencias opcionales separados | Tipo voluntario y etiqueta trans independiente implementados. No acreditan recomendador; cookies propias y preferencias cifradas de cuentas siguen diseño opcional. | B15opcional no bloquea beta local. DBvsobjetos/cookiepayloadvsIDopaco pendientes; no seguimiento conductual/importación automática autorizados. |
| AD09 | CB04/CB05/CB10: persona/cuenta/gestor/finalidad distintos | Mecanismos locales de verificación/representación/MFA/revocación conservados. Superficies prueban doce causas de exclusión antes/después de refresco. | B14/B17/G01–G08conservan integración/realidad de apertura; no se aceptan proveedores leyendo tests. |
| AD10 | CB01/CB10: textos románticos versionados sin reescribir aceptación | Bootstrapcrea dev-romantic-1en publishing/content por get_or_create, conserva cuerpos/aceptaciones previos y bloquea PRODUCTION. | Operador/textos definitivos/revisión jurídica son B17/G01–G08; no falta implementación sintética por la frase original cuando se implementen. |
| AD11 | CB10: historia y derechos conservan ámbito y significado | Tablas/tarifas legadas permanecen como evidencia privada; dato voluntario participa en derechos; restauración comercial conserva hash sin ranking/bump del suprimido. | B16candidata común y B17preparación real se mantienen; no eliminar historia para simplificar UI. |

## Criterios, migración y alcance por fila

### AD01

Objetivo: Publicar perfiles románticos sin selección profesional obligatoria.

Archivos: [seed_catalog.py](../apps/catalog/management/commands/seed_catalog.py), [profile_contract.py](../apps/listings/profile_contract.py), [revisions.py](../apps/listings/revisions.py), [0023_romantic_profile_contract.py](../apps/listings/migrations/0023_romantic_profile_contract.py), [0024_optional_profile_type.py](../apps/listings/migrations/0024_optional_profile_type.py), [0025_optional_trans_label.py](../apps/listings/migrations/0025_optional_trans_label.py).

Migración: 0023preserva legado;0024tipo voluntario;0025descenso bloqueado ante etiqueta seleccionada.

Aceptación: Ida/vuelta conserva IDs/tarifas/historia; legado privado; nuevo borrador limpio.

Evidencia: [106-matriz-aceptacion-perfil-beta-b02b03-20261020.md](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md), [12-beta-b02b03-aceptacion-local-20261020.md](actas/12-beta-b02b03-aceptacion-local-20261020.md), [test_beta_profile_contract.py](../tests/test_beta_profile_contract.py).

Límite: Acta12en candidata034242; testigo de migración posterior B13verificado. No esquema aplicado en servicios normales o cobertura nacional.

### AD02

Objetivo: Rellenar datos, ubicación, contactos, fotos y revisión.

Archivos: [forms.py](../apps/listings/forms.py), [profile_contract.py](../apps/listings/profile_contract.py), [views.py](../apps/listings/views.py), [draft.html](../templates/listings/draft.html).

Migración: Sin borrar tablas/evidencias; revisión versionada separa legado.

Aceptación: Publicar sin campos profesionales; manipulación400sin mutación y sin tablas eliminadas.

Evidencia: [106-matriz-aceptacion-perfil-beta-b02b03-20261020.md](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md), [test_beta_profile_contract.py](../tests/test_beta_profile_contract.py), [test_beta_profile_contract.py](../tests/test_beta_profile_contract.py).

Límite: Aserciones actuales contrastadas por root; aceptación histórica P02en su corte, no nueva ejecución de esos casos.

### AD03

Objetivo: Filtros/URL/paginación coherentes y contactos autorizados sin exposición profesional.

Archivos: [results.html](../templates/listings/results.html), [public_detail.html](../templates/listings/public_detail.html), [discovery.py](../apps/listings/discovery.py).

Migración: No traducción silenciosa de filtros viejos a resultados amplios.

Aceptación: GETprofesional400/recuento0; sólo elegibles; ES–EN/filtros/páginas coherentes.

Evidencia: [106-matriz-aceptacion-perfil-beta-b02b03-20261020.md](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md), [107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md](107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md), [16-beta-b07-aceptacion-local-20261023.md](actas/16-beta-b07-aceptacion-local-20261023.md).

Límite: Discovery cambió después de actas12/13. SHAactual coincide con B13/B07; carga pública B07cubre lectura/filtros/elegibilidad, no todos los formularios.

### AD04

Objetivo: Paridad envío/aprobación/lectura sin cachear autoridad.

Archivos: [submissions.py](../apps/listings/submissions.py), [moderation.py](../apps/listings/moderation.py), [public_validation.py](../apps/listings/public_validation.py), [publication_state.py](../apps/listings/publication_state.py), [profile_contract.py](../apps/listings/profile_contract.py).

Migración: 0023invalida estado anterior; cambios posteriores de regla siguen versión/dependencias.

Aceptación: Mismo rechazo nativo/contextual; retirada inmediata, integridad de dependencias y pruebas afectadas.

Evidencia: [106-matriz-aceptacion-perfil-beta-b02b03-20261020.md](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md), [107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md](107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md), [test_beta_public_surfaces.py](../tests/test_beta_public_surfaces.py), [16-beta-b07-aceptacion-local-20261023.md](actas/16-beta-b07-aceptacion-local-20261023.md).

Límite: Submissions/publication_state tienen SHAposterior a acta13, igual a B13/B07. No se generaliza una carga pública a todas las rutas privadas.

### AD05

Objetivo: Guardar, retomar, corregir, revisar y publicar sin perder datos.

Archivos: [accounts.py](../apps/core/accounts.py), [views.py](../apps/listings/views.py), [revisions.py](../apps/listings/revisions.py), [profile_status.py](../apps/listings/profile_status.py), [lifecycle.html](../templates/listings/lifecycle.html), [draft.html](../templates/listings/draft.html).

Migración: Sin crear otra persona/anuncio por navegar; historia conservada.

Aceptación: Recarga, teclado, ES–EN390/1280 y roles con separación borrador/aprobado.

Evidencia: [106-matriz-aceptacion-perfil-beta-b02b03-20261020.md](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md), [12-beta-b02b03-aceptacion-local-20261020.md](actas/12-beta-b02b03-aceptacion-local-20261020.md).

Límite: Acta12acredita recorrido local sintético. Panel posterior vinculado por SHAa acta13/B13/B07; no participantes reales ni regresión conjunta actual.

### AD06

Objetivo: Mismo ID/revisión, estados y reintentos/carreras correctos.

Archivos: [lifecycle.py](../apps/listings/lifecycle.py), [lifecycle.html](../templates/listings/lifecycle.html), [promotion_exposure.py](../apps/catalog/promotion_exposure.py).

Migración: Sin cambio de duraciones; autosubida sólo señal comercial separada.

Aceptación: Orden orgánico renovado, reintento único y carreras con caducidad; disponible4h sin promesa de cita.

Evidencia: [107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md](107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md), [13-beta-b04b06-aceptacion-local-20261020.md](actas/13-beta-b04b06-aceptacion-local-20261020.md), [test_beta_public_surfaces.py](../tests/test_beta_public_surfaces.py).

Límite: Lifecycle/panel coinciden con corte043105; B07ya aceptado por acta16, sin reabrir renovación ni atribuir capacidad global.

### AD07

Objetivo: Patrocinio explícito y filtros/rotación/paginación sin eludir moderación.

Archivos: [promotion_orders.py](../apps/catalog/promotion_orders.py), [promotion_exposure.py](../apps/catalog/promotion_exposure.py), [tasks.py](../apps/catalog/tasks.py), [test_promotion_recovery.py](../tests/test_promotion_recovery.py).

Migración: Snapshots/derechos/importes históricos no se recalculan por nombres.

Aceptación: Worker/Beatpropios, cuotas/replay/carreras; restauración conserva evidencia sin reactivar exposición/bump.

Evidencia: [107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md](107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md), [13-beta-b04b06-aceptacion-local-20261020.md](actas/13-beta-b04b06-aceptacion-local-20261020.md), [15-beta-b13-aceptacion-local-20261021.md](actas/15-beta-b13-aceptacion-local-20261021.md), [16-beta-b07-aceptacion-local-20261023.md](actas/16-beta-b07-aceptacion-local-20261023.md).

Límite: Exposure/recoverytest cambiaron respecto043105; SHAactuales iguales a B13/B07. JUnitB13incluye restauración comercial real propia; B07no ejecuta el archivo de test por incluirlo en manifest.

### AD08

Objetivo: Si B15se incorpora, contrato por atributo/preferencia y control de usuario sin inferencias implícitas.

Archivos: [14-contrato-funcional-v1.md](14-contrato-funcional-v1.md), [103-roadmap-beta-clasificados-20261020.md](103-roadmap-beta-clasificados-20261020.md), [models.py](../apps/listings/models.py), [forms.py](../apps/listings/forms.py), [0025_optional_trans_label.py](../apps/listings/migrations/0025_optional_trans_label.py).

Migración: Ninguna migración de recomendación aprobada por esta conciliación.

Aceptación: Definir datos/unidades/desconocidos, visibilidad, finalidad, persistencia, claves, retención, modificación/borrado/desactivación y utilidad.

Evidencia: [14-contrato-funcional-v1.md](14-contrato-funcional-v1.md#61-recomendaciones-físicas-opcionales), [103-roadmap-beta-clasificados-20261020.md](103-roadmap-beta-clasificados-20261020.md), [106-matriz-aceptacion-perfil-beta-b02b03-20261020.md](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md).

Límite: Dato voluntario aceptado localmente no prueba consentimiento productivo/RGPD o recomendación. No ausencia universal de personalización acreditada por búsqueda.

### AD09

Objetivo: Autorización individual actual; teléfono o casilla no sustituyen identidad/representación.

Archivos: [verification.py](../apps/core/verification.py), [agencies.py](../apps/core/agencies.py), [submissions.py](../apps/listings/submissions.py), [moderation.py](../apps/listings/moderation.py), [promotion_exposure.py](../apps/catalog/promotion_exposure.py).

Migración: Sin nuevo cambio de identidad o grants por redefinir el producto.

Aceptación: Permisos/gestión/edad/contacto/consentimiento obsoletos excluyen superficies y operaciones afectadas.

Evidencia: [106-matriz-aceptacion-perfil-beta-b02b03-20261020.md](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md), [107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md](107-matriz-fiabilidad-exposicion-beta-b04b06-20261020.md), [test_beta_public_surfaces.py](../tests/test_beta_public_surfaces.py).

Límite: Identidad/comunicaciones sintéticas; superficies públicas no prueban toda autoridad privada. Bugde cobertura tiene prueba propia B00-340.

### AD10

Objetivo: Runtime sintético romántico ES–EN con versión actual exigible.

Archivos: [bootstrap.py](../apps/core/management/commands/bootstrap.py), [accounts.py](../apps/core/accounts.py), [submissions.py](../apps/listings/submissions.py), [15-apartado-legal-publico.md](15-apartado-legal-publico.md).

Migración: Nueva versión por mecanismo existente, no edición retroactiva de LegalAcceptance.

Aceptación: Aceptaciones siguen ligadas al cuerpo original; publicación exige nuevo documento aplicable.

Evidencia: [106-matriz-aceptacion-perfil-beta-b02b03-20261020.md](106-matriz-aceptacion-perfil-beta-b02b03-20261020.md), [test_beta_profile_contract.py](../tests/test_beta_profile_contract.py), [15-apartado-legal-publico.md](15-apartado-legal-publico.md).

Límite: Bootstrap/testigo iguales a actas12/13; no demuestra instalación en servicio normal ni revisión jurídica real.

### AD11

Objetivo: Inventarios/huellas/cobertura coherentes, sin borrar terceros ni resucitar contenido.

Archivos: [rights_rectification.py](../apps/safety/rights_rectification.py), [rights_copy_data.py](../apps/safety/rights_copy_data.py), [promotion_order_inventory.py](../apps/safety/promotion_order_inventory.py), [recovery_apply.py](../apps/safety/recovery_apply.py), [test_declared_profile_label.py](../tests/test_declared_profile_label.py), [test_promotion_recovery.py](../tests/test_promotion_recovery.py).

Migración: 0023–0025y lectores históricos conservados; descenso destructivo de etiqueta seleccionado bloqueado.

Aceptación: Copia histórica compatible, invalidación ante cambios, supresión scoped y restauración sin exposición indebida.

Evidencia: [12-beta-b02b03-aceptacion-local-20261020.md](actas/12-beta-b02b03-aceptacion-local-20261020.md), [13-beta-b04b06-aceptacion-local-20261020.md](actas/13-beta-b04b06-aceptacion-local-20261020.md), [15-beta-b13-aceptacion-local-20261021.md](actas/15-beta-b13-aceptacion-local-20261021.md), [test_promotion_recovery.py](../tests/test_promotion_recovery.py).

Límite: B13incluye restauración real propia y testigos; no offsite/PITR/guardia/proveedor. Monitoreo B12no equivale a inventario universal.

## Identidad y cobertura son comprobaciones distintas

Se verificaron directamente siete rutas seleccionadas que difieren o faltan respecto a los primeros cortes B02–B06: submissions,publication_state,discovery,lifecycle.html,promotion_exposure,test_promotion_recovery ytest_beta_public_surfaces. Cinco manifiestos originales se cotejaron por SHA256:034242,043105,B13final,contractual265ycombinado296. Las siete rutas actuales coinciden con B13yB07. Esto no convierte todas las pruebas de034242/043105 en ejecuciones de la versión actual ni demuestra que un test incluido en el manifiesto se ejecutara durante una carga.

El JUnit B13 contiene26casos sin fallos/errores/omisiones; se localizaron los testigos de restauración comercial, migración romántica y bloqueo de reversión destructiva de etiqueta. Las cargas B07 aportan recorrido público, filtros, elegibilidad y presupuestos en sus escenarios. No acreditan todas las ramas de edición o lifecycle. B16 mantiene la exigencia de una candidata común y verificación afectada; no se inventa una regresión conjunta desde estos testigos. No se repitió una carga por actualizar documentación.

La revisión nativa fue de sólo lectura. El principal contrastó código/aserciones seleccionados, archivos, huellas y JUnit antes de integrar sus hallazgos. Los informes son entradas y sus extractos no son transcripciones completas. Un suplemento tuvo STATUS y un tipo de campo no conformes al contrato de reporte; se corrigió sólo su formato, sin releer ni generar evidencia nueva. La referencia «Contrato119» se corrigió a contrato14,línea119.

## Cruce con el DAFO

| DAFO | Conciliación y tratamiento |
| --- | --- |
| F1–F3; D1–D2 | La estructura de clasificados, catálogo romántico, panel y semántica de renovación tienen adaptación y aceptación técnica local identificada. No se vuelve a presentar la base profesional del alfa como requisito actual. Facilidad de uso y preferencias reales de personas siguen necesitando validación autorizada. |
| F4–F5; D5 | Las garantías y trazabilidad son mecanismos que deben comprobarse por recorrido. La revisión ha producido correcciones concretas, incluida autoridad antes del descifrado en299; no se acepta seguridad global por el grafo o por una cuenta de pruebas. Las optimizaciones siguen B08–B11 y las garantías conservan sus criterios. |
| D3; O2 | Recomendaciones físicas B15opcionales; tipo/etiqueta voluntarios no prueban recomendación implementada. Preferencias elegidas, cookies y almacenamiento privado requieren diseño pendiente; no biometría, inferencia por fotos o seguimiento implícito. |
| D4; A1–A3; O1/O3/O4 | Densidad, utilidad comercial, distribución de atención y disposición a pagar no están validadas. No se atribuye éxito comercial a Top, p95 o anuncios sintéticos. No activar ventas o captación con personas sin autorización correspondiente. |
| D6; A4–A6; O5 | Moderación y respuesta humana, terceros, custodia, seguridad independiente y revisión jurídica real conservan B17/G01–G08. Las referencias y condiciones de terceros del DAFO mantienen su fecha histórica; no se elige proveedor ni se afirma aprobación actual. Verificación concreta no garantiza conducta o interés romántico. |

## Decisiones abiertas y bloqueo

| Asunto | ¿Bloquea la implementación afectada? | ¿Bloquea beta técnica sin esa ampliación? | Destino |
| --- | --- | --- | --- |
| Campos físicos adicionales y recomendaciones | Sí, hasta definir catálogo/finalidad/exposición/desconocidos y criterio | No: B15es opcional | B15; no añade campos por esta conciliación |
| Cookies de preferencias, contenido cifrado o IDopaco, DBuobjetos, claves y retención | Sí para persistencia/personalización | No sin B15 | B15; búsqueda normal permanece y no se importa navegador automáticamente a cuenta |
| Seguimiento conductual/inferencia de imágenes | No autorizado como elección implícita | No se incluye | Fuera del alcance actual; requiere decisión específica |
| Precios, pasarela, reembolsos y venta real | Sí para activación comercial | No para lanzamiento gratuito/adaptadores sintéticos | B14/B17yautorización comercial, sin contratar por este documento |
| Operador/dominio, textos definitivos, proveedor real y dataset geográfico nacional | Sí para apertura real correspondiente | No para mecanismo local sintético probado | B17/G01–G08 |
| Responsables de moderación/incidentes, custodia externa, revisión jurídica y seguridad independiente | Sí para apertura real | No sustituye aceptación local por simuladores | B17/G01–G08 |
| Cuerpos judiciales originales ausentes, colas/remisiones de capturas y censo remoto posterior | Impiden usar esos originales o afirmar auditoría remota actual | No se adoptan sus conclusiones; límites quedan explícitos | Fuentes primarias/revisión real pendiente, sin fingir lectura |
| Autoridad de cobertura tras espera | Sí para aceptar la corrección privada | Se exige reproducción/regresión afectada |299; regresión25PASS, alcance afectado aceptado sin seguridad global |

## Obligaciones de B00 y condición de salida

La [etapa0del roadmap](103-roadmap-beta-clasificados-20261020.md#etapa-0-consolidar-el-alcance) exige revisión de fuentes y decisiones, corrección identificada del grafo y matriz por cambio, con las limitaciones de acceso declaradas. La revisión cubre295disposiciones del inventario capturado y todos los atributos de sus datos de grafo; whole_corpus_reviewed=false sigue distinguiendo cuerpos originales faltantes y nuevas entradas remotas no verificadas. No se borra esa limitación para cerrar una tarea técnica.

La matriz presente resuelve el desfase de las observaciones originales, enlaza decisiones e implementación/evidencia y asigna las decisiones diferidas. Las correcciones AST76Meta/cuatrosdecoradores/sietebases se conservaron por guardas del grafo; el refresco posterior a la corrección299 debe volver a comprobarlas. Antes de aceptar B00, verificar literalmente las cinco obligaciones derivadas, el resultado/alcance/limpieza/fuentes de la regresión299 y la consistencia final de documentos/grafo. Emitir aceptación local sólo si esas condiciones están probadas. No aceptar B08–B11,B14–B17,B16o producción por este documento.

La corrección de autoridad299terminó con25PASSsin fallos/omisiones, fuentes/limpieza/Telegram verificados. Las cinco obligaciones quedan conciliadas en la [matriz de aceptación por requisito](evidencias/b00-local-requirement-acceptance-matrix-20261024.json) y acta17. B00queda cerrado en ese alcance local; los límites y tareas B08–B17no se convierten en aceptación por esta matriz.
