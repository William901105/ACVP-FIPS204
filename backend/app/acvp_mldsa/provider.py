from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..acvp_core.algorithm_provider import (
    AcvpProviderExecutionError,
    AcvpProviderInputError,
)
from ..acvp_core.registry import (
    DEFAULT_REGISTRY,
    AlgorithmProviderRegistry,
    DuplicateProviderError,
    ProviderNotFoundError,
)
from ..acvp_protocol.capabilities import negotiate_mldsa_capabilities
from ..acvp_protocol.vector_generation import (
    DEFAULT_TESTS_PER_GROUP,
    GENERATION_PROFILES,
    LOCAL_DEBUG_PROFILE,
    MAX_TESTS_PER_GROUP,
    NIST_CONFORMANCE_PROFILE,
    NIST_KEYGEN_TESTS_PER_GROUP,
    NIST_SIGGEN_TESTS_PER_GROUP,
    NIST_SIGVER_TESTS_PER_GROUP,
    fallback_campaign_seed,
    generate_vector_sets_from_negotiated_capabilities,
)
from ..crypto_oracle.mldsa_errors import MldsaOracleError, MldsaOracleInputError
from ..validator import validate
from .constants import ALGORITHM, REVISION
from .expected import generate_expected_results_from_prompt
from .validators import (
    validate_mldsa_registration,
    validate_mldsa_response,
    validate_mldsa_vector_set,
)


class MldsaProvider:
    algorithm = ALGORITHM
    revisions = [REVISION]
    modes = ["keyGen", "sigGen", "sigVer"]
    generation_profiles = sorted(GENERATION_PROFILES)
    default_generation_profile = LOCAL_DEBUG_PROFILE
    local_debug_profile = LOCAL_DEBUG_PROFILE
    nist_conformance_profile = NIST_CONFORMANCE_PROFILE
    default_tests_per_group = DEFAULT_TESTS_PER_GROUP
    max_tests_per_group = MAX_TESTS_PER_GROUP

    def supports(self, algorithm: str, mode: str, revision: str) -> bool:
        return (
            algorithm == self.algorithm
            and revision in self.revisions
            and mode in self.modes
        )

    def validate_registration(self, registration: Dict[str, Any]) -> Dict[str, Any]:
        return validate_mldsa_registration(registration)

    def negotiate_capabilities(self, registration: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.validate_registration(registration)
        return negotiate_mldsa_capabilities({"algorithms": [normalized]})

    def generate_vector_sets(
        self,
        negotiated_capabilities: Dict[str, Any],
        *,
        campaign_seed: str,
        tests_per_group: int,
        generation_profile: str,
    ) -> List[Dict[str, Any]]:
        try:
            return generate_vector_sets_from_negotiated_capabilities(
                negotiated_capabilities,
                campaign_seed=campaign_seed,
                tests_per_group=tests_per_group,
                generation_profile=generation_profile,
            )
        except MldsaOracleInputError as exc:
            raise AcvpProviderInputError(str(exc)) from exc
        except MldsaOracleError as exc:
            raise AcvpProviderExecutionError(str(exc)) from exc

    def validate_prompt(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        return validate_mldsa_vector_set(prompt)

    def generate_expected_results(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return generate_expected_results_from_prompt(prompt)
        except MldsaOracleInputError as exc:
            raise AcvpProviderInputError(str(exc)) from exc
        except MldsaOracleError as exc:
            raise AcvpProviderExecutionError(str(exc)) from exc

    def validate_response(
        self,
        response: Dict[str, Any],
        *,
        expected_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        return validate_mldsa_response(response, expected_mode=expected_mode)

    def validate_results(
        self,
        *,
        prompt: Dict[str, Any],
        expected_results: Dict[str, Any],
        response: Dict[str, Any],
    ) -> Dict[str, Any]:
        return validate(
            {
                "prompt": prompt,
                "expectedResults": expected_results,
                "response": response,
            }
        )

    def fallback_campaign_seed(self, registration_container: Dict[str, Any]) -> str:
        return fallback_campaign_seed(registration_container)

    def generation_profile_minimums(self, generation_profile: str) -> Dict[str, int]:
        if generation_profile == NIST_CONFORMANCE_PROFILE:
            return {
                "keyGen": NIST_KEYGEN_TESTS_PER_GROUP,
                "sigGen": NIST_SIGGEN_TESTS_PER_GROUP,
                "sigVer": NIST_SIGVER_TESTS_PER_GROUP,
            }
        return {
            "keyGen": DEFAULT_TESTS_PER_GROUP,
            "sigGen": DEFAULT_TESTS_PER_GROUP,
            "sigVer": 2,
        }


_MLDSA_PROVIDER = MldsaProvider()


def get_mldsa_provider() -> MldsaProvider:
    return _MLDSA_PROVIDER


def register_mldsa_provider(
    registry: Optional[AlgorithmProviderRegistry] = None,
) -> MldsaProvider:
    target = registry or DEFAULT_REGISTRY
    target.register_provider(_MLDSA_PROVIDER)
    return _MLDSA_PROVIDER


def ensure_mldsa_provider_registered(
    registry: Optional[AlgorithmProviderRegistry] = None,
) -> MldsaProvider:
    target = registry or DEFAULT_REGISTRY
    missing_modes: List[str] = []
    existing_providers = []
    for mode in _MLDSA_PROVIDER.modes:
        try:
            existing_providers.append(target.get_provider(ALGORITHM, mode, REVISION))
        except ProviderNotFoundError:
            missing_modes.append(mode)

    if not missing_modes:
        return _MLDSA_PROVIDER
    if existing_providers:
        raise DuplicateProviderError(ALGORITHM, missing_modes[0], REVISION)
    return register_mldsa_provider(target)
