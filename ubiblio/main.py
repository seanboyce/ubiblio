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
        await FastAPILimiter.init(redis_connection)


templates = Jinja2Templates(directory="templates")
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
        response = RedirectResponse(url='/searchbooks')
        return response

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)
# --------------------------------------------------------------------------
# CRUD on Books
# --------------------------------------------------------------------------
@app.get("/add_book", dependencies=[get_rate_limiter(times=3, seconds=2)], response_class=HTMLResponse)
def add_book_form(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    context = {
        "request": request,
    }
    try:
        if user.isAdmin == True:
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
            newBook = schemas.BookCreate(title=form.title, author=form.author, summary=form.summary, coverImage=form.coverImage, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN = form.ISBN, owned = form.owned, withdrawn=form.withdrawn)
            crud.createBook(db, newBook)
            books = crud.getBooks(db)
            db.close()
            context = {
        "books": books,
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
        "request": request
    }
        return templates.TemplateResponse("booksearch.html", context)
    if not user.isAdmin == True:
        return "You are not authorized to delete books. Only an admin can do this."

@app.get("/bookDetails/{bookId}", dependencies=[get_rate_limiter(times=1, seconds=1)], response_class=HTMLResponse)
async def bookDetails(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        book = crud.getBookById(db,bookId)
        db.close()
        context = {
        "book": book,
        "request": request
    }
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
            book = schemas.Book(id=bookId, title=form.title, author=form.author, summary=form.summary, coverImage=form.coverImage, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN = form.ISBN, owned = form.owned, withdrawn=form.withdrawn)
            crud.updateBook(db, book)
            book = crud.getBookById(db,bookId)
            db.close()
            context = {
        "book": book,
        "request": request
    }
            return templates.TemplateResponse("updateBook.html", context)
        except Exception as e:
            print(e)
            return "Fail"

@app.get("/update_book/{bookId}", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
def update_cust_form(bookId, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            book = crud.getBookById(db,bookId)
            db.close()
            context = {
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
def searchCust(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    data=[]
    context = {
        "request": request,
        "data": data
    }
    return templates.TemplateResponse("booksearch.html", context)

@app.post("/searchbooks", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def searchCust(request: Request, user: schemas.User = Depends(get_current_user_from_token), title: str = "%", author: str= "%",skip: int = 0):
    try:
        db = SessionLocal()
        books = jsonable_encoder(crud.searchBooks(db, str(title),str(author), int(skip)))
        books = json.dumps(books)
        db.close()
        return books
    except Exception as e:
        db.close()
        return "An error has occured."
@app.post("/searchBooksByAuthor", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def searchbookAuthor(request: Request, user: schemas.User = Depends(get_current_user_from_token), author: str= "%",skip: int = 0):
    try:
        db = SessionLocal()
        books = jsonable_encoder(crud.searchBooksbyAuthor(db, str(author), int(skip)))
        books = json.dumps(books)
        db.close()
        return books
    except Exception as e:
        db.close()
        return "An error has occured."

@app.post("/searchBooksByTitle", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def searchbookTitle(request: Request, user: schemas.User = Depends(get_current_user_from_token), title: str = "%", skip: int = 0):
    try:
        db = SessionLocal()
        books = jsonable_encoder(crud.searchBooksbyTitle(db, str(title), int(skip)))
        books = json.dumps(books)
        db.close()
        return books
    except Exception as e:
        db.close()
        return "An error has occured."
# --------------------------------------------------------------------------
# ISBN autoadd
# --------------------------------------------------------------------------
@app.get("/isbn/{isbn}", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
def new_isbn(isbn, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            book = meta(isbn)
            title = book["Title"]
            author = book["Authors"][0]
            try:
                summary = desc(isbn)
                summary = summary.replace('\n', ' ')
            except: summary=""
            addISBN = [0]
            book = schemas.BookCreate(title=title, author=author, summary=summary, ISBN=isbn)
            context = {
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
        "request": request
    }
        return templates.TemplateResponse("addisbn.html", context)

@app.get("/addisbn", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
async def addIsbn(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user.isAdmin == True:
        context = {
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
            newBook = schemas.BookCreate(title=form.title, author=form.author, summary=form.summary, coverImage=form.coverImage, genre=form.genre, library=form.library, shelf=form.shelf, collection=form.collection, notes=form.notes, ISBN = form.ISBN, owned = form.owned, withdrawn=form.withdrawn)
            crud.createBook(db, newBook)
            books = crud.getBooks(db)
            db.close()
            context = {
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
        book = schemas.Book(id=bookId, title=book.title, author=book.author, summary=book.summary, coverImage=book.coverImage, genre=book.genre, library=book.library, shelf=book.shelf, collection=book.collection, notes=book.notes, ISBN = book.ISBN, owned = book.owned, withdrawn=False)
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
        book = schemas.Book(id=bookId, title=book.title, author=book.author, summary=book.summary, coverImage=book.coverImage, genre=book.genre, library=book.library, shelf=book.shelf, collection=book.collection, notes=book.notes, ISBN = book.ISBN, owned = book.owned, withdrawn=True)
        crud.bookWithdraw(db,book)
        db.close()
        return RedirectResponse(url='/searchbooks')
    if not user:
        return "You are not logged in. Login to withdraw books."

@app.get("/withdrawn", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def wdList(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if user:
        db = SessionLocal()
        books = crud.browseWithdrawn(db)
        db.close()
        context = {
        "books": books,
        "request": request
    }
        return templates.TemplateResponse("readinglist.html", context)
    if not user:
        return "You are not logged in. Login to see withdrawn books."




# --------------------------------------------------------------------------
# Database update / export / backup / restore
# --------------------------------------------------------------------------

@app.get("/updateDB", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def update(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
#    try:
        if user.isAdmin == True:
            crud.updateDB()
        return RedirectResponse(url='/backups')
#    except:
#           return "Only an admin can export the database." 


@app.get("/export", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def export(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            con = sqlite3.connect('sql_app.db')
            date_time = datetime.now()
            date_time = date_time.strftime("%m_%d_%Y_%H_%M_%S")
            with open('export/csvBookExport' + date_time + '.sql', 'w') as f:
                for line in con.iterdump():
                    f.write('%s\n' % line)
        return RedirectResponse(url='/backups')
    except:
           return "Only an admin can export the database." 

@app.get("/exportcsv", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def exportcsv(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            conn = sqlite3.connect('sql_app.db')
            cur = conn.cursor()
            bookData = cur.execute("SELECT * FROM books").fetchall()
            date_time = datetime.now()
            date_time = date_time.strftime("%m_%d_%Y_%H_%M_%S")
            with open('export/csvBookExport' + date_time + '.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerows(bookData)   
            f.close()
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
            for i in possibleBackups:
                if i.endswith('.sql'):
                    backups.append(i)     
                elif i.endswith('.csv'):
                    bookExports.append(i)
            context = {
        "request": request,
        "backups":backups,
        "bookExports":bookExports,
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
                 response = RedirectResponse(url='/searchbooks')
                 return response
    except:
           return "Restore failed. No changes made to database." 

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
            extension = file.filename[-4:]
            if (extension == ".sql") or (extension ==".SQL") or (extension == ".csv") or (extension == ".CSV"):
                filepath = os.path.join('./export/', str(filename_base))
                async with aiofiles.open(filepath, 'wb') as f:
                    while chunk := await file.read(CHUNK_SIZE):
                        await f.write(chunk)   
                response = RedirectResponse("/backups", status.HTTP_302_FOUND)
                return response
            if not (extension == ".sql") or (extension ==".csv"):
                return "Not a valid backup"
    except Exception as e:
        return {"message": e.args}

 
            

           
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
        "books": books,
        ##"images": images,
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
        "genres": genres,
        "request": request
    }
        return templates.TemplateResponse("genres.html", context)
    if not user:
        return "You are not logged in. Login to view books."
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
        self.title: Optional[str] = None
        self.author: Optional[str] = None
        self.summary: Optional[str] = None
        self.coverImage: Optional[str] = None
        self.genre: Optional[str] = None
        self.library: Optional[str] = None
        self.shelf: Optional[str] = None
        self.collection: Optional[str] = None
        self.ISBN: Optional[str] = None
        self.notes: Optional[str] = None
        self.owned: Optional[bool] = None
        self.withdrawn: Optional[bool] = None

    async def load_data(self):
        form = await self.request.form()
        self.title = form.get("title")
        self.author = form.get("author")
        self.summary = form.get("summary")
        self.coverImage = form.get("coverImage")
        self.genre = form.get("genre")
        self.library = form.get("library")
        self.shelf = form.get("shelf")
        self.collection = form.get("collection")
        self.ISBN = form.get("ISBN")
        self.notes = form.get("notes")
        self.owned = form.get("owned")
        self.withdrawn = form.get("withdrawn")

    async def is_valid(self):
        if not self.title:
            self.errors.append("At least a title is required to create a book.")
        if not self.errors:
            return True
        return False


# Create user from environment variables
@app.get("/user-setup/")
async def create_user():
    if CREATE_ADMIN_USER or CREATE_USER:
        db = database.SessionLocal()

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
