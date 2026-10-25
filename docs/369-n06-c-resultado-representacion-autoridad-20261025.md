# N06C — referencia de representación, autoridad y revocación

25 de octubre de 2026. [Prerregistro368](368-n06-c-prerregistro-representacion-autoridad-20261025.md), candidata instrumental a5a0555, run20261025-154544-5fcdc190. **2 PASS, 0 FAIL/ERROR/SKIP**,44peticiones observadas, fuentes congeladas intactas1735huellas. Ningún cambio de aplicación. N06abierto,alfa; N02restante diferido por decisión expresa367.

## Referencia por operación

Una observación por transición/ordinal, etapa Client.request instrumentada. La referencia anterior equivalente no estaba medida; no se inventa un antes ni un porcentaje. Son variantes distintas: no se agregan las peticiones de dos sujetos para afirmar una mediana/p95. Filas seleccionadas del primer caso; las44operaciones completas están en la [auditoría](evidencias/n06-c-representacion-auditoria-20261025.json).

| Acción / ordinal | Antes equivalente (ms) | Referencia actual (ms) | SQL actual | Mejora atribuible |
| --- | ---: | ---: | ---: | --- |
| Añadir primer representado / 3 | No medido | 30.534 | 10 | No evaluable |
| Invitar consentimiento primero / 4 | No medido | 76.133 | 17 | No evaluable |
| Aceptar consentimiento primero / 5 | No medido | 49.788 | 17 | No evaluable |
| Edad local primero / 6 | No medido | 66.556 | 28 | No evaluable |
| Iniciar teléfono primero / 7 | No medido | 29.620 | 17 | No evaluable |
| Confirmar teléfono primero / 8 | No medido | 62.278 | 21 | No evaluable |
| Asignar editor primero / 9 | No medido | 31.946 | 12 | No evaluable |
| Añadir segundo representado / 15 | No medido | 25.270 | 10 | No evaluable |
| Invitar consentimiento segundo / 16 | No medido | 25.772 | 14 | No evaluable |
| Aceptar consentimiento segundo / 17 | No medido | 47.753 | 17 | No evaluable |
| Edad local segundo / 18 | No medido | 60.079 | 25 | No evaluable |
| Iniciar teléfono segundo / 19 | No medido | 26.154 | 14 | No evaluable |
| Confirmar teléfono segundo / 20 | No medido | 92.632 | 33 | No evaluable |
| Editor sin asignación: inicio denegado404 / 21 | No medido | 32.306 | 5 | No evaluable |
| Revocar representación primero / 35 | No medido | 148.059 | 44 | No evaluable |

La segunda prueba conserva el bloqueo MFA y la revocación de membresía:

| Transición / ordinal | Antes equivalente (ms) | Referencia actual (ms) | SQL actual | Estado |
| --- | ---: | ---: | ---: | ---: |
| Editor sin MFA / 1 | No medido | 9.900 | 5 | 302 |
| Editor asignado con MFA / 2 | No medido | 130.527 | 33 | 200 |
| Otro representado denegado / 3 | No medido | 16.351 | 5 | 404 |
| Pausar con asignación / 4 | No medido | 163.392 | 46 | 302 |
| Leer tras revocación / 5 | No medido | 11.795 | 5 | 404 |
| Reanudar tras revocación / 6 | No medido | 12.588 | 5 | 404 |
| Propietario reanuda / 7 | No medido | 238.091 | 70 | 302 |

El reloj incluye middleware/render y SQL de esa conexión; no incluye servicios directos fuera de Client, navegador/TCP, otros procesos ni revisión humana. La primera creación de agencia739,273ms y las subidas1103,039/685,677ms permanecen en la evidencia; no se eliminan por ser mayores. Las tareas eager de la fixture están incluidas donde ocurren dentro de la petición y no acreditan cola real. La referencia encolada359 conserva su propio ámbito. Identidad y teléfono son sintéticos: no proveedores reales ni latencias externas.

## Corrección y recursos

El envoltorio solicita la fixture dentro del cuerpo y llama a los oráculos originales completos sin copiar sus aserciones. Se observaron37peticiones del flujo de agencia y7de MFA/asignación/revocación. Ninguna excepción ni error del observador, métricas finitas/no negativas y conteos íntegros. Se preservaron teléfono compartido con sujetos separados, editor sólo asignado al primero,403de moderación para propietario/editor, publicación independiente, retirada del primer perfil sin afectar al segundo y versión de lifecycle intacta ante operaciones del editor revocado. La verificación local de edad/teléfono sigue siendo simulada.

Runner oficial serial con PostgreSQL17/Redis7.4 propios, dependencias bloqueadas y herramientas nativas con commits/SHA en auditoría. No cuotas dedicadas, carga ni garantía de capacidad. Fuentes intactas hasta auditoría; consulta independiente de etiquetas: cero contenedores/redes/volúmenes; temporal retirado. Telegram terminal del runner y de la auditoría enviados. Lint inicialI001 del nuevo instrumento corregido; FAIL inicial yPASS posterior conservados en recibos, sin repetir pruebas funcionales válidas.

Tiempo QA separado: pytest54,28s de consola, JUnit54,110s y paso del runner56,587s; incluyen preparación y aserciones. No se usan como latencia de aplicación. La [reproducción](evidencias/n06-c-representacion-reproduccion-20261025.tar.gz) conserva fuentes/instrumento/congelación, sin logs privados.

## Disposición y siguiente contraste

Esta pasada aporta la base actual de representación que faltaba; no acredita optimización ni cierre íntegro deN06. Permanecen variantes de cuenta/panel y crecimiento por conciliar. La inspección del panel de agencia encuentra acceso a member.user.email dentro del bucle de memberships sin select_related en su queryset: hipótesis de coste lineal por editor, todavía sin medición ni candidato aceptado. El siguiente lote debe medir cohortes y paridad de propietario/editor/retirada antes de cualquier cambio; no atribuir el coste de subidas eager al panel ni abrir el contrato de optimización general de QA.
