"""LangGraph Studio entrypoint for ACM extraction graph.

This module keeps Studio bootstrapping lightweight and non-blocking:
- Loads `.env` values for local development.
- Emits a warning when SurrealDB env vars are missing.
- Exports the compiled graph at module scope for `langgraph.json` usage.

Note: graph import/compilation itself does not require a live SurrealDB connection.
Runtime DB access happens when graph nodes execute.
"""

import os

from dotenv import load_dotenv
from loguru import logger

# Load local environment for `langgraph dev` sessions.
load_dotenv(override=False)


def _warn_if_surrealdb_unconfigured() -> None:
    """Warn (without failing) when SurrealDB settings are missing.

    LangGraph Studio can still visualize and inspect topology without a running DB.
    """

    required = [
        "SURREAL_URL",
        "SURREAL_USER",
        "SURREAL_PASSWORD",
        "SURREAL_NAMESPACE",
        "SURREAL_DATABASE",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        logger.warning(
            "LangGraph Studio loaded without full SurrealDB configuration "
            f"(missing: {', '.join(missing)}). "
            "Visualization mode still works; runtime extraction may fail without DB."
        )


_warn_if_surrealdb_unconfigured()

from open_notebook.graphs.acm_extraction import graph as acm_extraction_graph

graph = acm_extraction_graph
