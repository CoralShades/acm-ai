"""
Model Provisioning Module

Auto-provisions AI models from environment variables on startup.
Supports fallback chain when primary provider is unavailable.
"""

import os
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from open_notebook.database.repository import repo_query
from open_notebook.domain.models import DefaultModels, Model


@dataclass
class ModelConfig:
    """Configuration for a model from environment variable."""

    provider: str
    name: str
    type: str = "language"


def parse_model_env(
    env_value: str, model_type: str = "language"
) -> Optional[ModelConfig]:
    """
    Parse model configuration from environment variable.

    Format: provider/model_name (e.g., "ollama/qwen3:14b")
    """
    if not env_value:
        return None

    parts = env_value.split("/", 1)
    if len(parts) != 2:
        logger.warning(
            f"Invalid model format: {env_value}. Expected 'provider/model_name'"
        )
        return None

    return ModelConfig(
        provider=parts[0].strip(), name=parts[1].strip(), type=model_type
    )


def get_fallback_providers() -> list[str]:
    """Get ordered list of fallback providers from env."""
    fallback_env = os.getenv(
        "MODEL_FALLBACK_PROVIDERS", "ollama,anthropic,openai,openrouter"
    )
    return [p.strip() for p in fallback_env.split(",") if p.strip()]


def is_provider_available(provider: str) -> bool:
    """Check if a provider is available based on environment configuration.

    Checks both standard and ACM-namespaced env vars (E30-S8).
    """
    provider_checks = {
        "ollama": lambda: os.getenv("OLLAMA_API_BASE") is not None,
        "openai": lambda: os.getenv("OPENAI_API_KEY") is not None,
        "anthropic": lambda: (
            os.getenv("ANTHROPIC_API_KEY") is not None
            or os.getenv("ACM_ANTHROPIC_API_KEY") is not None
        ),
        "openrouter": lambda: (
            os.getenv("OPENROUTER_API_KEY") is not None
            or os.getenv("ACM_OPENROUTER_API_KEY") is not None
        ),
        "google": lambda: os.getenv("GOOGLE_API_KEY") is not None
        or os.getenv("GEMINI_API_KEY") is not None,
        "groq": lambda: os.getenv("GROQ_API_KEY") is not None,
        "mistral": lambda: os.getenv("MISTRAL_API_KEY") is not None,
        "deepseek": lambda: os.getenv("DEEPSEEK_API_KEY") is not None,
        "xai": lambda: os.getenv("XAI_API_KEY") is not None,
    }

    check = provider_checks.get(provider.lower())
    return check() if check else False


# Default fallback models per provider (used when primary is unavailable)
FALLBACK_MODELS = {
    "ollama": {
        "chat": "qwen3:latest",
        "transformation": "qwen3:32b",
        "tools": "qwen3:32b",
        "large_context": "qwen2.5:32b",
        "extraction": "deepseek-r1:8b",
        "embedding": "mxbai-embed-large",
    },
    "anthropic": {
        "chat": "claude-3-5-haiku-20241022",
        "transformation": "claude-sonnet-4-20250514",
        "tools": "claude-sonnet-4-20250514",
        "large_context": "claude-sonnet-4-20250514",
        "extraction": "claude-sonnet-4-20250514",
        "embedding": None,
    },
    "openai": {
        "chat": "gpt-4o-mini",
        "transformation": "gpt-4o",
        "tools": "gpt-4o",
        "large_context": "gpt-4o",
        "extraction": "gpt-4o",
        "embedding": "text-embedding-3-small",
    },
    "openrouter": {
        "chat": "qwen/qwen3-next-80b-a3b-instruct:free",
        "transformation": "qwen/qwen3-next-80b-a3b-instruct:free",
        "tools": "qwen/qwen3-235b-a22b-thinking-2507",
        "large_context": "qwen/qwen2.5-32b-instruct",
        "extraction": "deepseek/deepseek-r1-0528:free",
        "embedding": None,
    },
}


