import json
import time

import requests

from ...vars import GOOGLE_BOOKS_API_KEY


class BookMetadataClient:
    GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
    OPEN_LIBRARY_API = "https://openlibrary.org"
    OPEN_WIKI_API = "https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/"
    USER_AGENT = "ubiblio_bot/1.0 (https://github.com/seanboyce/ubiblio;)"

    def google_books_by_isbn(self, isbn: str) -> tuple[dict[str, str], int | None]:
        if not GOOGLE_BOOKS_API_KEY:
            return {}, None
        response = requests.get(
            self.GOOGLE_BOOKS_API,
            params={"q": f"+isbn:{isbn}", "key": GOOGLE_BOOKS_API_KEY})
        if response.ok:
            raw_book = json.loads(response.text)["items"][0]["volumeInfo"]
            book = {}
            book["Title"] = raw_book["title"]
            book["Author"] = raw_book["authors"][0]
            book["Summary"] = raw_book.get("description", "")
            return book, 200
        return {}, response.status_code

    def open_library_by_isbn(self, isbn: str) -> tuple[dict[str, str], int]:
        url = self.OPEN_LIBRARY_API + f"/api/books?bibkeys={isbn}&format=json&jscmd=details"
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept-Encoding": "gzip",
        }
        response = requests.get(url, headers=headers)
        if response.ok:
            data = response.json()
            entry = data.get(isbn, {})
            book_details = entry.get("details", {})
            book = {
                "Title": book_details.get("title", ""),
                "Summary": book_details.get("description", {}).get("value", ""),
            }
            authors = book_details.get("authors", [])
            if len(authors) > 0 and "name" in authors[0]:
                book["Author"] = authors[0]["name"]
            else:
                book["Author"] = ""
            return book, 200
        else:
            return {}, response.status_code

    def open_wiki_by_isbn(self, isbn: str) -> tuple[dict[str, str], int]:
        url = self.OPEN_WIKI_API + "isbn/" + str(isbn) + ".json"
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept-Encoding": "gzip",
        }
        response = requests.get(url, headers=headers)
        if response.ok:
            raw_book = json.loads(response.text)[0]
            book = {}
            book["Title"] = raw_book["title"]
            raw_author = raw_book["author"][0]
            author = " ".join(raw_author).strip()
            book["Author"] = author
            book["Summary"] = ""
            return book, 200
        else:
            return {}, response.status_code
