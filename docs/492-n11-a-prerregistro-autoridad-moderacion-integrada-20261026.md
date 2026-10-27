# N11A — prerregistro de autoridad de moderación durante espera

N11 comienza sobre `1d2703d`, producto integrado sin cambios desde `0dcf89f`. N10 aceptado en491;10/13, alpha/noindex. N02 residual pospuesto al final del desarrollo, N12–N14 condicionados. N11 no se acepta por cerrar una duda: todavía requiere matriz de integración y regresión común pertinente de I01–I28, conciliación de fuentes, negativos, omisiones y recursos.

## Corte y preguntas

Grafo previo verificado:2152 fuentes,21535 nodos,87058 relaciones,1042 comunidades, SHA926a4e9b1e7dff69c758deb2aafd292172eed934fd46acab24b6e4cb92706950. Consulta decide/resolve y autoridad contrastada con apps/listings/moderation.py, match_review.py, sus vistas y fixtures nativas. El delta siguiente incorpora el nuevo instrumento AST y este prerregistro literal antes de congelar fuentes; no reconstrucción completa N15 ni cobertura semántica exhaustiva.

El acta472 reservó moderation.decide y match_review.resolve como incertidumbres de fuente, sin afirmar vulnerabilidad. Ambas vistas revisan permiso/MFA antes del servicio; ambos servicios consultan el User admitido antes de adquirir locks de persona/listing/target. Falta comprobar si retirar review_listing mientras se espera realmente en PostgreSQL evita la decisión. Una sospecha de caché no sustituye la reproducción.

## Cuatro escenarios y oráculos

Nuevo tests/test_moderation_authority_wait.py: cuatro casos seriales, dos POST nativos (rechazo de revisión pendiente y resolución conflict de pareja de fotografías), cada uno con control válido y retirada del permiso directo durante espera Person. Fixtures existentes pending/conflict preparan el dominio por flujos nativos, sin contenido real ni proveedor. Sesión admitida con force_login y epochs cuenta/MFA explícitos; no nueva ceremonia password/TOTP/CSRF. Las garantías generales siguen en sus testigos previos.

Observer puro en la entrada de servicio de la vista: siempre reenvía el original; registra permiso inicial efectivo/caché/actor y PID. Holder propio mantiene Person FOR UPDATE; pg_blocking_pids recursivo debe demostrar el bloqueo del PID real del POST, distinto al holder. Sólo entonces se retira el permiso si corresponde, se confirma autoridad fresca y se captura baseline completo dentro de la transacción. El commit de holder hace efectiva la retirada antes de continuar. No sleep como prueba de carrera ni permiso simulado.

Esperado: control302 con efecto nativo exacto; revocado403 y ningún efecto. Comparar todos los modelos/through y archivos del MEDIA_ROOT por hash/metadata, incluyendo sesiones, tablas auditadas y grants. Rechazo: un ModerationDecision del actor/target/outcome/reason y revisión/status/timestamp, listing rechazado/lifecycle+1 cuando procede. Conflicto: dos MatchResolution de la pareja, dos restricciones del target/decisión/persona/manager, matches/version/timestamps y listing/lifecycle/pausa; ningún otro campo/modelo/archivo. La retirada intencionada del permiso está incluida en baseline y no se cuenta como efecto de la petición.

Guardar antes de afirmar expectativas el HTTP real, espera, identidad/caché inicial, snapshot-digests, forma exacta o ausencia de efecto, cantidad de modelos y continuidad de archivos. No cuerpos, cookies, credenciales ni IDs privados en propiedades/Telegram. statement_timeout10s, PID queue8s, observación de bloqueo5s y future15s; cierre conexiones y pool en finally, cancel sólo conexión propia si sigue pendiente. Los tiempos incluyen fixture/espera/oráculos y son QA, no latencia ni optimización.

## Ejecución y decisiones

Revisión focal Django/autorización/seguridad del instrumento, Ruff y grafo antes de freeze. Runner oficial focused,1worker, PostgreSQL17/Redis7.4 propios, parser nativo, timeout600s. Congelar fuentes, dependencias, migraciones, instrumentos y grafo, IDs imágenes antes de lanzamiento y contrastar contra contenedores por PID/start_ticks. Cleanup propio y Telegram terminal confirmado. Sin cambio de aplicación hasta observar resultado original; cualquier FAIL/ERROR/SKIP se conserva y no es aceptación.

Si hay fallo real, diseñar corrección acotada y revisar variantes del mismo origen, repetir originales sin alterarlos junto a negativos pertinentes. Si no, documentar alcance acreditado. Posteriormente N11 conciliará todos los bloques y seleccionará regresión común por comportamiento/riesgo y cambios actuales, reutilizando testigos válidos con identidad explícita. Sin campaña de optimización QA, proveedores, servicios, migraciones persistentes o ampliación contractual.
