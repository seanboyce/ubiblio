# Core Concept

uBiblio is a small and fast web application to help you manage your personal library (and share it with friends, or form a book club). It provides a unified interface for both physical books and ebooks. It is free, open-source, designed for self-hosting, and will never contain ads or spy on you.

You don't have to connect it to the Internet. It can run on your LAN. Or even on a single computer with no network access at all. If you do connect it to the Internet though, it supports federated inter-library search!

# Main Features:

1. Add, remove, update and search books. Physical and ebook management.
2. User management! Admins can invite new users via one-time-use link.
3. Autopopulate a book's fields by entering an ISBN, either manually or with your device's camera!
4. Reading list management for each user, and a wishlist for the library (set owned=False)
5. Withdraw and return books. Display a list of withdrawn books (to help put them away or figure out who has them).
6. Admin users can access all features. Non-admin can only search, manage their reading list, and withdraw/return books.
7. Content discovery (browse by genre).
8. Works on most phones and ebook readers.
9. Really quite fast, low memory requirements for hosting (~100MB). Simple, distraction-free UI.
10. Docker, Docker Hub image, and no-container install options. A big thanks to m0ngr31 for helping with this!
11. Backup management, for both the database and files! 
12. Optional support for cover / book images (up to 16 for each book), with thumbnail support. You can now judge books by their cover (but only if you want to)!
13. A luxurious TWO optional custom fields, in case your library is structured differently than mine. Set them up in the admin menu.
14. It even runs on RISCV64 with memory to spare (check out the cursed branch)!
15. Aussi disponible en français! Démarrez ubiblio avec LANGUAGE='FR'

# Setup

![Setup has moved to it's own file to keep things organized](https://github.com/seanboyce/ubiblio/blob/main/SETUP.md)


# Possible future features (in no particular order):
![Roadmap has moved to it's own file to keep things organized](https://github.com/seanboyce/ubiblio/blob/main/ROADMAP.md)

# Contributing

Raise an issue here on Github explaining the feature you want (or want to add yourself). Then make a PR! If you are using an AI to assist, please let me know (and test first!), and keep the PR size to a minimum so that I can manually review it.

For bug reports, the process is the same. Maybe also include the steps to reproduce it.

Things I especially need help with: testing, getting more scalable language support in, adding in some kind of integrated help or wiki.

# HTML Theme
The HTML theme is modified from "forty" by HTML5UP (https://html5up.net/). Actually, check out their other themes too. They are excellent and provide the themes under CC Attribution 3.0 (https://html5up.net/license). It's a huge timesaver for building things like this. So please leave the attribution in the footer.

# Menu System
![Screenshot of the menu system](https://raw.githubusercontent.com/seanboyce/ubiblio/refs/heads/dev/ubiblio_menu.png)

# Book Search
![Screenshot of the book search system](https://raw.githubusercontent.com/seanboyce/ubiblio/refs/heads/dev/ubiblio_search.png)

# Reading list / Browse by Genre / Wishlist / Withdrawn Books List
![Screenshot of a more detailed list of books](https://raw.githubusercontent.com/seanboyce/ubiblio/refs/heads/dev/ubiblio_readling_list.png)
