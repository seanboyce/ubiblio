from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from . import service
from ... import crud, schemas
from ...database import SessionLocal
from ...dependencies import admin_user, bookForm, current_user, get_rate_limiter, templates

router = APIRouter()


# --------------------------------------------------------------------------
# Manage User API Keys
# --------------------------------------------------------------------------    

@router.get("/apiKey/", dependencies=[get_rate_limiter(times=1, seconds=2)], response_class=HTMLResponse)
async def fetchAPI(request: Request, user: current_user):
    if user:
        db = SessionLocal()
        APIKey = crud.getMyAPIKey(db, current_user) # This function will create it if it doesn't exist.
        db.close()
        context = {
            "user": user,
            "apiKey": APIKey,
            "request": request,
        }
        return templates.TemplateResponse(request, "api.html", context)
    if not user:
        return "You are not logged in. Login to access your API key."    
        
@router.get("/resetMyAPI/", dependencies=[get_rate_limiter(times=1, seconds=5)], response_class=HTMLResponse)
async def resetMyAPI(request: Request, user: current_user):
    if user:
        db = SessionLocal()
        APIKey = crud.resetMyAPIKey(db, current_user)
        db.close()
        context = {
            "user": user,
            "apiKey": APIKey,
            "request": request,
        }
        return templates.TemplateResponse(request, "api.html", context)
    if not user:
        return "You are not logged in. Login to reset your API key."        
        
