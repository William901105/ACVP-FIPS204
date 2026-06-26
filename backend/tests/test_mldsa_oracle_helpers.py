from __future__ import annotations

import json
import subprocess
import warnings
from pathlib import Path

import pytest

from app.crypto_oracle.mldsa_constants import SUPPORTED_PARAMETER_SETS
from app.crypto_oracle.mldsa_errors import (
    MldsaOracleExecutionError,
    MldsaOracleInputError,
)
from app.crypto_oracle.mldsa_helpers import (
    normalize_hex,
    parse_json_output,
    validate_bool_output,
    validate_parameter_set,
)
from app.crypto_oracle.mldsa_oracle import (
    keygen_internal,
    siggen_internal,
    sigver_internal,
)


SEED_32_BYTES = "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
MESSAGE_HEX = "00010203040506070809"
MU_64_BYTES = (
    "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
    "202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D3E3F"
)
BAD_MU_64_BYTES = (
    "100102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
    "202122232425262728292A2B2C2D2E2F303132333435363738393A3B3C3D3E3F"
)
RND_32_BYTES = "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
RND_32_BYTES_ALT = "1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A09080706050403020100"
SKIP_NATIVE_REASON = (
    "native keyGen oracle binary not built; run make in backend/native/mldsa_oracle"
)
SKIP_SIGGEN_NATIVE_REASON = (
    "native sigGen oracle binary not built; run make in backend/native/mldsa_oracle"
)
SKIP_SIGVER_NATIVE_REASON = (
    "native sigVer oracle binary not built; run make in backend/native/mldsa_oracle"
)


def test_normalize_hex_uppercases_lowercase() -> None:
    assert normalize_hex("seed", "0a0b", expected_bytes=2) == "0A0B"


def test_normalize_hex_rejects_invalid_hex() -> None:
    with pytest.raises(MldsaOracleInputError):
        normalize_hex("seed", "not-hex", expected_bytes=32)


def test_normalize_hex_rejects_wrong_length() -> None:
    with pytest.raises(MldsaOracleInputError):
        normalize_hex("seed", "00", expected_bytes=32)


def test_normalize_hex_rejects_odd_length() -> None:
    with pytest.raises(MldsaOracleInputError):
        normalize_hex("message", "ABC")


def test_validate_parameter_set_rejects_unsupported_value() -> None:
    with pytest.raises(MldsaOracleInputError):
        validate_parameter_set("ML-DSA-99")


def test_parse_json_output_accepts_valid_json() -> None:
    assert parse_json_output('{"pk": "AA", "sk": "BB"}') == {"pk": "AA", "sk": "BB"}


def test_parse_json_output_rejects_invalid_json() -> None:
    with pytest.raises(MldsaOracleExecutionError):
        parse_json_output("{not-json")


def test_validate_bool_output_accepts_boolean() -> None:
    assert validate_bool_output({"testPassed": False}, "testPassed") is False


def test_validate_bool_output_rejects_missing_or_non_boolean() -> None:
    with pytest.raises(MldsaOracleExecutionError):
        validate_bool_output({}, "testPassed")
    with pytest.raises(MldsaOracleExecutionError):
        validate_bool_output({"testPassed": "true"}, "testPassed")


def test_keygen_internal_returns_deterministic_uppercase_hex() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")

    first = keygen_internal("ML-DSA-44", SEED_32_BYTES.lower())
    second = keygen_internal("ML-DSA-44", SEED_32_BYTES.lower())

    assert first == second
    assert len(first["pk"]) == 1312 * 2
    assert len(first["sk"]) == 2560 * 2
    assert first["pk"] == first["pk"].upper()
    assert first["sk"] == first["sk"].upper()


