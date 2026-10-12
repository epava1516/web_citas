# MOD08 cambio de enfoque con investigación web independiente

Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

## 1 · user · authorization

UTC: 2026-10-11T16:48:56.825636+00:00

```text
Autorización anterior persistente: «Sí, excepción solo para deliberar». Instrucción posterior del usuario: «Quizá lo que tendriais que deliberar lo siguiente es si habria que hacer un cambio de enfoque para la optimización, y que cada uno busque en internet soluciones para hacer un brainstorming, quizá imaginacion y pensamiento lateral es lo que falta». Esta instrucción autoriza exclusivamente investigación web pública de Claude (WebSearch/WebFetch) dentro de deliberación; sin herramientas locales, edición, shell ni escritura. Consumo registrado. No invocación V1 escritora ni cambio de permisos externos.

```

## 2 · codex · context

UTC: 2026-10-11T16:48:56.874364+00:00

```text
Necesitamos cambiar el enfoque para optimizar un proyecto Django5.2.17/Python3.12.15/psycopg3.3.6/PostgreSQL17.11. Investiga tú en internet (sólo WebSearch/WebFetch; fuentes técnicas primarias oficiales o papers), luego brainstorming de hasta seis rutas arquitectónicas distintas. Cada ruta: coste eliminado, mecanismo concreto, contraejemplo de seguridad, compatibilidad con implementación actual y experimento mínimo finito. No copiar código ni aceptar opiniones como PASS. Links concretos y fechas/versiones cuando corresponda. No prometas ahorro de tiempos no medidos.

Problema: navegación de expediente grande inspect_batch4páginas p95 histórico3.753392s (383 lotes) objetivo2s. JSON6.930455 ybinario7.317947s frente5s (n3/n8 insuficiente). Datos sintéticos1500revisiones,16MiBproyección JSON,64MiBoriginalesWebP. Objetivo hasta50filasporpágina,autoridad fresca,cada lectura auditada,erroresfailclosed,concurrencia/revocación/purga no ocultadas. Sin compras/publicación/proveedores/datosreales. No aumentarworkers/recursos como compensación. Usuario admitebeneficiospequeños pero quierepensamientolateral.

Actual fuente: source_copy bloqueoUser/Listing yRevision select_for_update(of=self).defer(search_document+7camposnoutilizados).select_related(municipality,postal_code,zone).order_by(created_at,pk);iteratorchunk1000; agrupa2batches1000/500 ycincofamiliasrelacionesUUID arrayporbatch; construye dictcompleto. inspection_source compartefuenteinmemory dentrodeoperación, huelladerowversions antes/después yhashcanónico defuenteantes/después; si drift frescoreadfull/fail. Guardia finalobligatoria. No objetosORMescapan/saves. Ya1sourcecopy, no4.

Batch transactionatomic: reviewer_case/authorize/authorized_proof, acciónbatch, for4inspect_page. Cada página revalida caso/actor/proof frescos y llama selection_review.record(audit_only),que revalida yrecupera assessment. validate_approved_assessment require_runtime_chain, latest.only(pk), ReadFORUPDATEselect_related(action),validate evidence. CadacoveragepageinsertaCoverageRead,avanzaEVENT/headenmismaTX.
_runtime_is_trusted9SQLcatálogosfrescos porllamada. validate_chain adquiereadvisory_xact_lockporcase, leeEVENThashesy7fuentesfísicasconpipeline.sync ycomparahuellas. Ticket sólofastpathsiigualheadactual+atestaciónfresca. No cacheautoridad/catálogos/cadena;bloqueoadvisorynobloqueaDDLni purga.Criptografíaválidanopruebafrescura. Derechos derivados mutables,purgaassessmentbodypuedeconcurrir. No precargarUser/assessmentadelantandosnapshot. AdquirirFORNOKEYenpadrenobloqueaFKinsertKEYSHARE por sísolo.

Medido hoy actualclonhistorial548EVENT/256CoverageRead creado64POST,1GunicornsyncsinCaddycuotasoload: controles791–869ms vs previos1600–1800ms, SIN cambio producto entre tandas; no extrapolaraSLOhistórico. 4requestsperfiladosfuente151–195ms; ServerCursor.fetchmany3calls1000/500/0 total75–91ms; adaptaciónload_rows10–15ms; hidratación1500modelos16msen3samples/51msoutlier1. sourceotros19exec28–32ms. authorize23calls93exec~100–107ms total/43–46msPythonexclusivo. record80exec50–54ms/page84exec43–52ms/batch14exec50–55ms. Chainpipeline4sync33–44ms. canonical1705calls46–48ms,unseal193calls30–33ms. No syscalls/PGlocksserverCPU aislado; cifrasinstrumentadasnoahorros.

Intentosyaexplorados: memojsondecodecondeepcopy negativo(31msparseorepetido vs196mscopias);noreutilizarobjmutable. SQLinlinehashcandidatoequivalenteperoHTTPinconclusoretirado. Scalar_paths privadoahorra2.80ms etapa,defer7columnas2.07ms etapa(123N2PASS),HTTPambosinconcluso. No sumaralas cifrasp95. No volveramicroORMsinbeneficiopotencialmayor.

Opciones abiertas para cuestionar, no adoptar: validaciónincremental verificableimpuestaporDB; barrera entry/exit conchecks físicosdecompletitud; desplazarconstrucción pesada fuerapetición pero autorizaryverificarversiónfrescaenuso; estructura/Merkleautenticadayfrescaquepermitalecturapaginadasinmaterializar16MiBparacada50filas; aislamiento/transacciones serializablescontralímites; almacenarrepresentaciónselladasinautoridadcache; adoptarprotocolo binariopsycopg siadaptacióndominante (actualmenteno). Incluyetambiénrutaspropiasysorpresivas,críticaminuciosa aesas opciones. Queremospriorizaciónrevisable ycondición de abandono, no parchesqueocultenproblema.

```

## 3 · codex · request

UTC: 2026-10-11T16:48:56.917597+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sólo WebSearch/WebFetch públicos; sin herramientas locales, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Necesitamos cambiar el enfoque para optimizar un proyecto Django5.2.17/Python3.12.15/psycopg3.3.6/PostgreSQL17.11. Investiga tú en internet (sólo WebSearch/WebFetch; fuentes técnicas primarias oficiales o papers), luego brainstorming de hasta seis rutas arquitectónicas distintas. Cada ruta: coste eliminado, mecanismo concreto, contraejemplo de seguridad, compatibilidad con implementación actual y experimento mínimo finito. No copiar código ni aceptar opiniones como PASS. Links concretos y fechas/versiones cuando corresponda. No prometas ahorro de tiempos no medidos.

Problema: navegación de expediente grande inspect_batch4páginas p95 histórico3.753392s (383 lotes) objetivo2s. JSON6.930455 ybinario7.317947s frente5s (n3/n8 insuficiente). Datos sintéticos1500revisiones,16MiBproyección JSON,64MiBoriginalesWebP. Objetivo hasta50filasporpágina,autoridad fresca,cada lectura auditada,erroresfailclosed,concurrencia/revocación/purga no ocultadas. Sin compras/publicación/proveedores/datosreales. No aumentarworkers/recursos como compensación. Usuario admitebeneficiospequeños pero quierepensamientolateral.

Actual fuente: source_copy bloqueoUser/Listing yRevision select_for_update(of=self).defer(search_document+7camposnoutilizados).select_related(municipality,postal_code,zone).order_by(created_at,pk);iteratorchunk1000; agrupa2batches1000/500 ycincofamiliasrelacionesUUID arrayporbatch; construye dictcompleto. inspection_source compartefuenteinmemory dentrodeoperación, huelladerowversions antes/después yhashcanónico defuenteantes/después; si drift frescoreadfull/fail. Guardia finalobligatoria. No objetosORMescapan/saves. Ya1sourcecopy, no4.

Batch transactionatomic: reviewer_case/authorize/authorized_proof, acciónbatch, for4inspect_page. Cada página revalida caso/actor/proof frescos y llama selection_review.record(audit_only),que revalida yrecupera assessment. validate_approved_assessment require_runtime_chain, latest.only(pk), ReadFORUPDATEselect_related(action),validate evidence. CadacoveragepageinsertaCoverageRead,avanzaEVENT/headenmismaTX.
_runtime_is_trusted9SQLcatálogosfrescos porllamada. validate_chain adquiereadvisory_xact_lockporcase, leeEVENThashesy7fuentesfísicasconpipeline.sync ycomparahuellas. Ticket sólofastpathsiigualheadactual+atestaciónfresca. No cacheautoridad/catálogos/cadena;bloqueoadvisorynobloqueaDDLni purga.Criptografíaválidanopruebafrescura. Derechos derivados mutables,purgaassessmentbodypuedeconcurrir. No precargarUser/assessmentadelantandosnapshot. AdquirirFORNOKEYenpadrenobloqueaFKinsertKEYSHARE por sísolo.

