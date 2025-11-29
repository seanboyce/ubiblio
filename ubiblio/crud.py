from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.sql import func
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
from . import models, schemas
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import csv
from .vars import *
from os import remove, path
import uuid


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
        purgeFromImages(db, bookId)
        purgeFromEbooks(db, bookId)
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
    result = db.query(models.Book).offset(skip).limit(limit).all()
    resultCount = db.query(models.Book).with_entities(func.count()).scalar()
    return result, resultCount
  
  
  
    
def searchBooks(db: Session, title, author, skip: int, onlyEbooks: bool, noEbooks:bool, limit: int = 50):
    if (onlyEbooks==True) and (noEbooks==False):
        resultCount = db.query(models.Book).filter(
    (or_(models.Book.title.icontains(title),
    models.Book.author.icontains(author)) & (models.Book.owned==True) & (models.Book.ebook==True))).with_entities(func.count()).scalar()
        result = db.query(models.Book).filter(
    (or_(models.Book.title.icontains(title),
    models.Book.author.icontains(author)) & (models.Book.owned==True) & (models.Book.ebook==True))).limit(limit).offset(skip).all()
        return result, resultCount
    elif (onlyEbooks==False) and (noEbooks==True):
         resultCount = db.query(models.Book).filter(
    (or_(models.Book.title.icontains(title),
    models.Book.author.icontains(author)) & (models.Book.owned==True) & (models.Book.ebook==False))).with_entities(func.count()).scalar()
         result = db.query(models.Book).filter(
    (or_(models.Book.title.icontains(title),
    models.Book.author.icontains(author)) & (models.Book.owned==True) & (models.Book.ebook==False))).limit(limit).offset(skip).all()
         return result, resultCount
    else:
        resultCount = db.query(models.Book).filter(
    or_(models.Book.title.icontains(title),
    models.Book.author.icontains(author)) & (models.Book.owned==True)).with_entities(func.count()).scalar()
        result = db.query(models.Book).filter(
    or_(models.Book.title.icontains(title),
    models.Book.author.icontains(author)) & (models.Book.owned==True)).limit(limit).offset(skip).all()
        return result, resultCount

def searchBooksbyAuthor(db: Session, author, skip: int, onlyEbooks: bool, noEbooks:bool, limit: int = 50):
    if (onlyEbooks==True) and (noEbooks==False):
        resultCount = db.query(models.Book).filter(
    models.Book.author.icontains(author) & (models.Book.owned==True) & (models.Book.ebook==True)).with_entities(func.count()).scalar()
        result = db.query(models.Book).filter(
    models.Book.author.icontains(author) & (models.Book.owned==True) & (models.Book.ebook==True)).limit(limit).offset(skip).all()
        return result, resultCount
    elif (onlyEbooks==False) and (noEbooks==True):
        result = db.query(models.Book).filter(
    models.Book.author.icontains(author) & (models.Book.owned==True) & (models.Book.ebook==False)).limit(limit).offset(skip).all()
        resultCount = db.query(models.Book).filter(
    models.Book.author.icontains(author) & (models.Book.owned==True) & (models.Book.ebook==False)).with_entities(func.count()).scalar()
        return result, resultCount
    else:
        result = db.query(models.Book).filter(
    models.Book.author.icontains(author) & (models.Book.owned==True)).limit(limit).offset(skip).all()
        resultCount = db.query(models.Book).filter(
    models.Book.author.icontains(author) & (models.Book.owned==True)).with_entities(func.count()).scalar()
        return result, resultCount

def searchBooksbyTitle(db: Session, title, skip: int, onlyEbooks: bool, noEbooks:bool, limit: int = 50):
    if (onlyEbooks==True) and (noEbooks==False):
        result = db.query(models.Book).filter(
    models.Book.title.icontains(title) & (models.Book.owned==True) & (models.Book.ebook==True)).limit(limit).offset(skip).all()
        resultCount = db.query(models.Book).filter(
    models.Book.title.icontains(title) & (models.Book.owned==True) & (models.Book.ebook==True)).with_entities(func.count()).scalar()
        return result, resultCount    
    elif (onlyEbooks==False) and (noEbooks==True):
        result = db.query(models.Book).filter(
    models.Book.title.icontains(title) & (models.Book.owned==True) & (models.Book.ebook==False)).limit(limit).offset(skip).all()
        resultCount = db.query(models.Book).filter(
    models.Book.title.icontains(title) & (models.Book.owned==True) & (models.Book.ebook==False)).with_entities(func.count()).scalar()
        return result, resultCount
    else:
        result = db.query(models.Book).filter(
    models.Book.title.icontains(title) & (models.Book.owned==True)).limit(limit).offset(skip).all()    
        resultCount = db.query(models.Book).filter(
    models.Book.title.icontains(title) & (models.Book.owned==True)).with_entities(func.count()).scalar()
        return result, resultCount

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

