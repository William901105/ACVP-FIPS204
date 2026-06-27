from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi import HTTPException

from app.main import (
    create_demo_acvp_session,
    delete_demo_acvp_session,
    get_demo_acvp_session,
    get_demo_acvp_session_report,
    get_demo_acvp_session_validation,
    submit_demo_acvp_session_response,
)
from app.models import DemoAcvpResponseSubmitRequest, DemoAcvpSessionCreateRequest
from app.storage.sqlite_store import get_demo_session, list_state_events


SEED_32_BYTES = "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"


def test_demo_session_response_validation_report_and_delete_persist() -> None:
    created = create_demo_acvp_session(
        DemoAcvpSessionCreateRequest(
            prompt=keygen_prompt(),
            label="sqlite demo persistence",
        )
    )
    session_id = created["sessionId"]
    detail = get_demo_acvp_session(session_id)

    submit = submit_demo_acvp_session_response(
        session_id,
        DemoAcvpResponseSubmitRequest(response=detail["expectedResults"]),
    )
    validation = get_demo_acvp_session_validation(session_id)
    report = get_demo_acvp_session_report(session_id)
    stored = get_demo_session(session_id)
    events_before_delete = list_state_events("demo_session", session_id)
    deleted = delete_demo_acvp_session(session_id)
    events_after_delete = list_state_events("demo_session", session_id)

    assert submit["status"] == "validated"
    assert validation["validationResult"]["summary"]["failed"] == 0
    assert report["failedCount"] == 0
    assert stored is not None
    assert stored["validationResult"]["summary"]["passed"] == 1
    assert stored["report"]["passedCount"] == 1
    assert [event["event"] for event in events_before_delete] == ["created", "validated"]
    assert events_after_delete[-1]["event"] == "deleted"
    assert deleted["deleted"] is True
    with pytest.raises(HTTPException) as exc_info:
        get_demo_acvp_session(session_id)
    assert exc_info.value.status_code == 404


def keygen_prompt() -> Dict[str, Any]:
    return {
        "vsId": 4102,
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

