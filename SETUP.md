# Prerequesites (Linux):
1. Apache or other webserver set up to reverse-proxy to localhost -- so for example my.domain.com on port 443 redirect to localhost port 8000 where ubiblio runs.
2. redis-server must be installed (this is used for DDoS resistance)
3. gunicorn and uvicorn to launch it (gunicorn recommended for production)
4. sqlite must be installed
5. Around 100MB of memory (for a modest DB and number of users) and a very modest CPU. It will likely run on any computer faster than a potato. Even a raspberry pi is overkill.

NB: Users have reported success running ubiblio on Windows. I just don't know how to use Windows very well. If you would like to contribute setup instructions for Windows or other operating systems, please do so and I will include them.

# Setup:

1. I wrote this for Python 3.10.12 (reported working up to Python 3.12). A good first step is to install that to a venv, like so:
   > python3.10 -m venv "ubiblio"
2. Enter the virtual environment with:
   > source ubiblio/bin/activate
3. cd into the directory and clone the github repository with:
   > git clone https://github.com/seanboyce/ubiblio/
4. cd into the newly created folder (also named ubiblio) and install the requirements.
   > pip install -r requirements.txt
5. Generate a secret key for JWT (this is required to secure your login)
   > openssl rand -hex 32
6. Copy the output to your clipboard and open /ubiblio/main.py in a text editor. Paste it in to the parameter "SECRET_KEY" and save the file.
7. Go to the end of main.py. You will note a code block that defines an API endpoint that sets up user accounts, it is commended out. Add your desired usernames and passwords Note: the passwords will be securely stored as hashes.
8. Proceed to first-time launch!

# First Time Setup

1. Open a browser, connect, ignore the login, and access /setup. This sets up the initial accounts.
2. Shut down ubiblio. Open main.py and delete the code block at the end that you uncommented earlier (the whole /setup endpoint).
3. Launch ubiblio again. 

# Launching

There are two supported ways to launch ubiblio -- uvicorn and gunicorn. Both are ridiculously overpowered for such a simple application, but asking why we need such power is a question for philosophers and cowards.

Presently I launch using tmux as a terminal multiplexer. I open up a new tmux instance, run the command, and detatch from it using 'CTRL+B' and then pressing 'd'. Then if I need to see the logs, I just reattach to the terminal. There are surely better ways to do this, but it works fine.

## Launching with Uvicorn

uvicorn is already quite fast and quite capable of supporting a fair number of ubiblio users. From the main ubiblio directory, you can run it with:

> uvicorn ubiblio.main:app --host 0.0.0.0 --port 8000 --reload

Note that this example above does not enable SSL. It will accept all incoming connections on port 8000 -- so unless you have a firewall blocking access, you ought to be able to access it from another machine on your LAN via the IP address. Your browser will likely complain about the lack of HTTPS, but you can ignore the warning in this case (or run it with a certificate as below).

## Launching with Gunicorn and SSL / HTTPS

gunicorn will launch multiple instances of uvicorn as needed to support even more concurrent users. You need to add the paths to your cert files and choose a port. Certs from letsencrypt are just fine :) 

python -m gunicorn ubiblio.main:app -b 127.0.0.1:8000 -k uvicorn.workers.UvicornWorker --certfile= --keyfile=

# Password Recovery

There is no password recovery -- this is by design. I realize this is a little inconvenient, but I wanted something fully self-hosted. Registration / password recovery generally depends on email, which is a pain to host myself.

If you absolutely need to recover a user, you can shut down ubiblio, open up the DB in a sqlite database browser, and manually clear the users out. Then add back the /setup endpoint to recreate the same users with a known password. Or just add new admin users. Don't forget to clear out the code block after. However, it's a lot less work to simply not lose your password!

# Backups:

This is handled by sqlite. Try the command:

> sqlite3 sql_app.db ".backup daily.db"

I've left this in a bash script in daily_backup.sh. You can set it as a cron job (e.g. with crontab -e).

# Docker Deployment

Docker deployment is not supported yet. I plan to support it later. If you want to help me by figuring it out, please let me know. I would be happy for the assistance -- I don't particulary know Docker well, and don't enjoy using it much. So adding support for this would be a bit of a chore for me.

# Useful Guides

For setting up a reverse proxy: https://www.digitalocean.com/community/tutorials/how-to-use-apache-http-server-as-reverse-proxy-using-mod_proxy-extension

A good tutorial on production deployment with venv+fastapi+gunicorn: https://docs.vultr.com/how-to-deploy-fastapi-applications-with-gunicorn-and-nginx-on-ubuntu-20-04


