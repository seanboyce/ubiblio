import os
import subprocess


# Environment vars
DB_LOCATION = os.environ.get("DB_LOCATION", "./sql_app.db")

USE_REDIS = os.environ.get("USE_REDIS", "true").lower() == "true"
REDIS_URL = os.environ.get("REDIS_URI", "redis://localhost")

TOKEN_TTL = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

CREATE_ADMIN_USER = os.environ.get("CREATE_ADMIN_USER", "false").lower() == "true"
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

CREATE_USER = os.environ.get("CREATE_USER", "false").lower() == "true"
USER_USERNAME = os.environ.get("USER_USERNAME", "user")
USER_PASSWORD = os.environ.get("USER_PASSWORD", "user")

SECRET_KEY_ENV = os.environ.get("SECRET_KEY")
SECRET_KEY_FILE = os.environ.get("SECRET_KEY_FILE", "./secret_key.txt")

if SECRET_KEY_ENV:
    secret_key = SECRET_KEY_ENV
elif os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, "r") as f:
        secret_key = f.read().strip()
else:
    secret_key = (
        subprocess.check_output(["openssl", "rand", "-hex", "32"]).decode().strip()
    )
    with open(SECRET_KEY_FILE, "w+") as f:
        f.write(secret_key)

SECRET_KEY = secret_key
