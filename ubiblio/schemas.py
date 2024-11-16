from pydantic import BaseModel, Field
from datetime import datetime

class UserBase(BaseModel):
    username: str
    isAdmin: bool = Field(default=False)
    class Config:
        orm_mode = True
    

class User(UserBase):
    id: int
    passhash: str

        
#This is so password plaintext is only sent/received by anything on account creation
class UserCreate(UserBase):
    password: str
    

class BookBase(BaseModel):
    title: str
    class Config:
        orm_mode = True

class Book(BookBase):
    id: int 
    author: str = Field(default=None)
    summary: str = Field(default=None)
    coverImage: str = Field(default=None)
    genre: str = Field(default=None)
    library: str = Field(default=None)
    shelf: str = Field(default=None)
    collection: str = Field(default=None)
    ISBN: str = Field(default=None)
    notes: str = Field(default=None)
    owned: bool = Field(default=False)
    withdrawn: bool = Field(default=False)
    
class BookCreate(BookBase):
    author: str = Field(default=None)
    summary: str = Field(default=None)
    coverImage: str = Field(default=None)
    genre: str = Field(default=None)
    library: str = Field(default=None)
    shelf: str = Field(default=None)
    collection: str = Field(default=None)
    ISBN: str = Field(default=None)
    notes: str = Field(default=None)
    owned: bool = Field(default=None)
    withdrawn: bool = Field(default=False)    

class readingListItems(BaseModel):
    id: int
    book: int
    user_id: int 
 
class readingListItemCreate(BaseModel):
    book: int
    user_id: int
