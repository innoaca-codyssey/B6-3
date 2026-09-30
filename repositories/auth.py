from sqlalchemy import select
from models.task import AuthSession, User

class AuthRepository:
    def __init__(self, db):
        self.db = db

    def user(self, username):
        return self.db.scalar(select(User).where(User.username == username))

    def session(self, token_hash):
        return self.db.get(AuthSession, token_hash)

    def save(self, row):
        self.db.add(row)
        self.db.commit()

    def delete(self, row):
        self.db.delete(row)
        self.db.commit()