# Full model catalog: (provider, model_name, model_type) for all known models
MODEL_CATALOG: list[tuple[str, str, str]] = [
    # Ollama local models
    ("ollama", "qwen3:latest", "language"),
    ("ollama", "qwen3:8b", "language"),
    ("ollama", "qwen3:14b", "language"),
    ("ollama", "qwen3:32b", "language"),
    ("ollama", "qwen2.5:32b", "language"),
    ("ollama", "qwen2.5-coder:32b", "language"),
    ("ollama", "deepseek-r1:8b", "language"),
    ("ollama", "deepseek-r1:14b", "language"),
    ("ollama", "deepseek-r1:32b", "language"),
    ("ollama", "llama3.3:70b", "language"),
    ("ollama", "llama3.2:3b", "language"),
    ("ollama", "llama3.1:8b", "language"),
    ("ollama", "gemma3:27b", "language"),
    ("ollama", "gemma3:12b", "language"),
    ("ollama", "phi4:14b", "language"),
    ("ollama", "mistral-nemo:12b", "language"),
    ("ollama", "mxbai-embed-large", "embedding"),
    ("ollama", "nomic-embed-text", "embedding"),
    ("ollama", "bge-m3", "embedding"),
    ("ollama", "bge-large", "embedding"),
    # Anthropic
    ("anthropic", "claude-3-5-haiku-20241022", "language"),
    ("anthropic", "claude-3-5-sonnet-20241022", "language"),
    ("anthropic", "claude-sonnet-4-20250514", "language"),
    ("anthropic", "claude-opus-4-20250514", "language"),
    # OpenAI
    ("openai", "gpt-4o-mini", "language"),
    ("openai", "gpt-4o", "language"),
    ("openai", "gpt-4-turbo", "language"),
    ("openai", "text-embedding-3-small", "embedding"),
    ("openai", "text-embedding-3-large", "embedding"),
    # OpenRouter (free + paid)
    ("openrouter", "qwen/qwen2.5-32b-instruct", "language"),
    ("openrouter", "qwen/qwen3-14b", "language"),
    ("openrouter", "qwen/qwen3-30b-a3b", "language"),
    ("openrouter", "qwen/qwen3-235b-a22b", "language"),
    ("openrouter", "qwen/qwen3-235b-a22b-thinking-2507", "language"),
    ("openrouter", "qwen/qwen3-next-80b-a3b-instruct:free", "language"),
    ("openrouter", "qwen/qwen3-coder", "language"),
    ("openrouter", "deepseek/deepseek-r1-0528:free", "language"),
    ("openrouter", "deepseek/deepseek-r1", "language"),
    ("openrouter", "deepseek/deepseek-v3", "language"),
    ("openrouter", "meta-llama/llama-3.3-70b-instruct", "language"),
    ("openrouter", "meta-llama/llama-3.2-3b-instruct:free", "language"),
    ("openrouter", "google/gemma-3-27b-it", "language"),
    ("openrouter", "microsoft/phi-4", "language"),
    ("openrouter", "mistralai/mistral-nemo", "language"),
    ("openrouter", "moonshotai/kimi-k2", "language"),
    ("openrouter", "moonshotai/kimi-k2.5", "language"),
    ("openrouter", "minimax/minimax-m2", "language"),
    ("openrouter", "minimax/minimax-m2.1", "language"),
    ("openrouter", "zhipuai/glm-5", "language"),
    ("openrouter", "deepseek/deepseek-v3.2", "language"),
    ("openrouter", "anthropic/claude-sonnet-4.6", "language"),
    ("openrouter", "openai/gpt-5.2", "language"),
    ("openrouter", "google/gemini-2.5-pro", "language"),
]


async def seed_model_catalog() -> int:
    """Seed all known models for available providers. Idempotent via find_or_create_model()."""
    created = 0
    for provider, name, model_type in MODEL_CATALOG:
        if not is_provider_available(provider):
            continue
        model_id = await find_or_create_model(provider, name, model_type)
        if model_id:
            created += 1
    logger.info(f"Model catalog: {created} models available across active providers")
    return created


