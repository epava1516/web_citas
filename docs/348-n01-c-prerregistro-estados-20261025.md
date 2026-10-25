# N01C — Contraste de estados desconocidos y preparados

25 de octubre de2026. Prerregistro anterior a ejecución. [N01B347](347-n01-b-resultado-segmentos-20261025.md) y su contexto se han conciliado semánticamente antes de analizar este hito. N00aceptado1/13; N01/N04siguen abiertos,alfa. El nuevo código es sólo el instrumento, sin editar aplicación ni el instrumento N01B.

## Hipótesis y preparación nativa

N01B observó36peticiones fallback/state_unknown_over_limit. Hay que separar la lectura con estados no mantenidos de la lectura tras preparación operativa. No se declara defecto por aquel resultado. Este lote repite el mismo helper N01B sobre la misma población en dos fases, con comprobación explícita de rutas y paridad.

Un caso tests/test_discovery_state_baseline.py::test_native_discovery_unknown_and_prepared_states. Primero invoca directamente el instrumento B intacto, capturando sus propiedades:100publicados,ES/EN,listado/página2/perfil/vacío/ficha,6muestras/segmento=60peticiones. Es una referencia pareada en la misma base; el nuevo propósito justifica repetirla aquí, no una repetición rutinaria de la batería B.

Entre fases se ejecuta el comando real refresh_publication_state --all por call_command, en la base de pruebas propiedad del runner. El comando marca/recalcula con reglas nativas y actualiza estadísticas PostgreSQL mediante VACUUM/ANALYZE. Su tiempo se registra aparte. No se escriben estados derivados a mano ni se sustituye state_page, sus guards o límites. No acredita consumo real de worker/Beat, throughput, SLA o cadencia asíncrona.

Después se invoca de nuevo el mismo helper B. Su populate(100) encuentra la población ya creada y no añade perfiles; se conservan oráculos y parámetros. Se comprueba cobertura de estados bajo rules_version actual y ausencia de pendientes antes y después de esta fase. El orden es desconocido→preparado, ES→EN y segmentos fijos; cachés y estadísticas también pueden cambiar. El contraste corresponde a preparación operativa completa, no a efecto puro de estado o mejora de código.

## Oráculos y métricas anteriores al resultado

El helper B conserva sus gates200/no-store/idioma/email privado centinela/IDs/orden/conteo en120peticiones totales. Diez segmentos porfase y seis muestras cadauno. Comparación de hash de IDs/orden y tamaño entre fases para todas las muestras. La preparación no puede cambiar los campos de negocio de ninguna Listing: ID, revisión aprobada, estado,published_at yexpires_at se comparan exactamente.

En la fase inicial,listado/página2/perfil deben observar fallback/state_unknown_over_limit. Tras la preparación, todos los segmentos de búsqueda/listado deben observar state; la ficha conserva su guard propio sin ese marcador. Las dos fases deben completar todas las muestras sin FAIL/ERROR/SKIP; preparación con estados actuales y cero PublicationDirty. Cualquier incumplimiento se conserva para atribuirlo a instrumento/fixture/aplicación con evidencia.

Wall y SQL execute/count por petición, primera y mediana/mínimo/máximo de cinco posteriores porsegmento. Tiempo total de mantenimiento porseparado. Sin nuevos techos de tiempo inventados:es referencia diagnóstica antes de candidatos, no prueba de800ms, p95,20RPS,TCP o capacidad. No calcular porcentaje de mejora de código entre condiciones operativas distintas. Las tablas antes/después porbloque mantienen esa distinción y los límites de comparabilidad.

## Entorno, versión y ejecución

PostgreSQL17/Redis7.4 locales desechables,un worker,datos sintéticos y fotografías compartidas con los límites de populate. Nativo librdb2.4.0 fijado,imágenes y SHA encongelación. Mismo runner oficial queB;no afirmar aislamiento/cuotas8CPU8GiB de la carga contractual. Mantener1507fuentes previas y el instrumento B porbytes; añadir únicamente el instrumento C.

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test tests/test_discovery_state_baseline.py --workers 1 --timeout 900
```

Antes de lanzar:ASTdelinstrumento y semántica del protocolo actualizados,lint/documentación,fuentes/imagen/oráculos congelados y avisoTelegram. No editar fuentes durante la prueba. Timeout900porpaso noesSLA niETA;previsiónacotada,nohoras. Si surgeesperalarga,seguirAGENTS de persistencia/pausa/compactación/retorno delmismogoal.

Auditar JUnit/journal1caso,120muestras,rutas/paridad,fuentes,limpieza y Telegram antes deinterpretar. Se mantienenpendientes promociones,grandes tamaños/profundidad,concurrencia,browser/workerreal,estadosnegativos yotros8grupos. No aceptarN01/N04 por este lote.