def purgeFromImages(db: Session, bookId):
    try:
        book = db.query(models.bookImage).filter(models.bookImage.bookId == bookId).all()
        for i in book:
            jpgPath = os.path.join('./static/bookImages/', str(i.filename) + ".jpg")
            thumbPath = os.path.join('./static/bookImages/', str(i.filename) + "_thumbnail.jpg")
            if os.path.isfile(thumbPath):
                os.remove(thumbPath)
            if os.path.isfile(jpgPath):    
                os.remove(jpgPath)  
            db.delete(i)
        db.commit()
        return True
    except Exception as e:
        print(e)
        return False

def purgeFromEbooks(db: Session, bookId):
    try:
        book = db.query(models.ebook).filter(models.ebook.bookId == bookId).all()
        for i in book:
            ebookPath = os.path.join('./static/eBooks/', str(i.filename))
            if os.path.isfile(ebookPath):
                os.remove(ebookPath)
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
    conn = sqlite3.connect(DB_LOCATION)
    cursor = conn.execute("DROP TABLE IF EXISTS 'books';")
    cursor = conn.execute("DROP TABLE IF EXISTS 'ebooks';")
    cursor = conn.execute("DROP TABLE IF EXISTS 'userEmails';")
    cursor = conn.execute("DROP TABLE IF EXISTS 'readinglistitems';")
    cursor = conn.execute("DROP TABLE IF EXISTS 'users';")
    cursor = conn.execute("DROP TABLE IF EXISTS 'bookImages';")
    cursor = conn.execute("DROP TABLE IF EXISTS 'config';")
    cursor = conn.execute("DROP TABLE IF EXISTS 'links';")
    cursor = conn.execute("DROP TABLE IF EXISTS 'vkeys';")
    cursor.close()
    conn.commit()
    f = open(filename,'r')
    sql = f.read() # watch out for built-in `str`
    cursor = conn.executescript(sql)
    cursor.close()
    conn.commit()
    conn.close()
    return
    
def addCSV(filename):
    with open(filename,'r') as booksCSV: 
        books = csv.DictReader(booksCSV, fieldnames=['id','title','author','summary','genre','library','shelf','collection','ISBN','notes','owned','withdrawn']) 
        addBooks = [(i['title'], i['author'], i['summary'], i['genre'], i['library'], i['shelf'], i['collection'], i['ISBN'], i['notes'], i['owned'], i['withdrawn']) for i in books]
        print(type(addBooks))
    conn = sqlite3.connect(DB_LOCATION)
    cur = conn.cursor()
    cur.executemany("INSERT INTO books (title, author, summary, genre, library, shelf, collection, ISBN, notes, owned, withdrawn) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", addBooks)
    conn.commit()
    conn.close() 
    return

def checkDB():
    conn = sqlite3.connect(DB_LOCATION)
    configExists = conn.execute("PRAGMA table_info('books');").fetchall()
    if configExists[4][1] == "coverImage":
        return False
    else:
        return True


def updateDB():
    #This updates the DB version from (unversioned) to 1.0.0. Mostly, creating tables will be handled automatically on startup but altering columns will not. Main features added here are ebook and cover image support, library configuration, two custom fields, and a table that could one day store user emails, if we need to store them (currently we do not). 
    conn = sqlite3.connect(DB_LOCATION)
    initData =["1.0.1",False,"","",",".join(schemas.DEFAULT_GENRES)]
    cursor = conn.execute('create table if not exists Config (id INTEGER PRIMARY KEY, version VARCHAR, coverImages BOOLEAN, customFieldName1 VARCHAR, customFieldName2 VARCHAR, genres VARCHAR);')
    cursor = conn.execute('create table if not exists ebooks (id INTEGER PRIMARY KEY, bookId INTEGER, filename VARCHAR);')
    cursor = conn.execute('create table if not exists userEmails (id INTEGER PRIMARY KEY, email VARCHAR, userId INTEGER);')
    cursor = conn.execute('INSERT INTO config (version, coverImages, customFieldName1, customFieldName2, genres) VALUES (?, ?, ?, ?, ?);', initData)
    cursor = conn.execute('ALTER TABLE books DROP coverImage;')
    cursor = conn.execute('ALTER TABLE books ADD COLUMN withdrawnBy VARCHAR;')
    cursor = conn.execute('ALTER TABLE books ADD COLUMN ebook BOOLEAN;')
    cursor = conn.execute('ALTER TABLE books ADD COLUMN customField1 VARCHAR;')
    cursor = conn.execute('ALTER TABLE books ADD COLUMN customField2 VARCHAR;')
    conn.commit()
    conn.close()
    return

