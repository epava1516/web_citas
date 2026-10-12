# MOD08 mejora parcial: rutas sin diccionarios de valores

Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

## 1 · user · authorization

UTC: 2026-10-11T14:44:37.156281+00:00

```text
Excepción persistenteusuario: «Sí, excepción solo para deliberar». Claude exclusivamente revisorCLI sin herramientas ni edición, consumo registrado. Nuevogoalcontinúaindicaciones aceptarbeneficiospequeños, no ampliarpermisos.
```

## 2 · codex · context

UTC: 2026-10-11T14:44:37.429468+00:00

```text
Nuevo goal usuario «continua con estas nuevas indicaciones»: bajarbeneficiomínimoparaencontrarsolución. Codexinterpreta aceptar mejoras pequeñas/milisegundos, no rebajar2s/5sni seguridad,frescura,auditoría,completitud ni evidencia. Primergoal cerrado sólodictamen; nueva autorizaciónjustificareabrirramacostemodesto. Máximo3ciclosfinito,4turnosexternosciclo; cambiar1variable.
Hechos: originalA/A corpus1502rows/27163hojas,23msconjuntosrutas;4501punteros6ms/noahorro. Fixture1500revision/16MiBseleccionado,548eventos/256reads enclonescommits4reads8events. Compuerta20originalcontrols1workerTCPmed1556CPU877ms spreadTCP8.064%CPU11.824%,umbral10%:FAIL,no reinterpretar. GCgen2correlación77ms,no duraciónni causafactor2históricoprevio~800ms. Noencontradocandidatosgrandes. Ahora priorizar mejoraetapapurosin depender de compuertarequest;TCPbeneficiono demostrarpor microbenchmark.
Código EXACTO ORIGINAL:
def scalar_fields(value, prefix=''):
 if isinstance(value,dict):
  for key,child in value.items():
   if not isinstance(key,str): raise ValidationError('Invalid portability object key')
   escaped=key.replace('~','~0').replace('/','~1')
   yield from scalar_fields(child,prefix+'/'+escaped)
 elif isinstance(value,list):
  for index,child in enumerate(value):
   yield from scalar_fields(child,prefix+'/'+str(index))
 elif prefix: yield {'path':prefix,'value':value}
 else: raise ValidationError('Portability row requires an object or list')

Únicoconsumidorproductivoquecambia apps/safety/rights_portability_coverage.py compile_coverage:
for index,row in enumerate(SECTIONS[name](source)):
 reference=row_reference(name,index,row)
 paths={item['path'] for item in scalar_fields(row)}
 selected=selectors.get(reference,set());missing=paths-selected
 # restoautoridad/decisiones intactas
Candidata mínima: nuevomóduloprivado rights_portability_paths.py `_scalar_paths` copiaalgoritmorecursivoexacto,únicocambio `elif prefix: yield prefix` envezdict;compile usa set(_scalar_paths(row)). Publicscalar_fields permanece intacta,no cambiar otrosconsumidores ni pointer_value ni límitesrecursiónni freezeGC.
Justificación: compile sólolee leaf['path'], no valores. Eliminarasignacionesdictporhoja podría mejora parcial. Noasimila27163hojas=101755dicts ni garantiza ahorro.
Planprevio Codex: pruebasdiferencialescontraoriginalorden/conjuntos/cantidadexcepcionesymomento, badkeys,dict/list/strsubclasses,tuplas/nonfinitefloat/root/prefix/escapes, objetoscustomitems, empty/deep/cyclic, mutacióndict/listmientrasconsume,send/close/throw yRecursionError. Nobenchmarkdeepcopy/punterosporqueintactos.
Comparaciónpura en corpusREALmaterializado del fixture, fueraDB/servidor:20original20candidata intercaladoABBAx10,2warmups/variante,wall/threadCPU,GCno tocar,resultadosigualantes/después,GCstatsfuera,memoriacallocationsseparado/tracemallocNOtimed. Corpusancho256/profundo64/escapeadicional. No mínimoabsolutomsenaceptación;beneficiomicroreproducible yperfilordenno engaño, reportar4bloquescronológicos.
N2 afectado conPGreal(familiascoverage/sourcechanges/revocations/idempotencia/purgaraces),másHTTP20porvarianteclonesidénticos usandoaliasconsumeroriginalfallbackenmodooriginalymodoactualcandidata,noautoridadomitida. MismaAPI/digests/freshchecks/commit.20x2=40HTTP+2warmupsmodounworker;prefijartimeout,no repetirporquererwin. Comparaciónmediana/colas/recurso:siCPUstagegana peroTCPno distinguibleruido sólo declarar mejoraETAPA, nodeclarargananciarequest;siempeorarequestconsistenterechazar. Noraise10%puerta históricos.
Criticaplan: ¿algúncambio desemánticalatente,pruebasfaltantes o razón NOprobar con nuevo umbral? Máximo400palabras. Noeditar/herramientas, opinionesnoevidencia.

```

## 3 · codex · request

UTC: 2026-10-11T14:44:37.699596+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Nuevo goal usuario «continua con estas nuevas indicaciones»: bajarbeneficiomínimoparaencontrarsolución. Codexinterpreta aceptar mejoras pequeñas/milisegundos, no rebajar2s/5sni seguridad,frescura,auditoría,completitud ni evidencia. Primergoal cerrado sólodictamen; nueva autorizaciónjustificareabrirramacostemodesto. Máximo3ciclosfinito,4turnosexternosciclo; cambiar1variable.
Hechos: originalA/A corpus1502rows/27163hojas,23msconjuntosrutas;4501punteros6ms/noahorro. Fixture1500revision/16MiBseleccionado,548eventos/256reads enclonescommits4reads8events. Compuerta20originalcontrols1workerTCPmed1556CPU877ms spreadTCP8.064%CPU11.824%,umbral10%:FAIL,no reinterpretar. GCgen2correlación77ms,no duraciónni causafactor2históricoprevio~800ms. Noencontradocandidatosgrandes. Ahora priorizar mejoraetapapurosin depender de compuertarequest;TCPbeneficiono demostrarpor microbenchmark.
Código EXACTO ORIGINAL:
def scalar_fields(value, prefix=''):
 if isinstance(value,dict):
  for key,child in value.items():
   if not isinstance(key,str): raise ValidationError('Invalid portability object key')
   escaped=key.replace('~','~0').replace('/','~1')
   yield from scalar_fields(child,prefix+'/'+escaped)
 elif isinstance(value,list):
  for index,child in enumerate(value):
   yield from scalar_fields(child,prefix+'/'+str(index))
 elif prefix: yield {'path':prefix,'value':value}
 else: raise ValidationError('Portability row requires an object or list')