def test_siggen_internal_returns_deterministic_uppercase_signature() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")

    sk = keygen_internal("ML-DSA-44", SEED_32_BYTES)["sk"]
    first = siggen_internal("ML-DSA-44", sk, MESSAGE_HEX.lower())
    second = siggen_internal("ML-DSA-44", sk, MESSAGE_HEX.lower())

    assert first == second
    assert len(first["signature"]) == 2420 * 2
    assert first["signature"] == first["signature"].upper()


def test_siggen_internal_supports_randomized_and_external_mu_modes() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")

    sk = keygen_internal("ML-DSA-44", SEED_32_BYTES)["sk"]
    message_randomized = siggen_internal(
        "ML-DSA-44",
        sk,
        MESSAGE_HEX,
        deterministic=False,
        rnd_hex=RND_32_BYTES,
    )
    same_randomized = siggen_internal(
        "ML-DSA-44",
        sk,
        MESSAGE_HEX,
        deterministic=False,
        rnd_hex=RND_32_BYTES,
    )
    mu_deterministic = siggen_internal(
        "ML-DSA-44",
        sk,
        None,
        mu_hex=MU_64_BYTES.lower(),
        external_mu=True,
    )
    mu_randomized = siggen_internal(
        "ML-DSA-44",
        sk,
        None,
        mu_hex=MU_64_BYTES,
        external_mu=True,
        deterministic=False,
        rnd_hex=RND_32_BYTES,
    )

    assert message_randomized == same_randomized
    assert len(message_randomized["signature"]) == 2420 * 2
    assert len(mu_deterministic["signature"]) == 2420 * 2
    assert len(mu_randomized["signature"]) == 2420 * 2
    assert mu_deterministic["signature"] == mu_deterministic["signature"].upper()


def test_siggen_internal_rejects_invalid_sk_length() -> None:
    _skip_if_siggen_binary_missing("ML-DSA-44")

    with pytest.raises(MldsaOracleInputError):
        siggen_internal("ML-DSA-44", "00", MESSAGE_HEX)


def test_siggen_internal_rejects_invalid_message_hex() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")

    sk = keygen_internal("ML-DSA-44", SEED_32_BYTES)["sk"]
    with pytest.raises(MldsaOracleInputError):
        siggen_internal("ML-DSA-44", sk, "not-hex")


def test_siggen_internal_rejects_unsupported_parameter_set() -> None:
    with pytest.raises(MldsaOracleInputError):
        siggen_internal("ML-DSA-99", "00", MESSAGE_HEX)


def test_siggen_internal_rejects_invalid_phase25_combinations() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")

    sk = keygen_internal("ML-DSA-44", SEED_32_BYTES)["sk"]

    invalid_calls = (
        lambda: siggen_internal("ML-DSA-44", sk, MESSAGE_HEX, external_mu=True),
        lambda: siggen_internal("ML-DSA-44", sk, None, external_mu=True),
        lambda: siggen_internal(
            "ML-DSA-44",
            sk,
            MESSAGE_HEX,
            mu_hex=MU_64_BYTES,
        ),
        lambda: siggen_internal(
            "ML-DSA-44",
            sk,
            MESSAGE_HEX,
            deterministic=True,
            rnd_hex=RND_32_BYTES,
        ),
        lambda: siggen_internal(
            "ML-DSA-44",
            sk,
            MESSAGE_HEX,
            deterministic=False,
        ),
        lambda: siggen_internal(
            "ML-DSA-44",
            sk,
            None,
            mu_hex="00",
            external_mu=True,
        ),
        lambda: siggen_internal(
            "ML-DSA-44",
            sk,
            MESSAGE_HEX,
            deterministic=False,
            rnd_hex="00",
        ),
    )

    for call in invalid_calls:
        with pytest.raises(MldsaOracleInputError):
            call()


def test_native_siggen_binaries_exist() -> None:
    for parameter_set in ("ML-DSA-44", "ML-DSA-65", "ML-DSA-87"):
        _skip_if_siggen_binary_missing(parameter_set)


