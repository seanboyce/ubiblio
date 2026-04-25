import pytest
from fastapi.testclient import TestClient

from tests.helpers import access_token_cookie, create_test_user


class TestHeadRequestsNoMethodNotAllowed:

    @pytest.fixture(autouse=True)
    def setup_client(self):
        from ubiblio.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            self.client = client
            yield

    @pytest.mark.parametrize("path", [
        "/",
        "/favicon.ico",
    ])
    def test_head_on_public_endpoints_returns_200(self, path):
        response = self.client.head(path, follow_redirects=False)
        assert response.status_code == 200, (
            f"HEAD {path} returned {response.status_code} instead of 200"
        )

    @pytest.mark.parametrize("path", [
        "/searchbooks",
        "/genre/",
    ])
    def test_head_on_authenticated_endpoints(self, path):
        with create_test_user() as user:
            with access_token_cookie(self.client, user):
                response = self.client.head(path, follow_redirects=False)
        assert response.status_code == 200, (
            f"HEAD {path} returned {response.status_code} instead of 200"
        )
        assert response.content == b""

    @pytest.mark.parametrize("path", [
        "/add_book",
        "/addisbn",
        "/scan_isbn",
    ])
    def test_head_on_admin_endpoints(self, path):
        with create_test_user(is_admin=True) as user:
            with access_token_cookie(self.client, user):
                response = self.client.head(path, follow_redirects=False)
        assert response.status_code == 200, (
            f"HEAD {path} returned {response.status_code} instead of 200"
        )
        assert response.content == b""
