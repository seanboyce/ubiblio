BEGIN TRANSACTION;
CREATE TABLE "apiKeys" (
	id VARCHAR NOT NULL, 
	"userID" INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY("userID") REFERENCES users (id)
);
CREATE TABLE "bookImages" (
	id INTEGER NOT NULL, 
	"bookId" INTEGER, 
	filename VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY("bookId") REFERENCES books (id)
);
CREATE TABLE books (
	id INTEGER NOT NULL, 
	title VARCHAR, 
	author VARCHAR, 
	summary VARCHAR, 
	genre VARCHAR, 
	library VARCHAR, 
	shelf VARCHAR, 
	collection VARCHAR, 
	"ISBN" VARCHAR, 
	notes VARCHAR, 
	owned BOOLEAN, 
	withdrawn BOOLEAN, 
	"withdrawnBy" VARCHAR, 
	"customField1" VARCHAR, 
	"customField2" VARCHAR, 
	ebook BOOLEAN, 
	"addedTime" DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id)
);
CREATE TABLE config (
	id INTEGER NOT NULL, 
	version VARCHAR, 
	"coverImages" BOOLEAN, 
	"customFieldName1" VARCHAR, 
	"customFieldName2" VARCHAR, 
	genres VARCHAR, 
	"enableAPI" BOOLEAN, 
	PRIMARY KEY (id)
);
INSERT INTO "config" VALUES(1,'1.0.1',0,'','','Sci-Fi,Fantasy,Classic,Reference,Young Adult,Historical Fiction,Mystery,Anthology,Horror,Romance,Animal Fiction',NULL);
CREATE TABLE ebooks (
	id INTEGER NOT NULL, 
	"bookId" INTEGER, 
	filename VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY("bookId") REFERENCES books (id)
);
CREATE TABLE links (
	id INTEGER NOT NULL, 
	"accessCode" VARCHAR, 
	validity DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id)
);
CREATE TABLE readinglistitems (
	id INTEGER NOT NULL, 
	book INTEGER, 
	user_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(book) REFERENCES books (id)
);
CREATE TABLE "userEmails" (
	id INTEGER NOT NULL, 
	email VARCHAR, 
	user_id INTEGER, 
	PRIMARY KEY (id)
);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR, 
	passhash VARCHAR, 
	"isAdmin" BOOLEAN, 
	PRIMARY KEY (id)
);
INSERT INTO "users" VALUES(1,'username','$6$rounds=656000$xRjzqLNbaixjMAC9$ycfyt.uvi9RcPeFV2yLnWIi8SBU5A4p9I4I3DHCkLVG/VDAKVahmltwosuupyjizWzh6tM21UezdI0KEDY9IP0',1);
CREATE TABLE vkeys (
	id INTEGER NOT NULL, 
	vkey VARCHAR, 
	url VARCHAR, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE INDEX "ix_links_accessCode" ON links ("accessCode");
CREATE INDEX ix_vkeys_url ON vkeys (url);
CREATE INDEX ix_vkeys_vkey ON vkeys (vkey);
COMMIT;
