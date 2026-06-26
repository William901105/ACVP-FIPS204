from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


JsonObject = Union[Dict[str, Any], List[Any]]


class ImportRequest(BaseModel):
    prompt: JsonObject
    expectedResults: JsonObject
    response: JsonObject
    label: Optional[str] = None


class GeneratedKeygenImportRequest(BaseModel):
    prompt: JsonObject
    response: JsonObject
    label: Optional[str] = None


class ValidateRequest(BaseModel):
    importId: str


class LoadSampleRequest(BaseModel):
    sampleName: str
    responseVariant: Literal["pass", "fail"] = "pass"


class ImportSummary(BaseModel):
    importId: str
    label: Optional[str] = None
    vsId: Any = None
    algorithm: Optional[str] = None
    mode: Optional[str] = None
    revision: Optional[str] = None
    testGroupCount: int = 0
    testCaseCount: int = 0


class ApiError(BaseModel):
    detail: str = Field(..., examples=["Unknown importId"])


class MldsaKeygenRequest(BaseModel):
    parameterSet: str
    seed: str


class MldsaKeygenResponse(BaseModel):
    algorithm: Literal["ML-DSA"] = "ML-DSA"
    mode: Literal["keyGen"] = "keyGen"
    revision: Literal["FIPS204"] = "FIPS204"
    parameterSet: str
    seed: str
    pk: str
    sk: str


class MldsaKeygenExpectedResultsRequest(BaseModel):
    prompt: JsonObject


class MldsaKeygenExpectedResultsResponse(BaseModel):
    algorithm: Literal["ML-DSA"] = "ML-DSA"
    mode: Literal["keyGen"] = "keyGen"
    revision: Literal["FIPS204"] = "FIPS204"
    expectedResults: JsonObject


class MldsaSigGenRequest(BaseModel):
    parameterSet: Literal["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"]
    signatureInterface: Literal["internal"] = "internal"
    externalMu: bool = False
    deterministic: bool = True
    sk: str
    message: Optional[str] = None
    mu: Optional[str] = None
    rnd: Optional[str] = None

    @model_validator(mode="after")
    def validate_internal_siggen_inputs(self) -> "MldsaSigGenRequest":
        if self.externalMu:
            if self.mu is None:
                raise ValueError("mu is required when externalMu=true")
            if self.message is not None:
                raise ValueError("message is not allowed when externalMu=true")
        else:
            if self.message is None:
                raise ValueError("message is required when externalMu=false")
            if self.mu is not None:
                raise ValueError("mu is not allowed when externalMu=false")

        if self.deterministic:
            if self.rnd is not None:
                raise ValueError("rnd is not allowed when deterministic=true")
        elif self.rnd is None:
            raise ValueError("rnd is required when deterministic=false")

        return self


class MldsaSigGenResponse(BaseModel):
    algorithm: Literal["ML-DSA"] = "ML-DSA"
    mode: Literal["sigGen"] = "sigGen"
    revision: Literal["FIPS204"] = "FIPS204"
    parameterSet: str
    signatureInterface: Literal["internal"] = "internal"
    externalMu: bool
    deterministic: bool
    signature: str


class MldsaSigVerRequest(BaseModel):
    parameterSet: Literal["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"]
    signatureInterface: Literal["internal"] = "internal"
    externalMu: bool = False
    pk: str
    message: Optional[str] = None
    mu: Optional[str] = None
    signature: str

    @model_validator(mode="after")
    def validate_internal_sigver_inputs(self) -> "MldsaSigVerRequest":
        if self.externalMu:
            if self.mu is None:
                raise ValueError("mu is required when externalMu=true")
            if self.message is not None:
                raise ValueError("message is not allowed when externalMu=true")
        else:
            if self.message is None:
                raise ValueError("message is required when externalMu=false")
            if self.mu is not None:
                raise ValueError("mu is not allowed when externalMu=false")
        return self


class MldsaSigVerResponse(BaseModel):
    algorithm: Literal["ML-DSA"] = "ML-DSA"
    mode: Literal["sigVer"] = "sigVer"
    revision: Literal["FIPS204"] = "FIPS204"
    parameterSet: str
    signatureInterface: Literal["internal"] = "internal"
    externalMu: bool
    testPassed: bool
