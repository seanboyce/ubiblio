import secrets
import uuid
from contextlib import contextmanager
from typing import Iterator, NamedTuple

from ubiblio import crud, schemas
from ubiblio.database import SessionLocal


class TestUser(NamedTuple):
    username: str
    id: int


@contextmanager
def create_test_user(username: str | None = None, is_admin: bool = False) -> Iterator[TestUser]:
    """
    Create a user for the duration of the ``with`` block, then remove it from the database.

    Usage::

        with create_test_user() as user:
            ...
        with create_test_user("my_user") as user:
            ...
    """
    name = username or f"testuser_{uuid.uuid4().hex[:12]}"
    db = SessionLocal()
    try:
        result = crud.create_user(
            db,
            schemas.UserCreate(
                username=name,
                password=secrets.token_urlsafe(16),
                isAdmin=is_admin,
            ),
        )
    finally:
        db.close()

    if result is False:
        raise RuntimeError(f"Failed to create test user {name!r}")

    user = TestUser(username=result.username, id=result.id)
    try:
        yield user
    finally:
        db = SessionLocal()
        try:
            row = crud.get_user_by_username(db, name)
            if row is not None and not crud.deleteUser(db, row.id):
                raise RuntimeError(f"Failed to delete test user {name!r}")
        finally:
            db.close()
