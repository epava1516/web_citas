# N03F — conciliación de acciones y criterios (en curso)

25/10/2026. Alfa,N03abierto,3/13bloques obligatorios aceptados. Corte previoE0b9944eb480b395a5965d7627bc3e413f6ba55fa8ad783bddd75d34fa277a06d/1993fuentes revalidado antes del análisis. Consulta graphify seguida de contrato340,roadmap341,criterios354,base355,censo338/JSON ytestigos379/381/383/385/387. Grafo es guía selectiva,no evidencia de aceptación por centralidad.

I13/I14 contienen rutaR_photo_upload y tareaT_process_blob,con dispatches/guardias compartidos identificados por el censo. No importar automáticamente todaI15(gestión privada/orden/retirada) oI16(revisión/publicación) enN03: conservan dueñoN07. Recuperación/limpieza/retención ycomunicaciones mantienen propietariosN07/N09/N10,N06segúnacción, sin borrarlas del contrato global. Matriz de trabajo en JSON; clasificación de fuente no equivale a PASS individual.

| Criterio | Evidencia actual | Disposición |
| --- | --- | --- |
| Recepción→cola→process→ready | 379realPOST/worker y387broker/Beat,reintentos/errores | Verificado dentro de escenarios;conciliar identidad actual de ingest/autoridad ytabla final |
| Distintos/densidad/detector-confirmación-registro | 327verificado y381paridad completa/ORB200→101/14,954→12,729s | Verificado finito1000/100;no80k/índice/cap ni mejora universal |
| Recuperación yseguridadgeneración/retención | 383fences33PASS,385progreso37PASS,387transporte1PASS | Casos verificados;no sustituye límite global heredado |
| Variación de retención histórica | Estadoshistórico/mixto385,retenciónfuncional11casos | Falta crecimiento ortogonal con cohorte actual fija: N03F2 |
| Concurrencia | Dos conexionesPG/barreras ypurga/nuevo referente;prefork2real | Testigos acotados reutilizables;no throughputHTTPsimultáneo |
| Máximo cuatro generaciones automáticas | CR05L18heredado,consumer sin cap,selectorfailed<4 | Contradicción de fuente pendiente de reproducir/corregir: N03F1 |
| Coste/tabla/negativos/autoridad | 379/381/383/385/387 yfuentes actuales | Tabla consolidada/puente poracción pendiente de cierre |
| Apertura/capacidad/proveedores | Fuera/condicionados por340 | No80k,proveedorreal,datos reales o beta por estas pruebas |

## Límite que no se puede reinterpretar

CR05 dice «hasta cuatro intentos de generación automática»;340preserva garantías sin sustitución expresa. 338describe máximo3retries deunmensaje yselectorfailed<4,pero no revoca aquella garantía. 387sóloacredita4ejecuciones deunmensaje. process incrementa attempts bajo lock sin cap;queued/stale conattempts4 yready sinfirma pueden avanzar a5. No se declara fallo runtime antes de reproducirlo ni se transforma la garantía en opcional/per-messagepor comodidad. La aceptación de tiempos enalfa no dispensa este control funcional.

N03F1(389) reproducirá8combinaciones deestado/contador más3controles positivos;si confirma,guardia de generación bajo lock sin cancelar cuarto leasefresco ni impedir comparaciónready válida. Mantener original/derivado/evidencias ycontadores heredados>4 visibles,sinclamp. El selector podrá liquidar unqueued/stale agotado como failed sin generar otraimagen;no dejarlo colgado por filtrar sin resolver estado. Nueva prueba real de otro mensaje tras4agotados acreditará la rama enworker.

N03F2mediráretención0/10/100dehistoricalPhoto conbytesyaexistentes ycohorteactualfija,clasificaciónhistórica nativa,Matchsetexacto yrecovery/detectorSQL/relojes. Tamañosdiagnósticos justificados,no nuevo gate numérico ni promesa80k. Sin nueva búsqueda marginal de optimización.

Revisión nativa sólolectura n06e_coverage_review reportada;Codex contrasta fuentes/JUnit yretiene autoridad de aceptación. DosFAILoriginales383 ycuatroFAIL385 siguen diferenciados;E1PASSes transporte,no cierre delbloque. Tokensdesconocidos/noV1nuevo. No publicación/proveedores/datos reales. Falta evidencia obligatoria,por tantoN03permaneceabierto.

## Resultado posterior N03F1

390conserva8FAIL/3PASSreferencia y49PASScandidata:consumer impide generar más allá de4,bajoBloblock,sin cancelarleasefresco ni comparaciónready. Mensaje real adicional confirmafailed4sinretry/nueva generación. La discrepancia está corregida en su alcance;no reinterpretada. N03F2retención sigue sin medida yacta/tablafinalporacción siguen pendientes.
