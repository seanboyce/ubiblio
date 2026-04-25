import datetime as dt
from typing import Annotated, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
from rich import print

from .. import crud, database, schemas
from .settings import settings


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
        flows = OAuthFlowsModel(
            password={"tokenUrl": tokenUrl, "scopes": scopes})
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
                raise HTTPException(
                    status_code=302, detail="Not authorized", headers={"Location": "/"})
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
    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
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
    credentials_exception = HTTPException(
        status_code=302, detail="Not authorized", headers={"Location": "/"})
    token = token.removeprefix("Bearer").strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
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
        raise HTTPException(
            status_code=302, detail="Not authorized", headers={"Location": "/"})
    access_token = create_access_token(data={"username": user.username})
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=f"Bearer {access_token}",
        httponly=True
    )
    return {settings.COOKIE_NAME: access_token, "token_type": "bearer"}


current_user = Annotated[schemas.User, Depends(get_current_user_from_token)]


def get_admin_user(user: current_user):
    if not user.isAdmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to add books. Only an admin can do this."
        )
    return user


admin_user = Annotated[schemas.User, Depends(get_admin_user)]
