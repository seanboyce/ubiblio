import os
import shutil
import sqlite3
import csv
from os import listdir
from datetime import datetime
from fastapi import APIRouter, Depends, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.encoders import jsonable_encoder
import json
import aiofiles

from .. import crud, models, schemas
from ..database import SessionLocal
from ..dependencies import (
    get_rate_limiter, templates, CHUNK_SIZE,
    get_current_user_from_token, get_body,
    configForm,
)
from ..vars import DB_LOCATION

router = APIRouter()


# --------------------------------------------------------------------------
# Home Page
# --------------------------------------------------------------------------
@router.get("/", dependencies=[get_rate_limiter(times=3, seconds=1)], response_class=HTMLResponse)
def index(request: Request):
    from ..dependencies import get_current_user_from_cookie
    try:
        user = get_current_user_from_cookie(request)
    except:
        user = None
    if not user:
        context = {
            "request": request
        }
        return templates.TemplateResponse(request, "login.html", context)
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


@router.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')


# --------------------------------------------------------------------------
# Database update / export / backup / restore
# --------------------------------------------------------------------------
@router.get("/dbUpdate", dependencies=[get_rate_limiter(times=1, seconds=2)], response_class=HTMLResponse)
async def db_update_page(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    context = {
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse(request, "updateAdvisory.html", context)


@router.get("/dbUpdateVersion", dependencies=[get_rate_limiter(times=1, seconds=2)], response_class=HTMLResponse)
async def db_update_version_page(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    context = {
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse(request, "updateVersion.html", context)


@router.get("/updateDB", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def update_db(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
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


@router.get("/updateDBVersion", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def update_db_version(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
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
    except:
        return "Only an admin can export the database."


@router.get("/export", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def export_db(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
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


@router.get("/exportcsv", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def export_csv(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
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


@router.get("/backups", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def backups_page(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
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
                "backups": backups,
                "bookExports": bookExports,
                "fileExports": fileExports,
            }
        return templates.TemplateResponse(request, "backups.html", context)
    except:
        return "Only an admin can view database backups."


@router.get("/restoreBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def restore_db(filename, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            path = ('export/' + filename)
            if os.path.isfile(path):
                crud.wipeAndRestore(path)
                response = RedirectResponse(url='/')
                return response
    except Exception as e:
        print(e)


@router.get("/deleteBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def delete_backup(filename, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            path = ('export/' + filename)
            if os.path.isfile(path):
                os.remove(path)
                return RedirectResponse(url='/backups')
    except:
        return "Delete backup failed. It's likely you are not an admin user or there's a file permissions issue."


@router.get("/addByCSV/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def add_csv(filename, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            path = ('export/' + filename)
            if os.path.isfile(path):
                crud.addCSV(path)
                response = RedirectResponse(url='/searchbooks')
                return response
    except:
        return "Error adding books -- check the search page to see what was added."


@router.get("/downloadBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def download_backup(filename, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            path = ('export/' + filename)
            return FileResponse(path, media_type='application/octet-stream', filename=filename)
    except:
        return "Only admins can download backups."


@router.post("/uploadBackup/")
async def upload_backup(file: UploadFile, user: schemas.User = Depends(get_current_user_from_token)):
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
                response = RedirectResponse("/backups", status.HTTP_303_SEE_OTHER)
                return response
            if not (extension == ".sql") or (extension == ".csv"):
                return "Not a valid backup"
    except Exception as e:
        return {"message": e.args}


@router.get("/fileBackup", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def file_backup(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
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


@router.get("/restoreFileBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def restore_files(filename, request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            shutil.unpack_archive("export/" + filename, "static", "zip")
        return RedirectResponse(url='/')
    except:
        return "Only an admin can restore files."


# --------------------------------------------------------------------------
# Library Configuration
# --------------------------------------------------------------------------
@router.get("/config", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def config_page(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            config = crud.getConfig(db)
            db.close()
            context = {
                "user": user,
                "request": request,
                "config": config,
            }
        return templates.TemplateResponse(request, "config.html", context)
    except:
        return "Only an admin can edit the library configuration."


@router.post("/config", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def update_config(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            form = configForm(request)
            await form.load_data()
            if await form.is_valid():
                db = SessionLocal()
                config = schemas.config(id=1, version=form.version, coverImages=form.coverImages, customFieldName1=form.customFieldName1, customFieldName2=form.customFieldName2, genres=form.genres)
                crud.updateConfig(db, config)
                config = crud.getConfig(db)
                db.close()
                context = {
                    "user": user,
                    "config": config,
                    "request": request,
                }
                return templates.TemplateResponse(request, "config.html", context)
    except Exception as e:
        return "Only an admin can edit the library configuration."


# --------------------------------------------------------------------------
# User Management
# --------------------------------------------------------------------------
@router.get("/userManagement", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def user_management(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            context = {
                "user": user,
                "request": request
            }
            return templates.TemplateResponse(request, "userManagement.html", context)
    except:
        return "Only an admin can manage users."


@router.get("/promote/{userId}", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def user_promote(request: Request, userId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            crud.promoteUser(db, userId)
            return RedirectResponse(url='/userManagement')
    except:
        return "Only an admin can manage users."


@router.get("/demote/{userId}", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def user_demote(request: Request, userId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            crud.demoteUser(db, userId)
            return RedirectResponse(url='/userManagement')
    except:
        return "Only an admin can manage users."


@router.get("/deleteUser/{userId}", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def user_delete(request: Request, userId: int, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            crud.deleteUser(db, userId)
            return RedirectResponse(url='/userManagement')
    except:
        return "Only an admin can manage users."


@router.post("/searchUsers", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def search_users(request: Request, user: schemas.User = Depends(get_current_user_from_token), username: str = "%"):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            users = jsonable_encoder(crud.searchUsers(db, str(username)))
            users = json.dumps(users)
            return users
        else:
            return "Only an admin can manage users."
    except Exception as e:
        return "Only an admin can manage users."
    finally:
        db.close()


@router.get("/newUserCode", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def new_user_code(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    try:
        if user.isAdmin == True:
            db = SessionLocal()
            valid_uuid = crud.newUserLink(db)
            context = {
                "valid_uuid": valid_uuid,
                "request": request,
                "user": user
            }
        return templates.TemplateResponse(request, "userLink.html", context)
    except:
        return "Only an admin can add users."
    finally:
        db.close()


# --------------------------------------------------------------------------
# Library Statistics
# --------------------------------------------------------------------------
def vdir(obj):
    return [x for x in dir(obj) if not x.startswith('_')]


@router.post("/stats", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def stats_post(body: bytes = Depends(get_body), user: schemas.User = Depends(get_current_user_from_token)):
    if not user.isAdmin == True:
        return "You are not authorized to access the library stats page, only Admins can do this."
    body = json.loads(body)
    try:
        db = SessionLocal()
        result = crud.stats(db, body["isSum"], body["group"], body["target"])
        for key in result:
            result[key] = round(result[key], 2)
        return json.dumps(result)
    except Exception as e:
        print(e)
        return "Fail"
    finally:
        db.close()


@router.get("/stats", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def stats_get(request: Request, user: schemas.User = Depends(get_current_user_from_token)):
    if not user.isAdmin == True:
        return "You are not authorized to access the library stats page, only Admins can do this."
    try:
        db = SessionLocal()
        fields = vdir(models.Book)
        config = crud.getConfig(db)
        fields.remove("metadata")
        fields.remove("registry")
        fields.remove("id")
        if len(config.customFieldName1) == 0:
            fields.remove("customField1")
        if len(config.customFieldName2) == 0:
            fields.remove("customField2")

        context = {
            "fields": fields,
            "config": config,
            "user": user,
            "request": request
        }
        return templates.TemplateResponse(request, "stats.html", context)
    except Exception as e:
        print(e)
        return "Fail"
    finally:
        db.close()
