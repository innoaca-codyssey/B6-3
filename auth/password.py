import hashlib
import hmac
import bcrypt

ITERATIONS = 600000


def hash_password(password):
    raw = password.encode('utf-8')
    if len(password) < 8 or len(raw) > 72:
        raise ValueError('비밀번호는 8자 이상, UTF-8 기준 72바이트 이내로 입력하세요')
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=12)).decode('ascii')


def verify_password(password, encoded):
    raw = password.encode('utf-8')
    if len(raw) > 4096:
        return False
    try:
        if encoded.startswith(('$2a$', '$2b$', '$2y$')):
            return len(raw) <= 72 and bcrypt.checkpw(raw, encoded.encode('ascii'))
        # 기존 DB의 PBKDF2 해시도 검증하여 비밀번호를 초기화하지 않습니다.
        scheme, iterations, salt, expected = encoded.split('$')
        if scheme != 'pbkdf2_sha256' or int(iterations) != ITERATIONS:
            return False
        digest = hashlib.pbkdf2_hmac('sha256', raw, bytes.fromhex(salt), ITERATIONS)
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, UnicodeError):
        return False
