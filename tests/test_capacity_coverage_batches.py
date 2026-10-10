"""Coordinate partition only; not a capacity or audit acceptance test."""

import pytest
from capacity_delivery_flow import coverage_batches


def test_diagnostic_partition_preserves_every_coordinate_and_dataset_boundary():
    required = (
        [("profile", 0, 1, False)]
        + [("revisions", row, page, False) for row in range(3) for page in (1, 2)]
        + [("revisions", 0, page, True) for page in (1, 2, 3)]
        + [("favorites", 0, 1, False)]
    )
    groups = list(coverage_batches(required))
    assert [item for group in groups for item in group] == required
    assert [len(group) for group in groups] == [1, 4, 2, 3, 1]
    assert all(len({(row[0], row[3]) for row in group}) == 1 for group in groups)
    assert list(coverage_batches([])) == []


@pytest.mark.parametrize("count", [0, 5, True])
def test_diagnostic_partition_rejects_unbounded_sizes(count):
    with pytest.raises(ValueError):
        list(coverage_batches([], count))
