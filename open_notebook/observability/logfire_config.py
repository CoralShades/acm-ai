"""Logfire -> Langfuse OTel bridge for Pydantic-aware tracing."""

import os

from loguru import logger

_TRUE_VALUES = {"1", "true", "yes", "on"}
_LOGFIRE_INITIALIZED = False


def init_logfire() -> bool:
    """Initialize Logfire SDK to export OTel spans to Langfuse.

    Non-fatal: returns False if disabled or misconfigured.
    Requires LOGFIRE_ENABLED=true and valid LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY.
    No Logfire cloud account needed -- traces go to self-hosted Langfuse via OTel.
    """
    global _LOGFIRE_INITIALIZED
    if _LOGFIRE_INITIALIZED:
        return True

    if (
        os.getenv("LOGFIRE_ENABLED", "false").strip().lower()
        not in _TRUE_VALUES
    ):
        return False

    langfuse_base = os.getenv("LANGFUSE_BASE_URL", "http://localhost:3000")
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY", "")

    if not langfuse_public or not langfuse_secret:
        logger.warning(
            "LOGFIRE_ENABLED=true but Langfuse keys missing. Skipping Logfire init."
        )
        return False

    try:
        import base64

        import logfire

        # Langfuse OTel auth: Basic base64(public_key:secret_key)
        langfuse_auth = base64.b64encode(
            f"{langfuse_public}:{langfuse_secret}".encode()
        ).decode()
        otel_endpoint = f"{langfuse_base}/api/public/otel"
        otel_headers = f"Authorization=Basic {langfuse_auth}"

        # Set OTel env vars BEFORE logfire.configure() so the SDK picks them up.
        # Use traces-specific variant to avoid metrics export errors (Langfuse
        # OTel endpoint only accepts traces, not metrics).
        os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = otel_endpoint
        os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = otel_headers

        # Configure Logfire to NOT send to Logfire cloud -- OTel env vars route to Langfuse
        logfire.configure(
            send_to_logfire=False,
            service_name="acm-ai",
        )

        # Instrument Pydantic models
        logfire.instrument_pydantic()

        _LOGFIRE_INITIALIZED = True
        logger.info(
            "Logfire initialized -- Pydantic traces -> Langfuse OTel at {}",
            otel_endpoint,
        )
        return True
    except ImportError:
        logger.debug("logfire package not installed. Skipping Logfire init.")
        return False
    except Exception as exc:
        logger.warning(
            "Failed to initialize Logfire: {}. Continuing without.",
            str(exc),
        )
        return False