Únicoconsumidorproductivoquecambia apps/safety/rights_portability_coverage.py compile_coverage:
for index,row in enumerate(SECTIONS[name](source)):
 reference=row_reference(name,index,row)
 paths={item['path'] for item in scalar_fields(row)}
 selected=selectors.get(reference,set());missing=paths-selected
 # restoautoridad/decisiones intactas
Candidata mínima: nuevomóduloprivado rights_portability_paths.py `_scalar_paths` copiaalgoritmorecursivoexacto,únicocambio `elif prefix: yield prefix` envezdict;compile usa set(_scalar_paths(row)). Publicscalar_fields permanece intacta,no cambiar otrosconsumidores ni pointer_value ni límitesrecursiónni freezeGC.
Justificación: compile sólolee leaf['path'], no valores. Eliminarasignacionesdictporhoja podría mejora parcial. Noasimila27163hojas=101755dicts ni garantiza ahorro.
Planprevio Codex: pruebasdiferencialescontraoriginalorden/conjuntos/cantidadexcepcionesymomento, badkeys,dict/list/strsubclasses,tuplas/nonfinitefloat/root/prefix/escapes, objetoscustomitems, empty/deep/cyclic, mutacióndict/listmientrasconsume,send/close/throw yRecursionError. Nobenchmarkdeepcopy/punterosporqueintactos.
Comparaciónpura en corpusREALmaterializado del fixture, fueraDB/servidor:20original20candidata intercaladoABBAx10,2warmups/variante,wall/threadCPU,GCno tocar,resultadosigualantes/después,GCstatsfuera,memoriacallocationsseparado/tracemallocNOtimed. Corpusancho256/profundo64/escapeadicional. No mínimoabsolutomsenaceptación;beneficiomicroreproducible yperfilordenno engaño, reportar4bloquescronológicos.
N2 afectado conPGreal(familiascoverage/sourcechanges/revocations/idempotencia/purgaraces),másHTTP20porvarianteclonesidénticos usandoaliasconsumeroriginalfallbackenmodooriginalymodoactualcandidata,noautoridadomitida. MismaAPI/digests/freshchecks/commit.20x2=40HTTP+2warmupsmodounworker;prefijartimeout,no repetirporquererwin. Comparaciónmediana/colas/recurso:siCPUstagegana peroTCPno distinguibleruido sólo declarar mejoraETAPA, nodeclarargananciarequest;siempeorarequestconsistenterechazar. Noraise10%puerta históricos.
Criticaplan: ¿algúncambio desemánticalatente,pruebasfaltantes o razón NOprobar con nuevo umbral? Máximo400palabras. Noeditar/herramientas, opinionesnoevidencia.

```

## 4 · claude · opinion

UTC: 2026-10-11T14:45:15.450976+00:00

```text
# Crítica del plan para `_scalar_paths` (opinión, no PASS)

**Semántica latente: no veo cambio funcional directo, aunque quedan riesgos.**

- **Hecho del código:** `prefix` es siempre `str` base. Incluso con claves subclase de `str`, `replace` devuelve `str`. Por tanto el hash y la igualdad en el `set` coinciden. El original nunca lee `value`, así que valores inhashables o `nan` no alteran el resultado.
- **Riesgo 1, deriva por duplicación:** si `scalar_fields` cambia (nueva validación o límite), `_scalar_paths` divergirá en silencio. El diferencial debe quedar permanente en CI, no ser una prueba de una sola vez. Conviene un test que compare ambos sobre un generador aleatorio de árboles (property-based) y otro que rompa si cambia el bytecode o el hash del fuente de `scalar_fields`.
- **Riesgo 2, profundidad de recursión:** comprensión de conjunto frente a `set(gen)` puede desplazar en un frame el punto exacto del `RecursionError`, según la versión de CPython. La versión no consta: es evidencia faltante. Hay que probar en límite−1, límite y límite+1 con ambos consumidores reales, no sólo con los generadores.
- **Riesgo 3, GC:** eliminar ~27k dicts por corrida cambia el conteo de asignaciones. Eso desplaza cuándo caen las colecciones gen0/1/2, no sólo cuánto cuestan. En HTTP podría mover una pausa gen2 a otra etapa. Ya existe la correlación de 77 ms, así que conviene registrar `gc.get_stats()` por bloque y no sólo al final.

**Pruebas que faltan:**

- Claves `str` con `~` y `/` combinados (`'~1'` frente a `'/'`) para confirmar que el escape es inyectivo en la salida.
- Clave `''` (ruta `.../`).
- Subclase de `dict` con `items()` que repite claves: el conjunto colapsa igual, pero hay que verificar el conteo previo.
- Excepción lanzada desde `items()` a mitad de iteración, comparando el estado parcial del `set`.
- `send`/`close`/`throw` aportan poco: el consumidor interno nunca los usa. Priorizaría lo anterior.

**Diseño de medición:**

- **Criterio no predeclarado:** "beneficio micro reproducible" sin regla abre caminos bifurcados. Antes de medir, fijar algo como: los 4 bloques a favor de la candidata, IC de la diferencia pareada que excluya 0, y reducción de asignaciones confirmada por tracemalloc.
- **Potencia HTTP:** con spread TCP del 8 % sobre ~1556 ms, N=20 no detecta ahorros del orden de 1–3 ms. Esa magnitud es mi hipótesis: unos 27k dicts a ~50–100 ns. Las 40 peticiones sólo sirven como prueba de no-inferioridad. El margen de regresión aceptable debe declararse antes, no después.
- **Alias/fallback de modo:** debe tener coste idéntico en ambos modos y no quedar en producción.

