from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .acvp_parser import normalize_acvp_json, summarize_vector_set


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_ROOT = PROJECT_ROOT / "sample-data"


class SampleLoaderError(ValueError):
    """Raised when a requested sample cannot be loaded."""


def list_sample_data() -> list[dict[str, Any]]:
    if not SAMPLE_ROOT.exists():
        return []

    samples: list[dict[str, Any]] = []
    for sample_dir in sorted(path for path in SAMPLE_ROOT.iterdir() if path.is_dir()):
        prompt_path = sample_dir / "prompt.json"
        expected_path = sample_dir / "expectedResults.json"
        response_pass_path = sample_dir / "response.pass.json"
        response_fail_path = sample_dir / "response.fail.json"
        if not prompt_path.exists() or not expected_path.exists():
            continue

        metadata: dict[str, Any] = {}
        try:
            metadata = summarize_vector_set(normalize_acvp_json(_read_json(prompt_path)))
        except Exception:
            metadata = {}

        samples.append(
            {
                "name": sample_dir.name,
                "path": str(sample_dir.relative_to(PROJECT_ROOT)),
                "hasPassResponse": response_pass_path.exists(),
                "hasFailResponse": response_fail_path.exists(),
                **metadata,
            }
        )
    return samples


def load_sample(sample_name: str, response_variant: str = "pass") -> dict[str, Any]:
    if "\\" in sample_name or "/" in sample_name or sample_name in {"", ".", ".."}:
        raise SampleLoaderError("Invalid sample name")

    sample_dir = SAMPLE_ROOT / sample_name
    if not sample_dir.is_dir():
        raise SampleLoaderError(f"Unknown sample: {sample_name}")

    response_file = sample_dir / f"response.{response_variant}.json"
    if not response_file.exists():
        response_file = sample_dir / "response.json"
    if not response_file.exists():
        raise SampleLoaderError(f"Sample {sample_name} does not include response data")

    return {
        "prompt": _read_json(sample_dir / "prompt.json"),
        "expectedResults": _read_json(sample_dir / "expectedResults.json"),
        "response": _read_json(response_file),
        "label": f"{sample_name}:{response_variant}",
    }


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

