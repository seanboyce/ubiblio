# Core Concept

uBiblio is a small and fast web application to help you manage your personal library (and share it with friends, or form a book club). It provides a unified interface for both physical books and ebooks. It is free, open-source, designed for self-hosting, and will never contain ads or spy on you.

You don't have to connect it to the Internet. It can run on your LAN. Or even on a single computer with no network access at all. 

# Main Features:

1. Add, remove, update books
2. Search books and see their location (useful if stored in bins, because you don't have space for tons of bookshelves)
3. Autopopulate a book's fields by entering an ISBN (either by typing /isbn/[your-isbn]) into the address bar, or from the 'Add New Book" interface
4. Reading list management for each user
5. Book wishlist (just set owned=False, then update to True when you buy it)
6. Withdraw and return books. Display a list of withdrawn books (to help put them away or figure out who has them).
7. Admin users can access all features. Non-admin can only search, manage their reading list, and withdraw/return books.
8. Content discovery (browse by genre).
9. Works on most phones and ebook readers.
10. Really quite fast, low memory requirements for hosting (~100MB). 
11. No distractions -- it does what it needs to do and nothing else (by default).
12. Docker, Docker Hub image, and no-container install options. A big thanks to m0ngr31 for helping with this!
13. Backup management, for both the database and files! 
14. Ebook support, with the ability to store ebook files and download from your reader (as long as it has a web browser)
15. Optional support for cover / book images (up to 16 for each book), with thumbnail support. You can now judge books by their cover (but only if you want to)!
16. A luxurious TWO optional custom fields, in case your library is structured differently than mine. Set them up in the admin menu.
17. It even runs on RISCV64 with memory to spare (check out the cursed branch)!

# Setup

![Setup has moved to it's own file to keep things organized](https://github.com/seanboyce/ubiblio/blob/main/SETUP.md)


# Possible future features (in no particular order):
1. Modify content discovery via 'browse by genre' to be more practical for high numbers of books.
2. Search by a specific location would be nice -- can be another interface.
3. Limited UI customization -- what fields are displayed on the search results interface. This can easily break mobile compatibility though, but not everyone is using this on their phone, so being able to take advantage of that extra space is fine.


# HTML Theme
The HTML theme is modified from "forty" by HTML5UP (https://html5up.net/). Actually, check out their other themes too. They are excellent and provide the themes under CC Attribution 3.0 (https://html5up.net/license). It's a huge timesaver for building things like this. So please leave the attribution in the footer.

# Menu System
![Screenshot of the menu system](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_menu.png)

# Book Search
![Screenshot of the book search system](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_search.png)

# Reading list / Browse by Genre / Wishlist / Withdrawn Books List
![Screenshot of a more detailed list of books](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_readling_list.png)
