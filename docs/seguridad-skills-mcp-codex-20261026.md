# Herramientas de seguridad para Codex — 2026-10-26

Instalación autorizada en conversación lateral. Alcance: ampliar las capacidades del asistente, sin continuar el contrato principal ni modificar código de negocio, dependencias del proyecto, base de datos, servicios, CI o commits. Se han preservado las modificaciones previas y concurrentes.

## Skills instaladas

Instaladas con el instalador oficial local de skills de Codex, mediante descarga de referencias inmutables, en `/home/felidae/.codex/skills/`:

| Skill | Procedencia | Referencia |
| --- | --- | --- |
| code-security | https://github.com/semgrep/skills | 68177b8830f96cd9d10dacbb14dde2566360503d |
| security-review | https://github.com/getsentry/skills | d12f250460ffd961f549dbebf7eeb0cf4afd4c2e |
| django-access-review | https://github.com/getsentry/skills | d12f250460ffd961f549dbebf7eeb0cf4afd4c2e |
| differential-review | https://github.com/trailofbits/skills | 196a9073ab10d35bacf111f945e02c00b2c6883a |
| variant-analysis | https://github.com/trailofbits/skills | 196a9073ab10d35bacf111f945e02c00b2c6883a |

Se leyeron las instrucciones principales, se inventariaron los 87 archivos y sus hashes, y se buscaron instrucciones sensibles en el material. No contienen scripts ejecutables ni enlaces simbólicos. Las coincidencias de exfiltración/inyección encontradas en referencias Sentry son ejemplos de ataques, no instrucciones operativas. Esta revisión acotada no es una certificación del contenido completo. Inventario local: `/home/felidae/.local/share/security-codex/skills-review.json`.

**Adaptación obligatoria:** security-review contiene una exclusión de rutas con autenticación previa. No aplicarla: analizar también IDOR, escalada de privilegios, aislamiento, revocación, permisos actuales y carreras entre comprobación y efecto. La autenticación es una precondición de ataque, no prueba de autorización. Los ejemplos de valores configurados tampoco prueban seguridad de concatenaciones o flujos derivados: seguir el dato controlable y las protecciones reales. Las instrucciones del proyecto y el alcance del usuario prevalecen.

Las cinco skills aparecieron en el catálogo efectivo de esta conversación después de instalarlas. Los agentes propios de plugins y sus comandos con namespace no se han instalado: usar sus pasos directamente, sin asumir agentes disponibles ni autorización para delegar.

## Analizadores aislados

Entorno Python separado: `/home/felidae/.local/share/security-codex/.venv/` (Python 3.12.15). No se modificó `.venv` ni pyproject/lockfiles del proyecto.

| Herramienta | Versión | Ruta |
| --- | --- | --- |
| Semgrep CE | 1.182.1 | `/home/felidae/.local/share/security-codex/.venv/bin/semgrep` |
| Bandit | 1.9.4 | `/home/felidae/.local/share/security-codex/.venv/bin/bandit` |
| pip-audit | 2.10.1 | `/home/felidae/.local/share/security-codex/.venv/bin/pip-audit` |
| Gitleaks | 8.30.1 | `/home/felidae/.local/share/security-codex/bin/gitleaks` |

Gitleaks se descargó del release oficial https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1. Se verificó el SHA256 del archivo linux_x64 contra el fichero de checksums del mismo release: `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`. Esto comprueba integridad frente a ese checksum, no una firma independiente. Registro: `/home/felidae/.local/share/security-codex/gitleaks-install.json`. Versiones completas del entorno: `/home/felidae/.local/share/security-codex/requirements-installed.txt`.

## MCP Semgrep

Registrado globalmente como `semgrep` mediante `codex mcp add`, usando el binario oficial integrado, transporte stdio y ruta absoluta. Configuración en `/home/felidae/.codex/config.toml`; se preservaron los otros servidores y opciones.

Herramientas habilitadas y verificadas por protocolo:

- `semgrep_scan_with_custom_rule`: contenido y regla YAML explícita procesados por el servidor local.
- `get_abstract_syntax_tree`: AST local.
- `get_supported_languages`: lenguajes soportados.

