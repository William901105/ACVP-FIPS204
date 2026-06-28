from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi.responses import JSONResponse

from app.acvp_protocol.routes import (
    create_acvp_v1_test_session,
    submit_acvp_v1_vector_set_results,
)
from app.acvp_protocol.service import (
    ACVP_SKELETON_SESSION_STORE,
    ACVP_SKELETON_VECTOR_SET_STORE,
)


CAMPAIGN_SEED = "00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF"


def setup_function() -> None:
    ACVP_SKELETON_SESSION_STORE.clear()
    ACVP_SKELETON_VECTOR_SET_STORE.clear()


def test_post_test_session_dispatches_mldsa_provider_and_validates_results() -> None:
    created = _body(
        create_acvp_v1_test_session(
            {
                "algorithms": [_keygen_registration(["ML-DSA-44"])],
                "campaignSeed": CAMPAIGN_SEED,
                "testsPerGroup": 1,
            }
        )
    )
    vector_set_id = created["vectorSetIds"][0]
    expected = ACVP_SKELETON_VECTOR_SET_STORE[vector_set_id]["expectedResults"]
    submitted = _body(
        submit_acvp_v1_vector_set_results(
            vector_set_id,
            {"response": expected},
        )
    )

    assert created["status"] == "vectorReady"
    assert created["negotiatedCapabilities"]["negotiated"][0]["algorithm"] == "ML-DSA"
    assert submitted["validationResult"]["summary"]["failed"] == 0


def test_nist_conformance_generation_profile_dispatches_through_provider() -> None:
    created = _body(
        create_acvp_v1_test_session(
            {
                "algorithms": [_keygen_registration(["ML-DSA-44"])],
                "campaignSeed": CAMPAIGN_SEED,
                "testsPerGroup": 1,
                "generationProfile": "nist-conformance",
            }
        )
    )
    prompt = ACVP_SKELETON_VECTOR_SET_STORE[created["vectorSetIds"][0]]["prompt"]

    assert created["vectorGeneration"]["generationProfile"] == "nist-conformance"
    assert len(prompt["testGroups"][0]["tests"]) >= 25


def test_shake_registration_still_generates_through_provider_dispatch() -> None:
    registration = _siggen_external_registration()
    registration["preHash"] = ["preHash"]
    registration["capabilities"][0]["hashAlgs"] = ["SHAKE-256"]
    created = _body(
        create_acvp_v1_test_session(
            {
                "algorithms": [registration],
                "campaignSeed": CAMPAIGN_SEED,
                "testsPerGroup": 1,
            }
        )
    )
    prompt = ACVP_SKELETON_VECTOR_SET_STORE[created["vectorSetIds"][0]]["prompt"]

    assert created["status"] == "vectorReady"
    assert _hash_algs_in_prompt(prompt) == {"SHAKE-256"}


def test_unsupported_algorithm_returns_structured_provider_error() -> None:
    response = create_acvp_v1_test_session(
        {
            "algorithms": [
                {
                    "algorithm": "ML-KEM",
                    "mode": "keyGen",
                    "revision": "FIPS203",
                }
            ]
        }
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    body = _body(response)
    assert body["error"]["code"] == "unsupported_algorithm"
    assert body["error"]["path"] == "$.algorithms[0].algorithm"
    assert "Unsupported algorithm provider" in body["error"]["message"]


def _keygen_registration(parameter_sets: List[str]) -> Dict[str, Any]:
    return {
        "algorithm": "ML-DSA",
        "mode": "keyGen",
        "revision": "FIPS204",
        "prereqVals": [{"algorithm": "SHA", "valValue": "same"}],
        "parameterSets": parameter_sets,
    }


def _siggen_external_registration() -> Dict[str, Any]:
    return {
        "algorithm": "ML-DSA",
        "mode": "sigGen",
        "revision": "FIPS204",
        "prereqVals": [{"algorithm": "SHA", "valValue": "same"}],
        "deterministic": [True],
        "signatureInterfaces": ["external"],
        "preHash": ["pure", "preHash"],
        "capabilities": [
            {
                "parameterSets": ["ML-DSA-44"],
                "messageLength": [{"min": 8, "max": 128, "increment": 8}],
                "contextLength": [{"min": 0, "max": 64, "increment": 8}],
                "hashAlgs": ["SHA2-256", "SHAKE-256"],
            }
        ],
    }


def _hash_algs_in_prompt(prompt: Dict[str, Any]) -> set[str]:
    return {
        test["hashAlg"]
        for group in prompt["testGroups"]
        for test in group["tests"]
        if "hashAlg" in test
    }


def _body(value: Any) -> Dict[str, Any]:
    if isinstance(value, JSONResponse):
        value = json.loads(value.body.decode("utf-8"))
    if (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], dict)
        and value[0].get("acvVersion") == "1.0"
    ):
        return value[1]
    return value

