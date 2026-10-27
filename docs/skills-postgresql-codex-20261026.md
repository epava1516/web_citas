# PostgreSQL Best Practices para Codex

Instalada el26deoctubrede2026,02:18CEST, por petición del usuario, mediante el canal de orientación sin plugin documentado por [Microsoft](https://github.com/microsoft/postgres-skills#install-skills-through-skillssh).

```bash
npx skills add microsoft/postgres-skills --skill postgresql-best-practices --full-depth --agent codex --global --yes
```

Resultado del instalador: código0, una skill seleccionada y copiada para Codex en `/home/felidae/.agents/skills/postgresql-best-practices`. No se instaló pg-graph, el plugin completo, postgres-mcp ni servicios Azure. Este canal instala sólo instrucciones y referencias.

## Verificación

`npx skills list --global --agent codex --json` enumera la skill con alcance global y agente Codex. Se leyó SKILL.md, se comprobó su nombre y se encontraron24archivos, incluidas las23referencias Markdown enlazadas, sin ausencias.

Procedencia del registro `~/.agents/.skill-lock.json`: `microsoft/postgres-skills`, ruta `plugin/skills/postgresql-best-practices/SKILL.md`; huella de carpeta del instalador `a9a77c19907312334882fb848b2be4c6e82edf00` (no se presenta como commit Git). SHA256 de SKILL.md: `faca27246ea704342ad2dbf9001ca131e6fd1cf93743bffd5591354972155528`.

La verificación acredita instalación estructural y detección por el CLI para Codex, no una ejecución de consultas ni una validación de la base. Disponible para invocación como `$postgresql-best-practices` en el siguiente turno; reiniciar Codex si no aparece en el catálogo.

## Configuración del proyecto

Se añadió a AGENTS.md del worktree activo `/home/felidae/proyectos/web_modelos_mod08_vps` el uso combinado con las skills Django: ORM, N+1, consultas eficientes, índices justificados, integridad referencial y migraciones seguras. Mantiene los contratos, autoridad y verificaciones existentes. Sin Azure por defecto ni conexión automática; si una operación necesita MCP ausente, registrar la limitación y no cambiar de destino.

No se ha conectado a PostgreSQL, ejecutado SQL, creado o aplicado migraciones ni modificado esquema, índices, datos o configuración de la base existente. No se han iniciado pruebas de la aplicación ni alterado la ejecución del contrato en curso.
