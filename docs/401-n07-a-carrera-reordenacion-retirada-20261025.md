# N07A — carrera confirmada y candidato de corrección

25 de octubre de2026. Alfa, base4bd9a59. N07 sigue en curso,6/13obligatorios aceptados. Continúa el [prerregistro400](400-n07-a-prerregistro-medios-publicacion-20261025.md); aún no es acta de aceptación del candidato ni de N07.

## Reproducción original

Run20261025-222614-c4dfdaad:2FAIL/0ERROR/SKIP,44,212sJUnit. En ES y EN, después del lookup inicial, la petición reorder quedó bloqueada realmente por otra conexión PostgreSQL. Remove retiró la foto y confirmó antes de liberar el bloqueo. La petición de reordenación terminó con500en lugar de404; el log original identifica StopIteration en apps/mediafiles/views.py:149 al buscar el ID en la lista de fotos activas. Las aserciones previas confirmaron retirada conservada, compañera activa, posiciones intactas y un único incremento de versión debido a remove. Por tanto se confirma un defecto funcional de respuesta; no se afirma fuga de imagen ni pérdida de datos. Huellas originales intactas, contenedores propios ausentes y Telegram terminal sent.

Dos errores de preparación anteriores permanecen separados: argparse rechazó una opción native-source ausente sin ejecutar pruebas; run20261025-222519-72cf0bf2 fue ERROR de Ruff F811 antes de pytest. Se añadió una supresión explícita al binding intencionado de la fixture pytest; AST y número de líneas idénticos. No se redujeron casos u oráculos. Ambos avisos terminales enviados.

## Candidato y contraste previsto

Único cambio de producto: función reorder de apps/mediafiles/views.py. Con los bloqueos de gestor/revisión mantenidos, next usa valor por defecto None; si la foto ya no está en la lista activa devuelve404antes de ordenar o incrementar edit_version. Conserva todas las guardas, lista fresca y transacción, y no añade consultas. Los demás cuerpos de funciones son AST idénticos. SHA antes3a7e31e28881de89973cccf401e211e9161577af1f15c90e645c406f1390aad2; SHA candidato y copia original en el registro de alcance del lote.

Selección correctiva: tests/test_photo_reorder_remove_race.py (ES/EN) y tests/test_photo_edit_localization.py (ES/EN), cuatro casos. Los dos existentes verifican dirección inválida400, revisión no editable409, titular ajeno404, reordenación válida302y retirada/versiones/orden; usan navegador Chromium real y PostgreSQL. Los dos nuevos mantienen bloqueo/retirada concurrentes y esperan404sin efecto adicional. No se modifican los existentes. Preparación de imágenes eager explícita en la carrera; fixtures queued en localización no acreditan procesamiento ni broker.

Comando: `.venv/bin/python scripts/run_local_ci.py --profile focused --workers 1 --timeout 900 --native-source /tmp/web-modelos-librdb-v2.4.0 --test tests/test_photo_reorder_remove_race.py --test tests/test_photo_edit_localization.py`. Congelar fuentes, instrumentos y dependencias después del refresco focal de grafo y antes del contraste. Runner mantiene limpieza y aviso terminal Telegram. No iniciar una campaña de optimización de QA.

| Medida | Antes | Después previsto | Estado/límite |
| --- | --- | --- | --- |
| Reorder tras retirada mientras espera, ES/EN |500por StopIteration,2FAIL |404controlado, misma retirada/orden/versión | Pendiente de ejecutar candidato |
| Consulta y guardas del recorrido | Lista fresca con bloqueo; caso ausente sin manejar | Mismas consultas/guardas y denegación explícita | Fuente, no mejora temporal |
| Tiempo de aplicación antes/después | Sin muestras de latencia aislada equivalentes | Pendiente/no evaluable como mejora temporal |44,212s corresponde a QA; no es latencia de petición |

N07B conserva su preparación aislada de worker/Beat;39unidades aún por conciliar. N03/N04/N05/N06 y propietarios compartidos N09/N10 mantienen sus límites. Sin apertura ni optimización marginal forzada.
