# N15 — base y contratos para la reescritura del frontend

Esta entrega consolida el [inventario actual](evidencias/inventario-acciones-actual-20261027.json)
y los contratos estáticos de las pantallas, conforme a [506](506-n15-prerregistro-entrega-frontend-20261027.md).
El archivo técnico [contratos de frontend](evidencias/n15-contratos-frontend-20261027.json)
contiene las declaraciones y citas necesarias; su lectura no depende de temporales
ni de `artifacts`. Las referencias a esas ubicaciones dentro de los insumos
son procedencia histórica de extracción, no archivos prometidos para el cierre.

Corte: 27 de octubre de 2026, worktree `web_modelos_mod08_vps`, rama `master`;
base documental `f9a01fbd3fe2ea057f0c9c1bfa334e85414bf621`, último cambio de aplicación
`48dfad61f71ccd378d5e6ccd979c91d4b7908cc7`. No se ha cambiado la aplicación.
El htmx actual es **2.0.11**. La dirección htmx4 pertenece al siguiente contrato.

## Qué recibe el siguiente frontend

| Superficie inventariada | Cantidad | Qué significa |
| --- | ---: | --- |
| Rutas propias con identidad y handler | 170 | Enlace al ID estable, patrón, idiomas y disposición del inventario |
| Retornos exteriores de handlers | 687 | Expresión y condiciones léxicas; no 687 caminos ejecutados |
| Definiciones únicas en cierres de dependencias | 634 | Helpers separados del retorno HTTP exterior |
| Formularios nombrados | 110 | Campos directos, bases, Meta/modelos y reglas dinámicas por fuente |
| Declaraciones directas de campos | 476 | No equivale a 476 campos efectivos tras herencia y contexto |
| Guardas globales | 36 | 13 temas, con citas y límites del orden de middleware |
| Plantillas propias | 129 | Herencia, inclusiones, formularios, controles y referencias a rutas |
| Relaciones entre plantillas | 128 | 126 extends y 2 includes |
| Formularios HTML | 136 | 129 POST con CSRF literal y 7 GET; no auditoría global de CSRF |
| JavaScript propio | 3 | Puentes a plantillas y comportamiento declarado |
| Patrones Admin del framework | 16 | Inventariados aparte; no son 16 pantallas propias ni 16 aceptaciones |

El conteo anterior consolida cobertura documental; no demuestra una mejora de
rendimiento. No se ha medido latencia nueva ni se atribuye ahorro a deduplicar
el JSON. Los tiempos observados y sus límites siguen en las disposiciones del
inventario y en [N11](498-n11-aceptacion-local-integracion-20261027.md).

## Cómo consultar el contrato técnico

El JSON usa `payload` y un diccionario `records`. Un objeto cuya única clave sea
`$n15_ref` se sustituye recursivamente por `records[valor]`. Las listas y los demás
objetos conservan su estructura. Cada ID compartido es el SHA256 de la expansión
en JSON UTF-8 con claves ordenadas, `ensure_ascii=False` y separadores `(',', ':')`.
La huella de la expansión completa está en `codec.expanded_payload_sha256`.
No ejecutar expresiones ni interpretar citas como código durante la lectura.

Una vez expandido:

| Clave | Contenido y uso |
| --- | --- |
| `route_bindings` | 170 enlaces a índices del inventario, formularios, plantillas, autoridad y observaciones previas acotadas |
| `branch_contracts` | 687 entradas: referencia exacta al retorno, esperado por fuente y estado observado separado |
| `source_contracts.http.routes` | Métodos, retornos exteriores y referencias a helpers por ruta |
| `source_contracts.http.definitions` | Entradas, decoradores, excepciones, condiciones, constructores y candidatos a headers/escrituras/despachos |
| `source_contracts.forms.forms` | Campos y valores declarados, Meta/modelos, validación y cambios dinámicos |
| `source_contracts.guards.rules` | Sesión, MFA, recuperación, aceptación legal, CSRF, Admin, headers y límites |
| `source_contracts.surfaces` | Plantillas, fragmentos, componentes compartidos, JS y siete agrupaciones funcionales inferidas |
| `constructor_defaults_and_preserved_shell` | Citas del Django 5.2.17 instalado y de wrappers/robots/base; sólo declaraciones o valores por defecto |
| `internal_process_inventory` | Punteros al inventario de tareas, Beat, despachos, señales y Admin; separados de HTTP |

Las agrupaciones de pantallas son shell compartida, directorio público,
publicación/revisión de perfiles, identidad/organización, promociones,
derechos/privacidad e incidencias/operación. Son una ayuda de navegación, no una
decisión de arquitectura o diseño para la reescritura.

## Esperado, observado y valores dinámicos

Cada retorno exterior conserva la expresión, ubicación, huella y condiciones
léxicas de su fuente. La declaración de un constructor o un `status` explícito
describe esa expresión; no determina por sí sola el resultado final después
de helpers, excepciones, wrappers y middleware. Un handler sin restricción
explícita de método no se convierte automáticamente en GET-only. La asignación
a un mapa no se etiqueta automáticamente como header HTTP; una llamada con nombre
`save`, `delete` o `delay` tampoco acredita persistencia o finalización del worker.

