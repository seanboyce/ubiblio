from contextlib import contextmanager
from typing import Iterator

from fastapi.testclient import TestClient

from ubiblio.dependencies import create_access_token, settings

from .create_test_user import TestUser


@contextmanager
def access_token_cookie(
    client: TestClient,
    user: str | TestUser,
) -> Iterator[None]:
    """
    Set the app's ``access_token`` cookie (``Bearer <jwt>``), then restore the previous value or remove it on exit.

    ``user`` may be a :class:`TestUser` or a username string.
    """
    username = user.username if isinstance(user, TestUser) else user
    cookie_name = settings.COOKIE_NAME
    previous = client.cookies.get(cookie_name)
    token = create_access_token(data={"username": username})
    client.cookies.set(cookie_name, f"Bearer {token}")
    try:
        yield
    finally:
        if previous is None:
            client.cookies.delete(cookie_name)
        else:
            client.cookies.set(cookie_name, previous)
