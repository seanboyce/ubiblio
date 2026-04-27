import json
from typing import final

from ecdsa import BadSignatureError, SECP256k1, SigningKey, VerifyingKey
from fastapi import APIRouter, Depends, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import crud, schemas
from ..database import SessionLocal
from ..dependencies import (
    admin_user,
    current_user,
    get_body,
    get_rate_limiter,
    templates,
)
from ..vars import SIGNING_KEY, VERIFY_KEY

router = APIRouter()


@router.get("/vkey", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def verify_key_endpoint(request: Request):
    try:
        return VERIFY_KEY
    except:
        return


@router.post("/signsearch", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
async def signsearch(user: current_user, body: bytes = Depends(get_body)):
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
async def fed_search_page(request: Request, user: current_user):
    db = SessionLocal()
    try:
        vkeys = crud.getAllVkeys(db)
        context = {
            "user": user,
            "request": request,
            "vkeys": vkeys
        }
        return templates.TemplateResponse(request, "fedsearch.html", context)
    except:
        return "FAIL"
    finally:
        db.close()


@router.post("/fedsearch", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def fed_search_books(body: bytes = Depends(get_body)):
    db = SessionLocal()
    try:
        signedRequest = json.loads(body)
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
        books = crud.searchBooks(db, str(title), str(author), int(skip), bool(onlyEbooks), bool(noEbooks))
        result = json.dumps(jsonable_encoder(books[0]))
        data = {}
        data['result'] = result
        data['count'] = books[1]
        return json.dumps(jsonable_encoder(data))
    except BadSignatureError:
        return "Signature verification failed"
    except AssertionError:
        return "This key is not authorized yet"
    finally:
        db.close()


@router.get("/fedBookDetails/{bookId}/{vkeyId}", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def get_fed_book_details(request: Request, bookId: int, vkeyId: int, user: current_user):
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@router.post("/fedBookDetails/", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def fed_book_details(body: bytes = Depends(get_body)):
    db = SessionLocal()
    try:
        signedRequest = json.loads(body)
        assert crud.haveKey(db, signedRequest["vkey"])
        sig = bytearray.fromhex(signedRequest["signature"])
        message = json.dumps(signedRequest["message"])
        bytesMessage = bytearray(message, "utf-8")
        assert VerifyingKey.from_string(bytearray.fromhex(signedRequest["vkey"]), curve=SECP256k1).verify(sig, bytesMessage)
        bookId = signedRequest["message"]["bookId"]
        book = crud.getBookById(db, int(bookId))
        return json.dumps(jsonable_encoder(book))
    except BadSignatureError:
        return "Signature verification failed"
    except AssertionError:
        return "This key is not authorized yet"
    finally:
        db.close()


@router.get("/manageVkeys", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def manage_vkeys(request: Request, user: admin_user):
    db = SessionLocal()
    try:
        vkeys = crud.getAllVkeys(db)
        context = {
            "vkeys": vkeys,
            "user": user,
            "request": request,
        }
        return templates.TemplateResponse(request, "vkeyManagement.html", context)
    except Exception as e:
        print(e)
        return "Could not load verification keys."
    finally:
        db.close()


@router.get("/deleteVkey/{vkey}", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def delete_vkey(request: Request, vkey: int, user: admin_user):
    db = SessionLocal()
    try:
        crud.deleteVkey(db, vkey)
        return RedirectResponse(url='/manageVkeys')
    except Exception as e:
        print(e)
        return "Could not delete verification key."
    finally:
        db.close()


@router.get("/newVkey/", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def new_vkey_page(request: Request, user: admin_user):
    context = {
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse(request, "newVkey.html", context)


@router.post("/addVkey", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def add_vkey(user: admin_user, body: bytes = Depends(get_body)):
    body = json.loads(body)
    db = SessionLocal()
    try:
        if not body["url"].endswith("/"):
            body["url"] = body["url"] + "/"
        if len(body["vkey"]) != 128:
            return "FAIL"
        newVkey = schemas.vkeyBase(vkey=body["vkey"], url=body["url"])
        crud.addVkey(db, newVkey)
        return RedirectResponse(url='/manageVkeys/', status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        print(e)
        return "Fail"
    finally:
        db.close()


@router.post("/refreshVkey", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def refresh_vkey(user: admin_user, body: bytes = Depends(get_body)):
    body = json.loads(body)
    db = SessionLocal()
    try:
        if len(body["vkey"]) != 128:
            return "FAIL"
        vkey = crud.getVkeyById(db, body["id"])
        vkey.vkey = str(body["vkey"])
        crud.updateVkey(db, vkey)
        return RedirectResponse(url='/manageVkeys/', status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        print(e)
        return "Fail"
    finally:
        db.close()
