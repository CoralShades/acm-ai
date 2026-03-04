"""
SF Schema Provisioning Module

Idempotently loads Salesforce field schema into SurrealDB field_schema:sf_v1
at API startup.

Story: E30-S1 — SF Schema Config Loader
"""

import json
from datetime import datetime, timezone

from loguru import logger

from open_notebook.database.repository import repo_query
from open_notebook.extractors.parsers.config_loader import load_sf_field_schema
from open_notebook.extractors.parsers.field_config import SFSchemaBundle

SF_SCHEMA_RECORD_ID = "field_schema:sf_v1"
SF_SCHEMA_VERSION = "salesforce-v1"


async def run_sf_schema_provisioning() -> None:
    """Main entry point for SF schema provisioning.

    Called from api/main.py lifespan after run_model_provisioning().

    Idempotent: only writes to DB if record is absent or version differs.
    Non-fatal: logs warning on failure, does not block API startup.
    """
    try:
        # Check if current version is already loaded
        existing = await repo_query(f"SELECT version FROM {SF_SCHEMA_RECORD_ID}")
        if existing and existing[0].get("version") == SF_SCHEMA_VERSION:
            logger.info(
                f"SF schema already at version {SF_SCHEMA_VERSION}, "
                "skipping provisioning"
            )
            return

        # Load schema from V3 markdown files
        schema = load_sf_field_schema()
        await _upsert_sf_schema(schema)
        logger.success(
            f"SF schema provisioning complete: version={SF_SCHEMA_VERSION}, "
            f"building_fields={len(schema.building_fields.fields)}, "
            f"item_fields={len(schema.item_fields.fields)}"
        )

    except Exception as e:
        logger.warning(f"SF schema provisioning failed (non-fatal): {e}")


async def _upsert_sf_schema(schema: SFSchemaBundle) -> None:
    """Write schema bundle to field_schema:sf_v1."""
    schema.loaded_at = datetime.now(timezone.utc).isoformat()
    schema_dict = schema.model_dump()

    await repo_query(
        """
        UPSERT $id SET
            version = $version,
            building_fields = $building_fields,
            item_fields = $item_fields,
            picklists = $picklists,
            dependencies = $dependencies,
            loaded_at = $loaded_at,
            updated = time::now()
        """,
        {
            "id": SF_SCHEMA_RECORD_ID,
            "version": schema.version,
            "building_fields": json.dumps(schema_dict["building_fields"]),
            "item_fields": json.dumps(schema_dict["item_fields"]),
            "picklists": json.dumps(schema_dict["picklists"]),
            "dependencies": json.dumps(schema_dict["dependencies"]),
            "loaded_at": schema.loaded_at,
        },
    )
