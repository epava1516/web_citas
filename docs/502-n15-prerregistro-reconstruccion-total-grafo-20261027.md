# N15 — reconstrucción completa del grafo

Base de preparación `d0152061725a2989e597a3fb8fa489f8ab63e9fb`, aplicación
`48dfad61f71ccd378d5e6ccd979c91d4b7908cc7`. El grafo previoN11 está preservado
fuera de artifacts en `graphify-out/history/pre-n15-20261027`.
No se reutilizarán nodos, relaciones ni cachés de extracción del grafo anterior.
Se conserva por separado su procedencia y coste histórico disponible.

## Corpus y método

Detección inicial Graphify: 2.160 archivos, aproximadamente 1.421.197 palabras;
1.447 clasificados como código y713 como documentos. Es un corpus grande:
la extracción semántica tiene un coste considerable. Predominan docs, tests,
apps, templates y scripts; el alcance final se fijará en un manifiesto con hashes.

La detección omite por nombre `templates/core/token.html` y
`templates/core/token_invalid.html`. Se inspeccionarán como plantillas de
aplicación, sin credenciales, antes de incluirlas explícitamente. Los archivos
textuales de configuración y dependencias que Graphify deja sin clasificar se
inventariarán explícitamente; el archivo `.git` es un puntero y queda excluido.
Se seleccionarán las matrices JSON necesarias para preservar identidad de
acciones, inventario y aceptaciones, sin incluir todos los brutos históricos.

Exclusiones: Git, entornos/cachés, .ai, artefactos, datos/media, binarios,
node_modules, vendor, grafo generado e histórico repetido del seguimiento.
`docs/evidencias` no se incorpora en masa: sus matrices seleccionadas se
identifican individualmente. AGENTS y archivos de versión vendorizada pueden
registrarse como contexto explícito; no se atribuirá análisis de código minificado.
El manifiesto final declarará todas las inclusiones, exclusiones y categorías.

AST nuevo sobre fuentes actuales, con caché de extracción nueva y vacía.
Documentos y configuración: extracción semántica nueva mediante agentes nativos,
fragmentos de20–25 archivos, relaciones selectivas con citas/localización y
confianza. No es una transcripción exhaustiva de cada afirmación. Cada fragmento
es una propuesta hasta validar identidad de fuentes, esquema, citas y extremos.
No se declararán tokens cero por falta de contabilidad: consumo nativo desconocido.
No hay nuevas invocaciones ClaudeV1; se conserva su histórico.

Se distinguirán imports/referencias estáticas de enlaces de ejecución resueltos.
Las referencias no resueltas conservarán estado explícito; no se inventarán
extremos de código reales para eliminarlas. Verificar cobertura del corpus,
fuentes estables, integridad de nodos/relaciones, comunidades y salidas. HTML
será una proyección por comunidades, porque el grafo supera5.000 nodos; no una
vista exhaustiva de todos ellos. El JSON y el informe conservarán alcance y límites.

## Orden de entrega y límites

Reconstrucción completa antes del diferencial338/339 y censo, preservando111 y
los IDs originales. Después se integrarán los entregables nuevos en la semántica
sin fingir otra reconstrucción completa ni borrar su procedencia. El relevo de
frontend distinguirá código esperado, ramas observadas y ramas no ejecutadas.
La constancia final de purga, por ser posterior, acreditará su ejecución: este
grafo sólo describe la obligación y su estado pendiente antes del borrado.

No se repiten QA válidas ni se ejecutan pruebas globales por reconstruir el grafo.
No hay cambios de aplicación, migraciones, servicios, CI ni conexiones nuevas.
Los agentes sólo leen el corpus y devuelven propuestas; root verifica e integra.
Alpha/noindex, N15 abierto y11/13 aceptados. Se conserva la
[deuda viva](deuda-pendiente-viva.md); los condicionados no son PASS.
