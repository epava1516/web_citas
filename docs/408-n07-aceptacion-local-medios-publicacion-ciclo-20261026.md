# N07 — aceptación local de medios, publicación y ciclo de vida

26 de octubre de2026. Alfa. N07 queda aceptado localmente en los escenarios y límites declarados: **7/13 bloques obligatorios** (N00,N01,N03,N04,N05,N06,N07). MOD09/N02 restante conserva el diferimiento al final; N08 es el siguiente punto. No se abre beta ni producción.

## Alcance y pruebas de cumplimiento

Se concilian los39IDs del censo:17rutas,7tareas,1comando,1runbook,6entradas Beat,6dispatch y1conexión de señales. La [matriz final](evidencias/n07-disposiciones-finales-20261026.json) conserva cada ID, el registro histórico, las fuentes actuales directas y dependencias, ocho criterios y propietarios compartidos. Los39IDs no son39ejecuciones independientes ni39mejoras. La [auditoría independiente](evidencias/n07-aceptacion-verificacion-20261026.json) revalidó fuentes y resultados. La revisión nativa sólo propuso agrupaciones; Codex comprobó las fuentes, resultados originales y equivalencias.

| Grupo / IDs | Disposición y evidencia | Límites conservados |
| --- | --- | --- |
|G1 lifecycle and expiry /3|Lifecycle13 históricos/HTTP N01D; expiry real nativa60s/guardas durante retraso N07B. Cancelación2ESEN PASS54,192sQA con fuentes estables, reintento antiguo no cancela ventana nueva. Calendario no SLA.|N07; exposición comercial N08|
|G2 listing moderation /3|Cola/formulario ESEN por estado, aprobación exacta/rechazo concurrente/autoridad actuales C16 más originales conciliados; sin tiempo humano o crecimiento100.|N07; derechos N09|
|G3 listing appeals /3|Cola antes/open/terminal y formulario ESEN; submit idempotente/revisión independiente, sin publicación automática.|N07; derechos N09|
|G4 match review and photo appeals /6|Pares recíprocos/distinct_people/conflicto/permiso/imágenes/apelación/restricción privadas: C16 y originales conciliados. FileResponse sólo handler; N05 conserva cuerpo.|N03/N07; derechos N09; transporte N05/N10|
|G5 owned media routes and producer /6|Reorder/remove2FAIL500 originales y4PASS correctivo404/autoridad/browser; otras funciones AST idénticas. Upload/productor N03 y privados/sondeos/browser N05. Dos IDs dispatch son mismo productor/lambda, no dos muestras.|N07 gestión; N03 productor; N05 navegador|
|G6 processing and recovery consumers /4|N03 aceptado: global4generaciones,3retries sóloOSError, leases/ready/retención, prefork2restringido/Beat60;49PASS y F2retención3PASS separados. No repetir por pertenecer a N07.|N03/N07; retención/purga N09|
|G7 stored-publication state, signals and operator command /8|N07B7SUCCESSreales/rolrestringido/Beat30refresh60expiry/18GETESEN/102filasnativasporfase. Bulk/rawSQL/postcommit/rollback/locks/M2Mreal con puentehistórico limitado. Sweepmanual no prueba3600s.|N07; N11 integración|
|G8 retention and deletion /4|Cinco erasure históricos fuentesconciliadas/once preparation_cleanup actuales F1/lectura privada N05. Wrappers semánticamente intactos; negativos retenidos/referentes y concurrencia acotada. Backlog/purga física operativa general N09/N10; sin proveedor/SLA.|N07 consumer/wrapper; N09/N10 retención/purga/operación|
|G9 shared operational and account boundary /2|Retirada urgente2originales PASS/fuente exacta más guardas N07B; runbook no endpoint/tiempo. Callback cuenta aceptadoN06 no tiempofotográfico; mailreal N10/N12.|N07; cuenta N06/operación N09/transporte N10/N12 condicionado|

