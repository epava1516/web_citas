# MOD08: siguiente vía tras baseline escalar

Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

## 1 · user · authorization

UTC: 2026-10-11T13:59:56.294543+00:00

```text
Autorización previa del usuario 2026-10-11, persistente para esta deliberación: «Sí, excepción solo para deliberar». Claude CLI exclusivamente revisor sin herramientas ni edición, con registro de consumo. No amplía permiso a implementación delegada. Solicitud actual: «A deliverar pues, como proceder».
```

## 2 · codex · context

UTC: 2026-10-11T13:59:56.572938+00:00

```text
Deliberación sobre el siguiente experimento, no implementación. HEAD 7e04016d; código productivo intacto. Todos los datos sintéticos. Contrato: preservar autoridad y frescura, auditoría, purga, SELECT recientes; nunca cachear autoridad/cadena. PostgreSQL real obligatorio. MOD08 completo/capacidad contractual sigue pausado. No inferir p95 de tres controles.
Última campaña: 10 PASS real PG/TCP, 1208 fuentes verificadas, retirada propia completa. Fixture 1500 revisiones, selección 16MiB, 64 POST previos =548 eventos. Inspección de cuatro páginas añade cuatro lecturas/ocho eventos con commit comprobado. Dos workers sync calientes, clones equivalentes.
Tres requests control/spans/control: TCP1645/1664/1620ms; CPU911/939/883ms. Primera tanda del mismo arnés (falló después del HTTP por nombre ocultando dict en microbenchmark) controles801/769ms CPU428/420. No candidata/productivo cambiado, causa del factor2 desconocida; PIDs distintos, GC distinto. No atribuirlo a una corrección ni a frecuencia CPU sin medir.
Spans ocho consumidores: source_copy1 wall405.580/CPU251.397ms; compile_coverage1 incl42.851/42.837, excl31.289/31.275; project_selected2 incl64.789/64.789 (una dentrocompile, otra fuera); coverage_page4 .414/.407. Cuatro consumidores restantes no observados. No sumar inclusivos.
Conteo independiente sin tiempos: compile_coverage1502 invocaciones externas scalar_fields ->27163 hojas; cuatro páginas108hojas. No101755dicts: cifra profiler incluía reanudaciones recursivas. Corpus1502filas, profundidad3.
A/A código ORIGINAL en padre después de pararGunicorn,20muestras2warmups: conjuntosrutas23.059ms; conteo21.001;4501pointer_value6.305ms. GC0; resultados idénticos. Incluye consumo/construcciónset, no ahorro esperado ni cota request. Corpus ancho/profundo/escapes y APIoriginal cubiertos. DecisiónCodex: cerrar pista reescritura escalar por impacto modesto, ninguna variante preparada.
Previo cProfile enormemente intrusivo: TCPcontrol812/797 vsprofile1883ms CPU429/426 vs1564; no usar sus tiempos como presupuesto limpio. Catálogos Category/Service/Municipality residual estimado5.4ms, rama values primitives ya cerrada. SQL inline lector descartado:20porbrazo med798vs790,p95820vs829ms; no ganador. Pipeline cadenas/firma/atestación requieren frescura; no reaplicar memo autoridad ni precarga de campos purgables.
Código relevante real:
rights_copy_revision_batches.batches: records.iterator(chunk_size=size), list(islice(...size)); idsRawSQL unnest uuid[]; por lote CINCO querysets categories(order slug),services(slug),travelareas(code),rates(pk),photos(select_related blob ordercreated_at,pk); agrupación por copy_parent y setattr copy_categories/...; yield frombatch.
source_copy: revisions.select_for_update(of=('self',)).defer('search_document').select_related('municipality','postal_code','zone').order_by('created_at','pk'); batches; construye dict por revisión incluyendo title/description/description_alternative, contacts=contact_data(person,revision), images=image_inventory(revision), listas categorías/servicios/áreas/rates, sujeto/perfil. No sabemos reparto del coste en subfunciones.
inspection_source: BEFORErows source_fingerprint; source_copy; digest=fingerprint(canonical_bytes(source)); contexto restringido a conexiónatomic/scope. Al salir recalcula hash fuente enmemoria (detectamutaciones) y source_fingerprint fresco; si cambió compara freshsourcehash. No quitar estas comprobaciones.
inspect_batch mantiene operaciónsource/projection/summarycache local, sólo1compilepara4pages; record/inspect_page repiten autorización y validate_approved_assessment frescas. Costes request no cubiertos íntegros por ocho spans.
Mi opinión Codex: no perseguir23mscomo solución de segundos. La duplicación de controles/CPU entre tandas requiere caracterizar estabilidad antes de candidatos pequeños. source_copy251msCPU es perímetro mayor pero incluye consultas/materialización y construcción: no afirmarORMni redundancia. Un siguiente diagnóstico sólo merece ejecución si puede producir candidata concreta y criterio de descarte; evitar bucle interminable de profiling. Podría hacer controlesA/A intercalados y pocos spans de fases grandes existentes, sin SQL/nexthooks; constatar backend nativo efectivo porworker, estadoGC/host fuera del reloj. No alterar máquina ni recursos globales.
Pregunta: critica esta opinión y elige UNA siguiente vía finita. ¿Estabilidad primero, source_copy, fases de validación u otra? Pide sólo datos decisivos que no tenemos. Da secuencia mínima, métricas, límite de ejecuciones, señal necesaria para candidata productiva y salida si no aparece. No inventes semántica ni porcentajes; no prometer2s. No herramientas ni edición. Máximo650palabras.

```

