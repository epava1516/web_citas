# B07 — línea de base y presupuestos de lectura

Fecha:2026-10-20. Estado: diagnósticos100/1000/10000 completados y auditados; B07 permanece abierto por controlesTCP/carga y presupuestos pendientes. Continúa el contrato funcional1.1, ejecución1.9 y [roadmap103](103-roadmap-beta-clasificados-20261020.md), tras [B04–B06](actas/13-beta-b04b06-aceptacion-local-20261020.md).

## Condiciones fijadas antes de medir

No cambiar código de producto, recursos, workers, autoridad ni criterios para facilitar el resultado. Registrar huellas de producto, pruebas y dependencias, escenario y runtime. No reutilizar latencias del alfa como medida de la adaptación. La hipótesis inicial B08 es comprobable: promociones habilitadas omiten state_page, materializan/validan candidatos completos y vuelven a comprobar derechos en ranked; medir antes de cambiar esa ruta.

Se conservan los presupuestos de ejecución16§16: equivalencia de IDs ordenados, recuentos y páginas; generador sin solicitudes no emitidas, demora p95≤10ms/p99≤25ms/máximo≤100ms, timeout65s y contabilidad reconciliada. Corto10000anuncios/20RPS/60s/1200dinámicas y un upload; drain≤70s, pendientes al cierre≤20 y finales0; p95 observable de todas las dinámicas terminadas<800ms, errores<1%, upload302. Contractual sólo tras PASS corto:900s/18000dinámicas, mezcla tercios listado/búsqueda/ficha ES–EN y15uploads separados. FAIL/INVALID corto bloquea contractual; no rebajar estos criterios por la beta.

Para escenarios nuevos de promociones/filtros/página profunda/backlog, conservar<800ms y<1%errores como objetivo HTTP provisional de ingeniería, pendiente de contraste en mezcla preregistrada. Un diagnóstico secuencial no cumple ese gate. No prometer percentiles fiables desde cinco muestras. La aceptación provisional histórica MOD09 de expedientes grandes mantiene su ámbito y no acepta el listado promocional nuevo.

## Diagnóstico preregistrado

Instrumento: tests/test_beta_read_baseline.py, tres tamaños explícitos100/1000/10000. Primero ejecutar exclusivamente variante100 para validar instrumento y obtener coste inicial; no iniciar matriz grande hasta inspeccionar resultado y estimar duración. Fuente congelada por runner oficial, PostgreSQL/Redis propios y generación aislada. No datos reales.

Fixture diversa sintética existente,20%de perfiles con pedido/evento sintético Top/Premium emitido mediante servicio real, proporción Premium uno de cada tres promocionados. Conserva duración/snapshot y autoridad. Fotografías y agencia compartidas; distribución geográfica real de la fixture se registra, sin fingir diversidad nacional. No mide20%de compras reales ni moderación nativa de todo el inventario.

Doce escenarios: tres modos (orgánico, promociones, promociones con backlog) por cuatro rutas (primera ES, texto EN, última ES, ciudad+idioma EN). Backlog retira1%del inventario entre promocionados sin refrescar la proyección; la guarda pública sigue real. Las páginas profundas se ajustan al recuento tras retirada. Cada escenario calienta una vez, toma cinco controles sin profiler y una observación instrumentada separada. Verifica HTTP200, IDs únicos, recuento y huella estable; un inelegible no puede reaparecer. El control mide wall/CPU del proceso pytest; la observación mide llamadas SQL/tiempo de driver y render. RSS es máximo acumulado del proceso, no memoria exclusiva de la petición ni PostgreSQL. p50/p95/p99 nearest-rank son descriptivos y p95/p99 coinciden con máximo con cinco muestras.

El artefacto beta-read-diagnostic-TAMAÑO.json vive en el directorio del runner e incluye muestras crudas, modo/ruta/filtros, población, orden/etiquetas/route, geografía y límites. Sus huellas se conservan en JUnit. Registrar también fuente, limpieza y aviso terminal; no convertir DIAGNOSTIC_COMPLETE en PASS de capacidad.

