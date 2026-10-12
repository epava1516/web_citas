# MOD-08 VPS: lectores por conjunto y medición HTTP, 2026-10-12

## Veredicto

FAIL válido por seis incumplimientos de latencia; no aceptación global/N3.
El cambio del codec y los lectores SQL muestra una reducción observada de aproximadamente
7,7 % en navegación y 8,8–9,6 % en JSON; binario prácticamente igual. La prueba JUnit
completa baja 90,260 s (4,40 %). No se atribuye toda la diferencia a los lectores ni
se prueba causalidad aislada de cada cambio; una sola comparación antes/después,
imagen reconstruida distinta y posible variabilidad del host. No repetir un FAIL.
El diagnóstico separado posterior sí termina y pasa, sin alterar ni ocultar el fallo.

SHA medido: `388c991dd9158da13c0fb522578335ac464b1d3d`, incluye
`c46d0e101e8f260493a53bd4617b54dd4f0171f5`. Branch aislada
codex/mod08-vps-server-20261012; trabajo original del usuario preservado.
[Fase funcional, fallos de preparación y diseño](mod08-vps-lectores-conjunto-20261012.md).

## Comparativa contractual

Referencia8CPU: 20261012-023609-aa06db69, anterior al codec y a los lectores nuevos.
Actual: 20261012-125702-b2d8dd6f; 384 navegaciones y20 descargas por tipo en cada
uno de dos casos simultáneos. Descargas incluyen POST de autorización + GET.

| Caso/etapa p95 | Referencia | Actual | Reducción observada | Límite |
| --- | ---: | ---: | ---: | ---: |
| A navegación cobertura | 3,523783 s | 3,251440 s | 7,73 % | 2 s |
| B navegación cobertura | 3,547708 s | 3,275722 s | 7,67 % | 2 s |
| A JSON | 7,115129 s | 6,486092 s | 8,84 % | 5 s |
| B JSON | 7,060256 s | 6,379550 s | 9,64 % | 5 s |
| A binario | 7,099972 s | 7,064550 s | 0,50 % | 5 s |
| B binario | 7,011104 s | 7,070781 s | −0,85 % | 5 s |
| Prueba completa JUnit, incluye preparación/tramos | 2050,766 s | 1960,506 s | 4,40 % | — |

Lanzador actual: 12:57:01Z–13:31:26Z,2065s. Es otro intervalo que JUnit;
no compararlo con la duración JUnit antigua. No cifras del portátil: alternaba
cargador/perfil energético y no permite atribuir esas diferencias al código.

| Peor caso actual | p95 | Objetivo | Reducción pendiente |
| --- | ---: | ---: | ---: |
| Navegación | 3,275722 s | 2 s | 1,275722 s |
| JSON | 6,486092 s | 5 s | 1,486092 s |
| Binario | 7,070781 s | 5 s | 2,070781 s |

Los percentiles se recalcularon de las muestras, no del log Gunicorn. El log se leyó
únicamente como progreso desde el PID propio, sin SQL ni nuevos perfiles/spans.
La auditoría independiente confirma tamaños (~16MiB/64MiB),384/20/20 muestras,
solapamiento de intervalos por pareja,303→200 y cuerpos≤8MiB, ausencia de errores
de carga, salida Gunicorn0 y ausencia de perfiles/timings añadidos. ZIP/digests/
datasets se verifican en ambos workers aun cuando los límites de tiempo fallen.

## Entorno, versiones, recursos y limpieza

VPS OpenStack8CPU disponibles, Linux5.14/el9,glibc2.34, guest Haswell sin SHA-NI;
no se concluye que hardware sea la única causa. Python3.12.15, Django5.2.17,
psycopg3.3.6, cryptography50.0.2, orjson3.13.0, blake3 1.0.11, PostgreSQL17.11.
Dependencias congeladas; kernel native-sealed sin fallback y SHA binario
`ca3c388585ed10a6f5ca3f5e82aeea385c5c496368e3800b45758df6fa2a0726`.

Topología y controles reales:8CPU/8GiB agregados, storage propio≤20GiB, swap0;
workersGunicorn2sync. Pico superior propio4191248384bytes (<6GiB), noOOM/swap.
No PSI CPU/memoria disponible: no es cero presión medido. Metadatos/cgroups quedan
conservados; no se atribuye el tiempo de consulta o pared a CPU pura.

Imagen app `sha256:ecb4b179802ddef908a86d0379dcb8022fbbf20756d35c2de7ee92be33c0d9b4`;
no es el ID de la primera referencia8CPU. El código/interprete real se montan
readonly desde el worktree/uv; SHA y manifiesto congelado son la referencia del
código medido. Identidades PG/Redis/RustFS/Caddy completas y cuotas efectivas en
[evidencia estructurada](mod08-vps-medida-lectores-20261012.json).

| Fase/ID | Resultado JUnit | Duración JUnit | Veredicto |
| --- | --- | ---: | --- |
| preflight 20261012-125018-e52e94f1 | 1PASS/0FAIL/error/skips | 70,575 s | READY_NOT_CAPACITY |
| probe 20261012-125409-f94d14dc | 1PASS/0FAIL/error/skips | 39,980 s | NATIVE_INSTRUMENT_PROBE_NOT_CAPACITY |
| measure 20261012-125702-b2d8dd6f | 1FAIL/0error/skips | 1960,506 s | FAIL_DELIVERY_STAGE_LIMITS |
| diagnose SQL 20261012-133355-c56f5505 | 1PASS/0FAIL/error/skips | 771,444 s | SQL_PLANS_DIAGNOSTIC_NOT_CAPACITY |

En las cuatro ejecuciones:1418fuentes idénticas antes/después/archivo,manifest
`e0e8d06c116cb2530ce6e15f7092e1612b18880de2bb7c455f9b129afd7d275d`,
archivo íntegro sin problemas y cleanup independiente PASS de contenedores,
redes y volúmenes exactos. No servicios productivos ni datos reales; fixtures
con verificador simulado explícito. No publicación, proveedor ni push externo.

## Diagnóstico posterior y dirección técnica

[Planes y comparativa SQL actual](mod08-vps-planes-lectores-20261012.md) acreditan
outputs exactos y ahorro real en historia grande, con sobrecoste en conjuntos
pequeños. No son p95 ni una suma de validación completa. No se encadena otra
microoptimización o ensayo; primero definir el beneficio de los controles caros.

La solicitud posterior del usuario abre la [auditoría de ROI/sobreingeniería](mod08-auditoria-roi-20261012.md):
conservar garantías útiles, distinguir obligación legal de mecánica técnica y
revisar repetición/amplitud antes de acelerar más trabajo. Las propuestas no
se aplicaron durante el ensayo ni rebajan automáticamente el contrato.

Limpieza final:0entornos de capacidad activos. Retirada sólo la referencia temporal
web-modelos-app:latest, comprobada previamente como imagen propia ecb4; conservada
web-modelos-mod08-vps:84f1886-20261012 y su mismoID. Sin prune ni servicios ajenos.
Antes de un futuro runner, comprobar que latest sigue ausente y retaggear esa
imagen propia (mismoID), sin sustituir una referencia creada por otro proceso.
Recibo:artifacts/vps-preparation/sql-bulk-final-cleanup.json.
