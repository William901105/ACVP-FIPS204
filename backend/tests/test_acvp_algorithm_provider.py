from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

import pytest

from app.acvp_core.registry import (
    AlgorithmProviderRegistry,
    DuplicateProviderError,
    ProviderNotFoundError,
    get_provider,
)
from app.acvp_mldsa.provider import (
    MldsaProvider,
    ensure_mldsa_provider_registered,
    get_mldsa_provider,
)


CAMPAIGN_SEED = "00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF"


def setup_module() -> None:
    ensure_mldsa_provider_registered()


def test_default_registry_has_mldsa_provider_for_all_modes() -> None:
    for mode in ("keyGen", "sigGen", "sigVer"):
        provider = get_provider("ML-DSA", mode, "FIPS204")
        assert provider.supports("ML-DSA", mode, "FIPS204")


def test_unknown_algorithm_raises_clear_registry_error() -> None:
    registry = AlgorithmProviderRegistry()
    registry.register_provider(get_mldsa_provider())

    with pytest.raises(ProviderNotFoundError) as exc_info:
        registry.get_provider("ML-KEM", "keyGen", "FIPS203")

    assert exc_info.value.algorithm == "ML-KEM"
    assert exc_info.value.mode == "keyGen"
    assert exc_info.value.revision == "FIPS203"


def test_duplicate_provider_registration_is_rejected() -> None:
    registry = AlgorithmProviderRegistry()
    registry.register_provider(MldsaProvider())

    with pytest.raises(DuplicateProviderError):
        registry.register_provider(MldsaProvider())


def test_mldsa_provider_validates_and_negotiates_keygen_registration() -> None:
    provider = get_mldsa_provider()
    registration = provider.validate_registration(_keygen_registration())
    negotiated = provider.negotiate_capabilities(registration)

    assert registration["algorithm"] == "ML-DSA"
    assert negotiated["algorithm"] == "ML-DSA"
    assert negotiated["revision"] == "FIPS204"
    assert negotiated["negotiated"][0]["mode"] == "keyGen"
    assert negotiated["unsupported"] == []


def test_mldsa_provider_generates_local_debug_vectors_and_expected_results() -> None:
    provider = get_mldsa_provider()
    negotiated = provider.negotiate_capabilities(_keygen_registration())
    prompts = provider.generate_vector_sets(
        negotiated,
        campaign_seed=CAMPAIGN_SEED,
        tests_per_group=2,
        generation_profile="local-debug",
    )
    prompt = prompts[0]
    expected = provider.generate_expected_results(prompt)

    provider.validate_prompt(prompt)
    provider.validate_response(expected, expected_mode="keyGen")
    assert prompt["mode"] == "keyGen"
    assert len(prompt["testGroups"][0]["tests"]) == 2


def test_mldsa_provider_generates_nist_conformance_keygen_minimums() -> None:
    provider = get_mldsa_provider()
    negotiated = provider.negotiate_capabilities(_keygen_registration())
    prompts = provider.generate_vector_sets(
        negotiated,
        campaign_seed=CAMPAIGN_SEED,
        tests_per_group=1,
        generation_profile="nist-conformance",
    )

    assert len(prompts[0]["testGroups"][0]["tests"]) >= 25


def test_mldsa_provider_validate_results_passes_matching_and_fails_wrong_response() -> None:
    provider = get_mldsa_provider()
    prompt = provider.generate_vector_sets(
        provider.negotiate_capabilities(_keygen_registration()),
        campaign_seed=CAMPAIGN_SEED,
        tests_per_group=1,
        generation_profile="local-debug",
    )[0]
    expected = provider.generate_expected_results(prompt)
    wrong = copy.deepcopy(expected)
    wrong["testGroups"][0]["tests"][0]["pk"] = _mutate_hex(
        wrong["testGroups"][0]["tests"][0]["pk"]
    )

    passed = provider.validate_results(
        prompt=prompt,
        expected_results=expected,
        response=copy.deepcopy(expected),
    )
    failed = provider.validate_results(
        prompt=prompt,
        expected_results=expected,
        response=wrong,
    )

    assert passed["summary"]["failed"] == 0
    assert failed["summary"]["failed"] > 0


def _keygen_registration(parameter_sets: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "algorithm": "ML-DSA",
        "mode": "keyGen",
        "revision": "FIPS204",
        "prereqVals": [{"algorithm": "SHA", "valValue": "same"}],
        "parameterSets": parameter_sets or ["ML-DSA-44"],
    }


def _mutate_hex(value: str) -> str:
    return ("0" if value[0] != "0" else "1") + value[1:]
