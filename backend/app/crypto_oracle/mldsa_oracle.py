from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


class MldsaOracleError(Exception):
    """Base error raised by the ML-DSA native oracle wrapper."""


class MldsaOracleInputError(MldsaOracleError):
    """Raised when the caller provides invalid oracle input."""


class MldsaOracleConfigError(MldsaOracleError):
    """Raised when the native oracle binary is missing or misconfigured."""


class MldsaOracleExecutionError(MldsaOracleError):
    """Raised when the native oracle fails or returns invalid output."""


_BACKEND_DIR = Path(__file__).resolve().parents[2]
_NATIVE_DIR = _BACKEND_DIR / "native" / "mldsa_oracle"
_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")

_PARAMETER_SETS = {
    "ML-DSA-44": {
        "binary": _NATIVE_DIR / "bin" / "mldsa44_keygen_oracle",
        "pk_bytes": 1312,
        "sk_bytes": 2560,
    },
    "ML-DSA-65": {
        "binary": _NATIVE_DIR / "bin" / "mldsa65_keygen_oracle",
        "pk_bytes": 1952,
        "sk_bytes": 4032,
    },
    "ML-DSA-87": {
        "binary": _NATIVE_DIR / "bin" / "mldsa87_keygen_oracle",
        "pk_bytes": 2592,
        "sk_bytes": 4896,
    },
}


def keygen_internal(parameter_set: str, seed_hex: str) -> dict[str, str]:
    if parameter_set not in _PARAMETER_SETS:
        supported = ", ".join(sorted(_PARAMETER_SETS))
        raise MldsaOracleInputError(
            f"unsupported parameterSet {parameter_set!r}; supported values: {supported}"
        )

    seed = _normalize_seed(seed_hex)
    config = _PARAMETER_SETS[parameter_set]
    binary = config["binary"]
    if not isinstance(binary, Path):
        raise MldsaOracleConfigError("invalid ML-DSA oracle binary configuration")
    if not binary.exists():
        raise MldsaOracleConfigError(
            "native ML-DSA oracle binary not found at "
            f"{binary}. Run `make` in {_NATIVE_DIR} first."
        )

    completed = _run_oracle(binary, seed)
    output = _parse_json(completed.stdout)
    pk = _validate_hex_field(output, "pk", int(config["pk_bytes"]))
    sk = _validate_hex_field(output, "sk", int(config["sk_bytes"]))
    return {"pk": pk, "sk": sk}


def _normalize_seed(seed_hex: str) -> str:
    if len(seed_hex) != 64:
        raise MldsaOracleInputError("seed must be exactly 64 hex characters")
    if _HEX_RE.fullmatch(seed_hex) is None:
        raise MldsaOracleInputError("seed must contain only hex characters")
    return seed_hex.upper()


def _run_oracle(binary: Path, seed_hex: str) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            [str(binary), seed_hex],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise MldsaOracleExecutionError(
            f"native ML-DSA oracle timed out after {exc.timeout} seconds"
        ) from exc
    except OSError as exc:
        raise MldsaOracleExecutionError(
            f"failed to execute native ML-DSA oracle {binary}: {exc}"
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or "no stderr output"
        raise MldsaOracleExecutionError(
            f"native ML-DSA oracle failed with exit code {completed.returncode}: {detail}"
        )

    return completed


def _parse_json(stdout: str) -> dict[str, Any]:
    try:
        output = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise MldsaOracleExecutionError(
            f"native ML-DSA oracle returned invalid JSON: {exc}"
        ) from exc

    if not isinstance(output, dict):
        raise MldsaOracleExecutionError("native ML-DSA oracle returned non-object JSON")
    return output


def _validate_hex_field(output: dict[str, Any], field: str, expected_bytes: int) -> str:
    value = output.get(field)
    expected_hex_chars = expected_bytes * 2
    if not isinstance(value, str):
        raise MldsaOracleExecutionError(f"native ML-DSA oracle missing {field!r}")
    if len(value) != expected_hex_chars:
        raise MldsaOracleExecutionError(
            f"native ML-DSA oracle returned {field} with {len(value)} hex chars; "
            f"expected {expected_hex_chars}"
        )
    if _HEX_RE.fullmatch(value) is None:
        raise MldsaOracleExecutionError(
            f"native ML-DSA oracle returned non-hex {field}"
        )
    return value.upper()
