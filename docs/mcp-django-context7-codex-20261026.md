# Django AI Boost y Context7 en Codex

Instalación autorizada por el usuario el26deoctubrede2026. Ambos registrados globalmente en Codex; no se alteró el entorno Python del proyecto, sus dependencias, base de datos ni ejecución del contrato.

## Django AI Boost

Fuente: [repositorio oficial de Vinta](https://github.com/vintasoftware/django-ai-boost). Instalado django-ai-boost0.9.0 y Django5.2.17 (misma versión observada del proyecto) en el entorno independiente `/home/felidae/.local/share/django-ai-boost-codex/.venv`, Python3.12.15. Dependencias de soporte accesibles desde el site-packages existente del proyecto, sin modificarlo. No usar este entorno para ejecutar la aplicación o sus pruebas.

Registro Codex `django-ai-boost`, stdio, comando de ese entorno y launcher `/home/felidae/.local/share/django-ai-boost-codex/launch.py`. El launcher fija el worktree `/home/felidae/proyectos/web_modelos_mod08_vps`, elimina del entorno heredado credenciales y destinos de servicios y carga `inspection_settings.py`, externo al repositorio. Ese módulo deriva la configuración de desarrollo del código actual, reemplaza DATABASES por backend dummy, caché por memoria local, correo por dummy y logging por configuración sin archivos; utiliza un secreto sintético de inspección. No carga el archivo .env de la aplicación. No representa la configuración efectiva de una instancia desplegada.

Herramientas permitidas en `~/.codex/config.toml`: `application_info`, `list_models`, `list_urls`, `list_management_commands` y `reverse_url`. El servidor anuncia12herramientas, pero Codex sólo expone esas cinco. Quedan fuera lectura arbitraria de settings, logs, consultas de objetos, esquema físico, estado aplicado de migraciones y checks. El backend dummy impide conectar a la base existente desde este perfil. La restricción de herramientas es del cliente, no una modificación del paquete upstream.

Verificación: handshake initialize y tools/list sin errores; application_info respondió Django5.2.17,166modelos y database_engine dummy. La versión3.4.11 anunciada en serverInfo es la de FastMCP del entorno, no la versión del paquete django-ai-boost0.9.0. Proceso temporal de inspección terminado al finalizar. No se ejecutó SQL, migraciones, checks ni tareas Celery. La inspección de metadatos no prueba esquema real, migraciones aplicadas ni compatibilidad funcional completa.

El intento redundante de crear el entorno ya existente se rechazó sin borrarlo; la instalación del paquete posterior terminó correctamente. No se utilizó --clear ni se sustituyó el entorno de la aplicación.

## Context7

Fuente: [repositorio oficial de Upstash](https://github.com/upstash/context7). Registrado con `codex mcp add context7 --url https://mcp.context7.com/mcp`, transporte streamable HTTP. No se creó cuenta ni se añadió API key. El registro propuso OAuth; se interrumpió ese flujo y se comprobó que el acceso anónimo permite las operaciones verificadas.

Verificación HTTP: initialize200 con servidor Context7 versión4.4.3; tools/list disponible; resolve-library-id resolvió una consulta genérica sobre Django5.2 y select_related al ID `/websites/djangoproject_en_5_2`. No se envió código, datos, credenciales ni información privada del proyecto. No se garantiza disponibilidad ilimitada: límites o autenticación futuros deberán registrarse sin inventar acceso.

## Uso y disponibilidad

Consultar Context7 con nombre y versión detectados; validar procedencia y correspondencia de documentación. No transmitir contenido privado en consultas. Usar Django AI Boost para metadatos del proyecto, PostgreSQL MCP sólo con su destino y rol de lectura autorizados y graphify para relaciones documentales/estructurales. Ninguno sustituye evidencia real de pruebas o habilita cambios de alcance.

Ambos figuran habilitados en codex mcp get. Sus herramientas deben cargarse en un turno nuevo; reiniciar Codex si el catálogo no se actualiza. La verificación de protocolo directa no equivale a una invocación desde el catálogo ya cargado de esta conversación.
