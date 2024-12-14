from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    passhash = Column(String)
    isAdmin = Column(Boolean, default=False)

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    summary = Column(String)
    genre = Column(String)
    library = Column(String)
    shelf = Column(String)
    collection = Column(String)
    ISBN = Column(String)
    notes = Column(String, nullable=True)
    owned = Column(Boolean)
    withdrawn = Column(Boolean)
    withdrawnBy = Column(Integer, nullable=True)
    customField1 = Column(String, nullable=True)
    customField2 = Column(String, nullable=True)

class readingListItems(Base):
    __tablename__ = "readinglistitems"
    id = Column(Integer, primary_key=True)
    book = Column(Integer, ForeignKey("books.id"))
    user_id = Column(Integer)
    
class bookImage(Base):
    __tablename__ = "bookImages"
    id = Column(Integer, primary_key=True)
    bookId = Column(Integer, ForeignKey("books.id"))
    book = Column(Integer, ForeignKey("books.id"))
    filename = Column(String, nullable=False)  

class config(Base):
    __tablename__= "config"
    id = Column(Integer, primary_key=True)
    version = Column(String)
    coverImages = Column(Boolean)
    customFieldName1 = Column(String)
    customFieldName2 = Column(String)


    
