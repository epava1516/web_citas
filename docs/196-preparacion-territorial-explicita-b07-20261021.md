# B07 — Preparación territorial explícita

Estado: helper opcional verificado en PostgreSQL real; B07 abierto8/18.

Tras [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md), `redistribute_promotional_geography` prepara municipios con cantidades positivas explícitas cuya suma coincide con todos los publicados. Sólo PostgreSQL de pruebas test_promotion_gate_, modo promociones sintético y fuera de PRODUCTION/RECOVERY. Exige2–32municipios activos de fuente sintética; rechaza recuentos booleanos/cero/incompletos y revisiones ausentes/compartidas. Transacción atómica, recenso posterior, limpia zona/código postal incompatibles y deja invalidación nativa para refrescar. Devuelve metadata nueva sin reescribir el manifiesto previo. No cambia fixture por defecto ni rutas del producto.

## Protocolo previo

Ejecutar únicamente tests/test_promotional_statistics_preparation.py mediante runner oficial PostgreSQL, focused/1worker/snapshots/native-source, timeout300. Nuevo caso reparto7/3: seis negativas sin mutación,10visibles por regla nativa tras refresco, filtros ciudad ESEN con IDs/recuento exactos y partición completa, órdenes/derechos iguales antes/después. Reutilizar dos casos existentes para censo individual/agencia y finalizaciónANALYZE/guardas. Exigir3PASS/0FAIL/0ERROR/0SKIP, fuentes congeladas,628producto intactas, limpieza propia y recibo Telegram. Guardar SHA previo; FAIL/ERROR conserva evidencia y detiene secuencia.

Este helper no está activado en el arnés TCP. La distribución es sintética explícita, no nacional representativa;10perfiles no acreditan100/1000/10000, carga, filtros combinados, páginas profundas, PRODUCTIONchecked o recursos. Esas casillas de matriz180 siguen pendientes. Sin900automático ni aceptación B07/global.

## Resultado auditado

Run `20261021-221232-36472f74`:3PASS/0FAIL/0ERROR/0SKIP,58,261sJUnit sumados por caso. [Auditoría](evidencias/b07-territory196-preparation-20261021-audit.json):reparto7/3 en dos municipios,10perfiles visibles por regla nativa y filtros ciudad ESEN con IDs/recuento exactos; seis entradas inválidas sin mutación, órdenes/derechos idénticos. Dos casos previos de censo/finalizador pasan en el mismo corte.628fuentes de producto intactas, fuente/protocolo/limpieza/PIDs/Telegram verificados antes de editar documentos.

Pendiente conectar este helper a una mezcla TCP preregistrada. Antes de esa integración, actualizar también la frase heredada de limits que describe geografía compartida: geography_distribution/geography del retorno describen el nuevo reparto; no usar limits heredado para declararlo representativo. No se ha ejecutado carga multiterritorial ni demostrado filtros combinados/páginas profundas o PRODUCTIONchecked.

Actualización197: limits corregido y verificado en el nuevo retorno, manteniendo el objeto original intacto. Equivalencia funcional ampliada a100perfiles70/30 y veinte páginas HTTP ciudad/texto ESEN; no carga TCP ni capacidad grande. Véase [filtros197](197-filtros-paginacion-territorial-b07-20261021.md).