## 3 · codex · request

UTC: 2026-10-11T13:59:56.856393+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Deliberación sobre el siguiente experimento, no implementación. HEAD 7e04016d; código productivo intacto. Todos los datos sintéticos. Contrato: preservar autoridad y frescura, auditoría, purga, SELECT recientes; nunca cachear autoridad/cadena. PostgreSQL real obligatorio. MOD08 completo/capacidad contractual sigue pausado. No inferir p95 de tres controles.
Última campaña: 10 PASS real PG/TCP, 1208 fuentes verificadas, retirada propia completa. Fixture 1500 revisiones, selección 16MiB, 64 POST previos =548 eventos. Inspección de cuatro páginas añade cuatro lecturas/ocho eventos con commit comprobado. Dos workers sync calientes, clones equivalentes.
Tres requests control/spans/control: TCP1645/1664/1620ms; CPU911/939/883ms. Primera tanda del mismo arnés (falló después del HTTP por nombre ocultando dict en microbenchmark) controles801/769ms CPU428/420. No candidata/productivo cambiado, causa del factor2 desconocida; PIDs distintos, GC distinto. No atribuirlo a una corrección ni a frecuencia CPU sin medir.
Spans ocho consumidores: source_copy1 wall405.580/CPU251.397ms; compile_coverage1 incl42.851/42.837, excl31.289/31.275; project_selected2 incl64.789/64.789 (una dentrocompile, otra fuera); coverage_page4 .414/.407. Cuatro consumidores restantes no observados. No sumar inclusivos.
Conteo independiente sin tiempos: compile_coverage1502 invocaciones externas scalar_fields ->27163 hojas; cuatro páginas108hojas. No101755dicts: cifra profiler incluía reanudaciones recursivas. Corpus1502filas, profundidad3.
A/A código ORIGINAL en padre después de pararGunicorn,20muestras2warmups: conjuntosrutas23.059ms; conteo21.001;4501pointer_value6.305ms. GC0; resultados idénticos. Incluye consumo/construcciónset, no ahorro esperado ni cota request. Corpus ancho/profundo/escapes y APIoriginal cubiertos. DecisiónCodex: cerrar pista reescritura escalar por impacto modesto, ninguna variante preparada.
Previo cProfile enormemente intrusivo: TCPcontrol812/797 vsprofile1883ms CPU429/426 vs1564; no usar sus tiempos como presupuesto limpio. Catálogos Category/Service/Municipality residual estimado5.4ms, rama values primitives ya cerrada. SQL inline lector descartado:20porbrazo med798vs790,p95820vs829ms; no ganador. Pipeline cadenas/firma/atestación requieren frescura; no reaplicar memo autoridad ni precarga de campos purgables.
Código relevante real:
rights_copy_revision_batches.batches: records.iterator(chunk_size=size), list(islice(...size)); idsRawSQL unnest uuid[]; por lote CINCO querysets categories(order slug),services(slug),travelareas(code),rates(pk),photos(select_related blob ordercreated_at,pk); agrupación por copy_parent y setattr copy_categories/...; yield frombatch.
source_copy: revisions.select_for_update(of=('self',)).defer('search_document').select_related('municipality','postal_code','zone').order_by('created_at','pk'); batches; construye dict por revisión incluyendo title/description/description_alternative, contacts=contact_data(person,revision), images=image_inventory(revision), listas categorías/servicios/áreas/rates, sujeto/perfil. No sabemos reparto del coste en subfunciones.
inspection_source: BEFORErows source_fingerprint; source_copy; digest=fingerprint(canonical_bytes(source)); contexto restringido a conexiónatomic/scope. Al salir recalcula hash fuente enmemoria (detectamutaciones) y source_fingerprint fresco; si cambió compara freshsourcehash. No quitar estas comprobaciones.
inspect_batch mantiene operaciónsource/projection/summarycache local, sólo1compilepara4pages; record/inspect_page repiten autorización y validate_approved_assessment frescas. Costes request no cubiertos íntegros por ocho spans.
Mi opinión Codex: no perseguir23mscomo solución de segundos. La duplicación de controles/CPU entre tandas requiere caracterizar estabilidad antes de candidatos pequeños. source_copy251msCPU es perímetro mayor pero incluye consultas/materialización y construcción: no afirmarORMni redundancia. Un siguiente diagnóstico sólo merece ejecución si puede producir candidata concreta y criterio de descarte; evitar bucle interminable de profiling. Podría hacer controlesA/A intercalados y pocos spans de fases grandes existentes, sin SQL/nexthooks; constatar backend nativo efectivo porworker, estadoGC/host fuera del reloj. No alterar máquina ni recursos globales.
Pregunta: critica esta opinión y elige UNA siguiente vía finita. ¿Estabilidad primero, source_copy, fases de validación u otra? Pide sólo datos decisivos que no tenemos. Da secuencia mínima, métricas, límite de ejecuciones, señal necesaria para candidata productiva y salida si no aparece. No inventes semántica ni porcentajes; no prometer2s. No herramientas ni edición. Máximo650palabras.

