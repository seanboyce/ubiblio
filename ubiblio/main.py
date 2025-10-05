import datetime as dt
from os import listdir, path, remove
from typing import Dict, List, Optional, Union
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status, File, UploadFile
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
from pydantic import BaseModel
from rich import inspect, print
from rich.console import Console
from . import crud, models, schemas,database
import secrets
from .database import SessionLocal, engine
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import json
from datetime import datetime
from isbnlib import *
from .vars import *
import sqlite3
import csv
import aiofiles
from PIL import Image
import uuid
import shutil

console = Console()
CHUNK_SIZE = 1024 * 1024 #for uploads

def get_rate_limiter(times: int, seconds: int):
    if USE_REDIS:
        return Depends(RateLimiter(times, seconds))
    else:
        return Depends(lambda: None)


# --------------------------------------------------------------------------
# Setup FastAPI
# --------------------------------------------------------------------------

## Authentication uses JWT, pretty much from the tutorial here: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/#hash-and-verify-the-passwords
##SECRET_KEY is a string containing hex characters (0-9,a-f) that is length 64 (so, 32 bytes). You need to fill this in before running. A good way to do it is just run 'openssl rand -hex 32' on your command line
##Default is to force new login every 120 minutes by expiring tokens, but you can set it to much longer if you want.

class Settings:
    SECRET_KEY = SECRET_KEY
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = TOKEN_TTL  # in mins
    COOKIE_NAME = "access_token"

# initialize tables on first start
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
favicon_path = 'favicon.ico'

# Connect to local Redis for rate-limiting function -- this is for some DDoS resistance so you don't have to use Cloudflare for every little thing.
@app.on_event("startup")
async def startup():
    if USE_REDIS:
        redis_connection = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        #If your redis install uses auth, use the line below instead of the line above, adding in your username/password
        #redis_connection = redis.from_url(REDIS_URL, username=None, password=None, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_connection)

language_templates = "templates/" + LANGUAGE
print(language_templates)
templates = Jinja2Templates(directory=language_templates)
app.mount("/static", StaticFiles(directory="static"), name="static")
settings = Settings()


############## Helper Functions

def get_user(username: str) -> schemas.User:
    db = database.SessionLocal()
    user = crud.get_user_by_username(db, username = username)
    db.close()
    if user:
        return user
    return None

# --------------------------------------------------------------------------
# Authentication logic
# --------------------------------------------------------------------------
class user_exists(Exception):
    def __init__(self, message='Username already exists, try another.'):
        # Call the base class constructor with the parameters it needs
        super(user_exists, self).__init__(message)

class OAuth2PasswordBearerWithCookie(OAuth2):
    """
    This class is taken directly from FastAPI:
    https://github.com/tiangolo/fastapi/blob/26f725d259c5dbe3654f221e608b14412c6b40da/fastapi/security/oauth2.py#L140-L171

    The only change made is that authentication is taken from a cookie
    instead of from the header!
    """
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        # IMPORTANT: this is the line that differs from FastAPI. Here we use
        # `request.cookies.get(settings.COOKIE_NAME)` instead of
        # `request.headers.get("Authorization")`
        authorization: str = request.cookies.get(settings.COOKIE_NAME)
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(status_code=302, detail="Not authorized", headers = {"Location": "/"})
            else:
                return None
        return param

def create_access_token(data: Dict) -> str:
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authenticate_user(username: str, plain_password: str) -> schemas.User:
    user = get_user(username)
    if not user:
        return False
    if not crypto.verify(plain_password, user.passhash):
        return False
    return user


def decode_token(token: str) -> schemas.User:
    credentials_exception = HTTPException(status_code=302, detail="Not authorized", headers = {"Location": "/"})
    token = token.removeprefix("Bearer").strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        print(e)
        raise credentials_exception

    user = get_user(username)
    return user

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")

def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> schemas.User:
    """
    Get the current user from the cookies in a request.

    Use this function when you want to lock down a route so that only
    authenticated users can see access the route.
    """
    user = decode_token(token)
    return user


