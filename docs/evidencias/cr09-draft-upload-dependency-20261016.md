# CR09: invalidación conservadora de subida a borrador

Run040358-0c5d659d,HEADeb0e8c9 más testcongelado,1PASS89,01s. PG17.11propio/Python3.12.15/nativehostca3c,10k anunciossintéticos,controlador4CPU/PG1CPU ylímites habituales. SubidarealDjangoClientseed782134ymismo processBlob real,sinCelery/Beat,despachoregistrado. Dirtyborradoenfixtureentrefasesparaatribuircadauna;nooperaciónproductiva.

| Fase | Dirtylistings | Visibilidadnativacambia | Match | markcalls | marktimePGms |
|---|---:|---|---:|---:|---:|
|ingest|1(sóloowner)|No|0|6|1,833|
|process|1(sóloowner)|No|0|6|2,617|

Ingest:triggerRevision1/1,062ms,Photo1/0,693,Blob2/2,558. Process:Photo1/1,135ms,Blob2/16,460. Tiemposfuncionesanidadosincluyenmark,nosumar. PGtrack_functionsall sólo sesiónpropia,forceflush/clearsnapshotantesdespués. Nativeeligible_ignoring_expiry sobrePublicationContextfreshdelownerTrueantesydespués. Una solapersona/noMatchesno demuestra que todoslosborradoresseanindependientes. processactualizaPhoto.comparison_completeademásdeBlob,porloquesólofiltrarPhotoINSERT no resolveríaelcaso.

Resultado demuestra invalidaciónconservadoraenfixturedeaceptación,nocosteindirectoHTTPni causalidadp95. LecturasinicialesconDirtydebenrecalcularunknown ypuedenperdercaminorápido,peroimpactoexactodelaexcepción no medido. Noquitartriggers/tabledependenciessólo por esto. Match0020correctiva permaneceobligatoria.

## Diseño de contraste pendiente

Delimitarreduccióndeinvalidaciónsóloescriturasprivadasconservadoramenteindependientes:revisiónnoaprobada/statusdraft,actualizacionesmetadataedit_version/updated_at sinotroscambios;Photo/Blobpertenecensóloaborradoresnopublicados. Si hayMatchrelevante/refsreintro/disposición/rectificación/relacionesdesconocidas,conservarinvalidaciónoriginal. Blobcompartidoconfotoaprobada debeinvalidarpublicado. Revisionstatus/listing/created_at/cambioscamposrelevantes,Photoaprobada/comparison_complete/removed_at/rectificationrelation,DELETE/TRUNCATE ybulk debenconservarsemántica. ConsiderarOLD/NEW,FKdiferidasycarreras;no reducirporseñalesDjango que rawSQLomite.

Antes de migración/producto:prototipoPGpropioaislado,pruebasnegativasdeclausuradependencias/contrastevisibilidadyorden/cuentas,up/down/rollback/carrerarefreshgeneración,Matchindirectotodoscontroles,referenciasblobderechos. Si prueba no demuestraexcepciónseguraonoROI,descartar. SinretocarSLO/volumen/límites. Eventualcleansólodespuésdecorrectiva verificada,no repetirFAILni900s sinprerrequisitos.

Datos draft-dependency-parsed.json/JUnit/source-hashes en artifacts/local-ci/20261016-040358-0c5d659d. Fuentecongeladaigual;runner/hijo/temp/contenedoresausentesindependientes;unidadinactive/MainPID0/ControlGroupvacío. Sinproducción/datosreales/proveedores/Claude,consumopreviointacto. Nop95nuevo;últimoclean1,013029795FAIL. CR09/N3/contratoenterosabiertos.