```

## 4 · claude · opinion

UTC: 2026-10-11T14:00:42.775644+00:00

```text
# Crítica y siguiente vía

## Crítica a la opinión de Codex

**Coincido en:**
- Cerrar la reescritura escalar. Los 23 ms del A/A incluyen construcción de conjuntos y no acotan el request.
- No hay ahorro demostrado.
- La caracterización de estabilidad debe preceder a cualquier candidata pequeña.

**Matices:**

1. **La estabilidad debe funcionar como compuerta, no como estudio.** Hay que fijar antes de ejecutar qué dispersión se considera aceptable. Si no se fija, el A/A se convierte en el bucle que se quiere evitar.

2. **Los spans se midieron en el régimen lento** (control 1645 ms). No sabemos si source_copy escala igual en el régimen de unos 800 ms.
   - Hecho: wall 405,6 ms frente a CPU 251,4 ms, es decir, unos 154 ms fuera de CPU.
   - Hipótesis: espera de PostgreSQL o red. No está medido.

3. **El hueco mayor es la cobertura del request.** Los ocho spans no cubren el request completo, y cuatro consumidores no se han observado. Sin cobertura no se puede afirmar que source_copy sea el perímetro dominante, sólo el mayor de los observados.

4. **Contraejemplo a "A/A intercalado basta":** si el factor 2 depende del estado acumulado de la base de datos (tuplas muertas, estadísticas, tamaño de tablas tras 548 eventos y las retiradas) y no del host, un fixture recién creado puede parecer estable y ocultar la causa. Esto es una hipótesis, no un hallazgo. Por eso conviene registrar ese estado, en sólo lectura y fuera del reloj.

## Vía elegida

**Estabilidad como compuerta, seguida de cobertura por fases grandes existentes en el mismo arnés.** No se abre source_copy por dentro salvo que la compuerta y la cobertura lo justifiquen.

## Datos decisivos que faltan

- ¿El régimen es bimodal, presenta deriva por orden, o se separa por worker/PID, ciclos GC o estado de PostgreSQL?
- ¿Qué fracción del wall y del CPU del request explican las fases de primer nivel, en tiempos exclusivos?
- Backend nativo efectivo por worker, verificado y no supuesto.

## Secuencia mínima

**0. Comprobaciones frescas sin cachear:**
- HEAD 7e04016d y árbol limpio.
- PostgreSQL real por TCP.
- Fixture recreado con el mismo script y retirada previa verificada.
- Fuera del reloj:
  - backend nativo y PID por worker;
  - contadores GC antes y después;
  - RSS;
  - carga del host (sólo lectura);
  - tamaños y tuplas muertas de las tablas implicadas, y último autovacuum/analyze.

**1. Bloque A, sólo controles:**
- Alternar los dos workers.
- Registrar orden, wall TCP y CPU de proceso por request.
- Límite: 20 requests en una sola ejecución.

**2. Compuerta:**
- Se considera estable si no hay tendencia por orden ni separación por worker, PID, GC o estado de base de datos.
- Además, la dispersión intra-bloque debe ser menor que el efecto mínimo de interés, que el equipo fija numéricamente antes de ejecutar. Yo no propongo la cifra.

**3. Bloque B, sólo si pasa la compuerta:**
- 5 tripletas control/fases/control.
- Spans exclusivos sólo en fases de primer nivel de inspect_batch:
  - autorización y validate_approved_assessment;
  - BEFORE fingerprint;
  - source_copy;
  - canonical_bytes y digest;
  - compile;
  - páginas;
  - recomprobación final;
  - commit.
- Sin hooks SQL.
- Las comprobaciones de frescura se miden, no se tocan.
- Métrica: cobertura = suma de exclusivos / wall del request, más el reparto wall/CPU por fase.

