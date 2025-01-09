# New Features in this Version:

1. Database backup can now handle files, and the backu/restore UI lets you manage that.
2. If ISBN auto-adder failes to find a book, try other sources. This can take a little longer, but makes adding books faster overall.
3. Clean up book details template -- infrequently used (admin) actions are in an accordion element. Remove that useless 'Back' button.
4. Categorize action buttons on book details page
5. When cover images are enabled, display them by default, not hidden in an accordion element.
6. Ebook support! When creating the book, just set ebook=True
7. New template page for ebooks. Allows file upload / delete (admins only) and download (all users). Contains only fields pertinent to ebooks. 
8. Admin actions should be hidden on all pages for non-admin users (let me know if I've missed one)
9. Added a cursed branch, for deploying on RISCV64. Still no easter eggs, though.

# Notes

The application can be used just fine from the Kindle Paperwhite (and probably most other ebook readers with web browsers), because it is very simple. I find navigating / searching my ebooks gets impractically slow on-device. Ubiblio is much faster, and additionally lets me store all my ebooks elsewhere. No need to ever worry about device storage again! Incidentally, for better display on ebook displays, I've made some text in bold (ebook file management). 

# New Features in last Version:

1. Database import / export / restore from a GUI (using the backup script still works though).
2. Database versioning and automatic upgrade (it will back up first).
3. A library config menu for admins, where you can manage backups and other things.
4. You can now judge books by their cover! Image support for up to 16 images per book (enable in config menu -- or if you don't want it, leave it disabled)
5. A luxurious two custom fields you can enable and name at your leisure (from the config menu -- just give them a name to enable)
6. A view for withdrawn books that makes more sense -- you can see who withdrew a book.
7. You can export your book list as CSV in the backup management interface. For example if you just want to use ubiblio for data entry.
8. If you import a book list from ubiblio, is will ADD the books to the database instead of replacing the current database. For example, this lets you merge different libraries. 
9. New books no longer default to science fiction! Slightly inconvenient for time travelers, better for the rest of you.
10. Various minor UI improvements.
11. Still zero easter eggs!

# Notes:

1. Be advised that any files you add (book images, backups) are not included in the database backup presently. These are stored in /static/bookImages and /export respectively. In the next major release, files will be backed up and compressed too. For now, you must manually back up these folders. 

2. Database upgrade is a little sketchy in this first major update. I haven't been able to break it in testing though. Note that ubiblio will back up your database before attempting to upgrade -- if you encounter a bug with the upgrade process, please reach out. 


