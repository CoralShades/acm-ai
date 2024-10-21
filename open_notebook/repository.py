import asyncio
import os
from contextlib import asynccontextmanager

from loguru import logger
from surrealdb import Surreal

from open_notebook.exceptions import InvalidDatabaseSchema

EXPECTED_VERSION = "0.0.1"


@asynccontextmanager
async def db_connection():
    db = Surreal(os.environ["SURREAL_ADDRESS"])
    try:
        await db.connect()
        await db.signin(
            {"user": os.environ["SURREAL_USER"], "pass": os.environ["SURREAL_PASS"]}
        )
        await db.use(os.environ["SURREAL_NAMESPACE"], os.environ["SURREAL_DATABASE"])
        yield db
    finally:
        await db.close()


def repo_query(query_str, vars=None):
    async def _query():
        async with db_connection() as db:
            result = await db.query(query_str, vars)
        return result

    result = asyncio.run(_query())
    return result[0]["result"]


def check_version():
    async def _check_version():
        async with db_connection() as db:
            result = await db.query("select * from open_notebook:database_info;")
        return result

    try:
        result = asyncio.run(_check_version())
        if len(result) == 0 or len(result[0]["result"]) == 0:
            raise InvalidDatabaseSchema("Database schema not found")
        version = result[0]["result"][0]["version"]
        logger.info(f"Connected to SurrealDB, using schema version {version}")
        if version != EXPECTED_VERSION:
            raise InvalidDatabaseSchema(
                f"Version mismatch. Expected {EXPECTED_VERSION}, got {version}"
            )
    except Exception as e:
        logger.error(e)
        raise e


def repo_create(table, data):
    async def _create():
        async with db_connection() as db:
            result = await db.create(table, data)
        return result

    result = asyncio.run(_create())
    return result


def repo_update(id, data):
    async def _update():
        async with db_connection() as db:
            result = await db.update(id, data)
        return result

    result = asyncio.run(_update())
    return result


def repo_delete(id):
    async def _delete():
        async with db_connection() as db:
            result = await db.delete(id)
        return result

    result = asyncio.run(_delete())
    return result


def repo_relate(source, relationship, target):
    async def _relate():
        async with db_connection() as db:
            query = f"RELATE {source}->{relationship}->{target};"
            result = await db.query(query)
        return result

    result = asyncio.run(_relate())
    return result


def execute_migration():
    async def _query():
        content = None
        with open("db_setup.surrealql", "r") as file:
            content = file.read()
        async with db_connection() as db:
            result = await db.query(content)
        return result

    result = asyncio.run(_query())
    return result[0]["result"]
