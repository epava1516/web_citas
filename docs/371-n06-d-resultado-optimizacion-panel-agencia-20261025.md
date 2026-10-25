# N06D — corrección del crecimiento del panel de agencia

25 de octubre de 2026. Se acepta localmente la corrección acotada de apps/core/agencies.py::panel: los miembros activos del propietario cargan su usuario en la misma consulta mediante select_related("user"). Antes, la plantilla pedía cada member.user.email por separado. No cambian filtros, permisos, esquema, plantilla ni orden declarado. N06sigue abierto; esta aceptación corresponde al lote, no al bloque completo.

[Prerregistro370](370-n06-d-prerregistro-crecimiento-panel-agencia-20261025.md). Referencia20261025-155652-ba0c1f34:6PASS. Candidata20261025-160002-750b9431:6PASS. Validación existente20261025-160202-58da5277:3PASS. Sin FAIL/ERROR/SKIP funcionales. Son seis casos repetidos antes/después y tres casos adicionales, no quince casos distintos. El único cambio de fuente runtime entre mediciones es agencies.py; instrumento y datos idénticos. Fuentes/imagen/nativo/afinidad verificados en la [auditoría](evidencias/n06-d-panel-auditoria-comparacion-20261025.json).

## Tabla antes/después: propietario

Mediana de cinco observaciones posteriores por cohorte/idioma; primera llamada separada en evidencia. Cada pasada mide72peticiones, seis por actor/cohorte/idioma, con propietario y editor separados. Tiempos de la misma petición Client instrumentada, no QA ni p95.

| Editores activos | Idioma | Consultas antes → después | Tiempo antes (ms) | Tiempo después (ms) | Diferencia (ms) | Reducción observada |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | EN | 9 → 8 | 22.742 | 16.915 | -5.827 | 25.62% |
| 1 | ES | 9 → 8 | 15.539 | 13.539 | -1.999 | 12.87% |
| 10 | EN | 18 → 8 | 43.430 | 16.901 | -26.529 | 61.08% |
| 10 | ES | 18 → 8 | 41.634 | 22.321 | -19.313 | 46.39% |
| 100 | EN | 108 → 8 | 225.516 | 46.849 | -178.667 | 79.23% |
| 100 | ES | 108 → 8 | 279.575 | 54.110 | -225.466 | 80.65% |

Con100editores son100consultas menos por petición, reducción92,59%del total108→8. El coste SQL del propietario deja de crecer por una carga de usuario por editor en las cohortes medidas. No se extrapola a cardinalidades mayores, capacidad de producción ni otros estados.

El editor mantiene7consultas en todas las cohortes y ambos idiomas. Su camino no cambia y también presenta variación temporal entre pasadas: no se atribuyen sus diferencias al candidato. Las12medianas de pared no empeoran en esta muestra, pero el orden referencia→candidata y el entorno compartido limitan la atribución causal de cada porcentaje temporal. La reducción determinista de consultas sí queda contrastada con el único cambio de aplicación. Primera/rangos/CPU/tiempo SQL/bytes se conservan sin sumar unidades distintas.

CPU del propietario con100editores:199,982→41,792ms enES y151,228→36,306ms enEN (medianas posteriores). No se mide pico de memoria por petición ni se afirma reducción de memoria. Materializa los mismos miembros/usuarios que antes; se mantienen tamaños y oráculos, sin ocultar mayor población mediante límites/paginación nuevos.

## Corrección, pruebas y límites

Las144peticiones medidas antes/después conservan conjuntos, orden observado de personas/miembros y tamaño de respuesta en cada muestra emparejada. Se comprueban todos los emails activos para propietario, exclusión del miembro inactivo y agencia/persona ajena, sólo primera persona asignada para editor, lista de miembros oculta para éste, externo403/anónimo302 y editor403al perder membresía mientras el propietario conserva200. No se comparan cuerpos íntegros byte a byte entre fixtures con UUID/CSRF nuevos; se verifican los contenidos y las proyecciones declaradas.

Además pasan el caso existente de dos perfiles/alcance de editor/revocación y los dos casos de navegador de configuración de agencia con privacidad de membresía ES/EN. Son navegador real local y datos sintéticos, sin afirmar verificación externa/proveedor real ni medir latencia de navegador. PostgreSQL17/Redis7.4 propios, dependencias bloqueadas y herramientas nativas fijadas; sin carga paralela ni cuotas dedicadas. Las1736huellas se conservan durante cada ejecución/auditoría. Cero recursos propios tras consulta independiente, temporales retirados y recibos terminalesTelegram sent en las tres ejecuciones. LintF811 inicial del instrumento corregido conusefixtures; aviso inicial y posterior conservados, sin fallo funcional encubierto.

Duración QA separada, JUnit:referencia55,156s; candidata53,520s; verificación adicional54,381s. No se presentan esos1,636sde diferencia de batería como ahorro de la aplicación ni optimización general deQA.

## Grafo, reproducción y continuidad

[Reproducción](evidencias/n06-d-panel-reproduccion-20261025.tar.gz), [grafo congelado de candidata](evidencias/n06-d-panel-candidata-grafo-20261025.tar.gz). Refresco semántico focal previo de369/seguimiento y370, más AST del instrumento. Tras el cambio se reextrajo agencies.py:25nodos/64relaciones idénticos; el extractor no representa la cadena select_related añadida. Se actualizó la identidad exacta de fuente y se verificó el diff de una línea/AST del resto del módulo; no se declara reconstrucción semántica completa ni evidencia de ejecución por el grafo. Las mediciones aportan la prueba de consultas/tiempos. Base estructural y multirrelaciones anteriores preservadas.

N00/N01siguen aceptados2/13sin límite; N06con lotesA–Dverificados en su ámbito y conciliación de cuenta/panel/edición/representación pendiente antes de cerrar el bloque. El siguiente paso es conciliar acciones/variantes y sus evidencias, para seleccionar sólo los huecos restantes. N02restante sigue diferido al final del desarrollo por instrucción del usuario367; no repetir esa batería ni abrir beta. Alfa, sin nuevos proveedores ni publicación.
