# Captura fría con cierre de py-spy corregido

Run20261016-133015-e228758c: **1PASS132,70s**,72lecturas exactas200/no-store/cuerpos conformes. Py-spy0.4.2 termina0, supervisoraislado recogePIDexacto/start_ticks,waitstatus9(SIGKILL intencional después de terminar lecturas/cerrarDB/escribirsummary); ausencia PID/zombi comprobada. No declarar salida normal del hijo. Fuentes y limpieza verificadas independientemente. [Recibo](cr09-cold-mix-pyspy-duration-20261016.json), [control mínimo real del ciclo de vida](cr09-pyspy-duration-lifecycle-20261016.json). Fallo anterior conservado, sin actualización de herramienta/permisos globales.

Wall y CPU de aplicación **instrumentados**,ms. La primera petición real del proceso es listadoES; las demás son primeras visitas a su ruta dentro del mismo proceso ya usado. Comparación con11posteriores por ruta, no controles A/A ni efecto causal.

| Ruta | Primera wall | Media posteriores wall | Primera CPU app | Media posteriores CPU app |
|---|---:|---:|---:|---:|
| /es/ | 349.41 | 183.11 | 173.89 | 105.73 |
| /en/ | 187.99 | 215.42 | 101.70 | 120.82 |
| /es/?q=photography | 185.80 | 212.10 | 102.92 | 114.37 |
| /en/?q=synthetic | 203.10 | 234.30 | 116.48 | 119.18 |
| /es/listing/:id/ | 77.45 | 75.43 | 42.09 | 43.63 |
| /en/listing/:id/ | 102.94 | 56.05 | 30.29 | 32.07 |

MuestrasGIL: primera15,otrascinco33,posteriores668. Primera:11_state_page,7PublicationContext.__init__,3compilaciónSQL,2renderformularios; inclusivos/solapados/no sumables ni cuotas exactas deCPU. El perfil parcial anterior24muestrasprimera mostraba6formularios: no hay respaldo estable para declararlos causa dominante ni cambiarpreparaciónestática. Preparaciónestáticaproductiva está incluida; sin solicitudes niDBprevias en hijo. BuffersPG previamente usados, sin TCP/Gunicorn4/Beat/subida; no causa única de la cola. CPU dePostgreSQL ytiempo deespera delrequest no se derivan restando wall−CPUapp.

**Decisión:** instrumento reparado; no nuevo cambio especulativo ni otro corto/900. La propuesta de agrupar tres subconsultas deVerificationCheck ya fue [ensayada y rechazada](cr09-verification-payload-20261015.md), no reabrirla. El último p95 limpio sigue0,862172866sFAIL. Revisar ahora las otras filas locales pendientes del contrato con fuentes finitas, manteniendo rendimiento yN3 abiertos; esto no rebaja el umbral ni aceptaCR09. Próxima fila: conservación, finalidad/excepción/tarea/efecto; el despacho Beat17tareas por sí solo no prueba contenido de todas las purgas.
