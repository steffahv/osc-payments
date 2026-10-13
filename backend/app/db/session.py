"""One session per request. Future services decide when to commit."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args={"connect_timeout": 5},
        hide_parameters=True,
    )


def get_db() -> Iterator[Session]:
    # Closing rolls back uncommitted transactions, including on errors.
    with Session(get_engine()) as session:
        yield session
