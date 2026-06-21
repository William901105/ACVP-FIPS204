from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .acvp_parser import AcvpParseError, normalize_acvp_json, summarize_vector_set
from .models import ImportRequest, ImportSummary, LoadSampleRequest, ValidateRequest
from .report import build_report
from .sample_loader import SampleLoaderError, list_sample_data, load_sample
from .validator import validate


app = FastAPI(
    title="FIPS 204 / ML-DSA ACVP JSON Viewer + Local Validator",
    version="0.1.0",
    description="Local JSON comparison demo for ML-DSA ACVP prompt, expectedResults, and response files.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMPORT_STORE: dict[str, dict[str, Any]] = {}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/import", response_model=ImportSummary)
def import_bundle(payload: ImportRequest) -> ImportSummary:
    try:
        bundle = {
            "prompt": payload.prompt,
            "expectedResults": payload.expectedResults,
            "response": payload.response,
            "label": payload.label,
        }
        return _store_import(bundle)
    except (AcvpParseError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/validate")
def validate_import(payload: ValidateRequest) -> dict[str, Any]:
    bundle = _get_bundle(payload.importId)
    try:
        result = validate(bundle)
    except (AcvpParseError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    bundle["validationResult"] = result
    bundle["report"] = build_report(payload.importId, result)
    return result


@app.get("/api/import/{import_id}")
def get_import(import_id: str) -> dict[str, Any]:
    bundle = _get_bundle(import_id)
    prompt_vs = normalize_acvp_json(bundle["prompt"])
    expected_vs = normalize_acvp_json(bundle["expectedResults"])
    response_vs = normalize_acvp_json(bundle["response"])
    return {
        "importId": import_id,
        "label": bundle.get("label"),
        "summary": _summarize_bundle(import_id, bundle),
        "prompt": prompt_vs,
        "expectedResults": expected_vs,
        "response": response_vs,
        "validationResult": bundle.get("validationResult"),
    }


@app.get("/api/report/{import_id}")
def get_report(import_id: str) -> dict[str, Any]:
    bundle = _get_bundle(import_id)
    if "report" not in bundle:
        result = validate(bundle)
        bundle["validationResult"] = result
        bundle["report"] = build_report(import_id, result)
    return bundle["report"]


@app.get("/api/sample-data")
def sample_data() -> dict[str, Any]:
    return {"samples": list_sample_data()}


@app.post("/api/load-sample", response_model=ImportSummary)
def load_sample_import(payload: LoadSampleRequest) -> ImportSummary:
    try:
        bundle = load_sample(payload.sampleName, payload.responseVariant)
        return _store_import(bundle)
    except (SampleLoaderError, AcvpParseError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _store_import(bundle: dict[str, Any]) -> ImportSummary:
    prompt_vs = normalize_acvp_json(bundle["prompt"])
    normalize_acvp_json(bundle["expectedResults"])
    normalize_acvp_json(bundle["response"])

    import_id = str(uuid4())
    IMPORT_STORE[import_id] = bundle
    return _summarize_bundle(import_id, bundle)


def _summarize_bundle(import_id: str, bundle: dict[str, Any]) -> ImportSummary:
    prompt_summary = summarize_vector_set(normalize_acvp_json(bundle["prompt"]))
    return ImportSummary(importId=import_id, label=bundle.get("label"), **prompt_summary)


def _get_bundle(import_id: str) -> dict[str, Any]:
    bundle = IMPORT_STORE.get(import_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Unknown importId")
    return bundle

