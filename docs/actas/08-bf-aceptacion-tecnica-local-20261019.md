# B-F — terminación técnica local del frontend, 2026-10-19

Se aceptan los seis puntos de B-F del contrato16 §7 en el alcance técnico local. Revisor: Codex principal. Corte congelado de la comprobación Docker/Caddy: `dab95ec558347852801b22db2610104a5feaeef5`; producto y pruebas existentes permanecen iguales al corte común GS01 `e99dc96`. La [matriz por requisito](../evidencias/bf-local-acceptance-matrix-20261019.json) identifica implementación, versión, prueba y límites. No se afirma aceptación de B-B, C o producción.

## Evidencia y decisión

La [auditoría frontend actual](../evidencias/bf-current-six-point-audit-20261019.json) vincula 27 casos de navegador/SEO/contraste/reflow a la batería común: 3217 PASS más 4 subpruebas y 122 SKIP funcionales; capacidad 290 PASS y 8 SKIP, sin fallos. No se suman como pruebas nuevas ni se convierten omitidos en PASS. La [matriz de 19 familias](../evidencias/gs01-current-states-final-binding-20261019.json) conserva estados y autoridad de cuenta, agencia, publicación, paneles, moderación, derechos y promociones; no se han quitado estados para simplificar presentación.

Se revisaron tokens visuales claros/oscuros, fuentes del sistema, componentes, espaciado, etiquetas, responsive, foco y errores. El navegador común aporta teclado y errores ES/EN, 20 observaciones de reflow a 320/1280 CSS px y **640 mediciones de contraste PASS**; 72 selectores ausentes no son mediciones. Esto no constituye certificación WCAG, revisión jurídica ni prueba de zoom real al 400 %. La continuidad de CSS/plantillas/JS con el código probado se comprobó por SHA.

BF05 dispone ahora de [auditoría terminal independiente](../evidencias/bf05-assets-terminal-audit-20261019.json): imagen native-sealed v11 inmutable, PostgreSQL real, Caddy con configuración del repositorio idéntica y volumen estático propio. Cinco activos devuelven HTTP200, MIME correcto y bytes idénticos; dieciséis vistas ES/EN × 390/1280 × claro/oscuro × listado/ficha, con 24 imágenes decodificadas, sin errores JavaScript ni desbordamiento horizontal. El navegador rechaza peticiones a otros orígenes; el inventario de cargas de recursos de plantillas/CSS/JS no encuentra referencias remotas literales.

Ocho capturas nuevas revisadas cubren las ocho combinaciones de idioma/tema/anchura; además se revisaron dos referencias previas de formulario público inválido y conflicto privado, ligadas a CSS/base idénticos. No se detectó pérdida de contenido ni controles ilegibles. La tabla de tarifas estrecha puede partir palabras y los filtros requieren desplazamiento largo: mejoras de usabilidad futuras, sin ocultación de datos o acciones. Metadatos/idiomas/canonicalización se conservan mediante la prueba SEO vigente; las reglas servidor pasan a BB07.

## Métricas separadas de frontend

Mediciones locales, sin perfiladores y con fixtures sintéticos. Una observación por variante: no son p95 ni Core Web Vitals de campo. El enrutamiento de Playwright desactiva caché; listado precede a ficha en cada contexto nuevo. No hay un antes/después válido para atribuir mejora al código, ni cambios de producto en esta fase.

| Métrica | Antes de BF05 | Comprobación actual |
| --- | --- | --- |
| CSS propio | Sin medición válida de este montaje | 12.412 bytes; 4,07 ms en una descarga local |
| Cuatro JS propios | Sin medición válida de este montaje | 962 / 1.553 / 1.179 / 52.182 bytes; 1,52–2,44 ms por descarga local |
| Imágenes WebP sintéticas | Sin medición válida de este montaje | 10.516 / 11.110 bytes; 24 decodificaciones correctas |
| Navegación listado, 8 variantes | Sin medición válida de este montaje | 254,1–335,5 ms, rango observado |
| Navegación ficha, 8 variantes | Sin medición válida de este montaje | 254,4–344,0 ms, rango observado |
| FCP listado / ficha | Sin medición válida de este montaje | 268–364 / 188–292 ms, rangos locales |

Caddy entrega sin compresión adicional en esta configuración; se registra el comportamiento y no se inventa un umbral ni una mejora por habilitar opciones sin beneficio medido. Estos valores no cambian el p95 contractual de carga aceptado en CR09 ni la excepción provisional MOD09. Las diferencias históricas del portátil no se atribuyen al código: el perfil energético cambiaba al alternar el cargador.

## Fallos, entorno y limpieza

Se conservan los tres intentos anteriores: [publicación en red interna](../evidencias/bf05-internal-publishing-failure-20261019.json), [intérprete base por symlink](../evidencias/bf05-browser-interpreter-failure-20261019.json) y [permisos de copia Caddy](../evidencias/bf05-caddy-config-permissions-failure-20261019.json). Cada corrección se basó en un diagnóstico separado. El diagnóstico inicial de Caddy omitió NET_BIND_SERVICE y falló antes de leer configuración; se conserva separado, sin usarlo como evidencia del runtime real. La validación posterior con flags exactos confirma el permiso de lectura y su corrección.

Python3.12.15; imagen v11 `sha256:261d4b6d97f581ddf8cfd19318b3455eda8bafafb5de4e151c084d08d2200fbd`, PG17 y Caddy por identidades congeladas en el recibo. Controlador4CPU/3584MiB/swap0/pids512; PG1CPU/1536MiB; app2CPU/1536MiB; Caddy0,2CPU/128MiB. Sólo Caddy publica un puerto efímero en loopback mediante puente propio; aplicación/PG permanecen internos. Sin servicios normales modificados, proveedores, publicación ni datos reales.

4257 entradas de fuentes congeladas e instrumentos intactos; seis recursos propios eliminados y ausencia comprobada independientemente. Servicio terminal inactivo, PID0, resultado success. Telegram de la prueba confirma PASS/sent; auditoría independiente también pasa. Imágenes/capturas y sus huellas quedan referenciadas en el recibo.

**Continuación: B-B01–07 y C-S01.** Se mantiene el objetivo completo activo. Los requisitos externos de producción, revisión independiente y textos definitivos permanecen separados.
