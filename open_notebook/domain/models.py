import os
from typing import ClassVar, Dict, Optional, Union

from esperanto import (
    AIFactory,
    EmbeddingModel,
    LanguageModel,
    SpeechToTextModel,
    TextToSpeechModel,
)
from loguru import logger

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.base import ObjectModel, RecordModel

ModelType = Union[LanguageModel, EmbeddingModel, SpeechToTextModel, TextToSpeechModel]


class Model(ObjectModel):
    table_name: ClassVar[str] = "model"
    name: str
    provider: str
    type: str
    # Model capabilities (populated during provisioning or manually)
    max_output_tokens: Optional[int] = None
    context_window: Optional[int] = None
    supports_structured_output: Optional[bool] = None
    supports_tool_calling: Optional[bool] = None
    embedding_dimensions: Optional[int] = None
    # Optional per-model API key (E30-S8: ACM-namespaced key isolation)
    api_key: Optional[str] = None

    # Known provider defaults for output tokens and context windows
    # Keys are matched via `if key in name_lower` — order most-specific first within each family
    _PROVIDER_DEFAULTS: ClassVar[Dict[str, Dict[str, int]]] = {
        # Anthropic Claude
        "claude-3-5-haiku": {"max_output": 8192, "context": 200000},
        "claude-3-haiku": {"max_output": 4096, "context": 200000},
        "claude-sonnet-4.6": {"max_output": 16384, "context": 1000000},
        "claude-sonnet-4": {"max_output": 16384, "context": 200000},
        "claude-opus-4": {"max_output": 32768, "context": 200000},
        "claude-3-5-sonnet": {"max_output": 8192, "context": 200000},
        # OpenAI
        "gpt-5.2": {"max_output": 32768, "context": 400000},
        "gpt-4o-mini": {"max_output": 16384, "context": 128000},
        "gpt-4o": {"max_output": 16384, "context": 128000},
        "gpt-4-turbo": {"max_output": 4096, "context": 128000},
        # Qwen3 (most-specific first)
        "qwen3-next-80b": {"max_output": 16384, "context": 262144},
        "qwen3-235b-a22b-thinking": {"max_output": 81920, "context": 262144},
        "qwen3-235b": {"max_output": 32768, "context": 262144},
        "qwen3-coder": {"max_output": 32768, "context": 262144},
        "qwen3-30b": {"max_output": 32768, "context": 131072},
        "qwen3-14b": {"max_output": 8192, "context": 131072},
        "qwen3-8b": {"max_output": 8192, "context": 131072},
        "qwen3": {"max_output": 8192, "context": 32768},
        # Qwen2.5 (Ollama colon-format first, then OpenRouter dash-format)
        "qwen2.5:32b": {"max_output": 8192, "context": 131072},
        "qwen2.5:14b": {"max_output": 8192, "context": 131072},
        "qwen2.5:7b": {"max_output": 8192, "context": 131072},
        "qwen2.5-coder-32b": {"max_output": 8192, "context": 131072},
        "qwen2.5-coder": {"max_output": 8192, "context": 32768},
        "qwen2.5-72b": {"max_output": 8192, "context": 131072},
        "qwen2.5-32b": {"max_output": 8192, "context": 131072},
        "qwen2.5": {"max_output": 8192, "context": 32768},
        # DeepSeek
        "deepseek-r1-0528": {"max_output": 64000, "context": 131072},
        "deepseek-r1": {"max_output": 32768, "context": 131072},
        "deepseek-v3.2": {"max_output": 16384, "context": 163840},
        "deepseek-v3": {"max_output": 8192, "context": 131072},
        "deepseek": {"max_output": 8192, "context": 65536},
        # Meta Llama
        "llama-3.3": {"max_output": 8192, "context": 131072},
        "llama-3.2": {"max_output": 8192, "context": 131072},
        "llama-3.1": {"max_output": 8192, "context": 131072},
        "llama3": {"max_output": 8192, "context": 8192},
        # Google Gemini
        "gemini-2.5-pro": {"max_output": 65536, "context": 1000000},
        # Google Gemma
        "gemma-3-27b": {"max_output": 8192, "context": 131072},
        "gemma-3": {"max_output": 8192, "context": 131072},
        "gemma": {"max_output": 8192, "context": 32768},
        # Microsoft Phi
        "phi4": {"max_output": 8192, "context": 16384},
        "phi3": {"max_output": 4096, "context": 128000},
        # Moonshot Kimi
        "kimi-k2.5": {"max_output": 32768, "context": 262144},
        "kimi-k2": {"max_output": 32768, "context": 262144},
        # MiniMax
        "minimax-m2.1": {"max_output": 32768, "context": 196608},
        "minimax-m2": {"max_output": 32768, "context": 204800},
        # Z.AI GLM
        "glm-5": {"max_output": 32768, "context": 200000},
        "glm-4": {"max_output": 8192, "context": 131072},
        # Mistral
        "mistral-large": {"max_output": 8192, "context": 131072},
        "mistral-nemo": {"max_output": 8192, "context": 131072},
        "mistral": {"max_output": 8192, "context": 32768},
    }

    _EMBEDDING_DEFAULTS: ClassVar[Dict[str, int]] = {
        # Ollama local
        "mxbai-embed-large": 1024,
        "nomic-embed-text": 768,
        # OpenAI
        "text-embedding-3-large": 3072,
        "text-embedding-3-small": 1536,
        "text-embedding-ada-002": 1536,
        # Qwen3 Embedding
        "qwen3-embedding-8b": 4096,
        "qwen3-embedding-4b": 2560,
        "qwen3-embedding": 4096,
        # Google
        "gemini-embedding-001": 3072,
        # Mistral
        "codestral-embed-2505": 3072,
        "codestral-embed": 3072,
        "mistral-embed": 1024,
        # BAAI BGE
        "bge-m3": 1024,
        "bge-large": 1024,
    }

    def get_max_output_tokens(self, fallback: int = 8192) -> int:
        """Get max output tokens, using stored value or provider defaults."""
        if self.max_output_tokens:
            return self.max_output_tokens
        # Try to match against known model families
        name_lower = self.name.lower()
        for key, defaults in self._PROVIDER_DEFAULTS.items():
            if key in name_lower:
                return defaults["max_output"]
        return fallback

    def get_context_window(self, fallback: int = 128000) -> int:
        """Get context window, using stored value or provider defaults."""
        if self.context_window:
            return self.context_window
        name_lower = self.name.lower()
        for key, defaults in self._PROVIDER_DEFAULTS.items():
            if key in name_lower:
                return defaults["context"]
        return fallback

    def get_embedding_dimensions(self, fallback: int = 1024) -> int:
        """Get embedding dimensions, using stored value or known defaults."""
        if self.embedding_dimensions:
            return self.embedding_dimensions
        name_lower = self.name.lower()
        for key, dims in self._EMBEDDING_DEFAULTS.items():
            if key in name_lower:
                return dims
        return fallback

    @classmethod
    async def get_models_by_type(cls, model_type):
        models = await repo_query(
            "SELECT * FROM model WHERE type=$model_type;", {"model_type": model_type}
        )
        return [Model(**model) for model in models]


