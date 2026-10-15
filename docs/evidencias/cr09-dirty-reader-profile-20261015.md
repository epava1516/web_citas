# Perfil dirigido del lector actual con una publicación dirty

Run221105-624e1d8e, experimento aisladoc48002c, referencia _state_page85a5abe; **1PASS91.11s**. [Recibo y funciones](cr09-dirty-reader-profile-terminal-20261015.json). Ninguna modificación de producto integrada. PostgreSQL/Redis propios, Python3.12.15,10k sintéticos,1dirty,6lecturas (listado/búsqueda coincidente/sin resultados,2cadauna). Límites existentes intactos. Fuente congelada exacta, root/child/temporal/contenedores propios retirados, MainPID0/ControlGroupvacío verificados antes de editar.

cProfile con timer thread_time exclusivamente alrededor de candidates+state_page, no fixture. Conexión nueva porlectura. WrapperSQL registra wall/CPUthread sin SQL/params. Sin concurrenciaHTTP/worker consumidor. cProfile introduce overhead no cuantificado: **no son tiempos limpios, ni p95, ni capacidad**; distribución instrumental para localizar trabajo. Los costes inclusivos se solapan, no sumarlos.

|CPUthread acumulada instrumentada,6lecturas|Segundos|Relación|
|---|---:|---|
|state_page completo|3.5870|Referencia inclusiva|
|PublicationContext.__init__,10llamadas|2.6349|Dentro de state_page|
|publication_query,10llamadas|0.9914|Dentro del constructor|
|Compilador ORM as_sql,372llamadas|0.8503|Incluido en construcción/ejecución de varias consultas|
|publicly_visible,100llamadas|0.6624|Validación nativa, fuera del constructor|
|SQLcliente CPU,232consultas|0.1352|Contadorwrapper, inclusivo en ejecución|
|SQLwall,232consultas|1.2443|Otro reloj: no sumar a CPU|

Se identifica trabajo Python material en construcción de anotaciones/expresiones, compilación ORM y preparación/hidratación del contexto, además de validación nativa. **No todo el coste del lector dirty está en COUNT/selección de población**, lo que concuerda con el beneficio pequeño/irregular de la proyección híbrida. Esto no cuantifica qué produce toda la espera del arranque bajo carga ni prueba una única causa.

Lectura directa: PublicationContext construye publication_query (anotaciones vigentes de autoridad/histórico/verificación), prefetch de relaciones y catálogo actual; hay contexto para desconocidos y otro para la guardia de página. No eliminar esas verificaciones. La siguiente investigación debe separar construcción de la estructura de consulta de lectura de valores y validación, y buscar reutilización acotada sin compartir resultados/personas/decisiones entre requests. Sólo conservar una candidata si demuestra ahorro de lector completo y semántica exacta. No asumir que caché de planes PostgreSQL evita recompilar consultas en Django.

El prototipo limpia+dirty queda preservado pero no integrado, por retorno insuficiente. [Paridad y coste comparados](cr09-dirty-parity-20261015.md). Último limpio del producto f9f404d siguep951.118772sFAIL; CR09/N3 abiertos. No lanzar carga limpia hasta tener candidata respaldada por equivalencia y coste.
