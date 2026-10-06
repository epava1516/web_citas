# Contrato de ejecución del desarrollo — versión 1.3

Fecha: 2026-10-03. Estado: ejecución iniciada por autorización del usuario el 2026-10-03. Tipo: especificación de ejecución y aceptación, no contrato mercantil ni acreditación jurídica.

## 1. Objeto y documentos vinculantes

Desarrollar la aplicación definida en [contrato funcional v1](14-contrato-funcional-v1.md) y [apartado legal público](15-apartado-legal-publico.md) mediante entregas completas de frontend y backend, probarlas desde el principio y después terminar ambas áreas por separado bajo este mismo contrato.

Se incorporan [seguridad](11-plan-seguridad-validacion.md), [operación](12-operacion-seguridad.md), [antiduplicados](10-unicidad-antiduplicados.md), [geografía](09-taxonomia-ubicacion-busqueda.md) y [marco legal](06-marco-legal.md), subordinados a acuerdos posteriores del usuario y a las decisiones funcionales consolidadas. Este documento cambia el orden de ejecución del apartado 11 del contrato funcional; no amplía funcionalidades ni activa cobros.

El usuario delegó decisiones ordinarias. Elegir implementación dentro del alcance, registrar motivos y continuar sin solicitar aprobación al terminar cada hito. Un fallo de prueba obliga a corregir y repetir las pruebas afectadas; no detenerse para preguntar si se corrige.

La petición actual autoriza crear este contrato; no inicia programación, compra, publicación o despliegue externo. Una vez indicado el inicio, la ejecución seguirá la secuencia completa sin una nueva autorización por fase. «Sin parar» significa no introducir pausas de aprobación rutinarias, no omitir pruebas, requisitos o dependencias reales.

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

Cada entrega depende de las anteriores. Un flujo funciona en navegador con frontend real y backend real antes de pasar al siguiente; los servicios externos pendientes quedan simulados por adaptador y registrados.

| ID | Entrega de extremo a extremo | Frontend y backend incluidos | Aceptación temprana |
| --- | --- | --- | --- |
| CR-01 | Registro, acceso y aceptación legal | Formulario ES/EN, documentos versionados, cuenta, sesión, correo de prueba y recuperación básica | Cuenta se crea solo con aceptación válida; recuperar/acceder funciona; no se enumeran cuentas ni reutilizan códigos |
| CR-02 | Roles, agencias y MFA | Panel de agencia, invitación/editor, perfiles asignados, TOTP/recuperación y permisos | Dos modelos bajo una agencia, acceso aislado; miembro revocado pierde acceso; particulares sin privilegios de agencia |
| CR-03 | Verificación y representación | Pantalla de estado, adaptador de edad/contacto, autorización directa, revocación/transferencia | Una casilla no reemplaza verificación; resultado fallido/pending bloquea publicación; eventos repetidos no duplican estado |
| CR-04 | Borrador de anuncio | Formulario por pasos, categorías/servicios, ES/EN opcional, ciudad/CP, tarifas y contactos | Guarda/retoma datos reales, muestra errores, valida geografía y tarifa «consultar»; impide otra publicación activa por persona |
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
4. Importación geográfica completa con licencia cuando disponible, validación y actualización; no romper IDs públicos por renombrar.
5. Integración externa real cuando contratada, manteniendo adaptadores; registrar pruebas reales por separado de simuladores.
6. Configuración Docker/producción, redes, backups, alertas, migraciones y recuperación.
7. Sitemap, respuestas/códigos de retirados y reglas de indexación según contrato.

Criterio: conserva contratos GS-01, pasa pruebas de integridad/permisos/tareas, carga y recuperación; documenta bloqueos externos sin activar integraciones simuladas como reales.

## 8. Fase C — Integración final, correcciones y entrega

1. Ejecutar conjunto completo de pruebas unitarias necesarias, integración PostgreSQL, navegador, permisos y seguridad sobre un mismo commit.
2. Probar ES/EN, móvil/escritorio y roles; recorrer particular y agencia hasta publicación, búsqueda, denuncia y retirada.
3. Prueba de carga y objetivos del contrato funcional con recursos y dataset documentados; medir imágenes/CDN por separado.
4. Ensayo de despliegue, migración y rollback compatible; restauración completa y simulacros OP requeridos.
5. Revisión independiente de seguridad cuando exista responsable externo; corregir hallazgos y repetir pruebas afectadas.
6. Revisar apartado legal/textos y aceptación contra flujos implementados. No publicar placeholders de operador o políticas que describan funciones inexistentes.
7. Emitir entrega técnica y, por separado, acta de preparación de producción con G-01 a G-08.

