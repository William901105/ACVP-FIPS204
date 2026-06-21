from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


JsonObject = dict[str, Any] | list[Any]


class ImportRequest(BaseModel):
    prompt: JsonObject
    expectedResults: JsonObject
    response: JsonObject
    label: str | None = None


class ValidateRequest(BaseModel):
    importId: str


class LoadSampleRequest(BaseModel):
    sampleName: str
    responseVariant: Literal["pass", "fail"] = "pass"


class ImportSummary(BaseModel):
    importId: str
    label: str | None = None
    vsId: Any = None
    algorithm: str | None = None
    mode: str | None = None
    revision: str | None = None
    testGroupCount: int = 0
    testCaseCount: int = 0


class ApiError(BaseModel):
    detail: str = Field(..., examples=["Unknown importId"])

