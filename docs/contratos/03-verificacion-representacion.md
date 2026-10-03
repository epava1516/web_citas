# CR-03 — Verificación y representación, interfaz v1

Prefijos ES/EN, HTML SSR, sesión confirmada y documentos vigentes. Particular tiene una persona propia, agencia varias; la persona representada tiene acceso a sus controles independientemente del gestor. Editor limitado a asignaciones activas; autorización directa solo la persona, nunca el editor/propietario en su nombre.

| Ruta | Método | Acceso y resultado |
| --- | --- | --- |
| /person/create/ | GET/POST | Particular; alias; conserva persona existente, rol asignado servidor |
| /person/{id}/verification/ | GET | gestor autorizado o representado; estados edad/consentimiento/teléfono y bloqueo |
| /person/{id}/consent/invite/ | GET/POST | propietario agencia; email privado del representado; enlace dos días |
| /representation/{invitation}/{secret}/ | GET/POST | cuenta del email destinatario; GET no consume, POST acepta documento y gestor exactos |
| /person/{id}/consent/ | GET/POST | propio particular; autorización versionada de publicación |
| /person/{id}/age/ | GET/POST | representado; adaptador simulado pending/failed/passed, jamás operativo en producción |
| /person/{id}/phone/ | GET/POST | gestor; E.164, OTP simulado entregado por correo de pruebas |
| /phone/{challenge}/confirm/ | GET/POST | gestor vigente; código diez minutos, cinco intentos, consumo único |
| /person/{id}/revoke/ | POST | representado; invalida versión del gestor y edad; publicación no elegible |
| /person/{id}/transfer/ | GET/POST | representado; manager_version oculto obligatorio, agencia destino UUID o autogestión, ID persona conservado |

Edad y autorización separadas. Una casilla no prueba edad. `publication_ready` requiere sujeto, edad passed, consentimiento actual no revocado y teléfono verificado perteneciente al mismo gestor. Esto es elegibilidad local, no prueba real ni aprobación de anuncio: CR-06 volverá a comprobarlo al publicar y servir versiones públicas.

Gestor versionado: transferencia revoca consentimiento, borra asignación/teléfono y requiere nuevas comprobaciones. Eventos de edad e invitaciones anteriores no reactivan controles. Se conservan acciones de autorización/revocación/transferencia con sujeto, gestor/version, documento, fecha; no documentos de identidad ni biometría.

Adaptador de desarrollo: eventos firmados Django, vigencia cinco minutos, ID evento único, pending → passed/failed, resultado terminal no sobreescrito y comprobación de gestor/sujeto/verificación más reciente. El simulador se bloquea en producción tanto en ruta como en servicio. Proveedor real y evidencia de identidad/titularidad siguen pendientes externos.

Teléfonos: normalización española/internacional, unicidad global PostgreSQL; compartición solo dentro de la misma agencia. Dos particulares o agencias no pueden apropiarse simultáneamente del mismo contacto. OTP HMAC, reenvío invalida anterior; actor se revisa dentro de transacción y se serializa con revocación de editor. SMS local enviado por correo NO prueba control real del teléfono.

Recorrido particular: crear persona → autorizar publicación → simulador edad → solicitar/confirmar OTP → elegibilidad local → revocar. Agencia: crear persona → enviar autorización específica → representado confirma y completa edad → gestor confirma contacto → traslado conserva persona e invalida controles.

Esta entrega utiliza cuenta privada del representado para autorización directa. No implica perfil público de visitante. El canal público sin cuenta para personas representadas, reclamaciones y retirada se implementa en CR-09. No exigir acceso a la cuenta de agencia para ejercer derechos.

Pendientes compartidos: CR-04 acepta obligación del anunciante y liga contacto al anuncio; CR-06 implementa retirada/pausa de versiones publicadas al revocar/transferir; CR-09 reclamación pública sin cuenta. No marcar estas funciones como implementadas por existir requisitos de elegibilidad.

Ampliación CR-06: transferencia versionada, reintento exacto302 sin reset, versión/destino obsoletos409 e inválidos400; revisión humana del gestor y control del equipo anterior en contratos/06. Pausa/derivados privados ya conectados; navegador/agencia completa/reclamación todavía pendientes.


Ampliación compatible CR-07 — procedencia de comprobaciones: PhoneClaim conserva verification_procedure; confirmar el OTP local guarda simulator-v1. La migración core0011 deja vacío el origen de registros antiguos, sin atribuirles pruebas reales. Solicitud y confirmación del OTP simulado devuelven503 si se cambia el proveedor o se activa producción, incluso con un desafío anterior todavía vigente.

En producción, elegibilidad exige un proveedor de edad distinto de simulator y coincidente con el configurado, contacto sms-v1 y, para agencias, procedimiento organization-v1. Estos identificadores preparan el contrato de futuros adaptadores; no acreditan que exista integración real. Los simuladores actuales nunca generan esos procedimientos reales. La ficha y el listado leen la procedencia del registro, no infieren comprobaciones reales por el entorno. Un origen desconocido se presenta como sin acreditar.
