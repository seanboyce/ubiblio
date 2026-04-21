from urllib.parse import urlencode

from pytest import MonkeyPatch
import responses

from ubiblio.routers.books.service import BookMetadataClient


class TestBookMetadataClientGoogleBooksByIsbn:
    @responses.activate
    def test_google_books_by_isbn_should_return_book_metadata(self, monkeypatch: MonkeyPatch) -> None:
        # Arrange
        isbn = "9780123456789"
        api_key = "test-api-key"
        monkeypatch.setattr(
            "ubiblio.routers.books.service.GOOGLE_BOOKS_API_KEY", api_key)
        query = urlencode({"q": f"isbn:{isbn}", "key": api_key})
        url = f"{BookMetadataClient.GOOGLE_BOOKS_API}?{query}"
        responses.add(
            responses.GET,
            url,
            json={
                "items": [
                    {
                        "volumeInfo": {
                            "title": "Test Title",
                            "authors": ["A. Reader"],
                            "description": "A fine book.",
                        }
                    }
                ]
            },
            status=200,
        )

        client = BookMetadataClient()

        # Act
        book, status = client.google_books_by_isbn(isbn)

        # Assert
        assert status == 200
        assert book == {
            "Title": "Test Title",
            "Author": "A. Reader",
            "Summary": "A fine book."
        }
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

    @responses.activate
    def test_google_books_by_isbn_should_return_error_when_api_key_is_missing(self, monkeypatch: MonkeyPatch) -> None:
        # Arrange
        isbn = "9780123456789"
        monkeypatch.setattr(
            "ubiblio.routers.books.service.GOOGLE_BOOKS_API_KEY", None)
        client = BookMetadataClient()

        # Act
        book, status = client.google_books_by_isbn(isbn)

        # Assert
        assert status is None
        assert book == {}

    @responses.activate
    def test_google_books_by_isbn_should_return_error_when_response_is_not_ok(self, monkeypatch: MonkeyPatch) -> None:
        # Arrange
        isbn = "9780123456789"
        api_key = "test-api-key"
        monkeypatch.setattr(
            "ubiblio.routers.books.service.GOOGLE_BOOKS_API_KEY", api_key)
        query = urlencode({"q": f"isbn:{isbn}", "key": api_key})
        url = f"{BookMetadataClient.GOOGLE_BOOKS_API}?{query}"
        responses.add(
            responses.GET,
            url,
            json={"error": "notfound", "key": "/isbn/invalid"},
            status=404,
        )

        client = BookMetadataClient()

        # Act
        book, status = client.google_books_by_isbn(isbn)

        # Assert
        assert status == 404
        assert book == {}


class TestBookMetadataClientOpenLibraryByIsbn:
    @responses.activate
    def test_open_library_by_isbn_should_return_book_metadata(self, monkeypatch: MonkeyPatch) -> None:
        # Arrange
        isbn = "9780123456789"

        responses.add(
            responses.GET,
            f"{BookMetadataClient.OPEN_LIBRARY_API}isbn/{isbn}.json",
            json={
                "title": "Test Title",
                "authors": [
                    {
                        "key": "/authors/OL1607920A"
                    }
                ],
                "description": {
                    "value": "A fine book.",
                }
            },
            status=200,
        )

        responses.add(
            responses.GET,
            f"{BookMetadataClient.OPEN_LIBRARY_API}/authors/OL1607920A.json",
            json={
                "personal_name": "A. Reader",
            },
            status=200,
        )

        client = BookMetadataClient()

        # Act
        book, status = client.open_library_by_isbn(isbn)
        # Assert
        assert status == 200
        assert book == {
            "Title": "Test Title",
            "Author": "A. Reader",
            "Summary": "A fine book.",
        }
        assert len(responses.calls) == 2
        assert responses.calls[0].request.url == f"{BookMetadataClient.OPEN_LIBRARY_API}isbn/{isbn}.json"
        assert responses.calls[1].request.url == f"{BookMetadataClient.OPEN_LIBRARY_API}/authors/OL1607920A.json"

    @responses.activate
    def test_open_library_by_isbn_should_return_error_when_response_is_not_ok(self, monkeypatch: MonkeyPatch) -> None:
        # Arrange
        isbn = "9780123456789"
        responses.add(
            responses.GET,
            f"{BookMetadataClient.OPEN_LIBRARY_API}isbn/{isbn}.json",
            json={},
            status=404,
        )
        client = BookMetadataClient()

        # Act
        book, status = client.open_library_by_isbn(isbn)

        # Assert
        assert status == 404
        assert book == {}

    @responses.activate
    def test_open_library_by_isbn_should_still_return_book_metadata_when_author_response_is_not_ok(self, monkeypatch: MonkeyPatch) -> None:
        # Arrange
        isbn = "9780123456789"
        responses.add(
            responses.GET,
            f"{BookMetadataClient.OPEN_LIBRARY_API}isbn/{isbn}.json",
            json={
                "title": "Test Title",
                "authors": [
                    {
                        "key": "/authors/OL1607920A"
                    }
                ],
                "description": {
                    "value": "A fine book.",
                }
            },
            status=200,
        )
        responses.add(
            responses.GET,
            f"{BookMetadataClient.OPEN_LIBRARY_API}/authors/OL1607920A.json",
            json={},
            status=404,
        )
        client = BookMetadataClient()

        # Act
        book, status = client.open_library_by_isbn(isbn)
        # Assert
        assert status == 200
        assert book == {"Summary": "A fine book.", "Title": "Test Title"}
