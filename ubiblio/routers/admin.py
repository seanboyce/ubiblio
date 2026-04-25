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
    current_user, admin_user, get_body,
    configForm, get_current_user_from_cookie,
)
from ..vars import DB_LOCATION

router = APIRouter()


# --------------------------------------------------------------------------
# Home Page
# --------------------------------------------------------------------------
@router.get("/", dependencies=[get_rate_limiter(times=3, seconds=1)], response_class=HTMLResponse)
def index(request: Request):
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
async def db_update_page(request: Request, user: current_user):
    context = {
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse(request, "updateAdvisory.html", context)


@router.get("/dbUpdateVersion", dependencies=[get_rate_limiter(times=1, seconds=2)], response_class=HTMLResponse)
async def db_update_version_page(request: Request, user: current_user):
    context = {
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse(request, "updateVersion.html", context)


@router.get("/updateDB", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def update_db(request: Request, user: admin_user):
    try:
        conn = sqlite3.connect(DB_LOCATION)
        date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
        with open('export/preUpdateExport' + date_time + '.sql', 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        conn.close()
        crud.updateDB()
        return RedirectResponse(url='/searchbooks')
    except Exception as e:
        print(e)
        return "Database export failed."


@router.get("/updateDBVersion", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def update_db_version(request: Request, user: admin_user):
    try:
        dbVersion = crud.getVersion()
        conn = sqlite3.connect(DB_LOCATION)
        date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
        with open('export/preUpdateExport' + date_time + '.sql', 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        conn.close()
        db = SessionLocal()
        try:
            crud.updateDBVersion(db, dbVersion)
        finally:
            db.close()
        return RedirectResponse(url='/searchbooks')
    except Exception as e:
        print(e)
        return "Database export failed."


@router.get("/export", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def export_db(request: Request, user: admin_user):
    try:
        conn = sqlite3.connect(DB_LOCATION)
        date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
        with open('export/DBExport' + date_time + '.sql', 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        conn.close()
        filename = "allFiles" + date_time
        shutil.make_archive(filename, 'zip', "static")
        shutil.move(filename + ".zip", "export/" + filename + ".zip")
        return RedirectResponse(url='/backups')
    except Exception as e:
        print(e)
        return "Database export failed."


@router.get("/exportcsv", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def export_csv(request: Request, user: admin_user):
    try:
        conn = sqlite3.connect(DB_LOCATION)
        cur = conn.cursor()
        bookData = cur.execute("SELECT * FROM books").fetchall()
        date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
        with open('export/csvBookExport' + date_time + '.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerows(bookData)
        conn.close()
        return RedirectResponse(url='/backups')
    except Exception as e:
        print(e)
        return "Database export failed."


@router.get("/backups", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def backups_page(request: Request, user: admin_user):
    try:
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
    except Exception as e:
        print(e)
        return "Could not list database backups."


@router.get("/restoreBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def restore_db(filename, request: Request, user: admin_user):
    try:
        path = 'export/' + filename
        if os.path.isfile(path):
            crud.wipeAndRestore(path)
            return RedirectResponse(url='/')
    except Exception as e:
        print(e)


@router.get("/deleteBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def delete_backup(filename, request: Request, user: admin_user):
    try:
        path = 'export/' + filename
        if os.path.isfile(path):
            os.remove(path)
            return RedirectResponse(url='/backups')
    except Exception as e:
        print(e)
        return "Delete backup failed. There may be a file permissions issue."


@router.get("/addByCSV/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def add_csv(filename, request: Request, user: admin_user):
    try:
        path = 'export/' + filename
        if os.path.isfile(path):
            crud.addCSV(path)
            return RedirectResponse(url='/searchbooks')
    except Exception as e:
        print(e)
        return "Error adding books -- check the search page to see what was added."


@router.get("/downloadBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def download_backup(filename, request: Request, user: admin_user):
    path = 'export/' + filename
    return FileResponse(path, media_type='application/octet-stream', filename=filename)


@router.post("/uploadBackup/")
async def upload_backup(file: UploadFile, user: admin_user):
    try:
        filename_base = str(os.path.basename(file.filename))
        extension = file.filename[-4:].lower()
        if extension in (".sql", ".csv", ".zip"):
            filepath = os.path.join('./export/', filename_base)
            async with aiofiles.open(filepath, 'wb') as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)
            return RedirectResponse("/backups", status.HTTP_303_SEE_OTHER)
        return "Not a valid backup"
    except Exception as e:
        return {"message": e.args}


@router.get("/fileBackup", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def file_backup(request: Request, user: admin_user):
    try:
        date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
        filename = "allFiles" + date_time
        shutil.make_archive(filename, 'zip', "static")
        shutil.move(filename + ".zip", "export/" + filename + ".zip")
        return RedirectResponse(url='/backups')
    except Exception as e:
        print(e)
        return "File backup failed."


@router.get("/restoreFileBackup/{filename}", dependencies=[get_rate_limiter(times=1, seconds=10)], response_class=HTMLResponse)
async def restore_files(filename, request: Request, user: admin_user):
    try:
        shutil.unpack_archive("export/" + filename, "static", "zip")
        return RedirectResponse(url='/')
    except Exception as e:
        print(e)
        return "File restore failed."


# --------------------------------------------------------------------------
# Library Configuration
# --------------------------------------------------------------------------
@router.get("/config", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def config_page(request: Request, user: admin_user):
    try:
        db = SessionLocal()
        config = crud.getConfig(db)
        db.close()
        context = {
            "user": user,
            "request": request,
            "config": config,
        }
        return templates.TemplateResponse(request, "config.html", context)
    except Exception as e:
        print(e)
        return "Could not load library configuration."


@router.post("/config", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def update_config(request: Request, user: admin_user):
    try:
        form = configForm(request)
        await form.load_data()
        if await form.is_valid():
            db = SessionLocal()
            config = schemas.config(id=1, version=form.version, coverImages=form.coverImages,
                                    customFieldName1=form.customFieldName1, customFieldName2=form.customFieldName2, genres=form.genres)
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
        print(e)
        return "Could not update library configuration."


# --------------------------------------------------------------------------
# User Management
# --------------------------------------------------------------------------
@router.get("/userManagement", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def user_management(request: Request, user: admin_user):
    context = {
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse(request, "userManagement.html", context)


@router.get("/promote/{userId}", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def user_promote(request: Request, userId: int, user: admin_user):
    db = SessionLocal()
    try:
        crud.promoteUser(db, userId)
        return RedirectResponse(url='/userManagement')
    except Exception as e:
        print(e)
        return "Could not promote user."
    finally:
        db.close()


@router.get("/demote/{userId}", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def user_demote(request: Request, userId: int, user: admin_user):
    db = SessionLocal()
    try:
        crud.demoteUser(db, userId)
        return RedirectResponse(url='/userManagement')
    except Exception as e:
        print(e)
        return "Could not demote user."
    finally:
        db.close()


@router.get("/deleteUser/{userId}", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def user_delete(request: Request, userId: int, user: admin_user):
    db = SessionLocal()
    try:
        crud.deleteUser(db, userId)
        return RedirectResponse(url='/userManagement')
    except Exception as e:
        print(e)
        return "Could not delete user."
    finally:
        db.close()


@router.post("/searchUsers", dependencies=[get_rate_limiter(times=4, seconds=1)], response_class=HTMLResponse)
def search_users(request: Request, user: admin_user, username: str = "%"):
    db = SessionLocal()
    try:
        users = jsonable_encoder(crud.searchUsers(db, str(username)))
        return json.dumps(users)
    except Exception as e:
        print(e)
        return "User search failed."
    finally:
        db.close()


@router.get("/newUserCode", dependencies=[get_rate_limiter(times=1, seconds=3)], response_class=HTMLResponse)
async def new_user_code(request: Request, user: admin_user):
    db = SessionLocal()
    try:
        valid_uuid = crud.newUserLink(db)
        context = {
            "valid_uuid": valid_uuid,
            "request": request,
            "user": user,
        }
        return templates.TemplateResponse(request, "userLink.html", context)
    except Exception as e:
        print(e)
        return "Could not generate a new user code."
    finally:
        db.close()


# --------------------------------------------------------------------------
# Library Statistics
# --------------------------------------------------------------------------
def vdir(obj):
    return [x for x in dir(obj) if not x.startswith('_')]


@router.post("/stats", dependencies=[get_rate_limiter(times=2, seconds=2)], response_class=HTMLResponse)
async def stats_post(user: admin_user, body: bytes = Depends(get_body)):
    body = json.loads(body)
    db = SessionLocal()
    try:
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
async def stats_get(request: Request, user: admin_user):
    db = SessionLocal()
    try:
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
