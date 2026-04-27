from typing import List, Optional

from fastapi import Request

from .. import schemas


class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

    async def is_valid(self):
        if not self.username:
            self.errors.append("Please enter your username")
        if not self.password or not len(self.password) >= 3:
            self.errors.append("A valid password is required")
        if not self.errors:
            return True
        return False


class newUserForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.accessCode: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")
        self.accessCode = form.get("accessCode")

    async def is_valid(self):
        if not self.username:
            self.errors.append("Please enter your username")
        if not self.password or not len(self.password) >= 3:
            self.errors.append("A valid password over 3 characters is required")
        if not self.accessCode:
            self.errors.append("Something went wrong with your access link. Reload this page, or contact your library admin.")
        if not self.errors:
            return True
        return False


class newVkeyForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.url: str
        self.vkey: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.url = form.get("url")
        self.vkey = form.get("vkey")

    async def is_valid(self):
        if not self.url:
            self.errors.append("Validation keys require a URL to tie them to")
        if not self.errors:
            return True
        return False


class bookForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.title: str
        self.author: Optional[str] = None
        self.summary: Optional[str] = None
        self.genre: Optional[str] = None
        self.library: Optional[str] = None
        self.shelf: Optional[str] = None
        self.collection: Optional[str] = None
        self.ISBN: Optional[str] = None
        self.notes: Optional[str] = None
        self.owned: Optional[bool] = None
        self.withdrawn: Optional[bool] = None
        self.ebook: Optional[bool] = None
        self.customField1: Optional[str] = None
        self.customField2: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.title = form.get("title")
        self.author = form.get("author")
        self.summary = form.get("summary")
        self.genre = form.get("genre")
        self.library = form.get("library")
        self.shelf = form.get("shelf")
        self.collection = form.get("collection")
        self.ISBN = form.get("ISBN")
        self.notes = form.get("notes")
        self.owned = form.get("owned")
        self.withdrawn = form.get("withdrawn")
        self.ebook = form.get("ebook")
        self.customField1 = form.get("customField1")
        self.customField2 = form.get("customField2")

    async def is_valid(self):
        if not self.title:
            self.errors.append("At least a title is required to create a book.")
        if not self.errors:
            return True
        return False


class configForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.version: Optional[str] = None
        self.coverImages: Optional[bool] = None
        self.customFieldName1: Optional[str] = None
        self.customFieldName2: Optional[str] = None
        self.genres: str = ""

    async def load_data(self):
        form = await self.request.form()
        self.version = form.get("version")
        self.coverImages = form.get("coverImages")
        self.customFieldName1 = form.get("customFieldName1")
        self.customFieldName2 = form.get("customFieldName2")
        self.genres = form.get("genres") or ",".join(schemas.DEFAULT_GENRES)

    async def is_valid(self):
        if not self.version:
            self.errors.append("Database version is required so as not to break the DB")
        if not self.version:
            self.errors.append("Enable Cover Images must be either True or False")
        if not self.errors:
            return True
        return False
