from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    # 회원에 종속된 프로젝트는 회원 삭제 시 함께 삭제합니다.
    projects: Mapped[list[Project]] = relationship(back_populates='owner', cascade='all, delete-orphan')
    # 회원 삭제 시 로그인 세션도 폐기합니다.
    sessions: Mapped[list[AuthSession]] = relationship(back_populates='user', cascade='all, delete-orphan')

class Project(Base):
    __tablename__ = 'project'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'))
    owner: Mapped[User] = relationship(back_populates='projects')
    # 프로젝트에 종속된 할 일은 프로젝트 삭제 시 함께 삭제합니다.
    tasks: Mapped[list[Task]] = relationship(back_populates='project', cascade='all, delete-orphan')

class Task(Base):
    __tablename__ = 'task'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    project_id: Mapped[int] = mapped_column(ForeignKey('project.id', ondelete='CASCADE'))
    project: Mapped[Project] = relationship(back_populates='tasks')

class AuthSession(Base):
    __tablename__ = 'auth_session'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'))
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    user: Mapped[User] = relationship(back_populates='sessions')