def test_native_siggen_binary_outputs_deterministic_json() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")

    sk = keygen_internal("ML-DSA-44", SEED_32_BYTES)["sk"]
    binary = SUPPORTED_PARAMETER_SETS["ML-DSA-44"]["siggen_binary"]
    first = subprocess.check_output([str(binary), sk, MESSAGE_HEX], text=True)
    second = subprocess.check_output([str(binary), sk, MESSAGE_HEX], text=True)
    body = json.loads(first)

    assert first == second
    assert sorted(body) == ["signature"]
    assert len(body["signature"]) == 2420 * 2
    assert body["signature"] == body["signature"].upper()


def test_native_siggen_extended_cli_supports_phase25_modes() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")

    sk = keygen_internal("ML-DSA-44", SEED_32_BYTES)["sk"]
    binary = SUPPORTED_PARAMETER_SETS["ML-DSA-44"]["siggen_binary"]
    old = subprocess.check_output([str(binary), sk, MESSAGE_HEX], text=True)
    extended = subprocess.check_output(
        [str(binary), "0", "1", sk, MESSAGE_HEX],
        text=True,
    )
    randomized = subprocess.check_output(
        [str(binary), "0", "0", sk, MESSAGE_HEX, RND_32_BYTES],
        text=True,
    )
    randomized_again = subprocess.check_output(
        [str(binary), "0", "0", sk, MESSAGE_HEX, RND_32_BYTES],
        text=True,
    )
    alt_randomized = subprocess.check_output(
        [str(binary), "0", "0", sk, MESSAGE_HEX, RND_32_BYTES_ALT],
        text=True,
    )
    mu_deterministic = json.loads(
        subprocess.check_output([str(binary), "1", "1", sk, MU_64_BYTES], text=True)
    )
    mu_randomized = json.loads(
        subprocess.check_output(
            [str(binary), "1", "0", sk, MU_64_BYTES, RND_32_BYTES],
            text=True,
        )
    )

    assert old == extended
    assert randomized == randomized_again
    if randomized == alt_randomized:
        warnings.warn("different rnd produced same signature", UserWarning)
    for body in (json.loads(old), json.loads(randomized), mu_deterministic, mu_randomized):
        assert sorted(body) == ["signature"]
        assert len(body["signature"]) == 2420 * 2
        assert body["signature"] == body["signature"].upper()


def test_native_siggen_extended_cli_rejects_invalid_combinations() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")

    sk = keygen_internal("ML-DSA-44", SEED_32_BYTES)["sk"]
    binary = SUPPORTED_PARAMETER_SETS["ML-DSA-44"]["siggen_binary"]

    invalid_commands = (
        [str(binary), "1", "1", sk, "00"],
        [str(binary), "0", "0", sk, MESSAGE_HEX],
        [str(binary), "0", "1", sk, MESSAGE_HEX, RND_32_BYTES],
    )
    for command in invalid_commands:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        assert completed.returncode != 0


def test_sigver_internal_returns_true_for_valid_signature() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")
    _skip_if_sigver_binary_missing("ML-DSA-44")

    keypair = keygen_internal("ML-DSA-44", SEED_32_BYTES)
    signature = siggen_internal("ML-DSA-44", keypair["sk"], MESSAGE_HEX)["signature"]

    assert sigver_internal("ML-DSA-44", keypair["pk"], MESSAGE_HEX, signature) == {
        "testPassed": True
    }


def test_sigver_internal_supports_external_mu() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")
    _skip_if_sigver_binary_missing("ML-DSA-44")

    keypair = keygen_internal("ML-DSA-44", SEED_32_BYTES)
    signature = siggen_internal(
        "ML-DSA-44",
        keypair["sk"],
        None,
        mu_hex=MU_64_BYTES,
        external_mu=True,
    )["signature"]

    assert sigver_internal(
        "ML-DSA-44",
        keypair["pk"],
        None,
        signature,
        mu_hex=MU_64_BYTES.lower(),
        external_mu=True,
    ) == {"testPassed": True}
    assert sigver_internal(
        "ML-DSA-44",
        keypair["pk"],
        None,
        signature,
        mu_hex=BAD_MU_64_BYTES,
        external_mu=True,
    ) == {"testPassed": False}


