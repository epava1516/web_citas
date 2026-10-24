# B00-310 — DSA, moderación y alcance del apartado legal

Fecha: 2026-10-23. Conciliación textual de una captura jurídica, sin aceptación normativa vigente ni de beta.

B00-310: 228 de 295 fuentes únicas conciliadas; quedan 67. Se incorpora la captura completa del DSA mediante cuatro partes y se corrige el resumen de envío del apartado legal para el perfil romántico. Sin dictamen vigente, obligaciones nuevas adoptadas o cambios de aplicación. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Cobertura completa y procedencia

Fuente `source:8sw6xa9k5jx7wvutsq03`, 501.945 caracteres. El título de EUR-Lex lleva EN, pero el cuerpo jurídico capturado está en español. Cuatro lectores nativos de sólo lectura cubrieron partes fijadas antes de delegar, en dos tandas con un máximo de tres lectores simultáneos. Ninguna parte se contabiliza como fuente separada.

| Parte | Intervalo Unicode [inicio,fin) | Caracteres | Fronteras |
| --- | --- | ---: | --- |
| 1 | [0,124222) | 124222 | Navegación, identificación, preámbulo y considerandos 1–71; termina tras el marcador 72 |
| 2 | [124222,249897) | 125675 | Cuerpo del considerando 72, restantes considerandos hasta 156, artículos 1–2 y parte del 3; termina tras la letra o) |
| 3 | [249897,374598) | 124701 | Continúa la definición o), restantes definiciones, artículos 4–42 y primer párrafo del 43 |
| 4 | [374598,501945) | 127347 | Continúa el 43, artículos 44–93, firmas, notas y pie institucional |

Cada lector emitió once intervalos contiguos de hasta 12.000 caracteres, individualmente, sin truncamientos declarados. El principal cotejó hashes completos y parciales, continuidad, trece comprobaciones de cita en doce intervalos distintos y contextos de fronteras. Las 295 capturas se comprobaron contra sus hashes y longitudes del inventario. Los marcadores, índices y referencias no se cuentan como contenido jurídico leído por sí solos.

Plan, protocolo, informes íntegros, propuesta, contextos y auditoría se conservan en `artifacts/beta-promotion-fix-20261020/b00-310-*`. `verify_b00_310.py` valida la unión y la corrección documental, y sólo integra sobre su base227 o resultado idéntico, mediante reemplazo atómico que conserva permisos. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de 227 a 228 disposiciones de captura, con 67 pendientes. No se atribuye lectura de destinos enlazados, documentos citados, versiones alternativas o presentación visual.

## Considerandos, articulado y regímenes separados

La captura contiene 156 considerandos y 93 artículos. Los primeros explican objetivos e interpretación; no se convierten aisladamente en obligaciones operativas. El cuerpo distingue intermediación, alojamiento, plataformas, plataformas que permiten contratos a distancia entre consumidores y comerciantes y servicios designados de muy gran tamaño. La gratuidad, el contacto externo o el destino adulto del producto no deciden automáticamente su clasificación.

Se mantienen separadas las exenciones condicionadas de responsabilidad y las obligaciones de diligencia debida. La ausencia de obligación general de monitorización del artículo 8 capturado tampoco demuestra inmunidad, ausencia de deberes específicos o suficiencia de la moderación actual. Los artículos sobre órdenes y entrega de información contienen condiciones y garantías propias; no autorizan una cesión indiscriminada de datos ante cualquier denuncia.

Las exclusiones de los artículos 15, 19 y 29 tienen ámbitos distintos. En particular, el artículo 19 conserva expresamente el artículo 24.3; tampoco se presupone que el operador tenga condición de microempresa o pequeña empresa. El régimen de comerciantes, sus datos y plazos no se transforma en una retención universal de perfiles. Los mecanismos para servicios designados de muy gran tamaño, tasas, auditorías y repositorios específicos no se trasladan a esta beta por analogía.

La cola del texto diferencia supervisión, competencias, garantías, instrumentos voluntarios, modificaciones y régimen temporal. El artículo 93 capturado combina aplicación general y disposiciones anticipadas; no se usa una fecha aislada como prueba de situación jurídica actual. Las notas bibliográficas, firmas y pie institucional no son un anexo operativo adicional. La lectura no confirma autoridades actuales, actos de desarrollo, vigencia o cumplimiento.

## Implicaciones que requieren evaluación del funcionamiento real

El [marco legal](06-marco-legal.md#leg-005--dsa-y-moderación) ya conserva la clasificación y las excepciones como cuestiones por confirmar. Esta conciliación aporta preguntas verificables, sin conceder una exención ni adoptar requisitos adicionales:

- Notificación de contenido, reclamación contra una decisión y derechos de datos son procedimientos distintos. Los artículos 16–18 capturados contienen elementos, condiciones, motivos y supuestos propios; el contacto opcional de una denuncia general no resuelve la notificación formal. El [apartado legal](15-apartado-legal-publico.md) ya distingue esos recorridos.
- La definición capturada de sistema de recomendación incluye proponer o priorizar información y determinar orden relativo o relevancia, incluso tras una búsqueda. La revisión jurídica debe examinar el listado y sus promociones, además de la ampliación opcional B15; diferir B15 no permite dar por resuelto todo ese análisis.
- Publicidad, priorización, perfil público y elaboración de perfiles no son términos intercambiables. Los artículos 26 y 27 capturados separan publicidad y recomendación; las categorías especiales de datos exigen análisis concreto. No se toma el consentimiento como solución automática para combinar gustos físicos y anuncios promocionados.
- El artículo 28 capturado distingue protección de menores y minimización, sin imponer tratamiento adicional de datos para averiguar edad. No prueba que una declaración de mayoría de edad sea suficiente ni autoriza biometría o recopilación adicional en el proyecto.

Se conservan el [contrato14§6.1](14-contrato-funcional-v1.md#61-recomendaciones-físicas-opcionales), las decisiones separadas de edad/términos, cookies y personalización, y B15 opcional. Cookies propias sin cuenta y evaluación de almacenamiento privado cifrado con cuenta siguen siendo dirección de diseño, con catálogo, bases, claves, conservación y elección entre base de datos y objetos pendientes. No se implementa personalización, seguimiento o inferencia.

## Corrección concreta del apartado legal

El principal leyó completo el documento15. Su resumen de envío aún enumeraba servicios y tarifas pese al perfil romántico ya consolidado. Se sustituyó una sola línea por resumen de perfil, fotos, contactos y ubicación, sin catálogo profesional ni tarifas por servicios, de acuerdo con el contrato14. Se preservan copia íntegra previa, hashes y diff en `b00-310-legal-public-correction.json` y `b00-310-legal-public-before.md`.

La corrección afecta a la especificación, no a textos runtime, nuevas páginas, aceptación jurídica o controles ya aceptados. No modifica condiciones de publicación ni reabre el alfa o B07. La representación autorizada y los mecanismos de denuncia y derechos se conservan.

## Estado residual

Quedan 56 fuentes de arquitectura, seis legales, dos de moderación y tres comerciales. Los originales judiciales pendientes y límites de otras capturas siguen abiertos. Se mantiene el alcance íntegro del contrato: la lectura normativa es una parte de B00, no su sustituto ni el cierre del roadmap.

Sin pruebas funcionales, cargas, servicios, publicaciones o proveedores nuevos. Sólo comprobaciones documentales y del grafo. Cuatro lectores nativos de sólo lectura, sin nuevas invocaciones Claude V1 y con su consumo histórico conservado. Corte anterior: [conciliación268](268-conciliacion-lssi-marketing-b00-20261023.md).