def updateDBVersion(db: Session, version):
    if version == "1.0.0":
        conn = sqlite3.connect(DB_LOCATION)
        #Version 1.0.0->1.0.1: We add a genres field to config, which contains the default list of genres, so users can change it. Previously it was hardcoded. 
        cursor = conn.execute('ALTER TABLE config ADD COLUMN genres VARCHAR;')
        cursor = conn.execute('UPDATE config SET genres = ? where id = 1;',(",".join(schemas.DEFAULT_GENRES),))
        cursor = conn.execute('UPDATE config SET version = ? where id = 1;',("1.0.1",))
        conn.commit()
        conn.close()
    return

 
        
def getConfig(db: Session):
    try:
        config = db.query(models.config).first()
        return config
    except Exception as e:
        print(e)
        return

def getVersion():
    try:
        conn = sqlite3.connect(DB_LOCATION)
        cur = conn.cursor()
        version = cur.execute("SELECT version FROM config")
        version = version.fetchone()[0]
        conn.close()
        return version
    except Exception as e:
        print(e)
        return

def updateConfig(db: Session, config: schemas.config):
    try:
        config_exists = db.query(models.config).first()
        config = models.config(** config.dict())
        if config_exists:
            db.merge(config)
            db.commit()
        else:
            db.add(config)
            db.commit()
            db.refresh(config) 
    except Exception as e:
        print(e)
        return  
        
def initConfig(db: Session):
    try:
        config = db.query(models.config).first()
        if not config:    
            conn = sqlite3.connect(DB_LOCATION)
            initData =["1.0.1",False,"","",",".join(schemas.DEFAULT_GENRES)]
            cursor = conn.execute('create table if not exists Config (id INTEGER PRIMARY KEY, version VARCHAR, coverImages BOOLEAN, customFieldName1 VARCHAR, customFieldName2 VARCHAR, genres VARCHAR);')
            cursor = conn.execute('INSERT INTO config (version, coverImages, customFieldName1, customFieldName2, genres) VALUES (?, ?, ?, ?, ?);', initData)
            conn.commit()
            conn.close()
            return
        else:
            return
    except Exception as e:
        print(e)
        return
    
def getImages(db: Session, bookId: int):
    try:
        limit = 16
        return db.query(models.bookImage).filter(models.bookImage.bookId == bookId).limit(limit).all()  
    except Exception as e:
        print(e)
        return 
        
def getImagesByFilename(db: Session, filename: str):
    try:
        image = db.query(models.bookImage).filter(models.bookImage.filename == filename).first()
        if image:
            return True
        if not image:
            return False
    except Exception as e:
        print(e)
        return False

def addImage(db: Session, image: schemas.bookImageBase):
    try:
        image = models.bookImage(** image.dict())
        db.add(image)
        db.commit()
        db.refresh(image)
        return "True"
    except Exception as e:
        print(e)
        return "False"
 
    
def deleteImage(db: Session, imageId: int):
    try:
        image = db.query(models.bookImage).filter(models.bookImage.id == imageId).first()
        bookId = image.bookId
        dbpath = image.filename
        db.delete(image)
        db.commit()
        return bookId,dbpath
    except Exception as e:
        print(e)
        return "False"

def addEbook(db: Session, ebook: schemas.ebookBase):
    try:
        ebook = models.ebook(** ebook.dict())
        db.add(ebook)
        db.commit()
        db.refresh(ebook)
        return "True"
    except Exception as e:
        print(e)
        return "False"
 
    
