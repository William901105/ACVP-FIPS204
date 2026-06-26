from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi import HTTPException

from app.acvp_mldsa.errors import AcvpSchemaError
from app.acvp_mldsa.expected import (
    generate_expected_results_from_prompt,
    generate_keygen_expected_results_from_prompt,
)
from app.crypto_oracle.mldsa_oracle import keygen_internal, siggen_internal
from app.main import mldsa_expected_results, mldsa_keygen_expected_results
from app.models import MldsaExpectedResultsRequest, MldsaKeygenExpectedResultsRequest


SEED_32_BYTES = "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
MESSAGE_HEX = "00010203040506070809"
BAD_MESSAGE_HEX = "00010203040506070808"
CONTEXT_HEX = "0A0B0C"
BAD_CONTEXT_HEX = "0A0B0D"
MU_64_BYTES = (
    "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
    "202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D3E3F"
)
BAD_MU_64_BYTES = (
    "100102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
    "202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D3E3F"
)
RND_32_BYTES = "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"


def test_generic_keygen_matches_existing_keygen_generator() -> None:
    prompt = _keygen_prompt()

    assert generate_expected_results_from_prompt(prompt) == (
        generate_keygen_expected_results_from_prompt(prompt)
    )


def test_generic_siggen_internal_message_deterministic_shape() -> None:
    keypair = _keypair()
    prompt = _siggen_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "internal",
            "externalMu": False,
            "deterministic": True,
            "tests": [
                {"tcId": 1, "sk": keypair["sk"], "message": MESSAGE_HEX},
            ],
        }
    )

    expected = generate_expected_results_from_prompt(prompt)
    test = _single_test(expected)

    _assert_common_response(expected, prompt, "sigGen")
    assert sorted(expected["testGroups"][0]) == ["tests", "tgId"]
    assert sorted(test) == ["signature", "tcId"]
    assert test["tcId"] == 1
    assert len(test["signature"]) == 2420 * 2


def test_generic_siggen_internal_external_mu_randomized_shape() -> None:
    keypair = _keypair()
    prompt = _siggen_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "internal",
            "externalMu": True,
            "deterministic": False,
            "tests": [
                {
                    "tcId": 2,
                    "sk": keypair["sk"],
                    "mu": MU_64_BYTES,
                    "rnd": RND_32_BYTES,
                },
            ],
        }
    )

    expected = generate_expected_results_from_prompt(prompt)
    test = _single_test(expected)

    assert sorted(test) == ["signature", "tcId"]
    assert test["tcId"] == 2
    assert len(test["signature"]) == 2420 * 2


def test_generic_siggen_external_pure_shape() -> None:
    keypair = _keypair()
    prompt = _siggen_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "external",
            "preHash": "pure",
            "deterministic": True,
            "tests": [
                {
                    "tcId": 3,
                    "sk": keypair["sk"],
                    "message": MESSAGE_HEX,
                    "context": CONTEXT_HEX,
                },
            ],
        }
    )

    test = _single_test(generate_expected_results_from_prompt(prompt))

    assert sorted(test) == ["signature", "tcId"]
    assert test["tcId"] == 3
    assert len(test["signature"]) == 2420 * 2


def test_generic_siggen_external_prehash_shape() -> None:
    keypair = _keypair()
    prompt = _siggen_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "external",
            "preHash": "preHash",
            "deterministic": False,
            "tests": [
                {
                    "tcId": 4,
                    "sk": keypair["sk"],
                    "message": MESSAGE_HEX,
                    "rnd": RND_32_BYTES,
                    "context": CONTEXT_HEX,
                    "hashAlg": "SHA2-256",
                },
            ],
        }
    )

    test = _single_test(generate_expected_results_from_prompt(prompt))

    assert sorted(test) == ["signature", "tcId"]
    assert test["tcId"] == 4
    assert len(test["signature"]) == 2420 * 2


def test_generic_sigver_internal_message_true_case() -> None:
    keypair = _keypair()
    signature = siggen_internal("ML-DSA-44", keypair["sk"], MESSAGE_HEX)["signature"]
    prompt = _sigver_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "internal",
            "externalMu": False,
            "tests": [
                {
                    "tcId": 5,
                    "pk": keypair["pk"],
                    "message": MESSAGE_HEX,
                    "signature": signature,
                },
            ],
        }
    )

    assert _single_test(generate_expected_results_from_prompt(prompt)) == {
        "tcId": 5,
        "testPassed": True,
    }


def test_generic_sigver_internal_external_mu_false_case() -> None:
    keypair = _keypair()
    signature = siggen_internal(
        "ML-DSA-44",
        keypair["sk"],
        None,
        mu_hex=MU_64_BYTES,
        external_mu=True,
    )["signature"]
    prompt = _sigver_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "internal",
            "externalMu": True,
            "tests": [
                {
                    "tcId": 6,
                    "pk": keypair["pk"],
                    "mu": BAD_MU_64_BYTES,
                    "signature": signature,
                },
            ],
        }
    )

    assert _single_test(generate_expected_results_from_prompt(prompt)) == {
        "tcId": 6,
        "testPassed": False,
    }


def test_generic_sigver_external_pure_true_and_false_cases() -> None:
    keypair = _keypair()
    signature = siggen_internal(
        "ML-DSA-44",
        keypair["sk"],
        MESSAGE_HEX,
        signature_interface="external",
        pre_hash="pure",
        context_hex=CONTEXT_HEX,
    )["signature"]
    prompt = _sigver_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "external",
            "preHash": "pure",
            "tests": [
                {
                    "tcId": 7,
                    "pk": keypair["pk"],
                    "message": MESSAGE_HEX,
                    "context": CONTEXT_HEX,
                    "signature": signature,
                },
                {
                    "tcId": 8,
                    "pk": keypair["pk"],
                    "message": MESSAGE_HEX,
                    "context": BAD_CONTEXT_HEX,
                    "signature": signature,
                },
            ],
        }
    )

    tests = generate_expected_results_from_prompt(prompt)["testGroups"][0]["tests"]

    assert tests == [
        {"tcId": 7, "testPassed": True},
        {"tcId": 8, "testPassed": False},
    ]


