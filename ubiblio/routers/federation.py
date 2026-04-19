from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
import json
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError

from .. import crud, schemas
from ..database import SessionLocal
from ..dependencies import (
    get_rate_limiter, templates,
    get_current_user_from_token, get_body,
)
from ..vars import VERIFY_KEY, SIGNING_KEY

router = APIRouter()


@router.get("/vkey", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def verify_key_endpoint(request: Request):
    try:
        return VERIFY_KEY
    except:
        return


@router.post("/signsearch", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
async def signsearch(body: bytes = Depends(get_body), user: schemas.User = Depends(get_current_user_from_token)):
    try:
        data = {}
        body = json.loads(body)
        body = json.dumps(body)
        bodyBytes = bytearray(body, "utf-8")
        data['signature'] = SigningKey.from_string(bytearray.fromhex(SIGNING_KEY), curve=SECP256k1).sign(bodyBytes).hex()
        data['message'] = json.loads(body)
        data['vkey'] = VERIFY_KEY
        return json.dumps(jsonable_encoder(data))
    except Exception as e:
        return e


@router.get("/fedsearch", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def fed_search_page(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        db = SessionLocal()
        vkeys = crud.getAllVkeys(db)
        context = {
            "user": user,
            "request": request,
            "vkeys": vkeys
        }
        return templates.TemplateResponse(request, "fedsearch.html", context)
    except:
        return "FAIL"


@router.post("/fedsearch", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def fed_search_books(body: bytes = Depends(get_body)):
    try:
        signedRequest = json.loads(body)
        db = SessionLocal()
        assert crud.haveKey(db, signedRequest["vkey"])
        sig = bytearray.fromhex(signedRequest["signature"])
        message = json.dumps(signedRequest["message"])
        bytesMessage = bytearray(message, "utf-8")
        assert VerifyingKey.from_string(bytearray.fromhex(signedRequest["vkey"]), curve=SECP256k1).verify(sig, bytesMessage)
        title = signedRequest["message"]["title"]
        author = signedRequest["message"]["author"]
        onlyEbooks = signedRequest["message"]["onlyEbooks"]
        noEbooks = signedRequest["message"]["noEbooks"]
        skip = signedRequest["message"]["skip"]
        db = SessionLocal()
        books = crud.searchBooks(db, str(title), str(author), int(skip), bool(onlyEbooks), bool(noEbooks))
        result = json.dumps(jsonable_encoder(books[0]))
        data = {}
        data['result'] = result
        data['count'] = books[1]
        db.close()
        return json.dumps(jsonable_encoder(data))
    except BadSignatureError:
        return "Signature verification failed"
    except AssertionError:
        return "This key is not authorized yet"
    finally:
        db.close()


@router.get("/fedBookDetails/{bookId}/{vkeyId}", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def get_fed_book_details(request: Request, bookId: int, vkeyId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        db = SessionLocal()
        vkey = crud.getVkeyById(db, vkeyId)
        context = {
            "user": user,
            "request": request,
            "vkey": vkey,
            "bookId": bookId
        }
        return templates.TemplateResponse(request, "fedBookDetails.html", context)
    except:
        return "FAIL"


@router.post("/fedBookDetails/", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def fed_book_details(body: bytes = Depends(get_body)):
    try:
        signedRequest = json.loads(body)
        db = SessionLocal()
        assert crud.haveKey(db, signedRequest["vkey"])
        sig = bytearray.fromhex(signedRequest["signature"])
        message = json.dumps(signedRequest["message"])
        bytesMessage = bytearray(message, "utf-8")
        assert VerifyingKey.from_string(bytearray.fromhex(signedRequest["vkey"]), curve=SECP256k1).verify(sig, bytesMessage)
        bookId = signedRequest["message"]["bookId"]
        db = SessionLocal()
        book = crud.getBookById(db, int(bookId))
        db.close()
        return json.dumps(jsonable_encoder(book))
    except BadSignatureError:
        return "Signature verification failed"
    except AssertionError:
        return "This key is not authorized yet"
    finally:
        db.close()


@router.get("/manageVkeys", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def manage_vkeys(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            vkeys = crud.getAllVkeys(db)
            print(vkeys)
            context = {
                "vkeys": vkeys,
                "user": user,
                "request": request
            }
            return templates.TemplateResponse(request, "vkeyManagement.html", context)
        else:
            return "Only an admin can manage verification keys."
    except Exception as e:
        print(e)
        return "Only an admin can manage verification keys."
    finally:
        db.close()


@router.get("/deleteVkey/{vkey}", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def delete_vkey(request: Request, vkey: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            vkeys = crud.deleteVkey(db, vkey)
            return RedirectResponse(url='/manageVkeys')
        else:
            return "Only an admin can delete verification keys."
    except Exception as e:
        return "Only an admin can delete verification keys."
    finally:
        db.close()


@router.get("/newVkey/", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def new_vkey_page(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            context = {
                "user": user,
                "request": request
            }
            return templates.TemplateResponse(request, "newVkey.html", context)
        else:
            return "Only an admin can add new verification keys."
    except Exception as e:
        print(e)
        return "Only an admin can add new verification keys."


@router.post("/addVkey", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def add_vkey(body: bytes = Depends(get_body), user: schemas.User = Depends(get_current_user_from_token)):
    if not user.isAdmin == True:
        return "You are not authorized to add validation keys. Only an admin can do this."
    body = json.loads(body)
    try:
        if body["url"][-1] != "/":
            body["url"] = body["url"] + "/"
        if len(body["vkey"]) == 128:
            db = SessionLocal()
            newVkey = schemas.vkeyBase(vkey=body["vkey"], url=body["url"])
            crud.addVkey(db, newVkey)
            return RedirectResponse(url='/manageVkeys/', status_code=status.HTTP_303_SEE_OTHER)
        else:
            return "FAIL"
            db.close()
    except Exception as e:
        print(e)
        return "Fail"


@router.post("/refreshVkey", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def refresh_vkey(body: bytes = Depends(get_body), user: schemas.User = Depends(get_current_user_from_token)):
    if not user.isAdmin == True:
        return "You are not authorized to refresh validation keys. Only an admin can do this."
    body = json.loads(body)
    try:
        if len(body["vkey"]) == 128:
            db = SessionLocal()
            vkey = crud.getVkeyById(db, body["id"])
            vkey.vkey = str(body["vkey"])
            crud.updateVkey(db, vkey)
            return RedirectResponse(url='/manageVkeys/', status_code=status.HTTP_303_SEE_OTHER)
        else:
            return "FAIL"
            db.close()
    except Exception as e:
        print(e)
        return "Fail"
