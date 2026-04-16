from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

from . import models
from .database import engine
from .dependencies import templates
from .vars import USE_REDIS, REDIS_URL

from .routers import auth, books, reading_lists, files, admin, federation

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['POST'],
    allow_headers=['*']
)


@app.on_event("startup")
async def startup():
    if USE_REDIS:
        redis_connection = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_connection)


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(reading_lists.router)
app.include_router(files.router)
app.include_router(federation.router)