Métricas y trazas desactivadas (`SEMGREP_SEND_METRICS=off`, `SEMGREP_MCP_DISABLE_TRACING=true`), comprobación de versión desactivada, RPC Pro desactivado y fichero de settings aislado sin credenciales heredadas. Las herramientas de findings cloud, supply chain, esquema remoto, escaneo remoto y escaneo automático se deshabilitaron mediante variables oficiales y allowlist del cliente. En esta versión `semgrep_scan` no permite indicar reglas y rechaza auto con métricas desactivadas: no habilitarlo para sortear ese límite. Para conjuntos de reglas locales usar el CLI con `--config /ruta/absoluta/reglas.yml --metrics=off --disable-version-check`.

No se modificó el paquete Semgrep ni se instalaron hooks. Estas opciones no constituyen un aislamiento de red del proceso. No usar recursos remotos ni transmitir contenido privado; cualquier necesidad de acceso adicional debe ajustarse al alcance autorizado.

**Disponibilidad:** el servidor respondió a initialize, tools/list y llamadas reales de sus tres herramientas desde un cliente MCP independiente. No figura aún entre las herramientas MCP expuestas al modelo en esta conversación: refrescar/reabrir la sesión si es necesario. Registro y protocolo correctos no equivalen a disponibilidad efectiva en cada hilo.

## Verificación acotada

Se ejecutó una sola batería de instalación con `scripts/run_notified.py`, usando exclusivamente fixtures sintéticos fuera del repositorio. Resultado PASS:

- Semgrep CLI y MCP detectaron un eval sintético mediante una regla local explícita: un hallazgo esperado cada uno.
- Bandit detectó B307 en ese fichero sintético.
- Gitleaks detectó una cadena ficticia mediante una regla de prueba, con salida redactada.
- pip-audit consultó únicamente el paquete público sintético `urllib3==1.26.4` en PyPI, con `--no-deps --disable-pip`, y obtuvo avisos conocidos. No se enviaron dependencias privadas ni código del proyecto.
- MCP: negociación, lista exacta de tres herramientas, regla sintética, lenguajes y AST correctos.

El exit 1 de Bandit/Gitleaks/pip-audit se comprobó como detección esperada, no como error de instalación. pip-audit no instaló ese paquete ni ejecutó correcciones. Semgrep emitió un warning Pydantic sobre una anotación y avisó de ausencia de Pro Engine; sus tres herramientas funcionaron con CE. No se atribuye cobertura Pro ni análisis profundo interprocedimental.

Evidencia local: `/home/felidae/.local/share/security-codex/verification.json` y `verify_installation.py`. La batería no acredita seguridad del proyecto ni sustituye sus pruebas reales. No se ejecutó un nuevo análisis global ni se repitieron pruebas del contrato.

## Uso futuro y opciones descartadas

Cargar sólo la skill y referencias pertinentes al cambio. Revisar primero el alcance, distinguir candidato de vulnerabilidad comprobada y conservar las evidencias y notificaciones vigentes. Semgrep/Bandit no prueban por sí solos permisos ni seguridad ante concurrencia; Gitleaks no garantiza ausencia de secretos; pip-audit sólo cubre avisos conocidos y paquetes efectivamente evaluados. No añadir gates ni ejecutar auditorías automáticamente por esta instalación. Para pruebas, usar el runner de notificación y comprobar su recibo.

Se dejan sin instalar ZAP (requiere objetivo y entorno HTTP definidos), Snyk y Agent Scan (servicio/autenticación/transmisión adicionales), CodeQL (herramienta y condiciones de uso a resolver), Trivy (solapa capacidades y requiere un alcance de imágenes/infraestructura), SkillSpector y más skills generales (no necesarios para este primer conjunto). Django check --deploy ya forma parte de Django: no necesita instalación; ejecutarlo sólo con settings y entorno adecuados.

Referencias oficiales: https://github.com/semgrep/semgrep ; https://github.com/PyCQA/bandit ; https://github.com/pypa/pip-audit ; https://github.com/gitleaks/gitleaks ; https://learn.chatgpt.com/docs/extend/mcp .