async def find_or_create_model(
    provider: str, name: str, model_type: str = "language"
) -> Optional[str]:
    """
    Find existing model or create new one.

    Returns the model ID if found/created, None otherwise.
    """
    # Check if model already exists (case-insensitive)
    existing = await repo_query(
        "SELECT * FROM model WHERE string::lowercase(provider) = $provider AND string::lowercase(name) = $name LIMIT 1",
        {"provider": provider.lower(), "name": name.lower()},
    )

    if existing:
        model_id = existing[0].get("id")
        logger.debug(f"Found existing model: {provider}/{name} -> {model_id}")
        return model_id

    # Create new model with auto-detected capabilities
    try:
        new_model = Model(name=name, provider=provider, type=model_type)
        # Populate capabilities from known defaults
        new_model.max_output_tokens = (
            new_model.get_max_output_tokens() if model_type == "language" else None
        )
        new_model.context_window = (
            new_model.get_context_window() if model_type == "language" else None
        )
        new_model.embedding_dimensions = (
            new_model.get_embedding_dimensions() if model_type == "embedding" else None
        )
        # Set structured output and tool calling support based on provider
        if model_type == "language":
            name_lower = name.lower()
            new_model.supports_structured_output = any(
                k in name_lower
                for k in [
                    "claude",
                    "gpt-4",
                    "gpt-5",
                    "qwen3",
                    "qwen2.5",
                    "llama3",
                    "llama-3",
                    "mistral",
                    "deepseek",
                    "gemma-3",
                    "gemini",
                    "phi4",
                    "kimi-k2",
                    "minimax-m2",
                    "glm-5",
                ]
            )
            new_model.supports_tool_calling = any(
                k in name_lower
                for k in [
                    "claude",
                    "gpt-4",
                    "gpt-5",
                    "qwen3",
                    "deepseek",
                    "llama-3",
                    "mistral",
                    "gemini-2.5",
                    "kimi-k2",
                    "minimax-m2",
                    "glm-5",
                ]
            )
        await new_model.save()
        logger.info(f"Created model: {provider}/{name} -> {new_model.id}")
        return new_model.id
    except Exception as e:
        logger.error(f"Failed to create model {provider}/{name}: {e}")
        return None


async def get_model_with_fallback(
    purpose: str, primary_config: Optional[ModelConfig], model_type: str = "language"
) -> Optional[str]:
    """
    Get or create a model with fallback chain support.

    1. Try primary config from env var
    2. If primary provider unavailable, try fallback providers in order
    """
    # Try primary config first
    if primary_config and is_provider_available(primary_config.provider):
        model_id = await find_or_create_model(
            primary_config.provider, primary_config.name, model_type
        )
        if model_id:
            return model_id
        logger.warning(f"Primary model failed for {purpose}, trying fallback chain")
    elif primary_config:
        logger.info(
            f"Primary provider '{primary_config.provider}' not available for {purpose}, trying fallback chain"
        )

    # Try fallback providers
    fallback_providers = get_fallback_providers()
    for provider in fallback_providers:
        if not is_provider_available(provider):
            continue

        fallback_models = FALLBACK_MODELS.get(provider, {})
        model_name = fallback_models.get(purpose)

        if not model_name:
            continue

        model_id = await find_or_create_model(provider, model_name, model_type)
        if model_id:
            logger.info(f"Using fallback model for {purpose}: {provider}/{model_name}")
            return model_id

    logger.warning(f"No available model found for {purpose}")
    return None