def test_sigver_internal_returns_false_for_mutated_message_or_signature() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")
    _skip_if_sigver_binary_missing("ML-DSA-44")

    keypair = keygen_internal("ML-DSA-44", SEED_32_BYTES)
    signature = siggen_internal("ML-DSA-44", keypair["sk"], MESSAGE_HEX)["signature"]

    assert sigver_internal(
        "ML-DSA-44",
        keypair["pk"],
        "00010203040506070808",
        signature,
    ) == {"testPassed": False}
    assert sigver_internal(
        "ML-DSA-44",
        keypair["pk"],
        MESSAGE_HEX,
        _flip_first_hex_char(signature),
    ) == {"testPassed": False}


def test_sigver_internal_rejects_invalid_inputs() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")
    _skip_if_sigver_binary_missing("ML-DSA-44")

    keypair = keygen_internal("ML-DSA-44", SEED_32_BYTES)
    signature = siggen_internal("ML-DSA-44", keypair["sk"], MESSAGE_HEX)["signature"]

    with pytest.raises(MldsaOracleInputError):
        sigver_internal("ML-DSA-44", "00", MESSAGE_HEX, signature)
    with pytest.raises(MldsaOracleInputError):
        sigver_internal("ML-DSA-44", keypair["pk"], MESSAGE_HEX, "00")
    with pytest.raises(MldsaOracleInputError):
        sigver_internal("ML-DSA-44", keypair["pk"], "not-hex", signature)
    with pytest.raises(MldsaOracleInputError):
        sigver_internal("ML-DSA-99", keypair["pk"], MESSAGE_HEX, signature)


def test_sigver_internal_rejects_invalid_external_mu_combinations() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")
    _skip_if_sigver_binary_missing("ML-DSA-44")

    keypair = keygen_internal("ML-DSA-44", SEED_32_BYTES)
    signature = siggen_internal("ML-DSA-44", keypair["sk"], MESSAGE_HEX)["signature"]

    invalid_calls = (
        lambda: sigver_internal(
            "ML-DSA-44",
            keypair["pk"],
            MESSAGE_HEX,
            signature,
            external_mu=True,
        ),
        lambda: sigver_internal(
            "ML-DSA-44",
            keypair["pk"],
            None,
            signature,
            external_mu=True,
        ),
        lambda: sigver_internal(
            "ML-DSA-44",
            keypair["pk"],
            MESSAGE_HEX,
            signature,
            mu_hex=MU_64_BYTES,
        ),
        lambda: sigver_internal(
            "ML-DSA-44",
            keypair["pk"],
            None,
            signature,
            mu_hex="00",
            external_mu=True,
        ),
    )

    for call in invalid_calls:
        with pytest.raises(MldsaOracleInputError):
            call()


def test_native_sigver_binaries_exist() -> None:
    for parameter_set in ("ML-DSA-44", "ML-DSA-65", "ML-DSA-87"):
        _skip_if_sigver_binary_missing(parameter_set)


