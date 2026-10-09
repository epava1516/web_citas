"""Reusable domain-sized synthetic revisions; size calibration precedes persistence."""

import hashlib
import io
import random
from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision
from apps.mediafiles.models import Blob, Photo
from apps.mediafiles.services import read_upload
from apps.safety.rights_exports import canonical

TOPICS = [
    ("Cita previa", "La atención se organiza con reserva y confirmación de disponibilidad antes de concertar la visita.", "Appointments are arranged through a reservation and availability confirmation before a visit."),
    ("Horario", "El horario anunciado es orientativo y cada franja se confirma según la agenda de esta revisión.", "The advertised timetable is indicative and each time slot is confirmed against this revision's schedule."),
    ("Ubicación", "La ubicación se comunica mediante la ciudad elegida y se acuerda el punto de encuentro al reservar.", "The location is represented by the chosen city and the meeting point is agreed when booking."),
    ("Desplazamientos", "Los desplazamientos requieren consultar previamente la zona y el tiempo disponible para el trayecto.", "Travel requires advance discussion of the area and the time available for the journey."),
    ("Recepción", "La recepción se prepara según el tipo de cita, con indicaciones de acceso una vez confirmada la reserva.", "Reception arrangements depend on the appointment, with access instructions after confirmation."),
    ("Idioma", "Las preferencias de idioma se acuerdan al inicio para facilitar una comunicación clara sobre la cita.", "Language preferences are agreed at the start to make communication about the appointment clear."),
    ("Servicios", "Los servicios del catálogo se consultan individualmente y su disponibilidad depende de la reserva.", "Catalogue services are discussed individually and availability depends on the reservation."),
    ("Tarifas", "Las tarifas se facilitan al consultar y se explica el alcance antes de aceptar cualquier propuesta.", "Rates are provided on enquiry and the scope is explained before accepting any proposal."),
    ("Duración", "La duración de la cita se confirma por separado, respetando el margen de llegada y despedida acordado.", "Appointment duration is confirmed separately, including agreed arrival and departure allowances."),
    ("Confirmación", "La confirmación recoge la fecha, la franja horaria y los detalles acordados para evitar malentendidos.", "Confirmation includes the date, time slot and agreed details to avoid misunderstandings."),
    ("Cambios", "Los cambios de fecha se consultan con antelación y quedan sujetos a la disponibilidad de la nueva franja.", "Date changes are discussed in advance and depend on availability in the new time slot."),
    ("Cancelaciones", "Las cancelaciones se comunican por el canal pactado para liberar la agenda y evitar desplazamientos.", "Cancellations are communicated through the agreed channel to release the slot and avoid travel."),
    ("Puntualidad", "La puntualidad facilita la organización de las siguientes citas y cualquier retraso debe comunicarse.", "Punctuality helps organise subsequent appointments and any delay should be communicated."),
    ("Preparación", "La preparación de la visita incluye revisar el horario y las instrucciones recibidas al confirmar.", "Preparing for a visit includes reviewing the timetable and the instructions sent at confirmation."),
    ("Accesibilidad", "Las necesidades de acceso se consultan antes de reservar para comprobar las condiciones disponibles.", "Access requirements are discussed before booking to check the arrangements available."),
    ("Privacidad", "La comunicación evita compartir datos innecesarios y los detalles privados se mantienen en el canal acordado.", "Communication avoids unnecessary data sharing and private details remain in the agreed channel."),
    ("Preferencias", "Las preferencias se explican con claridad y se revisan de forma respetuosa antes de confirmar el encuentro.", "Preferences are explained clearly and reviewed respectfully before confirming the meeting."),
    ("Límites", "Los límites de la cita se acuerdan expresamente y cualquier cambio requiere una nueva conversación.", "Appointment boundaries are expressly agreed and any change requires a new conversation."),
    ("Descansos", "Los descansos entre citas ayudan a mantener la agenda y no forman parte de la duración reservada.", "Breaks between appointments help maintain the schedule and are separate from reserved duration."),
    ("Agenda", "La agenda puede variar según el día y las franjas no confirmadas siguen pendientes de consulta.", "The schedule can vary by day and unconfirmed slots remain subject to enquiry."),
    ("Disponibilidad", "La disponibilidad anunciada se revisa al responder y no equivale a una reserva automática.", "Advertised availability is reviewed when replying and does not amount to an automatic booking."),
    ("Transporte", "Las opciones de transporte se consideran al acordar la hora y los desplazamientos de la visita.", "Transport options are considered when agreeing the time and travel arrangements for a visit."),
    ("Estancia", "La estancia se organiza de acuerdo con el tiempo reservado y las condiciones confirmadas previamente.", "The visit is organised around the reserved time and the conditions confirmed in advance."),
    ("Comunicación", "La comunicación sobre la reserva se concentra en el canal acordado para mantener los detalles actualizados.", "Booking communication remains in the agreed channel to keep arrangements up to date."),
    ("Fotografías", "Las imágenes del anuncio se revisan al actualizarlo y representan únicamente el material autorizado.", "Listing images are reviewed on updates and represent only the material authorised for display."),
    ("Actualización", "La información de esta versión sustituye las indicaciones anteriores de agenda para nuevas consultas.", "Information in this version replaces previous scheduling details for new enquiries."),
    ("Acompañamiento", "Las condiciones de acompañamiento se describen antes de confirmar y dependen de lo acordado para la cita.", "Companionship arrangements are described before confirmation and depend on the agreement for the appointment."),
    ("Consulta", "Las consultas previas permiten comprobar los detalles pendientes sin compromiso de confirmar una reserva.", "Advance enquiries help check outstanding details without a commitment to confirm a booking."),
]
PATHS = ["/title", "/description", "/description_alternative"]


