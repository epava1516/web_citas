# N15 — preparación de la entrega de frontend

Continúa [505](505-n15-inventario-diferencial-verificado-20261027.md), conforme
al cierre y su adición de frontend en [340](340-contrato-recorridos-optimizacion-alpha-20261025.md).
Base documental y Git: `f9a01fbd3fe2ea057f0c9c1bfa334e85414bf621`;
último cambio de aplicación: `48dfad61f71ccd378d5e6ccd979c91d4b7908cc7`.
Worktree: `/home/felidae/proyectos/web_modelos_mod08_vps`, rama `master`.

El grafo se concilió antes de este hito con las 444 unidades actuales y los
443 IDs originales: 2189 fuentes, 17188 nodos y 76824 relaciones; SHA256
`ee2728bf76529b522e9fbf7083d1ca5b7a6acffa8c42e48acd90b87de90bc6a6`.
La extracción completa anterior permanece preservada y no se repetirá.

## Alcance y criterios

Consolidar los insumos estáticos ya contrastados contra fuentes: 170 handlers,
634 definiciones en sus cierres de dependencias, 687 retornos exteriores,
110 formularios, 36 reglas globales y 129 plantillas propias. Conservar las
condiciones, entradas, declaraciones de campos y modelos, reglas dinámicas,
decoradores, excepciones, candidatos a efectos/despachos, fragmentos y JavaScript.
No confundir candidatos con efectos comprobados ni retornos de helpers con
respuestas HTTP. Los 16 patrones del Admin nativo son una superficie distinta.

El resultado esperado se vinculará a la fuente y su huella. Las observaciones
previas se referenciarán con versión y alcance desde el inventario vigente;
no se asignará un estado HTTP observado a una rama específica sin testigo que
lo demuestre. Los valores efectivos desconocidos conservarán esa condición.
Los valores dinámicos se describirán por reglas y ejemplos sintéticos, sin
consultar datos reales. Las constantes del framework, si se incorporan, se
contrastarán con el Django 5.2.17 instalado y sólo probarán valores por defecto
de constructores, no la respuesta final tras wrappers o middleware.

Guardar la entrega técnica fuera de `artifacts`: los datos compartidos podrán
deduplicarse con referencias internas reversibles, comprobando reconstrucción
exacta contra los insumos verificados. Las rutas históricas a temporales o
artefactos serán procedencia, nunca dependencias necesarias para leer la entrega.
Vincular cada ruta a su ID y fuentes actuales, formularios y plantillas; preservar
por separado métodos admitidos explícitamente y condiciones léxicas.

Revisar los cambios propios y comprobar correspondencia, integridad de fuentes,
ausencia de pérdida al deduplicar y enlaces pertinentes con aviso Telegram.
Estas comprobaciones documentales no acreditan QA de la aplicación. No repetir
pruebas aceptadas ni iniciar batería global, navegador, servicios o migraciones.

## Límites y cierre

La entrega mantendrá permisos, CSRF, consentimientos, validación, revocación,
moderación, tareas y accesibilidad como garantías a conservar. El futuro contrato
implementará UI/UX con Django Templates y dirección htmx4; la versión actual
sigue siendo 2.0.11. No se ejecuta aquí esa reescritura ni se instalan sus skills.

N15 continúa abierto. Después de publicar la entrega: conciliación semántica
del grafo, verificación documental, acta y Git, resumen duradero y purga íntegra
de `artifacts` como última operación. Conservar [deuda viva](deuda-pendiente-viva.md),
incluidos N02, N12–N14 y QA general aplazado, con alpha/noindex.
