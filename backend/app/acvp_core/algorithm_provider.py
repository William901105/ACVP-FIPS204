from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class AcvpProviderError(Exception):
    """Base error for algorithm provider execution failures."""


class AcvpProviderInputError(AcvpProviderError):
    """Raised when a provider rejects an input before execution."""


class AcvpProviderExecutionError(AcvpProviderError):
    """Raised when a provider backend fails during execution."""


@runtime_checkable
class AcvpAlgorithmProvider(Protocol):
    """Minimal boundary implemented by each ACVP algorithm backend."""

    algorithm: str
    revisions: List[str]
    modes: List[str]

    def supports(self, algorithm: str, mode: str, revision: str) -> bool:
        ...

    def validate_registration(self, registration: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def negotiate_capabilities(self, registration: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def generate_vector_sets(
        self,
        negotiated_capabilities: Dict[str, Any],
        *,
        campaign_seed: str,
        tests_per_group: int,
        generation_profile: str,
    ) -> List[Dict[str, Any]]:
        ...

    def validate_prompt(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def generate_expected_results(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def validate_response(
        self,
        response: Dict[str, Any],
        *,
        expected_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    def validate_results(
        self,
        *,
        prompt: Dict[str, Any],
        expected_results: Dict[str, Any],
        response: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...
