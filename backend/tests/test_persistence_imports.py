from __future__ import annotations

from typing import Any, Dict

from app.acvp_mldsa.expected import generate_expected_results_from_prompt
from app.main import (
    get_report,
    import_generated_mldsa_bundle,
    validate_import,
)
from app.models import GeneratedMldsaImportRequest, ValidateRequest
from app.storage.sqlite_store import get_import_record


SEED_32_BYTES = "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"


def test_generated_import_validation_and_report_persist_in_sqlite() -> None:
    prompt = keygen_prompt()
    response = generate_expected_results_from_prompt(prompt)

    imported = import_generated_mldsa_bundle(
        GeneratedMldsaImportRequest(
            prompt=prompt,
            response=response,
            label="sqlite import persistence",
        )
    )
    stored = get_import_record(imported.importId)
    validation = validate_import(ValidateRequest(importId=imported.importId))
    report = get_report(imported.importId)
    stored_after_validation = get_import_record(imported.importId)

    assert stored is not None
    assert stored["prompt"] == prompt
    assert stored["generatedExpectedResults"] is True
    assert validation["summary"]["failed"] == 0
    assert report["passedCount"] == 1
    assert stored_after_validation is not None
    assert stored_after_validation["validationResult"]["summary"]["passed"] == 1
    assert stored_after_validation["report"]["passedCount"] == 1


def keygen_prompt() -> Dict[str, Any]:
    return {
        "vsId": 4101,
        "algorithm": "ML-DSA",
        "mode": "keyGen",
        "revision": "FIPS204",
        "testGroups": [
            {
                "tgId": 1,
                "testType": "AFT",
                "parameterSet": "ML-DSA-44",
                "tests": [{"tcId": 1, "seed": SEED_32_BYTES}],
            }
        ],
    }

