import pytest
from fastapi import HTTPException

from ubiblio.dependencies.auth import get_admin_user


class _StubUser:
    def __init__(self, *, is_admin: bool):
        self.isAdmin = is_admin


class TestGetAdminUser:
    def test_admin_user_is_returned(self):
        user = _StubUser(is_admin=True)
        result = get_admin_user(user)
        assert result is user

    def test_non_admin_raises_403(self):
        user = _StubUser(is_admin=False)
        with pytest.raises(HTTPException) as exc_info:
            get_admin_user(user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "You are not authorized to add books. Only an admin can do this."