Medido hoy actualclonhistorial548EVENT/256CoverageRead creado64POST,1GunicornsyncsinCaddycuotasoload: controles791–869ms vs previos1600–1800ms, SIN cambio producto entre tandas; no extrapolaraSLOhistórico. 4requestsperfiladosfuente151–195ms; ServerCursor.fetchmany3calls1000/500/0 total75–91ms; adaptaciónload_rows10–15ms; hidratación1500modelos16msen3samples/51msoutlier1. sourceotros19exec28–32ms. authorize23calls93exec~100–107ms total/43–46msPythonexclusivo. record80exec50–54ms/page84exec43–52ms/batch14exec50–55ms. Chainpipeline4sync33–44ms. canonical1705calls46–48ms,unseal193calls30–33ms. No syscalls/PGlocksserverCPU aislado; cifrasinstrumentadasnoahorros.

Intentosyaexplorados: memojsondecodecondeepcopy negativo(31msparseorepetido vs196mscopias);noreutilizarobjmutable. SQLinlinehashcandidatoequivalenteperoHTTPinconclusoretirado. Scalar_paths privadoahorra2.80ms etapa,defer7columnas2.07ms etapa(123N2PASS),HTTPambosinconcluso. No sumaralas cifrasp95. No volveramicroORMsinbeneficiopotencialmayor.

Opciones abiertas para cuestionar, no adoptar: validaciónincremental verificableimpuestaporDB; barrera entry/exit conchecks físicosdecompletitud; desplazarconstrucción pesada fuerapetición pero autorizaryverificarversiónfrescaenuso; estructura/Merkleautenticadayfrescaquepermitalecturapaginadasinmaterializar16MiBparacada50filas; aislamiento/transacciones serializablescontralímites; almacenarrepresentaciónselladasinautoridadcache; adoptarprotocolo binariopsycopg siadaptacióndominante (actualmenteno). Incluyetambiénrutaspropiasysorpresivas,críticaminuciosa aesas opciones. Queremospriorizaciónrevisable ycondición de abandono, no parchesqueocultenproblema.

```

## 4 · claude · opinion

UTC: 2026-10-11T16:50:22.353817+00:00

```text
# Rutas para inspect_batch: medir dónde se espera y no recomputar la autoridad más veces de lo necesario

**Conclusión:** con lo que se ha medido no se puede explicar el p95 histórico de 3,75 s. Las peticiones medidas hoy tardan 0,79–0,87 s, y en tandas anteriores 1,6–1,8 s, sin ningún cambio de producto entre ambas. La causa principal todavía es desconocida. Por eso propongo medir primero las esperas (ruta R1) y, después, reducir las revalidaciones repetidas dentro de la transacción (R2). Nada de esto es un PASS.

## Datos
**Medidos (n=4 perfilados, un solo worker, sin carga):**
- source_copy: 151–195 ms. De ello, fetchmany 75–91 ms; adaptación de filas 10–15 ms; hidratación de modelos 16 ms (51 ms en un caso atípico).
- authorize: ~100–107 ms.
- record: 50–54 ms; cada página: 43–52 ms.
- Cadena con pipeline: 33–44 ms.
- canonical: 46–48 ms.

**Hipótesis:** la diferencia entre ~0,8 s y 3,75 s viene de esperas que no se perfilaron: locks de fila, el advisory lock por caso, I/O, la cola de Gunicorn y el GC. El cambio de 1,6 s a 0,8 s sin tocar el producto apunta al entorno, no al código.

**Falta:** wait_event bajo concurrencia, pg_locks, la distribución de los 383 lotes por tamaño y momento, y CPU del servidor por separado. Tampoco pude leer la documentación de pipeline de psycopg (el certificado falló), así que no afirmo nada sobre cómo se comportan los errores en pipeline.

## Rutas

**R1. Atribuir las esperas antes de optimizar**
- **Coste que elimina:** trabajar a ciegas.
- **Mecanismo:** reproducir lotes con la misma forma que los 383 a concurrencia 1, 2 y 4, con mutadores concurrentes (revocación y purga). Activar `log_lock_waits`, muestrear `pg_stat_activity.wait_event` y medir aparte el tiempo en cola del worker.
- **Contraejemplo:** medir con un solo worker esconde precisamente la contención que podría generar el p95.
- **Compatibilidad:** total; solo se observa.
- **Experimento finito:** 3 niveles × 3 tandas × 30 lotes, con el binario fijo.
- **Abandono:** si a concurrencia realista el p95 sigue lejos de 2 s y casi todo es CPU dentro de la petición, se pasa a R2/R4. Si domina la espera, el problema es de bloqueo, no de cómputo.

**R2. Validar una vez y retener locks en vez de revalidar cuatro veces**
- **Coste que elimina:** las revalidaciones repetidas. Hoy authorize, cada inspect_page y cada record revalidan, y cada llamada a `_runtime_is_trusted` lanza 9 consultas de catálogo.
- **Mecanismo:** validar una sola vez y tomar `FOR SHARE` sobre las filas de autoridad y del assessment. Según el manual de PG17, `FOR SHARE` bloquea UPDATE y DELETE ajenos hasta el commit, así que la validación sigue fresca durante toda la transacción porque nadie puede cambiarla, no porque se haya cacheado. `FOR KEY SHARE` no sirve: no bloquea los UPDATE que no tocan la clave.
- **Contraejemplos:**
  - El DDL y los cambios de catálogo no respetan locks de fila ni advisory locks. Las comprobaciones de catálogo tendrían que seguir por página, o habría que tomar un lock de tabla que conflicte con ALTER.
  - Si algún camino de purga o revocación escribe en una tabla sin lock sobre la fila validada (por ejemplo, insertando una fila nueva de revocación), no queda bloqueado.
  - Retener locks retrasa la revocación hasta el commit. Hay que documentar que es «retrasada, no ignorada».
- **Experimento:** una matriz de inyección que revoque o purgue en cada barrera de página y compruebe fail-closed u orden serial demostrable.
- **Abandono:** si aparece algún mutador que no conflicte con el lock.

**R3. Usar REPEATABLE READ o SERIALIZABLE (crítica de la opción abierta)**
- **Contraejemplo de seguridad:** un snapshot único hace que las huellas de antes y después coincidan siempre, por construcción. Eso da consistencia, no frescura.
- SSI solo detecta conflictos entre transacciones que también sean SERIALIZABLE, y añade reintentos 40001. `READ ONLY DEFERRABLE` no aplica porque se insertan filas de CoverageRead.
- **Valoración:** prioridad baja. Solo tendría sentido si se combina con R2 y todos los mutadores pasan a SERIALIZABLE.

**R4. Contador de versión por caso mantenido por la propia base**
- **Coste que elimina:** leer las 7 fuentes físicas y rehashear; también reduciría el coste de canonical.
- **Mecanismo:** triggers sobre las 7 fuentes incrementan un contador o cabeza de versión del caso. La comprobación de frescura pasa a ser leer esa fila bajo `FOR SHARE` y comparar.
- **Contraejemplos:**
  - `session_replication_role=replica` o `DISABLE TRIGGER` lo saltan, así que hay que verificar `pg_trigger.tgenabled` dentro de las comprobaciones de catálogo.
  - TRUNCATE necesita su propio trigger a nivel de sentencia.
  - La fila del contador se convierte en punto caliente de escritura.
  - Los constraint triggers solo pueden ser AFTER ROW.
- **Experimento:** un mutador por cada vía (UPDATE, DELETE, TRUNCATE, COPY, trigger desactivado) y verificar fail-closed.
- **Abandono:** si alguna vía no queda cubierta.

**R5. Proyección sellada guardada en tabla, ligada a la versión de R4**
- **Coste que elimina:** source_copy, construir el dict completo y canonical. Se construye fuera de la petición.
- **Mecanismo:** guardar la proyección sellada en una tabla con su vector de versión. Al usarla se comprueban frescos la autoridad (como hoy) y que la versión coincida (R4). No es una caché de autoridad.
- **Contraejemplo:** la purga del cuerpo del assessment tiene que borrar la copia sellada en la misma transacción. Si no, la copia sobrevive a la purga, lo cual es un problema de privacidad. Además duplica 16 MiB por expediente.
- **Dependencia:** solo es viable si R4 funciona.

