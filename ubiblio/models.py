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
    coverImage = Column(String)
    genre = Column(String)
    library = Column(String)
    shelf = Column(String)
    collection = Column(String)
    ISBN = Column(String)
    notes = Column(String, nullable=True)
    owned = Column(Boolean)
    withdrawn = Column(Boolean)

class readingListItems(Base):
    __tablename__ = "readinglistitems"
    id = Column(Integer, primary_key=True)
    book = Column(Integer, ForeignKey("books.id"))
    user_id = Column(Integer)
