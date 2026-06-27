#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
DEFAULT_MLDSA_NATIVE_DIR = REPO_ROOT.parent / "mldsa-native"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.acvp_mldsa.expected import generate_expected_results_from_prompt  # noqa: E402
from app.acvp_mldsa.validators import validate_mldsa_vector_set  # noqa: E402


SUPPORTED_MODES = {"keyGen", "sigGen", "sigVer"}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate local ML-DSA IUT ACVP responses from prompt JSON.",
    )
    parser.add_argument(
        "--prompt",
        default=str(SCRIPT_DIR / "prompt.json"),
        help="Path to ACVP prompt JSON. Default: ./prompt.json",
    )
    parser.add_argument(
        "--response-dir",
        default=str(SCRIPT_DIR / "response"),
        help="Directory for response_pass.json and response_fail.json.",
    )
    parser.add_argument(
        "--variant",
        choices=("pass", "fail", "both"),
        default="both",
        help="Which response fixture to write.",
    )
    parser.add_argument(
        "--expect-mode",
        choices=tuple(sorted(SUPPORTED_MODES)),
        help="Fail if the prompt mode does not match this value.",
    )
    parser.add_argument(
        "--mldsa-native-dir",
        default=str(DEFAULT_MLDSA_NATIVE_DIR),
        help="Path to the mldsa-native checkout used as the IUT.",
    )
    args = parser.parse_args(argv)

    try:
        prompt_path = Path(args.prompt)
        response_dir = Path(args.response_dir)
        prompt = _read_json(prompt_path)
        vector_set = validate_mldsa_vector_set(prompt)
        mode = vector_set.get("mode")
        if mode not in SUPPORTED_MODES:
            raise RuntimeError(f"Unsupported ML-DSA mode: {mode!r}")
        if args.expect_mode and mode != args.expect_mode:
            raise RuntimeError(f"Prompt mode {mode!r} does not match expected mode {args.expect_mode!r}")

        response_dir.mkdir(parents=True, exist_ok=True)
        pass_response = _generate_pass_response(prompt_path, prompt, response_dir, Path(args.mldsa_native_dir))

        written: list[Path] = []
        if args.variant in {"pass", "both"}:
            written.append(_write_json(response_dir / "response_pass.json", pass_response))
        if args.variant in {"fail", "both"}:
            fail_response = copy.deepcopy(pass_response)
            _mutate_first_result(fail_response, mode)
            written.append(_write_json(response_dir / "response_fail.json", fail_response))

        for path in written:
            print(path)
        return 0
    except Exception as exc:  # pragma: no cover - script-level failure path
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"prompt JSON not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> Path:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return path


def _generate_pass_response(
    prompt_path: Path,
    prompt: Any,
    response_dir: Path,
    native_dir: Path,
) -> Any:
    native_error = None
    try:
        return _run_mldsa_native_client(prompt_path, response_dir, native_dir)
    except Exception as exc:
        native_error = str(exc)

    try:
        return generate_expected_results_from_prompt(prompt)
    except Exception as exc:
        raise RuntimeError(
            "mldsa-native ACVP client failed and backend oracle fallback failed. "
            f"mldsa-native: {native_error}; backend oracle: {exc}"
        ) from exc


def _run_mldsa_native_client(prompt_path: Path, response_dir: Path, native_dir: Path) -> Any:
    client = native_dir / "test" / "acvp" / "acvp_client.py"
    if not client.exists():
        raise FileNotFoundError(f"mldsa-native ACVP client not found: {client}")
    output_path = response_dir / ".mldsa_native_response.json"
    command = [
        sys.executable,
        str(client),
        "-p",
        str(prompt_path.resolve()),
        "-o",
        str(output_path.resolve()),
    ]
    completed = subprocess.run(
        command,
        cwd=str(native_dir),
        capture_output=True,
        check=False,
        text=True,
        timeout=300,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"mldsa-native ACVP client exited {completed.returncode}: "
            f"{_tail(completed.stderr) or _tail(completed.stdout) or 'no output'}"
        )
    if not output_path.exists():
        raise RuntimeError("mldsa-native ACVP client did not create an output file")
    payload = _read_json(output_path)
    output_path.unlink(missing_ok=True)
    return payload


def _tail(text: str, line_count: int = 12) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[-line_count:])


def _mutate_first_result(payload: Any, mode: str) -> None:
    body = _response_body(payload)
    test = _first_test(body)
    if mode == "keyGen":
        _mutate_hex_field(test, "pk")
        return
    if mode == "sigGen":
        _mutate_hex_field(test, "signature")
        return
    if mode == "sigVer":
        if "testPassed" not in test or not isinstance(test["testPassed"], bool):
            raise RuntimeError("sigVer response has no boolean testPassed field to mutate")
        test["testPassed"] = not test["testPassed"]
        return
    raise RuntimeError(f"Unsupported ML-DSA mode: {mode!r}")


def _response_body(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        for item in payload[1:]:
            if isinstance(item, dict) and "testGroups" in item:
                return item
    raise RuntimeError("response payload does not contain an ACVP response body")


def _first_test(body: dict[str, Any]) -> dict[str, Any]:
    groups = body.get("testGroups")
    if not isinstance(groups, list) or not groups:
        raise RuntimeError("response body has no testGroups")
    tests = groups[0].get("tests")
    if not isinstance(tests, list) or not tests:
        raise RuntimeError("response body has no tests")
    first = tests[0]
    if not isinstance(first, dict):
        raise RuntimeError("first response test is not an object")
    return first


def _mutate_hex_field(test: dict[str, Any], field: str) -> None:
    value = test.get(field)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"response test has no hex {field!r} field to mutate")
    replacement = "1" if value[0].upper() == "0" else "0"
    test[field] = f"{replacement}{value[1:]}"


if __name__ == "__main__":
    raise SystemExit(main())