**4. Bloque C, opcional, una sola vez:**
- Sólo si una fase domina claramente según el criterio predeclarado.
- 5 tripletas con subfases de esa fase. Para source_copy:
  - iteración de batches y cinco querysets;
  - contact_data;
  - image_inventory;
  - construcción de dict.

**Límite total:** 3 ejecuciones, como máximo 55 requests HTTP. Sin repeticiones "para confirmar" fuera de este presupuesto.

## Señal necesaria para candidata productiva

Las cuatro condiciones a la vez:
- Una subfase concreta con coste exclusivo atribuible y estable entre tripletas.
- Un mecanismo nombrable que no toque autoridad, cadena, firma, frescura, auditoría ni purga. Ejemplos de forma, no propuestas: trabajo repetido por lote demostrado por conteo, o materialización de campos no usados demostrada.
- Un A/B intercalado predeclarado con la misma compuerta.
- Ninguna afirmación sobre p95 contractual.

## Salidas

- **Falla la compuerta sin explicación:** se detiene la pista de optimización. La inestabilidad se registra como hallazgo y se abre un ticket separado de entorno, sin alterar la máquina.
- **Falla con correlación** (worker, GC o estado de base de datos): se documenta como hipótesis con su evidencia. No se generan candidatas de código.
- **Pasa la compuerta, pero la cobertura no explica el request o ninguna fase domina:** se cierra la búsqueda a nivel de código para este perímetro y MOD08 sigue pausado.
- **Bloque C sin mecanismo nombrable:** se cierra. No se abre un cuarto bloque.

