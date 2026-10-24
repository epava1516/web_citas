# B07 — Equivalencia territorial con49candidatos pendientes

Estado: control213 terminado y auditado; equivalencia funcional acotada, sin aceptación B07.

Prerregistro212 histórico: preparado control territorial100 con0/20derechos y49candidatos elegibles sucios más1retirado; instantánea propia extendida y READCOMMITTED heredado contrastados con referencia nativa en todas las páginas ESEN. Ruff PASS; ejecución213 pendiente. Sin cambio de producto ni cierre B07;8de18.

## Alcance y elección

La [calibración211](206-backlog-nativo-despacho-b07-20261022.md) prueba reparación por worker real de dos marcas a10perfiles. No cubre49candidatos publicables. Los diagnósticos históricos114/116 conservan sus distribuciones, referencias y límites: no se trasladan a esta nueva combinación territorial. Reutilizar la autoridad nativa y el comparador comercial independiente ya contrastado en199; no volver a medir una optimización ni cambiar reglas, SQL de producto, límites o caché.

Dos casos separados con100perfiles sintéticos70/30 en municipios activos: pipeline promocional habilitado con0derechos emitidos, y20derechos nativos Top/Premium por servicios con eventos firmados sintéticos. En el primer caso populate no emite pedidos/derechos y el censo0 se comprueba en base de datos; no se simula pago ni verificación externa. Fotografías/agencia compartidas, no diversidad nacional. Finalización de8tablas en PostgreSQL propio antes del control.

Por caso, retirar un perfil del primer municipio (promocionado cuando hay derechos) y actualizar available_until en49perfiles distintos que siguen siendo elegibles del mismo municipio. Mutación bulk transaccional por triggers reales, sin sustituir reglas ni tareas. Censo preparado100/70/30, visible posterior99/69/30,50marcas (49elegibles y1retirado). No afirmar que bulk reproduce una acción del panel. READ_REPAIR desactivado; no worker de recálculo en este control. La reparación final será una llamada manual explícita, nunca crédito de ejecución de Beat/Celery.

## Matriz213 congelada

Cuatro fases por caso: fresca, dirty49 con instantánea propia, dirty49 dentro de transacción heredada READ COMMITTED, y reparada manualmente. En cada fase: dos municipios × consulta vacía/photography × ES/EN × todas sus páginas (3+2),20páginas;80porcaso,160enlosdos. Comparar IDs ordenados, recuento exacto, páginas completas, duplicados y etiquetas comerciales con referencia que comparte autoridad publicly_visible y relevancia PostgreSQL, pero no helpers de orden comercial de discovery. Confirmar retirado ausente y49elegibles conservados; después de ambas fases sucias siguen50marcas, tras reparación0. Las firmas de ambas rutas sucias y reparada deben coincidir.

El código vigente usa trusted_state_extended_unknown cuando controla la instantánea y el censo está completo; no forzar el fallback antiguo de114. Esperar12páginas de primer municipio en esa vía con native_unknown49 y8del otro por estado normal. En READ COMMITTED heredado, verificar aislamiento real y esperar12fallback state_unknown_over_limit,8state. Fresca/reparada20state cadauna. NATIVE_UNKNOWN_LIMIT48 y DIRTY_LIMIT1000 intactos. Para20derechos:80tarjetas patrocinadas sumadas en las cuatro repeticiones frescas y76tras retirar un promocionado; el derecho emitido permanece pero no se expone. Para0derechos:0tarjetas en todas las fases.

Aceptar sólo2casosPASS/0FAIL/0ERROR/0SKIP con propiedades JUnit que registren fases, páginas, IDs, razones y conteos, referencias independientes y reparación manual declarada. Ruff PASS, fuentes congeladas/628producto iguales, runner PostgreSQL/Redis reales y kernel canónico nativo sellado, metadatos de origen y limpieza/recibo Telegram revisados. No profiler ni hooks de reemplazo en esta prueba. No TCP, percentiles, capacidad o edad de cola acreditados por160peticiones del cliente Django.

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test tests/test_backlog_territorial_equivalence.py --workers 1 --fixture-snapshots --isolate-test-broker --timeout 900
```

Oráculos nativos completos y dos cohortes: duración variable, estimación5–12min, timeout900s. Lanzar persistente con logs/PID+startticks y aviso terminal del runner tras limpieza. Verificar vigilante y disparador del mismo goal; aviso previo Telegram confirmado, pausa explícita y compactación durante espera, sin sondeos del modelo. Callback sólo reactiva, nunca acepta el resultado ni repite la prueba. Cualquier FAIL/ERROR se conserva y detiene; auditar antes de editar este protocolo. No cargas paralelas, nuevo short/900, proveedores o publicación. B07 abierto8de18; recursos/backlog a1000/10000, PRODUCTION/checked y colas completas siguen pendientes en [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md).


## Resultado auditado213

B07-213: equivalencia territorial verificada en PostgreSQL real: 2PASS,160páginas ESEN,100perfiles por cohorte con0/20derechos,49elegibles sucios y1retirado. Instantánea propia extendida y fallback READCOMMITTED coinciden con reparación manual. Fuentes/628producto, limpieza, Telegram, reactivación del mismo objetivo y solicitud de compactación comprobados. Sin crédito de capacidad ni worker; B07 abierto,8de18.

Ejecución `20261022-012925-539951ef`:131.103s y120.272s JUnit. [Auditoría independiente](evidencias/b07-equivalence213-unknown49-20261022-audit.json):80páginas por caso,50marcas conservadas durante ambas lecturas sucias y0tras reparación manual;100→99visibles,70/30→69/30. En cada cohorte:12páginas extendidas y8normales bajo instantánea propia;12fallback y8normales bajo READCOMMITTED heredado. Las firmas ordenadas, recuentos y etiquetas coinciden en las fases sucias y reparada. Comparador comercial independiente con autoridad y relevancia PostgreSQL compartidas; sin TCP ni aceptación de capacidad. El protocolo original permanece archivado e identificado por su SHA en la auditoría.