**¿Razón para NO crear un umbral nuevo?** Sí. La puerta del 10 % falló y redefinirla tras ver los datos sería reinterpretar. El nuevo criterio debe limitarse a la etapa pura y no sustituir la compuerta request.

**Decisión propuesta (ciclo 1/3, variable única = consumidor):**

- **(a) Proceder:** si el diferencial permanente pasa y los 4 bloques micro favorecen a la candidata con reducción de asignaciones, declarar sólo "mejora de etapa". HTTP queda como no-inferioridad.
- **(b) Rechazar:** si hay cualquier divergencia semántica, empeoramiento HTTP consistente o ganancia micro no reproducible entre bloques.

**Contraejemplo a vigilar:** la micro mejora, pero el desplazamiento del GC empeora la cola p95 HTTP. En ese caso, rechazar aunque la etapa gane.
```

## 5 · codex · request

UTC: 2026-10-11T14:46:06.916226+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Nuevo goal usuario «continua con estas nuevas indicaciones»: bajarbeneficiomínimoparaencontrarsolución. Codexinterpreta aceptar mejoras pequeñas/milisegundos, no rebajar2s/5sni seguridad,frescura,auditoría,completitud ni evidencia. Primergoal cerrado sólodictamen; nueva autorizaciónjustificareabrirramacostemodesto. Máximo3ciclosfinito,4turnosexternosciclo; cambiar1variable.
Hechos: originalA/A corpus1502rows/27163hojas,23msconjuntosrutas;4501punteros6ms/noahorro. Fixture1500revision/16MiBseleccionado,548eventos/256reads enclonescommits4reads8events. Compuerta20originalcontrols1workerTCPmed1556CPU877ms spreadTCP8.064%CPU11.824%,umbral10%:FAIL,no reinterpretar. GCgen2correlación77ms,no duraciónni causafactor2históricoprevio~800ms. Noencontradocandidatosgrandes. Ahora priorizar mejoraetapapurosin depender de compuertarequest;TCPbeneficiono demostrarpor microbenchmark.
Código EXACTO ORIGINAL:
def scalar_fields(value, prefix=''):
 if isinstance(value,dict):
  for key,child in value.items():
   if not isinstance(key,str): raise ValidationError('Invalid portability object key')
   escaped=key.replace('~','~0').replace('/','~1')
   yield from scalar_fields(child,prefix+'/'+escaped)
 elif isinstance(value,list):
  for index,child in enumerate(value):
   yield from scalar_fields(child,prefix+'/'+str(index))
 elif prefix: yield {'path':prefix,'value':value}
 else: raise ValidationError('Portability row requires an object or list')

Únicoconsumidorproductivoquecambia apps/safety/rights_portability_coverage.py compile_coverage:
for index,row in enumerate(SECTIONS[name](source)):
 reference=row_reference(name,index,row)
 paths={item['path'] for item in scalar_fields(row)}
 selected=selectors.get(reference,set());missing=paths-selected
 # restoautoridad/decisiones intactas
Candidata mínima: nuevomóduloprivado rights_portability_paths.py `_scalar_paths` copiaalgoritmorecursivoexacto,únicocambio `elif prefix: yield prefix` envezdict;compile usa set(_scalar_paths(row)). Publicscalar_fields permanece intacta,no cambiar otrosconsumidores ni pointer_value ni límitesrecursiónni freezeGC.
Justificación: compile sólolee leaf['path'], no valores. Eliminarasignacionesdictporhoja podría mejora parcial. Noasimila27163hojas=101755dicts ni garantiza ahorro.
Planprevio Codex: pruebasdiferencialescontraoriginalorden/conjuntos/cantidadexcepcionesymomento, badkeys,dict/list/strsubclasses,tuplas/nonfinitefloat/root/prefix/escapes, objetoscustomitems, empty/deep/cyclic, mutacióndict/listmientrasconsume,send/close/throw yRecursionError. Nobenchmarkdeepcopy/punterosporqueintactos.
Comparaciónpura en corpusREALmaterializado del fixture, fueraDB/servidor:20original20candidata intercaladoABBAx10,2warmups/variante,wall/threadCPU,GCno tocar,resultadosigualantes/después,GCstatsfuera,memoriacallocationsseparado/tracemallocNOtimed. Corpusancho256/profundo64/escapeadicional. No mínimoabsolutomsenaceptación;beneficiomicroreproducible yperfilordenno engaño, reportar4bloquescronológicos.
N2 afectado conPGreal(familiascoverage/sourcechanges/revocations/idempotencia/purgaraces),másHTTP20porvarianteclonesidénticos usandoaliasconsumeroriginalfallbackenmodooriginalymodoactualcandidata,noautoridadomitida. MismaAPI/digests/freshchecks/commit.20x2=40HTTP+2warmupsmodounworker;prefijartimeout,no repetirporquererwin. Comparaciónmediana/colas/recurso:siCPUstagegana peroTCPno distinguibleruido sólo declarar mejoraETAPA, nodeclarargananciarequest;siempeorarequestconsistenterechazar. Noraise10%puerta
CLAUDE OPINIÓN:
# Crítica del plan para `_scalar_paths` (opinión, no PASS)

**Semántica latente: no veo cambio funcional directo, aunque quedan riesgos.**

- **Hecho del código:** `prefix` es siempre `str` base. Incluso con claves subclase de `str`, `replace` devuelve `str`. Por tanto el hash y la igualdad en el `set` coinciden. El original nunca lee `value`, así que valores inhashables o `nan` no alteran el resultado.
- **Riesgo 1, deriva por duplicación:** si `scalar_fields` cambia (nueva validación o límite), `_scalar_paths` divergirá en silencio. El diferencial debe quedar permanente en CI, no ser una prueba de una sola vez. Conviene un test que compare ambos sobre un generador aleatorio de árboles (property-based) y otro que rompa si cambia el bytecode o el hash del fuente de `scalar_fields`.
- **Riesgo 2, profundidad de recursión:** comprensión de conjunto frente a `set(gen)` puede desplazar en un frame el punto exacto del `RecursionError`, según la versión de CPython. La versión no consta: es evidencia faltante. Hay que probar en límite−1, límite y límite+1 con ambos consumidores reales, no sólo con los generadores.
- **Riesgo 3, GC:** eliminar ~27k dicts por corrida cambia el conteo de asignaciones. Eso desplaza cuándo caen las colecciones gen0/1/2, no sólo cuánto cuestan. En HTTP podría mover una pausa gen2 a otra etapa. Ya existe la correlación de 77 ms, así que conviene registrar `gc.get_stats()` por bloque y no sólo al final.

**Pruebas que faltan:**

- Claves `str` con `~` y `/` combinados (`'~1'` frente a `'/'`) para confirmar que el escape es inyectivo en la salida.
- Clave `''` (ruta `.../`).
- Subclase de `dict` con `items()` que repite claves: el conjunto colapsa igual, pero hay que verificar el conteo previo.
- Excepción lanzada desde `items()` a mitad de iteración, comparando el estado parcial del `set`.
- `send`/`close`/`throw` aportan poco: el consumidor interno nunca los usa. Priorizaría lo anterior.

**Diseño de medición:**

- **Criterio no predeclarado:** "beneficio micro reproducible" sin regla abre caminos bifurcados. Antes de medir, fijar algo como: los 4 bloques a favor de la candidata, IC de la diferencia pareada que excluya 0, y reducción de asignaciones confirmada por tracemalloc.
- **Potencia HTTP:** con spread TCP del 8 % sobre ~1556 ms, N=20 no detecta ahorros del orden de 1–3 ms. Esa magnitud es mi hipótesis: unos 27k dicts a ~50–100 ns. Las 40 peticiones sólo sirven como prueba de no-inferioridad. El margen de regresión aceptable debe 
Codex: nueva funciónrecursivamínima mantiene orden/mutaciones/RecursionError,públicaintacta. Oráculo original y memoria medida por separado no mezclar tracemalloccon clocks.20original20variantpureABBAx10y20porvarianteTCPclonesidénticosnormalcommit. No descartarporpocosmsbajonuevoobjetivo; declararbeneficioetapa distinto aTCPsiinconcluyente. Revisa400palabrasmax,sin inventeahorro niumbrales. Losdiagnósticosdealias reconoceránnuevafunciónpara no contarcerofalsamente.

```

