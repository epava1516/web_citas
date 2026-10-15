# Segunda opinión de Claude: rendimiento CR09

Consulta explícita del usuario sobre base `f531aef`. Una invocación V1 oficial, sin herramientas ni escritura, 213.881s; no ultrareview. [Propuesta íntegra y procedencia](cr09-claude-rendimiento-propuesta-20261015.json). El CLI terminó con0 pero el adaptador rechazó el informe con66: declaró complete manteniendo cuestiones sin resolver. Se conserva como propuesta no aceptada; no se reintenta ni modifica el contrato.

## Aporte útil por contrastar

Claude prioriza determinar la demanda actual de CPU de aplicación/PostgreSQL y el trabajo de cada familia SQL antes de más microcambios Python. Sugiere estadísticas de consultas de la instancia sintética propia y CPU/presión de sus cgroups; después derivar una configuración sync de la demanda medida, sin barrido. Si PostgreSQL es el límite, priorizar búsqueda/conteo/página antes de añadir concurrencia. Una proyección transaccional o más presupuesto son alternativas estructurales, no conclusiones ya demostradas.

La p95 contractual sigue siendo obligatoria: las métricas de demanda complementan la decisión, no sustituyen su aceptación. No se adopta el plan de tres repeticiones de600 solicitudes, cinco minutos de fondo y nueva carga instrumentada como cadena automática. Antes debe acotarse qué desconocido concreto resuelve cada ejecución, con recursos propios y una sola prueba activa.

## Correcciones independientes de Codex

- `config/settings.py` ya fija `CONN_MAX_AGE=60` y `CONN_HEALTH_CHECKS=True`. Proponer activarlas no aporta un cambio actual. Se desconoce todavía la reutilización efectiva; requiere observación si aparece como hipótesis prioritaria.
- La creación de `TConn` de Gunicorn mide el socket HTTP aceptado. No demuestra creación de conexión PostgreSQL ni coste de fork/autenticación del backend. Esa inferencia de la respuesta es inválida.
- 885 completadas durante60s equivalen a14.75rps observados en esa ventana; no prueban régimen estacionario ni servicio medio0.27s. Los datos de ocupación/CPU utilizados pertenecen a otros runs/versiones. Las aproximaciones M/G/c y los umbrales de utilización0.7/35ms son heurísticos, no requisitos ni causas demostradas.
- `pg_stat_statements` ofrece duración de planificación/ejecución; no CPU por sentencia. La CPU del cgroup incluye fondo, mantenimiento y posibles interacciones. Restar una ventana de fondo no garantiza atribución causal exacta.
- La propuesta conserva el riesgo ya conocido de añadir workers con PostgreSQL cerca de su CPU asignada. No justifica reactivar ocho sync ni gthread, cambiar cuotas, almacenamiento/compresión o dependencias sin diagnóstico concreto y controles propios.

## Siguiente decisión

Preparar un diagnóstico finito de las familias SQL en PostgreSQL propio sobre el código actual, verificando primero disponibilidad y alcance de las estadísticas. Separar planificación, ejecución, llamadas, lecturas y CPU agregada; no atribuir esos intervalos a CPU por consulta. Mantener la candidata de membresía provisional y su FAIL19.666s conservado. No se aplica cambio de producto desde este informe; CR09/N3 permanecen abiertos.
