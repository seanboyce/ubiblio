import json
import time
from typing import Any

import requests
from sqlalchemy.orm import Session

from ... import crud, schemas
from ...vars import GOOGLE_BOOKS_API_KEY


# --------------------------------------------------------------------------
# External metadata (ISBN / title lookup)
# --------------------------------------------------------------------------

class BookMetadataClient:
    GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
    OPEN_LIBRARY_API = "https://openlibrary.org/"

    def google_books_by_isbn(self, isbn: str) -> tuple[dict[str, str], int | None]:
        if not GOOGLE_BOOKS_API_KEY:
            return {}, None
        response = requests.get(self.GOOGLE_BOOKS_API, params={
                                "q": f"isbn:{isbn}", "key": GOOGLE_BOOKS_API_KEY})
        if response.ok:
            raw_book = json.loads(response.text)["items"][0]["volumeInfo"]
            book = {}
            book["Title"] = raw_book["title"]
            book["Author"] = raw_book["authors"][0]
            try:
                book["Summary"] = raw_book["description"]
            except Exception:
                book["Summary"] = ""
            return book, 200
        else:
            return {}, response.status_code

    def open_library_by_isbn(self, isbn: str) -> tuple[dict[str, str], int | None]:
        url = self.OPEN_LIBRARY_API + "isbn/" + str(isbn) + ".json"
        headers = {
            "User-Agent": "ubiblio_bot/1.0 (https://github.com/seanboyce/ubiblio;)",
            "Accept-Encoding": "gzip",
        }
        response = requests.get(url, headers=headers)
        if response.ok:
            raw_book = json.loads(response.text)
            book = {}
            book["Title"] = raw_book["title"]
            author_url = str(raw_book["authors"][0]["key"])
            url = self.OPEN_LIBRARY_API + author_url + ".json"
            time.sleep(1)
            response = requests.get(url)
            if response.ok:
                book["Author"] = json.loads(response.text)["personal_name"]
            else:
                print(response.status_code)
            try:
                book["Summary"] = raw_book["description"]["value"]
            except Exception:
                book["Summary"] = ""
            return book, 200
        else:
            return {}, response.status_code


def open_wiki_meta(isbn):
    url = "https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/" + \
        str(isbn)
    headers = {
        "User-Agent": "ubiblio_bot/1.0 (https://github.com/seanboyce/ubiblio;)",
        "Accept-Encoding": "gzip",
    }
    response = requests.get(url, headers=headers)
    if response.ok:
        raw_book = json.loads(response.text)[0]
        book = {}
        book["Title"] = raw_book["title"]
        raw_author = raw_book["author"][0]
        author = ""
        for i in raw_author:
            author = author + i + " "
        author = author.strip()
        book["Author"] = author
        book["Summary"] = ""
        return book, 200
    else:
        return {}, response.status_code


def goob_title(title, key):
    url = "https://www.googleapis.com/books/v1/volumes?q=+intitle:" + \
        str(title) + "&key=" + str(key)
    response = requests.get(url)
    if response.ok:
        json.loads(response.text)
        return {}, 200
    else:
        return {}, response.status_code


def lookup_book_metadata_by_isbn(isbn: str) -> dict[str, Any]:
    """
    Resolve ISBN to Title/Author/Summary via Google Books, then Open Library, then Wikipedia.
    Raises LookupError if no source returns data.
    """
    book: dict[str, Any] = {}
    isbn = isbn.strip()
    response = 0
    client = BookMetadataClient()

    try:
        book, response = client.google_books_by_isbn(isbn)
        if response is not None and response != 200:
            print("Google Books API failed with response: ")
            print(response)
    except Exception:
        print("Google Books API failed with response: ")
        print(response)

    try:
        if len(book) == 0:
            book, response = client.open_library_by_isbn(isbn)
            if response is not None and response != 200:
                print("Open Library API failed with response: ")
                print(response)
    except Exception as e:
        print("Open Library API failed with response: ")
        print(e)

    try:
        if len(book) == 0:
            book, response = open_wiki_meta(isbn)
            if response != 200:
                print("Wikipedia API failed with response: ")
                print(response)
    except Exception as e:
        print("Wikipedia API failed with response: ")
        print(e)

    if len(book) == 0:
        raise LookupError(f"Book with isbn {isbn} not found!")
    return book


# --------------------------------------------------------------------------
# Form → schema (book fields)
# --------------------------------------------------------------------------
def book_create_from_form(form) -> schemas.BookCreate:
    return schemas.BookCreate(
        title=form.title,
        author=form.author,
        summary=form.summary,
        genre=form.genre,
        library=form.library,
        shelf=form.shelf,
        collection=form.collection,
        notes=form.notes,
        ISBN=form.ISBN,
        owned=form.owned,
        ebook=form.ebook,
        customField1=form.customField1,
        customField2=form.customField2,
        withdrawn=form.withdrawn,
    )


def book_update_from_form(book_id, form) -> schemas.Book:
    return schemas.Book(
        id=book_id,
        title=form.title,
        author=form.author,
        summary=form.summary,
        genre=form.genre,
        library=form.library,
        shelf=form.shelf,
        collection=form.collection,
        notes=form.notes,
        ISBN=form.ISBN,
        owned=form.owned,
        ebook=form.ebook,
        customField1=form.customField1,
        customField2=form.customField2,
        withdrawn=form.withdrawn,
    )


# --------------------------------------------------------------------------
# Search serialization
# --------------------------------------------------------------------------
def search_books_json(db: Session, title: str, author: str, skip: int, only_ebooks: bool, no_ebooks: bool) -> str | None:
    from fastapi.encoders import jsonable_encoder

    try:
        books = crud.searchBooks(db, str(title), str(author), int(
            skip), bool(only_ebooks), bool(no_ebooks))
        result = json.dumps(jsonable_encoder(books[0]))
        data: dict[str, Any] = {"result": result, "count": books[1]}
        return json.dumps(jsonable_encoder(data))
    except Exception as e:
        print(e)
        return None


def search_books_by_author_json(
    db: Session, author: str, skip: int, only_ebooks: bool, no_ebooks: bool
) -> str | None:
    from fastapi.encoders import jsonable_encoder

    try:
        books = jsonable_encoder(crud.searchBooksbyAuthor(
            db, str(author), int(skip), bool(only_ebooks), bool(no_ebooks)))
        result = json.dumps(jsonable_encoder(books[0]))
        data: dict[str, Any] = {"result": result, "count": books[1]}
        return json.dumps(jsonable_encoder(data))
    except Exception as e:
        print(e)
        return None


def search_books_by_title_json(
    db: Session, title: str, skip: int, only_ebooks: bool, no_ebooks: bool
) -> str | None:
    from fastapi.encoders import jsonable_encoder

    try:
        books = jsonable_encoder(crud.searchBooksbyTitle(
            db, str(title), int(skip), bool(only_ebooks), bool(no_ebooks)))
        result = json.dumps(jsonable_encoder(books[0]))
        data: dict[str, Any] = {"result": result, "count": books[1]}
        return json.dumps(jsonable_encoder(data))
    except Exception as e:
        print(e)
        return None


def book_create_from_isbn_metadata(book: dict[str, Any], isbn: str) -> schemas.BookCreate:
    return schemas.BookCreate(
        title=book["Title"],
        author=book["Author"],
        summary=book["Summary"],
        ISBN=isbn,
    )
