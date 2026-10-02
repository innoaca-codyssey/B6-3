import hmac
from fastapi import Cookie, Depends, Form
from database import get_db
from services.auth import AuthService, Forbidden, Unauthorized

def optional_session(session: str | None = Cookie(default=None), db=Depends(get_db)):
    return AuthService(db).context(session)

def require_session(context=Depends(optional_session)):
    if context is None:
        raise Unauthorized()
    return context

def require_csrf(csrf: str = Form(default=''), context=Depends(require_session)):
    if not csrf.isascii() or not context.csrf.isascii() or not hmac.compare_digest(csrf, context.csrf):
        raise Forbidden('화면을 새로고침한 뒤 다시 요청하세요')
    return context
