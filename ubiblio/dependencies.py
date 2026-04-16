import datetime as dt
from typing import Dict, List, Optional
from fastapi import Depends, HTTPException, Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
from rich import print
from rich.console import Console
from fastapi_limiter.depends import RateLimiter

from . import crud, schemas, database
from .vars import SECRET_KEY, TOKEN_TTL, USE_REDIS, LANGUAGE

console = Console()
CHUNK_SIZE = 1024 * 1024

# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------
class Settings:
    SECRET_KEY = SECRET_KEY
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = TOKEN_TTL
    COOKIE_NAME = "access_token"

settings = Settings()

language_templates = "templates/" + LANGUAGE
print(language_templates)
templates = Jinja2Templates(directory=language_templates)


def get_rate_limiter(times: int, seconds: int):
    if USE_REDIS:
        return Depends(RateLimiter(times, seconds))
    else:
        return Depends(lambda: None)


# --------------------------------------------------------------------------
# Authentication logic
# --------------------------------------------------------------------------
class user_exists(Exception):
    def __init__(self, message='Username already exists, try another.'):
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
        authorization: str = request.cookies.get(settings.COOKIE_NAME)
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(status_code=302, detail="Not authorized", headers={"Location": "/"})
            else:
                return None
        return param


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")


def get_user(username: str) -> schemas.User:
    db = database.SessionLocal()
    user = crud.get_user_by_username(db, username=username)
    db.close()
    if user:
        return user
    return None


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
    credentials_exception = HTTPException(status_code=302, detail="Not authorized", headers={"Location": "/"})
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


def login_for_access_token(response, form_data):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=302, detail="Not authorized", headers={"Location": "/"})
    access_token = create_access_token(data={"username": user.username})
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=f"Bearer {access_token}",
        httponly=True
    )
    return {settings.COOKIE_NAME: access_token, "token_type": "bearer"}


async def get_body(request: Request):
    return await request.body()


# --------------------------------------------------------------------------
# Form classes
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


class newUserForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.accessCode: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")
        self.accessCode = form.get("accessCode")

    async def is_valid(self):
        if not self.username:
            self.errors.append("Please enter your username")
        if not self.password or not len(self.password) >= 3:
            self.errors.append("A valid password over 3 characters is required")
        if not self.accessCode:
            self.errors.append("Something went wrong with your access link. Reload this page, or contact your library admin.")
        if not self.errors:
            return True
        return False


class newVkeyForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.url: str
        self.vkey: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.url = form.get("url")
        self.vkey = form.get("vkey")

    async def is_valid(self):
        if not self.url:
            self.errors.append("Validation keys require a URL to tie them to")
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