Esto es una opinión, no un PASS ni una autorización.
```

## 5 · codex · request

UTC: 2026-10-11T14:00:56.298624+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Deliberación sobre el siguiente experimento, no implementación. HEAD 7e04016d; código productivo intacto. Todos los datos sintéticos. Contrato: preservar autoridad y frescura, auditoría, purga, SELECT recientes; nunca cachear autoridad/cadena. PostgreSQL real obligatorio. MOD08 completo/capacidad contractual sigue pausado. No inferir p95 de tres controles.
Última campaña: 10 PASS real PG/TCP, 1208 fuentes verificadas, retirada propia completa. Fixture 1500 revisiones, selección 16MiB, 64 POST previos =548 eventos. Inspección de cuatro páginas añade cuatro lecturas/ocho eventos con commit comprobado. Dos workers sync calientes, clones equivalentes.
Tres requests control/spans/control: TCP1645/1664/1620ms; CPU911/939/883ms. Primera tanda del mismo arnés (falló después del HTTP por nombre ocultando dict en microbenchmark) controles801/769ms CPU428/420. No candidata/productivo cambiado, causa del factor2 desconocida; PIDs distintos, GC distinto. No atribuirlo a una corrección ni a frecuencia CPU sin medir.
Spans ocho consumidores: source_copy1 wall405.580/CPU251.397ms; compile_coverage1 incl42.851/42.837, excl31.289/31.275; project_selected2 incl64.789/64.789 (una dentrocompile, otra fuera); coverage_page4 .414/.407. Cuatro consumidores restantes no observados. No sumar inclusivos.
Conteo independiente sin tiempos: compile_coverage1502 invocaciones externas scalar_fields ->27163 hojas; cuatro páginas108hojas. No101755dicts: cifra profiler incluía reanudaciones recursivas. Corpus1502filas, profundidad3.
A/A código ORIGINAL en padre después de pararGunicorn,20muestras2warmups: conjuntosrutas23.059ms; conteo21.001;4501pointer_value6.305ms. GC0; resultados idénticos. Incluye consumo/construcciónset, no ahorro esperado ni cota request. Corpus ancho/profundo/escapes y APIoriginal cubiertos. DecisiónCodex: cerrar pista reescritura escalar por impacto modesto, ninguna variante preparada.
Previo cProfile enormemente intrusivo: TCPcontrol812/797 vsprofile1883ms CPU429/426 vs1564; no usar sus tiempos como presupuesto limpio. Catálogos Category/Service/Municipality residual estimado5.4ms, rama values primitives ya cerrada. SQL inline lector descartado:20porbrazo med798vs790,p95820vs829ms; no ganador. Pipeline cadenas/firma/atestación requieren frescura; no reaplicar memo autoridad ni precarga de campos purgables.
Código relevante real:
rights_copy_revision_batches.batches: records.iterator(chunk_size=size), list(islice(...size)); idsRawSQL unnest uuid[]; por lote CINCO querysets categories(order slug),services(slug),travelareas(code),rates(pk),photos(select_related blob ordercreated_at,pk); agrupación por copy_parent y setattr copy_categories/...; yield frombatch.
source_copy: revisions.select_for_update(of=('self',)).defer('search_document').select_related('municipality','postal_code','zone').order_by('created_at','pk'); batches; construye dict por revisión incluyendo title/description/description_alternative, contacts=contact_data(person,revision), images=image_inventory(revision), listas categorías/servicios/áreas/rates, sujeto/perfil. No sabemos reparto del coste en subfunciones.
inspection_source: BEFORErows source_fingerprint; source_copy; digest=fingerprint(canonical_bytes(source)); contexto restringido a conexiónatomic/scope. Al salir recalcula hash fuente enmemoria (detectamutaciones) y source_fingerprint fresco; si cambió compara freshsourcehash. No quitar estas comprobaciones.
inspect_batch mantiene operaciónsource/projection/summarycache local, sólo1compilepara4pages; record/inspect_page repiten autorización y validate_approved_assessment frescas. Costes request no cubiertos íntegros por ocho spans.
Mi opinión Codex: no perseguir23mscomo solución de segundos. La duplicación de controles/CPU entre tandas requiere caracterizar estabilidad antes de candidatos pequeños. source_copy251msCPU es perímetro mayor pero incluye consultas/materialización y construcción: no afirmarORMni redundancia. Un siguiente diagnóstico sólo merece ejecución si puede producir candidata concreta y criterio de descarte; evitar bucle interminable de profiling. Podría hacer controlesA/A intercalados y pocos spans de fases grandes existentes, sin SQL/nexthooks; constatar backend nativo efectivo porworker, estadoGC/host fuera del reloj. No alterar máquina ni recursos globales.
Pregunta: critica esta opinión y elige UNA siguiente vía finita. ¿Estabilidad primero, source_copy, fases de validación u otra? Pide sólo datos decisivos que no tenemos. Da secuencia mínima, métricas, límite de ejecuciones, señal necesaria para candidata productiva y salida si no aparece. No inventes semántica ni porcentajes; no prometer2s. No herramientas ni edición. Máximo650palabras.


Respuesta Claude (opinión no evidencia):
# Crítica y siguiente vía

## Crítica a la opinión de Codex

**Coincido en:**
- Cerrar la reescritura escalar. Los 23 ms del A/A incluyen construcción de conjuntos y no acotan el request.
- No hay ahorro demostrado.
- La caracterización de estabilidad debe preceder a cualquier candidata pequeña.

**Matices:**

1. **La estabilidad debe funcionar como compuerta, no como estudio.** Hay que fijar antes de ejecutar qué dispersión se considera aceptable. Si no se fija, el A/A se convierte en el bucle que se quiere evitar.

2. **Los spans se midieron en el régimen lento** (control 1645 ms). No sabemos si source_copy escala igual en el régimen de unos 800 ms.
   - Hecho: wall 405,6 ms frente a CPU 251,4 ms, es decir, unos 154 ms fuera de CPU.
   - Hipótesis: espera de PostgreSQL o red. No está medido.

3. **El hueco mayor es la cobertura del request.** Los ocho spans no cubren el request completo, y cuatro consumidores no se han observado. Sin cobertura no se puede afirmar que source_copy sea el perímetro dominante, sólo el mayor de los observados.

4. **Contraejemplo a "A/A intercalado basta":** si el factor 2 depende del estado acumulado de la base de datos (tuplas muertas, estadísticas, tamaño de tablas tras 548 eventos y las retiradas) y no del host, un fixture recién creado puede parecer estable y ocultar la causa. Esto es una hipótesis, no un hallazgo. Por eso conviene registrar ese estado, en sólo lectura y fuera del reloj.

## Vía elegida

**Estabilidad como compuerta, seguida de cobertura por fases grandes existentes en el mismo arnés.** No se abre source_copy por dentro salvo que la compuerta y la cobertura lo justifiquen.

## Datos decisivos que faltan

- ¿El régimen es bimodal, presenta deriva por orden, o se separa por worker/PID, ciclos GC o estado de PostgreSQL?
- ¿Qué fracción del wall y del CPU del request explican las fases de primer nivel, en tiempos exclusivos?
- Backend nativo efectivo por worker, verificado y no supuesto.

## Secuencia mínima

**0. Comprobaciones frescas sin cachear:**
- HEAD 7e04016d y árbol limpio.
- PostgreSQL real por TCP.
- Fixture recreado con el mismo script y retirada previa verificada.
- Fuera del reloj:
  - backend nativo y PID por worker;
  - contadores GC antes y después;
  - RSS;
  - carga del host (sólo lectura);
  - tamaños y tuplas muertas de las tablas implicadas, y último autovacuum/analyze.

**1. Bloque A, sólo controles:**
- Alternar los dos workers.
- Registrar orden, wall TCP y CPU de proceso por request.
- Límite: 20 requests en una sola ejecución.

**2. Compuerta:**
- Se considera estable si no hay tendencia por orden ni separación por worker, PID, GC o estado de base de datos.
- Además, la dispersión intra-bloque debe ser menor que el efecto mínimo de interés, que el equipo fija numéricamente antes de ejecutar. Yo no propongo la cifra.

**3. Bloque B, sólo si pasa la compuerta:**
- 5 tripletas control/fases/control.
- Spans exclusivos sólo en fases de primer nivel de inspect_batch:
  - autorización y validate_approved_assessment;
  - BEFORE fingerprint;
  - source_copy;
  - canonical_bytes y digest;
  - compile;
  - páginas;
  - recomprobación final;
  - commit.
- Sin hooks SQL.
- Las comprobaciones de frescura se miden, no se tocan.
- Métrica: cobertura = suma de exclusivos / wall del request, más el reparto wall/CPU por fase.

**4. Bloque C, opcional, una sola vez:**
- Sólo si una fase domina claramente según el criterio predeclarado.
- 5 tripletas con subfases de esa fase. Para source_copy:
  - iteración de batches y cinco querysets;
  - contact_data;
  - image_inventory;
  - construcción de dict.

**Límite total:** 3 ejecuciones, como máximo 55 requests HTTP. Sin repeticiones "para confirmar" fuera de este presupuesto.

## Señal necesaria para candidata productiva

Las cuatro condiciones a la vez:
- Una subfase concreta con coste exclusivo atribuible y estable entre tripletas.
- Un mecanismo nombrable que no toque autoridad, cadena, firma, frescura, auditoría ni purga. Ejemplos de forma, no propuestas: trabajo repetido por lote demostrado por conteo, o materialización de campos no usados demostrada.
- Un A/B intercalado predeclarado con la misma compuerta.
- Ninguna afirmación sobre p95 contractual.

## Salidas

- **Falla la compuerta sin explicación:** se detiene la pista de optimización. La inestabilidad se registra como hallazgo y se abre un ticket separado de entorno, sin alterar la máquina.
- **Falla con correlación** (worker, GC o estado de base de datos): se documenta como hipótesis con su evidencia. No se generan candidatas de código.
- **Pasa la compuerta, pero la cobertura no explica el request o ninguna fase domina:** se cierra la búsqueda a nivel de código para este perímetro y MOD08 sigue pausado.
- **Bloque C sin mecanismo nombrable:** se cierra. No se abre un cuarto bloque.

Esto es una opinión, no un PASS ni una autorización.

Codex: Contrasta especialmente si estabilidad se convierte en trabajo infinito. Existe PHASE_TARGETS con source,validate_assessment,record,canonical_bytes,fingerprint y otras fases, pero activar todo y SQLwrapper a la vez sería intrusivo. Falta comprobar kernel efectivo EN worker (padre sí validado). No tomar2workers como control pareado. Elige plan único finito, distingue condiciones de ejecución y descarte. Si identificas candidata, exige datos específicos antes de implementarla. Máximo500palabras.
```

