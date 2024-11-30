# Setup:

I wrote this for Python 3.10.12. A good first step is to install that to a venv.

Use pip to install the requirements in requirements.txt

Open main.py and add a secret key for JWT. Don't tell it to anyone. This is so authenticaton works. One way to generate this key is to open up a command line (linux) and enter: 

$openssl rand -hex 32

The output will be a 32-byte (64 character) hex string. Use it to populate the variable "SECRET_KEY"

Next, since I don't feel like adding the whole user registration / lost password flow, go to the end of main.py. There some code commented out that defines user accounts. Change the passwords and uncomment the code. Run the application, and visit the /setup endpoint. Now open main.py again and comment out the code or delete the whole block. The passwords are hashed in the DB, and not stored plaintext. Don't lose them. Although you can manually delete the user from the DB and add back the /setup endpoint to reset a password if you must.

I realize this is a little inconvenient, but I wanted something fully self-hosted. Registration / password recovery depends on email, which is a pain to host myself.

# Running:

Before you begin, you will need to install redis-server. Some perhaps useful instructions here: https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-20-04

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