No hacer un último merge sin pruebas después de terminar áreas. Si falla algo, corregirlo y revisar impacto; no declarar terminado solo por acabar el backlog de ambas áreas.

## 9. Pruebas y condiciones de trabajo

Herramientas candidatas: runner Django/pytest con PostgreSQL, Playwright para navegador y herramienta de carga seleccionada en ADR. Elegir según soporte/versiones, no añadir herramientas duplicadas por principio.

Reglas:

- CI obligatorio para cambios funcionales: migraciones, pruebas relevantes y calidad estática. No exigir cobertura porcentual arbitraria como sustituto de escenarios críticos.
- Para cada bug funcional, reproducción y regresión significativa cuando proceda; casos de permisos/concurrencia son obligatorios por riesgo.
- Datos y fotos sintéticos/autorizados; no importar anuncios de competidoras como fixtures.
- Entorno reproducible, tiempos/semillas controlados para caducidad/rotación y fallos externos deterministas.
- Pruebas de integración no saltadas para conseguir verde; registrar test no ejecutado y causa.
- Solo repetir/ampliar pruebas si cambios, errores o incertidumbre lo justifican; no ralentizar con verificaciones redundantes.
- Ningún test local acredita comportamiento de proveedor no contratado o revisión jurídica.

## 10. Ejecución continua, dependencias y cambios

Tras inicio de implementación seguir backlog en orden, corregir fallos y actualizar documentación sin cerrar cada fase preguntando «¿continuamos?». Preparar la siguiente entrega con los acuerdos actuales y resolver elecciones reversibles rutinarias.

Si falta proveedor/dato externo, trabajar con adaptador o fixtures, continuar áreas independientes y registrar impacto. No esperar credenciales para diseñar pantalla/estado. Si no existe alternativa válida para una condición de producción, no fingir que está cumplida: mantener entrega local operativa y gate externo pendiente.

Consultar al usuario solo ante cambio material incompatible con alcance/acuerdo, identidad real necesaria o acción externa no autorizada. No comprar, enviar mensajes, contratar ni publicar por la autorización de desarrollo. No inventar plazos de calendario, cuentas, evidencias o aceptación de riesgos.

Cambios de contrato: ID, motivo, requisitos afectados, efecto en datos/seguridad/coste/pruebas y versión. Correcciones internas compatibles se ejecutan y registran sin aprobación adicional; cambios de alcance se presentan concretos y revisables.

## 11. Entregables y definición de terminado

### Entrega técnica local

- Repositorio completo y aplicación funcional conforme al MVP.
- Docker/Compose, configuración de ejemplo, migraciones y bootstrap; inicio documentado sin secretos reales.
- Datos sintéticos y simuladores identificados; no verificación de edad/pago falsamente acreditados.
- Contratos internos, acta GS-01, decisiones técnicas y matriz requisito → implementación → prueba → evidencia.
- Frontend terminado y backend terminado sobre el mismo commit con regresión común.
- Resultados de pruebas/carga/recuperación y lista de pendientes externos explícita.
- Documentación para ejecutar, mantener, desplegar y recuperar; rutas legales y aceptación implementadas, textos incompletos solo en entornos privados.

### Preparación real de producción

Además: operador y dominio reales, contratos/proveedores/datasets, verificación válida, revisión jurídica, personal de moderación/incidentes, retención definitiva, revisión independiente y gates G-01 a G-08 verificados. Si no se cumplen, el estado es «entrega técnica local completa; producción pendiente», no «listo para producción».

Los cobros reales siguen fuera de v1 aunque el módulo comercial esté preparado. Tarifas no definidas no bloquean entrega técnica y no se activan con importes ficticios.

## 12. Seguimiento y punto de reanudación

[Registro de ejecución](17-seguimiento-desarrollo.md) conserva fase actual, próximo paso, resultado de pruebas y pendientes externos. Se actualiza al completar entregas o descubrir bloqueos, no como transcripción de cada comando.

Al retomar leer contrato vigente y registro; continuar próximo paso sin reiniciar fases completadas. Ningún cambio de conversación o sesión reduce las condiciones de terminado. El estado de los hitos es el registrado en el seguimiento vigente.

## 13. Modalidad de ejecución por bloques y dependencias

