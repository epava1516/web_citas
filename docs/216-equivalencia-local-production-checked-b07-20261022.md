# B07 — equivalencia local de PRODUCTION y checked

B07-242: implementado control local100 normal/PRODUCTION con filtros checked combinados ymetadatos sintéticos explícitos;equivalencia PostgreSQL pendiente. Sin proveedor real,capacidad ni cierre;8de18,B07 abierto.

## Alcance yprerregistro242

Contrato16§16exige matriz normal/PRODUCTION/checked. Las pruebas históricas test_publication_state.py comparan modo producción pequeño ytest_discovery.py comprueba metadatos específicos; no sustituyen crecimiento ni población positiva representativa. Después de239/240/241 se añade tests/test_production_checked_combined_equivalence.py, sin modificar producto ni guardas. Dos casos normal/production con100publicaciones sintéticas en municipios70/30,perfil mujer eidioma habladoen,textophotography yESEN. Sin promociones: PROMOTION_TEST_MODEFalse;no usar fixturepromocional rechazandoPRODUCTION ni quitarasserts.

Preparar población mediante populate mientras PRODUCTIONFalse ybase propia test_promotion_gate_;conservar suguarda. Sólo después activar rama políticaPRODUCTION para el caso correspondiente. Los100expedientes conservan pruebas sintéticas de fixture;los campos provider/procedure se preparan explícitamente con etiqueta synthetic-policy-fixture.invalid,age-v1 en80yprocedimiento vacío en20,contactosms-v1 yagenciaorganization-v1. No se invoca ni acredita proveedor externo,identidad real,pago oapertura. Probar la rama de política con metadatos sintéticos no equivale a arrancar configuración segura de producción ni capacidad de esa instalación.

Oráculo reference_territorial_order(promotions=False) aplica autoridad nativa públicamente visible yordenSQLtextual;predicado independiente any(real_checks(...)) parachecked,con semánticaOR. No toma selección esperada deHTTP,state_page,proyección nimatchesdelacapa de estado. Grupos sinchecked,age,contact,age+contact combinados conciudad+tipo+idioma+texto. Recuentos explícitos normales70/30exceptoage56/24;producción56/24paratodos. Tresfases fresh/pending/repaired. Invalidar manager_versiondelaprueba deunperfil mayoritario inicialmente elegible situado fueradelaprimerapágina de lacohorte;age55/24pendiente,reparado;enproducción55/24todaslasvariantes. Contacto conserva70/30normal. Una marca/generación debe permanecer trasGET;reparación manual explícita. Cada página enambosidiomas conciliaIDsordenados,recuento,unicidad yrecorrido completo,incluida tercera.

Ejecución autorizada siguiente: runnerfocusedserial PostgreSQL17/Redis7.4 propios,native-source existente,fixture-snapshots,isolate-test-broker,testarchivo completo,doscasos,timeout1200s. Ruff antesdecongelar;grafo259AST+semántico+sellado+documentación. Estimación variosminutos basada en239,sinpromesa lineal: shellpersistente,Telegraminicio/previo/terminal,pausa/compactación/reactivación mismo objetivo si espera larga. Congelar fuentes/protocolo216/grafoantesdeejecutar;auditarmismo conjunto,628producto,JUnitpropiedades,limpiezareal yrecibosantesdeeditar. ConservarFAIL/ERROR,ningúnreintento porbuscarverde.

No medimosSQL/render/CPU aquí,noHTTP TCP,worker,cuotas8CPU8GiB,concurrencia,capacidad1000/10000 ni integración real deproveedor. No900automático. Este control cubreparidad local de política;la aceptaciónB07completa yB08–B11mantienen suscriterios.


## Resultado negativo242b y corrección243

B07-243: negativo242b auditado: dos FAIL porque save activa reparación Celery eager del fixture antes de observar la marca. Corrección sólo del ensayo: actualización SQL conserva disparadores PostgreSQL sin emitir señal de modelo. Revalidación de los dos casos pendiente; no paridad aceptada, capacidad ni cierre; 8 de 18, B07 abierto.

Ejecución `20261022-131419-031dc7c3`: 2 FAIL, 0 ERROR/skip JUnit, 81,652 s. Fuentes1698/protocolo216 intactos y628fuentes producto iguales aB13; contenedores, temporal yprocesos del runner ausentes. Recibos de fase, terminal y reactivación enviados; compactación REQUEST_ACKNOWLEDGED. Auditoría preservada en `artifacts/beta-promotion-fix-20261020/policy242b-negative-audit.json`. El log registra refresh_publication_state inmediato tras save yel fixture photo_environment configura CELERY_TASK_ALWAYS_EAGER=True; publication_signals programa refresh por on_commit. No se cambia producto ni se atribuye este fallo al lector.