## Trabajo restante de B07

Tras la variante100, corregir el instrumento si falla, conservar negativos y comparar100/1000/10000 cuando la estimación lo permita. Completar distribución territorial/estados, escenario PRODUCTION y checked sin simular verificación real, consultas combinadas y páginas inicial/intermedia/última. Separar diagnóstico de SQL/render de controles TCP completos sin profiler y carga limpia. Reutilizar servidor/generador propios auditados, sin activar sus variantes históricas de reemplazo de funciones. Registrar CPU/memoria por servicio y techo de recursos, backlog/edad de colas y drenaje; no inferirlos desde cursor.execute o RSS de pytest.

Antes de cualquier comparación de optimización, fijar mezcla y recursos equivalentes y testigos de paridad de IDs/orden/recuento. Ejecutar corto y, sólo si válido y PASS, contractual pertinente. Preparar cualquier prueba de horas de forma persistente y aplicar aviso previo/pausa explícita del goal conforme AGENTS. No iniciar baterías largas por redactar este documento.

B07 no queda cerrado por instrumento, diagnóstico100 o latencia aislada. B08–B11 requieren coste observado, hipótesis finita, cambio mínimo, equivalencia y comparación HTTP. B12–B17/B00 residual siguen separados; B15 opcional. Sin publicación, pagos, proveedores o datos reales.

## Diagnóstico inicial observado y siguiente ensayo

Ejecución20261020-044503-0c903827:1PASS/0FAIL/0ERROR/0SKIP, doce escenarios diagnósticos. [Auditoría100](evidencias/b07-diagnostico100-audit-20261020.json) confirma artefacto, igualdad de fuentes, retirada de servicios/temporal/procesos y reciboTelegram1792471684821587717-1297853.json. Setup35,872s y call113,772s. No cambio de producto. La importaciónPathsinuso detectada por el preflightRuff se corrigió antes de congelar; no fallo de comportamiento.

Listado primera página ES: orgánico mediana145,2ms/máximo152,1ms y32consultas en observación separada; promociones mediana1797,9ms/máximo2050,7ms y366consultas. Las demás rutas promocionales tienen medianas1653,9–1727,8ms; backlog1464,9–1755,2ms. Se retiró correctamente un perfil promocionado pese a proyección pendiente. La observación SQL mide tiempo de driver, no CPU de PostgreSQL. La fixture registra99perfiles de agencia en un solo municipio; no diversidad territorial nacional. No convertir estos percentiles de cinco controles en aceptación SLO.

La diferencia observada justifica estudiar B08: revisión completa y validación de cada derecho con lecturas repetidas, incluyendo elegibilidad fresca, comprador y autoridad. Todavía no se ha aislado cuánto aporta cada función; no declarar causa dominante sólo desde el número de consultas. Preservar validación fresca y retirada inmediata en cualquier cambio posterior.

Siguiente ensayo preregistrado: las variantes1000 y10000 del mismo instrumento, un worker pytest, cinco controles por escenario y observación SQL/render separados, misma fixture/proporción comercial y sin modificar producto. Capturar recursos visibles y fuentes congeladas; es diagnóstico de crecimiento, no carga aislada ni TCP. La escala observada sugiere horas para la matriz completa, sin garantía lineal. Preparar runner persistente, límite del paso pytest18000s, aviso terminal y recibo de lanzamiento; antes de esperar, aviso previo confirmado y pausa explícita del goal. No reinicio automático ni nuevos sondeos tras la pausa. Un timeout o presupuesto de recursos insuficiente conserva resultado ERROR/INVALID y no se sustituye por PASS de100.

Resultado posterior: baseline045153 terminó2PASS/0ERROR/0SKIP, fuentes/limpieza/Telegram auditados. La [descomposición B08](109-correccion-ruta-promocional-beta-b08-20261020.md) recoge coste y siguiente perfil; la [auditoría grande](evidencias/b07-diagnostico1000-10000-audit-20261020.json) conserva muestras de ambos tamaños. NoTCP/capacidad.
