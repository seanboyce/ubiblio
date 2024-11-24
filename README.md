# Features:

1. Add books
2. Remove books
3. Update books
4. Search books and see their location (useful if stored in bins, because you don't have space for tons of bookshelves)
5. Autopopulate a book's fields by entering an ISBN (either by typing /isbn/[your-isbn]) into the address bar, or from the 'Add New Book" interface
6. Reading list management for each user
7. Book wishlist (just set owned=False, then update to True when you buy it)
8. Withdraw and return books. Display a list of withdrawn books (to help put them away).
9. Admin users can access all features. Non-admin can only search, manage their reading list, and withdraw/return books.
10. Content discovery (browse by genre).
11. Works on most phones (browsing by genre will only work in landscape though, because of the sometimes long book summaries)
12. Really quite fast, low memory requirements for hosting (I typically see under 100MB and tiny CPU usae).
13. No distractions -- it does what it needs to do and nothing else.

No support for cover images. Wanted to keep memory footprint down and performance lightning fast. Besides, who judges books by the cover?

# Setup:

Use pip to install the requirements in requirements.txt

Open main.py and add a secret key for JWT. Don't tell it to anyone. This is so authenticaton works. One way to generate this key is to open up a command line (linux) and enter: 

$openssl rand -hex 32

The output will be a 32-byte (64 character) hex string. Use it to populate the variable "SECRET_KEY"

Next, since I don't feel like adding the whole user registration / lost password flow, go to the end of main.py. There some code commented out that defines user accounts. Change the passwords and uncomment the code. Run the application, and visit the /setup endpoint. Now open main.py again and comment out the code or delete the whole block. The passwords are hashed in the DB, and not stored plaintext. Don't lose them. Although you can manually delete the user from the DB and add back the /setup endpoint to reset a password if you must.

I realize this is a little inconvenient, but I wanted something fully self-hosted. Registration / password recovery depends on email, which is a pain to host myself.

# Running:

You can run it with either uvicorn or gunicorn. Uvicorn is good for running it locally with no SSL for testing:

$uvicorn ubiblio.main:app --host 0.0.0.0 --port 8000 --reload

(replace the port with another port if you want)

However, on a VPS / server for long-term use, gunicorn is more powerful. Way too powerful for a small personal library, haha.

$python -m gunicorn ubiblio.main:app -b 127.0.0.1:8001 -k uvicorn.workers.UvicornWorker --certfile= --keyfile=

Be sure to remember to set the path to the certificate and key file in that command. This is needed for HTTPS support.

It's expected that you use an apache2 or nginx reverse proxy on your VPS to access the app -- setting this up is beyond the scope of these instructions, but here is a guide I found helpful: https://www.digitalocean.com/community/tutorials/how-to-use-apache-http-server-as-reverse-proxy-using-mod_proxy-extension

It's also expected that you create a virtual environent for deployment (although this is not strictly necessary). For a good tutorial on production deployment with venv+fastapi+gunicorn, give this a read: https://docs.vultr.com/how-to-deploy-fastapi-applications-with-gunicorn-and-nginx-on-ubuntu-20-04

You can use Docker if you like, but I wanted this to work fine without it.

## Backups:

This is handled by sqlite. Try the command:

$sqlite3 sql_app.db ".backup daily.db"

I've left this in a bash script in daily_backup.sh. You can set it as a cron job (e.g. with crontab -e).

# Why this exists:

1. It took about a day to build (well, at least until I thought of a few more features...).
2. I wanted something fast to manage a few hundred books. I tried Koha and others but the huge memory footprint (~4GB) made them expensive to self-host. This application runs with less than 100MB of memory, so I can cram it on a server that hosts lots of other stuff.
3. I wanted a way to quickly check if I own books from my phone, while visiting book sales / stores. Also a way to get a list of books I want. Since I read in English and French, but live in country where neither are common languages, this was a super important feature for me. Opportunities to buy a lot of books are few and far-between for me, so I have to carpe the diem pretty optimally.


# To Do:

1. If I have hundreds of books in a genre, content discovery with "browse by genre" is a bit cumbersome. When a genre is selected, I could display authors + a textbox with summary of their works. Then clicking that leads to a deisplay of all books of that genre by that author. This would let me scale to thousands of books more easily. Not high priority. The software is basically done.
2. I might add an endpoint that lets admin users add other users. In case I open my personal library to the public one day or whatever.

# HTML Theme
The HTML theme is modified from "forty" by HTML5UP (https://html5up.net/). Actually, check out their other themes too. They are excellent and provide the themes under CC Attribution 3.0 (https://html5up.net/license). It's a huge timesaver for building things like this. So please leave the attribution in the footer.