## 6 · notebook · error

UTC: 2026-10-11T14:00:59.807679+00:00

```text
Empty answer; inspect raw artifact
```

## 7 · codex · request

UTC: 2026-10-11T14:01:45.443971+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Solicito segunda opinión sobre siguiente experimento de optimización MOD08. Datos nuevos aportados aquí, no asumir que están en fuentes. Código productivo intacto. PostgreSQL real/sintético. No cachear autoridad/cadena ni adelantar lecturas purgables; preservar firmas,auditoría,autorización,frescura. Contrato general sigue pausado.
Campaña10PASS:1500revisiones, selección16MiB,548eventosprevios;cadaPOSTinspectbatchcuatropagesagrega4reads8events. Controles TCP1645/1620ms CPU911/883; en tanda previa del mismo arnés TCP801/769CPU428/420. Causa factor2desconocida; ningún cambio productivo. Dos workers calientes, distintosPID,GCdistinto. No p95contrato.
Spanssource_copy1 wall405.6CPU251.4ms; compile1incl42.9CPU42.8/excl31.3;project_selected2wall64.8CPU64.8(una anidada);pages4wall.414. No coberturatotal. Conteo27163hojas, no101755dicts. A/Aoriginal20muestras rutas23ms,4501punteros6.3ms, no ahorro ni cotarequest. Cerramos reescrituraescalar. cProfile previo triplicabaCPU. SQLinline descartadocolaempeora. PrimitivosCategory/Service/Municipality descartadosimpacto~5ms, no reabrir.
source_copy incluyeconsulta revisiones bloqueadas,5querysetsrelacionesporbatch,materialización,dictscontact_data/image_inventory; coste interno no separado. inspection_source fingerprintsantes/después yhashcanonicalmantener.
OpiniónCodex: compuerta estabilidad seguida de pocasfases grandes, antesdecualquiercandidata. Claude coincidey propone20controles,luego5tripletascontrol/fases/controlyopcionales5tripletassubfases;salirsinmecanismoestable, sincuartobloque. Reclama backendnativoefectivoporworker,GC,RSS,cargahost,estadísticasPG sólolecturafuera reloj. No atribuir esperawall-CPUared.
CorreccionesCodex: árbolYAcontienecambiosusuario/documentos/tests, preservarcomparandosnapshot/hash (noexigirtreelimpio). CPUthread_time delhilo WSGI, noproceso. No sumarspaninclusivos. No afirmarschedulingworkerporalternarPOST. Contextmanagers/generadores nosecronometranenvolviendocreación;medirbloquesrealesconpocos límites.45o50HTTPno55(20+15+15=50). Invasiónspans requiere controles,no restaroverheadcausal.
Propuesta concretaCodex: primerbloque20controles, servidorunworkersync para quitarconfusiónPID declarandocambiodescenario(no compararabsolutosprevios).20cloneshistorialidéntico;warmupsdescartados;fijarporadelantadoP90-P10≤10%mediana,derivamedianasprimer/últimocuarto≤10%,dos umbralesheurísticosnoaceptación. RegistrarCPU/GC/backendseal/codeSHA/cargahostlecturafuera reloj. Si falla,cerrarconvariaciónsinatribuircausa. Si pasa,5tripletascontrol/pocasfases/control;presupuesto50POSTmáximo incluídoopcionaltercerbloque,preparación/warmupscontabilizadosaparte. No datosreales ni modificarhost. Medirperímetroscompletosconresidualsinforzarcobertura100%;no redefinirfrescura. Sóloabrirsubfase si mecanismo específico evitable ycomparable. No publicarniimplementaroptimizaciónahora.
CriticaUNplanfinito. ¿Prioridadcorrecta? Qué dato cambiaríaladecisión,quédescartar? No inventesSQLniinmutabilidad. Máximo450palabras. La consulta anterior extensa fallóinvalidrequest; ésta es reducción deliberada, no retryautomático.