def get_current_user_from_cookie(request: Request) -> schemas.User:
    """
    Get the current user from the cookies in a request.

    Use this function from inside other routes to get the current user. Good
    for views that should work for both logged in, and not logged in users.
    """
    token = request.cookies.get(settings.COOKIE_NAME)
    user = decode_token(token)
    return user

@app.post("token")
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Dict[str, str]:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=302, detail="Not authorized", headers = {"Location": "/"})
    access_token = create_access_token(data={"username": user.username})

    # Set an HttpOnly cookie in the response. `httponly=True` prevents
    # JavaScript from reading the cookie.
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=f"Bearer {access_token}",
        httponly=True
    )
    return {settings.COOKIE_NAME: access_token, "token_type": "bearer"}


#################### Authentication Endpoints

@app.post("/auth/login", dependencies=[get_rate_limiter(times=1, seconds=2)], response_class=HTMLResponse)
async def login_post(request: Request):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            response = RedirectResponse("/", status.HTTP_302_FOUND)
            login_for_access_token(response=response, form_data=form)
            form.__dict__.update(msg="Login Successful!")
            console.log("[green]Login successful!!!!")
            return response
        except HTTPException:
            form.__dict__.update(msg="")
            form.__dict__.get("errors").append("Incorrect Email or Password")
            return templates.TemplateResponse("login.html", form.__dict__)
    return templates.TemplateResponse("login.html", form.__dict__)


@app.get("/auth/logout", response_class=HTMLResponse)
def login_get():
    response = RedirectResponse(url="/")
    response.delete_cookie(settings.COOKIE_NAME)
    return response


# --------------------------------------------------------------------------
# Home Page
# --------------------------------------------------------------------------
@app.get("/", dependencies=[get_rate_limiter(times=3, seconds=1)], response_class=HTMLResponse)
def index(request: Request):
    try:
        user = get_current_user_from_cookie(request)
    except:
        user = None
    if not user:
        context = {
        "request": request
    }
        return templates.TemplateResponse("login.html", context)
    if user:
        databaseNotFirstVersion = crud.checkDB()
        if databaseNotFirstVersion == True:
            dbVersion = crud.getVersion()
            if dbVersion == "1.0.1":
                response = RedirectResponse(url='/searchbooks')
            else:
                response = RedirectResponse(url='/dbUpdateVersion')
        else:
            response = RedirectResponse(url='/dbUpdate')
        return response

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)
# --------------------------------------------------------------------------
# CRUD on Books
# --------------------------------------------------------------------------
@app.get("/add_book", dependencies=[get_rate_limiter(times=3, seconds=2)], response_class=HTMLResponse)
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
            return templates.TemplateResponse("newBook.html", context)
        if not user.isAdmin == True:
            return "You are not authorized to add books. Only an admin can do this."
    except Exception as e:
        print(e)
        return "An error has occured."