Cambio MOD-01, autorizado por el usuario el 2026-10-06. Versión1.1. Motivo: reducir fragmentación, verificaciones redundantes y esperas, conservando alcance, seguridad, privacidad y aceptación. Afecta al orden de ejecución de las secciones4,6,9,10 y12; no modifica requisitos funcionales, datos, proveedores ni gates de producción. MOD-01 no autoriza gasto ni publicación. Su límite histórico de Claude3/3 queda sustituido por la política vigente de §15; se conserva el consumo registrado.

### Una cola y un cierre verificable por bloque

El seguimiento17 contiene la única cola operativa. Antes de desarrollar un bloque, registrar requisito, resultado observable, dependencias reales, evidencia exigida y criterio de cierre. Al entregarlo, registrar commit, pruebas y pendientes. Distinguir componente entregado, aceptación integral de fase y preparación de producción. Reabrir solo por defecto reproducible, regresión o requisito concreto incumplido, registrando motivo y alcance.

Para el censo histórico Redis/AOF de CR09, cerrar primero un inventario de fuentes conocidas: snapshot/base, prefijo y sufijo AOF, colas/reservados, copias y backups pertinentes. Por fuente registrar origen y corte temporal, lectura acotada reproducible, asociación autorizada al titular y tratamiento de formatos desconocidos, diferencias de contenido y cobertura pendiente. Igualdad de cantidades, inspección parcial o captura cifrada no acreditan cobertura completa. Una fuente necesaria no examinada mantiene el censo abierto; no convertirla arbitrariamente en exclusión ni permitir un acceso completo con cobertura parcial. Nuevas fuentes relevantes se añaden con el requisito que justifica incluirlas, sin rehacer componentes correctos.

### Avance independiente sin saltar puertas

La dependencia entre CR se exige cuando exista dependencia funcional real. Se pueden ejecutar tareas preparatorias de CR10 y de acabado visual, accesibilidad, ES/EN, SEO y operación antes del cierre de CR09 si se identifica por escrito que no necesitan modificar sus modelos, permisos, estados, rutas o contratos pendientes. Esto permite preparación anticipada, no acepta CR10 ni inicia formalmente BF/BB: GS01 conserva todas sus condiciones. Una tarea que requiera cambios compartidos sigue siendo un flujo cruzado con integración y prueba navegador.

Mantener como máximo un bloque de integración activo y un bloque independiente preparado para avanzar ante un bloqueo real. Paralelizar trabajo solo cuando responsabilidades, interfaces y archivos afectados permitan integración segura; no implica lanzar agentes ni procesos concurrentes sobre los mismos recursos. Ante una dependencia externa, registrar responsable requerido, evidencia faltante e impacto en aceptación, y continuar trabajo independiente. No sustituirla por un simulador declarado real.

### Verificación proporcionada y progreso

Después de cada cambio ejecutar las pruebas afectadas y las de riesgos compartidos identificados; permisos, privacidad, concurrencia y migraciones se incluyen cuando corresponda. Registrar versión, alcance y resultado para reutilizar evidencia aún válida. Repetir por cambio relevante, fallo o incertidumbre documentada, no por rutina. En el cierre integral de CR09 ejecutar su batería conjunta sobre una misma versión; conservar regresión completa y gates exigidos en GS01/faseC, sin sumar resultados de versiones diferentes como una verificación común. PostgreSQL sigue siendo obligatorio.

Actualizar la estimación ponderada al aceptar alcance nuevo usando los mismos pesos y justificando el cambio por bloque. El número de pruebas y el tiempo invertido no son avance aceptado. El contrato continúa hasta completar todas sus fases; esta modalidad no reduce comprobaciones ni permite declarar preparación de producción con revisión jurídica, seguridad o proveedores pendientes.


## 14. Ejecución eficiente — MOD-02

Adenda autorizada por el usuario en conversación lateral: implementar las propuestas de aceleración y avisar al hilo principal. Versión1.2. Complementa MOD01 y concreta secciones9/10/12/13; conserva alcance, pesos, seguridad, PostgreSQL obligatorio, aceptación de fases y gates externos. Se aplica al siguiente paso sin detener ni alterar procesos ya lanzados. No autoriza agentes adicionales, proveedores, publicación ni datos reales.

### Tres niveles de verificación