async def provision_default_models() -> dict[str, Optional[str]]:
    """
    Provision default models from environment variables.

    Environment variables:
    - DEFAULT_CHAT_MODEL=provider/model_name
    - DEFAULT_TRANSFORMATION_MODEL=provider/model_name
    - DEFAULT_TOOLS_MODEL=provider/model_name
    - DEFAULT_LARGE_CONTEXT_MODEL=provider/model_name
    - DEFAULT_EXTRACTION_MODEL=provider/model_name
    - DEFAULT_EMBEDDING_MODEL=provider/model_name
    - MODEL_FALLBACK_PROVIDERS=ollama,anthropic,openai,openrouter

    Returns dict of purpose -> model_id mappings.
    """
    logger.info("Starting model provisioning from environment...")

    # Parse environment configurations
    model_configs = {
        "chat": parse_model_env(os.getenv("DEFAULT_CHAT_MODEL", ""), "language"),
        "transformation": parse_model_env(
            os.getenv("DEFAULT_TRANSFORMATION_MODEL", ""), "language"
        ),
        "tools": parse_model_env(os.getenv("DEFAULT_TOOLS_MODEL", ""), "language"),
        "large_context": parse_model_env(
            os.getenv("DEFAULT_LARGE_CONTEXT_MODEL", ""), "language"
        ),
        "extraction": parse_model_env(
            os.getenv("DEFAULT_EXTRACTION_MODEL", ""), "language"
        ),
        "embedding": parse_model_env(
            os.getenv("DEFAULT_EMBEDDING_MODEL", ""), "embedding"
        ),
    }

    # Provision each model type
    provisioned = {}
    for purpose, config in model_configs.items():
        model_type = "embedding" if purpose == "embedding" else "language"
        model_id = await get_model_with_fallback(purpose, config, model_type)
        provisioned[purpose] = model_id

    return provisioned


async def update_defaults_if_needed(provisioned: dict[str, Optional[str]]) -> None:
    """
    Update default models record if any models were provisioned.

    Only updates fields where:
    1. A model was successfully provisioned
    2. The current default is None or points to a non-existent model
    """
    defaults = await DefaultModels.get_instance()

    # Mapping from purpose to DefaultModels field
    field_map = {
        "chat": "default_chat_model",
        "transformation": "default_transformation_model",
        "tools": "default_tools_model",
        "large_context": "large_context_model",
        "extraction": "default_extraction_model",
        "embedding": "default_embedding_model",
    }

    updated = False
    for purpose, model_id in provisioned.items():
        if not model_id:
            continue

        field = field_map.get(purpose)
        if not field:
            continue

        current_value = getattr(defaults, field, None)

        # Skip only if current value already matches the provisioned model
        if current_value == model_id:
            continue

        # Log why we're updating
        if current_value:
            logger.info(
                f"Updating {field}: {current_value} -> {model_id} (env var changed)"
            )
        else:
            logger.info(f"Setting {field} = {model_id}")

        setattr(defaults, field, model_id)
        updated = True

    if updated:
        await defaults.update()
        logger.success("Default models updated successfully")
    else:
        logger.info("No default model updates needed")


async def run_model_provisioning() -> None:
    """
    Main entry point for model provisioning.
    Called during API startup after database migrations.
    """
    try:
        # Step 1: Always seed full catalog for available providers
        await seed_model_catalog()

        # Step 2: Set default assignments from env vars (if any configured)
        env_vars = [
            "DEFAULT_CHAT_MODEL",
            "DEFAULT_TRANSFORMATION_MODEL",
            "DEFAULT_TOOLS_MODEL",
            "DEFAULT_LARGE_CONTEXT_MODEL",
            "DEFAULT_EXTRACTION_MODEL",
            "DEFAULT_EMBEDDING_MODEL",
        ]

        if not any(os.getenv(var) for var in env_vars):
            logger.info("No DEFAULT_*_MODEL env vars set, skipping default assignment")
            return

        provisioned = await provision_default_models()
        await update_defaults_if_needed(provisioned)

        # Log summary
        configured = {k: v for k, v in provisioned.items() if v}
        if configured:
            logger.success(
                f"Model provisioning complete. Configured: {list(configured.keys())}"
            )
        else:
            logger.warning("Model provisioning complete but no models were configured")

    except Exception as e:
        logger.error(f"Model provisioning failed: {e}")
        logger.exception(e)
        # Don't fail startup - models can be configured via UI
