# CR09: prototipo de invalidación acotada para borradores independientes

Sólo funcionesPGpropias instaladas/restauradasdentrodetests,NO migración ni app modificada. Basea8571b2+fuentesdiagnósticascongeladas. Primer041048-d8f5922f:**8PASS140,05s**. Controlesadicionales041511-8c2c87d2:**2PASS51,68s**. No sumar comoN3:10variantespertinentesdedistintasfuentesdeinstrumento,primerascuerposAST8intactosverificados;SQLcandidatoinmutable,añadidosguardexplicit/DDLrestorationasserts despuésprimeraejecución.

| Resultado fixture10k seed782134 | Antes | Prototipo |
|---|---:|---:|
| Dirtytrasingest |1|0|
| Dirtytrasprocess |1|0|
| Visibilidadnativa |True|True|
| Match |0|0|

Primeraejecuciónverifica5conservadores(approvedPhoto.comparison_complete/sharedBlob/statusRevision/titleDraft/deleteDraft)ytodos2sentidosMatchindirecto. Segunda:si hayrefsrectificacióninvalidaciónsiguesiendo conservadora;bulkmezcladoprivado/aprobadoinvalidaexactamentepeerpúblico;rollbackreviertecampoyDirty;pg_get_functiondefrestauradoexactamente/funciónhelpereliminada. RefledgeresfixtureFKsintética,noaprobaciónhumana.

Excepción:RevisionstatusdraftnoapuntadaporListing.approved_revision,yowner sinMatch/reintro/upload/disposición/rectificación. RevisionUPDATEquecambiasóloedit_version/updated_at;otrascolumnas/INSERT/DELETEconservadores. PhotoINSERT/UPDATEfiltranrevisionesprivadas,DELETEconservador. Blobrecorrephotosyconservatodoslosownersconrefsreintro/disposición. Mark0020no se toca. Triggers/tabledependencies/TRUNCATEpermanecen. ConsultasOLDNEW/vistasAFTERstatementVOLATILE,según https://www.postgresql.org/docs/17/trigger-datachanges.html y https://www.postgresql.org/docs/17/sql-createtrigger.html . Helpernoescachédeautorización.

Costeescrituramásalto:ingestRevision22,904ms/Photo9,228/Blob9,282,processPhoto8,774/Blob66,656,tiemposPGinstrumentadosanidados,no sumarmark. No ROItotaldemostradoaún. Próximo contrasteAB/BAconmismaseed/estadoysources,realesingest+processmáslecturas,sinperfilador;incluircosteescritura,conteoDirty yparidadexacta,antesdeintegración. EstosdatosnoaceptanSLOni justificannuevacargaHTTPcontractual.

Pendientescorrectitudantesdeproducto:casosDerechosblobindirectos/creaciónconFKdiferidas/moves/DELETE/TRUNCATE/bulkRevision/noop/erroresdespuésDDL,carrerarefresh+escritura,integraciónmigraciónup/downycontrolespublication/rightspertinentes. Conservarfallbackdesconocidos,sinrecortardatos/formularios/24guard/48unknown. Si ROI nulo/falladependencia,noseintegra.

PG17.11/Python3.12.15/nativeca3c,4CPUcontrolador/PG1CPU/memoriahabitual/swap0/serial. Ambasfuentescongeladasiguales/runner/hijo/temp/contenedoresausentes;unidadesinactive/MainPID0/ControlGroupvacío. Artefactosambosrunsenartifacts/local-ci,primerafuentescopiadas/hashoriginalconservado. Sinproducción/datosreales/proveedores/Claude,consumopreviointacto. Últimop95clean1,013029795FAIL,CR09/N3/contratoenterosabiertos.