## 6 · notebook · opinion

UTC: 2026-10-11T14:46:56.012824+00:00

```text
**Sala técnica local — Dictamen sobre candidata mínima `_scalar_paths`**

### 1. Hechos Medidos y del Código
- **Consumo de `scalar_fields`:** En `compile_coverage` (`apps/safety/rights_portability_coverage.py`), el compilador de cobertura únicamente extrae la propiedad `item['path']` mediante `{item['path'] for item in scalar_fields(row)}`, descartando el valor `item['value']` y los diccionarios generados [1, 2].
- **Asignación por hoja:** `scalar_fields` instancia un diccionario `{'path': prefix, 'value': value}` por cada elemento escalar [1]. En el corpus real (1.502 filas y 27.163 hojas), esto genera 27.163 asignaciones temporales de diccionarios por corrida.
- **Fallo de compuerta Request:** La prueba original mostró un spread del 8,064% en TCP y 11,824% en CPU frente al umbral del 10% (FAIL). No se reinterpreta la compuerta a nivel de request.

### 2. Hipótesis
- **Ahorro local en etapa pura:** Reemplazar la instanciación de diccionarios por la devolución directa de cadenas de texto (`yield prefix`) en `_scalar_paths` reducirá las asignaciones de memoria y la carga de CPU estrictamente durante la fase de compilación de rutas [1, 2]. Sin embargo, no alterará de forma separable la latencia p95 a nivel HTTP/TCP debido al ruido de red.
- **Riesgo de deriva por duplicación:** Mantener dos funciones recursivas paralelas (`scalar_fields` y `_scalar_paths`) introduce el riesgo de divergencia semántica si se modifica la función pública en el futuro sin actualizar la versión privada [1].

### 3. Evidencia Faltante
- **Métricas aisladas de memoria (`tracemalloc`):** Falta la medición explícita del número exacto de bytes y bloques asignados/liberados en la etapa pura antes y después del cambio.
- **Límite de pila en CPython:** Falta verificación sobre la equivalencia del marco exacto donde se dispara `RecursionError` al evaluar `set(_scalar_paths(row))` frente a la comprensión de conjunto original [1, 2].
- **Métrica de GC por bloques:** Falta el registro diferenciado de `gc.get_stats()` por cada bloque cronológico para comprobar si la eliminación de diccionarios desplaza pausas de recolección de generaciones (gen0/gen1/gen2).

### 4. Decisión Finita y Criterios de Rechazo
**Decisión:** **Aprobar la apertura de la rama para `_scalar_paths` únicamente orientada a la mejora de la ETAPA PURA.** Si la comparación pareada ABBAx10 fuera de red/DB muestra beneficio micro-reproducible y reducción de asignaciones, se aceptará la optimización de etapa sin declarar ganancia a nivel de request.

**Contraejemplos / Criterios de rechazo:**
1. Falla de paridad en la suite diferencial (claves con `~`, `/` combinados, cadenas vacías o excepciones durante iteración).
2. Ausencia de un test permanente en CI que verifique paridad continua entre `scalar_fields` y `_scalar_paths` ante eventuales cambios de código [1].
3. Diferencia de tiempo de CPU/wall en la prueba pura aislada que resulte indistinguible del ruido estadístico.

¿Deseas que prepare el diseño detallado de la prueba en CI para garantizar la paridad continua entre ambas funciones?
```

## 7 · codex · context

UTC: 2026-10-11T15:08:33.857195+00:00

