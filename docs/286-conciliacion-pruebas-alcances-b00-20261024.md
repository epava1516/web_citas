# B00-327 — Pruebas capturadas y alcance de evidencia

Fecha: 2026-10-24. Conciliación semántica de fuentes históricas de pruebas, con contraste estático seleccionado.

B00-327: 262 de 295 fuentes únicas conciliadas; quedan 33 de arquitectura. Se incorporan pruebas y verificación 1–2: fixtures, diagnósticos, cuentas, derechos, navegador y capacidad. Contrastadas aserciones actuales sin convertir su presencia en resultados. Sin cambios de aplicación o pruebas, defecto nuevo demostrado ni nueva aceptación funcional. B00 sigue abierto; nueve de los 18 puntos de beta cerrados y B15 opcional.

## Lectura y procedencia

Seis lectores nativos de sólo lectura cubrieron648.220caracteres en seis partes, mediante57emisiones literales contiguas de hasta12.000caracteres. Como máximo tres lectores simultáneos y menos de110.000caracteres por contexto asignado. Sin truncamientos ni reparaciones declaradas. Los informes guardados son extractos seleccionados marcados, no transcripciones completas. Cero nuevas invocaciones ClaudeV1; consumo histórico conservado y sin estimación de tokens nativos.

| Captura | Fuente | Caracteres | Particiones |
| --- | --- | ---: | --- |
| Pruebas1/11 | `source:56nawxs9vbk9nyaostx8` | 321897 | [0,107299), [107299,214598), [214598,321897) |
| Pruebas2/11 | `source:vwicahqjttg1w20d3h1t` | 326323 | [0,108774), [108774,217548), [217548,326323) |

SHA completos: `957a86a4735587ab365617704e5b3728c5510ac55ef5d978463130a35ed28621` y `a6853b2dbe603bc031a5b715f2cb512788833632265877bc308ed6226867b945`. Snapshot11/10/base7e04016; el formato capturado daña indentación, identificadores y selectores. Esta representación no acredita sintaxis ejecutable ni igualdad con las fuentes actuales. Los imports y enlaces no otorgan lectura a las dependencias externas al intervalo.

El principal verificó hashes de parte y citas declaradas contra texto original, inspeccionó fronteras y doce citas con contexto. El verificador realizó catorce cotejos sobre esos doce intervalos, unió las partes sin huecos y revalidó integridad de las295capturas. El [ledger](evidencias/b00-current-source-review-ledger-20261023.json) pasa de260a262disposiciones y de35a33pendientes mediante reemplazo atómico, permisos conservados y base260fijada o resultado idéntico. Artefactos: `artifacts/beta-promotion-fix-20261020/b00-327-*`.

## Qué describen estas pruebas

La captura1 reúne helpers de capacidad, generación asíncrona, transporte, roles PostgreSQL, profiling, baseline diagnóstico, snapshots de bootstrap, fixture RDB y pruebas de acceso/cuentas: localización, copias, confirmación, rectificación, supresión, inventarios, correo y cierre. La captura2 continúa cuentas y agencias/MFA/recursos, navegador, contabilidad y transporte de benchmark, kernel canónico, instrumentación/preflight/artefactos/capacidad y aclaraciones/reclamaciones.

| Familia | Qué establecen sus aserciones como especificación | Qué necesita evidencia ejecutada aparte |
| --- | --- | --- |
| Preflight finito | Worker no-eager y referencias de objetos, igualdad de bytes/hash, binding de exportación | Topología realmente iniciada y resultado terminal; no capacidad contractual por un caso |
| Contabilidad del benchmark | Exactamente1% y800ms incumplen umbrales estrictos; pendientes/generador inválido no se ocultan | Validez del generador, mezcla, recursos y población del ensayo contractual real |
| Perfiladores y wrappers | Restauración de hooks/aliases, errores originales, límites y semántica inclusiva | Integración real y coste observado; intervalos anidados no se suman como wall total |
| Copias y derechos de cuenta | Ámbito propio, denegación tras cambios, replay y efectos/versiones atómicos | Ejecución actual sobre PostgreSQL y correspondencia con el recorrido aceptado |
| Navegador y localización | ES/EN, privacidad de GET/POST, valores literales y rutas, móvil Chromium seleccionado | Resultados actuales; sesiones inyectadas no prueban login interactivo y simuladores no prueban identidad |
| Nativo, TCP y objetos | Guardas de identidad, transporte completo y referencias privadas | Artefacto nativo y servicios reales correspondientes; fallback, opener falso o una prueba omitida no los acreditan |