| Nivel | Cuándo | Evidencia exigida |
| --- | --- | --- |
| N1, feedback durante edición | Cambio reversible o reproducción de defecto | Ruff/diff/check y prueba significativa mínima afectada. Si necesita persistencia/locks, PostgreSQL real con dataset pequeño; unitarios/simuladores no sustituyen esa evidencia. |
| N2, cierre del bloque | Implementación completa con interfaz/contrato conocido | Migraciones, HTTP y navegador/idiomas/roles afectados; autorización, privacidad, revocación, concurrencia e idempotencia según riesgo. Recursos desechables y limpieza; resultado completo, no marcadores parciales. |
| N3, aceptación de fase | CR09 conjunto, GS01 y entrega final según contrato | Batería conjunta sobre una misma versión y carga/recuperación exigidas. Mantener todos los escenarios críticos; evidencia de bloques separada no equivale a batería conjunta. |

Antes de lanzar cada batería, registrar requisito, fuentes/commit, selección de casos, recurso/handle y condición de salida en seguimiento17. No ejecutar N3 ni ensayos largos tras cada edición. Repetir solo por cambio relevante, fallo o incertidumbre explícita; un cambio exclusivo de documentación no invalida pruebas funcionales. Ante un fallo, esperar terminal, identificar su causa, corregir y repetir casos afectados; ampliar solo por riesgo compartido. No retocar fuentes que usa un proceso vivo.

### Funcionalidad y rendimiento separados

Los casos funcionales pequeños cubren decisiones, permisos, errores, replays y carreras reales antes del volumen; reducir el dataset no reduce esos escenarios. Los ensayos grandes acreditan volumen, memoria, latencia/consultas y transporte en su alcance real. Primero probar funcionalidad; después medir cuando el cambio afecte al camino costoso o sea requisito de aceptación. Eliminar la obligación rutinaria de repetir un recorrido de89 minutos para cambios ajenos a ese recorrido; no eliminar el ensayo requerido al aceptar la fase ni la regresión grande afectada por una optimización.

Para una optimización: comparar la etapa afectada con evidencia anterior válida, mismo dataset/instrumentación y contexto de recursos documentado. Después ejecutar recorrido amplio si el cambio/riesgo lo requiere. Un resultado más rápido no acredita equivalencia, seguridad ni capacidad total. Las condiciones externas y pruebas de identidad/entrega no se acreditan con simuladores.

### Trabajo útil durante esperas

Mantener un bloque de integración activo y un independiente preparado, como MOD01. Durante N2/N3 se puede completar interfaz, accesibilidad, traducciones, contratos o trabajo independiente en archivos/worktree que no usa la prueba. No introducir dependencias personales fuera del censo ni aceptar fases anticipadamente. Una medición de rendimiento exige recursos estables: evitar otra carga PG/browser/build competidora mientras se mide; esa restricción temporal no congela todo el desarrollo. Las pruebas funcionales pueden coexistir únicamente con aislamiento real documentado y sin cambiar las fuentes probadas; no inferir aislamiento porque las bases tengan nombres distintos si comparten recursos relevantes.

### Entregas completas y criterio de parada

Precisión autorizada por el usuario en conversación lateral: la unidad de entrega es una funcionalidad completa y verificable, con resultado observable y criterio de aceptación definido antes de implementarla. No limitar ni dividir entregas por número de archivos, commits o duración. Los pasos internos preservan trabajo y permiten feedback, pero no son entregas independientes, cierres ni avance aceptado por sí mismos.

Dividir un bloque únicamente cuando cada parte tenga utilidad y aceptación propias, con integración y pruebas pertinentes completas. Si para verificar una parte es necesario terminar la siguiente, mantenerlas en la misma entrega. Priorizar cerrar los bloques actuales antes de abrir nuevas subdivisiones; conservar los pendientes reales de fase y producción sin convertirlos en cierres ficticios. Esta precisión complementa MOD-02 sin cambiar alcance, pesos ni gates.

Agrupar implementación, pruebas relevantes, contrato, integración/runtime y evidencia en una entrega por bloque. Los commits intermedios sirven para preservar trabajo; no son cierres ni obligan a una batería completa por commit. Una vez cumplido el criterio del bloque, registrar cerrado localmente, pendientes de fase/producción por separado y pasar al siguiente bloque preparado. No seguir puliendo/reabriendo el mismo componente sin defecto, requisito o riesgo concreto. La revisión inicial y el despliegue siguen sujetos a las reglas existentes.

Seguimiento17 contiene la próxima acción única y el próximo independiente. La cronología va al historial. Registrar avance al entregar o descubrir un fallo/dependencia material; durante esperas, verificar el handle y comunicar estado sin crear otra cola o volver a listar una preparación como nueva entrega.

### Dependencias externas desde ahora

