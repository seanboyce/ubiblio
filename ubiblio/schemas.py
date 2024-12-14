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
    genre: str = Field(default=None)
    library: str = Field(default=None)
    shelf: str = Field(default=None)
    collection: str = Field(default=None)
    ISBN: str = Field(default=None)
    notes: str = Field(default=None)
    owned: bool = Field(default=False)
    withdrawn: bool = Field(default=False)
    withdrawnBy: int = Field(default=False)
    customField1: str = Field(default=None)
    customField2: str = Field(default=None)
                
class BookCreate(BookBase):
    author: str = Field(default=None)
    summary: str = Field(default=None)
    genre: str = Field(default=None)
    library: str = Field(default=None)
    shelf: str = Field(default=None)
    collection: str = Field(default=None)
    ISBN: str = Field(default=None)
    notes: str = Field(default=None)
    owned: bool = Field(default=None)
    withdrawn: bool = Field(default=False)    
    withdrawnBy: int = Field(default=False)
    customField1: str = Field(default=None)
    customField2: str = Field(default=None)

class readingListItems(BaseModel):
    id: int
    book: int
    user_id: int 
    class Config:
        orm_mode = True
 
class readingListItemCreate(BaseModel):
    book: int
    user_id: int
    class Config:
        orm_mode = True
    
class bookImageBase(BaseModel):  
    bookId: int
    filename: str
    class Config:
        orm_mode = True    
        
class bookImage(bookImageBase):  
    id: int 

class config(BaseModel):
    id: int 
    version: str = Field(default=None)
    coverImages: bool = Field(default=False)
    customFieldName1: str = Field(default=None)
    customFieldName1: str = Field(default=None)
    class Config:
        orm_mode = True       