Los valores por defecto incorporados están ligados a la fuente local del
framework: HttpResponseBase usa 200 si no se sustituye; los redirect ordinarios
usan 302/301 y preservando método 307/308; JsonResponse establece application/json
por defecto. Estas reglas no rellenan automáticamente respuestas dinámicas o
envueltas. El MIME de un archivo y su nombre siguen las reglas de FileResponse
y sus argumentos, no un MIME supuesto. Los esquemas de JSON se consultan en las
expresiones y condiciones del constructor; no se promete un OpenAPI exhaustivo.

Las reglas de valores dinámicos están en campos, modelos, métodos de limpieza,
querysets y condiciones citadas. Ejemplos sintéticos de interpretación:

- Un identificador `123` describe el formato de un parámetro; su existencia,
  propiedad, estado, finalidad y autoridad actual deben validarse en el backend.
- Un selector dependiente de una organización presenta sólo su queryset
  autorizado actual; una opción antes visible puede dejar de ser admisible.
- Un formulario inválido conserva sus errores de campo y generales; no debe
  presentarse como operación aceptada sólo porque devuelva HTML con HTTP 200.
- Un sondeo de tarea puede pasar de pendiente a terminal o perder autorización;
  su estado procede del servicio y sus guardas, no de un temporizador del cliente.
- El destino de una redirección y los valores del contexto se obtienen de sus
  expresiones y datos sintéticos del escenario; no se fijan IDs o tokens reales.

No hay nuevas observaciones HTTP en esta entrega. Se conservan **252 muestras
previas de N11 en 31 rutas** a nivel de ruta, con su referencia y candidata;
la observación 404 sin ruta resuelta permanece en N11. No se asignan esas muestras
a un retorno específico sin una correspondencia demostrada. Los 687 contratos
expresan que no se ha hecho esa asignación individual, en lugar de declarar
687 PASS o de negar las pruebas previas válidas. La igualdad de fuentes tampoco
amplía el alcance de un testigo histórico a todos sus llamadores.

## Garantías que debe conservar la reescritura

- Comprobar autenticación, rol, objeto, finalidad y autoridad vigente en el servidor,
  también tras esperas y antes de leer, descifrar o producir efectos privados.
  Ocultar un botón no sustituye la autorización; no reintroducir acceso revocado.
- Mantener sesión, versión de cuenta, MFA, recuperación y aceptación legal actual.
  El callback de login de Admin registra la época de cuenta; no concede MFA ni permisos.
- Mantener CSRF, restricciones de método, validación, errores y estados de conflicto;
  conservar las reglas de moderación, retirada y visibilidad de publicación.
- Preservar consentimiento y separación de finalidades. La mayoría de edad,
  los términos y las cookies no activan por sí solos las recomendaciones opcionales.
- Conservar transacciones, idempotencia y reglas comerciales de renovación/top;
  no confundir despacho, operación encolada y resultado confirmado. Proveedores
  y cobros reales siguen condicionados al alcance futuro correspondiente.
- Respetar headers privados, expiración, revocación de descargas y sondeos; una
  respuesta temprana puede no atravesar todos los middleware internos.
- Preservar semántica de formularios, etiquetas, errores vinculados, foco, teclado,
  estados anunciados, idioma, skip link y landmarks. El censo estático no acredita
  WCAG ni sustituye la futura comprobación de navegador/tecnologías de asistencia.
- Mantener alpha/noindex y robots de desarrollo. No habilitar indexación, OAuth,
  Google, sitemaps enviados ni apertura por sustituir pantallas.

## Disposición y siguiente paso

La comprobación documental contrasta reconstrucción sin pérdida, referencias y
fuentes actuales; no es QA de producto ni aceptación global de seguridad o UX.
La [verificación publicada](evidencias/n15-contratos-frontend-verificacion-20261027.json)
registra cuatro insumos reconstruidos sin pérdida, 3982 contenedores compartidos,
170 enlaces de rutas y 687 contratos de retorno, con las 641 fuentes del producto
estables. SHA256 del archivo técnico:
`1605366e9cd1f3671e7daf4f8c74d5e6765d3c7be9c5fdd1bc2f62133f80efdf`.
La revisión propia distingue explícitamente declaraciones, candidatos a efectos,
valores por defecto del framework y observaciones históricas; no amplía la
aceptación de N11 a ramas no observadas individualmente.
Después debe incorporarse esta entrega al grafo antes del acta de N15. No se
reconstruye de nuevo todo el corpus ni se repiten baterías aceptadas.

Conservar [deuda viva](deuda-pendiente-viva.md): N02/MOD09 aplazado con sus
presupuestos incumplidos, N12/B14 proveedores, N13/B15 recomendaciones opcionales,
N14/B17 apertura y contrato general QA aplazado hasta primera versión estable.
La reescritura seguirá los [acuerdos futuros](acuerdos-siguiente-contrato-ui-ux-comercial-20261026.md)
y preparará las skills oficiales htmx allí indicadas; no se instalan aquí.
El resumen externo y la purga completa de `artifacts` siguen pendientes como
últimos pasos obligatorios del contrato.