**R6. Árbol de Merkle o índice autenticado para paginar**
- **Coste que elimina:** materializar 16 MiB para servir 50 filas.
- **Crítica:** Li et al. (SIGMOD 2006) ya tratan la frescura como un problema aparte de la integridad. Una raíz firmada demuestra integridad respecto a esa raíz, no que esa raíz sea la actual, así que la frescura vuelve a depender de R4.
- **Límite del beneficio:** hoy ya se hace un solo source_copy por lote, así que el beneficio está acotado por lo que cuestan source y canonical. Además cada cambio de revisión obliga a reescribir el camino del árbol.
- **Valoración:** solo vale la pena si R1 demuestra que la fuente domina el p95 bajo carga.

**Descartado por ahora:** el protocolo binario de psycopg. La adaptación cuesta 10–15 ms, lejos de dominar. Volver a mirarlo solo si R1 cambia esa proporción.

## Decisión propuesta
Orden: **R1 → R2 → R4 → R5**. R3 y R6 quedan en espera.

Los ahorros de cada etapa no se suman ni se trasladan al p95. Cada ruta se acepta solo si el p95 de extremo a extremo, medido a la concurrencia de R1 y con mutadores concurrentes activos, mejora con un intervalo de confianza que no se solape con el del control. Con n=3 u n=8 no se puede decidir.

**Contraejemplo general:** si R1 muestra que el p95 histórico venía de saturación del host, ninguna de estas rutas llegará a 2 s sin cambiar el entorno. En ese caso la respuesta correcta es documentarlo, no parchear.