@app.post("/add_book", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def addBook_post(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if not user.isAdmin == True:
        return "You are not authorized to add books. Only an admin can do this."
    form = bookForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            db = SessionLocal()
            newBook = schemas.BookCreate(title=form.title, author=form.author, summary=form.summary, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN = form.ISBN, owned = form.owned, ebook = form.ebook, customField1=form.customField1, customField2=form.customField2, withdrawn=form.withdrawn)
            crud.createBook(db, newBook)
            books = crud.getBooks(db)
            db.close()
            context = {
        "books": books,
        "user": user,
        "request": request,
    }
            return templates.TemplateResponse("booksearch.html", context)
        except Exception as e:
            print(e)
            return "Fail"


@app.get("/delete_book/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def delete_book(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user.isAdmin == True:
        db = SessionLocal()
        crud.deleteBook(db,bookId)
        books = crud.getBooks(db)
        db.close()
        context = {
        "books": books,
        "user": user,
        "request": request
        }
        return templates.TemplateResponse("booksearch.html", context)
    if not user.isAdmin == True:
        return "You are not authorized to delete books. Only an admin can do this."

@app.get("/bookDetails/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def bookDetails(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        config = crud.getConfig(db)
        book = crud.getBookById(db,bookId)
        context = {
            "config":config,
            "book": book,
            "user": user,
            "request": request
            }
        if config.coverImages:
            images = crud.getImages(db, bookId)
            context["images"] = images  
        if book.ebook==True:
            ebookFiles = crud.getEbookFiles(db, bookId)
            context["ebookFiles"] = ebookFiles  
            db.close()
            return templates.TemplateResponse("ebookDetails.html", context)
        else:
            db.close()
            return templates.TemplateResponse("bookDetails.html", context)
    if not user:
        return "You are not logged in. Login to view books."

@app.post("/update_book/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def update_book(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if not user.isAdmin == True:
        return "You are not authorized to update books. Only an admin can do this."
    form = bookForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            db = SessionLocal()
            config = crud.getConfig(db)
            book = schemas.Book(id=bookId, title=form.title, author=form.author, summary=form.summary, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN = form.ISBN, owned = form.owned, ebook = form.ebook, customField1=form.customField1, customField2=form.customField2, withdrawn=form.withdrawn)
            crud.updateBook(db, book)
            book = crud.getBookById(db,bookId)
            db.close()
            context = {
            "config": config,
            "book": book,
            "user": user,
            "request": request
            }
            return RedirectResponse(url='/bookDetails/'+bookId, 
        status_code=status.HTTP_302_FOUND)
        except Exception as e:
            print(e)
            return "Fail"

@app.get("/update_book/{bookId}", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
def update_cust_form(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            config = crud.getConfig(db)
            book = crud.getBookById(db,bookId)
            db.close()
            context = {
            "config":config,
            "user": user,
            "book": book,
            "request": request
            }
            return templates.TemplateResponse("updateBook.html", context)
        if not user.isAdmin == True:
            return "You are not authorized to update books. Only an admin can do this."
    except Exception as e:
        print(e)
        return "An error has occured."

# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------
@app.get("/searchbooks", dependencies=[get_rate_limiter(times=4, seconds=2)], response_class=HTMLResponse)
def searchbookget(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    data=[]
    context = {
        "request": request,
        "user": user,
        "data": data
    }
    return templates.TemplateResponse("booksearch.html", context)

@app.post("/searchbooks", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def searchBooks(request: Request, user: schemas.User = Depends(get_current_user_from_token), title: str = "%", author: str= "%",skip: int = "%",onlyEbooks: bool = "%", noEbooks:  bool = "%"):
    try:
        db = SessionLocal()
        books = jsonable_encoder(crud.searchBooks(db, str(title),str(author), int(skip), bool(onlyEbooks), bool(noEbooks)))
        books = json.dumps(books)
        db.close()
        return books
    except Exception as e:
        db.close()
        return e
@app.post("/searchBooksByAuthor", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def searchbookAuthor(request: Request, user: schemas.User = Depends(get_current_user_from_token), author: str= "%",skip: int = 0, onlyEbooks: bool = "%", noEbooks:  bool = "%"):
    try:
        db = SessionLocal()
        books = jsonable_encoder(crud.searchBooksbyAuthor(db, str(author), int(skip), bool(onlyEbooks), bool(noEbooks)))
        books = json.dumps(books)
        db.close()
        return books
    except Exception as e:
        db.close()
        return "An error has occured."

@app.post("/searchBooksByTitle", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def searchbookTitle(request: Request, user: schemas.User = Depends(get_current_user_from_token), title: str = "%", skip: int = 0, onlyEbooks: bool = "%", noEbooks:  bool = "%"):
    try:
        db = SessionLocal()
        books = jsonable_encoder(crud.searchBooksbyTitle(db, str(title), int(skip), bool(onlyEbooks), bool(noEbooks)))
        books = json.dumps(books)
        db.close()
        return books
    except Exception as e:
        db.close()
        return "An error has occured."
# --------------------------------------------------------------------------
# ISBN autoadd
# --------------------------------------------------------------------------
def get_metadata(isbn: str, service: str):
    try:
        book = meta(isbn, service=service)
        if "Title" in book:
            return book
    except Exception as e:
        print(e)

    return None

@app.get("/isbn/{isbn}", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
def new_isbn(isbn, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            book = meta(isbn,service='goob') or meta(isbn,service="openl") or meta(isbn,service='wiki')
            if book is None:
                raise LookupError(f"Book with isbn {isbn} not found!")
            title = book["Title"]
            author = book["Authors"][0]
            try:
                summary = desc(isbn)
                summary = summary.replace('\n', ' ')
            except: summary=""
            addISBN = [0]
            book = schemas.BookCreate(title=title, author=author, summary=summary, ISBN=isbn)
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
            return templates.TemplateResponse("newBook.html", context)
        if not user.isAdmin == True:
            return "You are not authorized to update books. Only an admin can do this."
    except Exception as e:
        errors = ["ISBN not found -- try another."]
        context = {
        "errors": errors,
        "user": user,
        "request": request
    }
        return templates.TemplateResponse("addisbn.html", context)

@app.get("/addisbn", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
async def addIsbn(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user.isAdmin == True:
        context = {
        "user": user,
        "request": request
    }
        return templates.TemplateResponse("addisbn.html", context)
    if not user.isAdmin == True:
        return "You are not authorized to add books. Only an admin can do this."

@app.post("/addanotherisbn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def addAnotherIsbn(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user.isAdmin == True:
        #Add book
        form = bookForm(request)
        await form.load_data()
        if await form.is_valid():
            db = SessionLocal()
            newBook = schemas.BookCreate(title=form.title, author=form.author, summary=form.summary, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN = form.ISBN, owned = form.owned, ebook = form.ebook, customField1=form.customField1, customField2=form.customField2, withdrawn=form.withdrawn)
            crud.createBook(db, newBook)
            books = crud.getBooks(db)
            db.close()
            context = {
            "user": user,
        "request": request
    }
        return templates.TemplateResponse("addisbn.html", context)
    if not user.isAdmin == True:
        return "You are not authorized to add books. Only an admin can do this."
# --------------------------------------------------------------------------
# Reading Lists
# --------------------------------------------------------------------------

@app.get("/read/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def bookRead(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        readingListItem = schemas.readingListItemCreate(book=bookId, user_id=user.id)
        crud.readBook(db,readingListItem)
        db.close()
        return RedirectResponse(url='/readingLists')
    if not user:
        return "You are not logged in. Login to modify your reading list."

@app.get("/unread/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def bookUnRead(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        crud.bookUnRead(db,bookId)
        db.close()
        return RedirectResponse(url='/readingLists')
    if not user:
        return "You are not logged in. Login to modify your reading list."

@app.get("/readingLists", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def readList(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        readingList = crud.readingList(db,user.id)
        books = []
        for i in readingList:
            books.append(crud.getBookById(db,i.book))
        db.close()
        context = {
        "books": books,
        "user": user,
        "request": request
    }
        return templates.TemplateResponse("readinglist.html", context)
    if not user:
        return "You are not logged in. Login to see your reading list."
# --------------------------------------------------------------------------
# Withdraw / Return
# --------------------------------------------------------------------------

@app.get("/return/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def bookReturn(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        book = crud.getBookById(db, bookId)
        book = schemas.Book(id=bookId, title=book.title, author=book.author, summary=book.summary, genre=book.genre, library=book.library, shelf=book.shelf, collection=book.collection, notes=book.notes, ISBN = book.ISBN, owned = book.owned, ebook=book.ebook, customField1=book.customField1, customField2=book.customField2, withdrawn=False)
        crud.bookReturn(db,book)
        db.close()
        return RedirectResponse(url='/searchbooks')
    if not user:
        return "You are not logged in. Login to return books."

@app.get("/withdraw/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def bookWithdraw(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        book = crud.getBookById(db, bookId)
        book = schemas.Book(id=bookId, title=book.title, author=book.author, summary=book.summary, genre=book.genre, library=book.library, shelf=book.shelf, collection=book.collection, notes=book.notes, ISBN = book.ISBN, owned = book.owned, ebook=book.ebook, withdrawnBy = user.username, customField1=book.customField1, customField2=book.customField2, withdrawn=True)
        crud.bookWithdraw(db,book)
        db.close()
        return RedirectResponse(url='/searchbooks')
    if not user:
        return "You are not logged in. Login to withdraw books."

@app.get("/withdrawn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def wdList(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        books=[]
        withdrawnList = crud.browseWithdrawn(db)
        #Convert query to list, so jinjia2 can determine it's length (so it knows whether to return "no results found" or a table of results)
        for i in withdrawnList:
            books.append(i)
        db.close()
        context = {
        "user": user,
        "books": books,
        "request": request
    }
        return templates.TemplateResponse("withdrawn.html", context)
    if not user:
        return "You are not logged in. Login to see withdrawn books."




# --------------------------------------------------------------------------
# Database update / export / backup / restore
# --------------------------------------------------------------------------


@app.get("/dbUpdate", dependencies=[get_rate_limiter(times=1, seconds=2)], response_class=HTMLResponse)
async def updatePage(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
   context = {
        "user": user,
        "request": request,
    }
   return templates.TemplateResponse("updateAdvisory.html", context)

@app.get("/dbUpdateVersion", dependencies=[get_rate_limiter(times=1, seconds=2)], response_class=HTMLResponse)
async def updatePage(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
   context = {
        "user": user,
        "request": request,
    }
   return templates.TemplateResponse("updateVersion.html", context)

#This is the function for updating the oldest version of the app only. DB versioning is implemented after. 
@app.get("/updateDB", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def update(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            conn = sqlite3.connect(DB_LOCATION)
            date_time = datetime.now()
            date_time = date_time.strftime("%m_%d_%Y_%H_%M_%S")
            with open('export/preUpdateExport' + date_time + '.sql', 'w') as f:
               for line in conn.iterdump():
                   f.write('%s\n' % line)
            conn.close()
            crud.updateDB()
        return RedirectResponse(url='/searchbooks')
    except:
           return "Only an admin can export the database."
            
#This is the function for DB updates except in the very first version of the uBiblio.
@app.get("/updateDBVersion", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def update(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
#    try:
        if user.isAdmin == True:
            dbVersion = crud.getVersion()
            conn = sqlite3.connect(DB_LOCATION)
            date_time = datetime.now()
            date_time = date_time.strftime("%m_%d_%Y_%H_%M_%S")
            with open('export/preUpdateExport' + date_time + '.sql', 'w') as f:
               for line in conn.iterdump():
                   f.write('%s\n' % line)
            conn.close()
            db = SessionLocal()
            crud.updateDBVersion(db, dbVersion)
            db.close()
        return RedirectResponse(url='/searchbooks')
#    except:
#           return "Only an admin can export the database." 


@app.get("/export", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def export(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            conn = sqlite3.connect(DB_LOCATION)
            date_time = datetime.now()
            date_time = date_time.strftime("%m_%d_%Y_%H_%M_%S")
            with open('export/DBExport' + date_time + '.sql', 'w') as f:
                for line in conn.iterdump():
                    f.write('%s\n' % line)
            conn.close()
            filename = "allFiles" + date_time
            shutil.make_archive(filename, 'zip', "static")
            shutil.move(filename + ".zip", "export/" + filename + ".zip")
        return RedirectResponse(url='/backups')
    except:
           return "Only an admin can export the database." 

@app.get("/exportcsv", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def exportcsv(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            conn = sqlite3.connect(DB_LOCATION)
            cur = conn.cursor()
            bookData = cur.execute("SELECT * FROM books").fetchall()
            date_time = datetime.now()
            date_time = date_time.strftime("%m_%d_%Y_%H_%M_%S")
            with open('export/csvBookExport' + date_time + '.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerows(bookData)   
            f.close()
            conn.close()
        return RedirectResponse(url='/backups')
    except:
           return "Only an admin can export the database." 

           
@app.get("/backups", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def backups(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            possibleBackups = listdir('export')
            backups = []
            bookExports = []
            fileExports = []
            for i in possibleBackups:
                if i.endswith('.sql'):
                    backups.append(i)     
                elif i.endswith('.csv'):
                    bookExports.append(i)
                elif i.endswith('.zip'):
                    fileExports.append(i)
            context = {
        "request": request,
        "user": user,
        "backups":backups,
        "bookExports":bookExports,
        "fileExports":fileExports,
    }
        return templates.TemplateResponse("backups.html", context)
    except:
           return "Only an admin can view database backups." 

@app.get("/restoreBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def restoreDB(filename,request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
             path = ('export/' + filename)
             if os.path.isfile(path):
                 crud.wipeAndRestore(path)
                 context = {
        "request": request,
    }
                 response = RedirectResponse(url='/')
                 return response
    except Exception as e:
           print(e)

@app.get("/deleteBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def deleteBk(filename,request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
             path = ('export/' + filename)
             if os.path.isfile(path):
                 os.remove(path)
                 context = {
        "request": request,
    }
                 return RedirectResponse(url='/backups')
                 return response
    except:
           return "Delete backup failed. It's likely you are not an admin user or there's a file permissions issue." 


@app.get("/addByCSV/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def addCSV(filename,request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
             path = ('export/' + filename)
             if os.path.isfile(path):
                 crud.addCSV(path)
                 context = {
        "request": request,
    }
                 response = RedirectResponse(url='/searchbooks')
                 return response
    except:
           return "Error adding books -- check the search page to see what was added." 
 
@app.get("/downloadBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def downloadBk(filename,request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            path = ('export/' + filename)
            return FileResponse(path, media_type='application/octet-stream',filename=filename)
    except:
           return "Only admins can download backups." 


@app.post("/uploadBackup/")
async def uploadfile(file: UploadFile, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            filename_base = str(os.path.basename(file.filename))
            db = SessionLocal()
            extension = file.filename[-4:].lower()
            if (extension == ".sql") or (extension == ".csv") or (extension == ".zip"):
                filepath = os.path.join('./export/', str(filename_base))
                async with aiofiles.open(filepath, 'wb') as f:
                    while chunk := await file.read(CHUNK_SIZE):
                        await f.write(chunk)   
                db.close()
                response = RedirectResponse("/backups", status.HTTP_302_FOUND)
                return response
            if not (extension == ".sql") or (extension ==".csv"):
                return "Not a valid backup"
    except Exception as e:
        return {"message": e.args}

@app.get("/fileBackup", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def fileBackup(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            date_time = datetime.now()
            date_time = date_time.strftime("%m_%d_%Y_%H_%M_%S")
            filename = "allFiles" + date_time
            shutil.make_archive(filename, 'zip', "static")
            shutil.move(filename + ".zip", "export/" + filename + ".zip")
        return RedirectResponse(url='/backups')
    except:
           return "Only an admin can backup all stored files."  

@app.get("/restoreFileBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def restoreFiles(filename, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            shutil.unpack_archive("export/" + filename, "static", "zip") 
        return RedirectResponse(url='/')
    except:
           return "Only an admin can restore files."  
# --------------------------------------------------------------------------
# Library Configuration
# --------------------------------------------------------------------------            

@app.get("/config", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def config(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            config = crud.getConfig(db)
            db.close()
            context = {
            "user": user,
        "request": request,
        "config":config,
    }
        return templates.TemplateResponse("config.html", context)
    except:
           return "Only an admin can edit the library configuration."    
   
@app.post("/config", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def updateConfig(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            form = configForm(request)
            await form.load_data()
            if await form.is_valid():
                    db = SessionLocal()
                    config = schemas.config(id = 1, version=form.version, coverImages=form.coverImages, customFieldName1=form.customFieldName1, customFieldName2=form.customFieldName2, genres=form.genres)
                    crud.updateConfig(db, config)
                    config = crud.getConfig(db)
                    db.close()
                    context = {
                    "user": user,
                    "config": config,
                    "request": request,
                     }
                    return templates.TemplateResponse("config.html", context)
    except Exception as e:
        return "Only an admin can edit the library configuration."
                      
# --------------------------------------------------------------------------
# Browse by Genre
# --------------------------------------------------------------------------

@app.get("/booksByGenre/{genre}", dependencies=[get_rate_limiter(times=12, seconds=2)], response_class=HTMLResponse)
async def bookDetails(genre, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        books = crud.browseBooksByGenre(db,genre)
        db.close()
        context = {
        "user": user,
        "books": books,
        "request": request
    }
        return templates.TemplateResponse("booksByGenre.html", context)
    if not user:
        return "You are not logged in. Login to view books."

@app.get("/genre/", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def bookGenres(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        genres = crud.getGenres(db)
        db.close()
        context = {
        "user": user,
        "genres": genres,
        "request": request
    }
        return templates.TemplateResponse("genres.html", context)
    if not user:
        return "You are not logged in. Login to view books."


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------

@app.post("/upload/{bookId}")
async def uploadfile(file: UploadFile, bookId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            filename_base = str(os.path.basename(file.filename))
            db = SessionLocal()
            extension = file.filename[-4:]
            if (extension == ".jpg") or (extension =="jpeg") or (extension == ".JPG") or (extension == ".JPEG"):
                unique_id = str(uuid.uuid4())
                dbpath = str(bookId) + "_" + unique_id
                basepath = os.path.join('./static/bookImages/', str(bookId) + "_" + unique_id)
                thumbpath = basepath + "_thumbnail" + ".jpg"
                filepath = basepath + ".jpg"
                async with aiofiles.open(filepath, 'wb') as f:
                    while chunk := await file.read(CHUNK_SIZE):
                        await f.write(chunk)   
                    #once we have the full file, generate a thumbnail
                    im = Image.open(filepath)
                    im.thumbnail((300, 300), resample = Image.BOX )
                    im.save(thumbpath, format='JPEG', quality=65)
                    #finally, add to db only if all suceeds
                    newImage = schemas.bookImageBase(bookId = bookId, filename = dbpath)
                    crud.addImage(db,newImage)  
                    db.close()
            return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_302_FOUND) 
        if not (extension == ".jpg") or (extension =="jpeg"):
            db.close()
            return "Not a valid jpg image"
    except Exception as e:
        return {"message": e.args}

        
@app.post("/getImages/{bookId}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
def getImages(request: Request, bookId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        db = SessionLocal()
        images = crud.getImages(db, bookId)
        return images
    except Exception as e:
        print(e)
        return "An error has occured."
    finally:
        db.close()

@app.post("/deleteImage/{imageId}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
def deleteImages(request: Request, imageId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            bookId,dbpath = crud.deleteImage(db, imageId)
            db.close()
            jpgPath = os.path.join('./static/bookImages/', str(dbpath) + ".jpg")
            thumbPath = os.path.join('./static/bookImages/', str(dbpath) + "_thumbnail.jpg")
            os.remove(thumbPath)
            os.remove(jpgPath)
            return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_302_FOUND) 
    except Exception as e:
        db.close()
        print(e)
        #just return the page if it errors out. This can happen if the file link in the DB is broken. It will remove the DB entry, then fail to find and delete the file, which is not a disaster.
        return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_302_FOUND)

# --------------------------------------------------------------------------
# E-book handling
# --------------------------------------------------------------------------
@app.get("/downloadEbook/{filename}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
def getImages(request: Request, filename: str, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user:
            path = ('static/eBooks/' + filename)
            return FileResponse(path, media_type='application/octet-stream',filename=filename)
    except:
           return "Only admins can download backups." 


@app.get("/deleteEbook/{ebookId}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
def getImages(request: Request, ebookId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            bookId,dbpath = crud.deleteEbook(db, ebookId)
            db.close()
            ebookPath = os.path.join('./static/eBooks/', str(dbpath))
            try:
                os.remove(ebookPath)
            except:
                print("Tried to delete an ebook file that doesn't exist, removing DB entry")
            return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_302_FOUND) 
    except Exception as e:
        db.close()
        print(e)
        return "An error has occured."

@app.post("/uploadEbook/{bookId}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
async def uploadEbook(file: UploadFile, request: Request, bookId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            filename = str(os.path.basename(file.filename))
            filename, extension = os.path.splitext(filename)
            db = SessionLocal()
            book = crud.getBookById(db, bookId)
            title = (book.title[:26]) if len(book.title) > 26 else book.title
            #Includes title, so full uuid is cumbersome. Just grab a couple of characters. 
            unique_id = (str(uuid.uuid4()))[0:5]
            dbpath = str(title) + "_" + unique_id + extension
            filepath = os.path.join('./static/eBooks/', dbpath)
            async with aiofiles.open(filepath, 'wb') as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)   
                #finally, add to db only if all suceeds
                newEbook = schemas.ebookBase(bookId = bookId, filename = dbpath)
                crud.addEbook(db,newEbook)  
            db.close()
            return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_302_FOUND) 
    except Exception as e:
        return {"message": e.args}

# --------------------------------------------------------------------------
# Wishlist (of books)
# --------------------------------------------------------------------------

@app.get("/wishlist", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
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
        return templates.TemplateResponse("wishlist.html", context)
    if not user:
        return "You are not logged in. Login to view books."


# --------------------------------------------------------------------------
# Login - GET
# --------------------------------------------------------------------------
@app.get("/auth/login", response_class=HTMLResponse)
def login_get(request: Request):
    context = {
        "request": request,
    }
    return templates.TemplateResponse("login.html", context)


# --------------------------------------------------------------------------
# Login - FORMS
# --------------------------------------------------------------------------
class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

    async def is_valid(self):
        if not self.username:
            self.errors.append("Please enter your username")
        if not self.password or not len(self.password) >= 3:
            self.errors.append("A valid password is required")
        if not self.errors:
            return True
        return False

class bookForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.title: str
        self.author: Optional[str] = None
        self.summary: Optional[str] = None
        self.genre: Optional[str] = None
        self.library: Optional[str] = None
        self.shelf: Optional[str] = None
        self.collection: Optional[str] = None
        self.ISBN: Optional[str] = None
        self.notes: Optional[str] = None
        self.owned: Optional[bool] = None
        self.withdrawn: Optional[bool] = None
        self.ebook: Optional[bool] = None
        self.customField1: Optional[str] = None
        self.customField2: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.title = form.get("title")
        self.author = form.get("author")
        self.summary = form.get("summary")
        self.genre = form.get("genre")
        self.library = form.get("library")
        self.shelf = form.get("shelf")
        self.collection = form.get("collection")
        self.ISBN = form.get("ISBN")
        self.notes = form.get("notes")
        self.owned = form.get("owned")
        self.withdrawn = form.get("withdrawn")
        self.ebook = form.get("ebook")
        self.customField1 = form.get("customField1")
        self.customField2 = form.get("customField2")

    async def is_valid(self):
        if not self.title:
            self.errors.append("At least a title is required to create a book.")
        if not self.errors:
            return True
        return False


class configForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.version: Optional[str] = None
        self.coverImages: Optional[bool] = None
        self.customFieldName1: Optional[str] = None
        self.customFieldName2: Optional[str] = None
        self.genres: str = ""

    async def load_data(self):
        form = await self.request.form()
        self.version = form.get("version")
        self.coverImages = form.get("coverImages")
        self.customFieldName1 = form.get("customFieldName1")
        self.customFieldName2 = form.get("customFieldName2")
        self.genres = form.get("genres") or ",".join(schemas.DEFAULT_GENRES)

    async def is_valid(self):
        if not self.version:
            self.errors.append("Database version is required so as not to break the DB")
        if not self.version:
            self.errors.append("Enable Cover Images must be either True or False")
        if not self.errors:
            return True
        return False

# Create user from environment variables
@app.get("/user-setup/")
async def create_user():
    if CREATE_ADMIN_USER or CREATE_USER:
        db = database.SessionLocal()
        #If creating a new user, also create a valid initial config if one does not already exist
        crud.initConfig(db)
        if CREATE_ADMIN_USER:
            try:
                admin_user = schemas.UserCreate(
                    username=ADMIN_USERNAME, password=ADMIN_PASSWORD, isAdmin=True
                )
                crud.create_user(db, admin_user)
            except:
                print(f"Could not create admin user: {ADMIN_USERNAME}")

        if CREATE_USER:
            try:
                user = schemas.UserCreate(
                    username=USER_USERNAME, password=USER_PASSWORD, isAdmin=False
                )
                crud.create_user(db, user)
            except:
                print(f"Could not create user: {USER_USERNAME}")

        db.close()
    return RedirectResponse(url='/auth/login')
