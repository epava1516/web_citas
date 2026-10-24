# B00 — Conciliación parcial de fuentes UX

Estado: cinco fuentes breves leídas íntegramente; revisión parcial, sin cierre B00 ni nuevos requisitos o aceptación de producto. Trabajo de lectura realizado durante la preparación de164; documentación posterior al terminal, sin alterar su freeze ni ejecutar otra batería.

[Registro con IDs, versiones y hashes](evidencias/b00-ux-precedence-review-20261021.json). Se leyeron completas las cinco fuentes siguientes mediante get_source, no por una respuesta top-k. Otras cuatro referencias recuperadas sólo se revisaron parcialmente o quedaron sin revisión integral: se marcan así, sin contabilizarlas como leídas completas. Los originales y notebooks no se modificaron; no hubo consulta a modelos, chats ni reindexación.

| Fuente Open Notebook | Clasificación y efecto en beta |
| --- | --- |
| source:lgltxw0qv57d3q1s9b3p, Gobernanza del MVP,17octubre | Separa diseño, implementación, prueba y validación jurídica. El título «Aceptadas» no demuestra por sí solo aprobación de cada alcance posterior ni sustituye contrato14. Sus afirmaciones jurídicas no se validan por esta lectura. |
| source:um6elgg521uwz8m27foh, PRD-VUX-02,0.1candidata | Propone navegación sin cuenta y niveles de persistencia; restringe preferencias sensibles. VUX013 de restauración de pestañas no autoriza persistencia íntima ni se convierte automáticamente en requisito aprobado de beta. |
| source:4ohdtwlrvkln50nouw3p, PRD-VUX-04,0.1candidata | Wireframes conceptuales; el texto conserva prototipo pendiente y no amplía contrato mínimo. Contacto como intención, revisión aprobada y retirada son principios que deben contrastarse con implementación/evidencia, no con el estado documental. |
| source:71bhs87349asy3s2tx67, síntesis atribuida a Baymard | No se identifica el original que respalde sus cifras de65% o100ms. No adoptar esas cifras, autocompletado ni garantías de UX como requisitos o resultados empíricos. |
| source:3yhqcvx1jsi9bh4aeuod, síntesis atribuida a NNGroup | Heurísticas de tarjetas/filtros y estados vacíos; no evidencia de estudio identificable, aprobación ni prueba de utilidad de este producto. |

## Contraste con las fuentes locales vigentes

Contrato14, apartados de perfil y B15, y matriz104 prevalecen para la adaptación romántica. Los atributos físicos detallados/preferencias/recomendador están pendientes de contrato por atributo y son opcionales para beta. No se implementa aprendizaje de navegación ni recuperación sensible por inferencia de estos PRD. No se cambia el presupuesto contractual de rendimiento a100ms por una síntesis.

Lectura de código: descubrimiento usa formularioGET y paginación HTML; base.html no carga HTMX ni habilita su historial, y los enlaces externos de contacto incluyen noreferrer. Esto no demuestra ausencia universal de almacenamiento o filtración de datos ni conformidad WCAG: no se ha ejecutado aquí una auditoría de navegadores/logs/almacenamiento. La copia extensa de WCAG recuperada se conserva como parcial, sin afirmar revisión normativa completa o vigencia externa.

Testigos existentes consultados: test_browser_discovery.py para filtros móviles/paginación/recarga; test_browser_beta_profile_journey.py para recorrido ESEN; test_public_seo.py para metadata. Son referencias de código, no nuevas pruebas ejecutadas ni reaceptación global. El alcance y los PASS anteriores mantienen sus actas y versiones; este documento no los extiende.

## Residual

Quedan el resto del corpus, las conversaciones extensas, originales de síntesis, conciliación completa de decisiones y cualquier evaluación jurídica/UX externa aplicable. El registro de control Open Notebook ya leído en104 se consultó como contexto; no se cuenta de nuevo como fuente nueva auditada. No deducir total de fuentes únicas desde source_count limitado del listado. B00 permanece parcial y ocho de18puntos cerrados.
