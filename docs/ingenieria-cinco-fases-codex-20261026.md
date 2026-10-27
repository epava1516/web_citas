# Preparación de las cinco fases de ingeniería — 26 de octubre de 2026

Autorizada en conversación lateral tras ampliar el alcance de dos a cinco fases. Instalación aislada y preparación; no ejecución del contrato principal ni acreditación de producto estable.

## Entrega y uso

Kit: `/home/felidae/.local/share/web-modelos-engineering-codex`.
Skill instalada: `/home/felidae/.codex/skills/web-modelos-engineering/SKILL.md`, invocable como `$web-modelos-engineering`. Mantiene selección implícita normal, circunscrita a este proyecto, y cinco referencias de carga selectiva. Archivo creado y validado; no afirmamos que el catálogo ya cargado de otro hilo lo haya incorporado. Si no aparece, leer su ruta explícitamente o refrescar la sesión. No modifica configuración MCP.

| Fase | Preparado e instalado | Integración pendiente |
| --- | --- | --- |
| 1 Calidad/accesibilidad | Hypothesis[django]6.170.11, factory_boy3.3.3, Playwright1.63.0, axe-core4.14.0 y adaptador4.14.0; pytest/Django aislados compatibles | Casos nuevos pertinentes mediante runner del proyecto; no sustitución ni repetición de QA existente |
| 2 Rendimiento | Lighthouse CI0.15.1 (Lighthouse12.6.1), Locust2.47.0, plantilla de informes locales; reutilización de perfiladores existentes | Instancia sintética, escenarios, presupuesto, carga y medición autorizados |
| 3 Arquitectura/dominio | Skill propia, referencia de contratos, invariantes y plantilla ADR | Decisiones reales y cambios de arquitectura/comercio, sin reorganización automática |
| 4 Operación | OpenTelemetry SDK1.45.1, instrumentaciones Django/Celery/psycopg0.66b1, Sentry SDK2.73.0, prometheus-client0.26.0; guía de release | Integración runtime, destino, redacción, retención y decisiones CI/CD/backup/rollback |
| 5 Crecimiento | BeautifulSoup4.15.0, Lighthouse reutilizado, plan propuesto de medición y guía SEO/capacidad | Eventos, privacidad, consentimiento, proveedor y validación futura; sin tracking activo |

Python3.12.15 y Django5.2.17, alineados con la aplicación observada. Node22.22.2 ya existente se usa por ruta explícita: axe4.14 exige Node>=22.12. No se cambia la versión global ni el shell del usuario. 64 paquetes Python instalados;335 paquetes npm. Dependencias fijadas mediante `uv.lock` y `package-lock.json`. npm se ejecutó con `--ignore-scripts --no-audit --no-fund --save-exact`; `.npmrc` conserva esa política y exige engine compatible.

Se descargó Chromium Headless Shell153.0.8010.12/revisión1243 y FFmpeg1011 exclusivamente en `browsers/` del kit; no se cambió la caché compartida de Playwright. El instalador usó fallback Ubuntu24.04 por no reconocer oficialmente la distribución anfitriona; el smoke local pasó, sin acreditar compatibilidad universal. No se instalaron dependencias del sistema.

## Evidencia y límites

`evidence/verification.json`: PASS_KIT_ONLY. Skill válida; Hypothesis y factory_boy sobre valores sintéticos; parser HTML; registro Prometheus aislado en memoria; versiones CLI de Lighthouse/Locust; Chromium real con documento sintético y red bloqueada: regla axe `label`, positivo sin violaciones y negativo sin etiqueta detectado. No acredita accesibilidad completa, WCAG, QA de app, carga, rendimiento, integración Django ni proveedores.

`uv pip check` comprobó64paquetes compatibles. No se invocó Django setup, base de datos, Celery, auto-instrumentación, Sentry init, exporter, scrape, tracking, Lighthouse contra sitio ni Locust contra destino alguno. Las instrumentaciones están instaladas, pero la integración y sus dependencias de runtime deben resolverse y validarse en el entorno objetivo autorizado.

Se conservaron fallos preparatorios: YAML inicial sin entrecomillar (corregido) y ausencia de la revisión1243 de Chromium (instalada aisladamente). Las comprobaciones fallidas y las finales llevan recibos Telegram en `evidence/notifications.json`; no se presentan los intentos fallidos como PASS. La validación final no repitió QA válida del producto.

