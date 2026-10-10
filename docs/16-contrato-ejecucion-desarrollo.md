# Contrato de ejecución del desarrollo — versión 1.8

Versión vigente1.8/MOD-08: modernización técnica autorizada (§MOD-08) sobre el relevo directo MOD-07; criterios técnicos anteriores se conservan.

Origen: 2026-10-03. Formulación consolidada: 2026-10-09, **MOD-06**, autorizada por el usuario al solicitar consolidar el contrato y adoptar CI propio sin presupuesto para alojamiento. Tipo: especificación de ejecución y aceptación. El proyecto es nuevo y no tiene producción real.

Este texto contiene las reglas vigentes; integra MOD-01–05 y la decisión de CI propio. El [registro de cambios](#18-registro-de-cambios-y-trazabilidad) identifica lo sustituido y el historial íntegro. La formulación anterior deja de ser una segunda fuente de obligaciones. Estado, versiones aceptadas, runtime y única próxima acción: [seguimiento17](17-seguimiento-desarrollo.md).

## 1. Objeto y documentos vinculantes

Desarrollar la aplicación definida en [contrato funcional v1](14-contrato-funcional-v1.md) y [apartado legal público](15-apartado-legal-publico.md) mediante entregas completas de frontend y backend, probarlas desde el principio y después terminar ambas áreas por separado bajo este mismo contrato.

Se incorporan [seguridad](11-plan-seguridad-validacion.md), [operación](12-operacion-seguridad.md), [antiduplicados](10-unicidad-antiduplicados.md), [geografía](09-taxonomia-ubicacion-busqueda.md) y [marco legal](06-marco-legal.md), subordinados a acuerdos posteriores del usuario y a las decisiones funcionales consolidadas. Este documento cambia el orden de ejecución del apartado 11 del contrato funcional; no amplía funcionalidades ni activa cobros.

El usuario delegó decisiones ordinarias. Elegir implementación dentro del alcance, registrar motivos y continuar sin solicitar aprobación al terminar cada hito. Un fallo de prueba obliga a corregir y repetir las pruebas afectadas; no detenerse para preguntar si se corrige.

La creación original de este contrato no inició programación, compra, publicación ni despliegue externo. El inicio de desarrollo fue autorizado el 2026-10-03, como registra el encabezado; desde esa autorización la ejecución sigue la secuencia completa sin una nueva autorización por fase. El estado de reanudación y los bloqueos se consultan en seguimiento17. La autorización de desarrollo no incluye compra, publicación ni despliegue externo. «Sin parar» significa no introducir pausas de aprobación rutinarias, no omitir pruebas, requisitos o dependencias reales.

## 2. Estrategia: flujos completos primero

La aplicación Django renderiza plantillas y fragmentos HTMX: frontend/backend son responsabilidades dentro del mismo producto, no dos proyectos obligatorios ni una API separada.

Cada entrega cruzada incluye modelo/regla, operación servidor, pantalla real, estados de error y pruebas desde navegador. Crear una primera interfaz funcional sencilla; el pulido visual llega después. No sustituir la aplicación por pantallas conectadas únicamente a respuestas inventadas.

PostgreSQL se usa desde las primeras pruebas de integración para que restricciones, transacciones y búsqueda se prueben sobre la base elegida. No usar SQLite como evidencia equivalente. Correo, verificadores y pagos pueden usar adaptadores simulados explícitos; no simular la base de datos, autorización o estados para dar por completo un flujo.

Las funciones locales quedan probadas con datos sintéticos. Una integración simulada no se marca como integración real verificada. La interfaz muestra en entornos de desarrollo/pruebas ese estado cuando corresponde, sin introducirlo en flujos públicos de producción.

## 3. Artefactos comunes preparados al inicio

Entregar antes o junto al primer flujo:

- ADR de versiones soportadas y dependencias compatibles, estructura modular y estrategia de ejecución.
- Compose para aplicación, PostgreSQL y servicios de tareas necesarios; almacenamiento local de pruebas compatible con el adaptador de objetos, sin tratarlo como alojamiento real.
- Configuración separada por entorno, ejemplo de variables sin secretos, migraciones y bootstrap idempotente.
- Datos sintéticos: particular, agencia con dos modelos y editor, moderador, visitante, perfiles pendientes/publicados/retirados y fotografías de prueba autorizadas.
- Comandos documentados para levantar servicios, migrar, cargar fixtures y ejecutar pruebas; CI que los reproduzca.
- Esqueleto ES/EN, navegación, sesiones y página de salud. No exponer salud detallada con secretos o información interna.
- Wireframes funcionales de los flujos que se implementan, matriz de permisos y estados inicial; no esperar diseño perfecto para conectar.

Las fuentes geográficas de pruebas se identifican como muestra sintética/limitada. Preparar importador con licencia/origen/version verificables; no mostrar cobertura nacional real como completada si no se ha importado.

## 4. Fase A — Desarrollo cruzado y pruebas tempranas

Las entregas siguen CR01–CR10 según sus dependencias funcionales reales. Cada flujo debe funcionar en navegador con frontend, backend y persistencia reales antes de aceptar su alcance. Se permite preparar CR10, UI, accesibilidad, ES/EN, SEO u operación mientras otro bloque esté pendiente si no requiere cambiar su contrato compartido; esa preparación no acepta fases ni evita GS-01. Los proveedores pendientes se prueban mediante adaptadores simulados identificados.

| ID | Entrega de extremo a extremo | Frontend y backend incluidos | Aceptación temprana |
| --- | --- | --- | --- |
| CR-01 | Registro, acceso y aceptación legal | Formulario ES/EN, documentos versionados, cuenta, sesión, correo de prueba y recuperación básica | Cuenta se crea solo con aceptación válida; recuperar/acceder funciona; no se enumeran cuentas ni reutilizan códigos |
| CR-02 | Roles, agencias y MFA | Panel de agencia, invitación/editor, perfiles asignados, TOTP/recuperación y permisos | Dos modelos bajo una agencia, acceso aislado; miembro revocado pierde acceso; particulares sin privilegios de agencia |
| CR-03 | Verificación y representación | Pantalla de estado, adaptador de edad/contacto, autorización directa, revocación/transferencia | Una casilla no reemplaza verificación; resultado fallido/pending bloquea publicación; eventos repetidos no duplican estado |
| CR-04 | Borrador de anuncio | Formulario por pasos, categorías/servicios, ES/EN opcional, ciudad/CP, tarifas y contactos | Guarda/retoma datos sintéticos con persistencia real, muestra errores, valida geografía y tarifa «consultar»; impide otra publicación activa por persona |
| CR-05 | Fotografías y coincidencias | Carga, orden/eliminación, límites, worker, SHA-256 y huellas visuales/regionales | Archivo válido produce derivados; fallos quedan visibles y seguros; coincidencia entre agencias/números distintos no publica ni suspende cuenta automáticamente |
| CR-06 | Revisión y publicación | Cola/moderador, motivos, reclamación, revisión aprobada y ficha pública | Aprobar versión válida publica exactamente esa versión; cambios sensibles siguen pendientes y recursos privados permanecen inaccesibles |
| CR-07 | Descubrimiento nacional | Portada/listado/ficha, filtros combinados, búsqueda, CP, paginación y ES/EN | Solo aparecen anuncios públicos/vigentes compatibles; filtros y URL coinciden; privacidad no se filtra en respuestas o caché |
| CR-08 | Favoritos y ciclo de vida | Favoritos privados, disponible ahora, pausa, renovación, caducidad, retiro y traslado | Caducidad/retirada quitan exposición; renovación conserva ID; favoritos aislados; tareas antiguas no republican retirados |
| CR-09 | Denuncias y derechos | Formularios públicos, colas separadas, estado/acuse, decisiones, exportación/retirada privada | Denuncia sin cuenta llega al responsable; derechos requieren comprobación proporcionada; no se filtran denunciantes ni datos ajenos |
| CR-10 | Promociones preparadas | Administración de productos, etiquetas/previsualización, ranking y pedidos/pagos solo en pruebas | Productos sin tarifa no se venden; promoción nunca evita moderación; reintentos no duplican derechos y patrocinio no falsea fecha editorial |

### Alcance mínimo de cada CR

Probar caso válido, error de entrada, usuario sin permiso, estado pendiente/fallo y persistencia tras recargar. Añadir concurrencia/idempotencia cuando afecte propiedad, publicación, códigos, tareas o derechos comerciales. Probar interfaz por acciones de usuario, sin tests que solo repitan el código.

La primera batería navegador empieza en CR-01 y crece con cada flujo. La seguridad se prueba en el flujo que introduce el riesgo; no se pospone toda al final.

En CR-05 se entrega recuperación de candidatos para recortes y un conjunto de pruebas de precisión/falsos positivos; elegir algoritmo y calibrar. No marcar recortes como resueltos solo por añadir un pHash global.

CR-09 incluye el camino público de reclamación de una persona representada sin cuenta, no únicamente solicitudes del titular de agencia. Las autorizaciones se ligan al modelo y al gestor, no a una aceptación genérica.

## 5. Contratos internos de interacción

Completar progresivamente durante fase A una referencia `docs/contratos/` con:

1. Rutas, nombres, métodos, acceso y códigos de resultado de cada operación pública/privada.
2. Formularios: campos, tipos, obligatorio/opcional, formatos, validación servidor y errores de campo/globales.
3. Contextos de plantilla y fragmentos: datos públicos autorizados, estados y acciones disponibles. La visibilidad de un botón no es autorización.
4. Eventos/tareas: entrada por IDs, resultados, reintentos, idempotencia, version y reglas al cambiar gestor/estado.
5. Catálogo, atributos, geografía, tarifas, contactos y estados con identificadores estables.
6. Adaptadores de correo, verificación, almacenamiento y pagos: resultados válidos/fallidos/pendientes y simuladores deterministas.
7. Semántica HTTP/HTMX: navegación normal y directa, errores, redirecciones y protección CSRF; fragmentos no sustituyen páginas canónicas.

No exigir OpenAPI para rutas HTML. Documentarlo solo si se incorpora una API real. Las pruebas de contrato verifican estas interfaces y permisos, sin inmovilizar detalles internos irrelevantes.

## 6. Puerta de separación — GS-01

No separar frontend/backend por fecha o por porcentaje subjetivo. Se puede pasar a fase B únicamente cuando:

- CR-01 a CR-10 tienen recorrido real y sus pruebas esenciales pasan.
- Todas las pantallas de MVP tienen operaciones/estados servidor conocidos y contratos documentados.
- No quedan cambios coordinados conocidos en modelo, permisos, campos, estados, rutas, tareas o presentación de resultados.
- Errores de permisos, publicación, datos privados y cargas introducidos están corregidos.
- Se han probado estados de carga/vacío/error/pendiente y variaciones de rol/idioma; no se necesita un endpoint nuevo para terminar UI.
- Integraciones externas pendientes están aisladas y no implican que se haya cumplido el gate de producción.
- Inventario residual asigna cada tarea a frontend o backend y prueba que no requiere cambiar el contrato compartido.

Entregar acta GS-01 con commit, pruebas, contratos congelados e inventario residual. Congelado significa cambios controlados y versionados, no imposibilidad de corregir errores.

Si una tarea futura necesita cambiar campos/estados o añadir interacción, vuelve a un mini-flujo cruzado con prueba navegador y actualización de contrato antes de seguir separada. No esconder un requisito cruzado como tarea exclusiva de un área para evitar el gate.

## 7. Fase B — Terminación separada bajo el mismo contrato

La separación es de responsabilidad y backlog. No obliga a ejecutar agentes en paralelo ni a mantener ramas divergentes; conserva la aplicación integrada y CI. Las pruebas de integración continúan durante toda la fase.

### B-F — Frontend

Orden de trabajo:

1. Sistema visual común: tipografía, espaciado, colores, componentes y etiquetas claras, sin copiar identidad visual de referencias.
2. Refinar portada/listados/ficha y formularios sobre contratos ya probados.
3. Responsive, navegación teclado, foco, labels, contraste, errores accesibles y mensajes ES/EN; objetivo de ingeniería WCAG 2.2 AA en recorridos principales, sujeto a verificación.
4. Estados de carga/vacío/error/pendiente y consistencia de paneles, agencia y moderación.
5. Entrega de imágenes, CSS/JS y métricas frontend; revisar recursos externos y no añadir rastreadores inadvertidos.
6. Metadatos/canonicalización/idiomas presentados por plantillas conforme a contratos; las reglas servidor se revisan en B-B.

Criterio: no inventar nuevos datos o quitar estados necesarios para simplificar diseño; pasa pruebas navegador y accesibilidad de flujos de MVP. El objetivo de accesibilidad no acredita cumplimiento legal automáticamente.

### B-B — Backend y operación

Orden de trabajo:

1. Optimización medida de consultas/índices, búsqueda y paginación; no cambiar semántica de filtros.
2. Reintentos, tareas pendientes/fallidas, idempotencia, caducidad, invalidación y retirada; calibración de duplicados con evidencia.
3. Seguridad y privacidad IMP-001 a IMP-011 pendientes, auditoría, derechos, retención configurada y permisos de almacenamiento.
4. Importador geográfico con origen/licencia/versionado, validación y actualización; no romper IDs públicos por renombrar. Verificar técnicamente con muestra sintética o fuente autorizada; reservar la cobertura nacional real para su dataset verificado antes de producción.
5. Contratos de adaptadores y fallos verificables localmente. Integración externa real cuando se autorice y exista proveedor, conservando evidencia separada; su contratación no bloquea la aceptación técnica de los adaptadores probados.
6. Configuración Docker/producción, redes, backups, alertas, migraciones y recuperación.
7. Sitemap, respuestas/códigos de retirados y reglas de indexación según contrato.

Criterio: conserva contratos GS-01, pasa pruebas de integridad/permisos/tareas, carga y recuperación; documenta bloqueos externos sin activar integraciones simuladas como reales.

## 8. Fase C — Integración final, correcciones y entrega

1. Ejecutar conjunto completo de pruebas unitarias necesarias, integración PostgreSQL, navegador, permisos y seguridad sobre un mismo commit.
2. Probar ES/EN, móvil/escritorio y roles; recorrer particular y agencia hasta publicación, búsqueda, denuncia y retirada.
3. Prueba de carga y objetivos del contrato funcional con recursos y dataset documentados; medir imágenes/CDN por separado.
4. Ensayo local de despliegue, migración, recuperación/rollback y restauración completa con recursos propios y datos sintéticos; simulacros OP técnicos. Los objetivos de restauración de docs14 §10 siguen vigentes en el alcance ensayado.
5. Revisión técnica de seguridad, permisos y privacidad por Codex, corrección de hallazgos y pruebas afectadas. La revisión independiente externa previa a producción se registra por separado y no se declara realizada desde esta revisión.
6. Revisar versiones ES/EN y mecanismos de aceptación contra flujos implementados, con textos/datos de prueba explícitos. Textos definitivos, identidad real del operador y revisión jurídica son requisitos de producción.
7. Emitir acta de entrega técnica local con evidencias comunes y, por separado, estado de preparación de producción G-01 a G-08; la segunda acta puede permanecer pendiente.

No hacer un último merge sin pruebas después de terminar áreas. Si falla algo, corregirlo y revisar impacto; no declarar terminado solo por acabar el backlog de ambas áreas.

## 9. Pruebas y condiciones de trabajo

Herramientas: Django/pytest sobre PostgreSQL, Playwright para navegador y arnés de carga documentado en ADR/criterios. El [gate propio local](ci-local.md) automatiza checks y perfiles de prueba, se invoca por Codex/operador y conserva evidencia; no hay un servicio de ejecución continua alojado obligatorio.

Reglas:

- CI obligatorio para cambios funcionales: migraciones, pruebas relevantes y calidad estática. No exigir cobertura porcentual arbitraria como sustituto de escenarios críticos.
- Entorno CI propio, por decisión expresa del usuario 2026-10-09 sin presupuesto para alojamiento: [ejecutor local y evidencia](ci-local.md). La obligación anterior se cumple ejecutando y conservando el gate pertinente sobre la versión de entrega; no exige GitHub Actions alojado ni gasto. No sustituye N3, carga requerida o revisión independiente por un perfil reducido.
- Para cada bug funcional, reproducción y regresión significativa cuando proceda; casos de permisos/concurrencia son obligatorios por riesgo.
- Datos y fotos sintéticos/autorizados; no importar anuncios de competidoras como fixtures.
- Entorno reproducible, tiempos/semillas controlados para caducidad/rotación y fallos externos deterministas.
- Pruebas de integración no saltadas para conseguir verde; registrar test no ejecutado y causa.
- Solo repetir/ampliar pruebas si cambios, errores o incertidumbre lo justifican; no ralentizar con verificaciones redundantes.
- Ningún test local acredita comportamiento de proveedor no contratado o revisión jurídica.

## 10. Ejecución continua, dependencias y cambios

La orden de pausa mantiene detenido el goal de Codex. La aclaración posterior MOD-07 autoriza continuidad autónoma de Claude principal hasta cerrar la entrega local; no implica reanudar Codex. El cierre seguro, los commits locales y el relevo autorizados se registran en [seguimiento17](17-seguimiento-desarrollo.md) y [relevo](relevo-claude-20261009.md); no cambian requisitos, objetivos, aceptación ni dirección del proyecto.

Tras inicio de implementación seguir backlog en orden, corregir fallos y actualizar documentación sin cerrar cada fase preguntando «¿continuamos?». Preparar la siguiente entrega con los acuerdos actuales y resolver elecciones reversibles rutinarias.

Si falta proveedor/dato externo, trabajar con adaptador o fixtures, continuar áreas independientes y registrar impacto. No esperar credenciales para diseñar pantalla/estado. Si no existe alternativa válida para una condición de producción, no fingir que está cumplida: mantener entrega local operativa y gate externo pendiente.

Consultar al usuario solo ante cambio material incompatible con alcance/acuerdo, identidad real necesaria o acción externa no autorizada. No comprar, enviar mensajes, contratar ni publicar por la autorización de desarrollo. No inventar plazos de calendario, cuentas, evidencias o aceptación de riesgos.

Cambios de contrato: ID, motivo, requisitos afectados, efecto en datos/seguridad/coste/pruebas y versión. Correcciones internas compatibles se ejecutan y registran sin aprobación adicional; cambios de alcance se presentan concretos y revisables.

## 11. Entregables y definición de terminado

### Entrega técnica local

Aceptar la aplicación conforme al MVP con infraestructura local real, datos sintéticos y adaptadores externos de prueba identificados. Requiere repositorio, Docker/Compose, configuración de ejemplo, migraciones/bootstrap, contratos internos, acta GS-01, frontend/backend terminados y batería N3 sobre la versión integrada, además de carga/recuperación exigidas y documentación operativa.

La aceptación de un flujo local exige cubrir sus decisiones, permisos, privacidad, revocación, concurrencia e idempotencia aplicables. Los datos de prueba deben incluir origen, asociación fiable al sujeto, tratamiento de terceros, identidad/representación simulada, políticas de ensayo explícitas y responsabilidades de revisión separadas dentro de la aplicación. Codex puede definir fixtures y parámetros sintéticos ordinarios y verificar sus mecanismos; no puede convertirlos en identidad, política jurídica o recepción externa reales. Una fuente necesaria sin examinar o un defecto que afecte la cobertura local impide cerrar ese alcance.

La [matriz83](83-auditoria-pendientes-cr09.md) distingue requisito técnico local, evidencia faltante y requisito de producción para cada bloque. Censo de servicios ajenos, responsables humanos reales, proveedor contratado, revisión jurídica y custodia externa no son prerrequisitos de aceptar el correspondiente mecanismo local probado. Se registran como pendientes de producción. Los objetivos numéricos técnicos vigentes y las decisiones de alcance que falten sí pueden bloquear la aceptación técnica afectada.

La entrega incluye una matriz requisito → implementación → versión → prueba → evidencia → límite y un inventario separado de pendientes de producción. Las páginas legales y los mecanismos de aceptación deben funcionar localmente; sus textos sintéticos no se publican. Componentes entregados y preparaciones independientes no equivalen a aceptación de fase.

### Preparación real de producción

Antes de operar con personas/datos reales se requieren operador/dominio, catálogo y tratamientos revisados, identidad/edad/autorización válidas, políticas definitivas por finalidad, contratos/proveedores cuando necesarios, dataset geográfico autorizado/verificado, moderación e incidentes con responsables, custodia/backups, revisión jurídica y seguridad independiente, además de G-01 a G-08. Se validan contra el entorno real autorizado; la prueba local no los acredita.

Si se ha aceptado toda la entrega técnica y faltan esas entradas, el estado es «entrega técnica local completa; producción pendiente». Si falta aceptación técnica, conservar su estado abierto. Cobros reales siguen fuera de v1; tarifas no definidas no bloquean preparación técnica y no se activan importes ficticios como ventas.

## 12. Seguimiento y punto de reanudación

[Registro de ejecución](17-seguimiento-desarrollo.md) conserva fase actual, próximo paso, resultado de pruebas y pendientes externos. Se actualiza al completar entregas o descubrir bloqueos, no como transcripción de cada comando.

Al retomar leer contrato vigente y registro; continuar próximo paso sin reiniciar fases completadas. Ningún cambio de conversación o sesión reduce las condiciones de terminado. El estado de los hitos es el registrado en el seguimiento vigente.

## 13. Modalidad de ejecución por bloques y dependencias

<a id="entregas-completas-y-criterio-de-parada"></a>

Una unidad de entrega es una funcionalidad completa con resultado observable y criterio de aceptación prefijado; no se divide por cantidad de archivos, commits o duración. Dividir solo cuando cada parte tenga utilidad y aceptación propias. Registrar requisito, dependencia real, evidencia exigida y condición de salida en seguimiento17 antes de trabajar.

Mantener como máximo un bloque de integración activo y otro independiente preparado. Avanzar por dependencia funcional; una tarea que cambia modelos, permisos, estados, rutas o presentación compartidos vuelve a un flujo cruzado con integración/navegador. Durante una espera solo editar fuentes que no use la prueba viva. Medir rendimiento sin otra carga propia competidora; bases distintas en el mismo host no acreditan aislamiento de recursos.

<a id="medidas-adicionales-de-eficiencia-autorizadas"></a>

Reutilizar imágenes, dependencias y constructores de fixtures válidos, conservando datos mutables, colas, medios y limpieza propios de cada ejecución. Al completar una entrega registrar versión integrada, resultado terminal y límites; pasos y commits intermedios no son aceptación ni avance. Reabrir componentes aceptados solo por defecto, regresión o requisito concreto demostrado.

Para censo local Redis/AOF/RDB y otras fuentes, inventariar origen/corte/huella/formato/período, lectura reproducible, asociación autorizada del fixture, diferencias de contenido y divulgación revisada. No inferir asociación por UUID, substring, cantidades o inspección parcial; no excluir arbitrariamente una fuente necesaria desconocida. El censo de fuentes reales ajenas a este entorno pertenece a preparación de producción.

## 14. Ejecución eficiente — MOD-02

Las reglas MOD-02 siguientes están incorporadas a la versión vigente; los antecedentes están en el historial.

### Tres niveles de verificación

| Nivel | Cuándo | Evidencia exigida |
| --- | --- | --- |
| N1 | Edición/reproducción de defecto | Ruff/diff/check y prueba significativa afectada; PostgreSQL real si hay persistencia/locks. |
| N2 | Cierre de bloque | Migraciones, HTTP y navegador/ESEN/roles afectados; permisos, privacidad, revocación, concurrencia e idempotencia aplicables; recursos propios y limpieza. |
| N3 | CR09 conjunto, GS01 y entrega final | Batería conjunta sobre la misma versión integrada y carga/recuperación exigidas. No sumar ejecuciones de versiones distintas como batería común. |

Antes de cada batería registrar en seguimiento17 requisito, fuentes/commit y huellas de cambios locales, casos, entorno/handles, evidencia esperada y condición de salida. Congelar las fuentes probadas mientras el proceso esté vivo. Un fallo obliga a esperar terminal, diagnosticar, corregir y repetir lo afectado; ampliar solo por riesgo compartido o incertidumbre concreta. Un cambio exclusivo de documentación no exige repetir pruebas funcionales.

Las atribuciones Codex de este contrato se transfieren al agente principal Claude únicamente para la entrega técnica local restante conforme a MOD-07 (§15); se conservan las exigencias de verificación y aceptación.

El gate propio guarda logs, selección, versiones/huellas, JUnit, exclusiones/skips, duraciones y limpieza. `checks`, `smoke` o `regression` con exclusiones no sustituyen N3 ni capacidad omitida. Codex revisa evidencia antes de aceptar, distingue preparación/fixtures, ejecución, diagnóstico/corrección e integración/runtime, y conserva el consumo realmente observado sin inventar tiempos/costes pasados.

Funcionalidad pequeña cubre todos los escenarios críticos antes del volumen. Volumen, memoria, latencia/consultas y transporte se aceptan en su escenario real documentado. Una optimización necesita hipótesis finita, comparación de la etapa con datos/instrumentación equivalentes y verificación del recorrido afectado. No repetir por rutina un ensayo de 89 minutos para cambios ajenos; tampoco omitirlo cuando una aceptación o riesgo pertinente lo exija. Una iteración sin evidencia nueva termina como negativa/no concluyente; no cierra el requisito ni justifica repetirla idéntica.

## 15. Delegación sin máximo numérico — MOD-03

## MOD-07 — relevo directo a Claude, autorización vigente

La aclaración posterior del usuario («Mis indicaciones han sido para que continúe Claude») cambia expresamente el relevo de propuesta acotada a ejecución principal directa. Claude puede leer/editar el proyecto, usar herramientas nativas/shell/Docker propio, ejecutar verificaciones, corregir, crear commits e integrar localmente y emitir aceptación técnica sustentada en evidencia hasta completar la entrega local. No necesita esperar aplicación/aceptación de Codex ni autorización rutinaria por hito. El goal de Codex permanece pausado; el nuevo goal de Claude tiene la entrega completa como condición de cierre, no la revisión de un prototipo.

Es una excepción local explícita a las atribuciones exclusivas Codex y al modelo delegado V1 de AI_ENGINEERING1.0.1; el contrato reconoce primacía de instrucciones del usuario y cambio del agente principal. Claude principal usa su ejecutor nativo con herramientas; no el adaptador tool-free. El adaptador oficial V1 y contrato externo permanecen intactos y rigen las delegaciones que realmente se invoquen por esa vía. Este relevo no cambia objetivos, pesos, aceptación de fases, datos, privacidad, costes o permisos externos. Registrar base/propiedad de archivos y pruebas; serializar ediciones y preservar trabajo ajeno/dudoso, evidencias negativas y las seis fuentes experimentales hasta revisión. Sin push/publicación/proveedores/gasto/datos reales ni intervención en servicios normales.

La revisión externa aportada por el usuario se conserva como propuesta no ejecutada, no como PASS ni informe V1 aceptado. No se aplica P1–P8 automáticamente: revisar fuentes/documentos y garantías reales, especialmente quota de storage, logs, limpieza exacta y timeouts; la suma de picos es cota superior, no pico síncrono, y un incumplimiento válido sigue FAIL. No dar por verificados controles kernel por leer flags. Un parseo de mounts y límites de conteo/tamaño no prueban por sí solos un techo kernel del almacenamiento ni de logs. Resultado JSON aportado usa STATUS/formatos distintos de V1; útil como contexto externo, no aceptación del adaptador. La lectura de archivos y los tiempos/tokens son declarados por el usuario/Claude, no auditados aquí.

## MOD-08 — modernización técnica del núcleo, autorizada 2026-10-10

Decisión expresa del usuario: «Acepto todo lo que modernice en post de mejorar nuestro proyecto … aprovechar que el desarrollo es nuevo». Se autoriza sustituir piezas técnicas por alternativas más eficientes mientras no exista producción ni datos reales: evidencia inmutable por construcción (append-only impuesto por PostgreSQL y cadena de hashes por expediente) con validación incremental; huellas de versión de fila y sellos de validación por reproducción de consultas; generación de exportaciones en tareas Celery; cifrado AEAD en flujo y binarios en almacenamiento de objetos S3 compatible propio; serialización canónica y hashing más rápidos; descargas servidas por el proxy tras verificación; paralelización de pruebas con bases por worker, plantillas de base de datos y selección por impacto; revisión independiente por lotes auditados.

Límites: no cambia objetivos numéricos ni criterios (página ≤50 filas, p95, revisión independiente auditada, autoridad fresca, privacidad, idempotencia), no rebaja garantías y no autoriza proveedores externos, compras, publicación ni datos reales. Cada sustitución necesita diseño breve, pruebas de equivalencia/completitud por fuente y mutación, N2 propia y registro; los artefactos y digests sintéticos existentes pueden regenerarse cuando una forma canónica cambie, conservando la evidencia histórica como tal. Prioridad: mejoras 3 y 4 en curso, después tareas asíncronas, AEAD/objetos, canónica/hashing y pruebas paralelas, y por último inmutabilidad con cadena de hashes y revisión por lotes, que tocan el contrato funcional y actualizarán contratos internos antes de GS01.

### Antecedente previo al relevo directo

Revisión para el relevo 2026-10-09: AI_ENGINEERING1.0.1 V1 prohíbe herramientas, ediciones directas y operaciones Git del delegado; solo Codex acepta e integra. No autoriza que un goal de Claude ejecute toda la entrega directamente. La [modificación propuesta](relevo-claude-20261009.md#autorización-necesaria-para-un-relevo-directo) requiere instrucción expresa del usuario y procedimiento de escritor compatible; no está adoptada.

Codex dirige arquitectura, integración y aceptación. Claude propone; Codex aplica y verifica. No hay máximo numérico de invocaciones desde la autorización del usuario del 2026-10-06. Conservar el consumo anterior y registrar todas las invocaciones y consumo real en `.ai/tasks/desarrollo.md`; no convertir ausencia de máximo en obligación de delegar o gastar.

Antes de delegar leer completo `/home/felidae/proyectos/arquitectura_codex/docs/AI_ENGINEERING.md`1.0.1 y usar su `scripts/claude-task`, sin copiar ni alterar el adaptador. Elegir tarea acotada dentro del alcance; continuar localmente si falla. No se autorizan compras, nuevas suscripciones o proveedores. Referencias históricas3/3 no son un límite vigente.

## 16. Consolidación del rendimiento de lectura — MOD-04

Estas son las condiciones vigentes de CR09-REND-LECTURA. Los diagnósticos JIT, prohibiciones sustituidas, pilotos y pausas anteriores se consultan como historial; no ordenan reabrir la lectura aceptada ni repetir sus experimentos.

Preservar elegibilidad, autoridad actual, privacidad, normalización, filtros, ranking, orden, recuento exacto y paginación. Cubrir rutas normales, `PRODUCTION`, `checked` y promociones con matriz modo/filtro/promoción → ruta → equivalencia → coste → límite. La arquitectura vigente es §17; los fallbacks nativos mantienen sus guards. No atribuir pruebas de proveedor sintético a verificación externa real.

Toda intervención posterior necesita coste observado → hipótesis → cambio mínimo → equivalencia → comparación HTTP completa → decisión. SQL especializado, raw SQL, conjuntos/EXISTS/joins/índices y eliminación de conversiones/objetos innecesarios son opciones permitidas; no es obligatorio permanecer en ORM. Código nativo solo ante CPU Python dominante demostrada tras eliminar trabajo innecesario. No estimar validación como total−SQL, CPU PostgreSQL desde cursor.execute o filas SQL desde objetos ORM; registrar materialización lazy, overhead y lo no medido.

Conservar recursos y criterios del ciclo de lectura: no aumentar workers, escalar PostgreSQL o añadir caché como compensación sin cambio autorizado. La comparación histórica 4/6/6/4 fue acotada y no autoriza adopción permanente de seis. El estado derivado expresamente aprobado en §17 está permitido; la antigua prohibición general de persistencia queda sustituida.

### Verificación y aceptación

Para un cambio que reabra esta entrega: equivalencia pertinente → integración → matriz comparable de 100/1.000/10.000 con diversidad y controles sin profiler → corto completo → contractual solo tras PASS. Reutilizar evidencia válida y ejecutar solo controles que el cambio o la incertidumbre justifiquen.

| Comprobación | Condición exigida |
| --- | --- |
| Equivalencia | IDs elegibles ordenados, recuento y páginas inicial/intermedia/última; errores/normalización/ranking; negativas fuera de primera página, wrappers/helpers y carreras de revocación/catálogo/documentos pertinentes. |
| Generador/contabilidad | 0 no emitidas; demora p95 ≤10 ms, p99 ≤25 ms, máximo ≤100 ms; timeout por petición 65 s; contabilidad reconciliada. |
| Corto | 10.000 anuncios, 20 RPS durante 60 s, 1.200 dinámicas y 1 upload separado; drain ≤70 s, pendientes al cierre ≤20 y finales 0; p95 observable de todas las dinámicas emitidas terminadas, incluidos errores/timeouts, <800 ms; errores <1%; upload 302 conforme. |
| Contractual | 10.000 anuncios, 20 RPS durante 900 s, 18.000 dinámicas; mezcla 1/3 listado, 1/3 búsqueda, 1/3 ficha ES/EN; 15 uploads separados, uno/minuto; p95 observable <800 ms, errores <1%, generador/drain/política contable vigentes y uploads conformes. |

Marco completo: [criterios de carga](criterios-revision-benchmark-carga.md). Conservar veredicto de transporte y gate completo separados. INVALID por escenario/generador/contabilidad inválidos; FAIL por criterio incumplido en ensayo válido; PASS solo al cumplir todos. FAIL/INVALID corto bloquean contractual. No cambiar clasificaciones históricas ni trasladar retroactivamente criterios.

El PASS acredita únicamente fuente, fixture, recursos y rutas declaradas. El cierre local requiere además integración/runtime pertinente y evidencia revisada. No prueba capacidad grande PRODUCTION/`checked`, expedientes grandes, proveedor, CR09 integral o producción por extrapolación. Las imágenes/CDN se miden aparte de peticiones Django. Los objetivos de expedientes grandes tienen criterios propios fijados por delegación posterior y registrados en seguimiento17; su definición no acredita capacidad y no modifica los umbrales de lectura.

## 17. Estado de publicación almacenado — MOD-05

Arquitectura vigente autorizada el 2026-10-08. Garantías obligatorias:

1. **Fuente de verdad única:** `moderation.publicly_visible` / `submissions.validate_submission` y sus formularios. El estado guarda su resultado excluida la caducidad, que siempre se compara en SQL, junto con los flags de comprobaciones reales para `checked`.
2. **Invalidación completa en base de datos:** triggers de sentencia (INSERT/UPDATE/DELETE con tablas de transición, y TRUNCATE) en cada tabla que lee la regla marcan los anuncios afectados en la misma transacción. Ninguna ruta de aplicación puede omitirlos. Una prueba de completitud compara las tablas leídas realmente por la regla con las que tienen trigger y falla ante una dependencia nueva sin cubrir.
3. **Exactitud independiente del recálculo:** un resultado almacenado solo se usa si el anuncio no está sucio y fue calculado con la versión de reglas vigente. Cualquier otro candidato se evalúa con la regla nativa en la misma petición, en una instantánea `REPEATABLE READ` común a recuento y página. La página se revalida con la regla nativa antes de presentarse.
4. **Recálculo concurrente seguro:** lotes `FOR UPDATE SKIP LOCKED`. La marca solo se retira si no cambió durante el cálculo. La reparación en lectura (recalcular en peticiones GET marcas de más de 2 s) queda desactivada por defecto por decisión del usuario y solo se activa explícitamente como resiliencia.
5. **Versión de reglas sin bytecode:** hash del código fuente de los módulos de la regla, versión de Django y configuración pertinente, calculado una vez por proceso.
6. **Invariante y barrido (decisión del usuario, 2026-10-08):** todo cambio de comportamiento de la regla debe producirse mediante una fuente versionada (`RULE_SOURCES`), la versión de Django, la configuración versionada o una escritura en una tabla de dependencia. Una prueba traza qué ficheros del proyecto ejecuta la regla y exige que estén versionados; otra compara las tablas leídas con las que tienen trigger. Para acotar cualquier divergencia no capturada, un barrido periódico (Beat, cada hora) recalcula con la regla nativa todo estado fiable y **marca** los anuncios divergentes, sin escribir estado directamente, y registra un aviso sin datos personales. Entre barridos, una divergencia no capturada solo puede ocultar un anuncio publicable (falso negativo): la exposición indebida la impide la revalidación nativa de la página.

El esquema actual define dos tablas derivadas, 35 tablas de dependencia × 4 triggers y migraciones 0015/0017. El recuento del código no prueba que el esquema esté aplicado en servicios normales; esa evidencia corresponde a seguimiento17. Cambios globales de documento/catálogo marcan toda la población y se recalculan dentro de la misma operación o mediante el comando dedicado.

Restauraciones con `--disable-triggers` o `session_replication_role=replica` deben marcar toda la población antes de servir tráfico, conforme al [procedimiento de restauración](85-operacion-registro-recuperacion.md#estado-de-publicación-tras-restaurar-mod-05). Probar completitud de dependencias, mutaciones por familia, carreras y equivalencia byte a byte con regla nativa normal/PRODUCTION. La página mantiene revalidación nativa actual.

La vía proyectada anterior y sus pruebas experimentales se retiraron; no se requieren como compatibilidad de producción inexistente. La evidencia histórica se conserva. Simplificar componentes abandonados y conservar migraciones/evidencia que aún tengan una función comprobable; cualquier reconstrucción de esquema necesita procedimiento y verificación, no se ejecuta por esta consolidación.

## 18. Registro de cambios y trazabilidad

| Cambio | Fecha / versión | Decisión incorporada |
| --- | --- | --- |
| Inicio | 2026-10-03  / 1.0 | Desarrollo cruzado, PostgreSQL y aceptación separada local/producción. |
| MOD-01 | 2026-10-06  / 1.1 | Bloques completos, dependencias funcionales y preparación independiente; su antiguo límite Claude fue sustituido. |
| MOD-02 | 2026-10-06  / 1.2 | N1/N2/N3, proporcionalidad, fuentes congeladas y reutilización de evidencia válida. |
| MOD-03 | 2026-10-06  / 1.3 | Delegación sin máximo numérico; adaptador oficial y consumo acumulado. |
| MOD-04 | 2026-10-07  / 1.4 | Rendimiento de lectura y criterios de medición; diagnóstico secuencial/prohibición de persistencia sustituidos por arquitectura MOD-05. |
| MOD-05 | 2026-10-08  / 1.5 | Estado de publicación con garantías, autorización para simplificar lo abandonado en proyecto nuevo. |
| MOD-08 | 2026-10-10  / 1.8 | Modernización técnica autorizada sin cambiar objetivos ni garantías; sustituciones con equivalencia y N2 propias. |
| MOD-06 | 2026-10-09  / 1.6 | Formulación operativa consolidada, aceptación local/producción explícita y CI propio sin dependencia de pago. |

MOD-06 afecta §§1–17, interpretación de cierre en matriz83 y formulación relacionada en contratos14/15. No amplía el MVP, introduce cobros, rebaja permisos/privacidad/pruebas, cambia pesos/SLO o acepta una fase. No cambia código, esquema o datos ni autoriza publicación, proveedores o cargas nuevas. Los parámetros sintéticos prueban mecanismos; no aprueban políticas reales. El presupuesto futuro de planificación no es presupuesto disponible ni autorización de gasto.

[Copia íntegra anterior a esta consolidación](17-historial/2026-10-09-16-contrato-ejecucion-desarrollo-antes-consolidacion-contrato.md): contiene texto 1.5 y adendas originales, incluyendo pausas, diagnósticos, cifras y decisiones sustituidas. [Manifest de copias y SHA-256](historial-documentacion.json), [registro de consolidación](evidencias/consolidacion-contrato-20261009.json). El historial sirve de evidencia, no de segunda cola o instrucción actual.


MOD-07 / v1.7: aclaración del usuario para continuidad principal directa de Claude. Excepción local de atribuciones/ejecutor/aceptación; objetivos y garantías preservados, adaptador/contrato externo intactos. No ejecución, nuevo PASS ni aceptación de fase por esta modificación documental.