Mantener en la cola un registro de requisito externo, responsable requerido (pendiente de designación si no existe), evidencia faltante, impacto local/producción y trabajo que puede continuar. Referenciar operación12/marco legal06 y gates existentes; no inventar responsables, plazos o aceptación. Proveedores/revisión jurídica/identidad real no paralizan trabajo local independiente. Las tarifas aún no decididas y los cobros reales fuera de v1 no bloquean la preparación técnica comercial ni autorizan activar ventas.

### Medidas adicionales de eficiencia autorizadas

Ampliación de MOD-02 solicitada por el usuario en conversación lateral el2026-10-06. Mantiene la entrega por funcionalidad completa definida arriba y todos los controles del contrato. Incorporar estas medidas al siguiente trabajo pertinente; no reiniciar procesos activos ni introducir una fase de optimización que impida cerrar los bloques actuales.

- **Entornos reutilizables y aislados:** reutilizar imágenes Docker, dependencias instaladas y constructores de fixtures sintéticos pequeños cuando sus versiones sigan siendo válidas. Cada ejecución conserva bases, medios, colas y limpieza propios según sus riesgos; no reutilizar datos mutables o evidencia antigua como un resultado nuevo. PostgreSQL real sigue siendo obligatorio en integración. Reconstruir los componentes afectados cuando cambien sus fuentes/configuración.
- **Diagnóstico con condición de salida:** antes de investigar registrar defecto o incertidumbre, hipótesis, evidencia nueva esperada y condición de salida. Si una iteración no aporta evidencia nueva, resumir lo descartado y cambiar de estrategia o registrar la dependencia real para avanzar trabajo independiente. No repetir pruebas o búsquedas idénticas sin cambio, hipótesis o fuente nueva; no declarar resuelto un requisito por agotar la investigación.
- **Informe de cierre automatizado:** aprovechar y completar los ejecutores existentes para reunir versión/huellas probadas, comando y selección de casos, resultado terminal, recursos y limpieza, enlaces de evidencia y pendientes. Generar un resumen por entrega completa; revisión de Codex antes de actualizar el seguimiento. No inferir aprobación desde marcadores parciales, mezclar versiones ni acreditar producción automáticamente. Implementar la automatización incrementalmente cuando sirva al bloque actual, sin crear otro bloque preparatorio innecesario.
- **Prioridad por dependencias reales:** resolver primero contratos de datos, permisos e interfaces compartidas que desbloqueen el siguiente resultado verificable. Documentar la dependencia concreta; no reabrir contratos ya correctos por prioridad abstracta. Reservar ajustes visuales y otros trabajos independientes para esperas compatibles con las restricciones de recursos de MOD-02.
- **Medición del tiempo perdido:** en los próximos ejecutores pertinentes registrar por separado preparación del entorno/fixtures, ejecución de pruebas, diagnóstico y corrección, e integración/verificación runtime. Distinguir duración observada y estimaciones; no reconstruir tiempos pasados sin evidencia ni convertirlos en avance porcentual. Usar los resultados para elegir la siguiente mejora del cuello de botella real, sin añadir instrumentación costosa a todas las operaciones ni confundir tiempos de test con latencia/capacidad del producto.


## 15. Delegación sin máximo numérico — MOD-03

Cambio autorizado expresamente por el usuario el2026-10-06: «Elimina el limite y actualizalo». Versión1.3. Se elimina el máximo de tres invocaciones Claude para el objetivo completo de desarrollo. No se establece un nuevo máximo numérico ni se reinicia el consumo: tres invocaciones anteriores siguen registradas en .ai/tasks/desarrollo.md y cada nueva llamada se registra allí. Referencias3/3 o «sin nuevas invocaciones» en cronologías y adendas anteriores reflejan la política histórica; esta sección prevalece para la delegación vigente.

Codex conserva arquitectura, integración y aceptación; Claude propone y Codex aplica y verifica. Antes de delegar leer completo /home/felidae/proyectos/arquitectura_codex/docs/AI_ENGINEERING.md (1.0.1) y usar su scripts/claude-task sin copiar ni alterar el adaptador. Elegir tareas acotadas útiles para el objetivo; continuar localmente si una llamada falla. La eliminación del máximo no exige delegar ni relaja aislamiento, fuentes congeladas o controles MOD-02.

Impacto: habilita nuevas invocaciones mediante el adaptador bajo el mismo alcance; consumo y costes reales se registran sin inventar importes. No cambia modelos, datos, alcance funcional, gates, pruebas, pesos o porcentajes; no autoriza publicación, contratación de proveedores ni datos reales. Este cambio documental no invalida evidencia funcional ni requiere reiniciar pruebas activas.
