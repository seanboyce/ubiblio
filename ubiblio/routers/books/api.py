from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from . import service
from ... import crud, schemas
from ...database import SessionLocal
from ...dependencies import admin_user, bookForm, current_user, get_rate_limiter, templates

router = APIRouter()


# --------------------------------------------------------------------------
# Book CRUD endpoints
# --------------------------------------------------------------------------
@router.get("/add_book", dependencies=[get_rate_limiter(times=3, seconds=2)], response_class=HTMLResponse)
def add_book_form(request: Request, user: admin_user):
    try:
        db = SessionLocal()
        config = crud.getConfig(db)
        db.close()
        context = {
            "config": config,
            "user": user,
            "request": request,
        }
        return templates.TemplateResponse(request, "newBook.html", context)
    except Exception as e:
        print(e)
        return "An error has occured."


@router.post("/add_book", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def add_book_post(request: Request, user: admin_user):
    form = bookForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            db = SessionLocal()
            new_book = service.book_create_from_form(form)
            crud.createBook(db, new_book)
            db.close()
            return RedirectResponse(url="/searchbooks/", status_code=status.HTTP_303_SEE_OTHER)
        except Exception as e:
            print(e)
            return "Fail"


@router.get("/delete_book/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def delete_book(bookId, request: Request, user: admin_user):
    db = SessionLocal()
    crud.deleteBook(db, bookId)
    db.close()
    return RedirectResponse(url="/searchbooks/")


@router.get("/bookDetails/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_details(bookId, request: Request, user: current_user):
    if user:
        db = SessionLocal()
        config = crud.getConfig(db)
        book = crud.getBookById(db, bookId)
        context = {
            "config": config,
            "book": book,
            "user": user,
            "request": request,
        }
        if config.coverImages:
            images = crud.getImages(db, bookId)
            context["images"] = images
        if book.ebook == True:
            ebook_files = crud.getEbookFiles(db, bookId)
            context["ebookFiles"] = ebook_files
            db.close()
            return templates.TemplateResponse(request, "ebookDetails.html", context)
        else:
            db.close()
            return templates.TemplateResponse(request, "bookDetails.html", context)
    if not user:
        return "You are not logged in. Login to view books."


@router.post("/update_book/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def update_book(bookId, request: Request, user: admin_user):
    form = bookForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            db = SessionLocal()
            book = service.book_update_from_form(bookId, form)
            crud.updateBook(db, book)
            book = crud.getBookById(db, bookId)
            db.close()
            return RedirectResponse(url="/bookDetails/" + bookId, status_code=status.HTTP_303_SEE_OTHER)
        except Exception as e:
            print(e)
            return "Fail"


@router.get("/update_book/{bookId}", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
def update_book_form(bookId, request: Request, user: admin_user):
    try:
        db = SessionLocal()
        config = crud.getConfig(db)
        book = crud.getBookById(db, bookId)
        db.close()
        context = {
            "config": config,
            "user": user,
            "book": book,
            "request": request,
        }
        return templates.TemplateResponse(request, "updateBook.html", context)
    except Exception as e:
        print(e)
        return "An error has occured."


@router.get("/scan_isbn", dependencies=[get_rate_limiter(times=3, seconds=2)], response_class=HTMLResponse)
def scan_book_form(request: Request, user: schemas.User = admin_user):
    try:
        db = SessionLocal()
        config = crud.getConfig(db)
        db.close()
        context = {
            "config": config,
            "user": user,
            "request": request,
        }
        return templates.TemplateResponse(request, "scanIsbn.html", context)
    except Exception as e:
        print(e)
        return "An error has occured."


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------
@router.get("/searchbooks", dependencies=[get_rate_limiter(times=4, seconds=2)], response_class=HTMLResponse)
def search_book_get(request: Request, user: current_user):
    data = []
    context = {
        "request": request,
        "user": user,
        "data": data,
    }
    return templates.TemplateResponse(request, "booksearch.html", context)


@router.post("/searchbooks", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def search_books(
        request: Request,
        user: schemas.User = current_user,
        title: str = "%",
        author: str = "%",
        skip: int = "%",
        onlyEbooks: bool = "%",
        noEbooks: bool = "%"):
    db = SessionLocal()
    try:
        return service.search_books_json(db, str(title), str(author), int(skip), bool(onlyEbooks), bool(noEbooks))
    finally:
        db.close()


@router.post("/searchBooksByAuthor", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def search_book_author(
    request: Request,
    user: current_user,
    author: str = "%",
    skip: int = 0,
    onlyEbooks: bool = "%",
    noEbooks: bool = "%",
):
    db = SessionLocal()
    try:
        out = service.search_books_by_author_json(
            db, str(author), int(skip), bool(onlyEbooks), bool(noEbooks))
        if out is None:
            return "An error has occured."
        return out
    finally:
        db.close()


@router.post("/searchBooksByTitle", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def search_book_title(
    request: Request,
    user: current_user,
    title: str = "%",
    skip: int = 0,
    onlyEbooks: bool = "%",
    noEbooks: bool = "%",
):
    db = SessionLocal()
    try:
        out = service.search_books_by_title_json(
            db, str(title), int(skip), bool(onlyEbooks), bool(noEbooks))
        if out is None:
            return "An error has occured."
        return out
    finally:
        db.close()


# --------------------------------------------------------------------------
# ISBN autoadd
# --------------------------------------------------------------------------
@router.get("/isbn/{isbn}/{method}", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
def new_isbn(isbn, method, response: Response, request: Request, user: admin_user):
    try:
        book = service.lookup_book_metadata_by_isbn(isbn)
        add_isbn = [0]
        book_schema = service.book_create_from_isbn_metadata(
            book, isbn.strip())
        db = SessionLocal()
        config = crud.getConfig(db)
        db.close()
        context = {
            "config": config,
            "user": user,
            "addISBN": add_isbn,
            "book": book_schema,
            "request": request,
        }
        return templates.TemplateResponse(request, "newBook.html", context)
    except Exception:
        errors = ["ISBN " + str(isbn) + " not found -- try another."]
        context = {
            "errors": errors,
            "user": user,
            "request": request,
        }
        if method == "scan":
            return templates.TemplateResponse(request, "scanIsbn.html", context)
        else:
            return templates.TemplateResponse(request, "addisbn.html", context)


@router.get("/addisbn", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
async def add_isbn(request: Request, user: admin_user):
    context = {
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse(request, "addisbn.html", context)


@router.post("/addanotherisbn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def add_another_isbn(request: Request, user: admin_user):
    form = bookForm(request)
    await form.load_data()
    if await form.is_valid():
        db = SessionLocal()
        new_book = service.book_create_from_form(form)
        crud.createBook(db, new_book)
        db.close()
        context = {
            "user": user,
            "request": request,
        }
    return templates.TemplateResponse(request, "addisbn.html", context)


@router.post("/scananotherisbn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def scan_another_isbn(request: Request, user: admin_user):
    form = bookForm(request)
    await form.load_data()
    if await form.is_valid():
        db = SessionLocal()
        new_book = service.book_create_from_form(form)
        crud.createBook(db, new_book)
        db.close()
        context = {
            "user": user,
            "request": request,
        }
    return templates.TemplateResponse(request, "scanIsbn.html", context)


# --------------------------------------------------------------------------
# Browse by Genre
# --------------------------------------------------------------------------
@router.get("/booksByGenre/{genre}", dependencies=[get_rate_limiter(times=12, seconds=2)], response_class=HTMLResponse)
async def books_by_genre(genre, request: Request, user: current_user):
    if user:
        db = SessionLocal()
        books = crud.browseBooksByGenre(db, genre)
        db.close()
        context = {
            "user": user,
            "books": books,
            "request": request,
        }
        return templates.TemplateResponse(request, "booksByGenre.html", context)
    if not user:
        return "You are not logged in. Login to view books."


@router.get("/genre/", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def book_genres(request: Request, user: current_user):
    if user:
        db = SessionLocal()
        genres = crud.getGenres(db)
        db.close()
        context = {
            "user": user,
            "genres": genres,
            "request": request,
        }
        return templates.TemplateResponse(request, "genres.html", context)
    if not user:
        return "You are not logged in. Login to view books."
