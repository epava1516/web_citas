# N09E — corrección prerregistrada de fronteras antes de descifrar

Plan anterior al cambio de aplicación. Base `a5cd18d`; [432](432-n09-e-prerregistro-lecturas-privadas-tras-espera-20261026.md) ejecutado y auditado. N09D117PASSaceptados se conservan sin repetir; N09 completo sigue abierto139IDs/8de13bloques. Alpha/noindex, identidad sintética y ausencia de proveedores reales.

## Tres defectos confirmados, sin filtración HTTP atribuida

Run `20261026-075104-d7159725`: **3 PASS/3 FAIL,129,909sJUnit**, cero ERROR/SKIP de pytest,1.770huellas estables, limpieza y Telegram terminal confirmados. El resultado global ERROR del runner corresponde a los tres FAIL, no a tres errores de preparación. Auditoría independiente válida: tres controles nativos satisfactorios y tres revocaciones observadas durante espera PostgreSQL con PID bloqueante propio, confirmadas al liberar.

| Servicio/fila | Control válido | Tras revocación durante la espera |
| --- | --- | --- |
| Decisión de campo |Éxito;2llamadas/2retornos nativos satisfactorios al descifrar el objetivo|PermissionDenied final y dominio intacto, pero2llamadas/2retornos nativos de descifrado previos|
| Información independiente |Éxito;1llamada/1retorno satisfactorio|PermissionDenied final y dominio intacto, pero1llamada/1retorno de descifrado previo|
| Borrador de respuesta final |Éxito;1llamada/1retorno satisfactorio|PermissionDenied final y dominio intacto, pero1llamada/1retorno de descifrado previo|

Los observadores reenviaron al callable real y su resultado sin modificarlo. Sólo contadores/hash/metadatos, sin contenido privado ni ciphertext. Los controles produjeron exactamente su auditoría/lectura esperadas y conservaron fuentes/versiones. En los tres negativos se confirma incumplimiento de autoridad antes del descifrado interno; **no** se observó devolución de plaintext por HTTP, y las llamadas del instrumento son servicios directos, no transporte HTTP. Conservar los FAIL originales y el instrumento432 byte a byte.

Los tiempos del caso registrado incluyen preparación nativa, espera y cleanup; no son latencias normales del servicio. Cualquier intervalo derivado de statement_seconds tendrá explícito su alcance parcial y la instrumentación/snapshots incluidos, sin atribución causal de rendimiento entre éxito y denegación.

## Cambio acotado previsto

Cuatro módulos, sin modificar autorizadores compartidos, roles, endpoints, formularios, modelos, migraciones, cifrado, servicios de infraestructura o configuración. Reutilizar el autorizador actual con el User original y sus epochs, después de obtener la fila que puede esperar y antes de auditoría, replay, descifrado o proyección. Usar su actor fresco para los controles posteriores. No adoptar epochs nuevos ni bloquear el User operador.

- `rights_access_field_decision.py`: revalidar en context después de obtener la decisión; protege inspect_decision/review mediante el helper existente. Revalidar en propose después del inventario y después del último lock de decisión existente, y en consume después de obtener la decisión aprobada. Las tres últimas fronteras se incorporan por revisión de variantes del mismo módulo, no como tres defectos runtime adicionales confirmados.
- `rights_information_review.py`: repetir authorize después de obtener RightsCopyInformation, antes de independencia/proof/firma/replay/auditoría/unseal, tanto para inspect como para review a través de record.
- `rights_access_response_review.py`: repetir authorize_reviewer después de obtener el borrador y antes de auditoría/ciphertext. Record ya usa inspect y conserva su flujo de evidencia y autorización final.
- `rights_access_field_read.py`: revalidar tras obtener el inventario propio y antes de leer su motivo cifrado/proyectar campo. Es variante de fuente adicional, sin reproducción original propia atribuida.

Total previsto: **siete nuevas comprobaciones en seis funciones existentes**, cuatro módulos, sin nuevos helpers ni cambios a los autorizadores. Mantener controles finales de autoridad, scope/COI, separación autor/revisor, proof/retención, lecturas auditadas, versiones, firmas, replays y transacciones. No afirmar serialización universal ni cobertura de todo recurso tardío de source_snapshot: sus locks/proyecciones y el ámbito de cuenta sin perfil conservan su evaluación independiente en N09.

## Verificación prevista:38casos antes de congelar

Reejecutar los seis diagnósticos432 íntegros:3controles nativos con descifrado válido y3revocaciones con PermissionDenied,cero llamadas al objetivo/cero retornos de descifrado y dominio intacto. El archivo original y sus oráculos no se editan.

Añadir ocho casos en instrumento nuevo: cuatro variantes × control/revocación. Propose reteniendo inventario propio y observando el motivo de su lectura previa; propose en replay reteniendo su decisión existente y observando el body de esa decisión; consume reteniendo decisión previamente aprobada de forma independiente y observando su body; field_read reteniendo inventario propio y observando su motivo cifrado. Preparación mediante servicios nativos, perfil, permisos/proof/lecturas actuales. No se atribuyen baseline ni cuatro defectos confirmados adicionales a esas regresiones nuevas.

En controles comprobar resultado nativo/contenido mediante booleanos sin repr privado, lecturas nuevas o replay legítimo con sus efectos exactos; en revocaciones exigir PermissionDenied,cero llamadas/retornos al ciphertext objetivo y dominio sin cambios. Mantener dos conexiones PG propias, PID/Lock/bloqueante real, retirada confirmada al liberar y cleanup acotado. Observador sólo pasivo y exacto al ciphertext objetivo; un replay puede haber realizado lecturas autorizadas antes de llegar al último lock: no afirmar que el contador de ese objetivo cubre cualquier otro contenido o etapa.

Regresión original seleccionada, sin editar: test_rights_access_field_decision.py2, test_rights_access_scope_inventory.py2, test_rights_information_review.py4, test_rights_information_review_races.py8, test_rights_information_review_mobile.py2, test_rights_access_response_draft.py2 y test_rights_access_response_mobile.py::test_mobile_final_response_preparation_and_independent_decision4. **24originales**, incluyendo perfil/cuenta, ES/EN, Chromium móvil, independencia, fuente/proof/epochs y replays, CSRF y carreras previas de caso.

Los ocho recorridos móviles auxiliares de metadatos físicos/logs no se vuelven a ejecutar: sus parsers/retención y payloads permanecen intactos; el cambio de guarda es anterior a cualquier rama de esos cuerpos y los cuatro recorridos móviles básicos cubren ambos ámbitos/idiomas del mismo entrypoint. Conservar sus testigos originales, sin declararlos PASS nuevo en este lote. No se repite el testigo original de coverage por semejanza ni N09D117por documentación.

Total6diagnósticos+8variantes+24originales=**38**. Runner oficial serial con PostgreSQL/Redis propios desechables, parser nativo, lint/revisión/AST/semántica/corte/freeze antes de ejecutar y Telegram terminal después de cleanup, con recibos verificados. Aceptar únicamente con38PASSválidos y oráculos auditados; si falla un caso, conservar el resultado y corregir el ámbito afectado sin recortar la selección.

Tabla posterior con contadores y tiempos disponibles/unidad/alcance. Esto corrige autoridad; consultas adicionales tienen coste de seguridad y no se presentarán como optimización. N09 sigue pendiente hasta disponer sus139IDs y las condiciones restantes de fuente/rectificación/purgas/outbox/jobs; N02restante al final, N10/N11/N15 pendientes y N12–N14condicionados. No apertura beta/producción ni proveedor por este bloque.
