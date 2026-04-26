import os
import uuid

from PIL import Image
import aiofiles
from fastapi import APIRouter, Depends, Request, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from .. import crud, schemas
from ..database import SessionLocal
from ..dependencies import (
    CHUNK_SIZE,
    admin_user,
    current_user,
    get_current_user_from_token,
    get_rate_limiter,
)

router = APIRouter()


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------
@router.post("/upload/{bookId}")
async def upload_image(file: UploadFile, bookId: int, user: admin_user):
    try:
        db = SessionLocal()
        extension = file.filename[-4:]
        if (extension == ".jpg") or (extension == "jpeg") or (extension == ".JPG") or (extension == ".JPEG"):
            unique_id = str(uuid.uuid4())
            dbpath = str(bookId) + "_" + unique_id
            basepath = os.path.join(
                './static/bookImages/', str(bookId) + "_" + unique_id)
            thumbpath = basepath + "_thumbnail" + ".jpg"
            filepath = basepath + ".jpg"
            async with aiofiles.open(filepath, 'wb') as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)
                im = Image.open(filepath)
                im.thumbnail((300, 300), resample=Image.BOX)
                im.save(thumbpath, format='JPEG', quality=65)
                newImage = schemas.bookImageBase(
                    bookId=bookId, filename=dbpath)
                crud.addImage(db, newImage)
        return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_303_SEE_OTHER)
        if not (extension == ".jpg") or (extension == "jpeg"):
            return "Not a valid jpg image"
    except Exception as e:
        return {"message": e.args}
    finally:
        db.close()


@router.post("/getImages/{bookId}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
def get_images(request: Request, bookId: int, user: current_user):
    try:
        db = SessionLocal()
        images = crud.getImages(db, bookId)
        return images
    except Exception as e:
        print(e)
        return "An error has occured."
    finally:
        db.close()


@router.post("/deleteImage/{imageId}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
def delete_image(request: Request, imageId: int, user: admin_user):
    try:
        db = SessionLocal()
        bookId, dbpath = crud.deleteImage(db, imageId)
        jpgPath = os.path.join(
            './static/bookImages/', str(dbpath) + ".jpg")
        thumbPath = os.path.join(
            './static/bookImages/', str(dbpath) + "_thumbnail.jpg")
        os.remove(thumbPath)
        os.remove(jpgPath)
        return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        print(e)
        return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_303_SEE_OTHER)
    finally:
        db.close()


# --------------------------------------------------------------------------
# E-book handling
# --------------------------------------------------------------------------
@router.get("/downloadEbook/{filename}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
def download_ebook(request: Request, filename: str, user: current_user):
    try:
        if user:
            path = ('static/eBooks/' + filename)
            if not os.path.isfile(path):
                raise FileNotFoundError(path)
            return FileResponse(path, media_type='application/octet-stream', filename=filename)
    except Exception:
        return "Failed to download ebook."


@router.get("/deleteEbook/{ebookId}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
def delete_ebook(request: Request, ebookId: int, user: admin_user):
    try:
        db = SessionLocal()
        bookId, dbpath = crud.deleteEbook(db, ebookId)
        ebookPath = os.path.join('./static/eBooks/', str(dbpath))
        try:
            os.remove(ebookPath)
        except:
            print(
                "Tried to delete an ebook file that doesn't exist, removing DB entry")
        return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        print(e)
        return "An error has occured."
    finally:
        db.close()


@router.post("/uploadEbook/{bookId}", dependencies=[get_rate_limiter(times=2, seconds=1)], response_class=HTMLResponse)
async def upload_ebook(file: UploadFile, request: Request, bookId: int, user: admin_user):
    db = SessionLocal()
    try:
        filename = str(os.path.basename(file.filename))
        filename, extension = os.path.splitext(filename)
        book = crud.getBookById(db, bookId)
        title = (book.title[:26]) if len(book.title) > 26 else book.title
        unique_id = (str(uuid.uuid4()))[0:5]
        dbpath = str(title) + "_" + unique_id + extension
        filepath = os.path.join('./static/eBooks/', dbpath)
        async with aiofiles.open(filepath, 'wb') as f:
            while chunk := await file.read(CHUNK_SIZE):
                await f.write(chunk)
            newEbook = schemas.ebookBase(bookId=bookId, filename=dbpath)
            crud.addEbook(db, newEbook)
        return RedirectResponse(url='/bookDetails/' + str(bookId), status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return {"message": e.args}
    finally:
        db.close()
