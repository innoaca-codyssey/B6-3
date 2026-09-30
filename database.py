import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

url = os.environ.get('TASK_DB_URL', 'sqlite:///./task.db')
engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

if url.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def foreign_keys(connection, record):
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

def get_db():
    with SessionLocal() as session:
        yield session
