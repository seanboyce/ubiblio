import os
from pathlib import Path
import uuid

from fastapi.testclient import TestClient
import pytest

from tests.helpers import access_token_cookie, create_test_user


@pytest.fixture
def client():
    from ubiblio.main import app

    with TestClient(app) as c:
        yield c


class TestDownloadEbook:
    @pytest.fixture
    def ebook_path(self):
        ebook_dir = Path("./static/eBooks")
        ebook_dir.mkdir(parents=True, exist_ok=True)
        name = f"test_ebook_{uuid.uuid4().hex}.txt"
        path = f"{ebook_dir}/{name}"

        return path

    def test_download_ebook_happy_path(self, client, ebook_path):
        # Arrange
        name = os.path.basename(ebook_path)
        content = b"hello ebook"

        with open(ebook_path, "wb") as f:
            f.write(content)

        try:
            # Act
            with create_test_user() as user:
                with access_token_cookie(client, user):
                    r = client.get(f"/downloadEbook/{name}")

            # Assert
            assert r.status_code == 200
            assert r.content == content
            assert "application/octet-stream" in (
                r.headers.get("content-type"))
            assert name in (r.headers.get("content-disposition") or "")
        finally:
            # Cleanup
            if os.path.exists(ebook_path):
                os.remove(ebook_path)

    def test_download_ebook_missing_file(self, client):
        # Arrange
        name = f"missing_{uuid.uuid4().hex}.epub"

        # Act
        with create_test_user() as user:
            with access_token_cookie(client, user):
                r = client.get(f"/downloadEbook/{name}")

        # Assert
        assert r.status_code == 200
        print(r.text)
        assert r.text == "Failed to download ebook."
