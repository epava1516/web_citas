"""Finite scalar-source feasibility only; no HTTP or security acceptance of a new architecture."""
import json
import statistics
from pathlib import Path
from time import perf_counter_ns, thread_time_ns
from uuid import uuid4

import pytest
from capacity_target_fixture import calibrated_rows
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision
from apps.safety.canonical_kernel_loader import kernel_identity, validated_kernel
from apps.safety.crypto import seal, unseal
from apps.safety.models import RightsRequest
from apps.safety.rights_exports import canonical, source_copy
from apps.safety.rights_inspection_source import inspection_source
from apps.safety.rights_source_fingerprint import source_fingerprint
from tests.capacity_page_manifest_prototype import prepare, read

pytestmark = pytest.mark.django_db(transaction=True)


def test_page_manifest_data_feasibility_and_mutation_filters(record_property):
    assert connection.vendor == "postgresql" and validated_kernel() is not None
    rows, calibration = calibrated_rows("page-manifest-synthetic")
    user = User.objects.create_user(username="page-manifest-synthetic", role="individual")
    person = Person.objects.create(alias="page-manifest-synthetic", individual=user, subject=user)
    listing = Listing.objects.create(person=person)
    Revision.objects.bulk_create([Revision(listing=listing, manager_version=person.manager_version, **row)
                                 for row in rows], batch_size=100)
    now = timezone.now()
    case = RightsRequest.objects.create(submission_key=uuid4(),kind="portability",actor=user,person=person,
        receipt_digest="a"*64,payload_digest="b"*64,encrypted_payload="synthetic",received_at=now,
        initial_due_at=now,receipt_expires_at=now)
    prep_wall, prep_cpu = perf_counter_ns(), thread_time_ns()
    try:
        with transaction.atomic():
            before = source_fingerprint(person, listing, case)
            source = source_copy(person, listing, case)
            expected_digest = prepare(person, listing, case, source)
            assert source_fingerprint(person, listing, case) == before
        preparation = dict(wall_ns=perf_counter_ns()-prep_wall,thread_cpu_ns=thread_time_ns()-prep_cpu)
        def operation(mode, position=0):
            with transaction.atomic():
                if mode == "full":
                    with inspection_source(person, listing, case) as context:
                        return context.get(person, listing, case)["revisions"][position*50:position*50+50]
                return read(person, listing, case, position, expected_digest)
        for position in (0,14,29):
            assert canonical(operation("page",position)) == canonical(operation("full",position))
        first, second = operation("page"), operation("page")
        assert first is not second and first[0] is not second[0]
        first[0]["title"] = "modified-return-must-not-leak"
        assert operation("page")[0]["title"] == second[0]["title"]
        for mode in ("full","page")*2:
            operation(mode)
        samples = []
        # Counterbalanced pairs; SQL/crypto/current physical stamps included, preparation outside.
        for number, mode in enumerate(("full","page","page","full")*10):
            wall, cpu = perf_counter_ns(), thread_time_ns()
            result = operation(mode)
            sample = dict(mode=mode,order=number,wall_ns=perf_counter_ns()-wall,
                          thread_cpu_ns=thread_time_ns()-cpu)
            assert canonical(result) == canonical(source["revisions"][:50])
            samples.append(sample)
        medians = {mode:{clock:statistics.median(s[clock] for s in samples if s["mode"]==mode)
                         for clock in ("wall_ns","thread_cpu_ns")} for mode in ("full","page")}
        deltas = []
        for index in range(0,len(samples),2):
            pair={s["mode"]:s for s in samples[index:index+2]}
            deltas.append({clock:pair["full"][clock]-pair["page"][clock]
                           for clock in ("wall_ns","thread_cpu_ns")})
        report=dict(kernel=kernel_identity(),samples=samples,medians=medians,deltas=deltas,preparation=preparation,
                    selected_bytes=calibration["candidate_bytes"],rows=1500,page_rows=50,
                    benefit_screen=all(sum(d[c]>0 for d in deltas)>=15 for c in ("wall_ns","thread_cpu_ns")),
                    limits=["Data-only helper never connected to an endpoint; no actor/proof/latest/chain checks exercised here",
                            "Warm same-connection scalar source, no photos/geography/relations corpus or RustFS/Caddy/concurrent load",
                            "Current attribute metadata binding is not complete function/RLS/enum/server-restore attestation",
                            "No XID-wrap experiment; bound tested arithmetically only; no long-term retention or purge task acceptance",
                            "Preparation stores encrypted chunks in temporary PostgreSQL; no fallback or durable product migration",
                            "No HTTP gain or SLO acceptance; full path returns same 50 rows after complete inspection_source work"])
        # Every attack rolls back to the same real prepared source/artifacts.
        with transaction.atomic():
            Revision.objects.filter(listing=listing).update(title="changed-source-synthetic")
            with pytest.raises(ValidationError,match="binding changed"):
                operation("page")
            transaction.set_rollback(True)
        with pytest.raises(ValidationError,match="binding changed"):
            with transaction.atomic():
                read(person,listing,case,0,"0"*64)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("UPDATE diagnostic_page_manifest SET content=(SELECT content FROM diagnostic_page_manifest WHERE position=1) WHERE position=0")
            with pytest.raises(ValidationError,match="binding changed"):
                operation("page")
            transaction.set_rollback(True)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM diagnostic_page_manifest WHERE position=0")
            with pytest.raises(ValidationError,match="unavailable"):
                operation("page")
            transaction.set_rollback(True)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("UPDATE diagnostic_page_manifest SET content='malformed-synthetic-token' WHERE position=0")
            with pytest.raises(ValidationError,match="authentication failed"):
                operation("page")
            transaction.set_rollback(True)
        for field, value in (("expires",0),("xid",-(1<<31)),("rows",1499)):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT manifest FROM diagnostic_page_manifest WHERE position=0")
                    manifest=unseal(cursor.fetchone()[0])
                    manifest[field]=value
                    cursor.execute("UPDATE diagnostic_page_manifest SET manifest=%s WHERE position=0",[seal(manifest)])
                with pytest.raises(ValidationError,match="binding changed"):
                    operation("page")
                transaction.set_rollback(True)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE listings_revision ADD COLUMN diagnostic_schema_change text DEFAULT 'synthetic'")
            with pytest.raises(ValidationError,match="binding changed"):
                operation("page")
            transaction.set_rollback(True)
        report["attacks_rejected"]=["source_update","wrong_expected_digest","swapped_chunk","missing_chunk",
            "invalid_ciphertext","expired_manifest","out_of_range_xid_anchor_not_real_wrap","wrong_count","changed_attribute_schema"]
        record_property("page_manifest_feasibility",json.dumps(report))
        Path("/tmp/mod08-page-manifest-report.json").write_text(json.dumps(report,indent=2))
    finally:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS pg_temp.diagnostic_page_manifest")