def deleteEbook(db: Session, ebookId: int):
    try:
        ebook = db.query(models.ebook).filter(models.ebook.id == ebookId).first()
        bookId = ebook.bookId
        dbpath = ebook.filename
        db.delete(ebook)
        db.commit()
        return bookId,dbpath
    except Exception as e:
        print(e)
        return "False"
        
def getEbookFiles(db: Session, bookId: int):
   try:
        limit = 32
        return db.query(models.ebook).filter(models.ebook.bookId == bookId).limit(limit).all()  
   except Exception as e:
        print(e)
        return        

def newUserLink(db: Session):
    try:
        unique_id = str(uuid.uuid4())
        newUserLink = models.link(accessCode=unique_id)
        db.add(newUserLink)
        db.commit()
        db.refresh(newUserLink)
        return unique_id
    except: return False        
    
def codeValidate(db: Session, accessCode: str):
    try:
        exists = db.query(models.link).filter(models.link.accessCode == accessCode).first()
        #timestamp depends on the DB, which ought to be UTC. It must be at most 3 days old.
        lastValid = datetime.utcnow() - timedelta(days = 3)
        if (exists is not None) and (exists.validity >= lastValid):
            #Link exists and is valid
            return True
        elif (exists is not None) and (exists.validity < lastValid):
            #Link exists, but is not valid
            db.delete(exists)
            db.commit()
            return False
        else:
            return False           
    except Exception as e: 
        print(e)
        return False 
        
def createWithCode(db: Session, user: schemas.UserCreate, accessCode: str):
    try:
        exists = db.query(models.link).filter(models.link.accessCode == accessCode).first()
        #timestamp depends on the DB, which ought to be UTC. It must be at most 3 days old.
        lastValid = datetime.utcnow() - timedelta(days = 3)
        if (exists is not None) and (exists.validity >= lastValid):
            #Link exists and is valid, void the link and create the user
            db.delete(exists)
            db.commit()
            passhash = crypto.hash(str(user.password))
            db_user = models.User(username=user.username, passhash=passhash, isAdmin = user.isAdmin)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return True
        elif (exists is not None) and (exists.validity < lastValid):
            #Link exists, but is not valid, delete the 
            db.delete(exists)
            db.commit()
            return False
        else:
            return False           
    except Exception as e: 
        return False 
        
def searchUsers(db: Session, name: str):
    try:
        return db.query(models.User).filter(models.User.username.icontains(name)).all()
    except:
        return False

def promoteUser(db: Session, userId: int):
    try:
        user = db.query(models.User).filter(models.User.id == userId).first()
        user.isAdmin = True
        db.merge(user)
        db.commit()
        return True
    except:
        return False
def demoteUser(db: Session, userId: int):
    try:
        user = db.query(models.User).filter(models.User.id == userId).first()
        user.isAdmin = False
        db.merge(user)
        db.commit()
        return True
    except:
        return False

def deleteUser(db: Session, userId: int):
    try:
        user = db.query(models.User).filter(models.User.id == userId).first()
        db.delete(user)
        db.commit()
        return True
    except:
        return False  
        
def haveKey(db: Session, key: str):
    try:
        result = db.query(models.vkey).filter(models.vkey.vkey==key)
        assert db.query(result.exists()).scalar()
        return True
    except Exception as e:
        print(e)
        return False

def deleteVkey(db: Session, keyId: int):
    try:
        vkey = db.query(models.vkey).filter(models.vkey.id == keyId).first()
        db.delete(vkey)
        db.commit()
        return True
    except:
        return False 
        
def addVkey(db: Session, newKey: schemas.vkeyBase):
    try:
        vkey = models.vkey(** newKey.dict())
        db.add(vkey)
        db.commit()
        db.refresh(vkey)
        return True
    except Exception as e:
        print(e)
        return False
def getAllVkeys (db: Session):
    try:
        return db.query(models.vkey).all()
    except Exception as e:
        print(e)
        return
        
def getVkeyById(db: Session, keyId: int):
    try:
        result = db.query(models.vkey).filter(models.vkey.id==keyId).first()
        return result
    except Exception as e:
        print(e)
        return False
        
def updateVkey(db: Session, newKey: schemas.vkey):
    try:  
        oldVkey = db.query(models.vkey).filter(models.vkey.id == newKey.id).first()
        oldVkey.vkey = newKey.vkey
        db.merge(oldVkey)  
        db.commit()
    except Exception as e:
        print(e)
        return False
