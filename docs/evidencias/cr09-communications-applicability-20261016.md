# Comunicaciones: identidad de fuentes y fases existentes

Corte e5cc7e3. Auditoría reproducible en `artifacts/cr09-communications-applicability-20261016/audit.py`; [recibo](cr09-communications-applicability-20261016.json). No se han ejecutado pruebas nuevas.

| Archivo actual idéntico | Ejecución de referencia | Casos setup/call/teardown PASS |
|---|---|---|
| test_notice_operations.py | 20261015-010758-a635c22e | 7 |
| test_historical_communication_candidates.py | 20261015-010758-a635c22e | 1 |
| test_rights_communications_localization.py | 20261015-010758-a635c22e | 2 |
| test_rights_notice_inventory.py | 20261015-024508-162c33cd | 2 |
| test_rights_communications.py | 20261015-092133-69b50022 | 6 |
| test_notice_delivery.py | 20261015-081053-9720829d | 6 |
| test_recipient_notice_revocation_races.py | 20261016-035615-b6d4e2ac | 10 |
| test_account_recipient_notice_revocation_races.py | 20261016-053617-156708a7 | 20 |
| test_editor_recipient_notice_revocation_races.py | 20261016-054713-fd15186b | 6 |

Los seis módulos directos de comunicaciones, vistas, entrega y operaciones coinciden con los manifiestos contrastados. No se deduce identidad de todas las dependencias transitivas. La prueba actual de comunicaciones difiere de la del bloque4: se usa su correctiva posterior69b50022 con los seis casos, no el archivo anterior.

Se conserva la distinción entre buzón interno real y adaptador de outbox explícitamente simulado. Sus fallos/reintentos no acreditan recepción externa. La conciliación previa de cuenta y las pruebas de revocación de perfil/editor siguen siendo evidencia de sus alcances; este inventario no amplía esos alcances ni añade un producto cartesiano de requisitos.

Los bloques3 y4 originales terminaron ERROR y después pasaron selecciones afectadas. No afirmar cuatro bloques PASS ni N3 común a partir de esa suma. Pendientes: aplicabilidad de dependencias cambiadas a la versión final, ensayo integrado común y criterios restantes de matriz83. Último p95 limpio0,862172866sFAIL, sin nueva medición. CR09 permanece abierto.
