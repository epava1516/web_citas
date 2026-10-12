# Salón local de deliberación

Sala de revisión por turnos entre Codex, Claude y NotebookLM, coordinada mediante
[deliberation_room.py](../scripts/deliberation_room.py). El historial común está en
[la primera sala MOD08](../.ai/rooms/mod08-20261011/transcript.md).

Codex participa desde la sesión de trabajo y selecciona explícitamente el contexto que
reciben los revisores. Claude y NotebookLM se invocan mediante sus CLI instalados y sus
cuentas existentes. No se crea una cuenta, proveedor, suscripción ni servicio de alojamiento.
No es una conversación autónoma: el coordinador revisa cada respuesta antes de preparar
el siguiente turno y registra la decisión final.

## Autorización y alcance

El usuario autorizó el 2026-10-11 una excepción **sólo para deliberar**: Claude CLI como
revisor sin herramientas ni permiso de editar, manteniendo el registro de consumo.
El contrato externo y el adaptador oficial exigidos por AGENTS.md no se localizaron en
este equipo. La excepción no modifica esos archivos, habilita delegaciones escritoras
ni reanuda la capacidad completa de MOD08.

Claude se lanza con herramientas vacías, configuración MCP vacía estricta, modo seguro,
comandos de habilidades deshabilitados y sin persistencia de sesión propia. Recibe el
contexto por stdin; no necesita inspeccionar el repositorio. Las opiniones no ejecutan
código ni constituyen evidencia de aceptación. NotebookLM consulta el notebook existente
y sus fuentes; la sala no añade ni elimina fuentes.

## Uso

Desde la raíz del proyecto:

```sh
uv run python scripts/deliberation_room.py show mod08-20261011
uv run python scripts/deliberation_room.py init mod08-siguiente --title "Siguiente deliberación" --notebook-id bb1f4634-45b7-4f41-b807-4b8502614b9d
uv run python scripts/deliberation_room.py add mod08-siguiente --speaker codex --kind opinion --file /ruta/intervencion.txt
uv run python scripts/deliberation_room.py ask mod08-siguiente --speaker notebook --file /ruta/consulta.txt --timeout 180
```

Una sala nueva se crea con `init ID --title TITULO --notebook-id UUID`. Por defecto permite
cuatro solicitudes externas; el límite puede fijarse al crearla entre una y ocho. Cada sala
requiere registrar su autorización expresa antes de usar Claude mediante
`authorize-claude ID --file ARCHIVO`; ese comando registra una autorización recibida, no
la solicita ni la genera. No usarlo sin la instrucción correspondiente del usuario.

Codex comparte manualmente las respuestas pertinentes y sus objeciones al redactar la
siguiente consulta. NotebookLM reutiliza la conversación creada para la sala; Claude
recibe cada vez el contexto seleccionado. Se exige un cierre acotado: decisión, evidencia
faltante, experimento propuesto y criterio de abandono. Un acuerdo entre modelos no prueba
equivalencia, seguridad ni rendimiento.

`close ID --file DECISION` registra el cierre y bloquea nuevas solicitudes externas de esa
sala. Para otra deliberación se crea una sala nueva, conservando el historial anterior.

## Registro y límites

Cada sala conserva configuración, autorización, manifiesto de fuentes del contexto,
consultas, respuestas originales, stderr, eventos JSONL y una transcripción Markdown.
Los eventos distinguen contexto, solicitud, opinión, error y decisión. Las respuestas
externas se marcan `verified=false`.

El script no ingiere archivos automáticamente: el coordinador debe preparar un contexto
sin secretos ni datos reales. Su límite local de consulta es 12000 caracteres; no representa
un límite publicado de NotebookLM. Las llamadas tienen timeout y, si se interrumpen, se
termina su grupo de procesos local. No hay retries automáticos; una solicitud fallida
consume un turno de la sala. El bloqueo de archivo serializa las escrituras e invocaciones.

Todas las invocaciones de Claude se registran en
[el consumo histórico](../.ai/tasks/desarrollo.md), conservando lo anterior. Tokens,
modelos y coste se guardan cuando el CLI los declara; una cifra `total_cost_usd` no es
una factura ni demuestra un cargo adicional en la suscripción. Ausencias se registran
como desconocidas, sin estimaciones. El CLI de NotebookLM no identifica el modelo usado.

Los tests de controles usan dobles de los servicios; no acreditan la conexión a modelos.
Las intervenciones reales de la primera sala permiten verificar esas conexiones por
separado. Esta herramienta no modifica la aplicación ni requiere integración PostgreSQL.

La campaña diagnóstica posterior propuesta en la sala está
[terminada y documentada](evidencias/mod08-scalar-consumers-20261011.md). Sus resultados
se añaden como contexto de Codex al historial; no son nuevas opiniones de Claude o
NotebookLM ni reabren las solicitudes externas de la sala cerrada.

La [segunda deliberación](evidencias/mod08-siguiente-plan-20261011.md) fija un bloque
de estabilidad de veinte controles como siguiente paso; todavía no ejecutado.


### Investigación web autorizada — 2026-10-11

El usuario pide expresamente «que cada uno busque en internet soluciones para hacer un brainstorming». Esta instrucción posterior amplía sólo la deliberación a investigación pública. Claude sigue sin herramientas locales ni edición: una sala nueva registra `authorize-claude --web-research` con la instrucción recibida y cada llamada requiere `ask --web-research`. Se habilitan exclusivamente WebSearch/WebFetch, MCP vacío, safe-mode y permisos dontAsk; la vía predeterminada continúa sin herramientas. NotebookLM puede usar `nlm research start --source web` sin auto-importar resultados. Codex contrasta documentación primaria por separado. Las fuentes encontradas y propuestas siguen siendo hipótesis y se registran; ningún acuerdo acredita seguridad o rendimiento.