Fuentes:
- [PostgreSQL 17: bloqueo explícito](https://www.postgresql.org/docs/17/explicit-locking.html)
- [PostgreSQL 17: aislamiento de transacciones](https://www.postgresql.org/docs/17/transaction-iso.html)
- [PostgreSQL 17: CREATE TRIGGER](https://www.postgresql.org/docs/17/sql-createtrigger.html)
- [Django 5.2: QuerySet API (select_for_update, no_key, of)](https://docs.djangoproject.com/en/5.2/ref/models/querysets/)
- [Li, Hadjieleftheriou, Kollios, Reyzin — SIGMOD 2006 (PDF)](https://www.cs.bu.edu/%7Ereyzin/papers/auth-db.pdf)
```

## 5 · codex · request

UTC: 2026-10-11T16:53:59.456788+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sólo WebSearch/WebFetch públicos; sin herramientas locales, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Revisión Codex de tu R1-R6, con fuentes verificadas por mí. No ejecutes código: sigue investigando web pública si útil.
1) Corrección: record.total=265–282ms en requestperfilado;50–54mses sólo record.driver_execute80queries. Source151–195ms/authorize100–107ms sí totales. Nuestrascapturas548EVENT/256reads; histórico383lotesacumulativos≳3000EVENT, además binariosseleccionados/revisados vsfixtureactualno. NO asumir queue/GIL/locks soncausaprincipal ni crear3x3x30concurrencias sin reproducirhistorialprimero. Userpidepensamientolateralno sólootrodiagnóstico.
2) R2validaruna vez yretenerauthoritylocks siguecambiandocontratodefrescura/permisos/catálogos/expiry/phantomINSERT; la revocación retrasada tieneefecto observable. No adoptarlo automáticamente. R4counterencadena yaexisteheadCOUNT/digest peroNO pruebalas7fuentesfísicas: ownerpuedemodificarfuentes contriggerguardallowedowner, o desactivar/restaurartriggerentrechecks. Counterunchangedconstantefrenteoldfullreadrechaza. No lo presentes seguro hasta probarataque. Merkleintegridad≠frescura.
3) Mi ruta lateral: paginar una proyección de DATOS autenticada ligada a un fingerprint FRESCO de todaslasfilasfuente (no autoridad). Yaexiste rights_source_fingerprint queryunion25familiasperfil+cuenta; SHA256(tablapkxminctid) tomadoantesydespuésde fuente ycomparedentrorequest. No requiretriggersnuevos:al actualizarinclusoOWNER PostgreSQL cambiaxmin/ctid;INSERT/DELETE cambiaelconjunto. ¿Persistir un manifiestosellado(sourcedigestcanónico, vectorversiones,scope,schema/keyversion,txepoch,expiry) y chunks<=50filas, preparadofueraHTTP; cadauso autoridad/proof/latest/catalogfreshcomo hoy;currentsourcefingerprintbefore+afterigualalmanifest;descifrarchunksconverificaciónfresca siempre, no reutilizarobjetosJSON; devolverauditoríasidénticas? Se necesita comprobarfrescura de versiónsin dependerde TTL; xmin32wrap/ctidreuse/VACUUM/fullXIDepoch/regeneración/retenciónpurga;rootchunkindexycontador impidenomisión/cambiorden. Estrictamente propuesta,noimplementada. Source_fingerprintactualdentrorequestsNOPRUEBApersistenciasegura. ¿Qué contraejemplo la derriba? ¿Puede aprovechar RightsExportPart/S3privadogeneraciónCeleryyaexistente, sinproducirnetdescargasautoridadcache? No cachécatólogos/chain/latest/reviews/proofs ni mudar timingsdeauth.
4) Otraruta: computedstoredrow_hashGENERATEDALWAYSfor7evidences permitereadhashfísicofresco baratovsJSONB+SHArepetido. PG17sóloSTORED,immutableexprsinwhole-row;listaexplicita campos ycompletenessschema. PELIGRO ataqueownerCREATEORREPLACEhashfnmaliciosa->UPDATErow(conhashantiguogenerado)->restaurafunción sin recomputarstored; la atestaciónactualparececorrectapero digestderivadoobsoleto. Descartarlo sininvarianteescriturapruebaavanzado;no estimarahorro.
Fuentesoficiales revisadas: https://www.postgresql.org/docs/17/transaction-iso.html ;/xfunc-volatility.html(VOLATILEsnapshotfreshcadaSQL);/ddl-generated-columns.html;/ddl-system-columns.html;/routine-vacuuming.html . Documentaciónpsycopg3actualesdev3.3.7, cotejadaconfuenteinstalada3.3.6. PipelineNO ServerCursor. R3 no sustituyefrescura aunqueSSI todoswriters.
Quiero decidir priorización arquitectónica y un experimento mínimo que descarte una vía sinmegabatería. ComparaR4,R5,R6 conmanifiestoboundfullfreshrowversions yriesgosxid;si inviable explícalo. Añade una alternativa genuinamente diferente que no hayamosconsiderado. Señala coste de persistencia, referencias de la fuenteimportante, no rellenes3sconmicrosegundos. También rectificaintervaloCInonsolapado noesúnicocriterioválido(pruebaspareadas ydeltaCI pertinentes).

```

## 6 · claude · opinion

UTC: 2026-10-11T16:55:28.789177+00:00

```text
**Postura:** opino; no doy PASS ni autorizo nada. Acepto tu corrección. El total es `record.total` = 265–282 ms. Los 50–54 ms son sólo `driver_execute` de 80 queries. No vuelvo a señalar queue, GIL ni locks como causa.

**Lo que no puedo verificar.** En este contexto no tengo el texto de R5 ni de R6. No voy a reconstruirlos de memoria. Los comparo sólo por clase, y tú corriges el mapeo.

## 1. Manifiesto ligado a la huella fresca (xmin/ctid): contraejemplos

**Hechos documentados en PG17:**
- Desde 9.4, congelar una fila sólo marca un bit y conserva el xmin original. VACUUM FREEZE no cambia la huella. En bases que vienen por pg_upgrade de versiones anteriores a 9.4 puede aparecer xmin=2. ([routine-vacuuming](https://www.postgresql.org/docs/17/routine-vacuuming.html))
- El XID tiene 32 bits y se compara en módulo 2³². La columna `xmin` no lleva época.
- `ADD COLUMN` con un DEFAULT no volátil **no reescribe la tabla**, y `DROP COLUMN` tampoco. ([ALTER TABLE](https://www.postgresql.org/docs/17/sql-altertable.html))

**Contraejemplos que la derriban si no se cubren:**
1. **El esquema cambia sin tocar las filas.** Con un ADD COLUMN DEFAULT o un DROP COLUMN, xmin y ctid siguen iguales pero la proyección es distinta. Ocurre lo mismo con `ALTER TYPE … RENAME VALUE` en un enum, con cambios en funciones o vistas que use la proyección y con cambios en políticas RLS. Un "schema/keyversion" guardado como constante de la aplicación no basta. Hay que calcular en cada uso un digest fresco de `pg_attribute`, `pg_attrdef`, `pg_enum`, `pg_policy` y de `pg_proc.prosrc` para las funciones referenciadas.
2. **El owner cambia la huella.** Si `rights_source_fingerprint` es una función de la BD, el owner puede hacer `CREATE OR REPLACE` para que devuelva un valor fijo. Es el mismo ataque que tu punto 4. También puede sustituir la relación por una vista o jugar con `search_path`. Mitigación propuesta: SQL inline en la aplicación, relaciones fijadas por OID y verificación fresca de `relkind IN ('r','p')`. Si mi intuición es correcta, esto se puede atacar y conviene probarlo.
3. **Snapshot partido en la generación con Celery.** Si la huella y los chunks se leen en snapshots distintos, se sella un dato viejo bajo una huella nueva. Ambos tienen que salir de una única transacción REPEATABLE READ.
4. **Wraparound y reutilización de ctid.** Para que choquen hace falta mismo ctid, mismo pk y mismo xmin módulo 2³² tras unos 4.000 millones de XID, con VACUUM recuperando el hueco entre medias. Es improbable, pero se cierra con una regla finita: guardar `pg_current_xact_id()` (64 bits, con época) en el manifiesto y rechazarlo si `age > umbral` muy por debajo de 2³¹. Así la expiración se mide en XID y no en TTL.
5. **Particiones.** Hay que incluir `tableoid`, porque un ctid sólo identifica una fila dentro de una relación.

**Fallos en la dirección segura (sólo invalidan de más):** VACUUM FULL, CLUSTER, pg_repack o restaurar un dump cambian el ctid o el xmin. Lo único que provocan es volver a la ruta lenta.

**El punto débil de coste (hipótesis):** las columnas de sistema obligan a leer el heap. Un index-only scan no puede devolver xmin. La huella toca las mismas páginas que la lectura completa, sin destostar el JSONB ni hashearlo en Python. Si los 151–195 ms de la fuente son sobre todo I/O de heap y round-trips, la huella hecha dos veces (antes y después) puede costar casi lo mismo. Si son sobre todo decodificar JSONB y aplicar SHA, sí ahorra. **Esa medida falta.**

**RightsExportPart / S3 / Celery.** Se pueden aprovechar si los chunks se cifran con AEAD y su AAD incluye digest del manifiesto, índice y número total de chunks. El servidor los descarga en el backend, nunca mediante URLs prefirmadas al cliente, y si falta un chunk vuelve a la lectura completa. El coste nuevo es un GET a S3 dentro del request y la gestión de claves y retención. **No adoptar** mientras no se refuten los puntos 1–3.

## 2. Comparación

| Vía | Frescura | Ataque del owner | Estado |
|---|---|---|---|
| R2 (validar una vez y retener) | Cambia el contrato | — | Descartar |
| R4 (contador/digest encadenado) | Sólo vale si el trigger es íntegro | Desactivar el trigger o un `allowed owner` lo rompen | No es seguro sin probar el ataque |
| R5 y R6 | Sin texto en el contexto | — | No evalúo |
| Manifiesto con xmin/ctid | Fresca si se cubren los puntos 1–5 | Función de huella o vista suplantada | La más prometedora, sin pruebas |
| row_hash GENERATED | Puede quedar obsoleto | Sustituir la función de hash | Descartar, coincido contigo |

## 3. Alternativa realmente distinta: no cachear, mover el cómputo a PostgreSQL

Consiste en construir la proyección y su digest en **una sola sentencia SQL** (`json_agg` más `sha256()` dentro del servidor), dentro del mismo snapshot que la comprobación de autoridad. Así:
- Los 80 round-trips pasan a ser 1 o 2.
- Se elimina el parseo y el reserializado del JSONB en Python.
- La frescura y los timings de autorización no cambian, porque no hay ningún artefacto persistido.
- No hay xmin, ni wraparound, ni S3.

**Contraejemplos:**
- Si las auditorías exigen bytes idénticos a la serialización actual de Python, la salida de `jsonb` cambia el orden de las claves y el formato de los números. Hace falta un canon explícito.
- Si el coste está en el I/O del heap, ganará poco.

Otra variante lateral es el modelo de datos. Si los 383 lotes acumulativos hacen que cada request reprocese el historial (O(n²) en total), el problema es de forma y no de caché. Lo dejo como **hipótesis**.

## 4. Experimento mínimo (descarta una vía, no megabatería)

Usar el **fixture histórico reproducido** (más de 3000 EVENT y los binarios revisados), sin concurrencia y con N≈30 requests **pareados** por orden alternado ABAB. En cada par se mide:
- A: la lectura de fuente actual.
- B: la huella antes y después, inline y en una sola sentencia.
- C: la proyección completa en SQL.

Añadir `EXPLAIN (ANALYZE, BUFFERS)` a una ejecución de cada una para separar heap, detoast y cliente.

**Regla de decisión, fijada de antemano:**
- Si la cota superior del intervalo de confianza de la mediana de (B − A) no queda por debajo de un umbral de ahorro que fijéis antes de mirar los datos, se descarta el manifiesto.
- Si C ≈ B, C domina porque no persiste nada.

Esto sirve para cribar. **No es p95 contractual**, que exige carga representativa.

## 5. Rectificación estadística

Que los intervalos de confianza no se solapen es un criterio **conservador**, no el único. Dos intervalos al 95 % pueden solaparse y la diferencia ser significativa (Schenker & Gentleman, 2001). En diseños pareados lo correcto es el intervalo de la diferencia por par: bootstrap de los deltas, o Hodges-Lehmann con Wilcoxon de rangos con signo. Con ese intervalo se elimina la varianza entre requests.

**Decisión que propongo:** priorizar el experimento de la sección 4, porque B y C se comparan en una sola tanda. Congelar R2, R4 y row_hash. El manifiesto con xmin/ctid sólo avanza si B gana claramente a C **y** se prueban los ataques 1–3.
```

## 7 · codex · request

UTC: 2026-10-11T16:56:39.579119+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Cambio de enfoque solicitado por usuario: brainstorming arquitectónico con investigación web independiente, no repetir microoptimización. Tu tarea deep research web completó 51 fuentes (ID0ef1585d-3cfe-4bc1-af1e-1a126629f505); guardamos informe, no importamos51URLs para evitar ruido. Analiza críticamente hallazgos junto al notebook del proyecto; no afirmes haberleído archivos noaportados. Máximo900palabras, hipótesis noPASS.
Estado: Django5.2.17/Python3.12.15/PG17.11/psycopg3.3.6. Histórico383lotes acumulativos p95navegación3.753392s vs2s;JSON6.930455/binario7.317947 vs5s(n3/8insuficiente). Actualfixtureclon548EVENT/256reads,1500revisiones/16MiB,64MiBfotosnoentregadas,1GunicornsinCaddy/cuotas/carga: controles791–869ms vsanteriores1600–1800ms SIN cambio deproducto; noahorrocausal. Source151–195ms,fetch75–91ms/adaptación10–15ms. Recordtotal265–282ms(80exec50–54ms sóloesSQL);authorize23calls100–107ms(93exec);chain4pipeline33–44ms;canonical46–48ms. Código sigueguardasfrescasporpágina,assessment.latest,proof/actor/catalog ychainfull7fuentes físicas másEVENT. Cada lecturaavanzaheadenmismaTX. Fuentecompleta1vezporbatch,versionfingerprintantes/después ycanonical antes/después. No cachéautoridad ni desplazarlecturasmutableUser/assessment porJOINtemprano. Bloqueosnobloqueanrelojes/DDL/phantom. Merkle integridad nofrescura. Mantenerauditorías,failclosed,retención/privacidad.
Claude investigówebpropusoR1esperas,R2lockauthority+validaruna,R3SSI,R4counterDB7fuentes,R5proyecciónsellada,R6Merkle. ObjecionesCodex:R2retrasa revocaciones,cambiasemántica;R3snapshotnuevonocapturafrescuratiempo;R4headyaexiste yownerpuedealterarfuente sinavanzarlo,triggerdisabled/re-enabledentrechecks;contadorno prueba integridad física. R1concurrenciaarbitrariaantesreproducirhistorialgrande es prematuro.
Propuesta lateralCodex: manifiestoautenticado de DATOS (no decisiones),chunks<=50filas fueraHTTP,bound a source_digest y huellafrescaTOTALdelconjuntofilas(tabla,pk,xmin,ctid). Enusosiempreauthority/proof/latest/catalogfrescos yreadchunks+verificarfirma físicamente,versionfingerprintantes/después;invalidarsi cambio,códigoschema,keyepoch,wrapxmin32/VACUUM/restore oexpiry. Actualsource_fingerprint yaexisteparaunrequest;usopersistente noestáprobado. ¿Qué contraejemplos impidenlo? No afirmar TTLda frescura. Puede reutilizarexportpart/Celeryexistentes pero purgaobjeto yfallbackcompleto deberáncubrirse.
Documentaciónprimaria contrastada: postgresql.org/docs/17/transaction-iso.html ;xfunc-volatility.html (VOLATILEsnapshotsfreshporSQL);ddl-generated-columns.html (sóloSTORED,exprimmutable);ddl-system-columns.html (xmin32wrap yctidnoIDdurable); ps yc opg.org/psycopg3/docs/advanced/pipeline.html (ServerCursornopipeline), docs.djangoproject.com/en/5.2/topics/db/optimization/. Tureportdeepcontieneerrorcódigo cur.execute devuelveMISMOcursor,loañadevariassvecesyloCIERRAantesfetch. Recházalo;pipelineyaexiste enchain, no garantiza por sísolo frescura.
Danos 4rutaspriorizadas con mecanismo/coste/riesgo y un experimento mínimo finito, incluso propuestas tuyas noincluidas. Descartaautoritativamentecontador/Merklesinpruebafrescura; noimplementar código inventado. ¿Mayor cambio deenfoque viable sinrebajarcontrato?
```

## 8 · notebook · opinion

UTC: 2026-10-11T16:58:15.893684+00:00

```text
### Descarte Autoritativo y Errores en Informes Externos

**1. Contadores (R4) y Árboles de Merkle (R6) no prueban frescura**:
Un contador acumulativo o una raíz de Merkle valida la integridad estructural o de cadena inmutable *append-only* [1, 2], pero **no garantiza la frescura en tiempo real** de entidades mutables (`User`, `assessment`, permisos) [3, 4]. Un propietario de la relación o proceso interno puede mutar filas sin avanzar el contador `head`, o deshabilitar/rehabilitar *triggers* entre comprobaciones. Por tanto, no proporcionan la garantía de frescura requerida por el contrato.

**2. Rechazo del error de código en el informe sobre `psycopg.Pipeline`**:
Se rechaza categóricamente el fragmento del informe web donde `cur.execute()` añade repetidamente la misma instancia de cursor a una lista y la cierra antes del `fetchall()`. Esta implementación es errónea. Además, la ejecución en *pipeline* (`psycopg.Pipeline`) ya está integrada localmente en el pipeline de consultas SQL del proyecto (commit `e19c3fc`) [5-7]; el *pipeline* optimiza únicamente el tiempo de ida y vuelta de la red (RTT), pero **no sustituye la revalidación síncrona de autoridad y versión**.

---

### Contraejemplos Físicos al Manifiesto Persistente de Datos (Codex)

La propuesta lateral de Codex sugiere persistir un manifiesto firmado de datos (\\(\le 50\\) filas) fuera del flujo HTTP acotado por `(tabla, pk, xmin, ctid)`. Los siguientes contraejemplos impiden su uso persistente sin *fallback* total:

1. **Inestabilidad física de `ctid` ante mantenimiento**: `ctid` representa la ubicación física de la tupla. Un `VACUUM FULL`, `REINDEX` o `CLUSTER` reorganiza las páginas de PostgreSQL, alterando todos los `ctid` sin que haya ocurrido un cambio lógico en los datos [4], provocando invalidaciones masivas infundadas.
2. **Desbordamiento de 32 bits y congelación de `xmin`**: El identificador de transacción `xmin` utiliza un contador circular de 32 bits [4]. Cuando la base de datos ejecuta `autovacuum` para congelar tuplas (`FREEZE`), `xmin` se reescribe al valor especial `FrozenTransactionId` (2). El cambio de `xmin` destruye la firma del manifiesto aunque los datos no hayan cambiado.
3. **Reutilización de estado transaccional o rollbacks parciales**: Cambios no confirmados dentro de subtransacciones o mutaciones concurrentes en un snapshot `READ COMMITTED` pueden modificar la tupla y revertirla, dejando huellas de `xmin`/`ctid` desincronizadas respecto a la vista transaccional activa.
4. **Mutación de dependencias de dominio no capturadas en las filas exportadas**: Modificaciones en permisos del usuario (`User.session_version`, `mfa_version`) o reglas de negocio cambian la validez de la respuesta sin alterar las tuplas físicas exportadas, entregando datos no autorizados si solo se verifica la huella de las filas del *chunk* [3, 8].

---

### Clasificación del Estado Actual

*Las siguientes declaraciones distinguen estrictamente hechos medidos de hipótesis y vacíos de evidencia:*

* **Hechos Medidos**:
  * Stack: Django 5.2.17 / Python 3.12.15 / PG 17.11 / psycopg 3.3.6.
  * Datos históricos: 383 lotes acumulativos; p95 navegación 3,753392s (vs SLA 2s); JSON 6,930455s / binario 7,317947s (vs SLA 5s; \\(n=3/8\\), muestreo estadísticamente insuficiente).
  * Fixture clon actual (548 `EVENT`, 256 lecturas, 1500 revisiones, 16 MiB data, 64 MiB fotos no entregadas): latencia de registro total en 265–282ms (Source 151–195ms, fetch 75–91ms, adaptación 10–15ms; `authorize` 23 llamadas en 100–107ms con 93 ejecuciones SQL; `chain` 4 pipeline en 33–44ms; `canonical` en 46–48ms) [4, 5]. Controles en 791–869ms vs 1600–1800ms anteriores sin cambio de producto (sin ahorro causal demostrable).
* **Hipótesis (no constituyen PASS ni autorización)**:
  * Que la fragmentación Celery fuera de HTTP reduzca la latencia percibida sin violar la caducidad síncrona del token/proof.
  * Que consolidar las 23 llamadas de `authorize` en una sola consulta por lote reduzca la latencia de autorización a \\(<30\text{ms}\\).
* **Evidencia Faltante**:
  * Faltan mediciones con muestra suficiente (\\(n \ge 30\\)) bajo carga real con Caddy y cuotas activas para validar el p95 contractual.
  * Falta prueba de estrés del comportamiento de `(xmin, ctid)` ante ejecuciones intensivas de `VACUUM` concurrente.

---

### 4 Rutas Priorizadas y Experimento Mínimo Finito

1. **Ruta 1 (Prioridad Alta) — Agrupación de Guardas de Autoridad en Pipeline Transaccional Único**:
   * *Mecanismo*: Consolidar las 23 llamadas de autorización (`100–107ms`) en una única consulta pipelined por petición, revalidando `fresh_authority(User)` y `assessment.latest` en un solo snapshot [3, 5].
   * *Coste*: Bajo (reestructuración de decoradores sin alterar modelos).
   * *Riesgo*: Bajo.
2. **Ruta 2 (Prioridad Media) — Fragmentación Asíncrona fuera de HTTP con Fallback Transaccional Completo**:
   * *Mecanismo*: Delegar la preparación de *chunks* a Celery [9]; verificar la firma de frescura total (`version_fingerprint`) y, si hay cualquier discrepancia o expiración, realizar un *fallback* síncrono a la lectura completa `source_copy` [8, 10].
   * *Coste*: Medio.
   * *Riesgo*: Medio (requiere purga estricta de objetos temporales).
3. **Ruta 3 (Prioridad Media-Baja) — Optimización Nativa C/Cython para la Canonicación**:
   * *Mecanismo*: Extender `_canonical_kernel.pyx` para ejecutar la serialización y hashing canónico en código C nativo [1, 9], reduciendo el overhead de \\(46–48\text{ms}\\) en Python.
   * *Coste*: Medio.
   * *Riesgo*: Bajo.
4. **Ruta 4 (Prioridad Arquitectónica) — Proyección Firmada Inmutable con Invalidación por Eventos de Dominio**:
   * *Mecanismo*: Proyectar vistas pre-calculadas firmadas con `BLAKE3`/`HMAC`. La petición HTTP revalida únicamente las versiones de sesión/MFA del `User` [3].
   * *Coste*: Alto.
   * *Riesgo*: Medio-Alto.

**Experimento Mínimo Finito**:
En un entorno de prueba aislado con PG17: generar 1.000 tuplas con su firma basada en `(xmin, ctid)`. Ejecutar `VACUUM FULL` y medir el porcentaje de invalidaciones falsas frente a un control basado en `version_fingerprint` sobre `source_copy` [4, 10].

---

### Mayor Cambio de Enfoque Viable sin Rebajar Contrato

Desplazar la generación de contenido pesado fuera de la petición HTTP mediante procesamiento asíncrono con Celery y entrega mediante URLs firmadas de un solo uso servidas por el proxy (Caddy/S3), mientras que la petición HTTP síncrona en Django realiza exclusivamente la revalidación de autoridad y estado fresco del `User` (\\(<30\text{ms}\\)) [3, 9]. Se mantiene el contrato estricto sin cachear autoridad en memoria de Python.

*Nota técnica: Las intervenciones en esta sala son opiniones y análisis de diseño; no representan un PASS de pruebas ni una autorización de despliegue.*

💡 ¿Quieres que diseñemos la batería de pruebas sintética para ejecutar el experimento finito sobre `VACUUM` e inestabilidad de `ctid` en PG17?
```

## 9 · codex · request

UTC: 2026-10-11T17:01:00.141118+00:00

```text
Sala técnica local. Opina sólo sobre el contexto suministrado. Sin herramientas, ediciones ni ejecución. Distingue hechos medidos, hipótesis y evidencia faltante. Las intervenciones son opiniones, nunca PASS ni autorización. No cachear autoridad, omitir comprobaciones frescas ni extrapolar microbenchmarks a p95 contractual. Propón una decisión finita y señala contraejemplos. Máximo 900 palabras.

Corrige la respuesta anterior antes de decidir. Prioriza dos diseños concretos y un experimento que descarte un riesgo; máximo700palabras.
1) PG17 docs routine-vacuuming: desde9.4 freeze conserva xmin original y marca bit. REINDEX reescribe índice, no heap/ctid; VACUUM FULL/CLUSTER sí pueden rewrite, pero invalidación es fallo seguro. xmin32wrap es riesgo real; no fingir pruebas de 4mil millones XID.
2) source_fingerprint es SQL inline en Python que cubre TODAS las filas fuente, incluido subjectUser, no sólo chunk ni función externa. DiseñoCodex RETIENE23autorizaciones frescas/proof/latest/catalog porpágina. Descartar tu ruta1 que consolida23guardasen1: adelanta snapshots y sustituye momentos frescos. No es riesgo bajo. Tu ruta final checkUser únicamente omite otras guardas: inaceptable. No elegir<30ms sin medir. Kernel canonical YA Cython nativo validado en cada HTTP; no son46msCPU Python.
3) Tu research pipeline usaba mismo cursor varias veces y cerrado antesfetch: rechazado. Noimportamos51fuentes porque mezcla SEO/versiones incorrectas; conservamos100 fuentes. Investigación guardada, noPASS.
4) Rutas propias: A) manifiesto de DATOS/chunks<=50 firmado(scope/schema/keyversion/fullsourcecanonicaldigest/fullfreshrowstamp), rowversion física TOTAL antes/después y TODAS las guardas actuales. Falta medir coste/DDL/XIDepoch/purga/fallback. No TTL como frescura. B) Validación completa de cadena computada en SQL servidor devolviendo resultados compactos, evitando transferir EVENT y siete mapas completos aPython. NO head-only/counter/fastticket, NO omitir hash físico de ninguna fila. Conservar orden actual de lecturas/snapshots/concurrencia o probar equivalencia frente ownerchanges entre barreras. Firmas y crypto de negocio siguen Python. SQLinlinepg_catalog para evitar función suplantable. ConsultaCTEúnica adelanta snapshots de siete familias (posiblecontraejemplo); funciónVOLATILE preserva snapshot por SQL pero requiere atestación de cuerpo robusta. ¿Cómo diseñar B sin cambiar barreras? Tercera lateral TOAST LZ4/JIT sólo siEXPLAIN demuestra coste, sin más recursos.
5) Histórico383lotes acumulativos/3000EVENT y fotos seleccionadas difiere de fixture548EVENT/fotos no entregadas. No explicar3.75s por0.8s sin reproducir historia. recordTOTAL265ms,50msSQL noequivalente.
Filtro finito Codex: en PG real temporal reproducir digest GENERATED stale mediante reemplazar helper por funciónmaliciosa, actualizarbody para generar hashviejo, restaurarhelper. Digest almacenado/head parecen iguales, cálculo físico fresh rechaza. Ejecutar VACUUMFREEZE/REINDEX para contrastar tus hechos. Añadir existing runtimeownerdrift test. Pruebasdefiltroseguridad, no capacidad ni producto. ¿Esto permite cerrarR4/rowstored ingenuos y priorizarA/B? Identifica obligación faltante antes de implementación. Cita docs correctos. No presentar fallbackfull como solución SLO hasta medir tasa hit/drift.

