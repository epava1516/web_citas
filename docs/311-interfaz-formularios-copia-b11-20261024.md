# B11-350 — Interfaz de formularios de copia

B11 comienza con12/18puntos cerrados; B10 conserva deuda separada abierta. Se selecciona una extracción acotada de presentación: ReviewedCopyField, CopyPresentationForm, PageReviewForm y ExportForm de rights_exports a rights_copy_forms. Se preservarán alias de importación heredados, nombres de campos, constructores, valores y validación.

## Responsabilidad y dependencias

El grafo420 y las importaciones actuales orientan al módulo rights_exports:66sentencias en59módulos de aplicación lo importan para servicios de copia, imágenes, autoridad o canonicalización. Su tamaño/grado no demuestra coste CPU. En él conviven cuatro clases de formulario de presentación con generación, locks y entrega. La extracción elegida separa esas clases sin cambiar las funciones de dominio ni migrar los59consumidores. El nuevo módulo dependerá sólo de django.forms y del helper de rótulos existente. rights_exports mantendrá las clases disponibles por importación directa.

Línea de base y candidata usarán exactamente tests/test_access_copy_preparation_localization.py y tests/test_copy_page_label_association.py:12casos, PostgreSQL/Redis propios, dos workers y timeout1200s. No se presenta el cambio como mejora de CPU o latencia. Se comprobará identidad estructural AST de las cuatro clases y de todas las demás sentencias no importadas del módulo de origen.

Reversión prevista: reintegrar los cuerpos de clases y retirar sus importaciones/nuevo módulo, con snapshot exacto anterior conservado. No restaurar el archivo completo sobre trabajo posterior. El cambio puede variar __module__ de las clases; no se cambia el contrato de importación heredado o datos de formularios. Se revisan referencias internas antes de aplicar, incluidas pruebas de JSON literal, opciones, errores, etiquetas/identificadores, guardado y replay. Sin cambios de autoridad fresca, versiones, locks, cifrado, formatos de evidencia, modelos o migraciones. B11 sigue abierto hasta conciliación del requisito y regresión.

## Candidata preparada

Base20261024-083917-bb075a5d:12PASS/0omisiones,173.912sJUnit,1720fuentes verificadas, limpieza y Telegram confirmados. Aplicada extracción de las cuatro clases intactas a rights_copy_forms; rights_exports conserva reexportaciones explícitas. AST confirma iguales todas las demás sentencias no importadas; candidata pendiente de las mismas12pruebas.

## Resultado y contrato de interfaz

Candidata20261024-084341-46d1f457:12PASS/0FAIL/0ERROR/0SKIP,177.655sJUnit,1721fuentes congeladas verificadas; misma selección de12testigos y dos workers que la base. Sólo cambian rights_exports.py y el nuevo rights_copy_forms.py en producto; pruebas idénticas. Limpieza y Telegram confirmados.

Se corrige el recuento inicial:66sentencias de importación,59módulos consumidores distintos. El [inventario estático](evidencias/b11-static-interface-inventory-20261024.json) distingue ambas medidas y no pretende descubrir importaciones dinámicas ni medir CPU.

| Interfaz conservada | Responsabilidad | Garantía del cambio |
|---|---|---|
| ReviewedCopyField | JSON de copia y representación de None | Misma clase estructural, misma validación/contenido literal |
| CopyPresentationForm | Rótulos estáticos según idioma | Mismos constructores/opciones; sin autoridad de dominio |
| PageReviewForm | Entradas de revisión de página | Campos, límites, UUID y versiones intactos |
| ExportForm | Datos de preparación de copia | Opciones, campos, cursor y contenido JSON intactos |

Las cuatro interfaces pueden importarse desde rights_copy_forms; rights_exports conserva los nombres heredados mediante reexportaciones explícitas. La dependencia nueva es sólo django.forms y rectification_presentation.caption; no importa generación, ORM, modelos ni autoridad. El resto del módulo mantiene todas sus sentencias no importadas exactamente por AST. Se conserva caption como reexportación heredada; django.forms sigue siendo necesario en download para validar UUID. El primer Ruff detectó orden de importaciones y se corrigió con la regla del proyecto; ambos recibos se conservan, sin disfrazar el fallo inicial como PASS.

[Base](evidencias/b11-forms-baseline-audit-20261024.json), [candidata](evidencias/b11-forms-corrected-audit-20261024.json) y [paridad estructural](evidencias/b11-forms-structure-parity-20261024.json). Las doce pruebas verifican ES/EN, perfil/cuenta, constructores sin consultas, esquema/literales JSON, controles HTTP nativos, errores/etiquetas, guardado y replay. No son una prueba nueva de todos los servicios de derechos ni una mejora de rendimiento: los tiempos de JUnit no son una comparación de latencias del producto. Sin dependencias instaladas, migraciones o cambio de formatos de evidencia.

## Aceptación acotada

B11 se acepta técnicamente en local para la interfaz y extracción justificadas, con inventario de dependencias y regresión antes/después. No se declara eliminado todo riesgo de mantenimiento ni se exige reescritura integral. El __module__ de las clases pasa al nuevo módulo; se preservan imports y constructores, no se promete identidad de metadatos de introspección. No se cambia la autoridad fresca, los locks o versiones por esta aceptación. La candidata conjunta y sus recursos/SLO siguen pendientes enB16; la etapa3 completa no se cierra mientras B10 conserve deuda separada pendiente. Véase [acta20](actas/20-beta-b11-aceptacion-local-20261024.md).