La renovación/autosubida conserva13testigos lifecycle, siete carreras de bump y un testigo comercial con prefork/Beat reales, todos con fuentes/resultados conciliados. El calendario comercial antiguo era sintético1s; no acredita cadencia nativa ni cierra N08. El comando propio refresh_publication_state se ejecutó en su testigo original; la tarea sweep se ejecutó manualmente por broker en N07B y no acredita el tick3600s.

## Cambios y resultados nuevos

[N07A402](402-n07-a-correccion-reordenacion-verificada-20261025.md) corrigió una carrera demostrada: una foto retirada mientras reorder esperaba el bloqueo acababa en500. La búsqueda posterior admite ausencia y devuelve404antes de escribir, sin consulta adicional. Dos FAIL originales se preservan; cuatro PASS correctivos57,786sQA incluyen ES/EN y regresiones de edición con navegador. Otras funciones AST idénticas. Es la única corrección de producto nueva de N07; no se atribuye aceleración.

[N07B405](405-n07-b-resultado-publicacion-worker-beat-20261025.md):1PASS118,068sQA, siete tareasSUCCESS reales/rolesSQL, prefork2 y Beat30s/60s sin acelerar;100publicados/102totales,18GETESEN y paridad nativa102filas en cada una de tres fases. Lectura pública/privada niega lo revocado durante retrasos sin depender de read-repair. Startup deliberadamente bloqueado, cola, CPU y cadencia separados; los snapshots dirty no son un censo atómico.

[N07C407](407-n07-c-resultado-colas-y-complemento-cancelacion-20261026.md):16PASS136,563sQA;108GETde cola,48de formulario y62controles de autoridad, con idioma real/contexto/IDs/orden/contenido/enlaces.156GETpropios están dentro de383operaciones globales; no se suman observadores. Ocho originales conservan decisiones/independencia/concurrencia. Escenarios sparse0/1/2, sin carga/p95 ni crecimiento100.

Complemento de cancelación: run20261026-002326-91562ec6, **2PASS54,192sQA**, cero errores/saltos,1758huellas congeladas y sources_unchanged verdadero; PostgreSQL/Client reales, limpieza y Telegramsent comprobados. [Auditoría](evidencias/n07-c-cancelacion-auditoria-20261026.json). Activar→cancelar→retry exacto→nueva ventana→retry antiguo→cancelación nueva conserva publicación/revisión/fechas editoriales y filtro1→0→1→1→0; cuatro eventos nuevos, actor/gestor/versiones correctos. Una cancelación antigua no borra la ventana nueva. Preparación eager, no worker/browser/proveedor ni nueva prueba CSRF.

Primer lote de cancelación002115-2ce17e96:2PASS57,593sJUnit pero runnerINVALID por cambio paralelo de AGENTS.md durante ejecución. Se conserva y no se acepta; no se reetiqueta como PASS. Se repitieron sólo los dos casos, sin tocar producto/instrumento ni repetir C16. Los FAIL de instrumentos anteriores N07B también se conservan como tales.

## Antes y después: tiempos y comportamiento

| Acción / etapa / muestras | Antes | Después o referencia | Diferencia y límite |
| --- | --- | --- | --- |
| Reorder tras remove confirmado, ES/EN |500/StopIteration,2FAIL |404controlado, retirada/orden/versión conservados;4PASS |Corrección funcional; tiempos de petición no comparados |
| Cola abierta, mediana5 ES/EN |Sin base temporal equivalente |Moderación21,976/25,599ms; apelación28,467/20,965ms; matches44,285/43,920ms; foto47,284/51,947ms |Referencia actual sin candidato; tabla407 separa primera/rango/estado/SQL |
| Formulario revisión abierto, mediana5 ES/EN |Sin base equivalente |Moderación93,929/64,778ms; apelación41,323/31,965ms; matches59,183/88,931ms; foto68,469/58,657ms |Nueva referencia; no aceleración causal ni tiempo humano |
| Refresh Beat, dos ejecuciones nativas |Sin base equivalente |177,410/273,180ms de tarea;24,851/10,529ms de cola |n1por fase distinta, no mediana; intervaloBeat29,991871s |
| Expiry Beat nativo |Sin base equivalente |122,627ms tarea/7,390ms cola;61,494s tras spawn |Edad de evento64,572947s observada, no SLA |
| Sweep manual y reparación posterior |Sin base equivalente |452,045/275,777ms tarea |Procesos distintos, no suma como latencia universal; sin calendario3600s |
| Cancelación manual inicial ES/EN, n1por idioma |Opción disponible sin testigo de ejecución localizado |121,143/325,137ms;45SQL y302 |Referencia de ramas separadas, no mejora; detalle de restantes reintentos en auditoría |
| Retry antiguo de cancelación ES/EN, n1 |Sin referencia equivalente |34,278/46,517ms;13SQL y302; nueva ventana intacta |Sin nuevo evento; no promediar con mutación |
| QA de lotes A/B/C/cancelación |Baterías distintas |57,786s/118,068s/136,563s/54,192s respectivamente |No sumar como una ejecución ni usar como latencia de app |

