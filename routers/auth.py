from fastapi import APIRouter, Cookie, Depends, Form, Request
from fastapi.responses import RedirectResponse
from auth.session import optional_session, require_csrf
from database import get_db
from routers.task import templates
from services.auth import AuthService

router = APIRouter()

@router.get('/')
def home(request: Request, auth=Depends(optional_session)):
    return templates.TemplateResponse(request=request, name='home.html', context={'auth': auth})

@router.get('/login')
def login_form(request: Request, auth=Depends(optional_session)):
    return templates.TemplateResponse(request=request, name='login.html', context={'auth': auth, 'message': None})

@router.post('/login')
def login(request: Request, username: str = Form(''), password: str = Form(''), session: str | None = Cookie(default=None), db=Depends(get_db)):
    try:
        token = AuthService(db).login(username, password, session)
    except ValueError as error:
        return templates.TemplateResponse(request=request, name='login.html', context={'auth': None, 'message': str(error)}, status_code=400)
    response = RedirectResponse('/app/projects', status_code=303)
    response.set_cookie('session', token, max_age=3600, httponly=True, samesite='lax', path='/')
    return response

@router.post('/logout')
def logout(auth=Depends(require_csrf), db=Depends(get_db)):
    AuthService(db).logout(auth)
    response = RedirectResponse('/', status_code=303)
    response.delete_cookie('session', path='/')
    return response
