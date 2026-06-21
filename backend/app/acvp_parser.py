from __future__ import annotations

from typing import Any


ACVP_VECTOR_KEYS = {"vsId", "algorithm", "mode", "revision", "testGroups"}


class AcvpParseError(ValueError):
    """Raised when an input cannot be treated as an ACVP vector set."""


def normalize_acvp_json(data: Any) -> dict[str, Any]:
    """Return the vector-set object from common ACVP top-level shapes."""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and (
                "testGroups" in item or ACVP_VECTOR_KEYS.intersection(item.keys())
            ):
                return item
        raise AcvpParseError("ACVP array did not contain a vector-set object")

    if isinstance(data, dict):
        if "testGroups" in data or ACVP_VECTOR_KEYS.intersection(data.keys()):
            return data
        raise AcvpParseError("ACVP object did not contain vector-set fields")

    raise AcvpParseError("ACVP JSON must be an object or array")


def extract_vector_set(data: Any) -> dict[str, Any]:
    return normalize_acvp_json(data)


def extract_algorithm_metadata(vector_set: dict[str, Any]) -> dict[str, Any]:
    return {
        "vsId": vector_set.get("vsId"),
        "algorithm": vector_set.get("algorithm"),
        "mode": vector_set.get("mode") or vector_set.get("operation"),
        "revision": vector_set.get("revision"),
    }


def get_test_groups(vector_set: dict[str, Any]) -> list[dict[str, Any]]:
    groups = vector_set.get("testGroups", [])
    return groups if isinstance(groups, list) else []


def flatten_test_cases(vector_set: dict[str, Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for group in get_test_groups(vector_set):
        if not isinstance(group, dict):
            continue
        tests = group.get("tests", [])
        if not isinstance(tests, list):
            tests = []
        group_meta = {key: value for key, value in group.items() if key != "tests"}
        for test in tests:
            if not isinstance(test, dict):
                continue
            flattened.append(
                {
                    "tgId": group.get("tgId"),
                    "tcId": test.get("tcId"),
                    "group": group_meta,
                    "test": test,
                }
            )
    return flattened


def index_test_cases(vector_set: dict[str, Any]) -> dict[tuple[Any, Any], dict[str, Any]]:
    return {
        (case["tgId"], case["tcId"]): case["test"]
        for case in flatten_test_cases(vector_set)
        if case.get("tgId") is not None and case.get("tcId") is not None
    }


def summarize_vector_set(vector_set: dict[str, Any]) -> dict[str, Any]:
    groups = get_test_groups(vector_set)
    return {
        **extract_algorithm_metadata(vector_set),
        "testGroupCount": len(groups),
        "testCaseCount": len(flatten_test_cases(vector_set)),
    }

