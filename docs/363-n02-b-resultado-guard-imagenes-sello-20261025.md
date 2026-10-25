# N02B — guard de imágenes con sello válido: corrección y coste

25 de octubre de 2026. [Protocolo362](362-n02-b-prerregistro-guard-imagenes-sello-20261025.md). Fuente de aplicación candidata4a83fe6, intacta en69e4d41; repetición20261025-131908-9c8862ce: **2PASS/0FAIL/ERROR/SKIP**,12muestras. Se conservan14oráculos originalesPASS del intento20261025-130439-39bc72b1 con identidad de aplicación/dependencias/cuerpos comprobada. **16casos distintos cubiertos por dos ejecuciones; no una batería de16PASS.** [Auditoría conjunta](evidencias/n02-b-guard-auditoria-20261025.json), [reproducción/evidencias](evidencias/n02-b-guard-evidencia-20261025.tar.gz), [congelación corregida](evidencias/n02-b-prerregistro-v2-congelacion-20261025.json). N00/N01aceptados2/13,N02/N06abiertos,alfa.

## Cambio y tabla anterior/candidato

Sólo _verify_current_images cambia de image_content por declaración a image_contents y zipstrict. El resto del módulo tiene ASTidéntico: no se modifica validador completo, sello/replay, autoridad, caducidad, objetos, snapshots, auditorías o transacción. La huella normal de código invalida sellos anteriores al cambio. [Alcance exacto](evidencias/n02-b-candidato-alcance-20261025.json). Guard anterior congelado byteexacto de6bffd48, con decorador equivalente; mismo caso/exportación/archivos/proceso y reloj por guard real alcanzado después de holds/replay. DEBUGFalse antes de generar; seis parejas alternas,primera aparte,cinco posteriores.

| Medida de esta etapa con2imágenes | Anterior | Candidato | Diferencia observada |
| --- | ---: | ---: | ---: |
| Primera llamada instrumentada | 39.813ms | 23.486ms | 16.327msmenos |
| Mediana5posteriores | 30.659ms | 23.557ms | 7.102msmenos (23.165%) |
| Rango5posteriores | 24.546–56.465ms | 17.234–41.294ms | Rangos solapados |
| SELECTporguard | 7 | 4 | 3menos (42,857%) |
| Lecturas/hash completos porguard | 2 | 2 | 0 |
| Bytes comprobados porguard | 10554 | 10554 | 0 |

La mediana observada baja, pero dos de las cinco parejas posteriores empeoran:8,480ms y7,191ms. **Resultado temporal inconcluso** por variabilidad;354 impide convertirlo enPASSde latencia o aceptar una mejora temporal. CosteSQLy corrección local sí verificados. El candidato conserva pendiente contraste temporal antes de adopción, además de medición del flujo completo. No se afirma23,165% de mejora estable, p95/p99 ni ganancia de descarga. Son dos archivos pequeños;361con16WebP/~64MiB compara primitivas existentes y no sustituye esta etapa integrada ni MOD09. No se cambia2s/5s ni FAIL/excepción provisional.

## Testigos reales y límites

Preparación sintética mediante servicios nativos de selección de dos imágenes distintas en orden inversoPK, inspección/aprobación/cobertura/generación. Se amplía sólo la receta de fixture binaria; ninguna función de autoridad, holds/replay o validador se sustituye por éxito falso. La verificación externa de identidad sigue siendo el simulador explícito histórico de la fixture, no proveedor real.

Antes de cada guard medido, otro backend PostgreSQL intentaNOWAIT sobre los2Blob y2Photo y recibe55P03 con rollback acotado por fila: cuatro bloqueos ya adquiridos antes del guard. Son48testigos de fila en las12invocaciones,fuera de sus relojes. No prueba ausencia universal de deadlocks ni concurrencia de sujetos o carga; sí confirma la hipótesis de replay para este caso real. Cada guard relee ambos archivos, verifica hashes y orden; no caché de bytes/metadatos entre invocaciones.

Negativo nuevo: mutar el último archivo manteniendo cabeceraWebP/metadatos; llegar al guard con sello válido,observar los cuatro bloqueos y las dos lecturas, rechazar digest y conservar contadores de acciones/descargas. Restauración en finally y validación posteriorPASS. Los14oráculos originales conservan generación/sello, ocho alteraciones de evidencia, caducidad/reglas, pipeline frente a sesión/cifrado/fuente y drift físico entre hijos con rollback de auditorías. No sustituye autorizaciónHTTP o entrega completa.

## Fallos conservados y auditoría

El [intento inicial](evidencias/n02-b-intento-inicial-20261025.json) fue14PASS/2FAIL,sin muestras aceptadas: las dos asignaciones redundantes de DEBUGFalse después de generar añaden otraUserSettingsHoldery cambian la enumeración de rule_version. [Reproducción aislada Django](evidencias/n02-b-configuracion-reproduccion-20261025.json): valores efectivos iguales,ocurrenciasDEBUG2→3. Se retiran sólo esas dos asignaciones; no se debilita holds ni su huella. Se preservan ambosFAIL y se repiten sólo los dos casos nuevos;14positivos reutilizados con hashes de aplicación,dependencias,oráculos/imágenes y versiones nativas contrastados.

Auditoría: selección exacta16casos distintos,48eventos del intento inicial y6de repetición; sólo dos callFAIL iniciales,restoPASS.12muestras finitas/pares completos,baseline literal575bytes/SHAexacto,7→4SQL,2lecturas/mismo volumen/digest y4locks porguard. Fuentes congeladas intactas antes de documentar; contenedores propios y temporales de ambos runs retirados, avisos terminalesTelegramsent. Pytest repetición81,12s/comando83,539s; inicial328,02s/comando330.274s. TiempoQA separado de latencia.

## Disposición y siguiente trabajo

Corrección funcional y coste determinista del candidato verificados localmente; aceptación temporal/adopción pendientes por ruido observado. Próximo contraste debe prerregistrar cómo reduce esa incertidumbre, sin elegir parejas favorables ni repetir los14controles válidos sin cambios. Después atribuir cobertura/entrega y evaluar el escenarioMOD09 completo con sus objetivos, crecimiento y concurrencia;N02no se cierra. N06cuenta/representación/crecimiento y demás bloques siguen obligatorios conforme a341;N12–N14no activados. Sin publicación/proveedores/datos reales.
