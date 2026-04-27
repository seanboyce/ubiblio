from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import crud, schemas
from ..database import SessionLocal
from ..dependencies import (
    get_rate_limiter, templates,
    current_user,
)

router = APIRouter()


@router.get("/read/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_read(bookId, request: Request, user: current_user):
    db = SessionLocal()
    try:
        readingListItem = schemas.readingListItemCreate(book=bookId, user_id=user.id)
        crud.readBook(db, readingListItem)
    finally:
        db.close()
    return RedirectResponse(url='/readingLists')


@router.get("/unread/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_unread(bookId, request: Request, user: current_user):
    db = SessionLocal()
    try:
        crud.bookUnRead(db, bookId)
    finally:
        db.close()
    return RedirectResponse(url='/readingLists')


@router.get("/readingLists", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def reading_list(request: Request, user: current_user):
    db = SessionLocal()
    try:
        readingList = crud.readingList(db, user.id)
        books = [crud.getBookById(db, i.book) for i in readingList]
    finally:
        db.close()
    context = {
        "books": books,
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse(request, "readinglist.html", context)


@router.get("/return/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_return(bookId, request: Request, user: current_user):
    db = SessionLocal()
    try:
        book = crud.getBookById(db, bookId)
        book = schemas.Book(
            id=bookId, title=book.title, author=book.author, summary=book.summary,
            genre=book.genre, library=book.library, shelf=book.shelf, collection=book.collection,
            notes=book.notes, ISBN=book.ISBN, owned=book.owned, ebook=book.ebook,
            customField1=book.customField1, customField2=book.customField2, withdrawn=False,
        )
        crud.bookReturn(db, book)
    finally:
        db.close()
    return RedirectResponse(url='/searchbooks')


@router.get("/withdraw/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_withdraw(bookId, request: Request, user: current_user):
    db = SessionLocal()
    try:
        book = crud.getBookById(db, bookId)
        book = schemas.Book(
            id=bookId, title=book.title, author=book.author, summary=book.summary,
            genre=book.genre, library=book.library, shelf=book.shelf, collection=book.collection,
            notes=book.notes, ISBN=book.ISBN, owned=book.owned, ebook=book.ebook,
            withdrawnBy=user.username, customField1=book.customField1,
            customField2=book.customField2, withdrawn=True,
        )
        crud.bookWithdraw(db, book)
    finally:
        db.close()
    return RedirectResponse(url='/searchbooks')


@router.get("/withdrawn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def withdrawn_list(request: Request, user: current_user):
    db = SessionLocal()
    try:
        books = list(crud.browseWithdrawn(db))
    finally:
        db.close()
    context = {
        "user": user,
        "books": books,
        "request": request,
    }
    return templates.TemplateResponse(request, "withdrawn.html", context)


@router.get("/wishlist", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def wishlist(request: Request, user: current_user):
    db = SessionLocal()
    try:
        books = crud.browseWishlist(db)
    finally:
        db.close()
    context = {
        "user": user,
        "books": books,
        "request": request,
    }
    return templates.TemplateResponse(request, "wishlist.html", context)
