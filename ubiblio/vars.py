import os
import subprocess
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from hashlib import sha256
# Environment vars
DB_LOCATION = os.environ.get("DB_LOCATION", "./sql_app.db")

USE_REDIS = os.environ.get("USE_REDIS", "true").lower() == "true"
REDIS_URL = os.environ.get("REDIS_URI", "redis://localhost")

LANGUAGE = os.environ.get("LANGUAGE", "FR")

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
    os.makedirs(os.path.dirname(SECRET_KEY_FILE), exist_ok=True)
    with open(SECRET_KEY_FILE, "w+") as f:
        f.write(secret_key)

SECRET_KEY = secret_key

#These are used for federation. We let the operating system handle file security, rather than store in the DB. We could put them in the OS keyring, but that would make it hard to move uBiblio.
SIGNING_KEY_ENV = os.environ.get("SIGNING_KEY")
VERIFY_KEY_ENV = os.environ.get("VERIFY_KEY")
SIGNING_KEY_FILE = os.environ.get("SIGNING_KEY_FILE", "./sign_key.txt")
VERIFY_KEY_FILE = os.environ.get("VERIFY_KEY_FILE", "./verify_key.txt")

if SIGNING_KEY_ENV:
    sign_key = SIGNING_KEY_ENV
    verify_key = VERIFY_KEY_ENV
elif os.path.exists(SIGNING_KEY_FILE):
    with open(SIGNING_KEY_FILE, "r") as f:
        sign_key = f.read().strip()
    with open(VERIFY_KEY_FILE, "r") as f:
        verify_key = f.read().strip()
else:
    sign_key_raw = (
        SigningKey.generate(curve=SECP256k1, hashfunc=sha256)
    )
    verify_key = (
        sign_key_raw.get_verifying_key().to_string().hex()
    )
    sign_key = (
        sign_key_raw.to_string().hex()
    )
    os.makedirs(os.path.dirname(SIGNING_KEY_FILE), exist_ok=True)
    with open(SIGNING_KEY_FILE, "w+") as f:
        f.write(sign_key)
        f.close()
    os.makedirs(os.path.dirname(VERIFY_KEY_FILE), exist_ok=True)
    with open(VERIFY_KEY_FILE, "w+") as f:
        f.write(verify_key)
        f.close()
VERIFY_KEY = verify_key
SIGNING_KEY = sign_key

#Quick test for federation
sig = SigningKey.from_string(bytearray.fromhex(SIGNING_KEY), curve=SECP256k1).sign(b"message")
try:
    assert VerifyingKey.from_string(bytearray.fromhex(VERIFY_KEY), curve=SECP256k1).verify(sig, b"message")
    print("Key validation successfull. Federation features enabled.")
except BadSignatureError: 
    print("WARNING: uBiblio's verification key does not match it's signing key. Federation features will not work correctly.")
