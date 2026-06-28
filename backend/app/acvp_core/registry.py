from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List, Tuple

from .algorithm_provider import AcvpAlgorithmProvider


ProviderKey = Tuple[str, str, str]


class ProviderRegistryError(Exception):
    """Base error for provider registry failures."""


class DuplicateProviderError(ProviderRegistryError):
    def __init__(self, algorithm: str, mode: str, revision: str):
        self.algorithm = algorithm
        self.mode = mode
        self.revision = revision
        super().__init__(
            f"Provider already registered for {algorithm}/{mode}/{revision}."
        )


class ProviderNotFoundError(ProviderRegistryError):
    def __init__(self, algorithm: str, mode: str, revision: str):
        self.algorithm = algorithm
        self.mode = mode
        self.revision = revision
        super().__init__(
            f"No provider registered for {algorithm}/{mode}/{revision}."
        )


class AlgorithmProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[ProviderKey, AcvpAlgorithmProvider] = {}

    def register_provider(self, provider: AcvpAlgorithmProvider) -> None:
        keys = self._provider_keys(provider)
        for key in keys:
            existing = self._providers.get(key)
            if existing is not None and existing is not provider:
                raise DuplicateProviderError(key[0], key[1], key[2])
            if existing is provider:
                continue
        for key in keys:
            self._providers[key] = provider

    def get_provider(
        self,
        algorithm: str,
        mode: str,
        revision: str,
    ) -> AcvpAlgorithmProvider:
        key = (algorithm, mode, revision)
        provider = self._providers.get(key)
        if provider is None:
            raise ProviderNotFoundError(algorithm, mode, revision)
        return provider

    def list_algorithms(self) -> List[Dict[str, object]]:
        summaries: "OrderedDict[str, Dict[str, object]]" = OrderedDict()
        for (algorithm, mode, revision), _provider in self._providers.items():
            summary = summaries.setdefault(
                algorithm,
                {"algorithm": algorithm, "revisions": [], "modes": []},
            )
            revisions = summary["revisions"]
            modes = summary["modes"]
            if isinstance(revisions, list) and revision not in revisions:
                revisions.append(revision)
            if isinstance(modes, list) and mode not in modes:
                modes.append(mode)
        return [
            {
                "algorithm": str(summary["algorithm"]),
                "revisions": list(summary["revisions"]),
                "modes": list(summary["modes"]),
            }
            for summary in summaries.values()
        ]

    def clear(self) -> None:
        self._providers.clear()

    @staticmethod
    def _provider_keys(provider: AcvpAlgorithmProvider) -> List[ProviderKey]:
        algorithm = provider.algorithm
        if not isinstance(algorithm, str) or not algorithm:
            raise ProviderRegistryError("Provider algorithm must be a non-empty string.")
        if not provider.revisions:
            raise ProviderRegistryError("Provider revisions must not be empty.")
        if not provider.modes:
            raise ProviderRegistryError("Provider modes must not be empty.")
        return [
            (algorithm, mode, revision)
            for revision in provider.revisions
            for mode in provider.modes
        ]


DEFAULT_REGISTRY = AlgorithmProviderRegistry()


def register_provider(provider: AcvpAlgorithmProvider) -> None:
    DEFAULT_REGISTRY.register_provider(provider)


def get_provider(algorithm: str, mode: str, revision: str) -> AcvpAlgorithmProvider:
    return DEFAULT_REGISTRY.get_provider(algorithm, mode, revision)


def list_algorithms() -> List[Dict[str, object]]:
    return DEFAULT_REGISTRY.list_algorithms()


def clear_providers() -> None:
    DEFAULT_REGISTRY.clear()