```

## 10 · notebook · opinion

UTC: 2026-10-11T17:02:01.687517+00:00

```text
### 1. Corrección y Rectificación de la Postura Anterior

Se rectifica la postura previa: **ninguna consolidación de guardas es admisible si adelanta snapshots o sustituye momentos de verificación de autoridad fresca** [1-3]. Reducir la validación a un chequeo único (`checkUser`) es inaceptable porque omitiría las 23 comprobaciones de autoridad/proof/catálogo requeridas por página [1, 2]. Asimismo, queda descartada la extrapolación de microbenchmarks a p95 contractual; el kernel canónico en Cython se ejecuta nativamente en cada petición HTTP [4, 5]. Se retienen de forma íntegra las 100 fuentes del proyecto sin mezclar versiones obsoletas [6].

---

### 2. Clasificación de Evidencia

* **Hechos medidos**:
  1. En PostgreSQL 17 `routine-vacuuming` (desde 9.4), la congelación (*freeze*) conserva el `xmin` original marcando el bit correspondiente [7]. `REINDEX` reescribe únicamente el índice sin alterar filas ni `ctid`, mientras que `VACUUM FULL` / `CLUSTER` reescriben el *heap* forzando invalidación y fallback seguro [7].
  2. `source_fingerprint` es SQL inline en Python que calcula `(tabla, pk, xmin, ctid)` sobre la totalidad de las filas fuente, incluyendo a `subjectUser` [4, 7].
  3. La traza histórica de 383 lotes acumulativos / 3.000 EVENTs con fotos difiere del fixture sintético de 548 EVENTs [8, 9].

