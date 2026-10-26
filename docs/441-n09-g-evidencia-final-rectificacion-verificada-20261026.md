# N09G — aceptación local de evidencia final de rectificación

Estado: aceptado localmente en las fronteras verificadas; N09 completo139IDs sigue abierto,8/13bloques obligatorios aceptados. Alpha/noindex, datos sintéticos; no apertura beta. Base28a02db y candidata de un módulo; [prerregistro439](439-n09-g-prerregistro-evidencia-final-rectificacion-20261026.md), [diagnóstico y selección440](440-n09-g-diagnostico-y-correccion-evidencia-final-20261026.md).

Original: run20261026-120035-1594b022,13casos6PASS7FAIL,0ERROR/SKIP,282,230sJUnit;1775huellas estables. Se conservan los fallos originales y los seis controles válidos. Seis retiros de permisos y una caducidad real durante espera PostgreSQL reproducidos: cinco retornos privados antes de denegación tardía, un retorno/Action tras revocar y un borrador con prueba caducada. Son siete condiciones en cuatro operaciones/seis fronteras/una ruta, no siete operaciones, causas raíz o bloques nuevos.

Candidata: run20261026-124639-58873558,18PASS/0FAIL/ERROR/SKIP,337,893sJUnit;1776huellas estables. Runner oficial focused serial, parser nativo, PostgreSQL/Redis propios, limpieza de contenedores/volúmenes/redes/temporal y Telegram terminalPASS comprobados. Auditoría independiente propiaPASS con recibo Telegramsent. Son los13diagnósticos íntegros y cinco originales de cierre/concurrencia/localización; no se repiten F75/E38.

Cambio: sólo apps/safety/rectification_final.py, SHA3d56d2feba96d38c3e74347049d11f26c0574b62e36c7a66a901e0689e5faa4d. Captura llamador, epochs y cuatro roles originales; comprobación fresca tras bloqueos y antes de privados/efectos. Callback vincula prueba original, versiones, asignación y caducidad; se propaga a helpers existentes de F. actor() y firmas públicas intactos. Cierre resuelto mantiene integridad/epochs históricos y autoridad actual sin exigir una nueva prueba activa; concurrencia y replay originales pasan.

## Antes y después

| Condición | Antes | Después | QA antes, s | QA después, s |
| --- | --- | --- | ---: | ---: |
| prepare_review/revocación | PermissionDenied,1 retorno privado | PermissionDenied,0 retornos privados | 17.898 | 18.105 |
| inspect_draft/revocación | success,1 retorno privado | PermissionDenied,0 retornos privados | 17.257 | 18.330 |
| review_draft/revocación | PermissionDenied,1 retorno privado | PermissionDenied,0 retornos privados | 17.332 | 18.884 |
| close_review/revocación | PermissionDenied,1 retorno privado | PermissionDenied,0 retornos privados | 17.090 | 17.567 |
| prepare_account_source/revocación | PermissionDenied,1 retorno privado | PermissionDenied,0 retornos privados | 17.112 | 17.487 |
| prepare_contact_claim/revocación | PermissionDenied,1 retorno privado | PermissionDenied,0 retornos privados | 18.284 | 17.743 |
| prepare_review/caducidad | success,1 retorno privado | ValidationError,0 retornos privados | 27.172 | 27.859 |

Los tiempos son cuerpo de caso QA con saga nativa, espera inducida, snapshots y limpieza. No son latencia de aplicación ni una mejora de rendimiento demostrada; JUnit incorpora además otros costes. El total original13 frente a candidata18 no es una comparación de rendimiento homogénea. Los seis controles legítimos mantienen efectos exactos previstos; los siete negativos deniegan sin efectos ni retorno del target después del evento, con snapshots y archivos intactos. En cuenta se permite entrar al wrapper antes del lock, pero no volver con la proyección privada.

Prueba de caducidad: TTL10s configurado antes de admisión; vigente al observar el bloqueo, vencida por reloj real antes de soltarlo. Todos sus campos y concesiones permanecen idénticos durante la espera; la candidata produce ValidationError antes del target. No se modifica reloj ni datos durante el intervalo.

Revisión propia: Django, acceso y diferencial de seguridad acotados al diff y callers; historia187b8e6/fa81bf6/72ff79a y helperF28a02db contrastados. Informe persistido en artifacts/recorridos-n09-g-20261026/DIFFERENTIAL_REVIEW_CANDIDATE.md. Sin hallazgo adicional confirmado en este diff; no es certificación global. RuffPASS, diagnóstico SHAa8ffcf64e0f411dc0250989628715869e4388e72f2aa0b9baac6ae5ff645172b idéntico antes/después.

Cortes: antes del original, grafo4392074fuentes SHA450e63f7fc232846db595ce0b53b711d3bda2783e8e41db05764e3760f24cda5. Antes de candidata, AST1fuente y semántica selectiva440/17:2075fuentes20186nodos84271relaciones975comunidades SHAb46449dc363cba63da7857efefc99a06ead8177df5870108577b9992474270ef. El cierre documental integra441/17 sin repetir runtime. Son deltas focales, no reconstrucciónN15 ni semántica exhaustiva;111 se preserva.

Límites: servicios nativos y fronteras privadas seleccionadas; sin nuevo testigo HTTP, worker ni proveedor real. El adaptador de prueba de identidad sigue sintético, no verificación productiva. Evaluación/revisión de destinatarios usada como fixture conserva pendientes propios. Otras ramas tardías, purgas/outbox/jobs y conciliación139IDs permanecen abiertas; N02restante al final, N10/N11/N15pendientes, N12–N14condicionados. A–F26puntos locales retenidos; G añade cuatro operaciones de una ruta con siete condiciones, sin equiparar puntos, casos,IDs y bloques.
