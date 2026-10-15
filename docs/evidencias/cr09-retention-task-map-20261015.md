# Conservación: mapa de tareas y hueco de caducidad comprobado

[Mapa estático](cr09-retention-task-static-map-20261015.json):18entradas declaradas deconservación/caducidad,18implementaciones existentes condecoradorshared_task. Cadenciaestática no prueba configuración efectiva, registrodelworker nidespachoBeat. El mapa incluye condiciones delAST;RECOVERY_MODEvacíaelschedule despuésdeestasdeclaraciones. Referencias porimports enpruebas son candidatos, noasercionesejecutadas nicobertura transitive completa.

| Tarea | Cadencia declarada | Implementación | Archivos candidatos de pruebas |
| --- | --- | --- | ---: |
| `apps.safety.tasks.purge_expired_access_field_decision` | 60.0 s | `apps/safety/tasks.py:230` | 1 |
| `apps.safety.tasks.reconcile_retention_reviews` | 60.0 s | `apps/safety/tasks.py:57` | 1 |
| `apps.mediafiles.tasks.cleanup_prepared_media` | 60.0 s | `apps/mediafiles/tasks.py:41` | 1 |
| `apps.mediafiles.tasks.erase_media_files` | 60.0 s | `apps/mediafiles/tasks.py:34` | 5 |
| `apps.safety.tasks.purge_expired_account_confirmation_delivery` | 60.0 s | `apps/safety/tasks.py:50` | 2 |
| `apps.safety.tasks.purge_expired_access_scope_inventory` | 60.0 s | `apps/safety/tasks.py:212` | 1 |
| `apps.safety.tasks.purge_expired_access_coverage` | 60.0 s | `apps/safety/tasks.py:194` | 1 |
| `apps.safety.tasks.purge_expired_access_response_drafts` | 60.0 s | `apps/safety/tasks.py:172` | 4 |
| `apps.safety.tasks.purge_expired_portability_response_drafts` | 60.0 s | `apps/safety/tasks.py:154` | 4 |
| `apps.safety.tasks.purge_expired_portability_coverage` | 60.0 s | `apps/safety/tasks.py:136` | 8 |
| `apps.safety.tasks.purge_expired_portability_selections` | 60.0 s | `apps/safety/tasks.py:118` | 7 |
| `apps.safety.tasks.purge_expired_portability_assessments` | 60.0 s | `apps/safety/tasks.py:100` | 5 |
| `apps.safety.tasks.purge_expired_copy_information` | 60.0 s | `apps/safety/tasks.py:82` | 5 |
| `apps.safety.tasks.purge_expired_copy_page_reviews` | 60.0 s | `apps/safety/tasks.py:64` | 10 |
| `apps.safety.tasks.purge_expired_exports` | 60.0 s | `apps/safety/tasks.py:31` | 7 |
| `apps.listings.tasks.expire_listings` | 60.0 s | `apps/listings/tasks.py:41` | 1 |
| `apps.safety.rights_object_delivery.purge_object_deliveries` | 10.0 s | `apps/safety/rights_object_delivery.py:313` | 1 |
| `apps.safety.rights_object_content.purge_orphan_export_objects` | 3600.0 s | `apps/safety/rights_object_content.py:185` | 165 |

La inspección inicial no encontró imports directos deexpire_listings;existían pruebasdeexpire_one. Se añadiótest_listing_expiry_dispatch.py yelmapafinalahoraenlaza18/18 tareasconalmenosunarchivo candidato. **Noequivale a18tareasejecutadas porworker.**

[Control PostgreSQL](cr09-expiry-dispatch-terminal-20261015.json):run235228-0735477e,SHApreviod77002e,**1PASS43,73s**. Testnuevoincluidoensource-hashesoriginales,despuéscommiteado3a6e1a6. Compruebabarridocompleto, sólo caducaelpublicadovencido,preservapublicadonovencidoypausadovencido, incrementaversióncorrecta,auditoría actorNone/revisiónaprobada/estadoanterioryposterior,yrepetición0sin nuevaauditoría. Noappmodificada.

Dependencias/Ruff/docs/Django/migraciones/nativos pasaron. Fuentescongeladasverificadasantesdecommit;controlador/hijo/temporal/contenedorespropiosausentes;unidadexit0/MainPID0/ControlGroupvacío. Datos exclusivamente sintéticos.

Falta correspondencia integral finalidad/excepción/recurso/política y evidencia aplicable de despacho programado. No ejecutar tareas contra serviciosnormales ni interpretar una prueba directa como brokerreal. Próximopasoacotado: verificaciónderegistro/configuración efectiva ytransportepropio delas tareasnecesarias, preservando cadencias ysinreejecutarbateríascerradas. Rendimiento yN3 siguen abiertos.