```text
Resultados reales ciclo1 mejoraPARCIAL autorizada aceptarbeneficiomilisegundos. Código: helper_scalar_pathsalgoritmorecursivoidénticoescalar_fieldsúnicoyieldprefix vsdict;compilecomprehensión {pathforpathin_scalar_paths(row)} mantieneframes/RecursionError. Publicscalar_fields/pointer_value/autoridad/lecturas/auditoría intactos. Diagnósticoscontadoraliasesadaptados,públicoaliasconservado. CPython3.12.15; diferencialpermanente12casesincluye250árbolesrandom/customitems/strreplaceoverrides/vacíos/escape/miditerationexceptions/mutación/sendclose/throw/cyclic ybarrido90nivelesenborderecursión;ASTbaselineenteroHEADigual/controlaliasregularlateerrores, no cachéautoridad.
Runner20261011-145141-3ea7872c terminal126PASS0fallos/errores/skips885.979sJUnit<900timeout;1275sourcehashesexactosantesdocs;PGRedis/Gunicornpropiosretiradosindependientemente. PruebasrealPGcoveragepure/store/pages/inspection/batch/races35varianteswaitrevocación/uso/http/reviewHTTP/mobile/reviewmobile ydiagnósticospure/http. BackendidentidadfixtureSIMULADOR,no proveedorreal;PGTCP/runtimeLOGINreales,sinouterrollback. Fixture1500revisiones/selección16777407bytes;historia548events256reads;unPID/kernelcanonicalnative-sealedmanifestigual;40samples20original20paths ABBAx10,1warmupcada;clonidénticos antes548/256después556/260commit4reads8eventsownerverified. Fuenteauténticabaseline compiladoASTfnoriginalcachepuro antesclocks,symmetricalalias setup/cleanup;noSQLhook/profiler/spansinreq,no GCchanged.
PUREmaterializedsource1502rows/27163leaves,HTTPservidoryaDETENIDO,20original20paths ABBAx10,2warmups/mode,GCfueratimers: originalwallmed20.39095CPU20.38716ms;paths17.58900/17.57157ms. PAIREDwallmedianbeneficio2.94320msCPU2.93828;20/20winsboth;4blockswallmedsaving[2.65917,3.15942,2.85445,3.00833]msCPU[2.65574,3.16651,2.86488,3.01880]. Originalyvariantresultorderedpaths/censosigual. Criteriopredeclared15/20winsy4blocksmed>0WALLCPU PASS;no minabsolutomsgainni pvalueformal. Memory5permode tracemallocseparatepeakmedianoriginal5706paths5698bytes:8bytes NO beneficio memoria significativo,ni cuenta cumulativeallocdicts. Códigoavoids27163dictsleafbyconstruction,diccionariooutputvaluesya noinstanciado, no101755dicts.
EDGEwide256/deep64/escapes/vacíos259hojas;originalwall.172635CPU.172093ms;paths.144772/.143841;20/20winsambos/fourblocks;peak39240vs38992bytes. No JSONnormalization.
HTTPoriginalTCPmed1626.67293/p95muestral1693.45751/CPUmed898.41925ms;paths1621.59579/1687.27893/889.80106. PairedTCPwins12/20medsaving8.0982msblocks[50.013,2.258,11.103,-48.554]CPUwins11/20blocks[27.15,10.58,7.51,-28.62],GC2totals11both. HTTPbenefitINCONCLUYENTE, no causal5mssaving,nonnoninferiorityproof,nop95contractual. No predeclaredregressionsignal>=15TCPpairlossall4blocksnegative, ni BOTHmedian+p95worse>5%;su ausencia NOpruebaequivalenciaperformanceuniversal. Singleworker,noproxy/RustFS/quotas/concurrentwork contractual. ScopeprepoutsideWSGIincludedTCP;GCstatspre clocks afterscope enter,postafterexit inclcleanupGC,no tiemposGCatribuidos.
OpiniónCodex: conservar SOLOmejoraETAPA~14%/~3msporque objetivoaceptaparciapequeña, seguridad/diferenciales/N2correctos; nada deHTTPwin ni2s/5saceptados. No repetirbenchmarkporruido,noredraftgoalparaaceptaciónfinal,126PASSno suma24localprechecks. Principalriesgodesarrollo duplicaciónwalkerconoraclepermanente. Antesfinalaceptación: ¿vesdefectoconcreto deequivalencia/medición/alcanceque requieraretirar? Si no, da dictamenconlímites ysi otra vía merecesiguiente ventana no probarautomáticamentepordeliberaciones. Máximo400palabras.

```

## 8 · codex · request

