from dataclasses import dataclass
from datetime import timedelta
import hashlib
import secrets
from auth.password import hash_password, verify_password
from models.task import AuthSession, User, utcnow
from repositories.auth import AuthRepository

class Unauthorized(Exception):
    pass

class Forbidden(Exception):
    pass

@dataclass
class AuthContext:
    user_id: int
    username: str
    csrf: str
    token_hash: str

class AuthService:
    def __init__(self, db):
        self.repository = AuthRepository(db)

    def seed(self):
        for username in ['demo', 'guest']:
            if self.repository.user(username) is None:
                self.repository.save(User(username=username, password_hash=hash_password('practice1234')))

    def login(self, username, password, old_token=None):
        user = self.repository.user(username)
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError('ID 또는 비밀번호가 올바르지 않습니다')
        if old_token:
            old = self.repository.session(hashlib.sha256(old_token.encode()).hexdigest())
            if old is not None:
                self.repository.delete(old)
        token = secrets.token_urlsafe(32)
        self.repository.save(AuthSession(token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id, csrf=secrets.token_urlsafe(32), expires_at=utcnow() + timedelta(hours=1)))
        return token

    def context(self, token):
        if not token or len(token) > 128:
            return None
        row = self.repository.session(hashlib.sha256(token.encode()).hexdigest())
        if row is None:
            return None
        if row.expires_at <= utcnow():
            self.repository.delete(row)
            return None
        return AuthContext(row.user_id, row.user.username, row.csrf, row.token_hash)

    def logout(self, context):
        row = self.repository.session(context.token_hash)
        if row is not None:
            self.repository.delete(row)
