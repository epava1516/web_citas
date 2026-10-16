# Ciclos del cliente de pruebas y GC de workers reales

Análisis sinloadnuevo al corte1bae315. Artefactos de atribuciónAA064636 ycapturaHTTP031208, másprobe puro sinDB/red en artifacts/cr09-client-lifetime-20261016.

## Descomposición del AA instrumentado

977coleccionesgen0 suman184,037ms,89gen1 suman171,031ms y8gen2 suman1424,115ms, máximo206,609ms. Generación2concentraaprox80,05%wallGCobservado. Es procesoPython deDjangoClient confixture10k, no workerGunicorn.

FuenteDjango5.2.17 instalada django/test/client.py:265 copia contextos porseñaldetemplate;1095–1097 asigna context/templates y response.json=partial(self._parse_json,response). Esto introduce ciclo response→partial→response. No implica fuga permanente: collector lo recoge normalmente.

Probecontrolado HttpResponsebytes sintéticos conhandlerClientdummy/RequestFactory sinvistas/DB/red: respuestaoriginal sindecoración se libera porrefcount; respuestaClient retiene trasdel yse libera trasgc.collect. Referenciapartial.args[0]isresponse comprobada, sólo weakrefparaobservar. GC se desactiva temporalmente únicamente enesteprocesoacotado yse restaura finalmente; no ajusteapp/runtime/benchmark.138objetos recogidos enprobenoseatribuyen todosalresponse. JSON/hashfuenteenartefacto. PrimerainvocaciónfallóModuleNotFoundErrorconfig porPYTHONPATHdel script; repetidoconPYTHONPATH=. sincambios alprobe, ningúnresultadoapp/performance deprimerintento.

[StackOverflow14392537](https://stackoverflow.com/questions/14392537/django-unit-test-client-response-has-empty-context) y[27136048](https://stackoverflow.com/questions/27136048/django-unit-test-response-context-is-none/36703491) ayudan a localizarcaptura decontextostest, contrastada con fuenteinstalada. [66720626](https://stackoverflow.com/questions/66720626/how-do-you-fix-a-memory-leak-within-django-tests) describeWebTest, **noel mismo cliente**; no usar como prueba denuestracausa. Nohaysolucióncomunitariacopiada.

## Evidencia independiente del workerHTTP

Captura031208/1200dynamicWSGI completadas,57eventosgen2retenidos entrelargest_events (máximo16porrequest), máximo201,639ms. SumaGCrequest9,195345s;no costeextraaditivo niCPUPG. Las120requestsconWSGIwallmásalto tienenmedia353,638ms yGC41,138ms. Gruposposthoc/mezclarutas, no causalidad ni reconstruccióndeSLO. GC workerreal existe sinDjangoClient dentrodeworker; nosepuededescartartodocomoharness. Tampoco los8gen2AAacreditan mismosobjetos/lifetimeenGunicorn.

Siguiente localizar ciclos/objetos retenidos **en el camino real WSGI**, coninventarioacotado de tipos yreferencias sintéticas, sinvalorespersonales. UsarprobetestClientcomo advertenciametodológica,no modificarDjangointerno nirespuestapúblicaparareducirunartefactotest. No gc.freeze/globalGCpolicy niotrocleanhastaevidenciamaterial. Últimop95sinperfiladores1,013029795FAIL;CR09/N3/goalenterosabiertos.
