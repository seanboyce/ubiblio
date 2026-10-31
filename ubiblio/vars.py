import os
import subprocess
import nacl.signing
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError
from hashlib import sha256
# Environment vars
DB_LOCATION = os.environ.get("DB_LOCATION", "./sql_app.db")

USE_REDIS = os.environ.get("USE_REDIS", "true").lower() == "true"
REDIS_URL = os.environ.get("REDIS_URI", "redis://localhost")

LANGUAGE = os.environ.get("LANGUAGE", "")
GOOGLE_BOOKS_API_KEY = os.environ.get("GB_API", "")
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
    SECRET_KEY = SECRET_KEY_ENV
elif os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, "r") as f:
        SECRET_KEY = f.read().strip()
else:
    SECRET_KEY = (
        subprocess.check_output(["openssl", "rand", "-hex", "32"]).decode().strip()
    )
    os.makedirs(os.path.dirname(SECRET_KEY_FILE), exist_ok=True)
    with open(SECRET_KEY_FILE, "w+") as f:
        f.write(SECRET_KEY)


SIGNING_KEY = (
    nacl.signing.SigningKey(SECRET_KEY, encoder=HexEncoder)
)
VERIFY_KEY = (
    SIGNING_KEY.verify_key
)

#Quick sanity test for federation that we run on boot
signed_hex = SIGNING_KEY.sign(b"message", encoder=HexEncoder)
try:
    assert VERIFY_KEY.verify(signed_hex, encoder=HexEncoder)
    assert len(SIGNING_KEY.encode(encoder=HexEncoder)) == 64
    print("Key validation successful. Federation features enabled.")
except BadSignatureError: 
    print("WARNING: uBiblio's verification key does not match it's signing key. Federation features will not work correctly.")
