from __future__ import annotations

from pathlib import Path


DOC = Path(__file__).resolve().parents[1] / "docs" / "acvp-conformance-matrix.md"


def test_acvp_conformance_matrix_exists_and_references_nist_sources() -> None:
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")

    assert "https://pages.nist.gov/ACVP/draft-fussell-acvp-spec.html" in text
    assert "https://pages.nist.gov/ACVP/draft-celi-acvp-ml-dsa.html" in text
    assert "https://pages.nist.gov/ACVP/" in text
    assert "https://csrc.nist.gov/pubs/fips/204/final" in text


def test_acvp_conformance_matrix_has_required_status_values() -> None:
    text = DOC.read_text(encoding="utf-8")

    for status in (
        "SUPPORTED",
        "PARTIAL",
        "MISSING",
        "LOCAL_DEMO_ONLY",
        "NOT_IN_SCOPE_YET",
        "NEEDS_SPEC_REVIEW",
    ):
        assert status in text


def test_acvp_conformance_matrix_declares_demo_and_skeleton_not_production() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "`/api/demo/acvp/...` routes are a local demo lifecycle" in text
    assert "not formal ACVP endpoints" in text
    assert "`/acvp/v1/...` routes are Phase 3-2 skeleton endpoints" in text
    assert "not a production-ready server" in text


def test_acvp_conformance_matrix_lists_required_future_phases() -> None:
    text = DOC.read_text(encoding="utf-8")

    for phase in (
        "Phase 3-2",
        "Phase 3-3",
        "Phase 3-4",
        "Phase 3-5",
        "Phase 4-1",
        "Phase 4-2",
    ):
        assert phase in text
