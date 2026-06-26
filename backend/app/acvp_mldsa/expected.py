from __future__ import annotations

from typing import Any, Dict, List

from ..crypto_oracle.mldsa_oracle import keygen_internal, siggen_internal, sigver_internal
from .constants import ALGORITHM, REVISION
from .errors import AcvpSchemaError
from .validators import validate_mldsa_vector_set


def generate_expected_results_from_prompt(prompt: Any) -> Any:
    vector_set = validate_mldsa_vector_set(prompt)
    mode = vector_set["mode"]

    if mode == "keyGen":
        expected_results = _build_keygen_expected_results(vector_set)
    elif mode == "sigGen":
        expected_results = _build_siggen_expected_results(vector_set)
    elif mode == "sigVer":
        expected_results = _build_sigver_expected_results(vector_set)
    else:
        raise AcvpSchemaError(
            "invalid_mode",
            f"Unsupported ML-DSA mode: {mode!r}",
            "$.mode",
        )

    if isinstance(prompt, list):
        return [_version_object(prompt), expected_results]
    return expected_results


def generate_keygen_expected_results_from_prompt(prompt: Any) -> Any:
    vector_set = validate_mldsa_vector_set(prompt)
    _require_keygen_prompt(vector_set)
    expected_results = _build_keygen_expected_results(vector_set)

    if isinstance(prompt, list):
        return [_version_object(prompt), expected_results]
    return expected_results


def _require_keygen_prompt(vector_set: Dict[str, Any]) -> None:
    algorithm = vector_set.get("algorithm")
    if algorithm != ALGORITHM:
        raise AcvpSchemaError(
            "unsupported_algorithm",
            f"Unsupported algorithm: {algorithm}",
            "$.algorithm",
        )

    mode = vector_set.get("mode")
    if mode != "keyGen":
        raise AcvpSchemaError(
            "invalid_mode",
            f"Expected ML-DSA keyGen prompt; got mode {mode!r}",
            "$.mode",
        )

    revision = vector_set.get("revision")
    if revision != REVISION:
        raise AcvpSchemaError(
            "unsupported_revision",
            f"Unsupported revision: {revision}",
            "$.revision",
        )


def _build_response_vector_set(
    vector_set: Dict[str, Any],
    test_groups: List[Dict[str, Any]],
) -> Dict[str, Any]:
    expected_results = {
        "vsId": vector_set["vsId"],
        "algorithm": ALGORITHM,
        "mode": vector_set["mode"],
        "revision": REVISION,
        "testGroups": test_groups,
    }
    if "isSample" in vector_set:
        expected_results["isSample"] = vector_set["isSample"]
    return expected_results


def _build_keygen_expected_results(vector_set: Dict[str, Any]) -> Dict[str, Any]:
    return _build_response_vector_set(
        vector_set,
        [_build_keygen_expected_group(group) for group in vector_set["testGroups"]],
    )


def _build_keygen_expected_group(group: Dict[str, Any]) -> Dict[str, Any]:
    parameter_set = group["parameterSet"]
    tests: List[Dict[str, Any]] = []
    for test in group["tests"]:
        result = keygen_internal(parameter_set, test["seed"])
        tests.append({"tcId": test["tcId"], "pk": result["pk"], "sk": result["sk"]})
    return {"tgId": group["tgId"], "tests": tests}


def _build_siggen_expected_results(vector_set: Dict[str, Any]) -> Dict[str, Any]:
    return _build_response_vector_set(
        vector_set,
        [_build_siggen_expected_group(group) for group in vector_set["testGroups"]],
    )


def _build_siggen_expected_group(group: Dict[str, Any]) -> Dict[str, Any]:
    parameter_set = group["parameterSet"]
    deterministic = group["deterministic"]
    signature_interface = group["signatureInterface"]
    tests: List[Dict[str, Any]] = []

    for test in group["tests"]:
        if signature_interface == "internal":
            result = _siggen_internal_result(parameter_set, deterministic, group, test)
        else:
            result = _siggen_external_result(parameter_set, deterministic, group, test)
        tests.append({"tcId": test["tcId"], "signature": result["signature"]})

    return {"tgId": group["tgId"], "tests": tests}


def _siggen_internal_result(
    parameter_set: str,
    deterministic: bool,
    group: Dict[str, Any],
    test: Dict[str, Any],
) -> Dict[str, str]:
    external_mu = group["externalMu"]
    rnd_hex = None if deterministic else test["rnd"]
    if external_mu:
        return siggen_internal(
            parameter_set,
            test["sk"],
            None,
            mu_hex=test["mu"],
            rnd_hex=rnd_hex,
            external_mu=True,
            deterministic=deterministic,
            signature_interface="internal",
        )

    return siggen_internal(
        parameter_set,
        test["sk"],
        test["message"],
        rnd_hex=rnd_hex,
        external_mu=False,
        deterministic=deterministic,
        signature_interface="internal",
    )


def _siggen_external_result(
    parameter_set: str,
    deterministic: bool,
    group: Dict[str, Any],
    test: Dict[str, Any],
) -> Dict[str, str]:
    pre_hash = group["preHash"]
    return siggen_internal(
        parameter_set,
        test["sk"],
        test["message"],
        rnd_hex=None if deterministic else test["rnd"],
        external_mu=False,
        deterministic=deterministic,
        signature_interface="external",
        pre_hash=pre_hash,
        context_hex=test["context"],
        hash_alg=test.get("hashAlg"),
    )


def _build_sigver_expected_results(vector_set: Dict[str, Any]) -> Dict[str, Any]:
    return _build_response_vector_set(
        vector_set,
        [_build_sigver_expected_group(group) for group in vector_set["testGroups"]],
    )


def _build_sigver_expected_group(group: Dict[str, Any]) -> Dict[str, Any]:
    parameter_set = group["parameterSet"]
    signature_interface = group["signatureInterface"]
    tests: List[Dict[str, Any]] = []

    for test in group["tests"]:
        if signature_interface == "internal":
            result = _sigver_internal_result(parameter_set, group, test)
        else:
            result = _sigver_external_result(parameter_set, group, test)
        tests.append({"tcId": test["tcId"], "testPassed": result["testPassed"]})

    return {"tgId": group["tgId"], "tests": tests}


def _sigver_internal_result(
    parameter_set: str,
    group: Dict[str, Any],
    test: Dict[str, Any],
) -> Dict[str, bool]:
    external_mu = group["externalMu"]
    if external_mu:
        return sigver_internal(
            parameter_set,
            test["pk"],
            None,
            test["signature"],
            mu_hex=test["mu"],
            external_mu=True,
            signature_interface="internal",
        )

    return sigver_internal(
        parameter_set,
        test["pk"],
        test["message"],
        test["signature"],
        external_mu=False,
        signature_interface="internal",
    )


def _sigver_external_result(
    parameter_set: str,
    group: Dict[str, Any],
    test: Dict[str, Any],
) -> Dict[str, bool]:
    pre_hash = group["preHash"]
    return sigver_internal(
        parameter_set,
        test["pk"],
        test["message"],
        test["signature"],
        external_mu=False,
        signature_interface="external",
        pre_hash=pre_hash,
        context_hex=test["context"],
        hash_alg=test.get("hashAlg"),
    )


def _version_object(prompt: List[Any]) -> Dict[str, Any]:
    if prompt and isinstance(prompt[0], dict):
        return dict(prompt[0])
    return {}
