import re
import uuid

from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Person, VerificationCheck, VerificationEvent


def normalize_phone(value):
    value = re.sub(r"[\s().-]", "", value)
    if value.startswith("00"):
        value = "+" + value[2:]
    if re.fullmatch(r"[6789]\d{8}", value):
        value = "+34" + value
    if not re.fullmatch(r"\+[1-9]\d{7,14}", value):
        raise ValidationError("Número internacional no válido / Invalid international number")
    return value


def real_checks(person, age=None):
    age = age or person.verificationcheck_set.order_by("-created_at").first()
    phone = person.phone_claim
    return {
        "age": bool(
            age
            and age.provider
            and age.provider != "simulator"
            and age.provider == settings.VERIFICATION_PROVIDER
            and age.procedure == "age-v1"
            and age.status == "passed"
            and age.subject_id == person.subject_id
            and age.manager_version == person.manager_version
        ),
        "contact": bool(
            phone
            and phone.verified_at
            and phone.verification_procedure == "sms-v1"
            and phone.individual_id == person.individual_id
            and phone.agency_id == person.agency_id
        ),
        "agency": bool(
            person.agency_id
            and person.agency.verification_status == "passed"
            and person.agency.verification_procedure == "organization-v1"
        ),
    }


def publication_ready(person):
    consent = person.consent_version == person.manager_version and not person.consent_revoked_at
    phone = person.phone_claim
    manager_phone = (
        phone
        and phone.verified_at
        and phone.individual_id == person.individual_id
        and phone.agency_id == person.agency_id
    )
    if settings.PRODUCTION:
        checks = real_checks(person)
        if (
            not checks["age"]
            or not checks["contact"]
            or (person.agency_id and not checks["agency"])
        ):
            return False
    return bool(
        person.subject_id
        and person.age_status == "passed"
        and consent
        and manager_phone
        and person.manager_review_status == "approved"
    )


def start_age_check(person, subject):
    if settings.VERIFICATION_PROVIDER != "simulator" or settings.PRODUCTION:
        raise PermissionDenied("Verification provider not integrated")
    return VerificationCheck.objects.create(
        person=person, subject=subject, manager_version=person.manager_version, provider="simulator"
    )


def simulate_event(check, outcome, event_id=None):
    if settings.PRODUCTION or settings.VERIFICATION_PROVIDER != "simulator":
        raise PermissionDenied("Simulator disabled")
    return signing.dumps(
        {"check": str(check.pk), "outcome": outcome, "event": str(event_id or uuid.uuid4())},
        salt="verification-simulator-v1",
    )


def receive_event(payload):
    if settings.PRODUCTION or settings.VERIFICATION_PROVIDER != "simulator":
        raise PermissionDenied("Simulator events disabled")
    data = signing.loads(payload, salt="verification-simulator-v1", max_age=300)
    if data.get("outcome") not in {"passed", "failed", "pending"}:
        raise ValidationError("Invalid verification outcome")
    with transaction.atomic():
        initial = VerificationCheck.objects.get(pk=data["check"])
        person = Person.objects.select_for_update().get(pk=initial.person_id)
        check = VerificationCheck.objects.select_for_update().get(pk=initial.pk)
        previous = VerificationEvent.objects.filter(event_id=data["event"]).first()
        if previous:
            if previous.verification_id != check.pk or previous.outcome != data["outcome"]:
                raise ValidationError("Conflicting event replay")
            return check
        if person.verificationcheck_set.order_by("-created_at").first().pk != check.pk:
            raise ValidationError("Verification superseded")
        if check.status != "pending":
            raise ValidationError("Verification already terminal")
        if check.manager_version != person.manager_version or check.subject_id != person.subject_id:
            raise ValidationError("Verification belongs to an obsolete manager/subject")
        VerificationEvent.objects.create(
            event_id=data["event"], verification=check, outcome=data["outcome"]
        )
        check.status = data["outcome"]
        if check.status != "pending":
            check.completed_at = timezone.now()
        check.save(update_fields=["status", "completed_at"])
        person.age_status = check.status
        person.save(update_fields=["age_status"])
        return check
