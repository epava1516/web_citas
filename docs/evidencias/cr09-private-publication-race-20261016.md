# CR09: carrera reproducida en prototipo de borradores privados

Primer042732-9dc1b45b:2FAIL52,96s,FieldErrorinstrumentoDirtylistingUUIDconsultadocomolistingFK,fuenteycleanupverificados,originalconservado. Corregidocampoexacto,sinrelajarcriterio. Segundo042942-2efd668e,HEAD295e2a6+testcongelado:**1PASSactual/1FAILprototipo53,09s**.

| Resultado después de amboscommits/refresco | Actual | Prototipo |
|---|---|---|
| Nativo visible |True|True|
| Estado almacenado elegible |True|False|
| Dirty pendiente |False|False|

AactualizaBlobqueued→ready dentroTxabierta,suPhotoesDraftprivadaeneseinstante. BdirectDBapruebaRevision/apuntaListing/refresca. Actual:seobservapg_blocking_pidspublisheresperandowriter;liberamosA,Bconfirma/refreshcorrecto. Prototipo:permiteBpublicar/refrescarnegativoconBlobviejo;Aconfirma sinDirty,quedafalsonegativocaché. NoHTTPomisiónmedidaaquí;invarianteestadonativo/almacenadoya falla ypuedecausaromisión. ClonessintéticosvalidFKconcamposnativoscorrectos,noevidenciadeaprobaciónhumana/servicioModeración.

El markeractualtambiénejerceserializaciónentreescritores;quitarloporunaobservaciónprivadanoessuficiente. ROIsecuencialpositivo9–25%nolocompensa. **PrototipoactualNOintegrable**,producto/migración intactos. Preservarfallofuncional,no convertirlo enesperadoPASS.

Siguientediseño:separar serializacióndeescrituras de necesidadderecalcular,sinrelajarautoridadniestadofresh. Evaluarbloqueosdedominioordenados/ListingenmodocompatibleFK,coordinadosenmarkyexcepciones;refresherdirtylock/NOWAIT/OLDNEW/Matchneighborhood ydeadlocksraces requeridos. Antesdeproductorepetircarreraactual/versióncorregida ycontrolesafectados;revalidarROIcosteescritura. Noaceptaciónporhipótesis/lecturafuentes.

PG17.11/Python3.12.15/nativeca3c,4CPUcontrolador/PG1CPU/memorialímiteshabituales/serial. Fuentescongeladasiguales;runner/hijo/temp/contenedoresausentes;unidadfailed/MainPID0/ControlGroupvacío. Sourcesexactos/pytest.xml/reportsporcasoen artifacts/local-ci/20261016-042942-2efd668e. Sinproducción/datosreales/proveedores/Claude,consumopreviointacto. Últimop95clean1,013029795FAIL,ningúnp95nuevo/CR09/N3/contratoaceptados.
