# B00-312 — Autónomos e inteligencia competitiva

Fecha: 2026-10-23. Conciliación textual, sin dictamen jurídico, nuevas funciones o aceptación de beta.

B00-312: 232 de 295 fuentes únicas conciliadas; quedan 63. Se incorporan las capturas completas del Estatuto del trabajo autónomo y de planificación de inteligencia competitiva mediante cuatro partes. Se conservan sus ámbitos, propuestas y negativos históricos sin ampliar el contrato. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura y procedencia

Se añaden dos fuentes únicas y 438.508 caracteres mediante cuatro lectores nativos de sólo lectura, con un máximo de tres simultáneos. El plan de partes y sus hashes se fijó antes de delegar. No se reutilizaron coincidencias entre fuentes como sustituto de su lectura.

| Fuente y parte | Intervalo Unicode [inicio,fin) | Caracteres |
| --- | --- | ---: |
| Estatuto — 1 | [0,103875) | 103875 |
| Estatuto — 2 | [103875,207497) | 103622 |
| Inteligencia competitiva — 1 | [0,115474) | 115474 |
| Inteligencia competitiva — 2 | [115474,231011) | 115537 |

Cada parte del Estatuto se emitió en nueve intervalos y cada parte de la conversación en diez, contiguos y de hasta 12.000 caracteres por salida individual, sin truncamientos declarados. El principal verificó continuidad, hashes completos y parciales, catorce comprobaciones de cita en doce intervalos distintos y sus contextos. Las 295 capturas se cotejaron contra sus hashes y longitudes del inventario.

La frontera del Estatuto divide notas históricas del artículo24; la conversación divide un turno User tras una precisión sobre estados internos de revisión. Las uniones conservan su contexto. Las partes no se contabilizan como fuentes separadas, y cargar un JSON para metadatos no se usa como prueba de lectura.

Plan, protocolo, informes íntegros, propuestas, contextos y auditoría están en `artifacts/beta-promotion-fix-20261020/b00-312-*`. `verify_b00_312.py` sólo integra sobre la base230 o resultado idéntico, mediante reemplazo atómico con permisos preservados. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa a 232/295, con 63 pendientes. No se acredita revisión visual, lectura de destinos enlazados, versiones alternativas o actualidad jurídica.

## Estatuto: hechos y sujetos antes de encuadrar

Fuente `source:9z5ocaj3ss1nogkjt7h2`, 207.497 caracteres en español. Contiene navegación y preámbulo, articulado principal, regímenes específicos, protección social, fomento e incentivos, disposiciones e historia editorial. La advertencia de consolidación informativa, los índices, estadísticas antiguas y notas se mantienen separados del texto principal.

La captura diferencia inclusiones y exclusiones subjetivas, derechos y obligaciones, relaciones profesionales, dependencia económica, representación colectiva y competencias públicas. El encuadramiento exige hechos y condiciones; no se clasifica al operador, anunciantes o agencias como autónomos por participar en un portal o publicar un perfil. El umbral de dependencia económica tampoco se aísla de sus demás condiciones.

Los mandatos a poderes públicos, reglas sectoriales, ayudas e incentivos condicionados no se convierten en funciones o requisitos del producto. Se preservan derogaciones, aplazamientos, períodos de beneficios y una modificación capturada con efectos sobre cuotas en octubre de2026, sin certificar su vigencia o aplicabilidad ni ofrecer importes actuales. Fecha de publicación, entrada en vigor y efectos económicos son conceptos distintos.

El [contrato14](14-contrato-funcional-v1.md) conserva perfiles para citas románticas, sin ofertas profesionales ni tarifas por servicios. La lectura del Estatuto no introduce acreditaciones laborales o fiscales para publicar, ni resuelve la forma jurídica, relaciones de trabajo o preparación real del operador. Esas cuestiones requieren su evaluación concreta antes de producción.

## Inteligencia competitiva: evolución y autoridad

Fuente `source:x38a255evnfra9971329`, 231.011 caracteres. Es una conversación histórica User/Gemini con encargos de investigación, bibliografía, auditorías pegadas, matrices sucesivas, PRD-ACQ-01 y adenda, PRD-DEP-01 y una misión citada de consolidación. Las etiquetas permiten localizar turnos; no prueban autoría original de los textos pegados ni convierten sus instrucciones en órdenes actuales.

