# Skills Celery y migraciones para Codex

Instalación solicitada por el usuario,26deoctubrede2026,02:23CEST. Canal único Agent Skills de Vinta:

```bash
npx skills add vintasoftware/django-ai-plugins --skill django-celery-expert django-safe-migration --agent codex --global --yes
```

Comando terminado con código0. Ambas copiadas en `~/.agents/skills/` y enumeradas por `npx skills list --global --agent codex --json`. No se instalaron otras skills, plugins ni MCP en esta tarea.

| Skill | Archivos | Referencias explícitas presentes | Huella de carpeta del instalador |
| --- | --- | --- | --- |
| django-celery-expert | 8 | 7 de7 | a08d49e740779ab2a2fe48ff27978ddbfa7897d4 |
| django-safe-migration | 4 | 3 de3 | 7e3b61fb93f0a8cce272ad2fe77622a9d9708d92 |

Procedencia registrada en `~/.agents/.skill-lock.json`: repositorio vintasoftware/django-ai-plugins, directorios canónicos skills/django-celery-expert y skills/django-safe-migration. Las huellas de carpeta no se presentan como commits Git. SHA256 de SKILL.md: Celery `091f6d9928cb0fcf39707d70c5bb2c3695684b94aa2ae2e9accd25661321bbb9`; migraciones `565a359f9d64cb5c9ea626c942afdae3c743143297d1eb4070bd9b5099212170`.

El instalador informó dos alertas Socket para django-celery-expert, sin detalle en su salida; sus otros indicadores fueron Gen Safe y Snyk Low Risk. No se interpreta ese resumen como auditoría de seguridad completa ni se ejecutan scripts de la skill para verificar la instalación.

AGENTS.md configura activación pertinente, alcance y límites; Django5.2 según pyproject.toml, estrategia de despliegue pendiente y guard de migraciones no verificado. No se ejecutaron tareas Celery, pruebas de aplicación, generación/aplicación de migraciones ni conexiones/modificaciones de base. Verificación estructural y detección por el instalador, no aceptación funcional del contrato.

Disponibles para invocación explícita `$django-celery-expert` y `$django-safe-migration` desde el siguiente turno; reiniciar Codex si no aparecen. Usar las [instrucciones oficiales de ciclo de vida](https://github.com/vintasoftware/django-ai-plugins/blob/main/docs/installation.md), manteniendo un único canal por ID.