def revision_values(identity, index, paragraphs):
    es, en = [], []
    for topic, spanish, english in TOPICS[:paragraphs]:
        # Each topic is a complete substantive paragraph, not byte padding.
        es.append(f"{topic}. {spanish} En la revisión {index:04d} de {identity}, se ofrece atención "
                  f"en la franja {9 + index % 10}:00 y se consulta la agenda del día {1 + index % 28}. "
                  "Este anuncio es sintético y no describe a una persona real.")
        en.append(f"{topic}. {english} Revision {index:04d} of {identity} offers appointments "
                  f"at {9 + index % 10}:00, subject to availability on day {1 + index % 28}. "
                  "This synthetic listing does not describe a real person.")
    return {"title": f"{identity}: agenda sintética, revisión {index:04d}",
            "description": "\n\n".join(es), "description_alternative": "\n\n".join(en)}


def candidate(rows):
    return {"schema": "portability-selected-fields-v1", "datasets": {
        "revisions": [{"fields": {"/" + name: row[name] for name in
                                  ["title", "description", "description_alternative"]}} for row in rows]
    }}


def calibrated_rows(identity, count=1500, target=16 * 1024 * 1024):
    # Find two adjacent complete topic sets, then distribute them across revisions.
    for paragraphs in range(1, len(TOPICS)):
        low = [revision_values(identity, index, paragraphs) for index in range(count)]
        high = [revision_values(identity, index, paragraphs + 1) for index in range(count)]
        if max(len(row[name]) for row in high for name in
               ["description", "description_alternative"]) > 6000:
            break
        low_bytes = len(canonical(candidate(low)).encode())
        high_bytes = len(canonical(candidate(high)).encode())
        if low_bytes <= target <= high_bytes:
            chosen = round(count * (target - low_bytes) / (high_bytes - low_bytes))
            rows = [high[index] if index < chosen else low[index] for index in range(count)]
            size = len(canonical(candidate(rows)).encode())
            if abs(size - target) / target > 0.01:
                raise AssertionError("Candidate calibration outside declared tolerance")
            return rows, {"candidate_bytes": size, "topic_counts": [paragraphs, paragraphs + 1],
                          "longer_revisions": chosen}
    raise AssertionError("Domain paragraphs cannot meet size within normal field limits")


def populate(identity):
    rows, calibration = calibrated_rows(identity)
    user = User.objects.create_user(username=identity, email=identity + "@example.invalid",
                                    role="individual")
    person = Person.objects.create(alias=identity, individual=user, subject=user)
    listing = Listing.objects.create(person=person)
    revisions = [Revision(listing=listing, manager_version=person.manager_version, **row)
                 for row in rows]
    Revision.objects.bulk_create(revisions, batch_size=100)
    originals = []
    for index in range(16):
        width, height = 1024, 1365
        # Real decoded pixel data, no added metadata or appended bytes.
        bitmap = Image.frombytes("RGB", (width, height),
                                 random.Random(identity + str(index)).randbytes(width * height * 3))
        output = io.BytesIO()
        bitmap.save(output, format="WEBP", lossless=True, method=0)
        content = output.getvalue()
        upload = SimpleUploadedFile("texture.webp", content, content_type="image/webp")
        raw, decoded, digest = read_upload(upload)
        assert raw == content and decoded.size == (width, height)
        blob = Blob.objects.create(sha256=digest, width=width, height=height, status="ready")
        blob.original.save(str(uuid4()) + ".webp", ContentFile(content))
        blob.derivative.save(str(uuid4()) + ".webp", ContentFile(content))
        Photo.objects.create(revision=revisions[index], blob=blob)
        with blob.original.open("rb") as saved:
            assert hashlib.sha256(saved.read()).hexdigest() == digest
        originals.append({"sha256": digest, "bytes": len(content), "blob": str(blob.pk)})
    total = sum(row["bytes"] for row in originals)
    assert abs(total - 64 * 1024 * 1024) / (64 * 1024 * 1024) <= 0.01
    return person, listing, rows, {**calibration, "originals_bytes": total, "originals": originals}
