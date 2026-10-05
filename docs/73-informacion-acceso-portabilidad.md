# Información adicional de acceso y distinción de portabilidad

Estado: especificación técnica pendiente de implementación. Continúa CR09 tras las proyecciones de datos de docs69–72; no convierte una copia parcial en respuesta final ni acredita producción.

## Fundamento primario consultado

Consulta2026-10-05: [RGPD, artículos15 y20, BOE](https://www.boe.es/buscar/doc.php?id=DOUE-L-2016-80807).

El acceso comprende copia e información sobre finalidades, categorías, destinatarios, conservación, derechos, reclamación, origen disponible, decisiones automatizadas relevantes y garantías de transferencias. Debe proteger los derechos de terceros. La portabilidad tiene condiciones propias: datos facilitados por el interesado, base de consentimiento o contrato y tratamiento automatizado; incluye transmisión directa cuando sea técnicamente posible. No basta con cambiar una etiqueta sobre una misma copia.

## Diseño de ejecución

Preparar un documento de información ligado a expediente, sujeto, tipo de derecho, versión de fuente y versión de política. Revisarlo mediante formulario ESEN y conservar decisiones cifradas/versionadas, auditoría previa de consulta, prueba vigente y permisos frescos. Definir origen de cada afirmación: configuración comprobada, dato del inventario o decisión del revisor; no inferir bases jurídicas desde el rol de usuario ni una casilla aceptada.

Campos de acceso: confirmación de tratamiento; finalidades y categorías aplicables; destinatarios/categorías y transferencias/garantías; plazo o criterio de conservación por finalidad; origen de datos ajenos al titular; descripción de automatización aplicable; vías de derechos/reclamación. Un dato desconocido permanece pendiente de revisión y bloquea el cierre integral, en lugar de transformarse en una afirmación falsa. La documentación técnica de desarrollo no reemplaza la política operativa aprobada.

Evaluación de portabilidad separada: decidir procedencia y ámbito por conjuntos de datos, indicar origen y base revisados, tratamiento automatizado y protección de terceros; no incluir automáticamente notas internas o datos ajenos. Toda exclusión necesita motivo operativo revisado y respuesta del caso; no ocultar datos de acceso por considerarlos no portables. Preparar formato estructurado y ruta de transmisión directa sin enviar a terceros ni contratar proveedor durante desarrollo.

## Verificación requerida

Perfil y cuenta propia, persona representada sin cuenta y gestor con aislamiento; accesos/replays/versiones/fuente/política obsoletos; referencias/motivos inyectados; campos pendientes no permiten cierre final; casos procedente/parcial/no procedente de portabilidad con justificación revisada. Navegador ESEN/móvil, PostgreSQL y carreras reales cuando consuman prueba o generen respuesta. Integrar la información revisada en generación, descarga y respuestas finales con su propia caducidad y conservación.

Pendientes conexos: completar censo/proyecciones, fuentes históricas y compartidas, originales/metadatos de imágenes según ámbito aprobado, volumen/memoria, conservación y restauración, destinatarios y cierre. No declarar satisfecho el artículo15/20 solo por aprobar esta especificación o por pasar pruebas de una selección de datos.