UTC: 2026-10-11T15:08:34.128841+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Resultados reales ciclo1 mejoraPARCIAL autorizada aceptarbeneficiomilisegundos. Código: helper_scalar_pathsalgoritmorecursivoidénticoescalar_fieldsúnicoyieldprefix vsdict;compilecomprehensión {pathforpathin_scalar_paths(row)} mantieneframes/RecursionError. Publicscalar_fields/pointer_value/autoridad/lecturas/auditoría intactos. Diagnósticoscontadoraliasesadaptados,públicoaliasconservado. CPython3.12.15; diferencialpermanente12casesincluye250árbolesrandom/customitems/strreplaceoverrides/vacíos/escape/miditerationexceptions/mutación/sendclose/throw/cyclic ybarrido90nivelesenborderecursión;ASTbaselineenteroHEADigual/controlaliasregularlateerrores, no cachéautoridad.
Runner20261011-145141-3ea7872c terminal126PASS0fallos/errores/skips885.979sJUnit<900timeout;1275sourcehashesexactosantesdocs;PGRedis/Gunicornpropiosretiradosindependientemente. PruebasrealPGcoveragepure/store/pages/inspection/batch/races35varianteswaitrevocación/uso/http/reviewHTTP/mobile/reviewmobile ydiagnósticospure/http. BackendidentidadfixtureSIMULADOR,no proveedorreal;PGTCP/runtimeLOGINreales,sinouterrollback. Fixture1500revisiones/selección16777407bytes;historia548events256reads;unPID/kernelcanonicalnative-sealedmanifestigual;40samples20original20paths ABBAx10,1warmupcada;clonidénticos antes548/256después556/260commit4reads8eventsownerverified. Fuenteauténticabaseline compiladoASTfnoriginalcachepuro antesclocks,symmetricalalias setup/cleanup;noSQLhook/profiler/spansinreq,no GCchanged.
PUREmaterializedsource1502rows/27163leaves,HTTPservidoryaDETENIDO,20original20paths ABBAx10,2warmups/mode,GCfueratimers: originalwallmed20.39095CPU20.38716ms;paths17.58900/17.57157ms. PAIREDwallmedianbeneficio2.94320msCPU2.93828;20/20winsboth;4blockswallmedsaving[2.65917,3.15942,2.85445,3.00833]msCPU[2.65574,3.16651,2.86488,3.01880]. Originalyvariantresultorderedpaths/censosigual. Criteriopredeclared15/20winsy4blocksmed>0WALLCPU PASS;no minabsolutomsgainni pvalueformal. Memory5permode tracemallocseparatepeakmedianoriginal5706paths5698bytes:8bytes NO beneficio memoria significativo,ni cuenta cumulativeallocdicts. Códigoavoids27163dictsleafbyconstruction,diccionariooutputvaluesya noinstanciado, no101755dicts.
EDGEwide256/deep64/escapes/vacíos259hojas;originalwall.172635CPU.172093ms;paths.144772/.143841;20/20winsambos/fourblocks;peak39240vs38992bytes. No JSONnormalization.
HTTPoriginalTCPmed1626.67293/p95muestral1693.45751/CPUmed898.41925ms;paths1621.59579/1687.27893/889.80106. PairedTCPwins12/20medsaving8.0982msblocks[50.013,2.258,11.103,-48.554]CPUwins11/20blocks[27.15,10.58,7.51,-28.62],GC2totals11both. HTTPbenefitINCONCLUYENTE, no causal5mssaving,nonnoninferiorityproof,nop95contractual. No predeclaredregressionsignal>=15TCPpairlossall4blocksnegative, ni BOTHmedian+p95worse>5%;su ausencia NOpruebaequivalenciaperformanceuniversal. Singleworker,noproxy/RustFS/quotas/concurrentwork contractual. ScopeprepoutsideWSGIincludedTCP;GCstatspre clocks afterscope enter,postafterexit inclcleanupGC,no tiemposGCatribuidos.
OpiniónCodex: conservar SOLOmejoraETAPA~14%/~3msporque objetivoaceptaparciapequeña, seguridad/diferenciales/N2correctos; nada deHTTPwin ni2s/5saceptados. No repetirbenchmarkporruido,noredraftgoalparaaceptaciónfinal,126PASSno suma24localprechecks. Principalriesgodesarrollo duplicaciónwalkerconoraclepermanente. Antesfinalaceptación: ¿vesdefectoconcreto deequivalencia/medición/alcanceque requieraretirar? Si no, da dictamenconlímites ysi otra vía merecesiguiente ventana no probarautomáticamentepordeliberaciones. Máximo400palabras.

```

## 9 · claude · opinion

UTC: 2026-10-11T15:09:00.844569+00:00

```text
# Dictamen: mantener la mejora de etapa con límites (opinión, no PASS)

**No veo un defecto concreto que obligue a retirar la mejora.** Los tres frentes quedan así:

**Equivalencia**
- El diferencial permanente coincide en orden y censo de paths. Cubre cambio de algoritmo, mutación a mitad de iteración, send/close/throw, ciclos y barrido de RecursionError.
- El conjunto deduplica igual que las claves del dict original, y la comprensión consume el generador al momento, así que no hay pereza observable.
- **Contraejemplo latente:** la frontera de recursión con generadores anidados depende del intérprete. Solo se ha medido en CPython 3.12.15. Si cambia la versión, el barrido de 90 niveles tiene que repetirse; no se puede heredar.

**Medición**
- Se cumple el criterio predeclarado: 20/20 en reloj y CPU, con los 4 bloques positivos. El 14,4 % (2,94 de 20,39 ms) es coherente.
- La memoria no mejora en pico (8 B). Que se eviten 27.163 dicts es cierto por construcción, pero no está medido como asignación acumulada. No debe citarse como beneficio medido.
- Hay una incoherencia menor sin efecto: 1 warmup en el protocolo general frente a 2 en PURE. Solo pido que el informe lo diga explícitamente.

**Alcance**
- Es un único fixture con identidad simulada y un solo worker.
- El beneficio vale únicamente para la etapa pura con esta forma de datos (1.502 filas, 27.163 hojas). No se extiende a otras formas ni a HTTP.

**Dictamen:** conservar la mejora como **parcial a nivel de etapa (~3 ms / ~14 % en PURE)**, con estos límites escritos:
1. No hay beneficio HTTP demostrado (12/20 y un bloque de −48 ms) ni no-inferioridad formal. La ausencia de señal de regresión no prueba equivalencia.
2. No hay conclusión sobre el p95 contractual ni sobre 2 s / 5 s.
3. No hay beneficio de memoria.
4. La validez está atada a CPython 3.12.15.
5. El oráculo diferencial debe seguir dentro de la suite obligatoria. Es lo que controla el riesgo de que los dos walkers diverjan. Si alguien modifica la semántica de `scalar_fields`, el test debe fallar y no adaptarse en silencio.

Coincido en no repetir el benchmark para perseguir ruido.

**Siguiente ventana (propuesta, sin probar automáticamente):**
- La etapa supone unos 20 ms de 898 ms de CPU HTTP (~2 %). Por eso 3 ms no podían verse en HTTP.
- Además hay unos 730 ms de reloj que no son CPU (espera de PG/IO o planificación).
- Antes de optimizar otra cosa, lo que más rinde es **atribuir el tiempo** de la petición HTTP: desglose por fases con instrumentación fuera de los relojes, separando SQL, serialización y espera.
- Con ese desglose, elegir un único objetivo cuyo peso pueda mover el p95 sea medible a nivel HTTP con un criterio predeclarado.

