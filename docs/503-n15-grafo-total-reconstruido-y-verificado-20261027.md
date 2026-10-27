# N15 — grafo completo reconstruido y verificado

El 27 de octubre, a las 02:25:42 UTC, terminó la comprobación independiente de la
reconstrucción desde cero prerregistrada en [502](502-n15-prerregistro-reconstruccion-total-grafo-20261027.md).
Base Git `d0152061725a2989e597a3fb8fa489f8ab63e9fb`; aplicación
`48dfad61f71ccd378d5e6ccd979c91d4b7908cc7`. El manifiesto de huellas fija el
working tree efectivo, incluido 502 sin commit al congelar; no se presume un
checkout limpio por citar HEAD. El grafo anterior N11 permanece preservado.

## Resultado y alcance

| Unidad | Corte N11 anterior | Reconstrucción N15 |
| --- | ---: | ---: |
| Fuentes del corpus definido | 2.163 | 2.183 |
| Nodos | 22.125 | 16.711 |
| Relaciones | 87.624 | 75.307 |
| Comunidades | 1.049 | 755 |
| AST nuevo, tiempo observado | Sin testigo comparable | 48,789 s |

Las extracciones semánticas tienen granularidad distinta: estos recuentos no
miden una mejora de rendimiento de la aplicación ni equivalencia nodo a nodo.
No se borraron las fuentes retirando nodos del grafo anterior: se reconstruyó el
corpus definido con entradas nuevas, sin reutilizar nodos ni cachés anteriores.

Se analizaron 1.447 archivos clasificados como código: 11.126 nodos y 56.021
relaciones AST, sin fuentes fallidas. Las 56.021 relaciones se conservaron con
su dirección, atributos originales y multiplicidad, comprobadas contra la salida
AST real. Se identificaron 1.124 referencias sintéticas que la biblioteca produce
sin archivo; se marcan explícitamente, sin tratarlas como declaraciones físicas.

Semántica nueva de 731 documentos/textos, en 30 fragmentos nativos de hasta 25
fuentes, con hashes antes/después y citas ligadas a líneas. Son 2.191 nodos
semánticos, 2.091 relaciones y siete hiperrelaciones. Los agentes trabajaron
en worktrees aislados de salida, leyendo el main actual; los índices vacíos
proceden de su creación `--no-checkout`, no de eliminaciones de fuentes. Root
comprobó HEAD, estado físico y propiedad exacta de sus 60 archivos. Las cinco
matrices JSON seleccionadas se indexaron mediante sus claves, punteros e IDs
originales; I01–I28 y las 443 identidades originales permanecen distinguibles.
Esto no atribuye nuevas pruebas ni PASS funcional a cada acción.

El [certificado compacto](evidencias/n15-grafo-reconstruccion-total-20261027.json)
guarda cortes, huellas, 30 verificaciones, propiedad, incidencias y salidas.
Nuevas invocaciones Claude V1: 0; histórico 8 conservado. N15 lleva 31 tareas
nativas contando el insumo frontend previo. Consumo nativo desconocido: no cero.

## Integridad, exclusiones y presentación

Cero extremos colgantes y cero duplicados exactos de relaciones. Se mantienen 200
referencias estáticas no resueltas y 143 autorrelaciones, sin inventar una
resolución runtime ni eliminar relaciones por su forma. Las 1.592 citas Markdown
fuera del corpus apuntan a archivos existentes excluidos deliberadamente,
principalmente evidencias; no son 1.592 enlaces rotos. Las exclusiones completas
y las referencias constan en CORPUS_POLICY/UNRESOLVED_REFERENCES del grafo.

El JSON conserva 75.307 relaciones; la proyección simple de análisis tiene 72.820.
El HTML representa 755 comunidades y el informe detalla 495, con 260 pequeñas
omitidas de la presentación pero presentes en JSON. Las cohesiones numéricas
permanecen en ANALYSIS.json. El diagnóstico de Graphify compara también un
DiGraph simple: su pérdida potencial de relaciones paralelas no es pérdida del
MultiDiGraph publicado, que se verificó por separado.

La revisión propia corrigió las afirmaciones automáticas del informe derivadas
de esa proyección: confianza real 67.718 EXTRACTED / 7.589 INFERRED, dirección real
de los enlaces de ejemplo y ausencia de conclusión sobre ciclos de importación.
La versión inicial de la proyección no justificaba «100% EXTRACTED» ni «ningún
ciclo». Tampoco se promete coste cero de futuras extracciones. El JSON de nodos
y relaciones conserva la misma huella tras esta conciliación de presentación.

Los hubs medidos incluyen User, unseal, RightsAction, Listing y Person; son
centralidad estática con pruebas incluidas, no una lista de defectos. Por ejemplo,
los enlaces entre pruebas y Category son `uses`, INFERRED 0,95, con dirección desde
la prueba al modelo. Preguntas útiles para el siguiente análisis: dónde se
recomprueba autoridad antes de descifrar/entregar imágenes y cómo se conectan
Person/Listing/Revision con sus pruebas. No prueban por sí solas ejecución real.

Salidas locales retenidas fuera de artifacts: `graphify-out/graph.json`,
`graph.html`, `GRAPH_REPORT.md`, `SOURCE_MANIFEST.json`, `CURRENT_OUTPUTS.json`,
`GRAPH_VERIFICATION.json` y demás metadatos. Son generados locales; el certificado
versionado permite identificar este corte. SHA256 del grafo:
`61eebf1bcfec0a0490c440a8bc1551be85c397294c8e4b7ba1abe897bbd4b4e0`.
El checkpoint N11 anterior tiene SHA256
`33ab425166999f2088acc47a20e34bfe9c0d10ea998ed91f70d7240c6cd78238`.

## Incidencias y continuación

Se conservaron los rechazos de metadatos: campo opcional de consumo, colisión de
IDs entre requirements.in/requirements.lock, referencia AST vacía normalizada
incorrectamente por el adaptador y comparador que descartaba puntuaciones AST
originales. Las dos identidades y ocho extremos afectados se corrigieron por
source_file sin sobrescribir la propuesta original. Los comparadores ahora
conservan las puntuaciones originales y distinguen las añadidas. También se
corrigió la expectativa de checkout completo de los worktrees de salida.
Son incidencias de instrumentos del grafo; no fallos nuevos de la aplicación.
No se repitieron AST/semántica ni las seis pruebas ya válidas del notificador.
Avisos terminales reales, incluidos los rechazos, confirmados por Telegram.

Este corte completa la reconstrucción previa al diferencial, **no N15**.
Siguen diferencial 338/339 y censo, entrega de frontend, conciliación semántica de
los entregables nuevos, acta/Git y purga de artifacts como última operación.
Los nuevos documentos 503/certificado y los cambios documentales posteriores
requieren conciliación explícita; no se finge que existían al congelar el corpus.

Continúan 11/13 aceptados. Se conserva [la deuda viva](deuda-pendiente-viva.md):
N02/MOD09 al final del desarrollo, N12/B14, N13/B15 y N14/B17 condicionados y QA
integral hasta estable. Alpha/noindex, sin abrir beta ni implementar el frontend
futuro. Los brutos bajo artifacts serán referencias históricas tras la purga;
este certificado compacto y el grafo local permanecen fuera de ella.
