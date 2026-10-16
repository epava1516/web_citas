# CR09: ROI del prototipo con serialización corregida

Run044611-b9dccd73,SHA5c3e171,**1PASS104,31s**,3bloquesABBA,ingest+processrealesseed782134+6lecturasanónimassecuenciales/10kPGpropio. No perfilador/Celery/Beat/socket/concurrencia. Dirty1actual/0candidato,cuerpos/status/no-storeexactos. Costeescrituraincluido,stackimagenwarmprevio/fixturecleanup/refreshprearmfuera intervalo.

| Bloque | Wallactual→fenced s | CPUactual→fenced s | Escrituraactual→fenced s |
|---|---:|---:|---:|
|0|2,2936→1,9748|1,3434→1,2741|0,4832→0,7076|
|1|2,4880→1,8291|1,5059→1,1695|0,4287→0,4949|
|2|2,3966→1,8380|1,5386→1,0867|0,4668→0,6323|

Totalreduce13,9–26,5%enlos3bloques;CPUtambiénmenor,escrituramáslenta. ActualDirtypersiste6lecturas:puedeexagerarROIfrenteBeatreal. No aceptarSLO/producircarga15minapartirdeesto. Fencedcorrigecontrapruebaunfencedpreservada encr09-private-publication-race-20261016.md;12controles+7concurrenciapasaronenalcancesdeclarados,nopruebadeausenciageneraldedeadlocks.

JustificaprepararmigraciónreversibleconSQLidéntico(normalizandonombresdehelpers) yN2sobreSQLinstaladoreal:up/down/restauración/privado0Dirty/dependientesDirty/generation/Match/rights/refreshlocks/filtros/paginación/guardas. Sin cambiosdefiltros/SLO/CPU/memoria/volumen. SiN2falla,conservarcorregirantesclean. SiN2pasa,cleancortoactualmismoentorno,sóloPASSrepiteunavezymáslargoatadoprerequisitos. CR09/N3/contratoenterosabiertos.

PG17.11/Python3.12.15/nativehostca3c/4CPUcontrolador/PG1/memorialímiteshabituales. Fuentecongeladaigual;runner/hijo/temp/contenedoresausentes;unidadinactive/MainPID0/ControlGroupvacío. Artefactosprivate-draft-roi.json/JUnit/source-hashesdelrun. Sinproducción/datosreales/proveedores/Claude,consumopreviointacto. Últimop95clean1,013029795FAIL,nuevo p95no medido.
