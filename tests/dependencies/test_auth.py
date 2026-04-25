import pytest
from fastapi import HTTPException

from ubiblio.dependencies.auth import get_admin_user, get_user
from tests.helpers.create_test_user import create_test_user


class TestGetAdminUser:
    def test_admin_user_is_returned(self):
        with create_test_user(is_admin=True) as test_user:
            user = get_user(test_user.username)
            result = get_admin_user(user)
            assert result is user

    def test_non_admin_raises_403(self):
        with create_test_user(is_admin=False) as test_user:
            user = get_user(test_user.username)
            with pytest.raises(HTTPException) as exc_info:
                get_admin_user(user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "You are not authorized to add books. Only an admin can do this."