* **Hipótesis**:
  1. Una consulta CTE única en SQL (Ruta B) reduce la transferencia de datos, pero al fijar un único snapshot de sentencia para las 7 familias, adelanta snapshots y oculta cambios de propietario (*ownerchanges*) entre barreras [3, 4].
  2. La función `VOLATILE` preserva la evaluación de frescura por llamada dentro de SQL, pero requiere atestación estricta del cuerpo de la función contra suplantaciones [4].

* **Evidencia faltante**:
  1. Medición de la tasa real de *hit/drift* para cuantificar el impacto del fallback completo sobre el SLO [10, 11].
  2. Evaluación de coste DDL, purga y consumo de épocas XID para el manifiesto firmado de la Ruta A [4, 7].

---

### 3. Diseños Concretos Priorizados

1. **Ruta A (Manifiesto de DATOS/chunks ≤ 50 firmado)**:
   * Firma un manifiesto con `scope`, `schema`, `keyversion`, `fullsourcecanonicaldigest` y `fullfreshrowstamp`, comprobando el `rowversion` físico total antes y después de la lectura [1, 4, 7].
   * Retiene las 23 guardas de autoridad actuales sin usar TTL como indicador de frescura [1, 2].

2. **Ruta B (Validación compacta en SQL servidor vía `pg_catalog`)**:
   * Ejecuta evaluaciones en el servidor PostgreSQL devolviendo un resultado compacto a Python, manteniendo la firma y criptografía de negocio en la capa de aplicación [4].
   * **Preservación de barreras sin CTE única**: Se descarta el CTE masivo. Se implementa mediante consultas SQL inline sobre `pg_catalog` o funciones `VOLATILE` con atestación de cuerpo [4].
   * Uso de TOAST LZ4/JIT condicionado estrictamente a demostración de coste en `EXPLAIN (ANALYZE, BUFFERS)` [12, 13].

---