npm avisó de dependencias transitivas obsoletas, entre ellas inflight, rimraf, glob y uuid. No se ejecutó auditoría de vulnerabilidades; estos avisos no acreditan una vulnerabilidad concreta ni seguridad del árbol. No se aplicaron overrides/actualizaciones forzadas a Lighthouse. La instalación no equivale a aceptación para producción.

## Lo existente se conserva

Proyecto con pytest9.1.1, pytest-django4.14.0, xdist3.8.0 y Playwright1.63.0 observados en su entorno, no sólo declarados. CI `.github/workflows/ci.yml` usa workflow_dispatch: no se ha convertido en gate automático de PR. Hay SEO, observabilidad y rollback previamente documentados; reutilizar sus estados vigentes, no reabrir bloques desde documentos históricos.

htmx observado2.0.11; htmx4 es dirección futura documentada. Esta preparación no migra frontend ni crea deuda nueva. El contrato general de optimización QA sigue aplazado según lo acordado.

Grafo consultado en modo lectura con vocabulario comprobado seo/observabilidad/rollback/contrato/pruebas/rendimiento y recorrido de un salto: `evidence/graph-context.json`. Corte SHA256 d5779c869c4fb96ca3b98f6f340371f5ab1bd35d62c66a9d26ff61b2c75f5928. No se reconstruyó ni se actualizó el grafo.

Playwright MCP, Chrome DevTools MCP, Context7 y las tres herramientas permitidas de Semgrep estaban expuestos en el catálogo de esta sesión; no se invocaron para acreditar conexión funcional ni se cambiaron sus registros. No confundir este catálogo con el de otro hilo.

No se instalaron/activaron servidores Prometheus/Grafana, Collector, Renovate, proveedor Sentry, analítica ni servicios: preparación documentada con decisiones pendientes, sin cuentas, tokens, contenedores, cron, workflows nuevos ni despliegue. Docker/CI existentes se reutilizarán cuando proceda. No hay nuevo compromiso de proveedor.

No se modificaron app, pyproject/uv.lock del proyecto, CI, AGENTS.md, seguimiento ni evidencias del contrato; sin commits ni push. El hilo principal trabaja en paralelo: la comparación puntual detectó cambios ajenos en complaints/complaint_actions/complaint_resolutions/privacy_release y se dejaron intactos. No se afirman inmutables los archivos que modifica ese hilo. La única adición al repositorio de esta tarea es el registro `docs/ingenieria-cinco-fases-codex-20261026.md`.

## Reconstitución y comprobación

Desde el kit, usar las rutas explícitas:

```bash
/home/felidae/.local/bin/uv sync --locked --project /home/felidae/.local/share/web-modelos-engineering-codex --no-install-project
PATH=/home/felidae/.nvm/versions/node/v22.22.2/bin:/usr/bin:/bin /home/felidae/.nvm/versions/node/v22.22.2/bin/npm ci --prefix /home/felidae/.local/share/web-modelos-engineering-codex --ignore-scripts --no-audit --no-fund
```

El entorno está aislado y no debe ejecutar la app. Para repetir sólo una comprobación justificada del kit, desde el worktree activo usar `scripts/run_notified.py` con su Python y ejecutar `.venv/bin/python -I -B verify.py` del kit. Registrar y comprobar el recibo; no repetir sólo por este documento. No ejecutar un `pytest` global desde aquí.

Los planes están en `plans/`: Lighthouse sin URLs por defecto y sólo salida filesystem, ADR sin decisión adoptada, medición comercial sin implementación y preparación de release. La configuración Lighthouse vacía no es una medición ejecutable hasta definir un destino explícito. El smoke no registra contenido, fotos, datos privados ni accesos de aplicación.

Fuentes oficiales consultadas:
- https://learn.chatgpt.com/docs/build-skills
- https://hypothesis.readthedocs.io/en/latest/extras.html
- https://playwright.dev/docs/accessibility-testing
- https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md
- https://docs.locust.io/en/stable/installation.html
- https://opentelemetry.io/docs/languages/python/instrumentation/
- https://docs.renovatebot.com/getting-started/running/
- https://developers.google.com/search/docs/fundamentals/seo-starter-guide
