# PostgreSQL MCP registrado en Codex

Instalado a petición del usuario el26deoctubrede2026, siguiendo el [repositorio oficial de Microsoft](https://github.com/microsoft/postgres-mcp) y su [guía de uso](https://github.com/microsoft/postgres-mcp/blob/main/USAGE.md). Registro global de Codex: servidor `postgres`, transporte stdio, paquete `@microsoft/postgres-mcp@0.3.0`, Node22.22.2 existente. No se instaló el plugin completo ni servicios Azure.

Se ejecutó `codex mcp add postgres` con `/usr/bin/env` y PATH explícito de Node22 para lanzar `npx -y @microsoft/postgres-mcp@0.3.0 run --no-telemetry`. Entorno del servidor: `POSTGRES_MCP_DISABLE_CWD_ACCESS=1`, sin credenciales ni cadena de conexión. Configuración en `~/.codex/config.toml`.

En la configuración de Codex se bloquearon las herramientas `postgres_mcp_modify`, `postgres_mcp_bulk_load_csv`, `postgres_mcp_add_connection` y `postgres_mcp_remove_connection`. Esto limita las herramientas expuestas por este cliente; no convierte un rol PostgreSQL con escritura en uno de sólo lectura.

## Verificación y límites

`codex mcp get postgres` confirma registro habilitado y comando. Se lanzó temporalmente el servidor, respondió a `initialize` como postgres-mcp0.3.0 y devolvió13herramientas mediante `tools/list`, sin errores. Los filtros se conciliaron con los nombres reales anunciados. El proceso de inspección se terminó después de esas dos operaciones; no se llamó a ninguna herramienta de base de datos.

El primer intento de validar TOML con el Python del sistema no encontró tomllib y no escribió configuración; la validación y modificación se completaron con el Python del entorno del proyecto. No se cambiaron dependencias Python.

La conexión real queda pendiente: seleccionar un destino explícito y un perfil con `access_mode: ro`, respaldado por un rol de sólo lectura ya autorizado. No se creó ningún perfil ni rol, no se recuperaron credenciales ni se estableció conexión PostgreSQL. No se ejecutó SQL, migraciones ni cambios de esquema/datos. No se acredita todavía inspección del esquema real ni planes de consultas.

En un turno nuevo de Codex comprobar la disponibilidad de herramientas; reiniciar el cliente si no carga el servidor recién añadido. Utilizarlo junto con postgresql-best-practices y las skills Django respetando AGENTS.md, el alcance de la tarea y la minimización de datos. La instalación no autoriza conectar automáticamente a un destino descubierto ni ampliar privilegios.
