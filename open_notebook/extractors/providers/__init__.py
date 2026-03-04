"""
Provider Adapter Framework — registry and auto-registration.

Provides a singleton ProviderRegistry pre-loaded with:
  - DoclingAdapter (always registered as "docling")
  - MinerUAdapter (registered as "mineru" regardless of MINERU_ENABLED;
    the adapter itself gates on the env var at extract() time)

Usage:
    from open_notebook.extractors.providers import get_provider_registry

    registry = get_provider_registry()
    provider = registry.get_default()
    result = provider.extract(pdf_path)

Story: E31-S2 Provider Adapter Framework
"""

from __future__ import annotations

import os
from typing import Dict, List

from loguru import logger

from open_notebook.extractors.providers.base import ExtractionProvider, ProviderError
from open_notebook.extractors.providers.docling_adapter import DoclingAdapter
from open_notebook.extractors.providers.mineru_adapter import MinerUAdapter

__all__ = [
    "ProviderRegistry",
    "get_provider_registry",
    "DoclingAdapter",
    "MinerUAdapter",
    "ExtractionProvider",
    "ProviderError",
]


class ProviderRegistry:
    """Registry for ExtractionProvider instances.

    Provides lookup by provider_id and default provider selection via
    ACM_EXTRACTION_PROVIDER environment variable.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, ExtractionProvider] = {}
        self._default_id: str = "docling"

    def register(self, provider: ExtractionProvider) -> None:
        """Register a provider instance.

        Args:
            provider: An object satisfying the ExtractionProvider protocol.
        """
        pid = provider.provider_id
        self._providers[pid] = provider
        logger.debug(f"ProviderRegistry: registered provider '{pid}'")

    def get_provider(self, provider_id: str) -> ExtractionProvider:
        """Look up a registered provider by ID.

        Args:
            provider_id: The stable string key (e.g. "docling", "mineru").

        Returns:
            The registered ExtractionProvider.

        Raises:
            KeyError: If no provider with the given ID is registered.
        """
        if provider_id not in self._providers:
            available = ", ".join(self.list_providers()) or "(none)"
            raise KeyError(
                f"Provider '{provider_id}' not found. "
                f"Available providers: {available}"
            )
        return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Return a sorted list of registered provider IDs.

        Returns:
            Sorted list of provider ID strings.
        """
        return sorted(self._providers.keys())

    def get_default(self) -> ExtractionProvider:
        """Return the default provider.

        Reads ACM_EXTRACTION_PROVIDER env var each call so tests can swap
        providers without re-importing this module.

        Returns:
            The default ExtractionProvider.

        Raises:
            KeyError: If the configured default provider is not registered.
        """
        env_id = os.environ.get("ACM_EXTRACTION_PROVIDER", "").strip()
        effective_id = env_id if env_id else self._default_id
        return self.get_provider(effective_id)

    def set_default(self, provider_id: str) -> None:
        """Set the default provider by ID.

        The provider must already be registered.

        Args:
            provider_id: The ID of a registered provider.

        Raises:
            KeyError: If the provider is not registered.
        """
        # Validate the provider exists first
        self.get_provider(provider_id)
        self._default_id = provider_id
        logger.debug(f"ProviderRegistry: default provider set to '{provider_id}'")


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_registry = ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    """Return the singleton ProviderRegistry instance.

    Returns:
        The global ProviderRegistry with all providers pre-registered.
    """
    return _registry


# ---------------------------------------------------------------------------
# Auto-registration
# ---------------------------------------------------------------------------
# Both adapters are always registered. The MinerUAdapter gates on MINERU_ENABLED
# at extract() time, not at construction/registration time.

_registry.register(DoclingAdapter())
_registry.register(MinerUAdapter())

logger.debug(
    f"ProviderRegistry: auto-registered providers: {_registry.list_providers()}"
)
