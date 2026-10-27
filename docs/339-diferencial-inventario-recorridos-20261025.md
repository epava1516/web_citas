# Diferencial del inventario de recorridos — 27 de octubre de 2026

Resultado actual: [inventario 338](338-inventario-acciones-recorridos-alpha-20261025.md),
[censo actual](evidencias/inventario-acciones-actual-20261027.json) y
[verificación](evidencias/inventario-acciones-verificacion-20261027.json).
Este diferencial corresponde al contrato 340 y sigue al [grafo 503](503-n15-grafo-total-reconstruido-y-verificado-20261027.md).

La [base 111](111-inventario-rendimiento-recorridos-beta-20261020.md) conserva SHA256
`380b026c51b5e9647052838bb77a0712e9efff4ccdd857b5df3d4b545d921a95`.
El [JSON del 25](evidencias/inventario-acciones-final-20261025.json) se mantiene
intacto, SHA256 `b958f8a9a257bfb3baac7bcf18952d0b688f7f26b93c9af255796b3065b21f4f`.
La comparación antigua 111→338 se conserva en prior_111_delta y Git `9a32f5e`;
no se hace pasar por una medida nueva.

## Antes y después del contrato actual

| Unidad | Antes 338 | DespuésN15 | Diferencia acreditada |
| --- | --- | --- | --- |
| Familias I01–I28 | 28 | 28 | Identidad conservada |
| Unidades con ID | 443 | 444 | 443 conservadas;1 alta;0 bajas |
| Rutas propias nombradas | 170 | 170 | Conjuntos y declaraciones conservados; implementaciones no necesariamente |
| shared_task | 27 | 27 | Identidades conservadas; servicios transitivos separados |
| Comandos propios/framework | 15/31 | 15/31 | Mismos 46 registros; no ejecución nueva |
| Patrones Admin canónicos | 16 | 16 | CurrentGroupAdmin propio añadido; mismas superficies |
| Patrones distintos ES/EN/comunes | 366 | 366 | 372 filas, seis duplicadas por rutas comunes |
| Beat / lugares async-commit | 25/14 | 25/14 | Unidades y cadencias distintas de tareas ejecutadas |
| Inscripciones de señal propias | 1 | 2 | Bucle original 3 eventos + receptor user_logged_in |
| Plantillas / interactivas / JS | 129/106/3 | 129/106/3 | Fuentes de presentación, no aceptación browser |
| Valores de controles asociados | 154 | 154 | No 154 acciones ni combinaciones válidas |

No se midió mejora nueva de rendimiento de la aplicación en esta fase documental.
Los tiempos del antes/después de cada optimización permanecen en los testigos
aceptados por N11; no se sustituye latencia de app por duración de QA o censo.
MOD09 mantiene sus objetivos 2 s/5 s y FAIL/diferimiento 367. Los cambios de fuente
no se traducen automáticamente en ganancias o pérdidas de rendimiento.

## Identidades y alta acreditada

443 IDs originales conservados literalmente, incluso los que incluyen líneas
históricas. Los 14 despachos se emparejan por archivo/expresión/dispatcher, no se
renumeran por su nueva posición. Los punteros actuales son localizadores,
no sustitutos del ID. La inscripción original signal_connection:0 pasa a la
posición 1 y conserva identidad; los 170 handlers se localizaron en sus líneas
actuales y cada una de las 444 unidades tiene correspondencia única.

Alta: `signal_connection:user_logged_in:apps.core.admin.bind_admin_login_epoch`.
core.admin no existía en N00/`5118a055`; el módulo y receptor se implementaron en N10.
Sólo POST del login nativo de Admin inicializa account_version a session_version;
no otorga MFA ni permisos. Fuente SHA actual coincide con el testigo N10 de login,
con disposición local 491. Inventariarlo ahora no exige repetir ese testigo ni
convierte sus ramas no medidas en PASS. I09 conserva N06 original y añade N10;
I28 conserva su relación operativa. No se crean familias I29 ni URL/tareas nuevas.

Se separan el registro global delete_selected y el override de Group. Su presencia
no prueba disponibilidad para cualquier petición. Los límites heredados de Admin
se acotan a «este inventario no ejecuta CRUD», preservando las pruebas N10 previas.

## Fuentes, evidencia y límites

| Comparación de 422 huellas inventariadas | Cantidad |
| --- | --- |
| new_inventory_coverage_file_creation_not_implied | 38 |
| conserved | 344 |
| modified | 40 |

«Nueva cobertura de inventario» no significa que se haya creado el archivo. El
módulo Admin sí tiene prueba independiente de ausencia en GitN00. Modificar un
archivo tampoco prueba que todas sus funciones cambiasen. Las 422 huellas incluyen
fuentes propias, operativas y framework; no son 422 funcionalidades.

Las fuentes directas de las 443 unidades originales coinciden con las conciliadas
por N11. Eso permite conservar sus disposiciones y límites, no declarar igualdad
transitiva o PASS íntegro por función. Las 31 rutas con muestras N11D sólo conservan
sus ejemplos/casos; los métodos, roles, estados, headers y contenidos no observados
siguen sin acreditarse por compartir nombre o código HTTP.

La comprobación nueva es estructural: AST, resolver sin conexiones, metadatosMCP,
huellas, IDs y revisión. Cero nuevas peticiones/consultas de base, CLIhandle o tareas.
Las omisiones, FAIL, errores de instrumento e INVALID de los testigos anteriores
no se borran ni se suman como una única batería verde.

## Roadmap y deuda

11/13 bloques obligatorios aceptados por 498; N15 todavía activo. No renombrar
el cierre local como ausencia de trabajo del proyecto. [Deuda viva](deuda-pendiente-viva.md):
N02/MOD09 al final del desarrollo, N12/B14 proveedores condicionados, N13/B15
recomendaciones opcionales con contrato de datos separado y N14/B17 apertura futura;
QA general hasta primera estable/productiva. Alpha/noindex y no apertura.

El siguiente entregable técnico es el relevo frontend. Después se conciliarán sus
metadatos y este inventario con el grafo antes del acta. El resumen externo y la
purga total de artifacts cierran la operación: su estado pendiente en este corte
no autoriza omitirla ni afirmar ejecución anticipada.
