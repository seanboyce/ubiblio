from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
import json
import requests
import time

from .. import crud, schemas
from ..database import SessionLocal
from ..dependencies import (
    get_rate_limiter, templates,
    get_current_user_from_token,
    bookForm,
)
from ..vars import GOOGLE_BOOKS_API_KEY

router = APIRouter()


# --------------------------------------------------------------------------
# Book fetch functions (ISBN lookup helpers)
# --------------------------------------------------------------------------
def goobMeta(isbn, key):
    url = "https://www.googleapis.com/books/v1/volumes?q=+isbn:" + str(isbn) + "&key=" + str(key)
    response = requests.get(url)
    if response.ok:
        rawBook = json.loads(response.text)["items"][0]["volumeInfo"]
        book = {}
        book["Title"] = rawBook["title"]
        book["Author"] = rawBook["authors"][0]
        try:
            book["Summary"] = rawBook["description"]
        except:
            book["Summary"] = ""
        return book, 200
    else:
        return {}, response.status_code


def openLibMeta(isbn):
    url = "https://openlibrary.org/isbn/" + str(isbn) + ".json"
    headers = {
        "User-Agent": 'ubiblio_bot/1.0 (https://github.com/seanboyce/ubiblio;)',
        "Accept-Encoding": 'gzip'
    }
    response = requests.get(url, headers=headers)
    if response.ok:
        rawBook = json.loads(response.text)
        book = {}
        book["Title"] = rawBook["title"]
        authorURL = str(rawBook["authors"][0]["key"])
        url = "https://openlibrary.org" + authorURL + ".json"
        time.sleep(1)
        response = requests.get(url)
        if response.ok:
            book["Author"] = json.loads(response.text)["personal_name"]
        else:
            print(response.status_code)
        try:
            book["Summary"] = rawBook["description"]["value"]
        except:
            book["Summary"] = ""
        return book, 200
    else:
        return {}, response.status_code


def openWikiMeta(isbn):
    url = "https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/" + str(isbn)
    headers = {
        "User-Agent": 'ubiblio_bot/1.0 (https://github.com/seanboyce/ubiblio;)',
        "Accept-Encoding": 'gzip'
    }
    response = requests.get(url, headers=headers)
    if response.ok:
        rawBook = json.loads(response.text)[0]
        book = {}
        book["Title"] = rawBook["title"]
        rawAuthor = rawBook["author"][0]
        author = ""
        for i in rawAuthor:
            author = author + i + " "
        author = author.strip()
        book["Author"] = author
        book["Summary"] = ""
        return book, 200
    else:
        return {}, response.status_code


def goobTitle(title, key):
    url = "https://www.googleapis.com/books/v1/volumes?q=+intitle:" + str(title) + "&key=" + str(key)
    response = requests.get(url)
    if response.ok:
        rawBooks = json.loads(response.text)
        return {}, 200
    else:
        return {}, response.status_code


