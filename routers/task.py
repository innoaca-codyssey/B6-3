from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from services.task import TaskService

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / 'templates'))


@router.get('/')
def home(request: Request):
    return templates.TemplateResponse(request=request, name='home.html')


@router.get('/tasks')
def listing(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse(request=request, name='list.html', context={'tasks': TaskService(db).list()})


@router.get('/tasks/new')
def new(request: Request):
    return templates.TemplateResponse(request=request, name='form.html', context={'task': None})


@router.post('/tasks')
def create(title: str = Form(''), description: str = Form(''), db=Depends(get_db)):
    task = TaskService(db).create(title, description)
    return RedirectResponse(f'/tasks/{task.id}', status_code=303)


@router.get('/tasks/{identifier}')
def detail(identifier: int, request: Request, db=Depends(get_db)):
    return templates.TemplateResponse(request=request, name='detail.html', context={'task': TaskService(db).get(identifier)})


@router.get('/tasks/{identifier}/edit')
def edit(identifier: int, request: Request, db=Depends(get_db)):
    return templates.TemplateResponse(request=request, name='form.html', context={'task': TaskService(db).get(identifier)})


@router.post('/tasks/{identifier}/edit')
def update(identifier: int, title: str = Form(''), description: str = Form(''), db=Depends(get_db)):
    task = TaskService(db).update(identifier, title, description)
    return RedirectResponse(f'/tasks/{task.id}', status_code=303)


@router.post('/tasks/{identifier}/delete')
def delete(identifier: int, db=Depends(get_db)):
    TaskService(db).delete(identifier)
    return RedirectResponse('/tasks', status_code=303)
