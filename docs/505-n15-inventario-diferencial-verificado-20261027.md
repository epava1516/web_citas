# N15 — inventario diferencial verificado

Se actualizaron [338](338-inventario-acciones-recorridos-alpha-20261025.md) y
[339](339-diferencial-inventario-recorridos-20261025.md) después del grafo completo
[503](503-n15-grafo-total-reconstruido-y-verificado-20261027.md), conforme a
[504](504-n15-prerregistro-diferencial-inventario-20261027.md). El
[censo actual](evidencias/inventario-acciones-actual-20261027.json) tiene **444
unidades**: conserva literalmente los 443 IDs originales y añade un receptor
de login de Admin. No hay bajas ni renumeración por desplazamiento de líneas.
La [verificación](evidencias/inventario-acciones-verificacion-20261027.json)
identifica el corte y sus límites.

| Unidad | Antes | Después |
| --- | ---: | ---: |
| IDs de acciones censadas | 443 | 444 |
| Familias I01–I28 | 28 | 28 |
| Rutas propias con nombre | 170 | 170 |
| Tareas shared_task | 27 | 27 |
| Comandos propios / framework | 15 / 31 | 15 / 31 |
| Patrones distintos tras ES/EN | 366 | 366 |
| Inscripciones propias de señales | 1 | 2 |
| Despachos async/commit | 14 | 14 |
| Plantillas / interactivas / JavaScript | 129 / 106 / 3 | 129 / 106 / 3 |

La fase no cambia código de aplicación ni mide nuevas latencias. El diferencial
conserva los tiempos de rendimiento en sus testigos originales, con escenario y
versión; duración de QA o censo no sustituye una medida de la app. Los objetivos
2 s / 5 s de MOD09 siguen FAIL y diferidos según367.

## Alta y correspondencia

Nuevo ID: `signal_connection:user_logged_in:apps.core.admin.bind_admin_login_epoch`.
El módulo propio core.admin no existía en el corte N00. El receptor añadido en
N10 sólo inicializa account_version desde session_version en POST del login
nativo de Admin; no concede MFA ni permisos. Su fuente actual coincide con la
fuente de login aceptada por N10. Se reutiliza esa disposición acotada, sin
emitir señales ni repetir pruebas. La inscripción original signal_connection:0
sigue siendo el bucle de publicación con tres eventos, ahora en posición1 del
escáner: posición y línea son localizadores, no identidad.

El resolver frío con conexiones bloqueadas produjo 372 filas ES/EN, 366 patrones
distintos y 46 comandos. Los 186 patrones ES y 46 comandos coinciden exactamente
con DjangoAI. Este último usa backend dummy; ambos censos son metadatos, no
prueba de esquema aplicado, peticiones, permisos o ejecución de CLI/tareas.
Django 5.2.17 y sólo auth.group, con CurrentGroupAdmin actual.

641 fuentes congeladas estables y 422 huellas del censo. Frente al JSON del25:
344 conservadas, 40 modificadas y 38 con cobertura añadida al inventario; esta
última categoría no demuestra creación de archivo. Las fuentes directas de las
443 unidades originales siguen coincidiendo con N11, sin prometer equivalencia
transitiva o PASS íntegro de cada unidad. Los 170 handlers quedaron localizados
en sus líneas actuales.

## Revisión e incidencias

Una revisión nativa detectó dos P2 documentales: límites Admin que no acotaban
«no ejecutado» a este inventario e I09 sin relación actual con N10 para el nuevo
receptor. Root contrastó y corrigió ambos, conservando límites/bloques históricos
en campos separados. La revisión del mismo patrón en las demás familias separa
asignación primaria de referencias por unidad: estas últimas incluyen los
diferimientos, sin atribuir aceptación global por bloque. También se recalcularon referencias URL de plantillas,
localizadores de autoridad y alcance de los comandos registrados. La candidata
final pasó la comprobación independiente de correspondencia e identidades.

Dos primeros ensamblados se detuvieron por adaptar como strings una lista de
objetos de autoridad y por asumir que existía core.admin en GitN00. No se tocó
app ni censo original; se preservan ambos errores de instrumentos y la propuesta
revisada. El código del censo nuevo reconoce decoradores receiver además de
connect. No se repitieron el AST de producto, el resolver ni ninguna QA válida.

El JSON original del25 y111 permanecen intactos. Los Markdown338/339 anteriores
se recuperan desde Git `9a32f5e`. Las cinco obligaciones de cierre de N15 se registran
como controles de ingeniería separados, sin inflar las 444 unidades de producto.

## Continuación

N15 todavía no está aceptado: 11/13 bloques obligatorios. Sigue la entrega final
de frontend, conciliación semántica/documental, acta/Git, resumen externo y purga
completa de artifacts como última operación. Los insumos estáticos de formularios,
guardas y HTTP no acreditan ejecución de frontend ni de todas las ramas.

Se conserva [deuda viva](deuda-pendiente-viva.md): N02/MOD09 al final del desarrollo,
N12/B14, N13/B15 y N14/B17 condicionados y QA general hasta estable. Alpha/noindex;
ningún proveedor, apertura, migración, servicio o CI nuevo.
