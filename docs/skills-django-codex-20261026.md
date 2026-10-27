# Skills Django instaladas para Codex

Instalación realizada el26deoctubrede2026 a las02:17CEST (00:17UTC), a petición expresa del usuario. Canal único: Agent Skills mediante el CLI `skills`, siguiendo la sección «Skills.sh and generic Agent Skills» de las [instrucciones oficiales de Vinta](https://github.com/vintasoftware/django-ai-plugins/blob/main/docs/installation.md). No se instaló además el marketplace nativo.

```bash
npx skills add vintasoftware/django-ai-plugins --skill django-expert django-reviewer --agent codex --global --yes
```

El comando terminó con código0 e informó de ambas instalaciones. Alcance global del usuario, disponible para este proyecto y otros proyectos Codex; no se instalaron dependencias Django ni se cambió la aplicación.

| Skill | Directorio | Archivos | Huella de carpeta registrada por el instalador |
| --- | --- | --- | --- |
| django-expert | /home/felidae/.agents/skills/django-expert | 10 | 9dd32c96bf5b717de9efdb17d96467dd13635f0c |
| django-reviewer | /home/felidae/.agents/skills/django-reviewer | 1 | d9c0d469f696986b94d9061aad547520959f9f4e |

Procedencia registrada en `~/.agents/.skill-lock.json`: `vintasoftware/django-ai-plugins`, rutas canónicas `skills/django-expert/SKILL.md` y `skills/django-reviewer/SKILL.md`. Las huellas anteriores identifican carpetas del instalador, no un commit Git.

## Comprobaciones de instalación

- `npx skills list --global --agent codex --json` enumera ambas skills con agente Codex y sus rutas.
- Ambos `SKILL.md` son legibles y contienen el nombre esperado y descripción. Se leyeron sus instrucciones.
- Las ocho referencias Markdown explícitas de django-expert existen; django-reviewer no declara referencias externas de ese tipo.
- SHA256 de `django-expert/SKILL.md`: `a4919acb26157e182b2d5da524f85efa8c837eaeff3596cbeadf8ec6b61702bb`.
- SHA256 de `django-reviewer/SKILL.md`: `b30bbcde32e1b359452b18367469a675eff4c794353a642ce4ac89b02b89f6d7`.

Esto acredita instalación, integridad estructural y detección por el instalador para Codex; no se ejecutó una tarea Django ni una revisión del contrato en curso para probarlas. La actualización del catálogo de skills de la sesión se comprobará en el siguiente turno; reiniciar Codex si no aparecen, según la [documentación oficial de descubrimiento](https://learn.chatgpt.com/docs/build-skills).

## Uso en el proyecto

La configuración de activación se añadió a `AGENTS.md` del worktree activo `/home/felidae/proyectos/web_modelos_mod08_vps`: django-expert para desarrollo/diagnóstico Django, django-reviewer después de cambios Django/Python o ante una revisión solicitada y siempre sobre un objetivo acotado. Se mantienen contratos, permisos, PostgreSQL real, datos sintéticos y notificaciones de pruebas del proyecto. La revisión informa por defecto; no autoriza ediciones ajenas a la tarea.

Invocación explícita: `$django-expert` o `$django-reviewer`. El descubrimiento implícito usa las descripciones de cada skill. No se necesita habilitar DRF, añadir MCP ni instalar las otras tres skills del repositorio para utilizarlas.

## Ciclo de vida

Seguir el mismo canal para actualizar o retirar, evitando duplicados. Consultar las instrucciones oficiales y la ayuda del CLI antes de futuras operaciones. Actualización global selectiva: `npx skills update django-expert django-reviewer --global --yes`. Retirada global selectiva: `npx skills remove django-expert django-reviewer --global --agent codex --yes`. Esas operaciones futuras no se han ejecutado ahora.
