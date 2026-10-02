import hmac
import secrets
from fastapi import APIRouter, Cookie, Depends, Form, Request
from fastapi.responses import RedirectResponse
from auth.session import optional_session, require_csrf
from database import get_db
from routers.task import templates
from services.auth import AuthService, Forbidden

router = APIRouter()

@router.get('/')
def home(request: Request, auth=Depends(optional_session)):
    return templates.TemplateResponse(request=request, name='home.html', context={'auth': auth})

@router.get('/login')
def login_form(request: Request, auth=Depends(optional_session)):
    return templates.TemplateResponse(request=request, name='login.html', context={'auth': auth, 'message': '회원가입이 완료되었습니다. 로그인해 주세요' if request.query_params.get('registered') == '1' else None})

@router.get('/signup')
def signup_form(request: Request, auth=Depends(optional_session)):
    csrf = secrets.token_urlsafe(32)
    response = templates.TemplateResponse(request=request, name='signup.html', context={'auth': auth, 'csrf': csrf, 'message': None, 'username': ''})
    response.set_cookie('signup_csrf', csrf, max_age=1800, httponly=True, samesite='lax', path='/signup')
    return response

@router.post('/signup')
def signup(request: Request, username: str = Form(''), password: str = Form(''), csrf: str = Form(''), signup_csrf: str | None = Cookie(default=None), auth=Depends(optional_session), db=Depends(get_db)):
    if not signup_csrf or not csrf or not csrf.isascii() or not signup_csrf.isascii() or not hmac.compare_digest(csrf, signup_csrf):
        raise Forbidden('회원가입 화면을 다시 열어 주세요')
    try:
        AuthService(db).signup(username, password)
    except ValueError as error:
        return templates.TemplateResponse(request=request, name='signup.html', context={'auth': auth, 'csrf': signup_csrf, 'username': username, 'message': str(error)}, status_code=400)
    response = RedirectResponse('/login?registered=1', status_code=303)
    response.delete_cookie('signup_csrf', path='/signup')
    return response

@router.post('/login')
def login(request: Request, username: str = Form(''), password: str = Form(''), session: str | None = Cookie(default=None), db=Depends(get_db)):
    try:
        token = AuthService(db).login(username, password, session)
    except ValueError as error:
        return templates.TemplateResponse(request=request, name='login.html', context={'auth': AuthService(db).context(session), 'message': str(error)}, status_code=400)
    response = RedirectResponse('/app/projects', status_code=303)
    response.set_cookie('session', token, max_age=3600, httponly=True, samesite='lax', path='/')
    return response

@router.post('/logout')
def logout(auth=Depends(require_csrf), db=Depends(get_db)):
    AuthService(db).logout(auth)
    response = RedirectResponse('/', status_code=303)
    response.delete_cookie('session', path='/')
    return response
