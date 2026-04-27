from fastapi.templating import Jinja2Templates
from rich import print
from rich.console import Console

from ..vars import SECRET_KEY, TOKEN_TTL, LANGUAGE

console = Console()


class Settings:
    SECRET_KEY = SECRET_KEY
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = TOKEN_TTL
    COOKIE_NAME = "access_token"


settings = Settings()

language_templates = "templates/" + LANGUAGE
print(language_templates)
templates = Jinja2Templates(directory=language_templates)
