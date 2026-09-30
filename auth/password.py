import hashlib
import hmac
import secrets

ITERATIONS = 600000

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'

def verify_password(password, encoded):
    if len(password) > 1024:
        return False
    scheme, iterations, salt, expected = encoded.split('$')
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations))
    return scheme == 'pbkdf2_sha256' and hmac.compare_digest(digest.hex(), expected)