```

## 8 · notebook · opinion

UTC: 2026-10-11T14:02:28.842141+00:00

```text
### Evaluación del experimento de optimización MOD08

#### 1. Clasificación del estado del experimento

*   **Hechos medidos:**
    *   Incremento x2 en tiempos de CPU y TCP (883–911 ms CPU vs. 420–428 ms en la tanda previa) sin cambios en el código productivo, ejecutando en dos workers calientes (PIDs distintos y comportamiento de GC divergente).
    *   El span `source_copy` concentra el mayor consumo relativo (wall 405.6 ms / CPU 251.4 ms).
    *   Descarte experimental previo de reescrituras escalares (A/A con 6.3 ms en punteros), `cProfile` (triplicaba CPU) y SQL inline (empeoraba la cola).
*   **Hipótesis:**
    *   La variabilidad observada no es una regresión de código, sino ruido de entorno provocado por la alternancia entre PIDs, contención en el host o ciclos de GC.
*   **Evidencia faltante:**
    *   Desglose del costo interno de `source_copy` (proporción entre I/O de la consulta de revisiones bloqueadas, evaluación de los 5 querysets de relaciones y la materialización de diccionarios).
    *   Métricas del entorno capturadas fuera de reloj (RSS, consumo de memoria por PID, pausado de GC y estadísticas de PostgreSQL).

---

#### 2. Crítica al plan propuesto

La **prioridad es correcta**: establecer la compuerta de estabilidad mediante un único worker *sync* y 20 ejecuciones de control antes de probar cualquier fase de modificación es la decisión metodológica adecuada para aislar el ruido del arnés.

*   **Qué dato cambiaría la decisión:**
    1.  **Inestabilidad en el bloque inicial:** Si las 20 muestras del control sobrepasan el umbral (\\(\text{P90}-\text{P10} > 10\%\\) de la mediana o deriva de medianas \\(> 10\%\\)), la decisión finita debe ser **cerrar la campaña MOD08** registrando la variación sin atribuir causas ni ejecutar fases.
    2.  **Inseparabilidad del costo en `source_copy`:** Si al desglosar `source_copy` se evidencia que el tiempo de CPU corresponde a la materialización ineludible impuesta por el contrato de integridad y huellas, se descarta la optimización.

*   **Qué descartar del plan:**
    1.  **Medición invasiva mediante *spans* anidados:** Descartar la adición de envoltorios o *context managers* sobre generadores o creación de objetos que introduzcan sobrecostes causales o distorsionen el `thread_time` del hilo WSGI.
    2.  **Tercer bloque de subfases:** Eliminar la opción de las 5 tripletas de subfases a menos que la fase principal muestre una reducción clara que supere holgadamente el margen de dispersión de los controles.

