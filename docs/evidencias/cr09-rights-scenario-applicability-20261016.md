# Aplicabilidad de cuatro escenarios locales de acceso

Se localizaron los artefactos originales en el worktree aislado de censo, sin modificarlo. Se contrastaron journals crudos setup/call/teardown y JUnit1PASS/0errores/fallos/skips por caso, además de ciphertext original y respuesta de revisión frente a las huellas registradas. [Recibo actual](cr09-rights-scenario-applicability-20261016.json).

| Escenario | Ejecución original | Resultado conservado |
|---|---|---|
| Perfil ES | 004843-e61513d6 | PASS |
| Cuenta ES | 005354-cf63c837 | PASS |
| Perfil EN | 005835-fdbd0981 | PASS |
| Cuenta EN | 010219-74be61fb | PASS |

Los seis módulos seleccionados de captura/contenido/registro/cobertura/cierre/entrega siguen idénticos a las huellas de esas ejecuciones. El archivo de test cambió, pero el wrapper positivo permanece idéntico por AST. Al resolver observed_census=False, valor predeterminado que utilizan esos wrappers, el helper también permanece idéntico: todas las adiciones pertenecen a ramas negativas excluyentes de censo observado.

Esto permite reutilizar los recorridos en ese alcance sin repetir cuatro revisiones interactivas. No se han descifrado ni revisado semánticamente otra vez sus contenidos: las [decisiones originales por23fuentes](cr09-historicos-escenarios-revisiones-20261015.json) conservan su alcance finito, con registro fresco, ausencia de snapshots/importaciones declaradas y revisión separada. No inferir que los logs antiguos carezcan de datos personales por UUID, substring o conteo.

El [archivo privado con asociación pendiente](cr09-archivo-privado-http-terminal-20261015.json) sigue siendo un negativo distinto: bloquea cierre409 sin efectos y no puede reinterpretarse como una entrega completa. No se ha añadido un lector universal ni se excluye una fuente necesaria desconocida. La igualdad de seis módulos no demuestra todas las dependencias transitivas o N3 de versión actual.

La revisión del requisito de representación detectó aparte que actor anónimo no implica FKsubjectausente. Se añadió y verificó [la variante sin cuenta vinculada y cierre HTTP](cr09-representation-http-replay-fixed-20261016.md), que también descubrió/corrigió un fallo de replay. No convierte estos cuatro escenarios de acceso en cobertura exhaustiva de todos los derechos/finalidades/canales. Rendimiento y CR09/N3 permanecen abiertos.
