# New Features in this Version:
1. Federated search! You can link up ubiblio instances, and search each other's books (but not edit them).
2. An advanced search page. For now, it just handles federated searches.
3. Google Books API returns HTTP 429 errors when no API key is specified. The library used by ubiblio could not correctly set Google Books API keys. So I wrote functions to access (Google Books, OpenLibrary, Wikipedia) so ubiblio no longer relies on external libraries for this. 
4. Google books will be skipped on ISBN auto-add unless you specify a Google books API key (free) by setting the environment variable GB_API="YOUR-API-KEY". I'll re-enable it without API key if it starts working again.


# Notes

The application can be used just fine from the Kindle Paperwhite (and probably most other ebook readers with web browsers), because it is very simple. I find navigating / searching my ebooks gets impractically slow on-device. Ubiblio is much faster, and additionally lets me store all my ebooks elsewhere. No need to ever worry about device storage again! Incidentally, for better display on ebook displays, I've made some text in bold (ebook file management). 

# New Features in last Version:

1. Database backup can now handle files, and the backup/restore UI lets you manage that.
2. If ISBN auto-adder failes to find a book, try other sources. This can take a little longer, but makes adding books faster overall.
3. Clean up book details template -- infrequently used (admin) actions are in an accordion element. Remove that useless 'Back' button.
4. Categorize action buttons on book details page
5. When cover images are enabled, display them by default, not hidden in an accordion element.
6. Ebook support! When creating the book, just set ebook=True
7. New template page for ebooks. Allows file upload / delete (admins only) and download (all users). Contains only fields pertinent to ebooks. 
8. Admin actions should be hidden on all pages for non-admin users (let me know if I've missed one)
9. Added a cursed branch, for deploying on RISCV64. Still no easter eggs, though.

# Notes:


1. Database upgrade is a little sketchy. I haven't been able to break it in testing though. Note that ubiblio will back up your database before attempting to upgrade -- if you encounter a bug with the upgrade process, please reach out. 