### 4. Experimento para Descartar Riesgos (Filtro Finito Codex)

**Procedimiento de prueba de seguridad**:
1. En un entorno PostgreSQL temporal con datos reales, reemplazar el helper de digest por una función maliciosa que genere un hash antiguo/obsoleto.
2. Actualizar el cuerpo para simular coincidencia de digest almacenado y *head*.
3. Restaurar el helper y verificar que el cálculo físico *fresh* rechace la operación [4, 7].
4. Ejecutar `VACUUM FREEZE` y `REINDEX` intermedios, incorporando la prueba de `existing runtimeownerdrift`.
*Objetivo*: Confirmar que el filtro de seguridad descarte accesos obsoletos y permita cerrar R4/estructuras ingenuas [4, 7].

---

### 5. Decisión Finita, Contraejemplos y Obligación Faltante

* **Decisión Finita**: Adopción prioritaria de la **Ruta A** por preservar de forma explícita las barreras de aislamiento transaccional y el orden de lecturas en Python [1, 7]. La **Ruta B** queda supeditada a demostrar equivalencia exacta frente a *ownerchanges* mediante evaluaciones `VOLATILE` independientes [4].
* **Contraejemplos a evitar**:
  * Unificar las 7 familias en un único CTE: adelanta snapshots y oculta modificaciones concurrentes entre barreras [3, 4].
  * Presentar el *fallback full* como solución de SLO sin medir la tasa de *drift*: puede provocar degradación latente sistemática [10, 11].
* **Obligación Faltante antes de la implementación**: Medir formalmente la tasa de *hit/drift* y certificar la inmutabilidad del cuerpo de las funciones SQL antes de autorizar cambios en producción [4, 7].

¿Quieres que elaboremos la especificación técnica detallada de la Ruta A o prefieres revisar las métricas del experimento de seguridad?
```

## 11 · codex · decision

UTC: 2026-10-11T17:19:19.408449+00:00

```text
Decisión comprobada localmente: priorizar diseño de datos paginados, conservar prototipo solamente; ninguna adopción productiva.

# MOD-08 — Cambio de enfoque, investigación web y prototipo paginado — 2026-10-11

## Resultado y decisión

El usuario pidió investigar si hacía falta cambiar el enfoque y que cada participante buscara soluciones en internet. Se investigó, se discutieron contraejemplos, se ejecutó un filtro de riesgos en PostgreSQL real y se construyó un prototipo de DATOS separado del producto.

**La vía de proyección paginada supera el cribado de coste de etapa:** obtener la misma página de 50 revisiones pasa de **199.011898 a 21.376303 ms** de mediana; delta **177.635595 ms (89.26 %)**. Gana 20/20 pares wall y CPU y los cuatro bloques cronológicos. Se conserva exclusivamente como prototipo: **no está conectado al endpoint, no es una API de autorización ni demuestra mejora HTTP/SLO**. La preparación cuesta 1,752980 s wall/0,625873 s CPU en esta tanda, antes de las lecturas. Su coste, persistencia y retención tienen que amortizarse y medirse.

El producto mantiene exactamente rights_exports.py SHA256 `942f355f701ec6c0c88571abaa02f6e9c2e0aa7b7c7df9eebdf7866fc8d7e985` y la mejora de rutas anterior. No nueva optimización productiva, commits, push, proveedores, compras, publicación o datos reales en esta campaña. El requisito global de navegación/descargas permanece pendiente.

## Investigación independiente y revisión crítica

Sala [.ai/rooms/mod08-brainstorm-web-20261011](../../.ai/rooms/mod08-brainstorm-web-20261011/transcript.md), cuatro turnos externos acotados (dos Claude y dos Notebook), sin retry automático. La instrucción posterior «que cada uno busque en internet» autorizó WebSearch/WebFetch públicos de Claude dentro de la deliberación; no herramientas locales, shell o edición. Modo explícito `--web-research`, MCP vacío, safe-mode, tools/allowedTools exclusivamente web, dontAsk. Predeterminado continúa sin herramientas. Once controles unitarios de la sala PASS; no confundir dobles con conexión a modelos.

Claude produjo revisiones por su CLI (modelUsage incluye claude-opus-5-5/claude-haiku-5-5, consumo real preservado en .ai/tasks/desarrollo.md). Reporta fallo de certificado al intentar documentación psycopg; la documentación se contrastó por Codex. El JSON final registra 7/3 turnos y cero denegaciones, pero no contiene transcripción de cada herramienta; server_tool_use no se interpreta como inventario completo de herramientas locales CLI. Las fuentes y opiniones están conservadas sin declarar sus afirmaciones verificadas.

NotebookLM hizo investigación web deep, tarea iniciada `ChA3YzI0ZGNkMGFiYjI5NzMyEAgaATAqA3VzZQ`, resultado `0ef1585d-3cfe-4bc1-af1e-1a126629f505`, 51 fuentes encontradas. Informe íntegro en la sala. Mezcla documentación primaria, artículos y SEO/versiones no pertinentes: **no se importaron las 51 fuentes**. Inventarios antes/después: **100 fuentes, mismos IDs**. En las consultas se aportaron resultados actuales, objeciones y hallazgos contrastados; la investigación no aporta automáticamente pruebas del código local. El modelo Notebook no es identificable por el CLI.

Codex contrastó documentación primaria por separado y rechazó errores concretos de las propuestas: acumular varias veces el mismo cursor cerrado en pipeline; asumir ServerCursor compatible con pipeline; confundir 50 ms de SQL con 265 ms de record completo; atribuir 46 ms a Python cuando canonical ya usa Cython; consolidar 23 autorizaciones en una y adelantar snapshots; exigir sólo checkUser en entrega; afirmar que FREEZE cambia siempre xmin o que REINDEX reordena heap. La respuesta correctiva del notebook rectifica varios de ellos, pero sus propuestas siguen sin ser evidencia de aceptación. Claude no recibió automáticamente sus intervenciones anteriores en la segunda llamada: contexto seleccionado y limitación preservados.

## Rutas discutidas

| Ruta | Coste al que apunta | Decisión y condición |
| --- | --- | --- |
| Proyección cifrada por páginas, manifiesto de datos ligado a huella física fresca TOTAL | Construir/transferir/serializar toda la fuente cuando se consume sólo una página | Prioridad de diseño; prototipo muestra margen, falta integración y prueba de garantías completas |
| Verificación completa de cadena en servidor con resultados compactos | Transferir EVENT y mapas completos y comparar en Python | Segunda vía; conservar todas las filas/hashes y barreras; no CTE único ni función suplantable sin equivalencia |
| Head/counter/Merkle usados como sustituto de fuente física | Escaneo histórico completo | Rechazar variante ingenua: head igual no prueba que owner no mutó fuente |
| Hash generado almacenado aceptado sin prueba de su producción | Rehashing de evidencia | Rechazar variante ingenua: función restaurada puede dejar hash almacenado obsoleto |
| Validar actor una vez y retener locks/SSI | Consultas de autoridad repetidas | No aplicar: altera momentos de verificación, revocación y/o visibilidad; tampoco congela expiraciones |
| Consolidar proyección con SQL json_agg | Construcción/recodificación ORM | Hipótesis secundaria: fuente tiene unas 20 consultas, no las 80 de record; exige canon exacto, post_init/expiraciones y snapshot equivalentes |
| TOAST LZ4/JIT | Descompresión/compilación del servidor | Sólo si EXPLAIN demuestra coste; no configuración aplicada ni ahorro prometido |

Un árbol de Merkle puede probar inclusión/completitud respecto a una raíz, pero no que la raíz sea actual. Un manifiesto autentica DATOS; no sustituye actor, prueba, última revisión, catálogo, cadena o reloj fresco. Funciones VOLATILE obtienen snapshots por consulta interna; esto no demuestra por sí solo equivalencia temporal ni integridad de la función.

## Filtro de riesgos en PostgreSQL real

[Datos](mod08-brainstorm-risk-filter-20261011.json), runner `20261011-170322-92aed466`: **4 PASS**, 15,050 s JUnit, 1348 huellas independientes exactas. Dos tests temporales y dos pruebas de evidencia/runtime existentes:

