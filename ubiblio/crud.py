from sqlalchemy.orm import Session
from sqlalchemy import or_
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
from . import models, schemas
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import csv

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    try:
        passhash = crypto.hash(str(user.password))
        db_user = models.User(username=user.username, passhash=passhash, isAdmin = user.isAdmin)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        print(e)
        return False
        
def isAdmin(db: Session, username: str):
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        return User.isAdmin
    except Exception as e:
        print(e)
        return False
        


def createBook(db: Session, book: schemas.Book):
    try:
        book = models.Book(** book.dict())
        db.add(book)
        db.commit()
        db.refresh(book)
        return "True"
    except Exception as e:
        print(e)
        return "False"
        
def deleteBook(db: Session, bookId):
    try:
        purgeFromReadingList(db, bookId)
        book = db.query(models.Book).filter(models.Book.id == bookId).first()
        db.delete(book)
        db.commit()
        return "True"
    except Exception as e:
        print(e)
        return "False"
 
def getBookById(db: Session, bookId):
    try:
        return db.query(models.Book).filter(models.Book.id == bookId).first()
    except Exception as e:
        print(e)
        return False
                
def updateBook(db: Session, book: schemas.Book):
    try:
        item = db.get(models.Book, book.id)  
        if item:
            book = models.Book(** book.dict())
            db.merge(book)
            db.commit()   
        if not item:
            print("updated item does not exist")
            return False
    except Exception as e:
        print(e)
        return False
        
def getBooks(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.Book).offset(skip).limit(limit).all()
    
def searchBooks(db: Session, title, author, skip: int, limit: int = 50):
    return db.query(models.Book).filter(
    or_(models.Book.title.icontains(title),
    models.Book.author.icontains(author)) & (models.Book.owned==True)) .limit(limit).offset(skip).all()

def searchBooksbyAuthor(db: Session, author, skip: int, limit: int = 50):
    return db.query(models.Book).filter(
    models.Book.author.icontains(author) & (models.Book.owned==True)) .limit(limit).offset(skip).all()

def searchBooksbyTitle(db: Session, title, skip: int, limit: int = 50):
    return db.query(models.Book).filter(
    models.Book.title.icontains(title) & (models.Book.owned==True)) .limit(limit).offset(skip).all()    

def browseBooksByGenre(db: Session, genre):
    return db.query(models.Book).filter(models.Book.genre == genre)

def browseWishlist(db: Session):
    return db.query(models.Book).filter(models.Book.owned == False)
    
def browseWithdrawn(db: Session):
    return db.query(models.Book).filter(models.Book.withdrawn == True)
    
def getGenres(db: Session):
    genres = []
    for value in db.query(models.Book.genre).distinct():
        genres.append(value[0])
    return genres
    
def readBook(db: Session, readingListItem: schemas.readingListItemCreate):
    try:
        readingListItem = models.readingListItems(** readingListItem.dict())
        db.add(readingListItem)
        db.commit()
        db.refresh(readingListItem)
        return "True"
    except Exception as e:
        print(e)
        return "False"
        
def readingList(db: Session, userId: int):  
    return db.query(models.readingListItems).filter(models.readingListItems.user_id == userId).all()
    
def bookUnRead(db: Session, bookId):
    try:
        readingListItem = db.query(models.readingListItems).filter(models.readingListItems.book == bookId).first()
        db.delete(readingListItem)
        db.commit()  
        return True
    except Exception as e:
        print(e)
        return False
        
def purgeFromReadingList(db: Session, bookId):
    try:
        book = db.query(models.readingListItems).filter(models.readingListItems.book == bookId).all()
        for i in book:
            db.delete(i)
        db.commit()  
        return True
    except Exception as e:
        print(e)
        return False

def bookReturn(db: Session, book: schemas.Book):
    try:  
        item = db.get(models.Book, book.id)  
        if item:
            book = models.Book(** book.dict())
            db.merge(book)
            db.commit()   
        if not item:
            print("updated item does not exist")
            return False
    except Exception as e:
        print(e)
        return False

def bookWithdraw(db: Session, book: schemas.Book):
    try:
        item = db.get(models.Book, book.id)  
        if item:
            book = models.Book(** book.dict())
            db.merge(book)
            db.commit()   
        if not item:
            print("updated item does not exist")
            return False
    except Exception as e:
        print(e)
        return False
        
def wipeAndRestore(filename):
    conn = sqlite3.connect('sql_app.db')
    cursor = conn.execute("DROP TABLE 'books';")
    cursor = conn.execute("DROP TABLE 'readinglistitems';")
    cursor = conn.execute("DROP TABLE 'users';")
    cursor.close()
    # Hm, what if new schema is different?
    # models.Base.metadata.create_all(bind=engine)
    f = open(filename,'r')
    sql = f.read() # watch out for built-in `str`
    cursor = conn.executescript(sql)
    cursor.close()
    return
    
def addCSV(filename):
    with open(filename,'r') as booksCSV: 
        books = csv.DictReader(booksCSV, fieldnames=['id','title','author','summary','coverImage','genre','library','shelf','collection','ISBN','notes','owned','withdrawn']) 
        addBooks = [(i['title'], i['author'], i['summary'], i['coverImage'], i['genre'], i['library'], i['shelf'], i['collection'], i['ISBN'], i['notes'], i['owned'], i['withdrawn']) for i in books]
        print(type(addBooks))
    conn = sqlite3.connect('sql_app.db')
    cur = conn.cursor()
    cur.executemany("INSERT INTO books (title, author, summary, coverImage, genre, library, shelf, collection, ISBN, notes, owned, withdrawn) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", addBooks)
    conn.commit()
    conn.close() 
    return

#def updateDB():
#    conn = sqlite3.connect('sql_app.db')
#    initData =["1.0.0",False]
#    configExists = conn.execute('SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type="table" AND name="config");')
#    if configExists:
#        cursor = conn.execute("create table if not exists Config (id INTEGER PRIMARY KEY, version VARCHAR, coverImages BOOLEAN);")
#        cursor = conn.execute("INSERT INTO config (version, coverImages) VALUES (?, ?);", initData)
#        #Other modifications to tables here, e.g. drop coverimage field, add custom fields
#    else:    
#        #if already exists, check version is at least current version. Although in this first upgrase, we can just pass.
#        pass