La presencia de una aserción no es un PASS. Pruebas de guards, mocks de montajes/recovery, respuestas falsas y relojes inyectados conservan ese alcance. Otras pruebas describen esperas observadas en PostgreSQL mediante PID y bloqueos; una intercalación con Events/monkeypatch es evidencia distinta. Los tests que dependen de flags, artefactos o entornos verificados pueden quedar omitidos: colección no acredita ejecución.

Los snapshots de directorio reutilizan bootstrap sintético, no lecturas o decisiones de derechos. Un baseline diagnóstico puede contener evidencia aprobada original, pero su hit no crea lecturas nuevas ni acepta N3/SLO. Los helpers referidos no reciben crédito por importarse. Simuladores de identidad/entrega, facts jurídicos sintéticos y direcciones example.invalid no prueban hechos jurídicos, proveedor o recepción humana.

Los fixtures antiguos de agencias, modelos, servicios y tarifas se contrastan con el contrato romántico vigente antes de reutilizar expectativas públicas. La corrección de datos históricos o de relaciones de cuenta conserva su propio ámbito. No se adopta el catálogo profesional desde los tests capturados ni se confunde cuenta propietaria de agencia con autoridad sobre todos sus perfiles.

## Contraste actual

Se seleccionaron once archivos actuales y veinticinco literales: nueve módulos de pruebas, el helper `capacity_async_preflight.py` y [CI local](ci-local.md). Se comprobaron límites explícitos del preflight, contabilidad, esperas de cuenta, ámbito editorial, artefactos/symlinks/RLIMIT, perfiladores, modo preflight, control pequeño y simuladores de confirmación/cierre. Las aserciones actuales conservan esas diferencias; este contraste estático no prueba que pasen ni certifica la implementación completa de cada consumidor.

El preflight declara un caso sintético finito y valida binding/bytes; su propio scope excluye veredicto de capacidad. Los tests de cuenta separan autoridad de perfil y esperan denegación sin nuevos registros/versiones tras un bloqueo observado. La contabilidad incluye fallos y pendientes en su población y mantiene umbrales estrictos. Los perfiles y controles pequeños delimitan su instrumentación. La documentación de CI distingue checks, selección, omisiones, paralelismo funcional y capacidad serial.

No se ha demostrado un defecto nuevo ni una aclaración documental necesaria en esta selección. Sin cambios de aplicación, helpers o pruebas, ni nueva batería funcional/carga. Los checks de integridad y documentación de esta conciliación tienen sus propios avisos; no se presentan como resultados de los tests leídos. B07 y las correctivas320–322 conservan sus auditorías y alcances originales.

## Grafo y continuación

Grafo380 revalidado antes de analizar; integración semántica dirigida381. Sin AST nuevo, semántica exhaustiva o HTML global. Las capturas de documentación1–8 ya tienen disposición; quedan nueve capturas de pruebas y las demás fuentes pendientes.

Quedan33fuentes de arquitectura,22.879.419caracteres: pruebas3–11, interfaz, herramientas, referencias y grandes grafos. Continuar lectura acotada y contraste actual, sin porcentajes de esfuerzo desde conteos. B00 sigue abierto, nueve de18puntos beta cerrados y B15 opcional. Se conservan límites legales y de producción; sin publicación, contratación, gasto o datos reales. Corte previo: [conciliación285](285-conciliacion-contratos-relevos-b00-20261024.md).
