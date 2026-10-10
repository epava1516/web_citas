# Propuesta de evaluación de GraphQL

Fecha: 2026-10-09. Estado: propuesta independiente, pendiente de lanzamiento manual por instrucción expresa del usuario. Documentar esta propuesta no autoriza su implementación ni la incorpora al goal activo, al backlog contractual o a los criterios de aceptación. No hay ensayo ejecutado ni beneficio medido.

## Objetivo

Evaluar si una consulta GraphQL de revisión paginada de expedientes reduce transferencia y trabajo del servidor frente al recorrido actual. Permitir selección de campos y filtros explícitos puede mejorar esos costes si los resolvers trasladan la selección a consultas y proyecciones eficientes; cambiar el protocolo por sí solo no demuestra una mejora.

## Alcance inicial propuesto

Una consulta de lectura paginada, en una rama independiente, reutilizando los servicios y reglas del proyecto. Conservar la interfaz actual para comparar. La elección de biblioteca, esquema y consumidores se resolverá al lanzar manualmente el trabajo, tras inspeccionar la implementación vigente.

Mantener autorización por sujeto y recurso, aislamiento, sesión/MFA actuales, auditoría de lecturas, límites de página y rechazo controlado de contenido ilegible. Solicitar menos campos no permite omitir la revisión requerida para aprobar un expediente. Las operaciones de aprobación, cierre y descarga quedan fuera del primer ensayo.

Prever límites de profundidad, complejidad y tamaño de página, y evitar consultas repetidas por relación. Los filtros deben tener una lista explícita y respetar permisos antes de devolver contenido o metadatos.

## Comparación y decisión

Usar los mismos expedientes sintéticos, campos, filtros y páginas en ambos recorridos. Medir bytes completos de respuesta, número y tiempo de consultas SQL, memoria y latencia HTTP, distinguiendo construcción del fixture y operaciones del producto. Conservar versión, escenario, resultados y limpieza en el CI propio con PostgreSQL real.

Definir umbrales de mejora y límites de regresión antes de ejecutar la comparación. Verificar permisos, revocación, aislamiento y equivalencia de datos. Ampliar la propuesta solo si la evidencia justifica el coste de mantener otra interfaz; una migración completa requerirá una decisión posterior explícita.

## Estimación preliminar

| Alcance | Trabajo efectivo orientativo |
| --- | --- |
| Diseño de esquema y prueba de lectura paginada | 2–4 jornadas. |
| Recorrido acotado con permisos, consultas eficientes, pruebas y mediciones | 1–2 semanas en total, incluyendo la preparación anterior. |
| Migración de consultas y operaciones de derechos | Varias semanas; estimar después del ensayo y del inventario de consumidores. |
| Migración de todo el proyecto y retirada de interfaces sustituidas | Sin estimación defendible hasta inventariar consumidores y contratos. |

Son estimaciones de planificación, no compromisos ni resultados. Cambios de frontend y de contratos aumentan el alcance.

## Lanzamiento manual y convivencia

Iniciar únicamente cuando el usuario solicite expresamente lanzar esta propuesta. Entonces concretar alcance, base de trabajo, umbrales y plan de verificación antes de implementar. No crear ahora una tarea automática, un goal, una rama ni dependencias.

Puede desarrollarse en paralelo al contrato en una línea independiente, sin cambiar su cola o bloquear su cierre. Las cargas de rendimiento locales deben ejecutarse por separado para evitar interferencias y consumo simultáneo de recursos. El trabajo permanece local, con datos sintéticos y sin publicación, contratación o gasto.

Referencias: [arquitectura vigente](02-arquitectura.md), [contrato de derechos](contratos/10-denuncias-derechos.md), [CI propio](ci-local.md) y [seguimiento del contrato](17-seguimiento-desarrollo.md).
