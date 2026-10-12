# MOD08 — Consulta sobre precarga de acciones (2026-10-11)

Notebook: web_citas — Arquitectura integral — 2026-10-11; ID bb1f4634-45b7-4f41-b807-4b8502614b9d. Conversación: 2abca77e-854a-4524-a2c8-ed004d893987. Se usó `nlm notebook query --new-conversation`; modelo interno no expuesto. 100 fuentes; no se añadieron ni borraron fuentes.

[Consulta exacta](mod08-notebook-precarga-actions-consulta-20261011.txt). [Respuesta completa y referencias](mod08-notebook-precarga-actions-20261011.json).

## Contraste local

El notebook retira la candidata de precargar selection_review__selection__action. El SQL rights_evidence_action_scope_guard no protege payload_digest/encrypted_reason; el test test_runtime_cannot_move_parent_action_scope_but_payload_remains_mutable recoge expresamente modificaciones permitidas y ticket conservado. La lectura adelantada puede conservar contenido anterior a una mutación posterior a record, donde la lectura diferida actual consultaría el nuevo estado. Es un contraejemplo razonado, NO una reproducción concurrente ejecutada en esta consulta.

Correcciones a la respuesta: salir del atomic interno de record no libera los bloqueos de la transacción exterior. La ausencia de bloqueo de RightsAction en la candidata no implica que no existan otros bloqueos: cada intercalado necesita comprobarlos. Un trigger que permite UPDATE no prueba por sí solo permisos efectivos; el test ilustra el rol y diseño correspondientes, no todas las configuraciones posibles. El trabajo nativo ejecutado en el mismo hilo está incluido en thread CPU; la respuesta no demuestra la causa de la diferencia wall/CPU ni una atribución causal de rendimiento. El rechazo se limita a esta candidata: no demuestra que ninguna optimización sea posible.

No modificaciones productivas ni pruebas nuevas ni mediciones de capacidad. La pausa de MOD08 se conserva. Las propuestas del notebook no constituyen aceptación técnica.
