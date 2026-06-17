#!/usr/bin/env -S uv run --no-progress
# /// script
# requires-python = "~=3.13.6"
# dependencies = ["sqlalchemy[postgresql-asyncpg]~=2.0.41"]
# ///

# pylint: disable=broad-exception-caught

"""Wait for PostgreSQL database to become available."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text as sa_text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


DB_URL_VARNAME = "{{ cookiecutter.env_prefix }}DATABASE_URL"
DB_URL = os.getenv(DB_URL_VARNAME)

RETRIES = int(os.getenv("PG_WAIT_RETRIES", "10"))
DELAY = float(os.getenv("PG_WAIT_DELAY", "2.0"))
CONNECT_TIMEOUT = float(os.getenv("PG_WAIT_CONNECT_TIMEOUT", "5.0"))

logger = logging.getLogger(Path(__file__).name)


async def wait_for_db(engine: AsyncEngine, retries: int, delay: float) -> bool:
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(sa_text("SELECT 1"))
            logger.info("Database is ready")
            return True

        except Exception as exc:
            logger.warning(
                "Database not ready (attempt %d/%d): %r", attempt, retries, exc
            )
            if attempt < retries:
                await asyncio.sleep(delay)

    return False


async def main() -> int:
    if not DB_URL:
        logger.error("%s environment variable is not set", DB_URL_VARNAME)
        return 1

    try:
        url = make_url(DB_URL)
    except ArgumentError as exc:
        logger.error("Invalid %s: %r", DB_URL_VARNAME, exc)
        return 1

    safe_url = url.render_as_string(hide_password=True)

    engine = create_async_engine(
        url,
        poolclass=NullPool,
        connect_args={"timeout": CONNECT_TIMEOUT},
    )
    try:
        if await wait_for_db(engine, RETRIES, DELAY):
            return 0

        logger.error("Could not connect to the database: `%s`", safe_url)
        return 2
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(asyncio.run(main()))