Sin ese desglose, cualquier nueva microoptimización tendría el mismo techo invisible.
```

## 10 · codex · request

UTC: 2026-10-11T15:10:14.482503+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Resultados reales ciclo1 mejoraPARCIAL autorizada aceptarbeneficiomilisegundos. Código: helper_scalar_pathsalgoritmorecursivoidénticoescalar_fieldsúnicoyieldprefix vsdict;compilecomprehensión {pathforpathin_scalar_paths(row)} mantieneframes/RecursionError. Publicscalar_fields/pointer_value/autoridad/lecturas/auditoría intactos. Diagnósticoscontadoraliasesadaptados,públicoaliasconservado. CPython3.12.15; diferencialpermanente12casesincluye250árbolesrandom/customitems/strreplaceoverrides/vacíos/escape/miditerationexceptions/mutación/sendclose/throw/cyclic ybarrido90nivelesenborderecursión;ASTbaselineenteroHEADigual/controlaliasregularlateerrores, no cachéautoridad.
Runner20261011-145141-3ea7872c terminal126PASS0fallos/errores/skips885.979sJUnit<900timeout;1275sourcehashesexactosantesdocs;PGRedis/Gunicornpropiosretiradosindependientemente. PruebasrealPGcoveragepure/store/pages/inspection/batch/races35varianteswaitrevocación/uso/http/reviewHTTP/mobile/reviewmobile ydiagnósticospure/http. BackendidentidadfixtureSIMULADOR,no proveedorreal;PGTCP/runtimeLOGINreales,sinouterrollback. Fixture1500revisiones/selección16777407bytes;historia548events256reads;unPID/kernelcanonicalnative-sealedmanifestigual;40samples20original20paths ABBAx10,1warmupcada;clonidénticos antes548/256después556/260commit4reads8eventsownerverified. Fuenteauténticabaseline compiladoASTfnoriginalcachepuro antesclocks,symmetricalalias setup/cleanup;noSQLhook/profiler/spansinreq,no GCchanged.
PUREmaterializedsource1502rows/27163leaves,HTTPservidoryaDETENIDO,20original20paths ABBAx10,2warmups/mode,GCfueratimers: originalwallmed20.39095CPU20.38716ms;paths17.58900/17.57157ms. PAIREDwallmedianbeneficio2.94320msCPU2.93828;20/20winsboth;4blockswallmedsaving[2.65917,3.15942,2.85445,3.00833]msCPU[2.65574,3.16651,2.86488,3.01880]. Originalyvariantresultorderedpaths/censosigual. Criteriopredeclared15/20winsy4blocksmed>0WALLCPU PASS;no minabsolutomsgainni pvalueformal. Memory5permode tracemallocseparatepeakmedianoriginal5706paths5698bytes:8bytes NO beneficio memoria significativo,ni cuenta cumulativeallocdicts. Códigoavoids27163dictsleafbyconstruction,diccionariooutputvaluesya noinstanciado, no101755dicts.
EDGEwide256/deep64/escapes/vacíos259hojas;originalwall.172635CPU.172093ms;paths.144772/.143841;20/20winsambos/fourblocks;peak39240vs38992bytes. No JSONnormalization.
HTTPoriginalTCPmed1626.67293/p95muestral1693.45751/CPUmed898.41925ms;paths1621.59579/1687.27893/889.80106. PairedTCPwins12/20medsaving8.0982msblocks[50.013,2.258,11.103,-48.554]CPUwins11/20blocks[27.15,10.58,7.51,-28.62],GC2totals11both. HTTPbenefitINCONCLUYENTE, no causal5mssaving,nonnoninferiorityproof,nop95contractual. No predeclaredregressionsignal>=15TCPpairlossall4blocksnegative, ni BOTHmedian+p95worse>5%;su ausencia NOpruebaequivalenciaperformanceuniversal. Singleworker,noproxy/RustFS/quotas/concurrentwork contractual. ScopeprepoutsideWSGIincludedTCP;GCstatspre clocks afterscope enter,postafterexit inclcleanupGC,no tiemposGCatribuidos.
OpiniónCodex: conservar SOLOmejoraETAPA~14%/~3msporque objetivoaceptaparciapequeña, seguridad/diferenciales/N2correctos; nada deHTTPwin ni2s/5saceptados. No repetirbenchmarkporruido,noredraftgoalparaaceptaciónfinal,126PASSno suma24localprechecks. Principalriesgodesarrollo duplicaciónwalkerconoraclepermanente. Antesfinalaceptación: ¿vesdefectoconcreto deequivalencia/medición/alcanceque requieraretirar? Si no, da dictamenconlímites ysi otra vía merecesiguiente ventana no probarautomáticamentepordeliberaciones. Máximo400palabras.

CLAUDE FINAL OPINIÓN (no PASS):
# Dictamen: mantener la mejora de etapa con límites (opinión, no PASS)

**No veo un defecto concreto que obligue a retirar la mejora.** Los tres frentes quedan así:

**Equivalencia**
- El diferencial permanente coincide en orden y censo de paths. Cubre cambio de algoritmo, mutación a mitad de iteración, send/close/throw, ciclos y barrido de RecursionError.
- El conjunto deduplica igual que las claves del dict original, y la comprensión consume el generador al momento, así que no hay pereza observable.
- **Contraejemplo latente:** la frontera de recursión con generadores anidados depende del intérprete. Solo se ha medido en CPython 3.12.15. Si cambia la versión, el barrido de 90 niveles tiene que repetirse; no se puede heredar.

**Medición**
- Se cumple el criterio predeclarado: 20/20 en reloj y CPU, con los 4 bloques positivos. El 14,4 % (2,94 de 20,39 ms) es coherente.
- La memoria no mejora en pico (8 B). Que se eviten 27.163 dicts es cierto por construcción, pero no está medido como asignación acumulada. No debe citarse como beneficio medido.
- Hay una incoherencia menor sin efecto: 1 warmup en el protocolo general frente a 2 en PURE. Solo pido que el informe lo diga explícitamente.

**Alcance**
- Es un único fixture con identidad simulada y un solo worker.
- El beneficio vale únicamente para la etapa pura con esta forma de datos (1.502 filas, 27.163 hojas). No se extiende a otras formas ni a HTTP.

**Dictamen:** conservar la mejora como **parcial a nivel de etapa (~3 ms / ~14 % en PURE)**, con estos límites escritos:
1. No hay beneficio HTTP demostrado (12/20 y un bloqu
Codex:últimoturno4/4,no repetir. Veredicto propioaceptaretapa~3msconsemánticayN2correctos;HTTPruidosono firmarganancia. No nuevosumbralesaposteriori niseguridadrebajada. Objetivousuarioadmitepequeñosbeneficios,nocompleto2s5s. Revisiónfinal300palabras:objecionesconcretasoalcanceaceptable;no inventarescapeframework.

```

## 11 · notebook · opinion

UTC: 2026-10-11T15:11:03.382892+00:00

