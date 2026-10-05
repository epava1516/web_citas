"""Pure page completeness boundaries; no authorization or review claims."""

from test_rights_portability_coverage import fixture

from apps.safety.rights_portability_coverage_read_gate import required_pages


def test_empty_datasets_still_require_reads_and_binary_mode_is_separate():
    source, *_ = fixture()
    pages = required_pages(source)
    assert len(pages) == 10
    assert ("revisions", 0, 1, False) in pages
    assert ("revisions", 0, 1, True) in pages
    assert len(set(pages)) == len(pages)


def test_full_scalar_and_binary_page_boundaries():
    source, *_ = fixture()
    source["profile"] = {str(index): index for index in range(101)}
    source["revisions"] = [{"images": [{"photo": str(index)} for index in range(21)]}]
    pages = required_pages(source)
    assert [(d, r, p) for d, r, p, b in pages if d == "profile" and not b] == [
        ("profile", 0, 1),
        ("profile", 0, 2),
        ("profile", 0, 3),
    ]
    assert [p for d, r, p, b in pages if b] == [1, 2]
