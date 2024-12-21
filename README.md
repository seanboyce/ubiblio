# Features:

1. Add, remove, update books
2. Search books and see their location (useful if stored in bins, because you don't have space for tons of bookshelves)
3. Autopopulate a book's fields by entering an ISBN (either by typing /isbn/[your-isbn]) into the address bar, or from the 'Add New Book" interface
4. Reading list management for each user
5. Book wishlist (just set owned=False, then update to True when you buy it)
6. Withdraw and return books. Display a list of withdrawn books (to help put them away or figure out who has them).
7. Admin users can access all features. Non-admin can only search, manage their reading list, and withdraw/return books.
8. Content discovery (browse by genre).
9. Works on most phones (browsing by genre will only work in landscape though, because of the sometimes long book summaries).
10. Really quite fast, low memory requirements for hosting (I typically see under 100MB and tiny CPU usage).
11. No distractions -- it does what it needs to do and nothing else (by default).
12. Docker, Docker Hub image, and no-container install options. A big thanks to m0ngr31 for helping with this!
13. Backup management! 
14. Optional support for cover / book images (up to 16 for each book), with thumbnail support. You can now judge books by their cover (but only if you want to)!
15. A luxurious TWO optional custom fields, in case your library is structured differently than mine. Set them up in the admin menu.
16. No hidden easter eggs!

# Setup

![Setup has moved to it's own file to keep things organized](https://github.com/seanboyce/ubiblio/blob/main/SETUP.md)

# Why this exists:

1. It took about a day to build the core features. 
2. I wanted something fast to manage a few hundred books. I tried Koha and others but the huge memory footprint (~4GB) made them expensive to self-host. This application runs with less than 100MB of memory, so I can cram it on a server that hosts lots of other stuff.
3. I wanted a way to quickly check if I own books from my phone, while visiting book sales / stores. Also a way to get a list of books I want. Since I read in English and French, but live in country where neither are common languages, this was a super important feature for me. Opportunities to buy a lot of books are few and far-between for me, so I have to carpe the diem pretty optimally.


# To Do (in no particular order):

1. Backup / migrate stored files.
2. Ebook support, including file storage/retrieval/backup for ebooks.
3. A one-button "send to my reader" for ebooks (requires an ebook reader that can receive books by email). Probably I'll look into something like Oauth2 support + Protonmail.
4. Modify content discovery via 'browse by genre' to be more practical for high numbers of books.
5. Search by a specific location would be nice -- can be another interface.
6. Limited UI customization -- what fields are displayed on the search results interface. This can easily break mobile compatibility though, but not everyone is using this on their phone, so being able to take advantage of that extra space is fine.


# HTML Theme
The HTML theme is modified from "forty" by HTML5UP (https://html5up.net/). Actually, check out their other themes too. They are excellent and provide the themes under CC Attribution 3.0 (https://html5up.net/license). It's a huge timesaver for building things like this. So please leave the attribution in the footer.

# Menu System
![Screenshot of the menu system](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_menu.png)

# Book Search
![Screenshot of the book search system](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_search.png)

# Reading list / Browse by Genre / Wishlist / Withdrawn Books List
![Screenshot of a more detailed list of books](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_readling_list.png)