No se persiguió una optimización marginal de N07. Los tiempos actuales son aceptables en alfa; cualquier optimización sin mejora clara se pospone al final del desarrollo y se avanza. El contraste ORB de N03 conserva sus propias cifras y no se cuenta como una nueva mejora de N07.

## Reutilización, garantías y capacidades

La [conciliación](evidencias/n07-testigos-fuentes-conciliacion-20261026.json) valida1507fuentes ejecutables B16:1500idénticas y siete variantes de alcance aceptado; parser/hiredis nativos iguales.145testigos seleccionados en22archivos son resultados originales, no una batería nueva; incluyen ocho de los16actuales, no161casos. La batería amplia histórica conserva3FAILCLI y129SKIP. Tres prototipos SKIP no reciben crédito runtime. Tres controles de317 retienen su instrumento histórico/producto exacto; el primer helper M2M no acredita señal real, que sí tiene un test posterior remove/add. N03/N04/N05/N06 conservan sus aceptaciones y límites; N09/N10 sus dominios compartidos. No se declara capacidad80 000fotos ni garantía universal.

Revisión acotada de los nuevos instrumentos con Django Expert/Reviewer y del consumidor/producer con Django Celery Expert: callbacks on_commit, argumentosID serializables, guardas frescas, límite global4generaciones independiente de retry por mensaje, erroresOSError acotados, lease/fence, estadoDB como autoridad y recuperaciónBeat. Límites globales90/120s de tarea existentes; no modificados ni presentados como prueba de timeout extremo. No se encontraron defectos nuevos en ese alcance; la revisión no sustituye los testigos reales ni copia recetas de skill sin comprobar idempotencia.

Se leyeron AGENTS.md y los cinco registros de instalación aportados por el usuario. Las seis skills son legibles en disco; el catálogo de esta sesión enumera Django Expert, Django Reviewer y UI/UX Pro Max, pero aún no enumera Celery/migraciones/PostgreSQL ni herramientas de django-ai-boost/postgres/context7. Se aplican instrucciones locales pertinentes sin afirmar acceso MCP. PostgreSQLMCP sigue sin destino/rolreadonly explícitos; DjangoMCP dummy no acredita esquema/migraciones. No se conectó por MCP ni se alteraron servicios/esquemas. Las instrucciones de migración/UI se cargarán cuando corresponda, sin repetir pruebas válidas ni reabrir bloques. Cambios laterales de skills/MCP/contrato/relevo se preservan fuera de este commit salvo las partes propias de seguimiento.

## Continuación

N08: favoritos, SEO/documentos públicos y exposición/pedidos sintéticos, familiasI07/I08/I19. Actualizar corte y grafo antes del análisis, revisar testigos/tamaños/permisos y fijar base y criterios antes de cualquier candidato. Reutilizar evidencia exacta cuando proceda, sin proveedores/cobros reales. N11 conciliará la candidata integrada; N15 reconstruirá una vez el grafo completo antes del diferencial final111/338/339 y entregará el inventario de relevo del frontend acordado, sin ejecutar esa reescritura.