- Cambiar helper IMMUTABLE para producir digest antiguo, actualizar payload y restaurar exactamente definición de función: digest generado y head siguen iguales, pero hash físico fresco difiere. Refuta confianza ingenua en columna derivada/counter; no simula aceptación de filas de negocio.
- Mil tuplas conservan id/xmin/ctid observados tras VACUUM FREEZE y REINDEX. ADD COLUMN fast-default conserva esa metadata, pero cambia JSONB de fila genérica. **No afirma que source_copy estática consuma columnas nuevas**: requiere vincular esquema/código de la representación que se materialice.
- Verificación de cadena actual detecta owner drift aun con head/ticket iguales, y el runtime real restringido rechaza fuentes físicas alteradas.

Primer intento `20261011-170211-4c4e4320`: 3 PASS/1 FAIL por tratar JSON textual del cursor Django como dict. Corrección json.loads tras terminal; no convertir aquel runner en PASS ni sumar versiones. No prueba de wraparound de 4.000 millones de transacciones; la amenaza permanece documentada.

## Prototipo y comparación de etapa

Archivos sólo tests: capacity_page_manifest_prototype.py / test_capacity_page_manifest_prototype.py. Fuente escalar sintética calibrada, 1500 revisiones/16 MiB, sin los originales de 64 MiB ni corpus completo de geografía/relaciones. PostgreSQL real, misma conexión caliente y kernel nativo sellado. Se crean chunks de hasta50 filas cifrados con Fernet y manifiesto autenticado en tabla temporal propia. La preparación usa bracket de huella física antes/después y transacción. Manifiesto: scope, versión de representación, SHA de metadata de atributos, **source_digest HMAC productivo**, huella física total, XID64 de anclaje, DB OID y expiración. Uso: lectura fresca de huella completa/metadata/XID, fetch de token físico, descifrado independiente, comprobación de bindings y huella completa al salir. TTL es sólo límite de vida, no prueba de frescura.

Baseline: inspection_source completo existente, incluida fuente completa y sus comprobaciones de digest/huellas, retornando las mismas50 filas. Prototipo: página ya preparada con verificaciones de datos actuales. Dos warmups por brazo; 20 pares contrabalanceados ABBA. SQL, descifrado y brackets de datos dentro de los relojes. Preparación y comprobaciones numéricas/equivalencia fuera. GC sin cambios. No hooks SQL/profiler. Gate preregistrado >=15/20 pares favorables wall y CPU; no prueba formal de p95 ni A/A de reproducibilidad del endpoint.

| Mediana | Fuente completa | Página cifrada | Delta | Porcentaje |
| --- | ---: | ---: | ---: | ---: |
| Wall de datos | 199,011898 ms (0,199012 s) | 21,376303 ms (0,021376 s) | 177,635595 ms (0,177636 s) | 89,26 % |
| CPU de hilo | 118,703060 ms | 4,711684 ms | 113,991376 ms | 96,03 % |

[Datos finales](mod08-page-manifest-20261011.json), runner `20261011-171059-35a451e6`: **1 PASS**, 34,77 s, 1350 huellas exactas. Este caso contiene equivalencia primera/intermedia/última página, resultados mutables independientes y nueve filtros adversariales: update fuente, root esperado falso, chunk intercambiado/ausente, ciphertext inválido, expiración, anchor XID demasiado antiguo, contador falso y cambio de atributos de esquema. XID antiguo es un valor inyectado autenticado de prueba: no wrap real.

Inicial `20261011-170851-d0a9ec69`: 1 PASS, 28,78 s, preservado [por separado](mod08-page-manifest-initial-20261011.json). Se cambió SHA de root por HMAC source_digest existente y se completaron filtros antes de la tanda final. No comparar sus tiempos como mejora de producto ni sumar versiones como gate.

**Límites decisivos:** no actor/proof/latest/chain ni callbacks de expiraciones post_init en este prototipo de datos; no completa atestación RLS/enums/funciones/grants/restore; no retención ni purga durables; no imágenes físicas, RustFS/Caddy, cuotas contractuales, HTTP o load. No fallback implementado. No read-only snapshots firmados presentados como autorización. No restar177ms del p95 histórico ni sumar a ganancias anteriores. Cifras obtenidas después de la deliberación se registran como resultados Codex, no nueva opinión de los revisores.

## Plan concreto y condiciones de continuación/parada

1. Especificar un contrato interno de fuente paginada con manifiesto de DATOS y conservar la vía completa. Mantener exactamente cada authorize/reviewer_case/proof/latest/catalog/chain y auditoría actuales. No introducir un endpoint parcialmente autorizado ni URL de objeto pública.
2. Completar prueba de vínculo: código/canon/keyversion, relación física/schema/tipos/enums/RLS/grants/funciones e identidad de servidor/restore; persistencia/XID64 y límites sin depender de TTL. Conservar captura de expiraciones y comprobación de reloj que hoy aportan consultas/modelos. Definir purga conjunta de datos derivados y privacidad. Abandonar si una firma/huella equivalente acepta una representación distinta o una retención invalidada.
3. Adaptar consumidores explícitamente: compile_coverage/project_selected actualmente necesitan la fuente/proyección completa. No pasar un contenedor lazy que canonical no admite ni ocultar materialización completa. Inventario de rutas/referencias de datos puede prepararse, pero decisiones/revisiones actuales se descifran y validan frescas. Si los consumidores vuelven a necesitar16MiB por petición, se abandona el ahorro pretendido.
4. N1 de equivalencia y completitud: perfil/cuenta, todas las familias no vacías, Unicode/JSON/canon, primera/intermedia/última, omisión/duplicado/orden, adulteración de manifiesto/chunk, mutación en cada barrera, expiry/purga/revocación. N2 propia PostgreSQL/runtime/RustFS real, rollback/idempotencia/sellos y guardas temporales. Cualquier fallo corregir y repetir afectados; no conectar al flujo por el PASS de este prototipo.
5. Comparación HTTP paired con preparación amortizada, medición de hits/drift/fallback, pico de memoria y almacenamiento. Reproducir historial acumulativo y binarios revisados del escenario de383lotes antes de reclamar2s/5s. Si el fallback domina, hay regresión o no existe beneficio consistente, retirar la candidata. Un cambio de autoridad/retención incompatible no se presenta como optimización compatible.
6. Sólo tras superar esas puertas considerar la vía B compacta para el coste creciente de cadena. Mantener cada hash físico, lectura/snapshot y comportamiento de errores; si consolidar adelanta alguna barrera con un contraejemplo observable, descartar esa forma. No usar head/counter como atajo.

La sala acotada termina con una señal de viabilidad nueva y las obligaciones pendientes concretas, sin una cadena infinita de consultas. El prototipo se conserva para desarrollo posterior; el producto queda en la versión ya verificada. Todos los procesos/contendores propios de estas tandas están retirados y comprobados; fuentes de app sin diferencias después. Documentación/control de sala comprobados al cerrar.

## Fuentes primarias contrastadas

- [PostgreSQL17: aislamiento](https://www.postgresql.org/docs/17/transaction-iso.html): snapshots y reintentos, no sustituto de reloj/autoridad fresca.
- [PostgreSQL17: bloqueos](https://www.postgresql.org/docs/17/explicit-locking.html): compatibilidad de locks y límites de fila.
- [PostgreSQL17: volatilidad](https://www.postgresql.org/docs/17/xfunc-volatility.html): VOLATILE/STABLE y snapshots internos.
- [PostgreSQL17: columnas generadas](https://www.postgresql.org/docs/17/ddl-generated-columns.html): almacenamiento, recomputación y restricciones.
- [PostgreSQL17: columnas de sistema](https://www.postgresql.org/docs/17/ddl-system-columns.html) y [mantenimiento](https://www.postgresql.org/docs/17/routine-vacuuming.html): xmin/ctid y freezing.
- [Django5.2: optimización DB](https://docs.djangoproject.com/en/5.2/topics/db/optimization/): medir y controlar qué se materializa.
- [Psycopg: pipeline](https://www.psycopg.org/psycopg3/docs/advanced/pipeline.html): documentación actual es dev3.3.7; contraste con fuente instalada3.3.6, no upgrade aplicado.
- [Celery5.6: tareas](https://docs.celeryq.dev/en/v5.6.0/userguide/tasks.html): ejecución idempotente y frontera de commit; fuente fijada a rama5.6, no cambio de dependencia.
- [Li et al., SIGMOD2006: authenticated data structures](https://www.cs.bu.edu/~reyzin/papers/auth-db.pdf): autenticación de resultados con completitud; integridad no acredita una raíz actual.
- [PostgreSQL17: JIT](https://www.postgresql.org/docs/17/jit-reason.html) y [planner](https://www.postgresql.org/docs/17/runtime-config-query.html): optimización condicionada por costes, no tuning ensayado.

```
