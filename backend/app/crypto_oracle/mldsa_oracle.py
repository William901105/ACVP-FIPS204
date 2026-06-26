from __future__ import annotations

from typing import Optional

from .mldsa_constants import MLDSA_NATIVE_ORACLE_DIR, SUPPORTED_PARAMETER_SETS
from .mldsa_errors import (
    MldsaOracleConfigError,
    MldsaOracleError,
    MldsaOracleExecutionError,
    MldsaOracleInputError,
)
from .mldsa_helpers import (
    normalize_hex,
    parse_json_output,
    run_native_binary,
    validate_bool_output,
    validate_hex_output,
    validate_parameter_set,
)


_NATIVE_DIR = MLDSA_NATIVE_ORACLE_DIR
_PARAMETER_SETS = SUPPORTED_PARAMETER_SETS


def keygen_internal(parameter_set: str, seed_hex: str) -> dict[str, str]:
    config = validate_parameter_set(parameter_set)
    seed = normalize_hex("seed", seed_hex, int(config["seed_bytes"]))
    completed = run_native_binary(config["keygen_binary"], [seed])
    output = parse_json_output(completed.stdout)
    pk = validate_hex_output(output, "pk", int(config["pk_bytes"]))
    sk = validate_hex_output(output, "sk", int(config["sk_bytes"]))
    return {"pk": pk, "sk": sk}


def siggen_internal(
    parameter_set: str,
    sk_hex: str,
    message_hex: Optional[str] = None,
    *,
    mu_hex: Optional[str] = None,
    rnd_hex: Optional[str] = None,
    external_mu: bool = False,
    deterministic: bool = True,
) -> dict[str, str]:
    config = validate_parameter_set(parameter_set)
    sk = normalize_hex("sk", sk_hex, int(config["sk_bytes"]))

    if external_mu:
        if message_hex is not None:
            raise MldsaOracleInputError("message is not allowed when externalMu=true")
        if mu_hex is None:
            raise MldsaOracleInputError("mu is required when externalMu=true")
        input_hex = normalize_hex("mu", mu_hex, int(config["mu_bytes"]))
    else:
        if message_hex is None:
            raise MldsaOracleInputError("message is required when externalMu=false")
        if mu_hex is not None:
            raise MldsaOracleInputError("mu is not allowed when externalMu=false")
        input_hex = normalize_hex("message", message_hex)

    args = ["1" if external_mu else "0", "1" if deterministic else "0", sk, input_hex]
    if deterministic:
        if rnd_hex is not None:
            raise MldsaOracleInputError("rnd is not allowed when deterministic=true")
    else:
        if rnd_hex is None:
            raise MldsaOracleInputError("rnd is required when deterministic=false")
        args.append(normalize_hex("rnd", rnd_hex, int(config["rnd_bytes"])))

    completed = run_native_binary(config["siggen_binary"], args)
    output = parse_json_output(completed.stdout)
    signature = validate_hex_output(output, "signature", int(config["sig_bytes"]))
    return {"signature": signature}


def sigver_internal(
    parameter_set: str,
    pk_hex: str,
    message_hex: Optional[str],
    signature_hex: str,
    *,
    mu_hex: Optional[str] = None,
    external_mu: bool = False,
) -> dict[str, bool]:
    config = validate_parameter_set(parameter_set)
    pk = normalize_hex("pk", pk_hex, int(config["pk_bytes"]))
    signature = normalize_hex("signature", signature_hex, int(config["sig_bytes"]))

    if external_mu:
        if message_hex is not None:
            raise MldsaOracleInputError("message is not allowed when externalMu=true")
        if mu_hex is None:
            raise MldsaOracleInputError("mu is required when externalMu=true")
        input_hex = normalize_hex("mu", mu_hex, int(config["mu_bytes"]))
    else:
        if message_hex is None:
            raise MldsaOracleInputError("message is required when externalMu=false")
        if mu_hex is not None:
            raise MldsaOracleInputError("mu is not allowed when externalMu=false")
        input_hex = normalize_hex("message", message_hex)

    completed = run_native_binary(
        config["sigver_binary"],
        ["1" if external_mu else "0", pk, input_hex, signature],
    )
    output = parse_json_output(completed.stdout)
    test_passed = validate_bool_output(output, "testPassed")
    return {"testPassed": test_passed}
