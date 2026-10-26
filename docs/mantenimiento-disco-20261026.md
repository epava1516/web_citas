# Mantenimiento de disco — 2026-10-26

Solicitud del usuario: revisar acumulación de imágenes y limpiar el disco raíz.
Worktree activo: `/home/felidae/proyectos/web_modelos_mod08_vps`.

| Medida | Antes | Después |
|---|---:|---:|
| Ocupación de raíz (`df`, redondeada) | 98 % | 81 % |
| Espacio disponible | 5,19 GiB | 39,74 GiB |
| Copias temporales de evidencias retiradas | 0 | 78 |

Ganancia real observada mediante statvfs: **37.093.126.144 bytes (34,55 GiB)**.
No es una estimación obtenida sumando tamaños de directorios.

Se retiró únicamente `docs/evidencias` de 78 worktrees temporales inactivos,
mediante sparse-checkout. Antes se comprobó ausencia de referencias de procesos y
montajes Docker, identidad de cada archivo con su objeto Git recuperable y ausencia
de cambios propios en esa carpeta. HEAD, estado Git y hashes de los cambios de
cada worktree se conservaron. No se eliminaron worktrees, fuentes modificadas,
artefactos únicos ni las evidencias originales del worktree activo.

Cada entrada de `artifacts/maintenance-disk-20261026/cleanup-summary.json` incluye
su comando de recuperación: `git -C <worktree> sparse-checkout disable`.
Restaurar las 78 copias consumiría de nuevo el espacio liberado. Para futuros
worktrees de trabajo, excluir desde su creación las evidencias históricas cuando
no sean necesarias, preservando siempre cambios y referencias activas.

Docker tenía unos 618 MB recuperables en imágenes y ninguna caché de construcción.
No se ejecutó prune, no se borraron volúmenes ni se detuvieron servicios.
Se conservaron los artefactos únicos, incluido image.tar.

Dockerfile usa `COPY . /app`. Se añadió a `.dockerignore` la exclusión de
`docs/evidencias/*`, con tres excepciones para manifiestos referenciados por
scripts del proyecto. Las reglas anteriores se mantienen. La revisión estática
no encontró dependencias de esa carpeta en apps/config; se conservaron los
manifiestos usados por las herramientas. El tamaño lógico excluido queda en
`artifacts/maintenance-disk-20261026/final-review.json` (aproximadamente 581 MiB).
No se construyó una nueva imagen: esta cifra mide archivos excluidos del contexto,
no una reducción observada de tamaño de imagen ni de tiempo de construcción.

Auditoría local: `artifacts/maintenance-disk-20261026/`, con inventarios, corte del
grafo consultado, plan, comprobaciones por archivo, resultados y recibos Telegram.
Las modificaciones laterales existentes se conservaron y no se incorporaron a
ningún commit. Contrato, avance, alpha/noindex y evidencias QA permanecen vigentes.
El grafo consultado corresponde al corte previo al cambio de `.dockerignore`;
este delta y este documento deben incorporarse antes del siguiente hito analítico.
No se repitieron baterías válidas ni se añadieron obligaciones al roadmap.