class DefaultModels(RecordModel):
    record_id: ClassVar[str] = "open_notebook:default_models"
    default_chat_model: Optional[str] = None
    default_transformation_model: Optional[str] = None
    large_context_model: Optional[str] = None
    default_text_to_speech_model: Optional[str] = None
    default_speech_to_text_model: Optional[str] = None
    # default_vision_model: Optional[str]
    default_embedding_model: Optional[str] = None
    default_tools_model: Optional[str] = None
    default_extraction_model: Optional[str] = None  # E1-S7: AI-powered ACM extraction

    @classmethod
    async def get_instance(cls) -> "DefaultModels":
        """Always fetch fresh defaults from database (override parent caching behavior)"""
        result = await repo_query(
            "SELECT * FROM ONLY $record_id",
            {"record_id": ensure_record_id(cls.record_id)},
        )

        if result:
            if isinstance(result, list) and len(result) > 0:
                data = result[0]
            elif isinstance(result, dict):
                data = result
            else:
                data = {}
        else:
            data = {}

        # Create new instance with fresh data (bypass singleton cache)
        instance = object.__new__(cls)
        object.__setattr__(instance, "__dict__", {})
        super(RecordModel, instance).__init__(**data)
        return instance


class ModelManager:
    def __init__(self):
        pass  # No caching needed

    @staticmethod
    def _looks_like_openrouter_model_name(model_name: str) -> bool:
        prefixes = (
            "anthropic/",
            "openai/",
            "google/",
            "qwen/",
            "deepseek/",
            "meta-llama/",
            "mistralai/",
            "moonshotai/",
            "minimax/",
            "zhipuai/",
            "microsoft/",
        )
        lower = model_name.lower()
        return any(lower.startswith(prefix) for prefix in prefixes)

    @staticmethod
    def _normalize_anthropic_model_name(model_name: str) -> str:
        lower = model_name.lower().strip()
        mapping = {
            "claude-sonnet-4.6": "claude-sonnet-4-20250514",
            "claude-sonnet-4": "claude-sonnet-4-20250514",
        }
        return mapping.get(lower, model_name)

    @classmethod
    def _route_provider_and_name(
        cls, provider: str, model_name: str
    ) -> tuple[str, str]:
        provider_lower = provider.lower().strip()
        routed_name = model_name.strip()

        if (
            provider_lower != "openrouter"
            and cls._looks_like_openrouter_model_name(routed_name)
            and os.getenv("OPENROUTER_API_KEY")
        ):
            logger.info(
                f"Routing model '{provider}/{model_name}' via openrouter provider"
            )
            return "openrouter", routed_name

        if provider_lower == "openrouter" and routed_name.lower().startswith(
            "anthropic/"
        ):
            if not os.getenv("OPENROUTER_API_KEY") and (
                os.getenv("ACM_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
            ):
                stripped = routed_name.split("/", 1)[1]
                normalized = cls._normalize_anthropic_model_name(stripped)
                logger.info(
                    f"OpenRouter unavailable for '{model_name}', "
                    f"routing to anthropic/{normalized}"
                )
                return "anthropic", normalized

        if provider_lower == "anthropic":
            routed_name = cls._normalize_anthropic_model_name(routed_name)

        return provider_lower, routed_name

    async def get_model(self, model_id: str, **kwargs) -> Optional[ModelType]:
        """Get a model by ID. Esperanto will cache the actual model instance."""
        if not model_id:
            return None

        try:
            model: Model = await Model.get(model_id)
        except Exception:
            raise ValueError(f"Model with ID {model_id} not found")

        if not model.type or model.type not in [
            "language",
            "embedding",
            "speech_to_text",
            "text_to_speech",
        ]:
            raise ValueError(f"Invalid model type: {model.type}")

        routed_provider, routed_name = self._route_provider_and_name(
            model.provider, model.name
        )

        # Merge per-model api_key into config if present (E30-S8)
        config = dict(kwargs)
        if model.api_key:
            config["api_key"] = model.api_key

        # Fallback: use ACM-namespaced API keys when per-model key is not set.
        # This prevents Claude Code's ANTHROPIC_API_KEY from being consumed.
        if "api_key" not in config and routed_provider == "anthropic":
            acm_key = os.getenv("ACM_ANTHROPIC_API_KEY")
            if acm_key:
                config["api_key"] = acm_key

        # Create model based on type (Esperanto will cache the instance)
        if model.type == "language":
            return AIFactory.create_language(
                model_name=routed_name,
                provider=routed_provider,
                config=config,
            )
        elif model.type == "embedding":
            return AIFactory.create_embedding(
                model_name=routed_name,
                provider=routed_provider,
                config=config,
            )
        elif model.type == "speech_to_text":
            return AIFactory.create_speech_to_text(
                model_name=routed_name,
                provider=routed_provider,
                config=config,
            )
        elif model.type == "text_to_speech":
            return AIFactory.create_text_to_speech(
                model_name=routed_name,
                provider=routed_provider,
                config=config,
            )
        else:
            raise ValueError(f"Invalid model type: {model.type}")

    async def get_defaults(self) -> DefaultModels:
        """Get the default models configuration from database"""
        defaults = await DefaultModels.get_instance()
        if not defaults:
            raise RuntimeError("Failed to load default models configuration")
        return defaults

    async def get_speech_to_text(self, **kwargs) -> Optional[SpeechToTextModel]:
        """Get the default speech-to-text model"""
        defaults = await self.get_defaults()
        model_id = defaults.default_speech_to_text_model
        if not model_id:
            return None
        model = await self.get_model(model_id, **kwargs)
        assert model is None or isinstance(model, SpeechToTextModel), (
            f"Expected SpeechToTextModel but got {type(model)}"
        )
        return model

    async def get_text_to_speech(self, **kwargs) -> Optional[TextToSpeechModel]:
        """Get the default text-to-speech model"""
        defaults = await self.get_defaults()
        model_id = defaults.default_text_to_speech_model
        if not model_id:
            return None
        model = await self.get_model(model_id, **kwargs)
        assert model is None or isinstance(model, TextToSpeechModel), (
            f"Expected TextToSpeechModel but got {type(model)}"
        )
        return model

    async def get_embedding_model(self, **kwargs) -> Optional[EmbeddingModel]:
        """Get the default embedding model"""
        defaults = await self.get_defaults()
        model_id = defaults.default_embedding_model
        if not model_id:
            return None
        model = await self.get_model(model_id, **kwargs)
        assert model is None or isinstance(model, EmbeddingModel), (
            f"Expected EmbeddingModel but got {type(model)}"
        )
        return model

    async def get_default_model(self, model_type: str, **kwargs) -> Optional[ModelType]:
        """
        Get the default model for a specific type.

        Args:
            model_type: The type of model to retrieve (e.g., 'chat', 'embedding', etc.)
            **kwargs: Additional arguments to pass to the model constructor
        """
        defaults = await self.get_defaults()
        model_id = None

        if model_type == "chat":
            model_id = defaults.default_chat_model
        elif model_type == "transformation":
            model_id = (
                defaults.default_transformation_model or defaults.default_chat_model
            )
        elif model_type == "tools":
            model_id = defaults.default_tools_model or defaults.default_chat_model
        elif model_type == "extraction":
            # E1-S7: AI-powered ACM extraction
            model_id = defaults.default_extraction_model or defaults.default_chat_model
        elif model_type == "embedding":
            model_id = defaults.default_embedding_model
        elif model_type == "text_to_speech":
            model_id = defaults.default_text_to_speech_model
        elif model_type == "speech_to_text":
            model_id = defaults.default_speech_to_text_model
        elif model_type == "large_context":
            model_id = defaults.large_context_model

        if not model_id:
            return None

        return await self.get_model(model_id, **kwargs)


model_manager = ModelManager()