def test_generic_sigver_external_prehash_true_and_false_cases() -> None:
    keypair = _keypair()
    signature = siggen_internal(
        "ML-DSA-44",
        keypair["sk"],
        MESSAGE_HEX,
        signature_interface="external",
        pre_hash="preHash",
        context_hex=CONTEXT_HEX,
        hash_alg="SHA2-256",
    )["signature"]
    prompt = _sigver_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "external",
            "preHash": "preHash",
            "tests": [
                {
                    "tcId": 9,
                    "pk": keypair["pk"],
                    "message": MESSAGE_HEX,
                    "context": CONTEXT_HEX,
                    "hashAlg": "SHA2-256",
                    "signature": signature,
                },
                {
                    "tcId": 10,
                    "pk": keypair["pk"],
                    "message": BAD_MESSAGE_HEX,
                    "context": CONTEXT_HEX,
                    "hashAlg": "SHA2-256",
                    "signature": signature,
                },
            ],
        }
    )

    tests = generate_expected_results_from_prompt(prompt)["testGroups"][0]["tests"]

    assert tests == [
        {"tcId": 9, "testPassed": True},
        {"tcId": 10, "testPassed": False},
    ]


def test_generic_array_container_preserved() -> None:
    prompt = [{"acvVersion": "1.0"}, _keygen_prompt()]

    expected = generate_expected_results_from_prompt(prompt)

    assert isinstance(expected, list)
    assert expected[0] == {"acvVersion": "1.0"}
    assert expected[1] == generate_keygen_expected_results_from_prompt(prompt)[1]


def test_generic_top_level_is_sample_preserved() -> None:
    prompt = _keygen_prompt()
    prompt["isSample"] = True

    expected = generate_expected_results_from_prompt(prompt)

    assert expected["isSample"] is True


def test_generic_invalid_prompt_raises_schema_error() -> None:
    with pytest.raises(AcvpSchemaError):
        generate_expected_results_from_prompt({"mode": "bad"})


def test_generic_endpoint_route_supports_keygen_siggen_sigver_and_errors() -> None:
    keygen_body = mldsa_expected_results(
        MldsaExpectedResultsRequest(prompt=_keygen_prompt())
    )
    old_keygen_body = mldsa_keygen_expected_results(
        MldsaKeygenExpectedResultsRequest(prompt=_keygen_prompt())
    )
    keypair = _keypair()
    siggen_prompt = _siggen_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "internal",
            "externalMu": False,
            "deterministic": True,
            "tests": [
                {"tcId": 11, "sk": keypair["sk"], "message": MESSAGE_HEX},
            ],
        }
    )
    siggen_body = mldsa_expected_results(MldsaExpectedResultsRequest(prompt=siggen_prompt))
    sigver_prompt = _sigver_prompt(
        {
            "tgId": 1,
            "testType": "AFT",
            "parameterSet": "ML-DSA-44",
            "signatureInterface": "internal",
            "externalMu": False,
            "tests": [
                {
                    "tcId": 12,
                    "pk": keypair["pk"],
                    "message": MESSAGE_HEX,
                    "signature": siggen_body.expectedResults["testGroups"][0]["tests"][0][
                        "signature"
                    ],
                },
            ],
        }
    )
    sigver_body = mldsa_expected_results(MldsaExpectedResultsRequest(prompt=sigver_prompt))

    assert keygen_body.mode == "keyGen"
    assert keygen_body.expectedResults == old_keygen_body.expectedResults
    assert siggen_body.mode == "sigGen"
    assert sorted(siggen_body.expectedResults["testGroups"][0]["tests"][0]) == [
        "signature",
        "tcId",
    ]
    assert sigver_body.mode == "sigVer"
    assert sigver_body.expectedResults["testGroups"][0]["tests"][0] == {
        "tcId": 12,
        "testPassed": True,
    }

    with pytest.raises(HTTPException) as exc_info:
        mldsa_expected_results(MldsaExpectedResultsRequest(prompt={"mode": "bad"}))
    assert exc_info.value.status_code == 400


def _keypair() -> Dict[str, str]:
    return keygen_internal("ML-DSA-44", SEED_32_BYTES)


def _keygen_prompt() -> Dict[str, Any]:
    return {
        "vsId": 7000,
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


def _siggen_prompt(group: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "vsId": 7001,
        "algorithm": "ML-DSA",
        "mode": "sigGen",
        "revision": "FIPS204",
        "testGroups": [group],
    }


def _sigver_prompt(group: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "vsId": 7002,
        "algorithm": "ML-DSA",
        "mode": "sigVer",
        "revision": "FIPS204",
        "testGroups": [group],
    }


def _single_test(expected_results: Dict[str, Any]) -> Dict[str, Any]:
    return expected_results["testGroups"][0]["tests"][0]


def _assert_common_response(
    expected_results: Dict[str, Any],
    prompt: Dict[str, Any],
    mode: str,
) -> None:
    assert expected_results["vsId"] == prompt["vsId"]
    assert expected_results["algorithm"] == "ML-DSA"
    assert expected_results["mode"] == mode
    assert expected_results["revision"] == "FIPS204"