```text
### Dictamen Técnico Local (Opinión, no PASS ni Autorización)

**No se observa un defecto concreto de equivalencia, medición o alcance que obligue a retirar la mejora.** El desglose de la evidencia suministrada establece las siguientes fronteras:

#### 1. Clasificación del Estado Técnico
* **Hechos medidos:**
  * **Ganancia en etapa PURE:** Beneficio de **2.94 ms (~14.4%)** en tiempo de muro y CPU (20/20 victorias pareadas y 4/4 bloques positivos). Coincidencia exacta en orden y censo de paths sobre 126/126 pruebas diferenciales (12 casos borde en CPython 3.12.15).
  * **Memoria en pico:** Sin ganancia significativa (**8 bytes** de diferencia: 5706 B vs 5698 B). Evitar 27,163 diccionarios ocurre por construcción del generador, pero no está medido como reducción de asignación acumulada.
* **Hipótesis:**
  * Menor carga sobre el recolección de basura (GC) en ejecuciones continuas con alta densidad de hojas.
* **Evidencia faltante:**
  * Impacto neutro o favorable demostrado en transporte HTTP (resultados inconclusos: 12/20 victorias TCP con un bloque negativo de -48.55 ms).
  * Validez en p95 contractual con concurrencia real, proxies o múltiples workers.

#### 2. Contraejemplos y Límites de Alcance
* **Frontera de recursión en el intérprete:** El comportamiento en el límite de recursión (90 niveles con generadores anidados) está acotado a CPython 3.12.15; no puede extrapolarse a otras versiones del runtime sin verificación fresca.
* **Incoherencia en protocolo:** Desfase menor de warmups (1 en protocolo general frente a 2 en PURE) que debe documentarse explícitamente sin alterar el resultado.

#### 3. Decisión Finita y Siguiente Paso
* **Dictamen:** **Mantener la mejora con carácter estrictamente parcial de etapa (~3 ms / ~14% en PURE)**.
* **Límites de aceptación:**
  1. Se excluye cualquier declaración de victoria en HTTP o cumplimiento de p95 contractual.
  2. No se acreditará beneficio de memoria no sustentado en pico.
* **Siguiente ventana:** **No repetir benchmarks automáticos por deliberaciones** para evitar ruido en la serie. Proceder al siguiente bloque o dependencia funcional pendiente en la cola.
```

## 12 · codex · decision

UTC: 2026-10-11T15:14:04.243294+00:00

```text
Decisión Codex — mejora parcial adoptada, 2026-10-11

La instrucción posterior permite aceptar beneficios pequeños; no reduce2s/5s ni seguridad/frescura/auditoría. Ciclo1: conservar helper privado recursivo_scalar_paths y uso único en compile_coverage. Sin cachéautoridad ni cambiosSQL/firmas/lecturas niAPIpública. Eliminar diccionarios hoja que este consumidor no usa es mecanismo concreto y medido a nivel de etapa, no una solución integral delrequest.

Pruebas126PASS/0fallos/errores/skips885.979sJUnit runner20261011-145141-3ea7872c;1275hashesexactosantesdocumentar;PGRedisGunicornpropiosretiradosindependientemente. Diferencialpermanente12casos,250árbolesdeterministasyborderecursión90nivelesCPython3.12.15;ASTcontroloriginalcompilermatchHEADentero;aliaseserror/late restaurados. Corpus1500revisiones16MiB/548EVENT256reads,40HTTPreal20porvariantunworker/clonigual/normalcommit4reads8events comprobados. Backendidentidadsimuladofixture,no proveedorreal;PG/HTTPsíreales. Sinprofiler/SQLhook/GCforzado/cargaownconcurrente.

Purecorpus1502rows/27163hojas: originalmedwall20.391msvs17.589ms(~13.74%diferencia de medianas). Parejasmedianwall2.943msCPU2.938ms,20/20mejores y4bloquespositivos,criterio15/20y4bloquespredeclaradoPASS. Edge259hojasancho/profundo64/escapes consistentetambién, sin normalizar JSON. Picotracemalloc5706vs5698bytes:no beneficio memoria significativo;no cuantifica dictstemporales acumulados. Retirardictshoja por construcción no equivale a medición de memoria ahorrada.

HTTPmed1626.673vs1621.596ms,p95muestral1693.458vs1687.279ms;12/20TCPpairedwinsyúltimobloquenegativo(-48.55ms). BeneficioHTTPINCONCLUYENTE,no ganar5mscomohecho,no noninferiorityformal,nop95contractual. No señalesde regresiónsegúnreglastriagepredeclaradas(15loss4bloquesnegativos obothmedian+p95>5%peores);ausenciaseñalno pruebaequivalencia universal de rendimiento. GCgen2total11cada variant no pruebacausaalguna. No reinterpretarcompuertaCPUhistórica11.824FAIL comoPASS.

Revisores dosClaude/dosNotebook opiniones válidas, sinherramientasClaude ni fuentesnotebookañadidas;consumodeclaradoCLIregistrado. No consenso comoPASS. Corregirafirmaciones:126esbateríacompletaNO126diferenciales;HTTP1warmuppormodoPURE2pormodo esplanintencional noincidente;no afirmar3msimposiblesHTTPporredni repartiretiemposdeexperimentosdistintoscomopresupuesto exacto. Prefijo puede serstrsubclassefectosparticulares;oráculo cubreitems/replace/subclasses, noafirmarbase-struniversal. `tracemalloc` midepicovivo,nobloques transitorios históricos. Instrumentación de fases tendríaoverhead,noprometermedirintrínsecofuera relojes.

Cierre goal: se ha encontrado/aplicado/verificado una mejora parcial con criterio menor de impacto. No consumir3ciclosporobligación ni ejecutarotrobenchmarkpordeliberación. Mantener pruebasdiferenciales endescubrimiento normalpytest;modificarsemántica de ambos sólo porrequisito explícito. Alcanceaceptación: etapa/local N2afectado, noMOD08completo ni2s5s. Sincommits/push/proveedores/datosreales. Recursospropios retiradosytrabajousuariopreservado. Próximas víasmásampliasrequierendiseñoymedicióndistintos;noreabrirautomáticamenteventanas agotadas.

```