def test_native_sigver_binary_outputs_json_true_and_false() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")
    _skip_if_sigver_binary_missing("ML-DSA-44")

    keypair = keygen_internal("ML-DSA-44", SEED_32_BYTES)
    signature = siggen_internal("ML-DSA-44", keypair["sk"], MESSAGE_HEX)["signature"]
    binary = SUPPORTED_PARAMETER_SETS["ML-DSA-44"]["sigver_binary"]

    valid = subprocess.run(
        [str(binary), keypair["pk"], MESSAGE_HEX, signature],
        check=False,
        capture_output=True,
        text=True,
    )
    bad_message = subprocess.run(
        [str(binary), keypair["pk"], "00010203040506070808", signature],
        check=False,
        capture_output=True,
        text=True,
    )
    bad_signature = subprocess.run(
        [str(binary), keypair["pk"], MESSAGE_HEX, _flip_first_hex_char(signature)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert valid.returncode == 0
    assert json.loads(valid.stdout) == {"testPassed": True}
    assert bad_message.returncode == 0
    assert json.loads(bad_message.stdout) == {"testPassed": False}
    assert bad_signature.returncode == 0
    assert json.loads(bad_signature.stdout) == {"testPassed": False}


def test_native_sigver_extended_cli_supports_external_mu() -> None:
    _skip_if_keygen_binary_missing("ML-DSA-44")
    _skip_if_siggen_binary_missing("ML-DSA-44")
    _skip_if_sigver_binary_missing("ML-DSA-44")

    keypair = keygen_internal("ML-DSA-44", SEED_32_BYTES)
    signature = siggen_internal("ML-DSA-44", keypair["sk"], MESSAGE_HEX)["signature"]
    mu_signature = siggen_internal(
        "ML-DSA-44",
        keypair["sk"],
        None,
        mu_hex=MU_64_BYTES,
        external_mu=True,
    )["signature"]
    binary = SUPPORTED_PARAMETER_SETS["ML-DSA-44"]["sigver_binary"]

    old = subprocess.run(
        [str(binary), keypair["pk"], MESSAGE_HEX, signature],
        check=False,
        capture_output=True,
        text=True,
    )
    extended = subprocess.run(
        [str(binary), "0", keypair["pk"], MESSAGE_HEX, signature],
        check=False,
        capture_output=True,
        text=True,
    )
    valid_mu = subprocess.run(
        [str(binary), "1", keypair["pk"], MU_64_BYTES, mu_signature],
        check=False,
        capture_output=True,
        text=True,
    )
    bad_mu = subprocess.run(
        [str(binary), "1", keypair["pk"], BAD_MU_64_BYTES, mu_signature],
        check=False,
        capture_output=True,
        text=True,
    )
    bad_signature = subprocess.run(
        [str(binary), "1", keypair["pk"], MU_64_BYTES, _flip_first_hex_char(mu_signature)],
        check=False,
        capture_output=True,
        text=True,
    )
    invalid_mu = subprocess.run(
        [str(binary), "1", keypair["pk"], "00", mu_signature],
        check=False,
        capture_output=True,
        text=True,
    )

    assert old.returncode == 0
    assert extended.returncode == 0
    assert old.stdout == extended.stdout
    assert json.loads(valid_mu.stdout) == {"testPassed": True}
    assert bad_mu.returncode == 0
    assert json.loads(bad_mu.stdout) == {"testPassed": False}
    assert bad_signature.returncode == 0
    assert json.loads(bad_signature.stdout) == {"testPassed": False}
    assert invalid_mu.returncode != 0


def _flip_first_hex_char(value: str) -> str:
    first = "0" if value[0] != "0" else "1"
    return first + value[1:]


def _skip_if_keygen_binary_missing(parameter_set: str) -> None:
    binary = SUPPORTED_PARAMETER_SETS[parameter_set]["keygen_binary"]
    if not isinstance(binary, Path) or not binary.exists():
        pytest.skip(SKIP_NATIVE_REASON)


def _skip_if_siggen_binary_missing(parameter_set: str) -> None:
    binary = SUPPORTED_PARAMETER_SETS[parameter_set]["siggen_binary"]
    if not isinstance(binary, Path) or not binary.exists():
        pytest.skip(SKIP_SIGGEN_NATIVE_REASON)


def _skip_if_sigver_binary_missing(parameter_set: str) -> None:
    binary = SUPPORTED_PARAMETER_SETS[parameter_set]["sigver_binary"]
    if not isinstance(binary, Path) or not binary.exists():
        pytest.skip(SKIP_SIGVER_NATIVE_REASON)
