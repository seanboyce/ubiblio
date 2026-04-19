from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from .. import crud, schemas, database
from ..database import SessionLocal
from ..dependencies import (
    get_rate_limiter, templates, settings, console,
    login_for_access_token, LoginForm, newUserForm,
)
from ..vars import ADMIN_USERNAME, ADMIN_PASSWORD, CREATE_ADMIN_USER, CREATE_USER, USER_USERNAME, USER_PASSWORD

router = APIRouter()


@router.post("/auth/login", dependencies=[get_rate_limiter(times=1, seconds=2)], response_class=HTMLResponse)
async def login_post(request: Request):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            response = RedirectResponse("/", status.HTTP_303_SEE_OTHER)
            login_for_access_token(response=response, form_data=form)
            form.__dict__.update(msg="Login Successful!")
            console.log("[green]Login successful!!!!")
            return response
        except HTTPException:
            form.__dict__.update(msg="")
            form.__dict__.get("errors").append("Incorrect Email or Password")
            return templates.TemplateResponse(request, "login.html", form.__dict__)
    return templates.TemplateResponse(request, "login.html", form.__dict__)


@router.get("/auth/logout", response_class=HTMLResponse)
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(settings.COOKIE_NAME)
    return response


@router.get("/auth/login", response_class=HTMLResponse)
def login_get(request: Request):
    context = {
        "request": request,
    }
    return templates.TemplateResponse(request, "login.html", context)


@router.get("/auth/create/{accessCode}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def new_user_page(request: Request, accessCode: str):
    try:
        db = SessionLocal()
        if crud.codeValidate(db, accessCode) == True:
            context = {
                "accessCode": accessCode,
                "request": request
            }
            return templates.TemplateResponse(request, "createUser.html", context)
        else:
            return "Your access code is invalid or expired."
    except:
        return "An error has occurred."
    finally:
        db.close()


@router.post("/auth/create/", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def create_user_with_code(request: Request):
    try:
        form = newUserForm(request)
        await form.load_data()
        if await form.is_valid():
            db = SessionLocal()
            assert crud.get_user_by_username(db, form.username) == None
            user = schemas.UserCreate(
                username=form.username, password=form.password, isAdmin=False
            )
            success = crud.createWithCode(db, user, form.accessCode)
            if success == True:
                errors = ["Account created successfully! Please log in with your new account."]
                context = {
                    "user": user,
                    "request": request,
                    "errors": errors
                }
                return templates.TemplateResponse(request, "login.html", context)
            else:
                raise Exception("Failed to create account.")
        else:
            return "The form you submitted is not valid. Try your access link again, or contact the library admin."
    except AssertionError:
        errors = ["Username already exists, please choose another."]
        context = {
            "accessCode": form.accessCode,
            "request": request,
            "errors": errors
        }
        return templates.TemplateResponse(request, "createUser.html", context)
    except Exception as e:
        errors = [e]
        context = {
            "accessCode": form.accessCode,
            "request": request,
            "errors": errors
        }
        return templates.TemplateResponse(request, "createUser.html", context)


@router.get("/user-setup/")
async def create_user():
    if CREATE_ADMIN_USER or CREATE_USER:
        db = database.SessionLocal()
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
