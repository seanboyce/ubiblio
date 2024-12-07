# Features:

1. Add, remove, update books
2. Search books and see their location (useful if stored in bins, because you don't have space for tons of bookshelves)
3. Autopopulate a book's fields by entering an ISBN (either by typing /isbn/[your-isbn]) into the address bar, or from the 'Add New Book" interface
4. Reading list management for each user
5. Book wishlist (just set owned=False, then update to True when you buy it)
6. Withdraw and return books. Display a list of withdrawn books (to help put them away).
7. Admin users can access all features. Non-admin can only search, manage their reading list, and withdraw/return books.
8. Content discovery (browse by genre).
9. Works on most phones (browsing by genre will only work in landscape though, because of the sometimes long book summaries)
10. Really quite fast, low memory requirements for hosting (I typically see under 100MB and tiny CPU usae).
11. No distractions -- it does what it needs to do and nothing else.
12. Docker, Docker Hub image, and no-container install options.

No support for cover images. Wanted to keep memory footprint down and performance lightning fast. Besides, who judges books by the cover?

# Setup

![Setup has moved to it's own file to keep things organized](https://github.com/seanboyce/ubiblio/blob/main/SETUP.md)

# Why this exists:

1. It took about a day to build (well, at least until I thought of a few more features. Then other people suggested features... and so on.).
2. I wanted something fast to manage a few hundred books. I tried Koha and others but the huge memory footprint (~4GB) made them expensive to self-host. This application runs with less than 100MB of memory, so I can cram it on a server that hosts lots of other stuff.
3. I wanted a way to quickly check if I own books from my phone, while visiting book sales / stores. Also a way to get a list of books I want. Since I read in English and French, but live in country where neither are common languages, this was a super important feature for me. Opportunities to buy a lot of books are few and far-between for me, so I have to carpe the diem pretty optimally.


# To Do (in no particular order):

1. Downloadable database export from the web interface. This is the highest priority, as I don't want people to lose their data entry if I make changes to the DB schema and so on (which some of the features below require). 
2. Modify content discovery via 'browse by genre' to be more practical for high numbers of books.
3. Search by a specific location would be nice -- can be another interface.
4. Limited backend customization -- a few custom fields for books that can be renamed through the UI (default:hidden)
5. Limited UI customization -- what fields are displayed on the search results interface. This can easily break mobile compatibility though, but not everyone is using this on their phone, so being able to take advantage of that extra space is fine.
6. Storing who withdrew a book instead of simply whether it is withdrawn or not, e.g. for when you reluctantly let other people use your personal library.


# HTML Theme
The HTML theme is modified from "forty" by HTML5UP (https://html5up.net/). Actually, check out their other themes too. They are excellent and provide the themes under CC Attribution 3.0 (https://html5up.net/license). It's a huge timesaver for building things like this. So please leave the attribution in the footer.

# Menu System
![Screenshot of the menu system](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_menu.png)

# Book Search
![Screenshot of the book search system](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_search.png)

# Reading list / Browse by Genre / Wishlist / Withdrawn Books List
![Screenshot of a more detailed list of books](https://github.com/seanboyce/ubiblio/blob/main/ubiblio_readling_list.png)
