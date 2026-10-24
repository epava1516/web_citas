"""Static producer drift is a failure, never permission to rotate persistent HMAC."""
from pathlib import Path

import pytest

from scripts.secret_dependencies import HMAC_RULES, DependencyInventoryError, inventory


def test_current_direct_hmac_producers_are_all_classified():
    result = inventory(Path(__file__).resolve().parents[1])
    assert len(result['producers']) == len(HMAC_RULES) == 8
    assert result['retirement_authorized'] is False
    assert result['unmeasured']
    assert len(result['source_sha256']) == 7


@pytest.mark.parametrize('body', [
    "from django.utils.crypto import salted_hmac\ndef unknown(value):\n return salted_hmac('new-purpose',value)",
    "from django.utils.crypto import salted_hmac as renamed\ndef unknown(value):\n return renamed('new-purpose',value)",
    "from django.utils import crypto\ndef unknown(value):\n return crypto.salted_hmac('new-purpose',value)",
    "from django.utils.crypto import salted_hmac\ndef unknown(value):\n return salted_hmac(value,value)",
])
def test_unclassified_or_dynamic_hmac_producer_is_not_silently_accepted(tmp_path, body):
    root = tmp_path / 'apps'
    root.mkdir()
    (root / 'new.py').write_text(body)
    with pytest.raises(DependencyInventoryError, match='Unclassified HMAC producer'):
        inventory(tmp_path)


def test_removed_producer_is_registry_drift(tmp_path):
    (tmp_path / 'apps').mkdir()
    with pytest.raises(DependencyInventoryError, match='registry differs'):
        inventory(tmp_path)