Prerregistro243: repetir únicamente el archivo completo de dos casos con los mismos100perfiles70/30, políticas, filtros, fases y aserciones, runnerfocusedserial/PG17/Redis7.4/snapshots/broker aislado/timeout1200; cambiar sólo la escritura pendiente a QuerySet.update. Conservará la marca por disparador SQL hasta reparación manual. Congelar corte y auditar antes de editar; no repetir sin causa ni aceptar por el resultado del auditor negativo.


## Resultado auditado243

B07-243 auditado: 1 PASS y 1 FAIL en 116,554 s; producción verifica 96 páginas, normal falla en el recuento nativo 69 frente a 70. Fuentes1698 y producto628 intactos, limpieza y Telegram confirmados; compactación y reactivación del mismo objetivo verificadas. B07 abierto; ocho de18 puntos cerrados.

Ejecución `20261022-132257-f359d7e1`; auditoría `artifacts/beta-promotion-fix-20261020/policy243-negative-audit.json`. Un PASS no acepta el archivo completo. El caso production recorre fresh/pending/repaired, ES/EN, cuatro variantes checked y hasta tercera página; una marca pendiente permanece tras GET, reparación manual. El caso normal termina antes de emitir su propiedad completa. No equivalencia normal completa, capacidad ni proveedor real.

Causa del recuento incorrecto del ensayo: `reference_territorial_order` llama a `publicly_visible`, que llama a `validate_submission`; `apps/listings/submissions.py:97–110` exige que la última prueba tenga estado passed, sujeto y manager_version actuales también fuera de PRODUCTION. La mutación de manager_version invalida por tanto la publicación completa en ambos modos: después de fresh quedan69 perfiles mayoritarios normales para sinchecked/contact/age+contact, y55 para age; producción55 para todas las variantes. El ensayo sobrescribe incorrectamente el decremento normal con70. Esto se deduce de la autoridad nativa y concuerda con69 observado; aún falta revalidación HTTP normal de las fases pendientes y reparadas. Siguiente corrección propuesta: conservar70/30 para fresh normal noage y restar1 después en mayoría para pending/repaired; mantener56/24 age/production y el decremento a55. No alterar producto, filtros, oráculo ni guardas para acomodar el fallo.


## Corrección y prerregistro244

B07-244: corregida sólo la expectativa del ensayo: invalidar manager_version excluye un perfil mayoritario en ambos modos y todos los filtros; normal69 o55 para age tras fresh, producción55. Revalidación de dos casos100 pendiente; sin cambios de producto, capacidad ni cierre.

Mismo archivo completo, población100 70/30, dos casos, fases, ES/EN, checked, IDs/orden/recuentos y marcas; runner focused serial PostgreSQL17/Redis7.4, snapshots, broker aislado, timeout1200. No otros cambios; congelar fuentes y protocolo, auditar resultado y limpieza antes de editar. Shell persistente con Telegram terminal, compactación y reactivación del mismo objetivo durante pausa autorizada.


## Resultado auditado244

B07-244 auditado: dos PASS en 139,130 s; normal114 y producción96 páginas, total210. Fuentes1698 y producto628 intactos, limpieza y Telegram confirmados; compactación y reactivación del mismo objetivo verificadas. B07 abierto; ocho de18 puntos cerrados.

Ejecución `20261022-133206-c545cb5f`; prueba y auditoría `artifacts/beta-promotion-fix-20261020/policy244-audit.json`. PostgreSQL17 y Redis7.4 reales locales; 100 perfiles sintéticos70/30, fresh/pending/repaired, ES/EN y cuatro variantes checked. IDs, orden, recuentos y unicidad contrastados con autoridad nativa; GET conserva la marca pendiente, reparación manual. El manager_version obsoleto excluye el perfil en ambos modos. Sin proveedor real, worker, TCP, capacidad ni configuración segura de producción acreditados. Se preservan negativos242b/243 y el primer auditor244 fallido por su supuesto incorrecto de96 páginas normales; corregido a114 sin repetir CI. Próximo trabajo: derivar del contrato y matriz la siguiente combinación pendiente antes de prerregistrar otra ejecución.