La bibliografía inicial y algunas métricas son impugnadas dentro de la propia conversación; esta conciliación no verifica esos trabajos externos ni adopta sus cifras como resultados. Intención de contacto no equivale a conversación o match, actividad no equivale a disponibilidad y créditos gratuitos no prueban conversión a pago. Los objetivos territoriales o numéricos se conservan como hipótesis de adquisición, no como umbrales de liquidez demostrados.

El intercambio propone separar inteligencia de mercado, planificación y adquisición sobre datos propios; su cierre mantiene un carácter conceptual y el contrato técnico mínimo intacto. El estado interno REQUIRES_LEGAL_REVIEW no es una categoría legislativa. La afirmación de que un documento es definitivo o ratificado no acredita revisión jurídica, implementación o prueba.

La captura conserva restricciones y revisiones sobre extracción, importación de anuncios y prospección, y afirma expresamente que la planificación no autoriza crawling ni captación comercial real. No se incorporan IA, crawling, contactos, créditos, referidos, proveedores o campañas al contrato vigente desde esta fuente. Tampoco se inicia la misión histórica de escritura en NotebookLM.

## Negativos de trazabilidad preservados

La conversación distingue diseño, implementación, ejecución de pruebas y validación jurídica, pero sus primeras auditorías confunden o sobregeneralizan esas evidencias. Las correcciones posteriores mantienen AUDIT-TRACE-01 en INSUFFICIENT_EVIDENCE. En concreto, según ese intercambio:

- ACQ-018 no queda respaldado por E2E-DEP-002, que trata revisiones pendientes y no disponibilidad vigente.
- La asociación de ACQ-017 a E2E-DEP-003/005 ofrece cobertura parcial, no todos los criterios de perfil publicado.
- La exclusión ACQ-001 requiere control de alcance; la nomenclatura se relaciona con REQ-ACQ-001 sin renumerar requisitos congelados.
- Se señalan documentos originales no disponibles y cobertura incompleta de dependencias, invariantes y pruebas; no se declara certificación global de trazabilidad.

Son límites documentales históricos del diseño de captación, no fallos nuevos acreditados en el runtime ni pruebas funcionales ejecutadas en este corte. La referencia a originales no accesibles describe la conversación, sin afirmar que hoy no existan. La [conciliación UX174](174-conciliacion-ampliada-fuentes-ux-beta-b00-20261021.md) ya conserva el carácter conceptual de los PRD de visitante y sus límites; tampoco equivale por sí sola a los originales o a una auditoría completa de implementación.

Las afirmaciones finales de CREATED, list_sources, indexación y recuperación RAG no incluyen recibos o inventarios verificables en la captura. La consolidación declarada enumera sólo parte de los dominios solicitados. La respuesta final sobre URLs se refiere a chats anteriores y no resuelve sustantivamente la precisión del usuario sobre este chat. No se acepta una importación o recuperación externa por una declaración de éxito de Gemini.

## Resultado y continuación

El [contrato vigente](14-contrato-funcional-v1.md), [roadmap](103-roadmap-beta-clasificados-20261020.md), decisiones B15 y aceptaciones locales conservan su alcance. No se añaden los PRD de captación como una nueva cola de implementación. Las propuestas que requieran datos, contacto real o proveedores necesitan evidencia y autorización propias; no se ejecutan durante esta conciliación.

Quedan 56 fuentes de arquitectura, cuatro legales y tres comerciales. Las 13 capturas del cuaderno de moderación siguen conciliadas sólo en su alcance documental, sin nuevo crédito por repetir ese estado. Los originales judiciales pendientes y límites de otras capturas se mantienen. B00 y la aceptación global continúan abiertos.

Sin cambios de aplicación, cargas o pruebas funcionales. Cuatro lectores nativos de sólo lectura, sin nuevas invocaciones ClaudeV1 y con su consumo histórico preservado. Corte anterior: [conciliación270](270-conciliacion-ia-infancia-b00-20261023.md).