---

#### 3. Dictamen y decisión recomendada

Proceder únicamente con la **fase 1 de la propuesta**: aislar el escenario a un servidor de un solo worker *sync* y ejecutar las 20 muestras de control con verificación estricta de umbrales (\\(\le 10\%\\)). Si la compuerta no se supera, declarar el experimento inconcluyente y concluir la intervención en MOD08.

💡 ¿Deseas que revisemos los parámetros de registro de telemetría fuera de reloj (GC, RSS y estado de PG) para asegurar que no afecten la medición del hilo WSGI?
```

## 9 · codex · decision

UTC: 2026-10-11T14:03:33.017407+00:00

```text
Decisión Codex — siguiente vía, 2026-10-11

Se cierra la deliberación, no se ejecuta una nueva campaña ni se modifica producto en este turno. Claude y NotebookLM son opiniones, no pruebas. Claude responde en turno1; Notebook turno2 inválido conservado, consulta reducida deliberada turno3 válida. ConsumoClaude registrado. No consenso equivale a PASS.

Prioridad: un único bloque de estabilidad A/A de 20 POST medidos, antes de optimizar. No continuar reescritura escalar ni variantes SQL descartadas. La diferencia ~0.8/~1.6s y CPU~0.42/~0.9s carece de causa demostrada.

Plan ejecutable posterior:
1. Preservar modificaciones previas y congelar manifiesto exacto de fuentes, entorno/dependencias y fixture. No exigir árbol limpio ni modificar archivos durante runner. PostgreSQL/Redis privados reales, rolruntime separado, datos sintéticos, clon idéntico por request, commit normal y comprobación independiente de cuatro lecturas/ocho eventos. Mismo historial548eventos/1500revisiones/16MiB. Retirada comprobada al terminar.
2. Un único worker Gunicorn sync para eliminar mezcla de PIDs; escenario diagnóstico distinto de dosworkers y de capacidad contractual. Sin comparar absolutos como regresión o mejora. Fijar PID y comprobar backend nativo sellado efectivo desde ese worker fuera del cronometraje, sin dar por suficiente la validación del padre. Dos warmups reales descartados, verificados y contabilizados aparte. No refrescar/cambiar recursos globales ni deshabilitar/forzar GC.
3. Veinte controles secuenciales sobre veinte clones equivalentes, sin cProfile, SQLhooks, per-next ni nuevos spans internos. TCP completo y wall/CPUdelhiloWSGI con límites definidos, separar cierreWSGI que puede terminar después de cuerpoTCP. Registrar orden/PID y estadísticasGC. RSS/cargahost/metadatosPG sólolectura antes/después de bloques, fuera del reloj; sus correlaciones no prueban causalidad.
4. Compuerta predeclarada: cuantiles con interpolación lineal reproducible; P90-P10 <=10%medianaTCP y <=10%medianaCPU; diferencia absoluta entre medianas primeras5/últimas5 <=10%mediana del mismo indicador, paraTCPyCPU. Son heurísticas de reproducibilidad de ESTEcontrol, no umbral contractual ni prueba estadística de ausencia de bimodalidad. Publicar muestras, rangos, dispersión, deriva y cualquier anomalía/backend/PID/fuente que invalide la campaña. Límite20medidas+2warmups; ningún rerun automático por querer pasar.
5. Si falla o se invalida: terminar ese diagnóstico como variable/inconcluyente, sin candidata de rendimiento ni causa atribuida. No declarar cerrado o fallido todoMOD08. Si pasa: decidir con datos un segundo bloque independiente de pocas fases grandes existentes, concontrolesadyacentes y tiempos exclusivos sólorespectoahijosobservados. No ejecutar automáticamente bloquesB/C de Claude. No cronometraje de creación de generadores/contextmanagers como ejecución. No sumar inclusivos, no restaroverhead como ganancia.

Criterio para futura candidata: mecanismo concreto de trabajo evitable localizado por medición y conteo, semántica/frescura conservadas por código y pruebas concurrentes, comparaciónA/B independiente que supere ruido observado. No exigir una reducción previa a instrumentos que no cambian producto. No prometer2s/5s ni convertir20controlesenp95contractual.

Correcciones: source_copy es mayorentreconsumidoresobservados, no dominante demostrada delrequest. A/Aescalar no fue comparaciónoptimizada. Variación puede proceder de entorno/backend/GC u otros factores, no demostrado. No pausarGC. Spans anidados no inválidosporprincipio, requieren límites/costes claros. Claude propuso20+15+15=50medidas,no55, pero no se adopta ese presupuesto amplio. Notebook confundió medición conreducción y cierre de diagnóstico con cierre general; rechazado. ModeloNotebook desconocido; sin fuentes añadidas/eliminadas.

```
