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

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


DB_URL_VARNAME = "DATABASE_URL"
DB_URL = os.getenv(DB_URL_VARNAME)
if not DB_URL:
    raise ValueError(f"{DB_URL_VARNAME} environment variable is not set")


logger = logging.getLogger(Path(__file__).name)
logging.basicConfig(level=logging.INFO)


async def wait_for_db(
    engine: AsyncEngine, retries: int = 10, delay: float = 2.0
) -> bool:
    for attempt in range(retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Database is ready")
                return True

        except Exception as exc:
            logger.warning(
                "Database not ready (attempt %d/%d): %r", attempt, retries, exc
            )

            await asyncio.sleep(delay)
    return False


async def main():
    try:
        engine = create_async_engine(DB_URL)
    except SQLAlchemyError as exc:
        logger.error("Cannot create database engine for `%s`: %r", DB_URL, exc)
        return 1

    try:
        if await wait_for_db(engine):
            logger.info("Successfully connected to the database")
            return 0

        logger.info("Failed to connect to the database")
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    status = asyncio.run(main())
    sys.exit(status)