# --------------------------------------------------------------------------
# Book CRUD endpoints
# --------------------------------------------------------------------------
@router.get("/add_book", dependencies=[get_rate_limiter(times=3, seconds=2)], response_class=HTMLResponse)
def add_book_form(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            config = crud.getConfig(db)
            db.close()
            context = {
                "config": config,
                "user": user,
                "request": request,
            }
            return templates.TemplateResponse(request, "newBook.html", context)
        if not user.isAdmin == True:
            return "You are not authorized to add books. Only an admin can do this."
    except Exception as e:
        print(e)
        return "An error has occured."


@router.post("/add_book", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def add_book_post(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if not user.isAdmin == True:
        return "You are not authorized to add books. Only an admin can do this."
    form = bookForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            db = SessionLocal()
            newBook = schemas.BookCreate(title=form.title, author=form.author, summary=form.summary, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN=form.ISBN, owned=form.owned, ebook=form.ebook, customField1=form.customField1, customField2=form.customField2, withdrawn=form.withdrawn)
            crud.createBook(db, newBook)
            db.close()
            return RedirectResponse(url='/searchbooks/', status_code=status.HTTP_303_SEE_OTHER)
        except Exception as e:
            print(e)
            return "Fail"


@router.get("/delete_book/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def delete_book(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user.isAdmin == True:
        db = SessionLocal()
        crud.deleteBook(db, bookId)
        db.close()
        return RedirectResponse(url='/searchbooks/')
    if not user.isAdmin == True:
        return "You are not authorized to delete books. Only an admin can do this."


@router.get("/bookDetails/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_details(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        config = crud.getConfig(db)
        book = crud.getBookById(db, bookId)
        context = {
            "config": config,
            "book": book,
            "user": user,
            "request": request
        }
        if config.coverImages:
            images = crud.getImages(db, bookId)
            context["images"] = images
        if book.ebook == True:
            ebookFiles = crud.getEbookFiles(db, bookId)
            context["ebookFiles"] = ebookFiles
            db.close()
            return templates.TemplateResponse(request, "ebookDetails.html", context)
        else:
            db.close()
            return templates.TemplateResponse(request, "bookDetails.html", context)
    if not user:
        return "You are not logged in. Login to view books."


@router.post("/update_book/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def update_book(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if not user.isAdmin == True:
        return "You are not authorized to update books. Only an admin can do this."
    form = bookForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            db = SessionLocal()
            config = crud.getConfig(db)
            book = schemas.Book(id=bookId, title=form.title, author=form.author, summary=form.summary, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN=form.ISBN, owned=form.owned, ebook=form.ebook, customField1=form.customField1, customField2=form.customField2, withdrawn=form.withdrawn)
            crud.updateBook(db, book)
            book = crud.getBookById(db, bookId)
            db.close()
            return RedirectResponse(url='/bookDetails/' + bookId, status_code=status.HTTP_303_SEE_OTHER)
        except Exception as e:
            print(e)
            return "Fail"


@router.get("/update_book/{bookId}", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
def update_book_form(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            config = crud.getConfig(db)
            book = crud.getBookById(db, bookId)
            db.close()
            context = {
                "config": config,
                "user": user,
                "book": book,
                "request": request
            }
            return templates.TemplateResponse(request, "updateBook.html", context)
        if not user.isAdmin == True:
            return "You are not authorized to update books. Only an admin can do this."
    except Exception as e:
        print(e)
        return "An error has occured."


@router.get("/scan_isbn", dependencies=[get_rate_limiter(times=3, seconds=2)], response_class=HTMLResponse)
def scan_book_form(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin:
            db = SessionLocal()
            config = crud.getConfig(db)
            db.close()
            context = {
                "config": config,
                "user": user,
                "request": request,
            }
            return templates.TemplateResponse(request, "scanIsbn.html", context)
        if not user.isAdmin:
            return "You are not authorized to add books. Only an admin can do this."
    except Exception as e:
        print(e)
        return "An error has occured."


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------
@router.get("/searchbooks", dependencies=[get_rate_limiter(times=4, seconds=2)], response_class=HTMLResponse)
def search_book_get(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    data = []
    context = {
        "request": request,
        "user": user,
        "data": data
    }
    return templates.TemplateResponse(request, "booksearch.html", context)


@router.post("/searchbooks", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def search_books(request: Request, user: schemas.User = Depends(get_current_user_from_token), title: str = "%", author: str = "%", skip: int = "%", onlyEbooks: bool = "%", noEbooks: bool = "%"):
    try:
        db = SessionLocal()
        books = crud.searchBooks(db, str(title), str(author), int(skip), bool(onlyEbooks), bool(noEbooks))
        result = json.dumps(jsonable_encoder(books[0]))
        data = {}
        data['result'] = result
        data['count'] = books[1]
        db.close()
        return json.dumps(jsonable_encoder(data))
    except Exception as e:
        print(e)


@router.post("/searchBooksByAuthor", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def search_book_author(request: Request, user: schemas.User = Depends(get_current_user_from_token), author: str = "%", skip: int = 0, onlyEbooks: bool = "%", noEbooks: bool = "%"):
    try:
        db = SessionLocal()
        books = jsonable_encoder(crud.searchBooksbyAuthor(db, str(author), int(skip), bool(onlyEbooks), bool(noEbooks)))
        result = json.dumps(jsonable_encoder(books[0]))
        data = {}
        data['result'] = result
        data['count'] = books[1]
        db.close()
        return json.dumps(jsonable_encoder(data))
    except Exception as e:
        db.close()
        return "An error has occured."


@router.post("/searchBooksByTitle", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def search_book_title(request: Request, user: schemas.User = Depends(get_current_user_from_token), title: str = "%", skip: int = 0, onlyEbooks: bool = "%", noEbooks: bool = "%"):
    try:
        db = SessionLocal()
        books = jsonable_encoder(crud.searchBooksbyTitle(db, str(title), int(skip), bool(onlyEbooks), bool(noEbooks)))
        result = json.dumps(jsonable_encoder(books[0]))
        data = {}
        data['result'] = result
        data['count'] = books[1]
        db.close()
        return json.dumps(jsonable_encoder(data))
    except Exception as e:
        db.close()
        return "An error has occured."


# --------------------------------------------------------------------------
# ISBN autoadd
# --------------------------------------------------------------------------
@router.get("/isbn/{isbn}/{method}", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
def new_isbn(isbn, method, response: Response, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            book = {}
            isbn = isbn.strip()
            if len(GOOGLE_BOOKS_API_KEY) > 0:
                try:
                    book, response = goobMeta(isbn, GOOGLE_BOOKS_API_KEY)
                    if response != 200:
                        print("Google Books API failed with response: ")
                        print(response)
                except Exception as e:
                    print("Google Books API failed with response: ")
                    print(response)
            else:
                pass
            try:
                if len(book) == 0:
                    book, response = openLibMeta(isbn)
                    if response != 200:
                        print("Open Library API failed with response: ")
                        print(response)
                else:
                    pass
            except Exception as e:
                print("Open Library API failed with response: ")
                print(e)
            try:
                if len(book) == 0:
                    book, response = openWikiMeta(isbn)
                    if response != 200:
                        print("Wikipedia API failed with response: ")
                        print(response)
                else:
                    pass
            except Exception as e:
                print("Wikipedia API failed with response: ")
                print(e)
            if len(book) == 0:
                raise LookupError(f"Book with isbn {isbn} not found!")
            addISBN = [0]
            book = schemas.BookCreate(title=book["Title"], author=book["Author"], summary=book["Summary"], ISBN=isbn)
            db = SessionLocal()
            config = crud.getConfig(db)
            db.close()
            context = {
                "config": config,
                "user": user,
                "addISBN": addISBN,
                "book": book,
                "request": request
            }
            return templates.TemplateResponse(request, "newBook.html", context)
        if not user.isAdmin == True:
            return "You are not authorized to update books. Only an admin can do this."
    except Exception as e:
        errors = ["ISBN " + str(isbn) + " not found -- try another."]
        context = {
            "errors": errors,
            "user": user,
            "request": request
        }
        if method == "scan":
            return templates.TemplateResponse(request, "scanIsbn.html", context)
        else:
            return templates.TemplateResponse(request, "addisbn.html", context)


@router.get("/addisbn", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
async def add_isbn(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user.isAdmin == True:
        context = {
            "user": user,
            "request": request
        }
        return templates.TemplateResponse(request, "addisbn.html", context)
    if not user.isAdmin == True:
        return "You are not authorized to add books. Only an admin can do this."


@router.post("/addanotherisbn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def add_another_isbn(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user.isAdmin == True:
        form = bookForm(request)
        await form.load_data()
        if await form.is_valid():
            db = SessionLocal()
            newBook = schemas.BookCreate(title=form.title, author=form.author, summary=form.summary, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN=form.ISBN, owned=form.owned, ebook=form.ebook, customField1=form.customField1, customField2=form.customField2, withdrawn=form.withdrawn)
            crud.createBook(db, newBook)
            db.close()
            context = {
                "user": user,
                "request": request
            }
        return templates.TemplateResponse(request, "addisbn.html", context)
    if not user.isAdmin == True:
        return "You are not authorized to add books. Only an admin can do this."


@router.post("/scananotherisbn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def scan_another_isbn(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user.isAdmin:
        form = bookForm(request)
        await form.load_data()
        if await form.is_valid():
            db = SessionLocal()
            newBook = schemas.BookCreate(title=form.title, author=form.author, summary=form.summary, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN=form.ISBN, owned=form.owned, ebook=form.ebook, customField1=form.customField1, customField2=form.customField2, withdrawn=form.withdrawn)
            crud.createBook(db, newBook)
            db.close()
            context = {
                "user": user,
                "request": request
            }
        return templates.TemplateResponse(request, "scanIsbn.html", context)
    if not user.isAdmin:
        return "You are not authorized to add books. Only an admin can do this."


# --------------------------------------------------------------------------
# Browse by Genre
# --------------------------------------------------------------------------
@router.get("/booksByGenre/{genre}", dependencies=[get_rate_limiter(times=12, seconds=2)], response_class=HTMLResponse)
async def books_by_genre(genre, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        books = crud.browseBooksByGenre(db, genre)
        db.close()
        context = {
            "user": user,
            "books": books,
            "request": request
        }
        return templates.TemplateResponse(request, "booksByGenre.html", context)
    if not user:
        return "You are not logged in. Login to view books."


@router.get("/genre/", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def book_genres(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        genres = crud.getGenres(db)
        db.close()
        context = {
            "user": user,
            "genres": genres,
            "request": request
        }
        return templates.TemplateResponse(request, "genres.html", context)
    if not user:
        return "You are not logged in. Login to view books."
