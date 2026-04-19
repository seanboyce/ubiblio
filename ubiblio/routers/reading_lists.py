from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import crud, schemas
from ..database import SessionLocal
from ..dependencies import (
    get_rate_limiter, templates,
    get_current_user_from_token,
)

router = APIRouter()


@router.get("/read/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_read(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        readingListItem = schemas.readingListItemCreate(book=bookId, user_id=user.id)
        crud.readBook(db, readingListItem)
        db.close()
        return RedirectResponse(url='/readingLists')
    if not user:
        return "You are not logged in. Login to modify your reading list."


@router.get("/unread/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_unread(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        crud.bookUnRead(db, bookId)
        db.close()
        return RedirectResponse(url='/readingLists')
    if not user:
        return "You are not logged in. Login to modify your reading list."


@router.get("/readingLists", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def reading_list(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        readingList = crud.readingList(db, user.id)
        books = []
        for i in readingList:
            books.append(crud.getBookById(db, i.book))
        db.close()
        context = {
            "books": books,
            "user": user,
            "request": request
        }
        return templates.TemplateResponse(request, "readinglist.html", context)
    if not user:
        return "You are not logged in. Login to see your reading list."


@router.get("/return/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_return(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        book = crud.getBookById(db, bookId)
        book = schemas.Book(id=bookId, title=book.title, author=book.author, summary=book.summary, genre=book.genre, library=book.library, shelf=book.shelf, collection=book.collection, notes=book.notes, ISBN=book.ISBN, owned=book.owned, ebook=book.ebook, customField1=book.customField1, customField2=book.customField2, withdrawn=False)
        crud.bookReturn(db, book)
        db.close()
        return RedirectResponse(url='/searchbooks')
    if not user:
        return "You are not logged in. Login to return books."


@router.get("/withdraw/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def book_withdraw(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        book = crud.getBookById(db, bookId)
        book = schemas.Book(id=bookId, title=book.title, author=book.author, summary=book.summary, genre=book.genre, library=book.library, shelf=book.shelf, collection=book.collection, notes=book.notes, ISBN=book.ISBN, owned=book.owned, ebook=book.ebook, withdrawnBy=user.username, customField1=book.customField1, customField2=book.customField2, withdrawn=True)
        crud.bookWithdraw(db, book)
        db.close()
        return RedirectResponse(url='/searchbooks')
    if not user:
        return "You are not logged in. Login to withdraw books."


@router.get("/withdrawn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def withdrawn_list(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        books = []
        withdrawnList = crud.browseWithdrawn(db)
        for i in withdrawnList:
            books.append(i)
        db.close()
        context = {
            "user": user,
            "books": books,
            "request": request
        }
        return templates.TemplateResponse(request, "withdrawn.html", context)
    if not user:
        return "You are not logged in. Login to see withdrawn books."


@router.get("/wishlist", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def wishlist(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        books = crud.browseWishlist(db)
        db.close()
        context = {
            "user": user,
            "books": books,
            "request": request
        }
        return templates.TemplateResponse(request, "wishlist.html", context)
    if not user:
        return "You are not logged in. Login to view books."
